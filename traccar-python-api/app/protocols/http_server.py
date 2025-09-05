"""
HTTP Protocol Server for OsmAnd and other HTTP-based protocols
"""
import asyncio
import json
import logging
from datetime import datetime
from typing import Dict, Any, Optional, Tuple
from aiohttp import web, ClientSession
from aiohttp.web import Request, Response
import structlog

from app.protocols.base import BaseProtocolHandler, ProtocolMessage
from sqlalchemy import select
from app.database import get_db, AsyncSessionLocal
from app.models import Device, Position, Event, UnknownDevice
from app.schemas.position import PositionCreate
from app.services.websocket_service import websocket_service

logger = structlog.get_logger(__name__)


class HTTPProtocolServer:
    """
    HTTP server for handling HTTP-based protocols like OsmAnd
    """
    
    def __init__(self, protocol_handler: BaseProtocolHandler, host: str = "0.0.0.0", port: int = 5055):
        self.protocol_handler = protocol_handler
        self.host = host
        self.port = port
        self.app = web.Application()
        self.runner = None
        self.site = None
        self.running = False
        
        # Setup routes
        self._setup_routes()
    
    def _setup_routes(self):
        """Setup HTTP routes for the protocol"""
        # Health check endpoint (must be first to avoid conflicts)
        self.app.router.add_get('/health', self.health_check)
        
        # Main endpoint for position data
        self.app.router.add_route('*', '/', self.handle_request)
        self.app.router.add_route('*', '/{path:.*}', self.handle_request)
    
    async def handle_request(self, request: Request) -> Response:
        """
        Handle incoming HTTP requests from mobile devices
        
        Args:
            request: HTTP request object
            
        Returns:
            HTTP response
        """
        try:
            # Read request data
            if request.method in ['POST', 'PUT', 'PATCH']:
                data = await request.read()
            else:
                # For GET requests, we'll reconstruct the data from URL and headers
                data = self._build_request_data(request)
            
            client_address = (request.remote, 0)  # HTTP doesn't have client port info
            
            # Parse message using protocol handler
            # For HTTP requests, we need to pass the request object instead of raw data
            message = await self._parse_http_request(request, client_address)
            
            if not message:
                logger.warning("Failed to parse message", client=client_address, protocol=self.protocol_handler.PROTOCOL_NAME)
                return web.Response(status=400, text="Invalid message format")
            
            # Validate device
            if not self.protocol_handler.validate_device_id(message.device_id):
                logger.warning("Invalid device ID", device_id=message.device_id, client=client_address)
                return web.Response(status=400, text="Invalid device ID")
            
            # Log message
            self.protocol_handler.log_message(message, client_address)
            
            # Process position data
            position_data = await self.protocol_handler.create_position(message)
            if position_data:
                await self._save_position(message.device_id, position_data)
            
            # Process events
            events = await self.protocol_handler.create_events(message)
            for event_data in events:
                await self._save_event(event_data)
            
            # Return success response
            return web.Response(
                status=200,
                text="OK",
                headers={'Content-Type': 'text/plain'}
            )
            
        except Exception as e:
            logger.error("Error handling HTTP request", error=str(e), client=request.remote)
            return web.Response(status=500, text="Internal server error")
    
    def _build_request_data(self, request: Request) -> bytes:
        """Build request data from HTTP request for GET requests"""
        # Reconstruct the HTTP request as it would appear to the protocol handler
        request_line = f"{request.method} {request.path_qs} HTTP/1.1"
        headers = []
        
        for name, value in request.headers.items():
            headers.append(f"{name}: {value}")
        
        headers_str = "\r\n".join(headers)
        return f"{request_line}\r\n{headers_str}\r\n\r\n".encode()
    
    async def _parse_http_request(self, request: Request, client_address: Tuple[str, int]) -> Optional[ProtocolMessage]:
        """Parse HTTP request using protocol handler"""
        try:
            # Check content type
            content_type = request.headers.get('content-type', '')
            
            if 'application/json' in content_type:
                # JSON format
                json_data = await request.json()
                device_id = json_data.get('device_id') or json_data.get('deviceid') or json_data.get('id')
                
                if not device_id:
                    return None
                
                message_data = {
                    'device_id': device_id,
                    'json_data': json_data,
                    'headers': dict(request.headers),
                    'client_address': client_address
                }
                
                return ProtocolMessage(
                    device_id=device_id,
                    message_type="location",
                    data=message_data,
                    timestamp=datetime.utcnow(),
                    raw_data=json.dumps(json_data).encode(),
                    valid=True
                )
            else:
                # Query string format
                query_params = {}
                for key, value in request.query.items():
                    query_params[key] = [value]
                
                # Also check POST data
                if request.method in ['POST', 'PUT', 'PATCH']:
                    try:
                        form_data = await request.post()
                        for key, value in form_data.items():
                            if key not in query_params:
                                query_params[key] = [value]
                    except:
                        pass
                
                if not query_params:
                    return None
                
                # Extract device ID
                device_id = None
                for key in ['id', 'deviceid', 'device_id']:
                    if key in query_params and query_params[key]:
                        device_id = query_params[key][0]
                        break
                
                if not device_id:
                    return None
                
                message_data = {
                    'device_id': device_id,
                    'query_params': query_params,
                    'headers': dict(request.headers),
                    'client_address': client_address
                }
                
                return ProtocolMessage(
                    device_id=device_id,
                    message_type="location",
                    data=message_data,
                    timestamp=datetime.utcnow(),
                    raw_data=json.dumps(query_params).encode(),
                    valid=True
                )
                
        except Exception as e:
            logger.error("Failed to parse HTTP request", error=str(e))
            return None
    
    async def _save_position(self, device_id: str, position_data: Dict[str, Any]):
        """Save position data to database"""
        db = None
        try:
            # Get database session
            db = AsyncSessionLocal()
            
            # Find device
            result = await db.execute(
                select(Device).filter(Device.unique_id == device_id)
            )
            device = result.scalar_one_or_none()
            if not device:
                logger.warning("Device not found", device_id=device_id)
                # Track unknown device
                await self._track_unknown_device(db, device_id, client_address)
                return
            
            # Create position
            position_create = PositionCreate(**position_data)
            position = Position(
                device_id=device.id,
                protocol=position_create.protocol,
                device_time=position_create.device_time,
                valid=position_create.valid,
                latitude=position_create.latitude,
                longitude=position_create.longitude,
                altitude=position_create.altitude,
                speed=position_create.speed,
                course=position_create.course,
                attributes=json.dumps(position_create.attributes or {})  # Convert to JSON string
            )
            
            db.add(position)
            await db.commit()
            
            logger.info("Position saved", device_id=device_id, position_id=position.id)
            
            # Broadcast via WebSocket
            await websocket_service.broadcast_position(position)
            
        except Exception as e:
            logger.error("Failed to save position", error=str(e), device_id=device_id)
        finally:
            if db:
                await db.close()
    
    async def _save_event(self, event_data: Dict[str, Any]):
        """Save event data to database"""
        db = None
        try:
            # Get database session
            db = AsyncSessionLocal()
            
            # Find device
            result = await db.execute(
                select(Device).filter(Device.unique_id == event_data['device_id'])
            )
            device = result.scalar_one_or_none()
            if not device:
                logger.warning("Device not found for event", device_id=event_data['device_id'])
                return
            
            # Create event
            event = Event(
                device_id=device.id,
                type=event_data['type'],
                event_time=event_data['timestamp'],
                attributes=json.dumps(event_data.get('attributes', {}))  # Convert to JSON string
            )
            
            db.add(event)
            await db.commit()
            
            logger.info("Event saved", device_id=event_data['device_id'], event_type=event_data['type'])
            
            # Broadcast via WebSocket (skip for now - method not implemented)
            # await websocket_service.broadcast_event(event)
            
        except Exception as e:
            logger.error("Failed to save event", error=str(e), event_data=event_data)
        finally:
            if db:
                await db.close()
    
    async def health_check(self, request: Request) -> Response:
        """Health check endpoint"""
        return web.json_response({
            "status": "healthy",
            "protocol": self.protocol_handler.PROTOCOL_NAME,
            "port": self.port
        })
    
    async def start(self):
        """Start the HTTP server"""
        try:
            self.runner = web.AppRunner(self.app)
            await self.runner.setup()
            
            self.site = web.TCPSite(self.runner, self.host, self.port)
            await self.site.start()
            
            self.running = True
            logger.info(f"HTTP server started for {self.protocol_handler.PROTOCOL_NAME} on {self.host}:{self.port}")
            
        except Exception as e:
            logger.error(f"Failed to start HTTP server for {self.protocol_handler.PROTOCOL_NAME}", error=str(e))
            raise
    
    async def stop(self):
        """Stop the HTTP server"""
        try:
            if self.site:
                await self.site.stop()
            if self.runner:
                await self.runner.cleanup()
            
            self.running = False
            logger.info(f"HTTP server stopped for {self.protocol_handler.PROTOCOL_NAME}")
            
        except Exception as e:
            logger.error(f"Failed to stop HTTP server for {self.protocol_handler.PROTOCOL_NAME}", error=str(e))
    
    def is_running(self) -> bool:
        """Check if server is running"""
        return self.running
    
    async def _track_unknown_device(self, db: AsyncSessionLocal, device_id: str, client_address: Tuple[str, int]):
        """Track unknown device connection"""
        try:
            # Check if this unknown device already exists
            result = await db.execute(
                select(UnknownDevice).where(
                    UnknownDevice.unique_id == device_id,
                    UnknownDevice.protocol == self.protocol_handler.PROTOCOL_NAME,
                    UnknownDevice.port == self.port
                )
            )
            existing = result.scalar_one_or_none()
            
            if existing:
                # Update existing record
                existing.last_seen = datetime.utcnow()
                existing.connection_count += 1
                existing.client_address = f"{client_address[0]}:{client_address[1]}"
            else:
                # Create new unknown device record
                unknown_device = UnknownDevice(
                    unique_id=device_id,
                    protocol=self.protocol_handler.PROTOCOL_NAME,
                    port=self.port,
                    protocol_type="http",
                    client_address=f"{client_address[0]}:{client_address[1]}",
                    connection_count=1
                )
                db.add(unknown_device)
            
            await db.commit()
            logger.info("Unknown device tracked", device_id=device_id, protocol=self.protocol_handler.PROTOCOL_NAME)
            
        except Exception as e:
            logger.error("Failed to track unknown device", error=str(e), device_id=device_id)

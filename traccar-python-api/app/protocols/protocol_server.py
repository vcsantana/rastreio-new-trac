"""
Protocol server manager for handling multiple GPS protocols.
"""

import asyncio
import logging
from typing import Dict, List, Optional, Type, Any
from datetime import datetime
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Device, Position, Event, User
from app.schemas.position import PositionCreate
from app.protocols.base import BaseProtocolHandler, ProtocolServer, ProtocolMessage
from app.protocols.suntech import SuntechProtocolHandler
from app.protocols.http_server import HTTPProtocolServer
from app.services.websocket_service import websocket_service

logger = logging.getLogger(__name__)


class TraccarProtocolServer:
    """
    Main protocol server that manages multiple protocol handlers.
    """
    
    def __init__(self):
        self.protocol_handlers: Dict[str, BaseProtocolHandler] = {}
        self.protocol_servers: Dict[str, ProtocolServer] = {}
        self.http_servers: Dict[str, HTTPProtocolServer] = {}
        self.running = False
        self.tasks: List[asyncio.Task] = []
        
        # Register available protocol handlers
        self._register_protocol_handlers()
    
    def _register_protocol_handlers(self):
        """Register available protocol handlers."""
        from app.protocols.osmand import OsmAndProtocolHandler
        
        self.protocol_handlers = {
            "suntech": SuntechProtocolHandler(),
            "osmand": OsmAndProtocolHandler(),
            # Add more protocols here as they are implemented
            # "gt06": GT06ProtocolHandler(),
            # "h02": H02ProtocolHandler(),
        }
        
        logger.info(f"Registered {len(self.protocol_handlers)} protocol handlers")
    
    async def start_protocol_server(self, protocol_name: str, host: str = "0.0.0.0", port: int = None, protocol_type: str = "tcp"):
        """Start a protocol server for a specific protocol."""
        if protocol_name not in self.protocol_handlers:
            raise ValueError(f"Unknown protocol: {protocol_name}")
        
        if port is None:
            port = self._get_default_port(protocol_name)
        
        handler = self.protocol_handlers[protocol_name]
        
        # Check if this is an HTTP-based protocol
        if protocol_name == "osmand":
            server = HTTPProtocolServer(handler, host, port)
            self.http_servers[protocol_name] = server
            await server.start()
            logger.info(f"Started HTTP server for {protocol_name} on {host}:{port}")
        else:
            # TCP/UDP protocols
            server = TraccarProtocolServerWrapper(handler, host, port, protocol_type)
            self.protocol_servers[protocol_name] = server
            
            if protocol_type.lower() == "tcp":
                task = asyncio.create_task(server.start_tcp_server())
            elif protocol_type.lower() == "udp":
                task = asyncio.create_task(server.start_udp_server())
            else:
                raise ValueError(f"Unsupported protocol type: {protocol_type}")
            
            self.tasks.append(task)
            logger.info(f"Started {protocol_type.upper()} server for {protocol_name} on {host}:{port}")
    
    def _get_default_port(self, protocol_name: str) -> int:
        """Get default port for protocol."""
        default_ports = {
            "suntech": 5001,
            "gt06": 5002,
            "h02": 5003,
            "meiligao": 5004,
            "teltonika": 5005,
            "concox": 5006,
            "osmand": 5055,
        }
        return default_ports.get(protocol_name, 5000)
    
    async def start_all_servers(self, host: str = "0.0.0.0"):
        """Start all registered protocol servers."""
        self.running = True
        
        for protocol_name in self.protocol_handlers.keys():
            try:
                await self.start_protocol_server(protocol_name, host)
            except Exception as e:
                logger.error(f"Failed to start server for {protocol_name}: {e}")
        
        logger.info(f"Started {len(self.protocol_servers)} protocol servers")
    
    async def stop_all_servers(self):
        """Stop all protocol servers."""
        self.running = False
        
        # Stop TCP/UDP servers
        for server in self.protocol_servers.values():
            await server.stop()
        
        # Stop HTTP servers
        for server in self.http_servers.values():
            await server.stop()
        
        # Cancel all tasks
        for task in self.tasks:
            task.cancel()
        
        # Wait for tasks to complete
        if self.tasks:
            await asyncio.gather(*self.tasks, return_exceptions=True)
        
        self.protocol_servers.clear()
        self.http_servers.clear()
        self.tasks.clear()
        logger.info("All protocol servers stopped")
    
    def get_server_status(self) -> Dict[str, Dict[str, Any]]:
        """Get status of all protocol servers."""
        status = {}
        
        # TCP/UDP servers
        for protocol_name, server in self.protocol_servers.items():
            status[protocol_name] = {
                "running": server.running,
                "host": server.host,
                "port": server.port,
                "protocol_type": getattr(server, 'protocol_type', 'tcp'),
                "clients": len(server.clients),
            }
        
        # HTTP servers
        for protocol_name, server in self.http_servers.items():
            status[protocol_name] = {
                "running": server.is_running(),
                "host": server.host,
                "port": server.port,
                "protocol_type": "http",
                "clients": 0,  # HTTP doesn't maintain persistent connections
            }
        
        return status


class TraccarProtocolServerWrapper(ProtocolServer):
    """
    Wrapper for protocol server that integrates with Traccar database and WebSocket.
    """
    
    def __init__(self, protocol_handler: BaseProtocolHandler, host: str, port: int, protocol_type: str = "tcp"):
        super().__init__(protocol_handler, host, port)
        self.protocol_type = protocol_type
        self.logger = logging.getLogger(f"{__name__}.{protocol_handler.PROTOCOL_NAME}")
    
    async def handle_parsed_message(self, message: ProtocolMessage, client_address: tuple):
        """Handle parsed protocol message with database integration."""
        if not message.valid:
            return
        
        try:
            # Get database session
            db = next(get_db())
            
            # Find device by unique_id
            device = db.query(Device).filter(Device.unique_id == message.device_id).first()
            if not device:
                self.logger.warning(f"Device not found: {message.device_id}")
                return
            
            # Create position if available
            position_data = await self.protocol_handler.create_position(message)
            if position_data:
                await self._create_position(db, device, position_data, message)
            
            # Create events if available
            events_data = await self.protocol_handler.create_events(message)
            for event_data in events_data:
                await self._create_event(db, device, event_data, message)
            
            # Update device last update time
            device.last_update = datetime.utcnow()
            db.commit()
            
            self.logger.info(f"Processed message for device {device.name} ({device.unique_id})")
            
        except Exception as e:
            self.logger.error(f"Error handling parsed message: {e}")
        finally:
            db.close()
    
    async def _create_position(self, db: Session, device: Device, position_data: Dict[str, Any], message: ProtocolMessage):
        """Create position in database and broadcast via WebSocket."""
        try:
            # Create position
            position = Position(
                device_id=device.id,
                latitude=position_data.get('latitude'),
                longitude=position_data.get('longitude'),
                altitude=position_data.get('altitude'),
                speed=position_data.get('speed'),
                course=position_data.get('course'),
                address=position_data.get('address'),
                valid=position_data.get('valid', True),
                device_time=position_data.get('device_time'),
                server_time=datetime.utcnow(),
                attributes=position_data.get('attributes', {})
            )
            
            db.add(position)
            db.commit()
            db.refresh(position)
            
            # Update device position
            device.position_id = position.id
            device.last_update = datetime.utcnow()
            
            # Broadcast position update via WebSocket
            await websocket_service.broadcast_position_update(position, device)
            
            self.logger.info(f"Created position for device {device.name}")
            
        except Exception as e:
            self.logger.error(f"Error creating position: {e}")
    
    async def _create_event(self, db: Session, device: Device, event_data: Dict[str, Any], message: ProtocolMessage):
        """Create event in database and broadcast via WebSocket."""
        try:
            # Create event
            event = Event(
                device_id=device.id,
                type=event_data.get('type'),
                event_time=event_data.get('event_time', datetime.utcnow()),
                server_time=datetime.utcnow(),
                position_id=device.position_id,
                geofence_id=event_data.get('geofence_id'),
                maintenance_id=event_data.get('maintenance_id'),
                attributes=event_data.get('attributes', {})
            )
            
            db.add(event)
            db.commit()
            db.refresh(event)
            
            # Broadcast event via WebSocket
            await websocket_service.broadcast_event_update(event, device)
            
            self.logger.info(f"Created event {event.type} for device {device.name}")
            
        except Exception as e:
            self.logger.error(f"Error creating event: {e}")


# Global protocol server instance
protocol_server_manager = TraccarProtocolServer()


async def start_protocol_servers():
    """Start all protocol servers."""
    await protocol_server_manager.start_all_servers()


async def stop_protocol_servers():
    """Stop all protocol servers."""
    await protocol_server_manager.stop_all_servers()


def get_protocol_server_status() -> Dict[str, Dict[str, Any]]:
    """Get protocol server status."""
    return protocol_server_manager.get_server_status()


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
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.protocol_handlers: Dict[str, BaseProtocolHandler] = {}
        self.protocol_servers: Dict[str, ProtocolServer] = {}
        self.http_servers: Dict[str, HTTPProtocolServer] = {}
        self.running = False
        self.tasks: List[asyncio.Task] = []
        self.config = config or {}
        
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
        if protocol_type.lower() == "http" or protocol_name == "osmand":
            server = HTTPProtocolServer(handler, host, port)
            self.http_servers[protocol_name] = server
            await server.start()
            logger.info(f"Started HTTP server for {protocol_name} on {host}:{port}")
        else:
            # TCP/UDP protocols
            server = TraccarProtocolServerWrapper(handler, host, port, protocol_type)
            server_key = f"{protocol_name}_{protocol_type}"
            self.protocol_servers[server_key] = server
            
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
            "suntech": 5011,
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
                # Check if protocol supports multiple transport protocols
                protocol_config = self.config.get('PROTOCOL_SERVERS', {}).get(protocol_name, {})
                
                if 'protocols' in protocol_config:
                    # Multiple protocols (e.g., ["tcp", "udp"])
                    protocols = protocol_config['protocols']
                    port = protocol_config.get('port', self._get_default_port(protocol_name))
                    
                    for protocol_type in protocols:
                        await self.start_protocol_server(protocol_name, host, port, protocol_type)
                elif 'protocol' in protocol_config:
                    # Single protocol with explicit type
                    protocol_type = protocol_config['protocol']
                    port = protocol_config.get('port', self._get_default_port(protocol_name))
                    await self.start_protocol_server(protocol_name, host, port, protocol_type)
                else:
                    # Single protocol (backward compatibility)
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
            self.logger.info(f"Received message for device: {message.device_id}")
            
            # Create position if available
            position_data = await self.protocol_handler.create_position(message)
            if position_data:
                self.logger.info(f"Position created for device {message.device_id}: {position_data}")
                
                # Save position to database
                await self._save_position_to_database(position_data, message)
            
            # Create events if available
            events_data = await self.protocol_handler.create_events(message)
            for event_data in events_data:
                self.logger.info(f"Event created for device {message.device_id}: {event_data}")
                
                # Save event to database
                await self._save_event_to_database(event_data, message)
            
        except Exception as e:
            self.logger.error(f"Error handling parsed message: {e}")
    
    async def _save_position_to_database(self, position_data: Dict[str, Any], message: ProtocolMessage):
        """Save position to database."""
        try:
            from app.database import AsyncSessionLocal
            from app.models.position import Position
            from app.models.unknown_device import UnknownDevice
            from sqlalchemy import select
            
            async with AsyncSessionLocal() as db:
                # Check if this is an unknown device by looking up the device_id in the message data
                # The message.device_id is actually the unknown device's database ID
                result = await db.execute(
                    select(UnknownDevice).where(UnknownDevice.id == message.device_id)
                )
                unknown_device = result.scalar_one_or_none()
                
                if unknown_device:
                    # Create position for unknown device
                    import json
                    attributes = position_data.get('attributes', {})
                    if isinstance(attributes, dict):
                        attributes = json.dumps(attributes)
                    
                    position = Position(
                        device_id=None,  # No registered device
                        unknown_device_id=unknown_device.id,  # Use unknown device ID
                        protocol=position_data.get('protocol', self.protocol_handler.PROTOCOL_NAME),
                        server_time=position_data.get('server_time'),
                        device_time=position_data.get('device_time'),
                        fix_time=position_data.get('fix_time'),
                        latitude=position_data.get('latitude'),
                        longitude=position_data.get('longitude'),
                        altitude=position_data.get('altitude', 0.0),
                        speed=position_data.get('speed', 0.0),
                        course=position_data.get('course', 0.0),
                        address=position_data.get('address'),
                        accuracy=position_data.get('accuracy'),
                        valid=position_data.get('valid', True),
                        attributes=attributes
                    )
                    
                    db.add(position)
                    await db.commit()
                    await db.refresh(position)
                    
                    self.logger.info(f"Position saved for unknown device {message.device_id}: ID {position.id}")
                    
                    # Broadcast position update via WebSocket
                    try:
                        from app.services.websocket_service import websocket_service
                        await websocket_service.broadcast_position_update(position, None)
                    except Exception as e:
                        self.logger.error(f"Failed to broadcast position update: {e}")
                
        except Exception as e:
            self.logger.error(f"Error saving position to database: {e}")
    
    async def _save_event_to_database(self, event_data: Dict[str, Any], message: ProtocolMessage):
        """Save event to database."""
        try:
            from app.database import AsyncSessionLocal
            from app.models.event import Event
            from app.models.unknown_device import UnknownDevice
            from sqlalchemy import select
            
            async with AsyncSessionLocal() as db:
                # Check if this is an unknown device by looking up the device_id in the message data
                # The message.device_id is actually the unknown device's database ID
                result = await db.execute(
                    select(UnknownDevice).where(UnknownDevice.id == message.device_id)
                )
                unknown_device = result.scalar_one_or_none()
                
                if unknown_device:
                    # Create event for unknown device
                    import json
                    event_attributes = event_data.get('attributes', {})
                    if isinstance(event_attributes, dict):
                        event_attributes = json.dumps(event_attributes)
                    
                    event = Event(
                        device_id=unknown_device.id,  # Use unknown device ID
                        type=event_data.get('type'),
                        event_time=event_data.get('timestamp'),
                        server_time=event_data.get('server_time'),
                        position_id=event_data.get('position_id'),
                        geofence_id=event_data.get('geofence_id'),
                        attributes=event_attributes
                    )
                    
                    db.add(event)
                    await db.commit()
                    await db.refresh(event)
                    
                    self.logger.info(f"Event saved for unknown device {message.device_id}: {event.type}")
                    
                    # Broadcast event update via WebSocket
                    try:
                        from app.services.websocket_service import websocket_service
                        await websocket_service.broadcast_event_update(event, None)
                    except Exception as e:
                        self.logger.error(f"Failed to broadcast event update: {e}")
                
        except Exception as e:
            self.logger.error(f"Error saving event to database: {e}")
    
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


# Global protocol server instance - will be initialized with config in start_protocol_servers
protocol_server_manager = None


async def start_protocol_servers():
    """Start all protocol servers."""
    global protocol_server_manager
    
    if protocol_server_manager is None:
        from app.config import settings
        config = {
            'PROTOCOL_SERVERS': settings.PROTOCOL_SERVERS
        }
        protocol_server_manager = TraccarProtocolServer(config)
    
    await protocol_server_manager.start_all_servers()


async def stop_protocol_servers():
    """Stop all protocol servers."""
    global protocol_server_manager
    
    if protocol_server_manager is not None:
        await protocol_server_manager.stop_all_servers()


def get_protocol_server_status() -> Dict[str, Dict[str, Any]]:
    """Get protocol server status."""
    global protocol_server_manager
    
    if protocol_server_manager is None:
        return {}
    
    return protocol_server_manager.get_server_status()


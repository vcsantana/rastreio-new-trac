"""
Base protocol handler for GPS tracking protocols.
"""

import asyncio
import logging
from abc import ABC, abstractmethod
from datetime import datetime
from typing import Optional, Dict, Any, List, Tuple
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class ProtocolMessage:
    """Represents a parsed protocol message."""
    device_id: str
    message_type: str
    data: Dict[str, Any]
    timestamp: datetime
    raw_data: bytes
    valid: bool = True
    error: Optional[str] = None


class BaseProtocolHandler(ABC):
    """
    Base class for all GPS protocol handlers.
    """
    
    PROTOCOL_NAME: str = "base"
    SUPPORTED_MESSAGE_TYPES: List[str] = []
    
    def __init__(self):
        self.logger = logging.getLogger(f"{__name__}.{self.PROTOCOL_NAME}")
    
    @abstractmethod
    async def parse_message(self, data: bytes, client_address: Tuple[str, int]) -> Optional[ProtocolMessage]:
        """
        Parse incoming message data.
        
        Args:
            data: Raw message data
            client_address: Client address tuple (host, port)
            
        Returns:
            Parsed ProtocolMessage or None if invalid
        """
        pass
    
    @abstractmethod
    async def create_position(self, message: ProtocolMessage) -> Optional[Dict[str, Any]]:
        """
        Create position data from parsed message.
        
        Args:
            message: Parsed protocol message
            
        Returns:
            Position data dictionary or None
        """
        pass
    
    @abstractmethod
    async def create_events(self, message: ProtocolMessage) -> List[Dict[str, Any]]:
        """
        Create events from parsed message.
        
        Args:
            message: Parsed protocol message
            
        Returns:
            List of event data dictionaries
        """
        pass
    
    def validate_device_id(self, device_id: str) -> bool:
        """Validate device ID format."""
        return device_id and len(device_id.strip()) > 0
    
    def validate_coordinates(self, latitude: float, longitude: float) -> bool:
        """Validate GPS coordinates."""
        return (-90 <= latitude <= 90) and (-180 <= longitude <= 180)
    
    def log_message(self, message: ProtocolMessage, client_address: Tuple[str, int]):
        """Log protocol message."""
        self.logger.info(
            f"Parsed {self.PROTOCOL_NAME} message",
            device_id=message.device_id,
            message_type=message.message_type,
            client_address=client_address,
            valid=message.valid
        )
    
    def log_error(self, error: str, data: bytes, client_address: Tuple[str, int]):
        """Log protocol error."""
        self.logger.error(
            f"Protocol error in {self.PROTOCOL_NAME}",
            error=error,
            client_address=client_address,
            data_length=len(data)
        )


class ProtocolServer:
    """
    Base protocol server for TCP/UDP connections.
    """
    
    def __init__(self, protocol_handler: BaseProtocolHandler, host: str = "0.0.0.0", port: int = 5001):
        self.protocol_handler = protocol_handler
        self.host = host
        self.port = port
        self.logger = logging.getLogger(f"{__name__}.{protocol_handler.PROTOCOL_NAME}_server")
        self.clients: Dict[Tuple[str, int], Dict[str, Any]] = {}
        self.server = None
        self.running = False
    
    async def start_tcp_server(self):
        """Start TCP server."""
        try:
            self.server = await asyncio.start_server(
                self.handle_tcp_client,
                self.host,
                self.port
            )
            self.running = True
            self.logger.info(f"TCP server started on {self.host}:{self.port}")
            
            async with self.server:
                await self.server.serve_forever()
                
        except Exception as e:
            self.logger.error(f"Failed to start TCP server: {e}")
            raise
    
    async def start_udp_server(self):
        """Start UDP server."""
        try:
            self.server = await asyncio.get_event_loop().create_datagram_endpoint(
                lambda: UDPProtocol(self.handle_udp_message),
                local_addr=(self.host, self.port)
            )
            self.running = True
            self.logger.info(f"UDP server started on {self.host}:{self.port}")
            
            # Keep server running
            while self.running:
                await asyncio.sleep(1)
                
        except Exception as e:
            self.logger.error(f"Failed to start UDP server: {e}")
            raise
    
    async def handle_tcp_client(self, reader: asyncio.StreamReader, writer: asyncio.StreamWriter):
        """Handle TCP client connection."""
        client_address = writer.get_extra_info('peername')
        self.logger.info(f"TCP client connected: {client_address}")
        
        try:
            while True:
                data = await reader.read(1024)
                if not data:
                    break
                
                await self.process_message(data, client_address)
                
        except Exception as e:
            self.logger.error(f"TCP client error: {e}")
        finally:
            writer.close()
            await writer.wait_closed()
            self.logger.info(f"TCP client disconnected: {client_address}")
    
    async def handle_udp_message(self, data: bytes, addr: Tuple[str, int]):
        """Handle UDP message."""
        await self.process_message(data, addr)
    
    async def process_message(self, data: bytes, client_address: Tuple[str, int]):
        """Process incoming message."""
        try:
            message = await self.protocol_handler.parse_message(data, client_address)
            if message:
                self.protocol_handler.log_message(message, client_address)
                await self.handle_parsed_message(message, client_address)
            else:
                self.logger.warning(f"Failed to parse message from {client_address}")
                
        except Exception as e:
            self.logger.error(f"Error processing message from {client_address}: {e}")
    
    async def handle_parsed_message(self, message: ProtocolMessage, client_address: Tuple[str, int]):
        """Handle parsed protocol message."""
        # This method should be overridden by subclasses to handle
        # position creation, event generation, etc.
        pass
    
    async def stop(self):
        """Stop the server."""
        self.running = False
        if self.server:
            self.server.close()
            await self.server.wait_closed()
        self.logger.info("Protocol server stopped")


class UDPProtocol(asyncio.DatagramProtocol):
    """UDP protocol handler."""
    
    def __init__(self, message_handler):
        self.message_handler = message_handler
        self.logger = logging.getLogger(__name__)
    
    def datagram_received(self, data: bytes, addr: Tuple[str, int]):
        """Handle received UDP datagram."""
        asyncio.create_task(self.message_handler(data, addr))
    
    def error_received(self, exc: Exception):
        """Handle UDP error."""
        self.logger.error(f"UDP error: {exc}")
    
    def connection_lost(self, exc: Optional[Exception]):
        """Handle connection lost."""
        if exc:
            self.logger.error(f"UDP connection lost: {exc}")
        else:
            self.logger.info("UDP connection closed")


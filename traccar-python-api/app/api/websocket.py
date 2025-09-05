"""
WebSocket API for real-time updates
"""
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import Dict, List, Optional, Set
import json
import asyncio
import logging
from datetime import datetime, timedelta
from enum import Enum

from app.database import get_db
from app.models import User, Device, Position, Event
from app.api.auth import get_current_user

logger = logging.getLogger(__name__)

router = APIRouter()

class MessageType(str, Enum):
    """WebSocket message types."""
    POSITION = "position"
    EVENT = "event"
    DEVICE_STATUS = "device_status"
    HEARTBEAT = "heartbeat"
    ERROR = "error"
    INFO = "info"

class ConnectionManager:
    def __init__(self):
        self.active_connections: Dict[int, List[WebSocket]] = {}
        self.connection_info: Dict[WebSocket, Dict] = {}
        self.subscriptions: Dict[int, Set[str]] = {}  # user_id -> set of subscription types
    
    async def connect(self, websocket: WebSocket, user_id: int, user_info: dict = None):
        await websocket.accept()
        if user_id not in self.active_connections:
            self.active_connections[user_id] = []
            self.subscriptions[user_id] = set()
        
        self.active_connections[user_id].append(websocket)
        self.connection_info[websocket] = {
            "user_id": user_id,
            "connected_at": datetime.utcnow(),
            "last_heartbeat": datetime.utcnow(),
            "user_info": user_info or {}
        }
        
        logger.info(f"WebSocket connected for user {user_id}")
        
        # Send welcome message
        await self.send_personal_message({
            "type": MessageType.INFO,
            "data": {
                "message": "Connected to Traccar WebSocket",
                "timestamp": datetime.utcnow().isoformat(),
                "user_id": user_id
            }
        }, user_id)
    
    def disconnect(self, websocket: WebSocket, user_id: int):
        if user_id in self.active_connections:
            self.active_connections[user_id].remove(websocket)
            if not self.active_connections[user_id]:
                del self.active_connections[user_id]
                if user_id in self.subscriptions:
                    del self.subscriptions[user_id]
        
        if websocket in self.connection_info:
            del self.connection_info[websocket]
        
        logger.info(f"WebSocket disconnected for user {user_id}")
    
    async def send_personal_message(self, message: dict, user_id: int):
        """Send message to specific user."""
        if user_id in self.active_connections:
            broken_connections = []
            for connection in self.active_connections[user_id]:
                try:
                    await connection.send_text(json.dumps(message))
                except Exception as e:
                    logger.warning(f"Failed to send message to user {user_id}: {e}")
                    broken_connections.append(connection)
            
            # Remove broken connections
            for connection in broken_connections:
                self.active_connections[user_id].remove(connection)
                if connection in self.connection_info:
                    del self.connection_info[connection]
    
    async def broadcast_to_subscribers(self, message: dict, subscription_type: str):
        """Broadcast message to users subscribed to specific type."""
        for user_id, subscriptions in self.subscriptions.items():
            if subscription_type in subscriptions:
                await self.send_personal_message(message, user_id)
    
    async def broadcast_position(self, position_data: dict, device_id: int = None):
        """Broadcast position update to subscribed clients."""
        message = {
            "type": MessageType.POSITION,
            "data": position_data,
            "timestamp": datetime.utcnow().isoformat()
        }
        
        if device_id:
            # Send to users who have access to this device
            await self.broadcast_to_subscribers(message, f"device_{device_id}")
        else:
            # Broadcast to all position subscribers
            await self.broadcast_to_subscribers(message, "positions")
    
    async def broadcast_event(self, event_data: dict, device_id: int = None):
        """Broadcast event to subscribed clients."""
        message = {
            "type": MessageType.EVENT,
            "data": event_data,
            "timestamp": datetime.utcnow().isoformat()
        }
        
        if device_id:
            await self.broadcast_to_subscribers(message, f"device_{device_id}")
        else:
            await self.broadcast_to_subscribers(message, "events")
    
    async def broadcast_device_status(self, device_data: dict, device_id: int):
        """Broadcast device status change."""
        message = {
            "type": MessageType.DEVICE_STATUS,
            "data": device_data,
            "timestamp": datetime.utcnow().isoformat()
        }
        
        await self.broadcast_to_subscribers(message, f"device_{device_id}")
        await self.broadcast_to_subscribers(message, "devices")
    
    def subscribe(self, user_id: int, subscription_type: str):
        """Subscribe user to specific updates."""
        if user_id not in self.subscriptions:
            self.subscriptions[user_id] = set()
        self.subscriptions[user_id].add(subscription_type)
        logger.info(f"User {user_id} subscribed to {subscription_type}")
    
    def unsubscribe(self, user_id: int, subscription_type: str):
        """Unsubscribe user from specific updates."""
        if user_id in self.subscriptions:
            self.subscriptions[user_id].discard(subscription_type)
            logger.info(f"User {user_id} unsubscribed from {subscription_type}")
    
    def get_connection_stats(self) -> dict:
        """Get connection statistics."""
        total_connections = sum(len(connections) for connections in self.active_connections.values())
        return {
            "total_users": len(self.active_connections),
            "total_connections": total_connections,
            "subscriptions": {user_id: list(subs) for user_id, subs in self.subscriptions.items()}
        }

# Global connection manager
manager = ConnectionManager()

@router.websocket("/ws/{user_id}")
async def websocket_endpoint(websocket: WebSocket, user_id: int):
    """WebSocket endpoint for real-time updates."""
    await manager.connect(websocket, user_id)
    try:
        while True:
            # Handle incoming messages
            data = await websocket.receive_text()
            try:
                message = json.loads(data)
                await handle_websocket_message(websocket, user_id, message)
            except json.JSONDecodeError:
                # Handle non-JSON messages (like heartbeat)
                if data == "ping":
                    await websocket.send_text("pong")
                else:
                    await websocket.send_text(json.dumps({
                        "type": MessageType.ERROR,
                        "data": {"message": "Invalid JSON format"}
                    }))
    except WebSocketDisconnect:
        manager.disconnect(websocket, user_id)
    except Exception as e:
        logger.error(f"WebSocket error for user {user_id}: {e}")
        manager.disconnect(websocket, user_id)


async def handle_websocket_message(websocket: WebSocket, user_id: int, message: dict):
    """Handle incoming WebSocket messages."""
    message_type = message.get("type")
    data = message.get("data", {})
    
    if message_type == "subscribe":
        subscription_type = data.get("type")
        if subscription_type:
            manager.subscribe(user_id, subscription_type)
            await websocket.send_text(json.dumps({
                "type": MessageType.INFO,
                "data": {"message": f"Subscribed to {subscription_type}"}
            }))
    
    elif message_type == "unsubscribe":
        subscription_type = data.get("type")
        if subscription_type:
            manager.unsubscribe(user_id, subscription_type)
            await websocket.send_text(json.dumps({
                "type": MessageType.INFO,
                "data": {"message": f"Unsubscribed from {subscription_type}"}
            }))
    
    elif message_type == "heartbeat":
        # Update last heartbeat time
        if websocket in manager.connection_info:
            manager.connection_info[websocket]["last_heartbeat"] = datetime.utcnow()
        await websocket.send_text(json.dumps({
            "type": MessageType.HEARTBEAT,
            "data": {"timestamp": datetime.utcnow().isoformat()}
        }))
    
    elif message_type == "get_stats":
        stats = manager.get_connection_stats()
        await websocket.send_text(json.dumps({
            "type": MessageType.INFO,
            "data": {"stats": stats}
        }))
    
    else:
        await websocket.send_text(json.dumps({
            "type": MessageType.ERROR,
            "data": {"message": f"Unknown message type: {message_type}"}
        }))


@router.get("/ws/stats")
async def get_websocket_stats():
    """Get WebSocket connection statistics."""
    return manager.get_connection_stats()


@router.post("/ws/broadcast")
async def broadcast_message(
    message_type: str,
    data: dict,
    subscription_type: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Broadcast message to WebSocket subscribers (admin only)."""
    if not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required"
        )
    
    message = {
        "type": message_type,
        "data": data,
        "timestamp": datetime.utcnow().isoformat()
    }
    
    if subscription_type:
        await manager.broadcast_to_subscribers(message, subscription_type)
    else:
        # Broadcast to all connected users
        for user_id in manager.active_connections.keys():
            await manager.send_personal_message(message, user_id)
    
    return {"message": "Broadcast sent successfully"}


@router.post("/ws/test-position")
async def test_position_broadcast(
    device_id: int,
    latitude: float,
    longitude: float,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Test position broadcast (for development)."""
    if not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required"
        )
    
    # Get device info
    result = await db.execute(select(Device).where(Device.id == device_id))
    device = result.scalar_one_or_none()
    if not device:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Device not found"
        )
    
    position_data = {
        "device_id": device_id,
        "device_name": device.name,
        "latitude": latitude,
        "longitude": longitude,
        "altitude": 0,
        "speed": 0,
        "course": 0,
        "address": "Test Location",
        "valid": True,
        "device_time": datetime.utcnow().isoformat(),
        "server_time": datetime.utcnow().isoformat()
    }
    
    await manager.broadcast_position(position_data, device_id)
    
    return {"message": "Test position broadcast sent", "data": position_data}


@router.post("/ws/test-event")
async def test_event_broadcast(
    device_id: int,
    event_type: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Test event broadcast (for development)."""
    if not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required"
        )
    
    # Get device info
    result = await db.execute(select(Device).where(Device.id == device_id))
    device = result.scalar_one_or_none()
    if not device:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Device not found"
        )
    
    event_data = {
        "device_id": device_id,
        "device_name": device.name,
        "type": event_type,
        "event_time": datetime.utcnow().isoformat(),
        "server_time": datetime.utcnow().isoformat(),
        "attributes": {}
    }
    
    await manager.broadcast_event(event_data, device_id)
    
    return {"message": "Test event broadcast sent", "data": event_data}


@router.post("/ws/test-device-status")
async def test_device_status_broadcast(
    device_id: int,
    new_status: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Test device status broadcast (for development)."""
    if not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required"
        )
    
    # Get device info
    result = await db.execute(select(Device).where(Device.id == device_id))
    device = result.scalar_one_or_none()
    if not device:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Device not found"
        )
    
    old_status = device.status
    device.status = new_status
    device.last_update = datetime.utcnow()
    await db.commit()
    
    device_data = {
        "id": device_id,
        "name": device.name,
        "unique_id": device.unique_id,
        "status": new_status,
        "last_update": device.last_update.isoformat(),
        "position_id": device.position_id,
        "attributes": device.attributes or {},
        "old_status": old_status
    }
    
    await manager.broadcast_device_status(device_data, device_id)
    
    return {"message": "Test device status broadcast sent", "data": device_data}


@router.post("/ws/simulate-gps-data")
async def simulate_gps_data(
    device_id: int,
    latitude: float,
    longitude: float,
    speed: float = 0.0,
    course: float = 0.0,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Simulate GPS data and broadcast via WebSocket (for development)."""
    if not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required"
        )
    
    # Get device info
    result = await db.execute(select(Device).where(Device.id == device_id))
    device = result.scalar_one_or_none()
    if not device:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Device not found"
        )
    
    # Create a new position
    position = Position(
        device_id=device_id,
        protocol="simulation",
        latitude=latitude,
        longitude=longitude,
        altitude=0.0,
        speed=speed,
        course=course,
        valid=True,
        device_time=datetime.utcnow(),
        server_time=datetime.utcnow(),
        address="Simulated Location"
    )
    
    db.add(position)
    await db.commit()
    await db.refresh(position)
    
    # Broadcast position update
    position_data = {
        "id": position.id,
        "device_id": device_id,
        "device_name": device.name,
        "latitude": float(latitude),
        "longitude": float(longitude),
        "altitude": 0.0,
        "speed": float(speed),
        "course": float(course),
        "address": "Simulated Location",
        "valid": True,
        "device_time": position.device_time.isoformat(),
        "server_time": position.server_time.isoformat(),
        "attributes": {}
    }
    
    await manager.broadcast_position(position_data, device_id)
    
    return {"message": "GPS data simulated and broadcast", "data": position_data}

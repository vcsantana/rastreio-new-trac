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


@router.post("/ws/simulate-gps-data")
async def simulate_gps_data(
    device_id: int = 1,
    count: int = 10,
    interval_seconds: float = 2.0,
    db: AsyncSession = Depends(get_db)
):
    """Simulate GPS data for testing WebSocket integration."""
    import asyncio
    from app.services.websocket_service import websocket_service
    from app.models import Position, Device
    from sqlalchemy import select
    from datetime import datetime, timedelta
    import random
    
    try:
        # Get device
        result = await db.execute(select(Device).where(Device.id == device_id))
        device = result.scalar_one_or_none()
        if not device:
            raise HTTPException(status_code=404, detail=f"Device {device_id} not found")
        
        # Simulate GPS positions
        base_lat = -23.5505  # São Paulo coordinates
        base_lon = -46.6333
        
        for i in range(count):
            # Generate random position around base coordinates
            lat = base_lat + random.uniform(-0.01, 0.01)
            lon = base_lon + random.uniform(-0.01, 0.01)
            
            # Create position
            position = Position(
                device_id=device_id,
                protocol="simulation",
                latitude=lat,
                longitude=lon,
                altitude=random.uniform(700, 800),
                speed=random.uniform(0, 60),
                course=random.uniform(0, 360),
                valid=True,
                device_time=datetime.utcnow(),
                server_time=datetime.utcnow(),
                address=f"Simulated Address {i+1}",
                attributes=f'{{"simulated": true, "test_run": {i+1}}}'
            )
            
            db.add(position)
            await db.commit()
            await db.refresh(position)
            
            # Broadcast via WebSocket
            await websocket_service.broadcast_position_update(position, device)
            
            # Wait before next position
            if i < count - 1:
                await asyncio.sleep(interval_seconds)
        
        return {
            "message": f"Simulated {count} GPS positions for device {device_id}",
            "device_id": device_id,
            "positions_created": count,
            "interval_seconds": interval_seconds
        }
        
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to simulate GPS data: {str(e)}")


@router.post("/ws/test-position")
async def test_position_broadcast(device_id: int = 1, db: AsyncSession = Depends(get_db)):
    """Test position broadcast via WebSocket."""
    from app.services.websocket_service import websocket_service
    from app.models import Position, Device
    from sqlalchemy import select
    from datetime import datetime
    import random
    
    try:
        # Get device
        result = await db.execute(select(Device).where(Device.id == device_id))
        device = result.scalar_one_or_none()
        if not device:
            raise HTTPException(status_code=404, detail=f"Device {device_id} not found")
        
        # Create test position
        position = Position(
            device_id=device_id,
            protocol="test",
            latitude=-23.5505 + random.uniform(-0.001, 0.001),
            longitude=-46.6333 + random.uniform(-0.001, 0.001),
            altitude=750.0,
            speed=45.5,
            course=180.0,
            valid=True,
            device_time=datetime.utcnow(),
            server_time=datetime.utcnow(),
            address="Test Position",
            attributes='{"test": true}'
        )
        
        db.add(position)
        await db.commit()
        await db.refresh(position)
        
        # Broadcast via WebSocket
        await websocket_service.broadcast_position_update(position, device)
        
        return {
            "message": "Test position broadcasted successfully",
            "position_id": position.id,
            "device_id": device_id,
            "latitude": position.latitude,
            "longitude": position.longitude
        }
        
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to test position broadcast: {str(e)}")


@router.post("/ws/test-event")
async def test_event_broadcast(device_id: int = 1, event_type: str = "deviceOnline", db: AsyncSession = Depends(get_db)):
    """Test event broadcast via WebSocket."""
    from app.services.websocket_service import websocket_service
    from app.models import Event, Device
    from sqlalchemy import select
    from datetime import datetime
    
    try:
        # Get device
        result = await db.execute(select(Device).where(Device.id == device_id))
        device = result.scalar_one_or_none()
        if not device:
            raise HTTPException(status_code=404, detail=f"Device {device_id} not found")
        
        # Create test event
        event = Event(
            type=event_type,
            device_id=device_id,
            event_time=datetime.utcnow(),
            attributes='{"test": true, "simulated": true}'
        )
        
        db.add(event)
        await db.commit()
        await db.refresh(event)
        
        # Broadcast via WebSocket
        await websocket_service.broadcast_event_update(event, device)
        
        return {
            "message": "Test event broadcasted successfully",
            "event_id": event.id,
            "device_id": device_id,
            "event_type": event_type
        }
        
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to test event broadcast: {str(e)}")


@router.post("/ws/test-device-status")
async def test_device_status_broadcast(device_id: int = 1, new_status: str = "online", db: AsyncSession = Depends(get_db)):
    """Test device status broadcast via WebSocket."""
    from app.services.websocket_service import websocket_service
    from app.models import Device
    from sqlalchemy import select
    from datetime import datetime
    
    try:
        # Get device
        result = await db.execute(select(Device).where(Device.id == device_id))
        device = result.scalar_one_or_none()
        if not device:
            raise HTTPException(status_code=404, detail=f"Device {device_id} not found")
        
        # Store old status
        old_status = device.status
        
        # Update device status
        device.status = new_status
        device.last_update = datetime.utcnow()
        
        await db.commit()
        await db.refresh(device)
        
        # Broadcast via WebSocket
        await websocket_service.broadcast_device_status_update(device, old_status)
        
        return {
            "message": "Test device status broadcasted successfully",
            "device_id": device_id,
            "old_status": old_status,
            "new_status": new_status
        }
        
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to test device status broadcast: {str(e)}")

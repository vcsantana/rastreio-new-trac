"""
WebSocket service for real-time updates integration.
"""

from typing import Dict, Any, Optional
from datetime import datetime
import logging

from app.api.websocket import manager, MessageType
from app.models import Device, Position, Event

logger = logging.getLogger(__name__)


class WebSocketService:
    """Service for handling WebSocket real-time updates."""
    
    @staticmethod
    async def broadcast_position_update(position: Position, device: Device = None):
        """Broadcast position update to WebSocket subscribers."""
        try:
            position_data = {
                "id": position.id,
                "device_id": position.device_id,
                "device_name": device.name if device else f"Device {position.device_id}",
                "latitude": float(position.latitude),
                "longitude": float(position.longitude),
                "altitude": float(position.altitude) if position.altitude else 0,
                "speed": float(position.speed) if position.speed else 0,
                "course": float(position.course) if position.course else 0,
                "address": position.address or "",
                "valid": position.valid,
                "device_time": position.device_time.isoformat() if position.device_time else None,
                "server_time": position.server_time.isoformat() if position.server_time else None,
                "attributes": position.attributes or {}
            }
            
            await manager.broadcast_position(position_data, position.device_id)
            logger.info(f"Broadcasted position update for device {position.device_id}")
            
        except Exception as e:
            logger.error(f"Failed to broadcast position update: {e}")
    
    @staticmethod
    async def broadcast_event_update(event: Event, device: Device = None):
        """Broadcast event update to WebSocket subscribers."""
        try:
            event_data = {
                "id": event.id,
                "device_id": event.device_id,
                "device_name": device.name if device else f"Device {event.device_id}",
                "type": event.type,
                "event_time": event.event_time.isoformat() if event.event_time else None,
                "server_time": event.server_time.isoformat() if event.server_time else None,
                "position_id": event.position_id,
                "geofence_id": event.geofence_id,
                "attributes": event.attributes or {}
            }
            
            await manager.broadcast_event(event_data, event.device_id)
            logger.info(f"Broadcasted event update for device {event.device_id}: {event.type}")
            
        except Exception as e:
            logger.error(f"Failed to broadcast event update: {e}")
    
    @staticmethod
    async def broadcast_device_status_update(device: Device, old_status: str = None):
        """Broadcast device status change to WebSocket subscribers."""
        try:
            device_data = {
                "id": device.id,
                "name": device.name,
                "unique_id": device.unique_id,
                "status": device.status,
                "last_update": device.last_update.isoformat() if device.last_update else None,
                "position_id": device.position_id,
                "attributes": device.attributes or {},
                "old_status": old_status
            }
            
            await manager.broadcast_device_status(device_data, device.id)
            logger.info(f"Broadcasted device status update for device {device.id}: {old_status} -> {device.status}")
            
        except Exception as e:
            logger.error(f"Failed to broadcast device status update: {e}")
    
    @staticmethod
    async def broadcast_unknown_device_update(unknown_device_data: Dict[str, Any]):
        """Broadcast unknown device update to WebSocket subscribers."""
        try:
            await manager.broadcast_to_subscribers({
                "type": "unknown_device",
                "data": unknown_device_data,
                "timestamp": datetime.utcnow().isoformat()
            }, "unknown_devices")
            logger.info(f"Broadcasted unknown device update for device {unknown_device_data.get('unique_id')}")
            
        except Exception as e:
            logger.error(f"Failed to broadcast unknown device update: {e}")
    
    @staticmethod
    async def broadcast_system_notification(message: str, notification_type: str = "info", user_id: Optional[int] = None):
        """Broadcast system notification to WebSocket subscribers."""
        try:
            notification_data = {
                "message": message,
                "type": notification_type,
                "timestamp": datetime.utcnow().isoformat()
            }
            
            if user_id:
                await manager.send_personal_message({
                    "type": MessageType.INFO,
                    "data": notification_data
                }, user_id)
            else:
                # Broadcast to all connected users
                for uid in manager.active_connections.keys():
                    await manager.send_personal_message({
                        "type": MessageType.INFO,
                        "data": notification_data
                    }, uid)
            
            logger.info(f"Broadcasted system notification: {message}")
            
        except Exception as e:
            logger.error(f"Failed to broadcast system notification: {e}")
    
    @staticmethod
    async def broadcast_geofence_alert(device: Device, geofence_name: str, event_type: str, position: Position = None):
        """Broadcast geofence alert to WebSocket subscribers."""
        try:
            alert_data = {
                "device_id": device.id,
                "device_name": device.name,
                "geofence_name": geofence_name,
                "event_type": event_type,  # "enter" or "exit"
                "latitude": float(position.latitude) if position else None,
                "longitude": float(position.longitude) if position else None,
                "timestamp": datetime.utcnow().isoformat()
            }
            
            await manager.broadcast_to_subscribers({
                "type": MessageType.EVENT,
                "data": {
                    "type": "geofence_alert",
                    "data": alert_data
                }
            }, f"device_{device.id}")
            
            # Also broadcast to general geofence subscribers
            await manager.broadcast_to_subscribers({
                "type": MessageType.EVENT,
                "data": {
                    "type": "geofence_alert",
                    "data": alert_data
                }
            }, "geofences")
            
            logger.info(f"Broadcasted geofence alert for device {device.id}: {event_type} {geofence_name}")
            
        except Exception as e:
            logger.error(f"Failed to broadcast geofence alert: {e}")
    
    @staticmethod
    async def broadcast_maintenance_reminder(device: Device, maintenance_type: str, due_date: datetime):
        """Broadcast maintenance reminder to WebSocket subscribers."""
        try:
            reminder_data = {
                "device_id": device.id,
                "device_name": device.name,
                "maintenance_type": maintenance_type,
                "due_date": due_date.isoformat(),
                "timestamp": datetime.utcnow().isoformat()
            }
            
            await manager.broadcast_to_subscribers({
                "type": MessageType.INFO,
                "data": {
                    "type": "maintenance_reminder",
                    "data": reminder_data
                }
            }, f"device_{device.id}")
            
            logger.info(f"Broadcasted maintenance reminder for device {device.id}: {maintenance_type}")
            
        except Exception as e:
            logger.error(f"Failed to broadcast maintenance reminder: {e}")
    
    @staticmethod
    def get_connection_stats() -> Dict[str, Any]:
        """Get WebSocket connection statistics."""
        return manager.get_connection_stats()
    
    @staticmethod
    async def cleanup_stale_connections():
        """Clean up stale WebSocket connections."""
        try:
            current_time = datetime.utcnow()
            stale_threshold = 300  # 5 minutes
            
            stale_connections = []
            for websocket, info in manager.connection_info.items():
                last_heartbeat = info.get("last_heartbeat", current_time)
                if (current_time - last_heartbeat).total_seconds() > stale_threshold:
                    stale_connections.append((websocket, info["user_id"]))
            
            for websocket, user_id in stale_connections:
                manager.disconnect(websocket, user_id)
                logger.info(f"Cleaned up stale connection for user {user_id}")
            
            if stale_connections:
                logger.info(f"Cleaned up {len(stale_connections)} stale connections")
                
        except Exception as e:
            logger.error(f"Failed to cleanup stale connections: {e}")


# Global WebSocket service instance
websocket_service = WebSocketService()


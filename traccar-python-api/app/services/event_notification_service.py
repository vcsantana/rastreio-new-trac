"""
Event notification service for sending notifications when events occur
"""
from datetime import datetime
from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session

from app.models import Event, Device, User, Notification
from app.services.websocket_service import websocket_service


class EventNotificationService:
    """Service for handling event-based notifications"""

    def __init__(self, db: Session):
        self.db = db

    async def process_event_notification(self, event: Event, device: Device) -> None:
        """Process notification for a new event"""
        
        # Determine notification type based on event type
        notification_type = self._get_notification_type(event.type)
        if not notification_type:
            return  # No notification needed for this event type
        
        # Get users who should be notified
        users_to_notify = self._get_users_to_notify(event, device)
        if not users_to_notify:
            return
        
        # Create notification for each user
        for user in users_to_notify:
            await self._create_notification(
                user=user,
                event=event,
                device=device,
                notification_type=notification_type
            )

    def _get_notification_type(self, event_type: str) -> Optional[str]:
        """Determine notification type based on event type"""
        
        notification_mapping = {
            # Critical events - immediate notification
            "alarm": "critical",
            "deviceOffline": "high",
            "deviceOverspeed": "high",
            
            # Medium priority events
            "geofenceEnter": "medium",
            "geofenceExit": "medium",
            "deviceFuelDrop": "medium",
            
            # Low priority events
            "deviceOnline": "low",
            "deviceMoving": "low",
            "deviceStopped": "low",
            "ignitionOn": "low",
            "ignitionOff": "low"
        }
        
        return notification_mapping.get(event_type)

    def _get_users_to_notify(self, event: Event, device: Device) -> List[User]:
        """Get users who should be notified for this event"""
        
        # For now, get all admin users and device owners
        # In a more sophisticated system, this would check user preferences
        # and notification rules
        
        users = []
        
        # Get admin users
        admin_users = self.db.query(User).filter(User.is_admin == True).all()
        users.extend(admin_users)
        
        # Get users who have access to this device
        # This would need to be implemented based on your user-device relationship
        # For now, we'll include all users (you can refine this logic)
        all_users = self.db.query(User).all()
        users.extend(all_users)
        
        # Remove duplicates
        unique_users = list({user.id: user for user in users}.values())
        
        return unique_users

    async def _create_notification(
        self, 
        user: User, 
        event: Event, 
        device: Device, 
        notification_type: str
    ) -> None:
        """Create notification for user"""
        
        # Create notification message
        message = self._create_notification_message(event, device)
        
        # Create notification record
        notification = Notification(
            user_id=user.id,
            type=notification_type,
            title=f"Event: {event.type}",
            message=message,
            data={
                "event_id": event.id,
                "device_id": device.id,
                "device_name": device.name,
                "event_type": event.type,
                "event_time": event.event_time.isoformat()
            }
        )
        
        self.db.add(notification)
        self.db.commit()
        
        # Send real-time notification via WebSocket
        await websocket_service.broadcast_notification(user.id, notification)

    def _create_notification_message(self, event: Event, device: Device) -> str:
        """Create human-readable notification message"""
        
        device_name = device.name or f"Device {device.id}"
        event_time = event.event_time.strftime("%Y-%m-%d %H:%M:%S")
        
        message_templates = {
            "alarm": f"🚨 Alarm triggered on {device_name} at {event_time}",
            "deviceOffline": f"📴 Device {device_name} went offline at {event_time}",
            "deviceOnline": f"🟢 Device {device_name} came online at {event_time}",
            "deviceOverspeed": f"⚡ Device {device_name} exceeded speed limit at {event_time}",
            "geofenceEnter": f"📍 Device {device_name} entered geofence at {event_time}",
            "geofenceExit": f"📍 Device {device_name} exited geofence at {event_time}",
            "deviceMoving": f"🚗 Device {device_name} started moving at {event_time}",
            "deviceStopped": f"🛑 Device {device_name} stopped at {event_time}",
            "ignitionOn": f"🔑 Ignition turned on for {device_name} at {event_time}",
            "ignitionOff": f"🔑 Ignition turned off for {device_name} at {event_time}",
            "deviceFuelDrop": f"⛽ Fuel drop detected on {device_name} at {event_time}"
        }
        
        return message_templates.get(event.type, f"Event {event.type} occurred on {device_name} at {event_time}")

    async def send_immediate_notification(
        self, 
        user_id: int, 
        title: str, 
        message: str, 
        notification_type: str = "info",
        data: Optional[Dict[str, Any]] = None
    ) -> None:
        """Send immediate notification to specific user"""
        
        user = self.db.query(User).filter(User.id == user_id).first()
        if not user:
            return
        
        notification = Notification(
            user_id=user_id,
            type=notification_type,
            title=title,
            message=message,
            data=data or {}
        )
        
        self.db.add(notification)
        self.db.commit()
        
        # Send real-time notification via WebSocket
        await websocket_service.broadcast_notification(user_id, notification)

    async def send_bulk_notification(
        self, 
        user_ids: List[int], 
        title: str, 
        message: str, 
        notification_type: str = "info",
        data: Optional[Dict[str, Any]] = None
    ) -> None:
        """Send notification to multiple users"""
        
        for user_id in user_ids:
            await self.send_immediate_notification(
                user_id=user_id,
                title=title,
                message=message,
                notification_type=notification_type,
                data=data
            )

    def get_user_notifications(
        self, 
        user_id: int, 
        limit: int = 50, 
        unread_only: bool = False
    ) -> List[Notification]:
        """Get notifications for a user"""
        
        query = self.db.query(Notification).filter(Notification.user_id == user_id)
        
        if unread_only:
            query = query.filter(Notification.read == False)
        
        return query.order_by(Notification.created_at.desc()).limit(limit).all()

    def mark_notification_read(self, notification_id: int, user_id: int) -> bool:
        """Mark notification as read"""
        
        notification = self.db.query(Notification).filter(
            Notification.id == notification_id,
            Notification.user_id == user_id
        ).first()
        
        if not notification:
            return False
        
        notification.read = True
        notification.read_at = datetime.utcnow()
        self.db.commit()
        
        return True

    def mark_all_notifications_read(self, user_id: int) -> int:
        """Mark all notifications as read for a user"""
        
        count = self.db.query(Notification).filter(
            Notification.user_id == user_id,
            Notification.read == False
        ).update({
            "read": True,
            "read_at": datetime.utcnow()
        })
        
        self.db.commit()
        return count

    def cleanup_old_notifications(self, days: int = 30) -> int:
        """Clean up old notifications"""
        
        cutoff_date = datetime.utcnow() - timedelta(days=days)
        
        count = self.db.query(Notification).filter(
            Notification.created_at < cutoff_date
        ).delete()
        
        self.db.commit()
        return count

    def get_notification_stats(self, user_id: int) -> Dict[str, int]:
        """Get notification statistics for a user"""
        
        total = self.db.query(Notification).filter(Notification.user_id == user_id).count()
        unread = self.db.query(Notification).filter(
            Notification.user_id == user_id,
            Notification.read == False
        ).count()
        
        return {
            "total": total,
            "unread": unread,
            "read": total - unread
        }

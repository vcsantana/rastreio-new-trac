"""
Notification background tasks
"""
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
import structlog
from celery import current_task
from app.core.celery_app import celery_app
from app.database import get_db
from app.models.user import User
from app.models.device import Device
from app.models.event import Event
from app.models.geofence import Geofence
from app.core.cache import cache_manager
from app.api.websocket import manager as websocket_manager
from sqlalchemy import select, and_, or_, func
from sqlalchemy.orm import selectinload
import json

logger = structlog.get_logger(__name__)


@celery_app.task(bind=True, name="app.tasks.notification_tasks.send_geofence_alert")
def send_geofence_alert(self, device_id: int, geofence_id: int, 
                       event_type: str, position_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Send geofence alert notification
    
    Args:
        device_id: Device ID
        geofence_id: Geofence ID
        event_type: Type of geofence event (enter, exit)
        position_data: Position data that triggered the event
    
    Returns:
        Notification result
    """
    try:
        logger.info("Sending geofence alert", 
                   task_id=self.request.id, 
                   device_id=device_id,
                   geofence_id=geofence_id,
                   event_type=event_type)
        
        db = next(get_db())
        
        # Get device and geofence
        device = db.execute(
            select(Device).where(Device.id == device_id)
        ).scalar_one_or_none()
        
        geofence = db.execute(
            select(Geofence).where(Geofence.id == geofence_id)
        ).scalar_one_or_none()
        
        if not device or not geofence:
            return {"error": "Device or geofence not found"}
        
        # Get users who should receive this notification
        users = _get_users_for_device_notifications(db, device_id)
        
        notification_data = {
            "type": "geofence_alert",
            "device_id": device_id,
            "device_name": device.name,
            "geofence_id": geofence_id,
            "geofence_name": geofence.name,
            "event_type": event_type,
            "position": position_data,
            "timestamp": datetime.utcnow().isoformat()
        }
        
        # Send notifications
        sent_count = 0
        for user in users:
            try:
                _send_notification_to_user(user, notification_data)
                sent_count += 1
            except Exception as e:
                logger.error("Failed to send notification to user", 
                           user_id=user.id, error=str(e))
        
        # Broadcast via WebSocket
        try:
            # Note: This would need to be called in an async context
            # For now, we'll just log the broadcast
            logger.info("Geofence alert broadcast", device_id=device_id, geofence_id=geofence_id)
        except Exception as e:
            logger.error("Failed to broadcast geofence alert", error=str(e))
        
        result = {
            "task_id": self.request.id,
            "device_id": device_id,
            "geofence_id": geofence_id,
            "event_type": event_type,
            "users_notified": sent_count,
            "notification_sent_at": datetime.utcnow().isoformat()
        }
        
        logger.info("Geofence alert sent", **result)
        return result
        
    except Exception as e:
        logger.error("Geofence alert failed", 
                   task_id=self.request.id, 
                   error=str(e))
        raise


@celery_app.task(bind=True, name="app.tasks.notification_tasks.send_device_offline_alert")
def send_device_offline_alert(self, device_id: int, offline_duration_minutes: int) -> Dict[str, Any]:
    """
    Send device offline alert notification
    
    Args:
        device_id: Device ID
        offline_duration_minutes: How long the device has been offline
    
    Returns:
        Notification result
    """
    try:
        logger.info("Sending device offline alert", 
                   task_id=self.request.id, 
                   device_id=device_id,
                   offline_duration_minutes=offline_duration_minutes)
        
        db = next(get_db())
        
        # Get device
        device = db.execute(
            select(Device).where(Device.id == device_id)
        ).scalar_one_or_none()
        
        if not device:
            return {"error": "Device not found"}
        
        # Get users who should receive this notification
        users = _get_users_for_device_notifications(db, device_id)
        
        notification_data = {
            "type": "device_offline",
            "device_id": device_id,
            "device_name": device.name,
            "offline_duration_minutes": offline_duration_minutes,
            "timestamp": datetime.utcnow().isoformat()
        }
        
        # Send notifications
        sent_count = 0
        for user in users:
            try:
                _send_notification_to_user(user, notification_data)
                sent_count += 1
            except Exception as e:
                logger.error("Failed to send notification to user", 
                           user_id=user.id, error=str(e))
        
        # Broadcast via WebSocket
        try:
            # Note: This would need to be called in an async context
            # For now, we'll just log the broadcast
            logger.info("Device offline alert broadcast", device_id=device_id)
        except Exception as e:
            logger.error("Failed to broadcast device offline alert", error=str(e))
        
        result = {
            "task_id": self.request.id,
            "device_id": device_id,
            "offline_duration_minutes": offline_duration_minutes,
            "users_notified": sent_count,
            "notification_sent_at": datetime.utcnow().isoformat()
        }
        
        logger.info("Device offline alert sent", **result)
        return result
        
    except Exception as e:
        logger.error("Device offline alert failed", 
                   task_id=self.request.id, 
                   error=str(e))
        raise


@celery_app.task(bind=True, name="app.tasks.notification_tasks.send_speed_alert")
def send_speed_alert(self, device_id: int, speed: float, speed_limit: float, 
                    position_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Send speed alert notification
    
    Args:
        device_id: Device ID
        speed: Current speed
        speed_limit: Speed limit
        position_data: Position data
    
    Returns:
        Notification result
    """
    try:
        logger.info("Sending speed alert", 
                   task_id=self.request.id, 
                   device_id=device_id,
                   speed=speed,
                   speed_limit=speed_limit)
        
        db = next(get_db())
        
        # Get device
        device = db.execute(
            select(Device).where(Device.id == device_id)
        ).scalar_one_or_none()
        
        if not device:
            return {"error": "Device not found"}
        
        # Get users who should receive this notification
        users = _get_users_for_device_notifications(db, device_id)
        
        notification_data = {
            "type": "speed_alert",
            "device_id": device_id,
            "device_name": device.name,
            "speed": speed,
            "speed_limit": speed_limit,
            "position": position_data,
            "timestamp": datetime.utcnow().isoformat()
        }
        
        # Send notifications
        sent_count = 0
        for user in users:
            try:
                _send_notification_to_user(user, notification_data)
                sent_count += 1
            except Exception as e:
                logger.error("Failed to send notification to user", 
                           user_id=user.id, error=str(e))
        
        # Broadcast via WebSocket
        try:
            # Note: This would need to be called in an async context
            # For now, we'll just log the broadcast
            logger.info("Speed alert broadcast", device_id=device_id)
        except Exception as e:
            logger.error("Failed to broadcast speed alert", error=str(e))
        
        result = {
            "task_id": self.request.id,
            "device_id": device_id,
            "speed": speed,
            "speed_limit": speed_limit,
            "users_notified": sent_count,
            "notification_sent_at": datetime.utcnow().isoformat()
        }
        
        logger.info("Speed alert sent", **result)
        return result
        
    except Exception as e:
        logger.error("Speed alert failed", 
                   task_id=self.request.id, 
                   error=str(e))
        raise


@celery_app.task(bind=True, name="app.tasks.notification_tasks.send_maintenance_reminder")
def send_maintenance_reminder(self, device_id: int, maintenance_type: str, 
                            days_until_due: int) -> Dict[str, Any]:
    """
    Send maintenance reminder notification
    
    Args:
        device_id: Device ID
        maintenance_type: Type of maintenance
        days_until_due: Days until maintenance is due
    
    Returns:
        Notification result
    """
    try:
        logger.info("Sending maintenance reminder", 
                   task_id=self.request.id, 
                   device_id=device_id,
                   maintenance_type=maintenance_type,
                   days_until_due=days_until_due)
        
        db = next(get_db())
        
        # Get device
        device = db.execute(
            select(Device).where(Device.id == device_id)
        ).scalar_one_or_none()
        
        if not device:
            return {"error": "Device not found"}
        
        # Get users who should receive this notification
        users = _get_users_for_device_notifications(db, device_id)
        
        notification_data = {
            "type": "maintenance_reminder",
            "device_id": device_id,
            "device_name": device.name,
            "maintenance_type": maintenance_type,
            "days_until_due": days_until_due,
            "timestamp": datetime.utcnow().isoformat()
        }
        
        # Send notifications
        sent_count = 0
        for user in users:
            try:
                _send_notification_to_user(user, notification_data)
                sent_count += 1
            except Exception as e:
                logger.error("Failed to send notification to user", 
                           user_id=user.id, error=str(e))
        
        result = {
            "task_id": self.request.id,
            "device_id": device_id,
            "maintenance_type": maintenance_type,
            "days_until_due": days_until_due,
            "users_notified": sent_count,
            "notification_sent_at": datetime.utcnow().isoformat()
        }
        
        logger.info("Maintenance reminder sent", **result)
        return result
        
    except Exception as e:
        logger.error("Maintenance reminder failed", 
                   task_id=self.request.id, 
                   error=str(e))
        raise


@celery_app.task(bind=True, name="app.tasks.notification_tasks.send_daily_summary")
def send_daily_summary(self, user_id: int) -> Dict[str, Any]:
    """
    Send daily summary notification to a user
    
    Args:
        user_id: User ID
    
    Returns:
        Notification result
    """
    try:
        logger.info("Sending daily summary", 
                   task_id=self.request.id, 
                   user_id=user_id)
        
        db = next(get_db())
        
        # Get user
        user = db.execute(
            select(User).where(User.id == user_id)
        ).scalar_one_or_none()
        
        if not user:
            return {"error": "User not found"}
        
        # Get user's devices
        devices = _get_user_devices(db, user_id)
        
        # Generate summary data
        summary_data = _generate_daily_summary(db, user_id, devices)
        
        notification_data = {
            "type": "daily_summary",
            "user_id": user_id,
            "summary": summary_data,
            "timestamp": datetime.utcnow().isoformat()
        }
        
        # Send notification
        _send_notification_to_user(user, notification_data)
        
        result = {
            "task_id": self.request.id,
            "user_id": user_id,
            "devices_count": len(devices),
            "notification_sent_at": datetime.utcnow().isoformat()
        }
        
        logger.info("Daily summary sent", **result)
        return result
        
    except Exception as e:
        logger.error("Daily summary failed", 
                   task_id=self.request.id, 
                   user_id=user_id,
                   error=str(e))
        raise


@celery_app.task(bind=True, name="app.tasks.notification_tasks.send_system_alert")
def send_system_alert(self, alert_type: str, message: str, 
                     severity: str = "info") -> Dict[str, Any]:
    """
    Send system-wide alert notification
    
    Args:
        alert_type: Type of system alert
        message: Alert message
        severity: Alert severity (info, warning, error, critical)
    
    Returns:
        Notification result
    """
    try:
        logger.info("Sending system alert", 
                   task_id=self.request.id, 
                   alert_type=alert_type,
                   severity=severity)
        
        db = next(get_db())
        
        # Get all admin users
        admin_users = db.execute(
            select(User).where(User.admin == True)
        ).scalars().all()
        
        notification_data = {
            "type": "system_alert",
            "alert_type": alert_type,
            "message": message,
            "severity": severity,
            "timestamp": datetime.utcnow().isoformat()
        }
        
        # Send notifications to all admins
        sent_count = 0
        for user in admin_users:
            try:
                _send_notification_to_user(user, notification_data)
                sent_count += 1
            except Exception as e:
                logger.error("Failed to send system alert to user", 
                           user_id=user.id, error=str(e))
        
        # Broadcast via WebSocket
        try:
            # Note: This would need to be called in an async context
            # For now, we'll just log the broadcast
            logger.info("System alert broadcast", alert_type=alert_type)
        except Exception as e:
            logger.error("Failed to broadcast system alert", error=str(e))
        
        result = {
            "task_id": self.request.id,
            "alert_type": alert_type,
            "severity": severity,
            "admin_users_notified": sent_count,
            "notification_sent_at": datetime.utcnow().isoformat()
        }
        
        logger.info("System alert sent", **result)
        return result
        
    except Exception as e:
        logger.error("System alert failed", 
                   task_id=self.request.id, 
                   error=str(e))
        raise


# Helper functions
def _get_users_for_device_notifications(db, device_id: int) -> List[User]:
    """Get users who should receive notifications for a device"""
    try:
        # This is a simplified implementation
        # In a real system, you'd check device permissions, user preferences, etc.
        users = db.execute(
            select(User).where(User.enabled == True)
        ).scalars().all()
        
        return list(users)
        
    except Exception as e:
        logger.error("Failed to get users for device notifications", 
                   device_id=device_id, error=str(e))
        return []


def _get_user_devices(db, user_id: int) -> List[Device]:
    """Get devices for a user"""
    try:
        # This is a simplified implementation
        # In a real system, you'd check user permissions
        devices = db.execute(
            select(Device).where(Device.disabled == False)
        ).scalars().all()
        
        return list(devices)
        
    except Exception as e:
        logger.error("Failed to get user devices", 
                   user_id=user_id, error=str(e))
        return []


def _send_notification_to_user(user: User, notification_data: Dict[str, Any]):
    """Send notification to a user"""
    try:
        # Store notification in user's notification queue
        notification_key = f"user_notifications:{user.id}"
        
        # Get existing notifications
        existing_notifications = cache_manager.get(notification_key) or []
        
        # Add new notification
        existing_notifications.append(notification_data)
        
        # Keep only last 100 notifications
        if len(existing_notifications) > 100:
            existing_notifications = existing_notifications[-100:]
        
        # Store back in cache
        cache_manager.set(notification_key, existing_notifications, expire=86400)  # 24 hours
        
        # In a real implementation, you'd also send email, SMS, push notifications, etc.
        logger.info("Notification stored for user", 
                   user_id=user.id, 
                   notification_type=notification_data.get("type"))
        
    except Exception as e:
        logger.error("Failed to send notification to user", 
                   user_id=user.id, error=str(e))
        raise


def _generate_daily_summary(db, user_id: int, devices: List[Device]) -> Dict[str, Any]:
    """Generate daily summary for a user"""
    try:
        # Get yesterday's data
        yesterday = datetime.utcnow().date() - timedelta(days=1)
        start_dt = datetime.combine(yesterday, datetime.min.time())
        end_dt = datetime.combine(yesterday, datetime.max.time())
        
        summary = {
            "date": yesterday.isoformat(),
            "devices": [],
            "total_positions": 0,
            "total_events": 0,
            "total_distance": 0.0
        }
        
        for device in devices:
            # Get device statistics for yesterday
            position_count = db.execute(
                select(func.count(Position.id))
                .where(
                    and_(
                        Position.device_id == device.id,
                        Position.fix_time >= start_dt,
                        Position.fix_time <= end_dt
                    )
                )
            ).scalar()
            
            event_count = db.execute(
                select(func.count(Event.id))
                .where(
                    and_(
                        Event.device_id == device.id,
                        Event.event_time >= start_dt,
                        Event.event_time <= end_dt
                    )
                )
            ).scalar()
            
            device_summary = {
                "device_id": device.id,
                "device_name": device.name,
                "position_count": position_count,
                "event_count": event_count
            }
            
            summary["devices"].append(device_summary)
            summary["total_positions"] += position_count
            summary["total_events"] += event_count
        
        return summary
        
    except Exception as e:
        logger.error("Failed to generate daily summary", 
                   user_id=user_id, error=str(e))
        return {}

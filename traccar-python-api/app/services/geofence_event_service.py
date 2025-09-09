"""
Geofence Event Service
Handles geofence-related events and notifications
"""
import json
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
import structlog
from sqlalchemy.orm import Session
from sqlalchemy import select, and_, or_, func, desc

from app.models.geofence import Geofence
from app.models.position import Position
from app.models.device import Device
from app.models.event import Event
from app.models.user import User
from app.core.celery_app import celery_app
from app.services.websocket_service import WebSocketService
from app.services.notification_service import NotificationService

logger = structlog.get_logger(__name__)


class GeofenceEventService:
    """
    Service for handling geofence events and notifications
    """
    
    def __init__(self, db: Session):
        self.db = db
        self.notification_service = NotificationService()
    
    async def create_geofence_event(self, position: Position, device: Device, 
                                  geofence: Geofence, event_type: str, 
                                  previous_position: Optional[Position] = None) -> Optional[Event]:
        """
        Create a geofence event with proper validation and duplicate prevention
        
        Args:
            position: Current position
            device: Device that generated the position
            geofence: Geofence involved in the event
            event_type: Type of event (geofenceEnter, geofenceExit)
            previous_position: Previous position for context
            
        Returns:
            Created event or None if creation failed
        """
        try:
            # Validate event type
            if event_type not in ['geofenceEnter', 'geofenceExit']:
                logger.error("Invalid geofence event type", event_type=event_type)
                return None
            
            # Check for duplicate events (within 5 minutes)
            duplicate_event = self._check_duplicate_event(device.id, geofence.id, event_type, position.device_time)
            if duplicate_event:
                logger.debug("Duplicate geofence event prevented", 
                           event_id=duplicate_event.id,
                           event_type=event_type)
                return duplicate_event
            
            # Create event attributes
            attributes = {
                "geofence_name": geofence.name,
                "geofence_type": geofence.type,
                "latitude": position.latitude,
                "longitude": position.longitude,
                "speed": position.speed,
                "course": position.course,
                "altitude": position.altitude,
                "device_time": position.device_time.isoformat() if position.device_time else None,
                "server_time": datetime.utcnow().isoformat()
            }
            
            # Add previous position context if available
            if previous_position:
                attributes.update({
                    "previous_latitude": previous_position.latitude,
                    "previous_longitude": previous_position.longitude,
                    "previous_speed": previous_position.speed,
                    "previous_course": previous_position.course
                })
            
            # Create the event
            event = Event(
                type=event_type,
                event_time=position.device_time or datetime.utcnow(),
                device_id=device.id,
                geofence_id=geofence.id,
                position_id=position.id,
                attributes=json.dumps(attributes)
            )
            
            self.db.add(event)
            self.db.commit()
            self.db.refresh(event)
            
            logger.info("Geofence event created", 
                       event_id=event.id,
                       event_type=event_type,
                       geofence_id=geofence.id,
                       device_id=device.id)
            
            # Trigger notifications and WebSocket broadcasts
            await self._handle_event_notifications(event, device, geofence, position)
            
            return event
            
        except Exception as e:
            logger.error("Failed to create geofence event", 
                       error=str(e),
                       geofence_id=geofence.id,
                       device_id=device.id,
                       event_type=event_type)
            return None
    
    def _check_duplicate_event(self, device_id: int, geofence_id: int, 
                             event_type: str, event_time: datetime) -> Optional[Event]:
        """
        Check for duplicate geofence events within a time window
        
        Args:
            device_id: Device ID
            geofence_id: Geofence ID
            event_type: Event type
            event_time: Event time
            
        Returns:
            Existing event if found, None otherwise
        """
        try:
            # Look for similar events within 5 minutes
            time_window = event_time - timedelta(minutes=5)
            
            result = self.db.execute(
                select(Event).where(and_(
                    Event.device_id == device_id,
                    Event.geofence_id == geofence_id,
                    Event.type == event_type,
                    Event.event_time >= time_window
                )).order_by(desc(Event.event_time))
            )
            
            return result.scalar_one_or_none()
            
        except Exception as e:
            logger.error("Error checking for duplicate events", error=str(e))
            return None
    
    async def _handle_event_notifications(self, event: Event, device: Device, 
                                        geofence: Geofence, position: Position):
        """
        Handle notifications and broadcasts for geofence events
        
        Args:
            event: Created event
            device: Device involved
            geofence: Geofence involved
            position: Position that triggered the event
        """
        try:
            # Broadcast via WebSocket
            await WebSocketService.broadcast_geofence_alert(
                device, 
                geofence.name, 
                event.type.replace("geofence", "").lower(), 
                position
            )
            
            # Send notifications to relevant users
            await self._send_geofence_notifications(event, device, geofence, position)
            
            # Queue background tasks for additional processing
            self._queue_geofence_tasks(event, device, geofence, position)
            
        except Exception as e:
            logger.error("Error handling geofence event notifications", 
                       error=str(e),
                       event_id=event.id)
    
    async def _send_geofence_notifications(self, event: Event, device: Device, 
                                         geofence: Geofence, position: Position):
        """
        Send notifications to users about geofence events
        
        Args:
            event: Geofence event
            device: Device involved
            geofence: Geofence involved
            position: Position that triggered the event
        """
        try:
            # Get users who should receive notifications for this device
            users = self._get_users_for_device_notifications(device.id)
            
            if not users:
                logger.debug("No users to notify for geofence event", 
                           device_id=device.id,
                           geofence_id=geofence.id)
                return
            
            # Prepare notification data
            notification_data = {
                "type": "geofence_event",
                "event_type": event.type,
                "device_id": device.id,
                "device_name": device.name,
                "geofence_id": geofence.id,
                "geofence_name": geofence.name,
                "position": {
                    "latitude": position.latitude,
                    "longitude": position.longitude,
                    "speed": position.speed,
                    "course": position.course,
                    "timestamp": position.device_time.isoformat() if position.device_time else None
                },
                "timestamp": datetime.utcnow().isoformat()
            }
            
            # Send notifications to each user
            for user in users:
                try:
                    await self.notification_service.send_notification(
                        user, 
                        "Geofence Alert", 
                        f"Device {device.name} {event.type.replace('geofence', '').lower()}ed {geofence.name}",
                        notification_data
                    )
                except Exception as e:
                    logger.error("Failed to send geofence notification to user", 
                               user_id=user.id, error=str(e))
            
            logger.info("Geofence notifications sent", 
                       event_id=event.id,
                       user_count=len(users))
            
        except Exception as e:
            logger.error("Error sending geofence notifications", error=str(e))
    
    def _get_users_for_device_notifications(self, device_id: int) -> List[User]:
        """
        Get users who should receive notifications for a device
        
        Args:
            device_id: Device ID
            
        Returns:
            List of users to notify
        """
        try:
            # Get users who have access to this device
            # This is a simplified implementation - in production you'd check permissions
            result = self.db.execute(
                select(User).where(User.disabled == False)
            )
            return result.scalars().all()
            
        except Exception as e:
            logger.error("Error getting users for device notifications", 
                       device_id=device_id, error=str(e))
            return []
    
    def _queue_geofence_tasks(self, event: Event, device: Device, 
                            geofence: Geofence, position: Position):
        """
        Queue background tasks for geofence event processing
        
        Args:
            event: Geofence event
            device: Device involved
            geofence: Geofence involved
            position: Position that triggered the event
        """
        try:
            # Queue geofence alert task
            send_geofence_alert_task.delay(
                device_id=device.id,
                geofence_id=geofence.id,
                event_type=event.type,
                position_data={
                    "latitude": position.latitude,
                    "longitude": position.longitude,
                    "speed": position.speed,
                    "course": position.course,
                    "altitude": position.altitude,
                    "timestamp": position.device_time.isoformat() if position.device_time else None
                }
            )
            
            logger.debug("Geofence tasks queued", event_id=event.id)
            
        except Exception as e:
            logger.error("Error queueing geofence tasks", error=str(e))
    
    async def get_geofence_events(self, device_id: Optional[int] = None, 
                                geofence_id: Optional[int] = None,
                                event_type: Optional[str] = None,
                                start_date: Optional[datetime] = None,
                                end_date: Optional[datetime] = None,
                                limit: int = 100) -> List[Event]:
        """
        Get geofence events with filtering options
        
        Args:
            device_id: Filter by device ID
            geofence_id: Filter by geofence ID
            event_type: Filter by event type
            start_date: Filter by start date
            end_date: Filter by end date
            limit: Maximum number of events to return
            
        Returns:
            List of geofence events
        """
        try:
            query = select(Event).where(
                or_(Event.type == "geofenceEnter", Event.type == "geofenceExit")
            )
            
            # Apply filters
            if device_id:
                query = query.where(Event.device_id == device_id)
            
            if geofence_id:
                query = query.where(Event.geofence_id == geofence_id)
            
            if event_type:
                query = query.where(Event.type == event_type)
            
            if start_date:
                query = query.where(Event.event_time >= start_date)
            
            if end_date:
                query = query.where(Event.event_time <= end_date)
            
            # Order by event time descending and limit
            query = query.order_by(desc(Event.event_time)).limit(limit)
            
            result = self.db.execute(query)
            return result.scalars().all()
            
        except Exception as e:
            logger.error("Error getting geofence events", error=str(e))
            return []
    
    async def get_geofence_event_stats(self, device_id: Optional[int] = None,
                                     geofence_id: Optional[int] = None,
                                     days: int = 30) -> Dict[str, Any]:
        """
        Get geofence event statistics
        
        Args:
            device_id: Filter by device ID
            geofence_id: Filter by geofence ID
            days: Number of days to analyze
            
        Returns:
            Dictionary with event statistics
        """
        try:
            start_date = datetime.utcnow() - timedelta(days=days)
            
            # Base query for geofence events
            base_query = select(Event).where(
                and_(
                    or_(Event.type == "geofenceEnter", Event.type == "geofenceExit"),
                    Event.event_time >= start_date
                )
            )
            
            # Apply filters
            if device_id:
                base_query = base_query.where(Event.device_id == device_id)
            
            if geofence_id:
                base_query = base_query.where(Event.geofence_id == geofence_id)
            
            # Get total events
            total_events = self.db.execute(
                select(func.count(Event.id)).select_from(base_query.subquery())
            ).scalar()
            
            # Get events by type
            enter_events = self.db.execute(
                select(func.count(Event.id)).select_from(
                    base_query.where(Event.type == "geofenceEnter").subquery()
                )
            ).scalar()
            
            exit_events = self.db.execute(
                select(func.count(Event.id)).select_from(
                    base_query.where(Event.type == "geofenceExit").subquery()
                )
            ).scalar()
            
            # Get events by geofence
            geofence_stats = self.db.execute(
                select(
                    Event.geofence_id,
                    func.count(Event.id).label('event_count')
                ).select_from(base_query.subquery())
                .group_by(Event.geofence_id)
            ).all()
            
            # Get events by device
            device_stats = self.db.execute(
                select(
                    Event.device_id,
                    func.count(Event.id).label('event_count')
                ).select_from(base_query.subquery())
                .group_by(Event.device_id)
            ).all()
            
            return {
                "total_events": total_events,
                "enter_events": enter_events,
                "exit_events": exit_events,
                "geofence_stats": [{"geofence_id": gid, "event_count": count} 
                                 for gid, count in geofence_stats],
                "device_stats": [{"device_id": did, "event_count": count} 
                               for did, count in device_stats],
                "period_days": days,
                "start_date": start_date.isoformat(),
                "end_date": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error("Error getting geofence event stats", error=str(e))
            return {"error": str(e)}
    
    async def cleanup_old_geofence_events(self, days_to_keep: int = 90) -> int:
        """
        Clean up old geofence events
        
        Args:
            days_to_keep: Number of days of events to keep
            
        Returns:
            Number of events deleted
        """
        try:
            cutoff_date = datetime.utcnow() - timedelta(days=days_to_keep)
            
            # Get events to delete
            events_to_delete = self.db.execute(
                select(Event).where(
                    and_(
                        or_(Event.type == "geofenceEnter", Event.type == "geofenceExit"),
                        Event.event_time < cutoff_date
                    )
                )
            ).scalars().all()
            
            deleted_count = len(events_to_delete)
            
            # Delete events
            for event in events_to_delete:
                self.db.delete(event)
            
            self.db.commit()
            
            logger.info("Cleaned up old geofence events", 
                       deleted_count=deleted_count,
                       cutoff_date=cutoff_date.isoformat())
            
            return deleted_count
            
        except Exception as e:
            logger.error("Error cleaning up old geofence events", error=str(e))
            return 0


# Celery task for sending geofence alerts
@celery_app.task(bind=True, name="app.services.geofence_event_service.send_geofence_alert")
def send_geofence_alert_task(self, device_id: int, geofence_id: int, 
                           event_type: str, position_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Celery task for sending geofence alerts
    
    Args:
        device_id: Device ID
        geofence_id: Geofence ID
        event_type: Event type
        position_data: Position data
        
    Returns:
        Task result
    """
    try:
        logger.info("Processing geofence alert task", 
                   task_id=self.request.id,
                   device_id=device_id,
                   geofence_id=geofence_id,
                   event_type=event_type)
        
        # This task would handle additional processing like:
        # - Sending emails
        # - SMS notifications
        # - External API calls
        # - Logging to external systems
        
        result = {
            "task_id": self.request.id,
            "status": "completed",
            "device_id": device_id,
            "geofence_id": geofence_id,
            "event_type": event_type,
            "processed_at": datetime.utcnow().isoformat()
        }
        
        logger.info("Geofence alert task completed", task_id=self.request.id)
        return result
        
    except Exception as e:
        logger.error("Geofence alert task failed", 
                   task_id=self.request.id,
                   error=str(e))
        raise

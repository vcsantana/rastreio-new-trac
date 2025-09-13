"""
Event service for business logic and event processing
"""
import json
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload
from sqlalchemy import and_, or_, desc, func, select

from app.models import Event, Device, Position, User
from app.schemas.event import EventCreate, EventUpdate, EVENT_TYPES
from app.services.websocket_service import websocket_service
from app.services.event_notification_service import EventNotificationService


class EventService:
    """Service for event management and processing"""

    def __init__(self, db: AsyncSession):
        self.db = db
        self.notification_service = EventNotificationService(db)

    async def create_event(self, event_data: EventCreate, user: User) -> Event:
        """Create a new event with validation and WebSocket broadcast"""
        
        # Validate event type
        if event_data.type not in EVENT_TYPES:
            raise ValueError(f"Invalid event type: {event_data.type}")
        
        # Verify device exists and user has access
        result = await self.db.execute(select(Device).where(Device.id == event_data.device_id))
        device = result.scalar_one_or_none()
        if not device:
            raise ValueError("Device not found")
        
        # Verify position exists if provided
        if event_data.position_id:
            result = await self.db.execute(select(Position).where(Position.id == event_data.position_id))
            position = result.scalar_one_or_none()
            if not position:
                raise ValueError("Position not found")
        
        # Create event
        event = Event(
            type=event_data.type,
            device_id=event_data.device_id,
            position_id=event_data.position_id,
            event_time=event_data.event_time,
            geofence_id=event_data.geofence_id,
            maintenance_id=event_data.maintenance_id,
            attributes=event_data.attributes
        )
        
        self.db.add(event)
        self.db.commit()
        self.db.refresh(event)
        
        # Broadcast event update via WebSocket
        await websocket_service.broadcast_event_update(event, device)
        
        # Send notifications for the event
        try:
            await self.notification_service.process_event_notification(event, device)
        except Exception as e:
            # Log error but don't fail event creation
            print(f"Error sending event notification: {e}")
        
        return event

    async def get_event(self, event_id: int, user: User) -> Optional[Event]:
        """Get event by ID with related data"""
        result = await self.db.execute(
            select(Event)
            .options(joinedload(Event.device), joinedload(Event.position))
            .where(Event.id == event_id)
        )
        return result.scalar_one_or_none()

    async def get_events(
        self, 
        user: User,
        device_id: Optional[int] = None,
        event_type: Optional[str] = None,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
        page: int = 1,
        size: int = 50
    ) -> tuple[List[Event], int]:
        """Get events with filtering and pagination"""
        
        # Build query
        query = select(Event).options(
            joinedload(Event.device),
            joinedload(Event.position)
        )
        
        # Apply filters
        filters = []
        
        if device_id:
            filters.append(Event.device_id == device_id)
        
        if event_type:
            if event_type not in EVENT_TYPES:
                raise ValueError(f"Invalid event type: {event_type}")
            filters.append(Event.type == event_type)
        
        if start_time:
            filters.append(Event.event_time >= start_time)
        
        if end_time:
            filters.append(Event.event_time <= end_time)
        
        if filters:
            query = query.filter(and_(*filters))
        
        # Get total count
        count_query = select(func.count(Event.id))
        if filters:
            count_query = count_query.where(and_(*filters))
        total_result = await self.db.execute(count_query)
        total = total_result.scalar()
        
        # Apply pagination and ordering
        if filters:
            query = query.where(and_(*filters))
        events_result = await self.db.execute(
            query.order_by(desc(Event.event_time))
            .offset((page - 1) * size)
            .limit(size)
        )
        events = events_result.scalars().all()
        
        return events, total

    async def update_event(self, event_id: int, event_data: EventUpdate, user: User) -> Optional[Event]:
        """Update event"""
        
        result = await self.db.execute(select(Event).where(Event.id == event_id))
        event = result.scalar_one_or_none()
        if not event:
            return None
        
        # Update fields
        if event_data.type is not None:
            if event_data.type not in EVENT_TYPES:
                raise ValueError(f"Invalid event type: {event_data.type}")
            event.type = event_data.type
        
        if event_data.event_time is not None:
            event.event_time = event_data.event_time
        
        if event_data.attributes is not None:
            event.attributes = event_data.attributes
        
        self.db.commit()
        self.db.refresh(event)
        
        return event

    async def delete_event(self, event_id: int, user: User) -> bool:
        """Delete event"""
        
        result = await self.db.execute(select(Event).where(Event.id == event_id))
        event = result.scalar_one_or_none()
        if not event:
            return False
        
        self.db.delete(event)
        self.db.commit()
        
        return True

    async def get_event_stats(self, days: int = 7) -> Dict[str, Any]:
        """Get event statistics for the specified period"""
        
        # Calculate date range
        end_time = datetime.utcnow()
        start_time = end_time - timedelta(days=days)
        
        # Total events
        result = await self.db.execute(select(func.count(Event.id)).where(
            Event.event_time >= start_time
        ))
        total_events = result.scalar()
        
        # Events by type
        events_by_type = {}
        result = await self.db.execute(
            select(Event.type, func.count(Event.id).label('count'))
            .where(Event.event_time >= start_time)
            .group_by(Event.type)
        )
        type_counts = result.all()
        
        for type_name, count in type_counts:
            events_by_type[type_name] = count
        
        # Recent events (last 24 hours)
        recent_start = end_time - timedelta(hours=24)
        result = await self.db.execute(select(func.count(Event.id)).where(
            Event.event_time >= recent_start
        ))
        recent_events = result.scalar()
        
        # Events by device
        device_events = {}
        result = await self.db.execute(
            select(Event.device_id, func.count(Event.id).label('count'))
            .where(Event.event_time >= start_time)
            .group_by(Event.device_id)
        )
        device_counts = result.all()
        
        for device_id, count in device_counts:
            device_events[device_id] = count
        
        # Get recent events list (last 10 events)
        recent_events_result = await self.db.execute(
            select(Event)
            .options(joinedload(Event.device), joinedload(Event.position))
            .where(Event.event_time >= recent_start)
            .order_by(desc(Event.event_time))
            .limit(10)
        )
        recent_events_list = recent_events_result.scalars().all()
        
        # Transform recent events to response format
        recent_events_data = []
        for event in recent_events_list:
            event_data = {
                "id": event.id,
                "type": event.type,
                "device_id": event.device_id,
                "device_name": event.device.name if event.device else None,
                "event_time": event.event_time.isoformat(),
                "attributes": event.attributes
            }
            if event.position:
                event_data["position_data"] = {
                    "latitude": event.position.latitude,
                    "longitude": event.position.longitude,
                    "speed": event.position.speed,
                    "course": event.position.course
                }
            recent_events_data.append(event_data)
        
        return {
            "total_events": total_events,
            "events_by_type": events_by_type,
            "recent_events": recent_events_data,
            "device_events": device_events
        }

    def create_device_status_event(self, device_id: int, status: str, **kwargs) -> Event:
        """Create device status event (online/offline/unknown/inactive)"""
        
        event_type_map = {
            "online": Event.TYPE_DEVICE_ONLINE,
            "offline": Event.TYPE_DEVICE_OFFLINE,
            "unknown": Event.TYPE_DEVICE_UNKNOWN,
            "inactive": Event.TYPE_DEVICE_INACTIVE
        }
        
        if status not in event_type_map:
            raise ValueError(f"Invalid device status: {status}")
        
        event = Event.create_device_event(
            event_type=event_type_map[status],
            device_id=device_id,
            **kwargs
        )
        
        self.db.add(event)
        self.db.commit()
        self.db.refresh(event)
        
        return event

    def create_motion_event(self, position: Position, is_moving: bool) -> Event:
        """Create motion event (moving/stopped) from position"""
        
        event_type = Event.TYPE_DEVICE_MOVING if is_moving else Event.TYPE_DEVICE_STOPPED
        
        event = Event.create_from_position(
            event_type=event_type,
            position=position
        )
        
        self.db.add(event)
        self.db.commit()
        self.db.refresh(event)
        
        return event

    def create_geofence_event(self, position: Position, geofence_id: int, is_enter: bool) -> Event:
        """Create geofence event (enter/exit)"""
        
        event_type = Event.TYPE_GEOFENCE_ENTER if is_enter else Event.TYPE_GEOFENCE_EXIT
        
        event = Event.create_from_position(
            event_type=event_type,
            position=position,
            geofence_id=geofence_id
        )
        
        self.db.add(event)
        self.db.commit()
        self.db.refresh(event)
        
        return event

    def create_alarm_event(self, device_id: int, alarm_type: str, **kwargs) -> Event:
        """Create alarm event"""
        
        event = Event.create_device_event(
            event_type=Event.TYPE_ALARM,
            device_id=device_id,
            **kwargs
        )
        
        # Add alarm type to attributes
        if event.attributes:
            attrs = json.loads(event.attributes)
        else:
            attrs = {}
        attrs["alarmType"] = alarm_type
        event.attributes = json.dumps(attrs)
        
        self.db.add(event)
        self.db.commit()
        self.db.refresh(event)
        
        return event

    def create_ignition_event(self, position: Position, is_on: bool) -> Event:
        """Create ignition event (on/off)"""
        
        event_type = Event.TYPE_IGNITION_ON if is_on else Event.TYPE_IGNITION_OFF
        
        event = Event.create_from_position(
            event_type=event_type,
            position=position
        )
        
        self.db.add(event)
        self.db.commit()
        self.db.refresh(event)
        
        return event

    def create_overspeed_event(self, position: Position, speed_limit: float) -> Event:
        """Create overspeed event"""
        
        event = Event.create_from_position(
            event_type=Event.TYPE_DEVICE_OVERSPEED,
            position=position
        )
        
        # Add speed limit to attributes
        attrs = {"speedLimit": speed_limit}
        event.attributes = json.dumps(attrs)
        
        self.db.add(event)
        self.db.commit()
        self.db.refresh(event)
        
        return event

    async def get_events_by_device(self, device_id: int, limit: int = 100) -> List[Event]:
        """Get recent events for a specific device"""
        
        result = await self.db.execute(
            select(Event)
            .options(joinedload(Event.position))
            .where(Event.device_id == device_id)
            .order_by(desc(Event.event_time))
            .limit(limit)
        )
        return result.scalars().all()

    async def get_events_by_type(self, event_type: str, limit: int = 100) -> List[Event]:
        """Get recent events of a specific type"""
        
        if event_type not in EVENT_TYPES:
            raise ValueError(f"Invalid event type: {event_type}")
        
        result = await self.db.execute(
            select(Event)
            .options(joinedload(Event.device), joinedload(Event.position))
            .where(Event.type == event_type)
            .order_by(desc(Event.event_time))
            .limit(limit)
        )
        return result.scalars().all()

    async def cleanup_old_events(self, days: int = 90) -> int:
        """Clean up events older than specified days"""
        
        cutoff_date = datetime.utcnow() - timedelta(days=days)
        
        # Count events to be deleted
        result = await self.db.execute(select(func.count(Event.id)).where(
            Event.event_time < cutoff_date
        ))
        count = result.scalar()
        
        # Delete old events
        result = await self.db.execute(
            select(Event).where(Event.event_time < cutoff_date)
        )
        old_events = result.scalars().all()
        for event in old_events:
            await self.db.delete(event)
        await self.db.commit()
        
        return count

"""
Events API endpoints
"""
from datetime import datetime, timedelta
from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import and_, or_, desc, func

from app.database import get_db
from app.models import Event, Device, Position, User
from app.schemas.event import (
    EventResponse, 
    EventCreate, 
    EventUpdate, 
    EventListResponse,
    EventStatsResponse,
    EVENT_TYPES,
    EVENT_TYPE_INFO
)
from app.services.websocket_service import websocket_service
from app.api.auth import get_current_user

router = APIRouter(prefix="/events", tags=["events"])


@router.get("/", response_model=EventListResponse)
async def get_events(
    device_id: Optional[int] = Query(None, description="Filter by device ID"),
    event_type: Optional[str] = Query(None, description="Filter by event type"),
    start_time: Optional[datetime] = Query(None, description="Start time filter"),
    end_time: Optional[datetime] = Query(None, description="End time filter"),
    page: int = Query(1, ge=1, description="Page number"),
    size: int = Query(50, ge=1, le=1000, description="Page size"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get events with optional filtering and pagination"""
    
    # Build query
    query = db.query(Event).options(
        joinedload(Event.device),
        joinedload(Event.position)
    )
    
    # Apply filters
    filters = []
    
    if device_id:
        filters.append(Event.device_id == device_id)
    
    if event_type:
        if event_type not in EVENT_TYPES:
            raise HTTPException(status_code=400, detail=f"Invalid event type: {event_type}")
        filters.append(Event.type == event_type)
    
    if start_time:
        filters.append(Event.event_time >= start_time)
    
    if end_time:
        filters.append(Event.event_time <= end_time)
    
    if filters:
        query = query.filter(and_(*filters))
    
    # Get total count
    total = query.count()
    
    # Apply pagination and ordering
    events = query.order_by(desc(Event.event_time)).offset((page - 1) * size).limit(size).all()
    
    # Transform to response format
    event_responses = []
    for event in events:
        event_data = EventResponse.model_validate(event)
        if event.device:
            event_data.device_name = event.device.name
        if event.position:
            event_data.position_data = {
                "latitude": event.position.latitude,
                "longitude": event.position.longitude,
                "speed": event.position.speed,
                "course": event.position.course
            }
        event_responses.append(event_data)
    
    return EventListResponse(
        events=event_responses,
        total=total,
        page=page,
        size=size,
        has_next=(page * size) < total,
        has_prev=page > 1
    )


@router.get("/{event_id}", response_model=EventResponse)
async def get_event(
    event_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get a specific event by ID"""
    
    event = db.query(Event).options(
        joinedload(Event.device),
        joinedload(Event.position)
    ).filter(Event.id == event_id).first()
    
    if not event:
        raise HTTPException(status_code=404, detail="Event not found")
    
    event_data = EventResponse.model_validate(event)
    if event.device:
        event_data.device_name = event.device.name
    if event.position:
        event_data.position_data = {
            "latitude": event.position.latitude,
            "longitude": event.position.longitude,
            "speed": event.position.speed,
            "course": event.position.course
        }
    
    return event_data


@router.post("/", response_model=EventResponse)
async def create_event(
    event_data: EventCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Create a new event"""
    
    # Validate event type
    if event_data.type not in EVENT_TYPES:
        raise HTTPException(status_code=400, detail=f"Invalid event type: {event_data.type}")
    
    # Verify device exists
    device = db.query(Device).filter(Device.id == event_data.device_id).first()
    if not device:
        raise HTTPException(status_code=404, detail="Device not found")
    
    # Verify position exists if provided
    if event_data.position_id:
        position = db.query(Position).filter(Position.id == event_data.position_id).first()
        if not position:
            raise HTTPException(status_code=404, detail="Position not found")
    
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
    
    db.add(event)
    db.commit()
    db.refresh(event)
    
    # Broadcast event update via WebSocket
    await websocket_service.broadcast_event_update(event, device)
    
    return EventResponse.model_validate(event)


@router.put("/{event_id}", response_model=EventResponse)
async def update_event(
    event_id: int,
    event_data: EventUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Update an event"""
    
    event = db.query(Event).filter(Event.id == event_id).first()
    if not event:
        raise HTTPException(status_code=404, detail="Event not found")
    
    # Update fields
    if event_data.type is not None:
        if event_data.type not in EVENT_TYPES:
            raise HTTPException(status_code=400, detail=f"Invalid event type: {event_data.type}")
        event.type = event_data.type
    
    if event_data.event_time is not None:
        event.event_time = event_data.event_time
    
    if event_data.attributes is not None:
        event.attributes = event_data.attributes
    
    db.commit()
    db.refresh(event)
    
    return EventResponse.model_validate(event)


@router.delete("/{event_id}")
async def delete_event(
    event_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Delete an event"""
    
    event = db.query(Event).filter(Event.id == event_id).first()
    if not event:
        raise HTTPException(status_code=404, detail="Event not found")
    
    db.delete(event)
    db.commit()
    
    return {"message": "Event deleted successfully"}


@router.get("/stats/summary", response_model=EventStatsResponse)
async def get_event_stats(
    days: int = Query(7, ge=1, le=365, description="Number of days to analyze"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get event statistics"""
    
    # Calculate date range
    end_time = datetime.utcnow()
    start_time = end_time - timedelta(days=days)
    
    # Total events
    total_events = db.query(Event).filter(
        Event.event_time >= start_time
    ).count()
    
    # Events by type
    events_by_type = {}
    type_counts = db.query(
        Event.type, 
        func.count(Event.id).label('count')
    ).filter(
        Event.event_time >= start_time
    ).group_by(Event.type).all()
    
    for type_name, count in type_counts:
        events_by_type[type_name] = count
    
    # Recent events (last 24 hours)
    recent_start = end_time - timedelta(hours=24)
    recent_events = db.query(Event).filter(
        Event.event_time >= recent_start
    ).count()
    
    # Events by device
    device_events = {}
    device_counts = db.query(
        Event.device_id,
        func.count(Event.id).label('count')
    ).filter(
        Event.event_time >= start_time
    ).group_by(Event.device_id).all()
    
    for device_id, count in device_counts:
        device_events[device_id] = count
    
    return EventStatsResponse(
        total_events=total_events,
        events_by_type=events_by_type,
        recent_events=recent_events,
        device_events=device_events
    )


@router.get("/types/info")
async def get_event_types():
    """Get information about available event types"""
    return {
        "types": list(EVENT_TYPES),
        "type_info": EVENT_TYPE_INFO
    }

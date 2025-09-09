"""
Events API endpoints
"""
from datetime import datetime, timedelta
from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload
from sqlalchemy import and_, or_, desc, func, select

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
from app.services.event_service import EventService
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
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get events with optional filtering and pagination"""
    
    event_service = EventService(db)
    
    try:
        events, total = await event_service.get_events(
            user=current_user,
            device_id=device_id,
            event_type=event_type,
            start_time=start_time,
            end_time=end_time,
            page=page,
            size=size
        )
        
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
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/{event_id}", response_model=EventResponse)
async def get_event(
    event_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get a specific event by ID"""
    
    event_service = EventService(db)
    event = await event_service.get_event(event_id, current_user)
    
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
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Create a new event"""
    
    event_service = EventService(db)
    
    try:
        event = await event_service.create_event(event_data, current_user)
        return EventResponse.model_validate(event)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.put("/{event_id}", response_model=EventResponse)
async def update_event(
    event_id: int,
    event_data: EventUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Update an event"""
    
    event_service = EventService(db)
    
    try:
        event = await event_service.update_event(event_id, event_data, current_user)
        if not event:
            raise HTTPException(status_code=404, detail="Event not found")
        return EventResponse.model_validate(event)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.delete("/{event_id}")
async def delete_event(
    event_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Delete an event"""
    
    event_service = EventService(db)
    
    success = await event_service.delete_event(event_id, current_user)
    if not success:
        raise HTTPException(status_code=404, detail="Event not found")
    
    return {"message": "Event deleted successfully"}


@router.get("/stats/summary", response_model=EventStatsResponse)
async def get_event_stats(
    days: int = Query(7, ge=1, le=365, description="Number of days to analyze"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get event statistics"""
    
    event_service = EventService(db)
    stats = await event_service.get_event_stats(days)
    
    return EventStatsResponse(**stats)


@router.get("/types/info")
async def get_event_types():
    """Get information about available event types"""
    return {
        "types": list(EVENT_TYPES),
        "type_info": EVENT_TYPE_INFO
    }


@router.get("/rules/stats")
async def get_event_rules_stats(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get event rules statistics (admin only)"""
    if not current_user.is_admin:
        raise HTTPException(
            status_code=403,
            detail="Admin access required"
        )
    
    from app.services.event_handler import EventHandler
    
    # Convert AsyncSession to regular Session for event handler
    from sqlalchemy.orm import sessionmaker
    from app.database import engine
    
    SessionLocal = sessionmaker(bind=engine)
    sync_db = SessionLocal()
    
    try:
        event_handler = EventHandler(sync_db)
        stats = event_handler.get_rule_stats()
        return {"rule_stats": stats}
    finally:
        sync_db.close()


@router.post("/rules/{rule_name}/enable")
async def enable_event_rule(
    rule_name: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Enable event rule (admin only)"""
    if not current_user.is_admin:
        raise HTTPException(
            status_code=403,
            detail="Admin access required"
        )
    
    from app.services.event_handler import EventHandler
    
    # Convert AsyncSession to regular Session for event handler
    from sqlalchemy.orm import sessionmaker
    from app.database import engine
    
    SessionLocal = sessionmaker(bind=engine)
    sync_db = SessionLocal()
    
    try:
        event_handler = EventHandler(sync_db)
        event_handler.enable_rule(rule_name)
        return {"message": f"Rule '{rule_name}' enabled successfully"}
    finally:
        sync_db.close()


@router.post("/rules/{rule_name}/disable")
async def disable_event_rule(
    rule_name: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Disable event rule (admin only)"""
    if not current_user.is_admin:
        raise HTTPException(
            status_code=403,
            detail="Admin access required"
        )
    
    from app.services.event_handler import EventHandler
    
    # Convert AsyncSession to regular Session for event handler
    from sqlalchemy.orm import sessionmaker
    from app.database import engine
    
    SessionLocal = sessionmaker(bind=engine)
    sync_db = SessionLocal()
    
    try:
        event_handler = EventHandler(sync_db)
        event_handler.disable_rule(rule_name)
        return {"message": f"Rule '{rule_name}' disabled successfully"}
    finally:
        sync_db.close()


@router.post("/cleanup")
async def cleanup_old_events(
    days: int = Query(90, ge=1, le=365, description="Delete events older than this many days"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Clean up old events (admin only)"""
    if not current_user.is_admin:
        raise HTTPException(
            status_code=403,
            detail="Admin access required"
        )
    
    event_service = EventService(db)
    deleted_count = await event_service.cleanup_old_events(days)
    
    return {
        "message": f"Cleaned up {deleted_count} events older than {days} days",
        "deleted_count": deleted_count
    }


# Event Reports Endpoints
@router.get("/reports/summary")
async def get_events_summary_report(
    start_date: datetime = Query(..., description="Start date for report"),
    end_date: datetime = Query(..., description="End date for report"),
    device_ids: Optional[List[int]] = Query(None, description="Filter by device IDs"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Generate events summary report"""
    
    from app.services.event_report_service import EventReportService
    
    report_service = EventReportService(db)
    summary = report_service.generate_events_summary_report(
        user=current_user,
        start_date=start_date,
        end_date=end_date,
        device_ids=device_ids
    )
    
    return summary


@router.get("/reports/alarms")
async def get_alarm_report(
    start_date: datetime = Query(..., description="Start date for report"),
    end_date: datetime = Query(..., description="End date for report"),
    device_ids: Optional[List[int]] = Query(None, description="Filter by device IDs"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Generate alarm events report"""
    
    from app.services.event_report_service import EventReportService
    
    report_service = EventReportService(db)
    alarms = report_service.generate_alarm_report(
        user=current_user,
        start_date=start_date,
        end_date=end_date,
        device_ids=device_ids
    )
    
    return {"alarms": alarms, "count": len(alarms)}


@router.get("/reports/geofences")
async def get_geofence_report(
    start_date: datetime = Query(..., description="Start date for report"),
    end_date: datetime = Query(..., description="End date for report"),
    device_ids: Optional[List[int]] = Query(None, description="Filter by device IDs"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Generate geofence events report"""
    
    from app.services.event_report_service import EventReportService
    
    report_service = EventReportService(db)
    geofence_events = report_service.generate_geofence_report(
        user=current_user,
        start_date=start_date,
        end_date=end_date,
        device_ids=device_ids
    )
    
    return {"geofence_events": geofence_events, "count": len(geofence_events)}


@router.get("/reports/motion")
async def get_motion_report(
    start_date: datetime = Query(..., description="Start date for report"),
    end_date: datetime = Query(..., description="End date for report"),
    device_ids: Optional[List[int]] = Query(None, description="Filter by device IDs"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Generate motion events report"""
    
    from app.services.event_report_service import EventReportService
    
    report_service = EventReportService(db)
    motion_events = report_service.generate_motion_report(
        user=current_user,
        start_date=start_date,
        end_date=end_date,
        device_ids=device_ids
    )
    
    return {"motion_events": motion_events, "count": len(motion_events)}


@router.get("/reports/overspeed")
async def get_overspeed_report(
    start_date: datetime = Query(..., description="Start date for report"),
    end_date: datetime = Query(..., description="End date for report"),
    device_ids: Optional[List[int]] = Query(None, description="Filter by device IDs"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Generate overspeed events report"""
    
    from app.services.event_report_service import EventReportService
    
    report_service = EventReportService(db)
    overspeed_events = report_service.generate_overspeed_report(
        user=current_user,
        start_date=start_date,
        end_date=end_date,
        device_ids=device_ids
    )
    
    return {"overspeed_events": overspeed_events, "count": len(overspeed_events)}


@router.get("/reports/trends")
async def get_event_trends(
    days: int = Query(30, ge=1, le=365, description="Number of days to analyze"),
    device_ids: Optional[List[int]] = Query(None, description="Filter by device IDs"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get event trends over time"""
    
    from app.services.event_report_service import EventReportService
    
    report_service = EventReportService(db)
    trends = report_service.get_event_trends(
        user=current_user,
        days=days,
        device_ids=device_ids
    )
    
    return trends


@router.get("/reports/device/{device_id}/summary")
async def get_device_event_summary(
    device_id: int,
    days: int = Query(7, ge=1, le=365, description="Number of days to analyze"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get event summary for a specific device"""
    
    from app.services.event_report_service import EventReportService
    
    report_service = EventReportService(db)
    summary = report_service.get_device_event_summary(
        user=current_user,
        device_id=device_id,
        days=days
    )
    
    if not summary:
        raise HTTPException(status_code=404, detail="Device not found")
    
    return summary


@router.get("/reports/export/csv")
async def export_events_csv(
    start_date: datetime = Query(..., description="Start date for export"),
    end_date: datetime = Query(..., description="End date for export"),
    device_ids: Optional[List[int]] = Query(None, description="Filter by device IDs"),
    event_types: Optional[List[str]] = Query(None, description="Filter by event types"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Export events to CSV format"""
    
    from app.services.event_report_service import EventReportService
    from fastapi.responses import Response
    
    report_service = EventReportService(db)
    csv_content = report_service.export_events_to_csv(
        user=current_user,
        start_date=start_date,
        end_date=end_date,
        device_ids=device_ids,
        event_types=event_types
    )
    
    if not csv_content:
        raise HTTPException(status_code=404, detail="No events found for the specified criteria")
    
    return Response(
        content=csv_content,
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename=events_{start_date.date()}_to_{end_date.date()}.csv"}
    )

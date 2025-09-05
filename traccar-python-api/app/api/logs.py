"""
Logs API endpoints
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select, desc, and_
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional
from datetime import datetime, timedelta
import structlog

from app.database import get_db
from app.models.position import Position
from app.models.event import Event
from app.models.device import Device
from app.schemas.logs import LogEntry, LogsResponse, LogsFilter
from app.api.auth import get_current_user
from app.models.user import User

logger = structlog.get_logger(__name__)
router = APIRouter(prefix="/api/logs", tags=["logs"])


@router.get("/positions", response_model=LogsResponse)
async def get_position_logs(
    limit: int = Query(100, ge=1, le=1000, description="Number of logs to return (max 1000)"),
    device_id: Optional[int] = Query(None, description="Filter by device ID"),
    protocol: Optional[str] = Query(None, description="Filter by protocol"),
    hours: int = Query(24, ge=1, le=168, description="Hours to look back (max 1 week)"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get position logs with filtering options
    """
    try:
        # Build query
        query = select(Position).join(Device, Position.device_id == Device.id)
        
        # Apply filters
        filters = []
        
        # Time filter
        since = datetime.utcnow() - timedelta(hours=hours)
        filters.append(Position.server_time >= since)
        
        # Device filter
        if device_id:
            filters.append(Position.device_id == device_id)
        
        # Protocol filter
        if protocol:
            filters.append(Position.protocol == protocol)
        
        if filters:
            query = query.where(and_(*filters))
        
        # Order by time descending and limit
        query = query.order_by(desc(Position.server_time)).limit(limit)
        
        # Execute query
        result = await db.execute(query)
        positions = result.scalars().all()
        
        # Convert to log entries
        log_entries = []
        for position in positions:
            # Get device name separately to avoid lazy loading issues
            device_result = await db.execute(
                select(Device.name).where(Device.id == position.device_id)
            )
            device_name = device_result.scalar_one_or_none() or "Unknown"
            
            log_entries.append(LogEntry(
                id=str(position.id),
                timestamp=position.server_time,
                device_id=position.device_id,
                device_name=device_name,
                protocol=position.protocol,
                type="position",
                data={
                    "latitude": position.latitude,
                    "longitude": position.longitude,
                    "speed": position.speed,
                    "course": position.course,
                    "altitude": position.altitude,
                    "valid": position.valid,
                    "attributes": position.attributes
                }
            ))
        
        return LogsResponse(
            entries=log_entries,
            total=len(log_entries),
            limit=limit,
            filters=LogsFilter(
                device_id=device_id,
                protocol=protocol,
                hours=hours
            )
        )
        
    except Exception as e:
        logger.error("Failed to get position logs", error=str(e))
        raise HTTPException(status_code=500, detail="Failed to retrieve position logs")


@router.get("/events", response_model=LogsResponse)
async def get_event_logs(
    limit: int = Query(100, ge=1, le=1000, description="Number of logs to return (max 1000)"),
    device_id: Optional[int] = Query(None, description="Filter by device ID"),
    event_type: Optional[str] = Query(None, description="Filter by event type"),
    hours: int = Query(24, ge=1, le=168, description="Hours to look back (max 1 week)"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get event logs with filtering options
    """
    try:
        # Build query
        query = select(Event).join(Device, Event.device_id == Device.id)
        
        # Apply filters
        filters = []
        
        # Time filter
        since = datetime.utcnow() - timedelta(hours=hours)
        filters.append(Event.event_time >= since)
        
        # Device filter
        if device_id:
            filters.append(Event.device_id == device_id)
        
        # Event type filter
        if event_type:
            filters.append(Event.type == event_type)
        
        if filters:
            query = query.where(and_(*filters))
        
        # Order by time descending and limit
        query = query.order_by(desc(Event.event_time)).limit(limit)
        
        # Execute query
        result = await db.execute(query)
        events = result.scalars().all()
        
        # Convert to log entries
        log_entries = []
        for event in events:
            # Get device name separately to avoid lazy loading issues
            device_result = await db.execute(
                select(Device.name).where(Device.id == event.device_id)
            )
            device_name = device_result.scalar_one_or_none() or "Unknown"
            
            log_entries.append(LogEntry(
                id=str(event.id),
                timestamp=event.event_time,
                device_id=event.device_id,
                device_name=device_name,
                protocol="event",
                type=event.type,
                data={
                    "attributes": event.attributes,
                    "position_id": event.position_id
                }
            ))
        
        return LogsResponse(
            entries=log_entries,
            total=len(log_entries),
            limit=limit,
            filters=LogsFilter(
                device_id=device_id,
                protocol=event_type,
                hours=hours
            )
        )
        
    except Exception as e:
        logger.error("Failed to get event logs", error=str(e))
        raise HTTPException(status_code=500, detail="Failed to retrieve event logs")


@router.get("/combined", response_model=LogsResponse)
async def get_combined_logs(
    limit: int = Query(100, ge=1, le=1000, description="Number of logs to return (max 1000)"),
    device_id: Optional[int] = Query(None, description="Filter by device ID"),
    protocol: Optional[str] = Query(None, description="Filter by protocol"),
    hours: int = Query(24, ge=1, le=168, description="Hours to look back (max 1 week)"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get combined position and event logs
    """
    try:
        log_entries = []
        
        # Get positions
        position_query = select(Position).join(Device, Position.device_id == Device.id)
        position_filters = []
        
        since = datetime.utcnow() - timedelta(hours=hours)
        position_filters.append(Position.server_time >= since)
        
        if device_id:
            position_filters.append(Position.device_id == device_id)
        
        if protocol:
            position_filters.append(Position.protocol == protocol)
        
        if position_filters:
            position_query = position_query.where(and_(*position_filters))
        
        position_query = position_query.order_by(desc(Position.server_time)).limit(limit // 2)
        
        result = await db.execute(position_query)
        positions = result.scalars().all()
        
        for position in positions:
            # Get device name separately to avoid lazy loading issues
            device_result = await db.execute(
                select(Device.name).where(Device.id == position.device_id)
            )
            device_name = device_result.scalar_one_or_none() or "Unknown"
            
            log_entries.append(LogEntry(
                id=f"pos_{position.id}",
                timestamp=position.server_time,
                device_id=position.device_id,
                device_name=device_name,
                protocol=position.protocol,
                type="position",
                data={
                    "latitude": position.latitude,
                    "longitude": position.longitude,
                    "speed": position.speed,
                    "course": position.course,
                    "altitude": position.altitude,
                    "valid": position.valid,
                    "attributes": position.attributes
                }
            ))
        
        # Get events
        event_query = select(Event).join(Device, Event.device_id == Device.id)
        event_filters = []
        
        event_filters.append(Event.event_time >= since)
        
        if device_id:
            event_filters.append(Event.device_id == device_id)
        
        if event_filters:
            event_query = event_query.where(and_(*event_filters))
        
        event_query = event_query.order_by(desc(Event.event_time)).limit(limit // 2)
        
        result = await db.execute(event_query)
        events = result.scalars().all()
        
        for event in events:
            # Get device name separately to avoid lazy loading issues
            device_result = await db.execute(
                select(Device.name).where(Device.id == event.device_id)
            )
            device_name = device_result.scalar_one_or_none() or "Unknown"
            
            log_entries.append(LogEntry(
                id=f"evt_{event.id}",
                timestamp=event.event_time,
                device_id=event.device_id,
                device_name=device_name,
                protocol="event",
                type=event.type,
                data={
                    "attributes": event.attributes,
                    "position_id": event.position_id
                }
            ))
        
        # Sort combined results by timestamp
        log_entries.sort(key=lambda x: x.timestamp, reverse=True)
        
        # Limit final results
        log_entries = log_entries[:limit]
        
        return LogsResponse(
            entries=log_entries,
            total=len(log_entries),
            limit=limit,
            filters=LogsFilter(
                device_id=device_id,
                protocol=protocol,
                hours=hours
            )
        )
        
    except Exception as e:
        logger.error("Failed to get combined logs", error=str(e))
        raise HTTPException(status_code=500, detail="Failed to retrieve combined logs")


@router.get("/devices")
async def get_devices_for_logs(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get list of devices for log filtering
    """
    try:
        query = select(Device).order_by(Device.name)
        result = await db.execute(query)
        devices = result.scalars().all()
        
        return [
            {
                "id": device.id,
                "name": device.name,
                "unique_id": device.unique_id,
                "status": device.status
            }
            for device in devices
        ]
        
    except Exception as e:
        logger.error("Failed to get devices for logs", error=str(e))
        raise HTTPException(status_code=500, detail="Failed to retrieve devices")


@router.get("/protocols")
async def get_protocols_for_logs(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get list of protocols for log filtering
    """
    try:
        # Get unique protocols from positions
        query = select(Position.protocol).distinct()
        result = await db.execute(query)
        protocols = [row[0] for row in result.fetchall()]
        
        # Add event protocol
        protocols.append("event")
        
        return sorted(protocols)
        
    except Exception as e:
        logger.error("Failed to get protocols for logs", error=str(e))
        raise HTTPException(status_code=500, detail="Failed to retrieve protocols")

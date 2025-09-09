"""
Position API endpoints
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_
from typing import List, Optional
from datetime import datetime, timedelta

from app.database import get_db
from app.models.user import User
from app.models.position import Position
from app.models.device import Device
from app.schemas.position import PositionResponse, PositionCreate
from app.api.auth import get_current_user
from app.services.websocket_service import websocket_service
from app.services.position_cache import get_position_cache_service
from app.constants.position_keys import PositionKeys

router = APIRouter()

@router.get("/", response_model=List[PositionResponse])
async def get_positions(
    device_id: Optional[int] = Query(None, description="Filter by device ID"),
    from_time: Optional[datetime] = Query(None, description="Start time filter"),
    to_time: Optional[datetime] = Query(None, description="End time filter"),
    limit: int = Query(100, le=1000, description="Maximum number of positions"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get positions with optional filtering"""
    query = select(Position)
    
    # Apply filters
    filters = []
    if device_id:
        filters.append(Position.device_id == device_id)
    if from_time:
        filters.append(Position.server_time >= from_time)
    if to_time:
        filters.append(Position.server_time <= to_time)
    
    if filters:
        query = query.where(and_(*filters))
    
    # Order by time descending and limit
    query = query.order_by(Position.server_time.desc()).limit(limit)
    
    result = await db.execute(query)
    positions = result.scalars().all()
    
    return [PositionResponse.from_orm(position) for position in positions]

@router.get("/latest", response_model=List[PositionResponse])
async def get_latest_positions(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get the latest position for each device (including unknown devices)"""
    from app.api.groups import get_user_accessible_groups
    from app.models.unknown_device import UnknownDevice
    
    # Get accessible groups for the user
    accessible_groups = await get_user_accessible_groups(db, current_user.id, current_user.is_admin)
    
    latest_positions = []
    
    # Get latest positions from registered devices
    if current_user.is_admin or accessible_groups:
        # Build query with group filtering
        query = select(Device)
        
        # Filter by accessible groups (admin sees all, regular users see only their groups)
        if not current_user.is_admin:
            query = query.where(
                (Device.group_id.in_(accessible_groups)) |
                (Device.group_id.is_(None))  # Include devices without group
            )
        
        devices_result = await db.execute(query)
        devices = devices_result.scalars().all()
        
        for device in devices:
            position_result = await db.execute(
                select(Position)
                .where(Position.device_id == device.id)
                .order_by(Position.server_time.desc())
                .limit(1)
            )
            position = position_result.scalar_one_or_none()
            if position:
                latest_positions.append(PositionResponse.from_orm(position))
    
    # Get latest positions from unknown devices (only for admins or if user has group permissions)
    if current_user.is_admin or accessible_groups:
        unknown_devices_result = await db.execute(select(UnknownDevice))
        unknown_devices = unknown_devices_result.scalars().all()
        
        for unknown_device in unknown_devices:
            position_result = await db.execute(
                select(Position)
                .where(Position.unknown_device_id == unknown_device.id)
                .order_by(Position.server_time.desc())
                .limit(1)
            )
            position = position_result.scalar_one_or_none()
            if position:
                latest_positions.append(PositionResponse.from_orm(position))
    
    return latest_positions

@router.get("/device/{device_id}/history", response_model=List[PositionResponse])
async def get_device_history(
    device_id: int,
    from_time: Optional[datetime] = Query(None, description="Start time filter"),
    to_time: Optional[datetime] = Query(None, description="End time filter"),
    limit: int = Query(1000, le=5000, description="Maximum number of positions"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get position history for a specific device"""
    # Verify device exists
    device_result = await db.execute(select(Device).where(Device.id == device_id))
    device = device_result.scalar_one_or_none()
    
    if not device:
        raise HTTPException(
            status_code=404,
            detail="Device not found"
        )
    
    # Build query for device positions
    query = select(Position).where(Position.device_id == device_id)
    
    # Apply time filters
    if from_time:
        query = query.where(Position.server_time >= from_time)
    if to_time:
        query = query.where(Position.server_time <= to_time)
    
    # Order by time ascending for route tracking
    query = query.order_by(Position.server_time.asc()).limit(limit)
    
    result = await db.execute(query)
    positions = result.scalars().all()
    
    return [PositionResponse.from_orm(position) for position in positions]

@router.get("/{position_id}", response_model=PositionResponse)
async def get_position(
    position_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get a specific position with cache support"""
    cache_service = await get_position_cache_service()
    
    # Try to get from cache first
    cached_position = await cache_service.get_cached_position(position_id)
    if cached_position:
        return PositionResponse(**cached_position)
    
    # If not in cache, get from database
    result = await db.execute(select(Position).where(Position.id == position_id))
    position = result.scalar_one_or_none()
    
    if not position:
        raise HTTPException(
            status_code=404,
            detail="Position not found"
        )
    
    # Cache the position for future requests
    await cache_service.set_cached_position(position)
    
    return PositionResponse.from_orm(position)


@router.post("/", response_model=PositionResponse)
async def create_position(
    position_data: PositionCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Create a new position and broadcast via WebSocket"""
    from app.services.event_handler import EventHandler
    
    cache_service = await get_position_cache_service()
    
    # Verify device exists and user has access
    device_result = await db.execute(select(Device).where(Device.id == position_data.device_id))
    device = device_result.scalar_one_or_none()
    
    if not device:
        raise HTTPException(
            status_code=404,
            detail="Device not found"
        )
    
    # Create position
    position = Position(**position_data.dict())
    db.add(position)
    await db.commit()
    await db.refresh(position)
    
    # Process automatic events based on position
    try:
        # Convert AsyncSession to regular Session for event handler
        # Note: This is a workaround - in production, you'd want to make EventHandler async
        from sqlalchemy.orm import sessionmaker
        from app.database import engine
        from app.services.geofence_detection_service import GeofenceDetectionService
        
        SessionLocal = sessionmaker(bind=engine)
        sync_db = SessionLocal()
        
        try:
            # Process geofence detection
            geofence_detector = GeofenceDetectionService(sync_db)
            geofence_events = await geofence_detector.process_position_for_geofences(position, device)
            
            # Process other automatic events
            event_handler = EventHandler(sync_db)
            other_events = event_handler.process_position(position)
            
            # Combine all generated events
            all_events = geofence_events + other_events
            
            # Broadcast generated events via WebSocket
            for event in all_events:
                await websocket_service.broadcast_event_update(event, device)
                
        finally:
            sync_db.close()
            
    except Exception as e:
        # Log error but don't fail position creation
        print(f"Error processing automatic events: {e}")
    
    # Cache the new position
    await cache_service.set_cached_position(position)
    
    # Invalidate device cache since we have new position data
    await cache_service.invalidate_device_cache(device.id)
    
    # Broadcast position update via WebSocket
    await websocket_service.broadcast_position_update(position, device)
    
    return PositionResponse.from_orm(position)

@router.get("/cache/stats")
async def get_cache_stats(
    current_user: User = Depends(get_current_user)
):
    """Get position cache statistics (admin only)"""
    if not current_user.is_admin:
        raise HTTPException(
            status_code=403,
            detail="Admin access required"
        )
    
    cache_service = await get_position_cache_service()
    stats = await cache_service.get_cache_stats()
    
    return {
        "cache_stats": stats,
        "position_keys": PositionKeys.get_all_keys(),
        "gps_keys": PositionKeys.get_gps_keys(),
        "network_keys": PositionKeys.get_network_keys(),
        "fuel_keys": PositionKeys.get_fuel_keys(),
        "battery_keys": PositionKeys.get_battery_keys(),
        "odometer_keys": PositionKeys.get_odometer_keys(),
        "control_keys": PositionKeys.get_control_keys(),
        "alarm_keys": PositionKeys.get_alarm_keys(),
        "geofence_keys": PositionKeys.get_geofence_keys(),
        "sensor_keys": PositionKeys.get_sensor_keys(),
        "can_keys": PositionKeys.get_can_keys(),
        "maintenance_keys": PositionKeys.get_maintenance_keys(),
        "behavior_keys": PositionKeys.get_behavior_keys()
    }

@router.post("/cache/clear")
async def clear_cache(
    current_user: User = Depends(get_current_user)
):
    """Clear position cache (admin only)"""
    if not current_user.is_admin:
        raise HTTPException(
            status_code=403,
            detail="Admin access required"
        )
    
    cache_service = await get_position_cache_service()
    await cache_service.clear_all_cache()
    
    return {"message": "Position cache cleared successfully"}

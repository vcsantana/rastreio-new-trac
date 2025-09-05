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
from app.schemas.position import PositionResponse
from app.api.auth import get_current_user

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
    """Get the latest position for each device"""
    # This is a simplified version - in production you'd use a more efficient query
    devices_result = await db.execute(select(Device))
    devices = devices_result.scalars().all()
    
    latest_positions = []
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
    
    return latest_positions

@router.get("/{position_id}", response_model=PositionResponse)
async def get_position(
    position_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get a specific position"""
    result = await db.execute(select(Position).where(Position.id == position_id))
    position = result.scalar_one_or_none()
    
    if not position:
        raise HTTPException(
            status_code=404,
            detail="Position not found"
        )
    
    return PositionResponse.from_orm(position)

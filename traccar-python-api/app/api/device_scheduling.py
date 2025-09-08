"""
Device scheduling management endpoints
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import Optional

from app.database import get_db
from app.models.user import User
from app.models.device import Device
from app.api.groups import get_user_accessible_groups
from app.api.auth import get_current_user
from app.services.device_scheduling_service import device_scheduling_service

router = APIRouter()

@router.get("/{device_id}/schedule")
async def get_device_schedule(
    device_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get device schedule information"""
    # Check if device exists
    result = await db.execute(select(Device).where(Device.id == device_id))
    device = result.scalar_one_or_none()
    
    if not device:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Device not found"
        )
    
    # Check permissions for non-admin users
    if not current_user.is_admin:
        accessible_groups = await get_user_accessible_groups(db, current_user.id, current_user.is_admin)
        if device.group_id and device.group_id not in accessible_groups:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You don't have permission to view this device"
            )
    
    # Get schedule information
    schedule_info = await device_scheduling_service.get_device_schedule(db, device_id)
    
    if not schedule_info:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Device not found"
        )
    
    return schedule_info

@router.put("/{device_id}/schedule")
async def set_device_schedule(
    device_id: int,
    calendar_id: Optional[int] = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Set device schedule calendar"""
    # Check if device exists
    result = await db.execute(select(Device).where(Device.id == device_id))
    device = result.scalar_one_or_none()
    
    if not device:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Device not found"
        )
    
    # Check permissions for non-admin users
    if not current_user.is_admin:
        accessible_groups = await get_user_accessible_groups(db, current_user.id, current_user.is_admin)
        if device.group_id and device.group_id not in accessible_groups:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You don't have permission to modify this device"
            )
    
    # Set calendar
    await device_scheduling_service.set_device_calendar(db, device_id, calendar_id)
    
    return {"message": "Device schedule updated successfully"}

@router.get("/scheduled")
async def get_scheduled_devices(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get all devices with active schedules"""
    # Only admin users can view all scheduled devices
    if not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only admin users can view scheduled devices"
        )
    
    # Get scheduled devices
    scheduled_devices = await device_scheduling_service.get_scheduled_devices(db)
    
    return {
        "scheduled_devices": scheduled_devices,
        "count": len(scheduled_devices)
    }

@router.get("/scheduling/statistics")
async def get_scheduling_statistics(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get device scheduling statistics"""
    # Only admin users can view scheduling statistics
    if not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only admin users can view scheduling statistics"
        )
    
    # Get statistics
    stats = await device_scheduling_service.get_scheduling_statistics(db)
    
    return stats

@router.post("/scheduling/check")
async def check_scheduled_actions(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Manually check for scheduled actions"""
    # Only admin users can manually check scheduled actions
    if not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only admin users can check scheduled actions"
        )
    
    # Check for scheduled actions
    scheduled_actions = await device_scheduling_service.check_scheduled_actions(db)
    
    return {
        "message": "Scheduled actions check completed",
        "scheduled_actions": scheduled_actions,
        "count": len(scheduled_actions)
    }

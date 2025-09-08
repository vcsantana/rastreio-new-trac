"""
Device detection endpoints (motion and overspeed)
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
from app.services.motion_detection_service import motion_detection_service
from app.services.overspeed_detection_service import overspeed_detection_service

router = APIRouter()

# Motion Detection Endpoints

@router.get("/{device_id}/motion/statistics")
async def get_motion_statistics(
    device_id: int,
    days: int = 7,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get motion detection statistics for a device"""
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
    
    # Get motion statistics
    stats = await motion_detection_service.get_motion_statistics(db, device_id, days)
    return stats

@router.post("/{device_id}/motion/reset")
async def reset_motion_data(
    device_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Reset motion detection data for a device"""
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
    
    # Reset motion data
    await motion_detection_service.reset_motion_data(db, device_id)
    
    return {"message": "Motion data reset successfully"}

# Overspeed Detection Endpoints

@router.get("/{device_id}/overspeed/statistics")
async def get_overspeed_statistics(
    device_id: int,
    days: int = 7,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get overspeed detection statistics for a device"""
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
    
    # Get overspeed statistics
    stats = await overspeed_detection_service.get_overspeed_statistics(db, device_id, days)
    return stats

@router.put("/{device_id}/overspeed/geofence")
async def set_overspeed_geofence(
    device_id: int,
    geofence_id: Optional[int] = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Set overspeed detection geofence for a device"""
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
    
    # Set overspeed geofence
    await overspeed_detection_service.set_overspeed_geofence(db, device_id, geofence_id)
    
    return {"message": "Overspeed geofence updated successfully"}

@router.post("/{device_id}/overspeed/reset")
async def reset_overspeed_data(
    device_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Reset overspeed detection data for a device"""
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
    
    # Reset overspeed data
    await overspeed_detection_service.reset_overspeed_data(db, device_id)
    
    return {"message": "Overspeed data reset successfully"}

"""
Device expiration management endpoints
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import Optional
from datetime import datetime

from app.database import get_db
from app.models.user import User
from app.models.device import Device
from app.api.groups import get_user_accessible_groups
from app.api.auth import get_current_user
from app.services.device_expiration_service import device_expiration_service

router = APIRouter()

@router.get("/{device_id}/expiration")
async def get_device_expiration(
    device_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get device expiration information"""
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
    
    # Calculate expiration info
    current_time = datetime.now()
    is_expired = device.is_expired()
    days_until_expiration = None
    
    if device.expiration_time and not is_expired:
        days_until_expiration = (device.expiration_time - current_time).days
    
    return {
        "device_id": device_id,
        "expiration_time": device.expiration_time,
        "is_expired": is_expired,
        "days_until_expiration": days_until_expiration,
        "disabled": device.disabled
    }

@router.put("/{device_id}/expiration")
async def set_device_expiration(
    device_id: int,
    expiration_time: Optional[datetime] = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Set device expiration time"""
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
    
    # Set expiration time
    await device_expiration_service.set_device_expiration(db, device_id, expiration_time)
    
    return {"message": "Device expiration updated successfully"}

@router.post("/{device_id}/expiration/extend")
async def extend_device_expiration(
    device_id: int,
    additional_days: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Extend device expiration by specified days"""
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
    
    # Extend expiration
    await device_expiration_service.extend_device_expiration(db, device_id, additional_days)
    
    return {"message": f"Device expiration extended by {additional_days} days"}

@router.get("/expiring")
async def get_expiring_devices(
    days_ahead: int = 7,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get devices that will expire within specified days"""
    # Only admin users can view all expiring devices
    if not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only admin users can view expiring devices"
        )
    
    # Get expiring devices
    expiring_devices = await device_expiration_service.get_expiring_devices(db, days_ahead)
    
    return {
        "expiring_devices": expiring_devices,
        "days_ahead": days_ahead,
        "count": len(expiring_devices)
    }

@router.get("/expiration/statistics")
async def get_expiration_statistics(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get device expiration statistics"""
    # Only admin users can view expiration statistics
    if not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only admin users can view expiration statistics"
        )
    
    # Get statistics
    stats = await device_expiration_service.get_expiration_statistics(db)
    
    return stats

@router.post("/expiration/check")
async def check_expired_devices(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Manually check for expired devices and disable them"""
    # Only admin users can manually check expired devices
    if not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only admin users can check expired devices"
        )
    
    # Check for expired devices
    disabled_device_ids = await device_expiration_service.check_expired_devices(db)
    
    return {
        "message": f"Expired devices check completed",
        "disabled_devices": disabled_device_ids,
        "count": len(disabled_device_ids)
    }

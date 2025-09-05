"""
Device management API endpoints
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List

from app.database import get_db
from app.models.user import User
from app.models.device import Device
from app.models.group import Group
from app.schemas.device import DeviceCreate, DeviceUpdate, DeviceResponse
from app.api.auth import get_current_user
from app.services.websocket_service import websocket_service

router = APIRouter()

@router.get("/", response_model=List[DeviceResponse])
async def get_devices(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get all devices for the current user"""
    result = await db.execute(
        select(Device, Group.name.label('group_name'))
        .outerjoin(Group, Device.group_id == Group.id)
    )
    devices_with_groups = result.all()
    
    devices = []
    for device, group_name in devices_with_groups:
        device_dict = {
            "id": device.id,
            "name": device.name,
            "unique_id": device.unique_id,
            "phone": device.phone,
            "model": device.model,
            "contact": device.contact,
            "category": device.category,
            "disabled": device.disabled,
            "group_id": device.group_id,
            "status": device.status,
            "protocol": device.protocol,
            "last_update": device.last_update,
            "created_at": device.created_at,
            "group_name": group_name
        }
        devices.append(DeviceResponse(**device_dict))
    
    return devices

@router.post("/", response_model=DeviceResponse)
async def create_device(
    device_create: DeviceCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Create a new device"""
    # Check if unique_id already exists
    result = await db.execute(select(Device).where(Device.unique_id == device_create.unique_id))
    if result.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Device with this unique ID already exists"
        )
    
    # Create device
    db_device = Device(**device_create.dict())
    db.add(db_device)
    await db.commit()
    await db.refresh(db_device)
    
    # Broadcast device creation via WebSocket
    await websocket_service.broadcast_device_status_update(db_device)
    
    return DeviceResponse.from_orm(db_device)

@router.get("/{device_id}", response_model=DeviceResponse)
async def get_device(
    device_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get a specific device"""
    result = await db.execute(select(Device).where(Device.id == device_id))
    device = result.scalar_one_or_none()
    
    if not device:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Device not found"
        )
    
    return DeviceResponse.from_orm(device)

@router.put("/{device_id}", response_model=DeviceResponse)
async def update_device(
    device_id: int,
    device_update: DeviceUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Update a device"""
    result = await db.execute(select(Device).where(Device.id == device_id))
    device = result.scalar_one_or_none()
    
    if not device:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Device not found"
        )
    
    # Store old status for comparison
    old_status = device.status
    
    # Update fields
    update_data = device_update.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(device, field, value)
    
    await db.commit()
    await db.refresh(device)
    
    # Broadcast device status change via WebSocket if status changed
    if old_status != device.status:
        await websocket_service.broadcast_device_status_update(device, old_status)
    
    return DeviceResponse.from_orm(device)

@router.delete("/{device_id}")
async def delete_device(
    device_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Delete a device"""
    result = await db.execute(select(Device).where(Device.id == device_id))
    device = result.scalar_one_or_none()
    
    if not device:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Device not found"
        )
    
    await db.delete(device)
    await db.commit()
    
    return {"message": "Device deleted successfully"}

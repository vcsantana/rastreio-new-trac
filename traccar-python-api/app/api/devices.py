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
from app.models.person import Person
from app.api.groups import get_user_accessible_groups
from app.schemas.device import DeviceCreate, DeviceUpdate, DeviceResponse
from app.api.auth import get_current_user
from app.services.websocket_service import websocket_service

router = APIRouter()

@router.get("/", response_model=List[DeviceResponse])
async def get_devices(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get all devices for the current user based on their group permissions"""
    # Get accessible groups for the user
    accessible_groups = await get_user_accessible_groups(db, current_user.id, current_user.is_admin)
    
    # Build query with group filtering
    query = select(Device, Group.name.label('group_name'), Person.name.label('person_name'))
    query = query.outerjoin(Group, Device.group_id == Group.id)
    query = query.outerjoin(Person, Device.person_id == Person.id)
    
    # Filter by accessible groups (admin sees all, regular users see only their groups)
    if not current_user.is_admin:
        if not accessible_groups:
            # User has no group permissions, return empty list
            return []
        query = query.where(
            (Device.group_id.in_(accessible_groups)) |
            (Device.group_id.is_(None))  # Include devices without group
        )
    
    result = await db.execute(query)
    devices_with_relations = result.all()
    
    devices = []
    for device, group_name, person_name in devices_with_relations:
        device_dict = {
            "id": device.id,
            "name": device.name,
            "unique_id": device.unique_id,
            "phone": device.phone,
            "model": device.model,
            "contact": device.contact,
            "category": device.category,
            "license_plate": device.license_plate,
            "disabled": device.disabled,
            "group_id": device.group_id,
            "person_id": device.person_id,
            "status": device.status,
            "protocol": device.protocol,
            "last_update": device.last_update,
            "created_at": device.created_at,
            "group_name": group_name,
            "person_name": person_name
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
    
    # Check group permissions for non-admin users
    if not current_user.is_admin and device_create.group_id:
        accessible_groups = await get_user_accessible_groups(db, current_user.id, current_user.is_admin)
        if device_create.group_id not in accessible_groups:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You don't have permission to create devices in this group"
            )
    
    # Create device
    db_device = Device(**device_create.dict())
    db.add(db_device)
    await db.commit()
    await db.refresh(db_device)
    
    # Broadcast device creation via WebSocket
    await websocket_service.broadcast_device_status_update(db_device)
    
    # Get created device with relationships
    result = await db.execute(
        select(Device, Group.name.label('group_name'), Person.name.label('person_name'))
        .outerjoin(Group, Device.group_id == Group.id)
        .outerjoin(Person, Device.person_id == Person.id)
        .where(Device.id == db_device.id)
    )
    device_data = result.first()
    device, group_name, person_name = device_data
    
    device_dict = {
        "id": device.id,
        "name": device.name,
        "unique_id": device.unique_id,
        "phone": device.phone,
        "model": device.model,
        "contact": device.contact,
        "category": device.category,
        "license_plate": device.license_plate,
        "disabled": device.disabled,
        "group_id": device.group_id,
        "person_id": device.person_id,
        "status": device.status,
        "protocol": device.protocol,
        "last_update": device.last_update,
        "created_at": device.created_at,
        "group_name": group_name,
        "person_name": person_name
    }
    
    return DeviceResponse(**device_dict)

@router.get("/{device_id}", response_model=DeviceResponse)
async def get_device(
    device_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get a specific device"""
    result = await db.execute(
        select(Device, Group.name.label('group_name'), Person.name.label('person_name'))
        .outerjoin(Group, Device.group_id == Group.id)
        .outerjoin(Person, Device.person_id == Person.id)
        .where(Device.id == device_id)
    )
    device_data = result.first()
    
    if not device_data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Device not found"
        )
    
    device, group_name, person_name = device_data
    
    # Check permissions for non-admin users
    if not current_user.is_admin:
        accessible_groups = await get_user_accessible_groups(db, current_user.id, current_user.is_admin)
        if device.group_id and device.group_id not in accessible_groups:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You don't have permission to view this device"
            )
    device_dict = {
        "id": device.id,
        "name": device.name,
        "unique_id": device.unique_id,
        "phone": device.phone,
        "model": device.model,
        "contact": device.contact,
        "category": device.category,
        "license_plate": device.license_plate,
        "disabled": device.disabled,
        "group_id": device.group_id,
        "person_id": device.person_id,
        "status": device.status,
        "protocol": device.protocol,
        "last_update": device.last_update,
        "created_at": device.created_at,
        "group_name": group_name,
        "person_name": person_name
    }
    
    return DeviceResponse(**device_dict)

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
    
    # Check permissions for non-admin users
    if not current_user.is_admin:
        accessible_groups = await get_user_accessible_groups(db, current_user.id, current_user.is_admin)
        if device.group_id and device.group_id not in accessible_groups:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You don't have permission to modify this device"
            )
        
        # Check if user is trying to change group to one they don't have access to
        if device_update.group_id and device_update.group_id not in accessible_groups:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You don't have permission to assign devices to this group"
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
    
    # Get updated device with relationships
    result = await db.execute(
        select(Device, Group.name.label('group_name'), Person.name.label('person_name'))
        .outerjoin(Group, Device.group_id == Group.id)
        .outerjoin(Person, Device.person_id == Person.id)
        .where(Device.id == device_id)
    )
    device_data = result.first()
    device, group_name, person_name = device_data
    
    device_dict = {
        "id": device.id,
        "name": device.name,
        "unique_id": device.unique_id,
        "phone": device.phone,
        "model": device.model,
        "contact": device.contact,
        "category": device.category,
        "license_plate": device.license_plate,
        "disabled": device.disabled,
        "group_id": device.group_id,
        "person_id": device.person_id,
        "status": device.status,
        "protocol": device.protocol,
        "last_update": device.last_update,
        "created_at": device.created_at,
        "group_name": group_name,
        "person_name": person_name
    }
    
    return DeviceResponse(**device_dict)

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
    
    # Check permissions for non-admin users
    if not current_user.is_admin:
        accessible_groups = await get_user_accessible_groups(db, current_user.id, current_user.is_admin)
        if device.group_id and device.group_id not in accessible_groups:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You don't have permission to delete this device"
            )
    
    await db.delete(device)
    await db.commit()
    
    return {"message": "Device deleted successfully"}

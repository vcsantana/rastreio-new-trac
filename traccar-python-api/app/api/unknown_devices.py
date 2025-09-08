"""
Unknown Devices API endpoints
"""
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, desc, func
from typing import List, Optional
from datetime import datetime, timedelta

from app.database import get_db
from app.models.user import User
from app.models.unknown_device import UnknownDevice
from app.models.device import Device
from app.schemas.unknown_device import (
    UnknownDeviceResponse, 
    UnknownDeviceUpdate, 
    UnknownDeviceFilter
)
from app.api.auth import get_current_user

router = APIRouter()


@router.get("/", response_model=List[UnknownDeviceResponse])
async def get_unknown_devices(
    protocol: Optional[str] = Query(None, description="Filter by protocol"),
    port: Optional[int] = Query(None, description="Filter by port"),
    protocol_type: Optional[str] = Query(None, description="Filter by protocol type (tcp/udp/http)"),
    is_registered: Optional[bool] = Query(None, description="Filter by registration status"),
    hours: int = Query(24, description="Show devices seen in last N hours"),
    limit: int = Query(100, description="Maximum number of results"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get unknown devices with optional filtering"""
    
    # Build query
    query = select(UnknownDevice)
    
    # Apply filters
    filters = []
    
    if protocol:
        filters.append(UnknownDevice.protocol == protocol)
    
    if port:
        filters.append(UnknownDevice.port == port)
    
    if protocol_type:
        filters.append(UnknownDevice.protocol_type == protocol_type)
    
    if is_registered is not None:
        filters.append(UnknownDevice.is_registered == is_registered)
    
    # Time filter
    if hours > 0:
        cutoff_time = datetime.utcnow() - timedelta(hours=hours)
        filters.append(UnknownDevice.last_seen >= cutoff_time)
    
    if filters:
        query = query.where(and_(*filters))
    
    # Order by last seen (most recent first) and limit
    query = query.order_by(desc(UnknownDevice.last_seen)).limit(limit)
    
    result = await db.execute(query)
    unknown_devices = result.scalars().all()
    
    # Convert parsed_data from JSON string to object for each device
    import json
    result_devices = []
    for device in unknown_devices:
        # Create a copy of the device data
        device_dict = {
            'id': device.id,
            'unique_id': device.unique_id,
            'protocol': device.protocol,
            'port': device.port,
            'protocol_type': device.protocol_type,
            'client_address': device.client_address,
            'first_seen': device.first_seen,
            'last_seen': device.last_seen,
            'connection_count': device.connection_count,
            'raw_data': device.raw_data,
            'is_registered': device.is_registered,
            'registered_device_id': device.registered_device_id,
            'notes': device.notes,
            'parsed_data': {}
        }
        
        # Parse the JSON data
        if device.parsed_data:
            try:
                device_dict['parsed_data'] = json.loads(device.parsed_data)
            except:
                device_dict['parsed_data'] = {}
        
        result_devices.append(device_dict)
    
    return result_devices


@router.get("/stats")
async def get_unknown_devices_stats(
    hours: int = Query(24, description="Stats for last N hours"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get statistics about unknown devices"""
    
    cutoff_time = datetime.utcnow() - timedelta(hours=hours)
    
    # Total unknown devices in time period
    total_query = select(func.count(UnknownDevice.id)).where(
        UnknownDevice.last_seen >= cutoff_time
    )
    total_result = await db.execute(total_query)
    total_count = total_result.scalar()
    
    # By protocol
    protocol_query = select(
        UnknownDevice.protocol,
        func.count(UnknownDevice.id).label('count')
    ).where(
        UnknownDevice.last_seen >= cutoff_time
    ).group_by(UnknownDevice.protocol)
    
    protocol_result = await db.execute(protocol_query)
    protocol_stats = {row.protocol: row.count for row in protocol_result}
    
    # By port
    port_query = select(
        UnknownDevice.port,
        func.count(UnknownDevice.id).label('count')
    ).where(
        UnknownDevice.last_seen >= cutoff_time
    ).group_by(UnknownDevice.port)
    
    port_result = await db.execute(port_query)
    port_stats = {row.port: row.count for row in port_result}
    
    # Registered vs unregistered
    registered_query = select(
        UnknownDevice.is_registered,
        func.count(UnknownDevice.id).label('count')
    ).where(
        UnknownDevice.last_seen >= cutoff_time
    ).group_by(UnknownDevice.is_registered)
    
    registered_result = await db.execute(registered_query)
    registration_stats = {str(row.is_registered): row.count for row in registered_result}
    
    return {
        "total_count": total_count,
        "protocol_stats": protocol_stats,
        "port_stats": port_stats,
        "registration_stats": registration_stats,
        "time_period_hours": hours
    }


@router.get("/{unknown_device_id}", response_model=UnknownDeviceResponse)
async def get_unknown_device(
    unknown_device_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get a specific unknown device by ID"""
    
    result = await db.execute(
        select(UnknownDevice).where(UnknownDevice.id == unknown_device_id)
    )
    unknown_device = result.scalar_one_or_none()
    
    if not unknown_device:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Unknown device not found"
        )
    
    return unknown_device


@router.put("/{unknown_device_id}", response_model=UnknownDeviceResponse)
async def update_unknown_device(
    unknown_device_id: int,
    update_data: UnknownDeviceUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Update an unknown device (mainly for notes and registration status)"""
    
    result = await db.execute(
        select(UnknownDevice).where(UnknownDevice.id == unknown_device_id)
    )
    unknown_device = result.scalar_one_or_none()
    
    if not unknown_device:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Unknown device not found"
        )
    
    # Update fields
    if update_data.notes is not None:
        unknown_device.notes = update_data.notes
    
    if update_data.is_registered is not None:
        unknown_device.is_registered = update_data.is_registered
    
    if update_data.registered_device_id is not None:
        unknown_device.registered_device_id = update_data.registered_device_id
    
    await db.commit()
    await db.refresh(unknown_device)
    
    return unknown_device


@router.delete("/{unknown_device_id}")
async def delete_unknown_device(
    unknown_device_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Delete an unknown device record"""
    
    result = await db.execute(
        select(UnknownDevice).where(UnknownDevice.id == unknown_device_id)
    )
    unknown_device = result.scalar_one_or_none()
    
    if not unknown_device:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Unknown device not found"
        )
    
    await db.delete(unknown_device)
    await db.commit()
    
    return {"message": "Unknown device deleted successfully"}


@router.post("/{unknown_device_id}/register")
async def register_unknown_device(
    unknown_device_id: int,
    request_data: dict,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Mark an unknown device as registered and link it to a device"""
    
    device_id = request_data.get('device_id')
    if not device_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="device_id is required in request body"
        )
    
    # Check if unknown device exists
    result = await db.execute(
        select(UnknownDevice).where(UnknownDevice.id == unknown_device_id)
    )
    unknown_device = result.scalar_one_or_none()
    
    if not unknown_device:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Unknown device not found"
        )
    
    # Check if device exists
    device_result = await db.execute(
        select(Device).where(Device.id == device_id)
    )
    device = device_result.scalar_one_or_none()
    
    if not device:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Device not found"
        )
    
    # Update unknown device
    unknown_device.is_registered = True
    unknown_device.registered_device_id = device_id
    
    await db.commit()
    
    return {
        "message": f"Unknown device {unknown_device.unique_id} linked to device {device.name}",
        "unknown_device_id": unknown_device_id,
        "device_id": device_id
    }


@router.post("/{unknown_device_id}/create-device")
async def create_device_from_unknown(
    unknown_device_id: int,
    device_data: dict,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Create a new device from an unknown device"""
    
    # Check if unknown device exists
    result = await db.execute(
        select(UnknownDevice).where(UnknownDevice.id == unknown_device_id)
    )
    unknown_device = result.scalar_one_or_none()
    
    if not unknown_device:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Unknown device not found"
        )
    
    if unknown_device.is_registered:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Unknown device is already registered"
        )
    
    # Create new device
    from app.models.device import Device
    from app.schemas.device import DeviceCreate
    
    # Use unknown device data as base
    device_create = DeviceCreate(
        name=device_data.get('name', f"Device {unknown_device.unique_id}"),
        unique_id=unknown_device.unique_id,
        model=device_data.get('model', ''),
        contact=device_data.get('contact', ''),
        category=device_data.get('category', 'other'),
        phone=device_data.get('phone', ''),
        license_plate=device_data.get('license_plate', ''),
        group_id=device_data.get('group_id'),
        person_id=device_data.get('person_id')
    )
    
    # Create the device
    new_device = Device(
        name=device_create.name,
        unique_id=device_create.unique_id,
        protocol=unknown_device.protocol,  # Use protocol from unknown device
        model=device_create.model,
        contact=device_create.contact,
        category=device_create.category,
        phone=device_create.phone,
        license_plate=device_create.license_plate,
        group_id=device_create.group_id,
        person_id=device_create.person_id
    )
    
    db.add(new_device)
    await db.commit()
    await db.refresh(new_device)
    
    # Mark unknown device as registered and link to new device
    unknown_device.is_registered = True
    unknown_device.registered_device_id = new_device.id
    
    await db.commit()
    
    return {
        "message": f"Device created from unknown device {unknown_device.unique_id}",
        "unknown_device_id": unknown_device_id,
        "device_id": new_device.id,
        "device": {
            "id": new_device.id,
            "name": new_device.name,
            "unique_id": new_device.unique_id,
            "protocol": new_device.protocol,
            "category": new_device.category
        }
    }



"""
Client Monitoring API endpoints for Central de Monitoramento
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import select, func, and_, or_
from typing import List, Optional
from datetime import datetime, timedelta
import json

from app.database import get_db
from app.models.device import Device
from app.models.position import Position
from app.models.person import Person
from app.models.group import Group
from app.schemas.device import ClientMonitoringSummary, DeviceMonitoringResponse
from app.api.auth import get_current_user
from app.models.user import User

router = APIRouter()

@router.get("/summary", response_model=ClientMonitoringSummary)
async def get_client_monitoring_summary(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get summary statistics for client monitoring dashboard"""
    
    # Get all devices
    query = select(Device).options(
        joinedload(Device.last_position),
        joinedload(Device.person),
        joinedload(Device.group)
    )
    result = await db.execute(query)
    devices = result.scalars().all()
    
    # Calculate statistics
    total_devices = len(devices)
    online_count = sum(1 for d in devices if d.status == 'online')
    offline_count = sum(1 for d in devices if d.status == 'offline')
    unknown_count = sum(1 for d in devices if d.status == 'unknown')
    
    # Critical devices (high priority, communication issues, or problematic status)
    critical_count = sum(1 for d in devices if d.is_critical())
    
    # Status-based counts
    delinquent_count = sum(1 for d in devices if d.client_status == 'delinquent')
    test_devices = sum(1 for d in devices if d.client_status == 'test')
    lost_devices = sum(1 for d in devices if d.client_status == 'lost')
    
    # Alert counts (simplified for now - can be enhanced with real alert system)
    communication_alerts = sum(1 for d in devices 
                             if d.get_communication_status()["color"] == "red")
    battery_alerts = 0  # TODO: Implement based on position attributes
    recent_sos = 0      # TODO: Implement based on events/alarms
    
    active_alerts = communication_alerts + battery_alerts + recent_sos
    
    return ClientMonitoringSummary(
        total_devices=total_devices,
        online_count=online_count,
        offline_count=offline_count,
        unknown_count=unknown_count,
        critical_count=critical_count,
        delinquent_count=delinquent_count,
        test_devices=test_devices,
        lost_devices=lost_devices,
        active_alerts=active_alerts,
        recent_sos=recent_sos,
        battery_alerts=battery_alerts,
        communication_alerts=communication_alerts
    )

@router.get("/devices", response_model=List[DeviceMonitoringResponse])
async def get_monitoring_devices(
    client_filter: Optional[str] = Query(None, description="Filter: all, active, delinquent, test, lost, removal"),
    priority_only: Optional[bool] = Query(False, description="Show only high priority devices"),
    communication_status: Optional[str] = Query(None, description="Filter by communication: excellent, normal, attention, critical"),
    limit: Optional[int] = Query(100, description="Limit number of results"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get devices for monitoring dashboard with enhanced information"""
    
    # Build query with filters
    query = select(Device).options(
        joinedload(Device.last_position),
        joinedload(Device.person),
        joinedload(Device.group)
    )
    
    # Apply client status filter
    if client_filter and client_filter != "all":
        if client_filter == "active":
            query = query.where(Device.client_status == 'active')
        elif client_filter == "delinquent":
            query = query.where(Device.client_status == 'delinquent')
        elif client_filter == "test":
            query = query.where(Device.client_status == 'test')
        elif client_filter == "lost":
            query = query.where(Device.client_status == 'lost')
        elif client_filter == "removal":
            query = query.where(Device.client_status == 'removal')
    
    # Apply priority filter
    if priority_only:
        query = query.where(Device.priority_level <= 2)
    
    # Execute query
    result = await db.execute(query.limit(limit))
    devices = result.scalars().all()
    
    # Convert to monitoring response format
    monitoring_devices = []
    for device in devices:
        # Get communication status
        comm_status = device.get_communication_status()
        
        # Apply communication filter if specified
        if communication_status and comm_status["status"] != communication_status:
            continue
        
        # Get position data if available
        position_data = {}
        if device.last_position:
            position_data = {
                "latitude": device.last_position.latitude,
                "longitude": device.last_position.longitude,
                "speed": device.last_position.speed,
                "course": device.last_position.course,
            }
            
            # Parse ignition from attributes
            if device.last_position.attributes:
                try:
                    attrs = json.loads(device.last_position.attributes)
                    position_data["ignition"] = attrs.get("ignition", False)
                except:
                    position_data["ignition"] = False
        
        # Create monitoring response
        monitoring_device = DeviceMonitoringResponse(
            id=device.id,
            name=device.name,
            unique_id=device.unique_id,
            status=device.status,
            protocol=device.protocol,
            phone=device.phone,
            model=device.model,
            contact=device.contact,
            category=device.category,
            license_plate=device.license_plate,
            disabled=device.disabled,
            group_id=device.group_id,
            person_id=device.person_id,
            client_code=device.client_code,
            client_status=device.client_status,
            priority_level=device.priority_level,
            fidelity_score=device.fidelity_score,
            last_service_date=device.last_service_date,
            notes=device.notes,
            last_update=device.last_update,
            created_at=device.created_at,
            group_name=device.group.name if device.group else None,
            person_name=device.person.name if device.person else None,
            
            # Computed fields
            total_distance_km=device.get_total_distance_km(),
            hours_formatted=device.get_hours_formatted(),
            is_expired=device.is_expired(),
            communication_status=comm_status,
            is_critical=device.is_critical(),
            client_type_display=device.get_client_type_display(),
            priority_display=device.get_priority_display(),
            
            # Position data
            **position_data,
            
            # Alert flags (simplified for now)
            has_communication_alert=comm_status["color"] == "red",
            has_battery_alert=False,  # TODO: Implement
            has_sos_alert=False,      # TODO: Implement
            
            # Time information
            minutes_since_update=comm_status["minutes_ago"]
        )
        
        monitoring_devices.append(monitoring_device)
    
    # Sort by priority (critical first, then by priority level, then by communication status)
    monitoring_devices.sort(key=lambda d: (
        not d.is_critical,  # Critical devices first
        d.priority_level,   # Then by priority level
        d.minutes_since_update or 0  # Then by communication delay
    ))
    
    return monitoring_devices

@router.put("/devices/{device_id}/client-info")
async def update_device_client_info(
    device_id: int,
    client_code: Optional[str] = None,
    client_status: Optional[str] = None,
    priority_level: Optional[int] = None,
    fidelity_score: Optional[int] = None,
    notes: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Update client-specific information for a device"""
    
    # Get device
    result = await db.execute(select(Device).where(Device.id == device_id))
    device = result.scalar_one_or_none()
    
    if not device:
        raise HTTPException(status_code=404, detail="Device not found")
    
    # Update fields if provided
    if client_code is not None:
        device.client_code = client_code
    if client_status is not None:
        device.client_status = client_status
    if priority_level is not None:
        device.priority_level = priority_level
    if fidelity_score is not None:
        device.fidelity_score = fidelity_score
    if notes is not None:
        device.notes = notes
    
    # Update last service date to now if status changed to active
    if client_status == "active":
        device.last_service_date = datetime.utcnow()
    
    await db.commit()
    await db.refresh(device)
    
    return {"message": "Device client info updated successfully", "device_id": device_id}

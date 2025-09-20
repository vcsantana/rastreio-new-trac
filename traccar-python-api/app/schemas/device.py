"""
Device schemas
"""
from pydantic import BaseModel
from typing import Optional, Dict, Any
from datetime import datetime

class DeviceBase(BaseModel):
    name: str
    unique_id: str
    phone: Optional[str] = None
    model: Optional[str] = None
    contact: Optional[str] = None
    category: Optional[str] = None
    license_plate: Optional[str] = None
    disabled: Optional[bool] = False
    group_id: Optional[int] = None
    person_id: Optional[int] = None
    
    # Client Management Fields
    client_code: Optional[str] = None
    client_status: Optional[str] = "active"
    priority_level: Optional[int] = 3
    fidelity_score: Optional[int] = 3
    last_service_date: Optional[datetime] = None
    notes: Optional[str] = None
    
    # Accumulators
    total_distance: Optional[float] = 0.0
    hours: Optional[float] = 0.0
    
    # Motion Detection
    motion_streak: Optional[bool] = False
    motion_state: Optional[bool] = False
    motion_time: Optional[datetime] = None
    motion_distance: Optional[float] = 0.0
    
    # Overspeed Detection
    overspeed_state: Optional[bool] = False
    overspeed_time: Optional[datetime] = None
    overspeed_geofence_id: Optional[int] = None
    
    # Expiration and Scheduling
    expiration_time: Optional[datetime] = None
    calendar_id: Optional[int] = None

class DeviceCreate(DeviceBase):
    pass

class DeviceUpdate(BaseModel):
    name: Optional[str] = None
    unique_id: Optional[str] = None
    phone: Optional[str] = None
    model: Optional[str] = None
    contact: Optional[str] = None
    category: Optional[str] = None
    license_plate: Optional[str] = None
    disabled: Optional[bool] = None
    group_id: Optional[int] = None
    person_id: Optional[int] = None
    
    # Client Management Fields
    client_code: Optional[str] = None
    client_status: Optional[str] = None
    priority_level: Optional[int] = None
    fidelity_score: Optional[int] = None
    last_service_date: Optional[datetime] = None
    notes: Optional[str] = None
    
    # Accumulators
    total_distance: Optional[float] = None
    hours: Optional[float] = None
    
    # Motion Detection
    motion_streak: Optional[bool] = None
    motion_state: Optional[bool] = None
    motion_time: Optional[datetime] = None
    motion_distance: Optional[float] = None
    
    # Overspeed Detection
    overspeed_state: Optional[bool] = None
    overspeed_time: Optional[datetime] = None
    overspeed_geofence_id: Optional[int] = None
    
    # Expiration and Scheduling
    expiration_time: Optional[datetime] = None
    calendar_id: Optional[int] = None

class DeviceResponse(DeviceBase):
    id: int
    status: str
    protocol: Optional[str] = None
    last_update: Optional[datetime] = None
    created_at: datetime
    group_name: Optional[str] = None
    person_name: Optional[str] = None
    
    # Computed fields
    total_distance_km: Optional[float] = None
    hours_formatted: Optional[str] = None
    is_expired: Optional[bool] = None
    communication_status: Optional[Dict[str, Any]] = None
    is_critical: Optional[bool] = None
    client_type_display: Optional[str] = None
    priority_display: Optional[str] = None
    
    class Config:
        from_attributes = True

class ClientMonitoringSummary(BaseModel):
    """Summary for Client Monitoring Dashboard"""
    total_devices: int
    online_count: int
    offline_count: int
    unknown_count: int
    critical_count: int
    delinquent_count: int
    test_devices: int
    lost_devices: int
    active_alerts: int
    recent_sos: int
    battery_alerts: int
    communication_alerts: int

class DeviceMonitoringResponse(DeviceResponse):
    """Enhanced device response for monitoring dashboard"""
    # Position data
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    speed: Optional[float] = None
    course: Optional[float] = None
    ignition: Optional[bool] = None
    
    # Alert flags
    has_sos_alert: Optional[bool] = False
    has_battery_alert: Optional[bool] = False
    has_communication_alert: Optional[bool] = False
    
    # Time since last communication in minutes
    minutes_since_update: Optional[int] = None

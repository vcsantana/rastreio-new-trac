"""
Position schemas
"""
from pydantic import BaseModel, validator
from typing import Optional, Dict, Any, List
from datetime import datetime
import json

class PositionBase(BaseModel):
    device_id: Optional[int] = None
    unknown_device_id: Optional[int] = None
    protocol: str
    valid: bool = True
    latitude: float
    longitude: float
    altitude: Optional[float] = 0.0
    speed: Optional[float] = 0.0
    course: Optional[float] = 0.0
    
    # GPS and Satellite Information
    hdop: Optional[float] = None
    vdop: Optional[float] = None
    pdop: Optional[float] = None
    satellites: Optional[int] = None
    satellites_visible: Optional[int] = None
    
    # Network and Communication
    rssi: Optional[int] = None
    roaming: Optional[bool] = None
    network_type: Optional[str] = None
    cell_id: Optional[str] = None
    lac: Optional[str] = None
    mnc: Optional[str] = None
    mcc: Optional[str] = None
    
    # Fuel and Engine
    fuel_level: Optional[float] = None
    fuel_used: Optional[float] = None
    fuel_consumption: Optional[float] = None
    rpm: Optional[int] = None
    engine_load: Optional[float] = None
    engine_temp: Optional[float] = None
    throttle: Optional[float] = None
    coolant_temp: Optional[float] = None
    hours: Optional[float] = None
    
    # Battery and Power
    battery: Optional[float] = None
    battery_level: Optional[int] = None
    power: Optional[float] = None
    charge: Optional[bool] = None
    external_power: Optional[bool] = None
    
    # Odometer and Distance
    odometer: Optional[float] = None
    odometer_service: Optional[float] = None
    odometer_trip: Optional[float] = None
    total_distance: Optional[float] = None
    distance: Optional[float] = None
    trip_distance: Optional[float] = None
    
    # Control and Status
    ignition: Optional[bool] = None
    motion: Optional[bool] = None
    armed: Optional[bool] = None
    blocked: Optional[bool] = None
    lock: Optional[bool] = None
    door: Optional[bool] = None
    driver_unique_id: Optional[str] = None
    
    # Alarms and Events
    alarm: Optional[str] = None
    event: Optional[str] = None
    status: Optional[str] = None
    alarm_type: Optional[str] = None
    event_type: Optional[str] = None
    
    # Geofences
    geofence_ids: Optional[List[int]] = None
    geofence: Optional[str] = None
    geofence_id: Optional[int] = None
    
    # Additional Sensors
    temperature: Optional[float] = None
    humidity: Optional[float] = None
    pressure: Optional[float] = None
    light: Optional[float] = None
    proximity: Optional[float] = None
    acceleration: Optional[float] = None
    gyroscope: Optional[float] = None
    magnetometer: Optional[float] = None
    
    # CAN Bus Data
    can_data: Optional[Dict[str, Any]] = None
    obd_speed: Optional[float] = None
    obd_rpm: Optional[int] = None
    obd_fuel: Optional[float] = None
    obd_temp: Optional[float] = None
    
    # Maintenance
    maintenance: Optional[bool] = None
    service_due: Optional[datetime] = None
    oil_level: Optional[float] = None
    tire_pressure: Optional[float] = None
    
    # Driver Behavior
    hard_acceleration: Optional[bool] = None
    hard_braking: Optional[bool] = None
    hard_turning: Optional[bool] = None
    idling: Optional[bool] = None
    overspeed: Optional[bool] = None
    
    # Location Quality
    location_accuracy: Optional[float] = None
    gps_accuracy: Optional[float] = None
    network_accuracy: Optional[float] = None
    
    # Protocol Specific
    protocol_version: Optional[str] = None
    firmware_version: Optional[str] = None
    hardware_version: Optional[str] = None
    
    # Time and Status
    outdated: Optional[bool] = False
    
    # Custom Attributes
    custom1: Optional[str] = None
    custom2: Optional[str] = None
    custom3: Optional[str] = None
    custom4: Optional[str] = None
    custom5: Optional[str] = None
    
    @validator('latitude')
    def validate_latitude(cls, v):
        if not -90 <= v <= 90:
            raise ValueError('Latitude must be between -90 and 90 degrees')
        return v
    
    @validator('longitude')
    def validate_longitude(cls, v):
        if not -180 <= v <= 180:
            raise ValueError('Longitude must be between -180 and 180 degrees')
        return v

class PositionCreate(PositionBase):
    device_time: Optional[datetime] = None
    fix_time: Optional[datetime] = None
    address: Optional[str] = None
    accuracy: Optional[float] = None
    attributes: Optional[Dict[str, Any]] = None

class PositionResponse(PositionBase):
    id: int
    server_time: datetime
    device_time: Optional[datetime] = None
    fix_time: Optional[datetime] = None
    address: Optional[str] = None
    accuracy: Optional[float] = None
    attributes: Optional[Dict[str, Any]] = None
    
    @validator('attributes', pre=True)
    def parse_attributes(cls, v):
        if isinstance(v, str):
            try:
                return json.loads(v)
            except (json.JSONDecodeError, TypeError):
                return {}
        return v or {}
    
    @validator('geofence_ids', pre=True)
    def parse_geofence_ids(cls, v):
        if isinstance(v, str):
            try:
                return json.loads(v)
            except (json.JSONDecodeError, TypeError):
                return []
        return v or []
    
    @validator('can_data', pre=True)
    def parse_can_data(cls, v):
        if isinstance(v, str):
            try:
                return json.loads(v)
            except (json.JSONDecodeError, TypeError):
                return {}
        return v or {}
    
    class Config:
        from_attributes = True

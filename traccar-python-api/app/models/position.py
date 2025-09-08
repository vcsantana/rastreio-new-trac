"""
Position model
"""
from sqlalchemy import Column, Integer, String, Boolean, DateTime, Text, ForeignKey, Float, Index
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from typing import Optional, Dict, Any, List
from datetime import datetime
import json
from app.database import Base

class Position(Base):
    __tablename__ = "positions"
    
    id = Column(Integer, primary_key=True, index=True)
    device_id = Column(Integer, ForeignKey("devices.id"), nullable=True, index=True)
    unknown_device_id = Column(Integer, ForeignKey("unknown_devices.id"), nullable=True, index=True)
    protocol = Column(String(50), nullable=False)
    
    # Time information
    server_time = Column(DateTime(timezone=True), server_default=func.now(), index=True)
    device_time = Column(DateTime(timezone=True), index=True)
    fix_time = Column(DateTime(timezone=True))
    
    # Position data
    valid = Column(Boolean, default=True)
    latitude = Column(Float, nullable=False, index=True)
    longitude = Column(Float, nullable=False, index=True)
    altitude = Column(Float, default=0.0)
    
    # Movement data
    speed = Column(Float, default=0.0)  # knots
    course = Column(Float, default=0.0)  # degrees
    
    # Additional data
    address = Column(String(512))
    accuracy = Column(Float)
    network = Column(Text)  # JSON string for network info
    
    # Raw data
    attributes = Column(Text)  # JSON string for additional attributes
    
    # GPS and Satellite Information
    hdop = Column(Float)  # Horizontal Dilution of Precision
    vdop = Column(Float)  # Vertical Dilution of Precision
    pdop = Column(Float)  # Position Dilution of Precision
    satellites = Column(Integer)  # Number of satellites in use
    satellites_visible = Column(Integer)  # Number of visible satellites
    
    # Network and Communication
    rssi = Column(Integer)  # Received Signal Strength Indicator
    roaming = Column(Boolean)  # Roaming status
    network_type = Column(String(50))  # Network type (2G, 3G, 4G, etc.)
    cell_id = Column(String(50))  # Cell tower ID
    lac = Column(String(50))  # Location Area Code
    mnc = Column(String(50))  # Mobile Network Code
    mcc = Column(String(50))  # Mobile Country Code
    
    # Fuel and Engine
    fuel_level = Column(Float)  # Fuel level percentage
    fuel_used = Column(Float)  # Fuel used in liters
    fuel_consumption = Column(Float)  # Fuel consumption rate
    rpm = Column(Integer)  # Engine RPM
    engine_load = Column(Float)  # Engine load percentage
    engine_temp = Column(Float)  # Engine temperature
    throttle = Column(Float)  # Throttle position
    coolant_temp = Column(Float)  # Coolant temperature
    hours = Column(Float)  # Engine hours
    
    # Battery and Power
    battery = Column(Float)  # Battery voltage
    battery_level = Column(Integer)  # Battery level percentage
    power = Column(Float)  # Power supply voltage
    charge = Column(Boolean)  # Charging status
    external_power = Column(Boolean)  # External power status
    
    # Odometer and Distance
    odometer = Column(Float)  # Total odometer reading
    odometer_service = Column(Float)  # Service odometer
    odometer_trip = Column(Float)  # Trip odometer
    total_distance = Column(Float)  # Total distance traveled
    distance = Column(Float)  # Distance from previous position
    trip_distance = Column(Float)  # Distance in current trip
    
    # Control and Status
    ignition = Column(Boolean)  # Ignition status
    motion = Column(Boolean)  # Motion status
    armed = Column(Boolean)  # Armed status
    blocked = Column(Boolean)  # Blocked status
    lock = Column(Boolean)  # Lock status
    door = Column(Boolean)  # Door status
    driver_unique_id = Column(String(255))  # Driver ID
    
    # Alarms and Events
    alarm = Column(String(255))  # Alarm type
    event = Column(String(255))  # Event type
    status = Column(String(255))  # Device status
    alarm_type = Column(String(255))  # Specific alarm type
    event_type = Column(String(255))  # Specific event type
    
    # Geofences
    geofence_ids = Column(Text)  # JSON array of geofence IDs
    geofence = Column(String(255))  # Geofence name
    geofence_id = Column(Integer)  # Single geofence ID
    
    # Additional Sensors
    temperature = Column(Float)  # Temperature sensor
    humidity = Column(Float)  # Humidity sensor
    pressure = Column(Float)  # Pressure sensor
    light = Column(Float)  # Light sensor
    proximity = Column(Float)  # Proximity sensor
    acceleration = Column(Float)  # Acceleration sensor
    gyroscope = Column(Float)  # Gyroscope sensor
    magnetometer = Column(Float)  # Magnetometer sensor
    
    # CAN Bus Data
    can_data = Column(Text)  # JSON string for CAN bus data
    obd_speed = Column(Float)  # OBD speed reading
    obd_rpm = Column(Integer)  # OBD RPM reading
    obd_fuel = Column(Float)  # OBD fuel level
    obd_temp = Column(Float)  # OBD temperature
    
    # Maintenance
    maintenance = Column(Boolean)  # Maintenance status
    service_due = Column(DateTime(timezone=True))  # Service due date
    oil_level = Column(Float)  # Oil level
    tire_pressure = Column(Float)  # Tire pressure
    
    # Driver Behavior
    hard_acceleration = Column(Boolean)  # Hard acceleration event
    hard_braking = Column(Boolean)  # Hard braking event
    hard_turning = Column(Boolean)  # Hard turning event
    idling = Column(Boolean)  # Idling status
    overspeed = Column(Boolean)  # Overspeed event
    
    # Location Quality
    location_accuracy = Column(Float)  # Location accuracy
    gps_accuracy = Column(Float)  # GPS accuracy
    network_accuracy = Column(Float)  # Network accuracy
    
    # Protocol Specific
    protocol_version = Column(String(50))  # Protocol version
    firmware_version = Column(String(50))  # Firmware version
    hardware_version = Column(String(50))  # Hardware version
    
    # Time and Status
    outdated = Column(Boolean, default=False)  # Position outdated status
    
    # Custom Attributes
    custom1 = Column(String(255))  # Custom attribute 1
    custom2 = Column(String(255))  # Custom attribute 2
    custom3 = Column(String(255))  # Custom attribute 3
    custom4 = Column(String(255))  # Custom attribute 4
    custom5 = Column(String(255))  # Custom attribute 5
    
    # Performance indexes
    __table_args__ = (
        Index('idx_position_device_time', 'device_id', 'server_time'),
        Index('idx_position_lat_lon', 'latitude', 'longitude'),
        Index('idx_position_protocol', 'protocol'),
        Index('idx_position_valid', 'valid'),
        Index('idx_position_fix_time', 'fix_time'),
        Index('idx_position_unknown_device', 'unknown_device_id'),
        Index('idx_position_ignition', 'ignition'),
        Index('idx_position_motion', 'motion'),
        Index('idx_position_alarm', 'alarm'),
        Index('idx_position_event', 'event'),
    )
    
    # Relationships
    device = relationship("Device", back_populates="positions", foreign_keys=[device_id])
    events = relationship("Event", back_populates="position")
    
    def __repr__(self):
        return f"<Position(id={self.id}, device_id={self.device_id}, lat={self.latitude}, lon={self.longitude})>"
    
    # Typed attribute access methods
    def get_string_attribute(self, key: str, default: str = None) -> str:
        """Get string attribute from attributes JSON"""
        if not self.attributes:
            return default
        try:
            attrs = json.loads(self.attributes)
            return attrs.get(key, default)
        except (json.JSONDecodeError, TypeError):
            return default
    
    def get_double_attribute(self, key: str, default: float = None) -> float:
        """Get double/float attribute from attributes JSON"""
        if not self.attributes:
            return default
        try:
            attrs = json.loads(self.attributes)
            value = attrs.get(key, default)
            return float(value) if value is not None else default
        except (json.JSONDecodeError, TypeError, ValueError):
            return default
    
    def get_boolean_attribute(self, key: str, default: bool = False) -> bool:
        """Get boolean attribute from attributes JSON"""
        if not self.attributes:
            return default
        try:
            attrs = json.loads(self.attributes)
            value = attrs.get(key, default)
            return bool(value) if value is not None else default
        except (json.JSONDecodeError, TypeError):
            return default
    
    def get_integer_attribute(self, key: str, default: int = None) -> int:
        """Get integer attribute from attributes JSON"""
        if not self.attributes:
            return default
        try:
            attrs = json.loads(self.attributes)
            value = attrs.get(key, default)
            return int(value) if value is not None else default
        except (json.JSONDecodeError, TypeError, ValueError):
            return default
    
    def get_date_attribute(self, key: str, default: datetime = None) -> datetime:
        """Get date attribute from attributes JSON"""
        if not self.attributes:
            return default
        try:
            attrs = json.loads(self.attributes)
            value = attrs.get(key, default)
            if isinstance(value, str):
                return datetime.fromisoformat(value.replace('Z', '+00:00'))
            return value
        except (json.JSONDecodeError, TypeError, ValueError):
            return default
    
    def set_attribute(self, key: str, value: Any) -> None:
        """Set attribute in attributes JSON"""
        if not self.attributes:
            attrs = {}
        else:
            try:
                attrs = json.loads(self.attributes)
            except (json.JSONDecodeError, TypeError):
                attrs = {}
        
        attrs[key] = value
        self.attributes = json.dumps(attrs)
    
    def get_geofence_ids(self) -> List[int]:
        """Get geofence IDs as list"""
        if not self.geofence_ids:
            return []
        try:
            return json.loads(self.geofence_ids)
        except (json.JSONDecodeError, TypeError):
            return []
    
    def set_geofence_ids(self, ids: List[int]) -> None:
        """Set geofence IDs as JSON array"""
        self.geofence_ids = json.dumps(ids)
    
    def get_can_data(self) -> Dict[str, Any]:
        """Get CAN bus data as dictionary"""
        if not self.can_data:
            return {}
        try:
            return json.loads(self.can_data)
        except (json.JSONDecodeError, TypeError):
            return {}
    
    def set_can_data(self, data: Dict[str, Any]) -> None:
        """Set CAN bus data as JSON"""
        self.can_data = json.dumps(data)

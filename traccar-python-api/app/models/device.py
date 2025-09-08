"""
Device model
"""
from sqlalchemy import Column, Integer, String, Boolean, DateTime, Text, ForeignKey, Float
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.database import Base

class Device(Base):
    __tablename__ = "devices"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    unique_id = Column(String(255), unique=True, index=True, nullable=False)
    status = Column(String(50), default="unknown")  # online, offline, unknown
    protocol = Column(String(50))
    
    # Last known position
    last_update = Column(DateTime(timezone=True))
    position_id = Column(Integer, ForeignKey("positions.id"))
    
    # Device attributes
    phone = Column(String(50))
    model = Column(String(255))
    contact = Column(String(255))
    category = Column(String(50))
    license_plate = Column(String(20))  # Placa do veículo
    disabled = Column(Boolean, default=False)
    
    # Relationships
    group_id = Column(Integer, ForeignKey("groups.id"))
    person_id = Column(Integer, ForeignKey("persons.id"))  # Associação com pessoa
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Additional attributes (JSON)
    attributes = Column(Text)
    
    # Accumulators
    total_distance = Column(Float, default=0.0)  # Total distance in meters
    hours = Column(Float, default=0.0)  # Total hours of operation
    
    # Motion Detection
    motion_streak = Column(Boolean, default=False)  # Motion streak status
    motion_state = Column(Boolean, default=False)  # Current motion state
    motion_position_id = Column(Integer, ForeignKey("positions.id"))  # Last motion position
    motion_time = Column(DateTime(timezone=True))  # Last motion time
    motion_distance = Column(Float, default=0.0)  # Motion distance
    
    # Overspeed Detection
    overspeed_state = Column(Boolean, default=False)  # Current overspeed state
    overspeed_time = Column(DateTime(timezone=True))  # Last overspeed time
    overspeed_geofence_id = Column(Integer, ForeignKey("geofences.id"))  # Overspeed geofence
    
    # Expiration and Scheduling
    expiration_time = Column(DateTime(timezone=True))  # Device expiration time
    calendar_id = Column(Integer)  # Associated calendar (no FK constraint for now)
    
    # Relationships
    positions = relationship("Position", back_populates="device", cascade="all, delete-orphan", foreign_keys="Position.device_id")
    events = relationship("Event", back_populates="device", cascade="all, delete-orphan")
    commands = relationship("Command", back_populates="device", cascade="all, delete-orphan")
    images = relationship("DeviceImage", back_populates="device", cascade="all, delete-orphan")
    last_position = relationship("Position", foreign_keys=[position_id], post_update=True)
    motion_position = relationship("Position", foreign_keys=[motion_position_id], post_update=True)
    group = relationship("Group", back_populates="devices")
    person = relationship("Person", back_populates="devices")
    overspeed_geofence = relationship("Geofence", foreign_keys=[overspeed_geofence_id])
    # calendar = relationship("Calendar", foreign_keys=[calendar_id])  # TODO: Implement Calendar model
    user_permissions = relationship(
        "User", 
        secondary="user_device_permissions", 
        back_populates="device_permissions"
    )
    
    def is_expired(self) -> bool:
        """Check if device has expired"""
        if self.expiration_time:
            from datetime import datetime
            return datetime.now() > self.expiration_time
        return False
    
    def get_total_distance_km(self) -> float:
        """Get total distance in kilometers"""
        return self.total_distance / 1000.0 if self.total_distance else 0.0
    
    def get_hours_formatted(self) -> str:
        """Get formatted hours (hours:minutes)"""
        if not self.hours:
            return "0:00"
        hours = int(self.hours)
        minutes = int((self.hours - hours) * 60)
        return f"{hours}:{minutes:02d}"

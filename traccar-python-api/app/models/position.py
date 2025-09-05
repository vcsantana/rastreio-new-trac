"""
Position model
"""
from sqlalchemy import Column, Integer, String, Boolean, DateTime, Text, ForeignKey, Float
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.database import Base

class Position(Base):
    __tablename__ = "positions"
    
    id = Column(Integer, primary_key=True, index=True)
    device_id = Column(Integer, ForeignKey("devices.id"), nullable=False, index=True)
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
    
    # Relationships
    device = relationship("Device", back_populates="positions", foreign_keys=[device_id])
    events = relationship("Event", back_populates="position")
    
    def __repr__(self):
        return f"<Position(id={self.id}, device_id={self.device_id}, lat={self.latitude}, lon={self.longitude})>"

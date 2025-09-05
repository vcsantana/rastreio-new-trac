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
    disabled = Column(Boolean, default=False)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Additional attributes (JSON)
    attributes = Column(Text)
    
    # Relationships
    positions = relationship("Position", back_populates="device", cascade="all, delete-orphan")

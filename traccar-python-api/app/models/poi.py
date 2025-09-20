from sqlalchemy import Column, Integer, String, Float, DateTime, Text, Boolean, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database import Base

class POI(Base):
    """Point of Interest model"""
    __tablename__ = "pois"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False, index=True)  # Ex: "CASA", "TRABALHO"
    description = Column(Text)
    
    # Geographic data
    latitude = Column(Float, nullable=False)
    longitude = Column(Float, nullable=False)
    radius = Column(Float, default=100.0)  # Radius in meters
    
    # Ownership
    device_id = Column(Integer, ForeignKey("devices.id"), nullable=False, index=True)
    person_id = Column(Integer, ForeignKey("persons.id"), nullable=True, index=True)
    group_id = Column(Integer, ForeignKey("groups.id"), nullable=True, index=True)
    
    # Configuration
    is_active = Column(Boolean, default=True)
    color = Column(String(7), default="#2196F3")  # Hex color for map display
    icon = Column(String(50), default="location_on")  # Material icon name
    
    # Metadata
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    created_by = Column(Integer, ForeignKey("users.id"))
    
    # Relationships
    device = relationship("Device", back_populates="pois")
    person = relationship("Person", back_populates="pois")
    group = relationship("Group", back_populates="pois")
    creator = relationship("User")
    visits = relationship("POIVisit", back_populates="poi", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<POI(id={self.id}, name='{self.name}', device_id={self.device_id})>"

    @property
    def visit_count(self):
        """Get total number of visits to this POI"""
        return len(self.visits)
    
    @property
    def last_visit(self):
        """Get the most recent visit to this POI"""
        if self.visits:
            return max(self.visits, key=lambda v: v.entry_time)
        return None

class POIVisit(Base):
    """POI Visit tracking model"""
    __tablename__ = "poi_visits"

    id = Column(Integer, primary_key=True, index=True)
    
    # References
    poi_id = Column(Integer, ForeignKey("pois.id"), nullable=False, index=True)
    device_id = Column(Integer, ForeignKey("devices.id"), nullable=False, index=True)
    position_entry_id = Column(Integer, ForeignKey("positions.id"), nullable=True)
    position_exit_id = Column(Integer, ForeignKey("positions.id"), nullable=True)
    
    # Time tracking
    entry_time = Column(DateTime(timezone=True), nullable=False, index=True)
    exit_time = Column(DateTime(timezone=True), nullable=True, index=True)
    duration_minutes = Column(Integer)  # Calculated duration in minutes
    
    # Entry/Exit coordinates (for accuracy tracking)
    entry_latitude = Column(Float)
    entry_longitude = Column(Float)
    exit_latitude = Column(Float)
    exit_longitude = Column(Float)
    
    # Status
    is_active = Column(Boolean, default=True)  # True if still inside POI
    
    # Metadata
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    poi = relationship("POI", back_populates="visits")
    device = relationship("Device")
    entry_position = relationship("Position", foreign_keys=[position_entry_id])
    exit_position = relationship("Position", foreign_keys=[position_exit_id])

    def __repr__(self):
        return f"<POIVisit(id={self.id}, poi_id={self.poi_id}, device_id={self.device_id})>"

    def calculate_duration(self):
        """Calculate and update duration if exit_time is set"""
        if self.exit_time and self.entry_time:
            delta = self.exit_time - self.entry_time
            self.duration_minutes = int(delta.total_seconds() / 60)
            return self.duration_minutes
        return None

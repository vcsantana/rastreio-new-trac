"""
Geofence model
"""
from datetime import datetime
from typing import Optional
from sqlalchemy import Column, Integer, String, DateTime, Text, Boolean, Float
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.database import Base


class Geofence(Base):
    """
    Geofence model representing geographical boundaries for tracking.
    Migrated from org.traccar.model.Geofence
    """
    __tablename__ = "geofences"

    # Primary key
    id = Column(Integer, primary_key=True, index=True)
    
    # Basic information
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    
    # Geofence geometry (GeoJSON format)
    geometry = Column(Text, nullable=False)  # GeoJSON string
    
    # Geofence type and properties
    type = Column(String(50), default="polygon")  # polygon, circle, polyline
    area = Column(Float, nullable=True)  # Calculated area in square meters
    
    # Status and scheduling
    disabled = Column(Boolean, default=False)
    calendar_id = Column(Integer, nullable=True)  # Will link to calendar table later
    
    # Attributes and configuration
    attributes = Column(Text, nullable=True)  # JSON string for additional attributes
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    events = relationship("Event", back_populates="geofence")

    def __init__(self, name: str, geometry: str, **kwargs):
        """
        Initialize Geofence with name and geometry.
        """
        super().__init__(**kwargs)
        self.name = name
        self.geometry = geometry
        self.type = kwargs.get('type', 'polygon')
        self.description = kwargs.get('description')
        self.disabled = kwargs.get('disabled', False)
        self.attributes = kwargs.get('attributes')

    def is_polygon(self) -> bool:
        """Check if geofence is a polygon"""
        return self.type == "polygon"

    def is_circle(self) -> bool:
        """Check if geofence is a circle"""
        return self.type == "circle"

    def is_polyline(self) -> bool:
        """Check if geofence is a polyline"""
        return self.type == "polyline"

    def is_active(self) -> bool:
        """Check if geofence is active (not disabled)"""
        return not self.disabled

    def get_geometry_type(self) -> str:
        """Get the geometry type from GeoJSON"""
        import json
        try:
            geom_data = json.loads(self.geometry)
            return geom_data.get('type', 'Unknown')
        except (json.JSONDecodeError, AttributeError):
            return 'Invalid'

    def get_coordinates(self) -> Optional[list]:
        """Extract coordinates from GeoJSON geometry"""
        import json
        try:
            geom_data = json.loads(self.geometry)
            return geom_data.get('coordinates')
        except (json.JSONDecodeError, AttributeError):
            return None

    def calculate_area(self) -> Optional[float]:
        """
        Calculate area of the geofence in square meters.
        This is a simplified calculation - in production you'd use a proper geospatial library.
        """
        if self.is_circle():
            coords = self.get_coordinates()
            if coords and len(coords) >= 2:
                # For circle: coordinates = [center_lon, center_lat, radius_meters]
                radius = coords[2] if len(coords) > 2 else 1000  # Default 1km radius
                import math
                return math.pi * radius * radius
        
        elif self.is_polygon():
            # For polygon, you'd use a proper geospatial library like Shapely
            # This is a placeholder calculation
            coords = self.get_coordinates()
            if coords and len(coords) > 0:
                # Simplified area calculation (not accurate for real-world use)
                return len(coords[0]) * 10000  # Rough estimate
        
        return None

    def __repr__(self):
        return f"<Geofence(id={self.id}, name='{self.name}', type='{self.type}')>"


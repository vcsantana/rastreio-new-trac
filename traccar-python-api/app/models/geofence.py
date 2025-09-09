"""
Geofence model
"""
import json
from datetime import datetime
from typing import Optional
from sqlalchemy import Column, Integer, String, DateTime, Text, Boolean, Float, Index
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
    
    # Table indexes for performance
    __table_args__ = (
        Index('idx_geofences_disabled', 'disabled'),
        Index('idx_geofences_type', 'type'),
        Index('idx_geofences_calendar_id', 'calendar_id'),
        Index('idx_geofences_created_at', 'created_at'),
        Index('idx_geofences_updated_at', 'updated_at'),
        Index('idx_geofences_active_type', 'disabled', 'type'),
        Index('idx_geofences_active_calendar', 'disabled', 'calendar_id'),
    )

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

    def get_string_attribute(self, key: str, default: str = None) -> str:
        """
        Get a string attribute from the attributes JSON
        
        Args:
            key: Attribute key
            default: Default value if key not found
            
        Returns:
            String value or default
        """
        if not self.attributes:
            return default
        
        try:
            attrs = json.loads(self.attributes)
            value = attrs.get(key, default)
            return str(value) if value is not None else default
        except (json.JSONDecodeError, TypeError):
            return default
    
    def get_double_attribute(self, key: str, default: float = None) -> float:
        """
        Get a double/float attribute from the attributes JSON
        
        Args:
            key: Attribute key
            default: Default value if key not found
            
        Returns:
            Float value or default
        """
        if not self.attributes:
            return default
        
        try:
            attrs = json.loads(self.attributes)
            value = attrs.get(key, default)
            return float(value) if value is not None else default
        except (json.JSONDecodeError, TypeError, ValueError):
            return default
    
    def get_boolean_attribute(self, key: str, default: bool = None) -> bool:
        """
        Get a boolean attribute from the attributes JSON
        
        Args:
            key: Attribute key
            default: Default value if key not found
            
        Returns:
            Boolean value or default
        """
        if not self.attributes:
            return default
        
        try:
            attrs = json.loads(self.attributes)
            value = attrs.get(key, default)
            if isinstance(value, bool):
                return value
            elif isinstance(value, str):
                return value.lower() in ('true', '1', 'yes', 'on')
            elif isinstance(value, (int, float)):
                return bool(value)
            return default
        except (json.JSONDecodeError, TypeError):
            return default
    
    def get_integer_attribute(self, key: str, default: int = None) -> int:
        """
        Get an integer attribute from the attributes JSON
        
        Args:
            key: Attribute key
            default: Default value if key not found
            
        Returns:
            Integer value or default
        """
        if not self.attributes:
            return default
        
        try:
            attrs = json.loads(self.attributes)
            value = attrs.get(key, default)
            return int(value) if value is not None else default
        except (json.JSONDecodeError, TypeError, ValueError):
            return default
    
    def get_json_attribute(self, key: str, default: dict = None) -> dict:
        """
        Get a JSON object attribute from the attributes JSON
        
        Args:
            key: Attribute key
            default: Default value if key not found
            
        Returns:
            Dictionary value or default
        """
        if not self.attributes:
            return default or {}
        
        try:
            attrs = json.loads(self.attributes)
            value = attrs.get(key, default)
            if isinstance(value, dict):
                return value
            elif isinstance(value, str):
                return json.loads(value)
            return default or {}
        except (json.JSONDecodeError, TypeError):
            return default or {}
    
    def set_attribute(self, key: str, value: any) -> None:
        """
        Set an attribute in the attributes JSON
        
        Args:
            key: Attribute key
            value: Attribute value
        """
        try:
            if self.attributes:
                attrs = json.loads(self.attributes)
            else:
                attrs = {}
            
            attrs[key] = value
            self.attributes = json.dumps(attrs)
        except (json.JSONDecodeError, TypeError):
            # If parsing fails, create new attributes dict
            self.attributes = json.dumps({key: value})
    
    def remove_attribute(self, key: str) -> bool:
        """
        Remove an attribute from the attributes JSON
        
        Args:
            key: Attribute key to remove
            
        Returns:
            True if attribute was removed, False if not found
        """
        if not self.attributes:
            return False
        
        try:
            attrs = json.loads(self.attributes)
            if key in attrs:
                del attrs[key]
                self.attributes = json.dumps(attrs)
                return True
            return False
        except (json.JSONDecodeError, TypeError):
            return False
    
    def has_attribute(self, key: str) -> bool:
        """
        Check if an attribute exists in the attributes JSON
        
        Args:
            key: Attribute key to check
            
        Returns:
            True if attribute exists, False otherwise
        """
        if not self.attributes:
            return False
        
        try:
            attrs = json.loads(self.attributes)
            return key in attrs
        except (json.JSONDecodeError, TypeError):
            return False
    
    def get_all_attributes(self) -> dict:
        """
        Get all attributes as a dictionary
        
        Returns:
            Dictionary of all attributes
        """
        if not self.attributes:
            return {}
        
        try:
            return json.loads(self.attributes)
        except (json.JSONDecodeError, TypeError):
            return {}
    
    def set_attributes(self, attributes: dict) -> None:
        """
        Set all attributes from a dictionary
        
        Args:
            attributes: Dictionary of attributes to set
        """
        self.attributes = json.dumps(attributes) if attributes else None
    
    def clear_attributes(self) -> None:
        """
        Clear all attributes
        """
        self.attributes = None

    def __repr__(self):
        return f"<Geofence(id={self.id}, name='{self.name}', type='{self.type}')>"


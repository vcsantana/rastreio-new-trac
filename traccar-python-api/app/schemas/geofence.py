"""
Geofence schemas for API serialization
"""
from datetime import datetime
from typing import Optional, Dict, Any, List
from pydantic import BaseModel, Field, ConfigDict, validator
import json


class GeofenceBase(BaseModel):
    """Base geofence schema"""
    name: str = Field(..., min_length=1, max_length=255, description="Geofence name")
    description: Optional[str] = Field(None, description="Geofence description")
    geometry: str = Field(..., description="GeoJSON geometry string")
    type: str = Field("polygon", description="Geofence type: polygon, circle, or polyline")
    disabled: bool = Field(False, description="Whether geofence is disabled")
    calendar_id: Optional[int] = Field(None, description="Associated calendar ID")
    attributes: Optional[str] = Field(None, description="Additional attributes as JSON")

    @validator('geometry')
    def validate_geometry(cls, v):
        """Validate GeoJSON geometry"""
        try:
            geom_data = json.loads(v)
            if not isinstance(geom_data, dict):
                raise ValueError("Geometry must be a JSON object")
            
            required_fields = ['type', 'coordinates']
            for field in required_fields:
                if field not in geom_data:
                    raise ValueError(f"Geometry must contain '{field}' field")
            
            valid_types = ['Polygon', 'Circle', 'LineString', 'Point']
            if geom_data['type'] not in valid_types:
                raise ValueError(f"Invalid geometry type: {geom_data['type']}")
            
            return v
        except json.JSONDecodeError:
            raise ValueError("Geometry must be valid JSON")

    @validator('type')
    def validate_type(cls, v):
        """Validate geofence type"""
        valid_types = ['polygon', 'circle', 'polyline']
        if v not in valid_types:
            raise ValueError(f"Type must be one of: {valid_types}")
        return v


class GeofenceCreate(GeofenceBase):
    """Schema for creating geofences"""
    pass


class GeofenceUpdate(BaseModel):
    """Schema for updating geofences"""
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = None
    geometry: Optional[str] = None
    type: Optional[str] = None
    disabled: Optional[bool] = None
    calendar_id: Optional[int] = None
    attributes: Optional[str] = None

    @validator('geometry')
    def validate_geometry(cls, v):
        """Validate GeoJSON geometry if provided"""
        if v is None:
            return v
        return GeofenceBase.validate_geometry(cls, v)

    @validator('type')
    def validate_type(cls, v):
        """Validate geofence type if provided"""
        if v is None:
            return v
        return GeofenceBase.validate_type(cls, v)


class GeofenceResponse(GeofenceBase):
    """Schema for geofence responses"""
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    area: Optional[float] = Field(None, description="Calculated area in square meters")
    created_at: datetime
    updated_at: Optional[datetime] = None
    
    # Parsed geometry for easier frontend consumption
    geometry_data: Optional[Dict[str, Any]] = Field(None, description="Parsed geometry data")
    geometry_type: Optional[str] = Field(None, description="Geometry type from GeoJSON")
    coordinates: Optional[List] = Field(None, description="Extracted coordinates")

    def __init__(self, **data):
        super().__init__(**data)
        # Parse geometry for easier access
        if self.geometry:
            try:
                geom_data = json.loads(self.geometry)
                self.geometry_data = geom_data
                self.geometry_type = geom_data.get('type')
                self.coordinates = geom_data.get('coordinates')
            except json.JSONDecodeError:
                pass


class GeofenceListResponse(BaseModel):
    """Schema for paginated geofence list"""
    geofences: List[GeofenceResponse]
    total: int
    page: int
    size: int
    has_next: bool
    has_prev: bool


class GeofenceStatsResponse(BaseModel):
    """Schema for geofence statistics"""
    total_geofences: int
    active_geofences: int
    disabled_geofences: int
    geofences_by_type: Dict[str, int]
    total_area: float


class GeofenceTestRequest(BaseModel):
    """Schema for testing if a point is inside a geofence"""
    latitude: float = Field(..., ge=-90, le=90, description="Latitude to test")
    longitude: float = Field(..., ge=-180, le=180, description="Longitude to test")


class GeofenceTestResponse(BaseModel):
    """Schema for geofence test results"""
    geofence_id: int
    geofence_name: str
    is_inside: bool
    distance: Optional[float] = Field(None, description="Distance to geofence boundary in meters")


# Example GeoJSON geometries for reference
EXAMPLE_GEOMETRIES = {
    "polygon": {
        "type": "Polygon",
        "coordinates": [[
            [-46.6333, -23.5505],
            [-46.6300, -23.5505],
            [-46.6300, -23.5480],
            [-46.6333, -23.5480],
            [-46.6333, -23.5505]
        ]]
    },
    "circle": {
        "type": "Circle",
        "coordinates": [-46.6333, -23.5505, 1000]  # [lon, lat, radius_meters]
    },
    "polyline": {
        "type": "LineString",
        "coordinates": [
            [-46.6333, -23.5505],
            [-46.6300, -23.5480],
            [-46.6250, -23.5450]
        ]
    }
}


"""
Position schemas
"""
from pydantic import BaseModel, validator
from typing import Optional, Dict, Any
from datetime import datetime

class PositionBase(BaseModel):
    device_id: int
    protocol: str
    valid: bool = True
    latitude: float
    longitude: float
    altitude: Optional[float] = 0.0
    speed: Optional[float] = 0.0
    course: Optional[float] = 0.0
    
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
    
    class Config:
        from_attributes = True

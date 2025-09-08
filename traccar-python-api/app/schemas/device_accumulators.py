"""
Device accumulators schemas
"""
from pydantic import BaseModel
from typing import Optional

class DeviceAccumulatorsUpdate(BaseModel):
    """Schema for updating device accumulators"""
    total_distance: Optional[float] = None  # Total distance in meters
    hours: Optional[float] = None  # Total hours of operation

class DeviceAccumulatorsResponse(BaseModel):
    """Schema for device accumulators response"""
    device_id: int
    total_distance: float  # Total distance in meters
    hours: float  # Total hours of operation
    total_distance_km: float  # Total distance in kilometers
    hours_formatted: str  # Formatted hours (hours:minutes)
    
    class Config:
        from_attributes = True

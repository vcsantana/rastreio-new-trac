from typing import Optional, List
from datetime import datetime
from pydantic import BaseModel, validator

# POI Schemas
class POIBase(BaseModel):
    name: str
    description: Optional[str] = None
    latitude: float
    longitude: float
    radius: Optional[float] = 100.0
    device_id: Optional[int] = None
    person_id: Optional[int] = None
    group_id: Optional[int] = None
    is_active: Optional[bool] = True
    color: Optional[str] = "#2196F3"
    icon: Optional[str] = "location_on"

    @validator('radius')
    def validate_radius(cls, v):
        if v is not None and v <= 0:
            raise ValueError('Radius must be greater than 0')
        return v

    @validator('latitude')
    def validate_latitude(cls, v):
        if v < -90 or v > 90:
            raise ValueError('Latitude must be between -90 and 90')
        return v

    @validator('longitude')
    def validate_longitude(cls, v):
        if v < -180 or v > 180:
            raise ValueError('Longitude must be between -180 and 180')
        return v

    @validator('color')
    def validate_color(cls, v):
        if v and not v.startswith('#') or len(v) != 7:
            raise ValueError('Color must be a valid hex color (e.g., #FF0000)')
        return v

class POICreate(POIBase):
    device_id: int  # Required for creation

class POIUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    radius: Optional[float] = None
    is_active: Optional[bool] = None
    color: Optional[str] = None
    icon: Optional[str] = None

class POIResponse(POIBase):
    id: int
    created_at: datetime
    updated_at: Optional[datetime] = None
    created_by: Optional[int] = None
    visit_count: Optional[int] = 0
    last_visit_time: Optional[datetime] = None

    class Config:
        from_attributes = True

# POI Visit Schemas
class POIVisitBase(BaseModel):
    poi_id: int
    device_id: int
    entry_time: datetime
    exit_time: Optional[datetime] = None
    entry_latitude: Optional[float] = None
    entry_longitude: Optional[float] = None
    exit_latitude: Optional[float] = None
    exit_longitude: Optional[float] = None
    is_active: Optional[bool] = True

class POIVisitCreate(POIVisitBase):
    pass

class POIVisitUpdate(BaseModel):
    exit_time: Optional[datetime] = None
    exit_latitude: Optional[float] = None
    exit_longitude: Optional[float] = None
    is_active: Optional[bool] = None

class POIVisitResponse(POIVisitBase):
    id: int
    duration_minutes: Optional[int] = None
    created_at: datetime
    poi_name: Optional[str] = None
    device_name: Optional[str] = None

    class Config:
        from_attributes = True

# POI Statistics and Reports
class POIStats(BaseModel):
    poi_id: int
    poi_name: str
    total_visits: int
    total_duration_minutes: int
    average_duration_minutes: float
    last_visit: Optional[datetime] = None
    most_frequent_day: Optional[str] = None
    most_frequent_hour: Optional[int] = None

class DevicePOIStats(BaseModel):
    device_id: int
    device_name: str
    total_pois: int
    total_visits: int
    most_visited_poi: Optional[str] = None
    average_visits_per_poi: float

class POIReportRequest(BaseModel):
    device_ids: Optional[List[int]] = None
    poi_ids: Optional[List[int]] = None
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    group_by: Optional[str] = "day"  # day, week, month
    include_active_visits: Optional[bool] = True

class POIReportResponse(BaseModel):
    device_stats: List[DevicePOIStats]
    poi_stats: List[POIStats]
    total_visits: int
    total_duration_hours: float
    report_period: str
    generated_at: datetime

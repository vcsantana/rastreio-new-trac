"""
Event schemas for API serialization
"""
from datetime import datetime
from typing import Optional, Dict, Any
from pydantic import BaseModel, Field, ConfigDict


class EventBase(BaseModel):
    """Base event schema"""
    type: str = Field(..., description="Event type")
    event_time: datetime = Field(..., description="When the event occurred")
    device_id: int = Field(..., description="Device ID that triggered the event")
    position_id: Optional[int] = Field(None, description="Associated position ID")
    geofence_id: Optional[int] = Field(None, description="Associated geofence ID")
    maintenance_id: Optional[int] = Field(None, description="Associated maintenance ID")
    attributes: Optional[str] = Field(None, description="Additional event attributes as JSON")


class EventCreate(EventBase):
    """Schema for creating events"""
    pass


class EventUpdate(BaseModel):
    """Schema for updating events"""
    type: Optional[str] = None
    event_time: Optional[datetime] = None
    attributes: Optional[str] = None


class EventResponse(EventBase):
    """Schema for event responses"""
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    created_at: datetime
    updated_at: Optional[datetime] = None
    
    # Include related data when needed
    device_name: Optional[str] = Field(None, description="Device name")
    position_data: Optional[Dict[str, Any]] = Field(None, description="Position data")


class EventListResponse(BaseModel):
    """Schema for paginated event list"""
    events: list[EventResponse]
    total: int
    page: int
    size: int
    has_next: bool
    has_prev: bool


class EventStatsResponse(BaseModel):
    """Schema for event statistics"""
    total_events: int
    events_by_type: Dict[str, int]
    recent_events: list[Dict[str, Any]]
    device_events: Dict[int, int]


# Event type constants for validation
EVENT_TYPES = {
    "commandResult",
    "deviceOnline",
    "deviceUnknown", 
    "deviceOffline",
    "deviceInactive",
    "queuedCommandSent",
    "deviceMoving",
    "deviceStopped",
    "deviceOverspeed",
    "deviceFuelDrop",
    "deviceFuelIncrease",
    "geofenceEnter",
    "geofenceExit",
    "alarm",
    "ignitionOn",
    "ignitionOff",
    "maintenance",
    "driverChanged",
    "media"
}


class EventTypeInfo(BaseModel):
    """Information about event types"""
    type: str
    description: str
    category: str
    severity: str  # low, medium, high, critical


# Event type metadata
EVENT_TYPE_INFO = {
    "deviceOnline": EventTypeInfo(
        type="deviceOnline",
        description="Device came online",
        category="status",
        severity="low"
    ),
    "deviceOffline": EventTypeInfo(
        type="deviceOffline", 
        description="Device went offline",
        category="status",
        severity="medium"
    ),
    "deviceMoving": EventTypeInfo(
        type="deviceMoving",
        description="Device started moving",
        category="motion",
        severity="low"
    ),
    "deviceStopped": EventTypeInfo(
        type="deviceStopped",
        description="Device stopped moving", 
        category="motion",
        severity="low"
    ),
    "deviceOverspeed": EventTypeInfo(
        type="deviceOverspeed",
        description="Device exceeded speed limit",
        category="violation",
        severity="high"
    ),
    "geofenceEnter": EventTypeInfo(
        type="geofenceEnter",
        description="Device entered geofence",
        category="geofence", 
        severity="medium"
    ),
    "geofenceExit": EventTypeInfo(
        type="geofenceExit",
        description="Device exited geofence",
        category="geofence",
        severity="medium"
    ),
    "alarm": EventTypeInfo(
        type="alarm",
        description="Device alarm triggered",
        category="alarm",
        severity="critical"
    ),
    "ignitionOn": EventTypeInfo(
        type="ignitionOn",
        description="Vehicle ignition turned on",
        category="ignition",
        severity="low"
    ),
    "ignitionOff": EventTypeInfo(
        type="ignitionOff",
        description="Vehicle ignition turned off",
        category="ignition", 
        severity="low"
    )
}

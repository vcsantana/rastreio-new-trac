"""
Unknown Device schemas
"""
from pydantic import BaseModel
from typing import Optional, Dict, Any
from datetime import datetime


class UnknownDeviceBase(BaseModel):
    unique_id: str
    protocol: str
    port: int
    protocol_type: str
    client_address: Optional[str] = None
    raw_data: Optional[str] = None
    parsed_data: Optional[Dict[str, Any]] = None
    notes: Optional[str] = None


class UnknownDeviceCreate(UnknownDeviceBase):
    pass


class UnknownDeviceUpdate(BaseModel):
    notes: Optional[str] = None
    is_registered: Optional[bool] = None
    registered_device_id: Optional[int] = None


class UnknownDeviceResponse(UnknownDeviceBase):
    id: int
    first_seen: datetime
    last_seen: datetime
    connection_count: int
    is_registered: bool
    registered_device_id: Optional[int] = None
    
    class Config:
        from_attributes = True


class UnknownDeviceFilter(BaseModel):
    protocol: Optional[str] = None
    port: Optional[int] = None
    protocol_type: Optional[str] = None
    is_registered: Optional[bool] = None
    hours: int = 24  # Show devices seen in last N hours
    limit: int = 100



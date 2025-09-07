"""
Device schemas
"""
from pydantic import BaseModel
from typing import Optional, Dict, Any
from datetime import datetime

class DeviceBase(BaseModel):
    name: str
    unique_id: str
    phone: Optional[str] = None
    model: Optional[str] = None
    contact: Optional[str] = None
    category: Optional[str] = None
    license_plate: Optional[str] = None
    disabled: Optional[bool] = False
    group_id: Optional[int] = None
    person_id: Optional[int] = None

class DeviceCreate(DeviceBase):
    pass

class DeviceUpdate(BaseModel):
    name: Optional[str] = None
    phone: Optional[str] = None
    model: Optional[str] = None
    contact: Optional[str] = None
    category: Optional[str] = None
    license_plate: Optional[str] = None
    disabled: Optional[bool] = None
    group_id: Optional[int] = None
    person_id: Optional[int] = None

class DeviceResponse(DeviceBase):
    id: int
    status: str
    protocol: Optional[str] = None
    last_update: Optional[datetime] = None
    created_at: datetime
    group_name: Optional[str] = None
    person_name: Optional[str] = None
    
    class Config:
        from_attributes = True

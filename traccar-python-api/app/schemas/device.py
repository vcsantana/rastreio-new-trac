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
    disabled: Optional[bool] = False

class DeviceCreate(DeviceBase):
    pass

class DeviceUpdate(BaseModel):
    name: Optional[str] = None
    phone: Optional[str] = None
    model: Optional[str] = None
    contact: Optional[str] = None
    category: Optional[str] = None
    disabled: Optional[bool] = None

class DeviceResponse(DeviceBase):
    id: int
    status: str
    protocol: Optional[str] = None
    last_update: Optional[datetime] = None
    created_at: datetime
    
    class Config:
        from_attributes = True

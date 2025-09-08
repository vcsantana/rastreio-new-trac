"""
Device image schemas
"""
from pydantic import BaseModel
from typing import Optional
from datetime import datetime

class DeviceImageBase(BaseModel):
    description: Optional[str] = None

class DeviceImageCreate(DeviceImageBase):
    pass

class DeviceImageResponse(DeviceImageBase):
    id: int
    device_id: int
    filename: str
    original_filename: str
    content_type: str
    file_size: int
    file_path: str
    created_at: datetime
    
    class Config:
        from_attributes = True

class DeviceImageUpload(BaseModel):
    """Schema for image upload response"""
    id: int
    device_id: int
    filename: str
    original_filename: str
    content_type: str
    file_size: int
    url: str  # URL to access the image
    created_at: datetime
    
    class Config:
        from_attributes = True

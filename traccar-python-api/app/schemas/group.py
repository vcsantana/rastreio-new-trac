"""
Group schemas
"""
from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime

class GroupBase(BaseModel):
    name: str
    description: Optional[str] = None
    disabled: Optional[bool] = False

class GroupCreate(GroupBase):
    pass

class GroupUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    disabled: Optional[bool] = None

class GroupResponse(GroupBase):
    id: int
    created_at: datetime
    updated_at: Optional[datetime] = None
    device_count: Optional[int] = 0

    class Config:
        from_attributes = True

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
    person_id: Optional[int] = None
    parent_id: Optional[int] = None

class GroupCreate(GroupBase):
    pass

class GroupUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    disabled: Optional[bool] = None
    person_id: Optional[int] = None
    parent_id: Optional[int] = None

class GroupResponse(GroupBase):
    id: int
    created_at: datetime
    updated_at: Optional[datetime] = None
    device_count: Optional[int] = 0
    person_name: Optional[str] = None
    parent_name: Optional[str] = None
    children_count: Optional[int] = 0
    level: Optional[int] = 0  # Hierarchical level (0 = root, 1 = first level, etc.)

    class Config:
        from_attributes = True

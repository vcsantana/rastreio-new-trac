"""
User schemas for user management
"""
from pydantic import BaseModel, EmailStr, validator
from typing import Optional, Dict, Any, List
from datetime import datetime


class UserBase(BaseModel):
    email: EmailStr
    name: str
    is_active: bool = True
    is_admin: bool = False
    attributes: Optional[Dict[str, Any]] = None
    phone: Optional[str] = None
    map: Optional[str] = None
    latitude: Optional[str] = "0"
    longitude: Optional[str] = "0"
    zoom: Optional[int] = 0
    coordinate_format: Optional[str] = None
    expiration_time: Optional[datetime] = None
    device_limit: Optional[int] = -1  # -1 = unlimited
    user_limit: Optional[int] = 0  # 0 = no management rights
    device_readonly: Optional[bool] = False
    limit_commands: Optional[bool] = False
    disable_reports: Optional[bool] = False
    fixed_email: Optional[bool] = False
    poi_layer: Optional[str] = None


class UserCreate(UserBase):
    password: str
    
    @validator('password')
    def validate_password(cls, v):
        if len(v) < 6:
            raise ValueError('Password must be at least 6 characters long')
        return v


class UserUpdate(BaseModel):
    email: Optional[EmailStr] = None
    name: Optional[str] = None
    password: Optional[str] = None
    is_active: Optional[bool] = None
    is_admin: Optional[bool] = None
    attributes: Optional[Dict[str, Any]] = None
    phone: Optional[str] = None
    map: Optional[str] = None
    latitude: Optional[str] = None
    longitude: Optional[str] = None
    zoom: Optional[int] = None
    coordinate_format: Optional[str] = None
    expiration_time: Optional[datetime] = None
    device_limit: Optional[int] = None
    user_limit: Optional[int] = None
    device_readonly: Optional[bool] = None
    limit_commands: Optional[bool] = None
    disable_reports: Optional[bool] = None
    fixed_email: Optional[bool] = None
    poi_layer: Optional[str] = None
    
    @validator('password')
    def validate_password(cls, v):
        if v is not None and len(v) < 6:
            raise ValueError('Password must be at least 6 characters long')
        return v


class UserResponse(UserBase):
    id: int
    created_at: datetime
    updated_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True


class UserStats(BaseModel):
    total_users: int
    active_users: int
    admin_users: int
    inactive_users: int


class UserFilter(BaseModel):
    search: Optional[str] = None
    is_active: Optional[bool] = None
    is_admin: Optional[bool] = None
    limit: int = 100
    offset: int = 0


class UserPermissionUpdate(BaseModel):
    device_ids: Optional[List[int]] = None
    group_ids: Optional[List[int]] = None
    managed_user_ids: Optional[List[int]] = None


class UserPermissionResponse(BaseModel):
    device_permissions: List[Dict[str, Any]] = []
    group_permissions: List[Dict[str, Any]] = []
    managed_users: List[Dict[str, Any]] = []
    managers: List[Dict[str, Any]] = []

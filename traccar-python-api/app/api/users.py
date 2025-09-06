"""
User management API endpoints
"""
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, or_, and_
from sqlalchemy.orm import selectinload
from typing import List, Optional
import json

from app.database import get_db
from app.models.user import User
from app.models.device import Device
from app.models.group import Group
from app.models.user_permission import user_device_permissions, user_group_permissions, user_managed_users
from app.schemas.user import (
    UserCreate, UserUpdate, UserResponse, UserStats, UserFilter,
    UserPermissionUpdate, UserPermissionResponse
)
from app.api.auth import get_current_user, get_password_hash

router = APIRouter()


@router.get("/", response_model=List[UserResponse])
async def get_users(
    search: Optional[str] = Query(None, description="Search in name, email"),
    is_active: Optional[bool] = Query(None, description="Filter by active status"),
    is_admin: Optional[bool] = Query(None, description="Filter by admin status"),
    limit: int = Query(100, ge=1, le=1000, description="Maximum number of results"),
    offset: int = Query(0, ge=0, description="Number of results to skip"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get all users with optional filters"""
    if not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required"
        )
    
    query = select(User)
    
    # Apply filters
    conditions = []
    if is_active is not None:
        conditions.append(User.is_active == is_active)
    if is_admin is not None:
        conditions.append(User.is_admin == is_admin)
    if search:
        search_condition = or_(
            User.name.ilike(f"%{search}%"),
            User.email.ilike(f"%{search}%")
        )
        conditions.append(search_condition)
    
    if conditions:
        query = query.where(*conditions)
    
    query = query.order_by(User.name).offset(offset).limit(limit)
    
    result = await db.execute(query)
    users = result.scalars().all()
    
    return users


@router.get("/stats", response_model=UserStats)
async def get_user_stats(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get user statistics"""
    if not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required"
        )
    
    # Get total users
    total_result = await db.execute(select(func.count(User.id)))
    total_users = total_result.scalar()
    
    # Get active users
    active_result = await db.execute(
        select(func.count(User.id)).where(User.is_active == True)
    )
    active_users = active_result.scalar()
    
    # Get admin users
    admin_result = await db.execute(
        select(func.count(User.id)).where(User.is_admin == True)
    )
    admin_users = admin_result.scalar()
    
    # Get inactive users
    inactive_users = total_users - active_users
    
    return UserStats(
        total_users=total_users,
        active_users=active_users,
        admin_users=admin_users,
        inactive_users=inactive_users
    )


@router.get("/{user_id}", response_model=UserResponse)
async def get_user(
    user_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get a specific user by ID"""
    if not current_user.is_admin and current_user.id != user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied"
        )
    
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    return user


@router.post("/", response_model=UserResponse)
async def create_user(
    user_create: UserCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Create a new user"""
    if not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required"
        )
    
    # Check if user already exists
    result = await db.execute(select(User).where(User.email == user_create.email))
    if result.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User with this email already exists"
        )
    
    # Create new user
    hashed_password = get_password_hash(user_create.password)
    db_user = User(
        email=user_create.email,
        name=user_create.name,
        password_hash=hashed_password,
        is_active=user_create.is_active,
        is_admin=user_create.is_admin,
        phone=user_create.phone,
        map=user_create.map,
        latitude=user_create.latitude,
        longitude=user_create.longitude,
        zoom=user_create.zoom,
        coordinate_format=user_create.coordinate_format,
        expiration_time=user_create.expiration_time,
        device_limit=user_create.device_limit,
        user_limit=user_create.user_limit,
        device_readonly=user_create.device_readonly,
        limit_commands=user_create.limit_commands,
        disable_reports=user_create.disable_reports,
        fixed_email=user_create.fixed_email,
        poi_layer=user_create.poi_layer,
        attributes=json.dumps(user_create.attributes) if user_create.attributes else None
    )
    
    db.add(db_user)
    await db.commit()
    await db.refresh(db_user)
    
    return db_user


@router.put("/{user_id}", response_model=UserResponse)
async def update_user(
    user_id: int,
    user_update: UserUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Update a user"""
    if not current_user.is_admin and current_user.id != user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied"
        )
    
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    # Check email uniqueness if being updated
    if user_update.email and user_update.email != user.email:
        existing_result = await db.execute(
            select(User).where(User.email == user_update.email)
        )
        if existing_result.scalar_one_or_none():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="User with this email already exists"
            )
    
    # Update user
    update_data = user_update.dict(exclude_unset=True)
    for field, value in update_data.items():
        if field == "password" and value:
            setattr(user, "password_hash", get_password_hash(value))
        elif field == "attributes" and value is not None:
            setattr(user, field, json.dumps(value))
        else:
            setattr(user, field, value)
    
    await db.commit()
    await db.refresh(user)
    
    return user


@router.delete("/{user_id}")
async def delete_user(
    user_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Delete a user"""
    if not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required"
        )
    
    if current_user.id == user_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot delete your own account"
        )
    
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    await db.delete(user)
    await db.commit()
    
    return {"message": "User deleted successfully"}


@router.get("/{user_id}/permissions", response_model=UserPermissionResponse)
async def get_user_permissions(
    user_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get user permissions (devices, groups, managed users)"""
    if not current_user.is_admin and current_user.id != user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied"
        )
    
    result = await db.execute(
        select(User)
        .options(
            selectinload(User.device_permissions),
            selectinload(User.group_permissions),
            selectinload(User.managed_users),
            selectinload(User.managers)
        )
        .where(User.id == user_id)
    )
    user = result.scalar_one_or_none()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    return UserPermissionResponse(
        device_permissions=[
            {"id": device.id, "name": device.name, "unique_id": device.unique_id}
            for device in user.device_permissions
        ],
        group_permissions=[
            {"id": group.id, "name": group.name, "description": group.description}
            for group in user.group_permissions
        ],
        managed_users=[
            {"id": managed.id, "name": managed.name, "email": managed.email}
            for managed in user.managed_users
        ],
        managers=[
            {"id": manager.id, "name": manager.name, "email": manager.email}
            for manager in user.managers
        ]
    )


@router.put("/{user_id}/permissions")
async def update_user_permissions(
    user_id: int,
    permission_update: UserPermissionUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Update user permissions"""
    if not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required"
        )
    
    result = await db.execute(
        select(User)
        .options(
            selectinload(User.device_permissions),
            selectinload(User.group_permissions),
            selectinload(User.managed_users)
        )
        .where(User.id == user_id)
    )
    user = result.scalar_one_or_none()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    # Update device permissions
    if permission_update.device_ids is not None:
        # Clear existing device permissions
        user.device_permissions.clear()
        
        # Add new device permissions
        if permission_update.device_ids:
            device_result = await db.execute(
                select(Device).where(Device.id.in_(permission_update.device_ids))
            )
            devices = device_result.scalars().all()
            user.device_permissions.extend(devices)
    
    # Update group permissions
    if permission_update.group_ids is not None:
        # Clear existing group permissions
        user.group_permissions.clear()
        
        # Add new group permissions
        if permission_update.group_ids:
            group_result = await db.execute(
                select(Group).where(Group.id.in_(permission_update.group_ids))
            )
            groups = group_result.scalars().all()
            user.group_permissions.extend(groups)
    
    # Update managed users
    if permission_update.managed_user_ids is not None:
        # Clear existing managed users
        user.managed_users.clear()
        
        # Add new managed users
        if permission_update.managed_user_ids:
            managed_result = await db.execute(
                select(User).where(User.id.in_(permission_update.managed_user_ids))
            )
            managed_users = managed_result.scalars().all()
            user.managed_users.extend(managed_users)
    
    await db.commit()
    
    return {"message": "User permissions updated successfully"}



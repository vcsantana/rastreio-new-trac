"""
Groups API endpoints
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from typing import List

from app.database import get_db
from app.models.user import User
from app.models.group import Group
from app.models.device import Device
from app.schemas.group import GroupCreate, GroupUpdate, GroupResponse
from app.api.auth import get_current_user

router = APIRouter()

@router.get("/", response_model=List[GroupResponse])
async def get_groups(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get all groups"""
    result = await db.execute(
        select(Group, func.count(Device.id).label('device_count'))
        .outerjoin(Device, Group.id == Device.group_id)
        .group_by(Group.id)
        .order_by(Group.name)
    )
    groups_with_counts = result.all()
    
    groups = []
    for group, device_count in groups_with_counts:
        group_dict = {
            "id": group.id,
            "name": group.name,
            "description": group.description,
            "disabled": group.disabled,
            "created_at": group.created_at,
            "updated_at": group.updated_at,
            "device_count": device_count
        }
        groups.append(GroupResponse(**group_dict))
    
    return groups

@router.post("/", response_model=GroupResponse)
async def create_group(
    group_create: GroupCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Create a new group"""
    # Check if group name already exists
    result = await db.execute(select(Group).where(Group.name == group_create.name))
    if result.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Group with this name already exists"
        )
    
    # Create group
    db_group = Group(**group_create.dict())
    db.add(db_group)
    await db.commit()
    await db.refresh(db_group)
    
    return GroupResponse(
        id=db_group.id,
        name=db_group.name,
        description=db_group.description,
        disabled=db_group.disabled,
        created_at=db_group.created_at,
        updated_at=db_group.updated_at,
        device_count=0
    )

@router.get("/{group_id}", response_model=GroupResponse)
async def get_group(
    group_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get a specific group"""
    result = await db.execute(select(Group).where(Group.id == group_id))
    group = result.scalar_one_or_none()
    
    if not group:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Group not found"
        )
    
    # Get device count
    device_count_result = await db.execute(
        select(func.count(Device.id)).where(Device.group_id == group_id)
    )
    device_count = device_count_result.scalar() or 0
    
    return GroupResponse(
        id=group.id,
        name=group.name,
        description=group.description,
        disabled=group.disabled,
        created_at=group.created_at,
        updated_at=group.updated_at,
        device_count=device_count
    )

@router.put("/{group_id}", response_model=GroupResponse)
async def update_group(
    group_id: int,
    group_update: GroupUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Update a group"""
    result = await db.execute(select(Group).where(Group.id == group_id))
    group = result.scalar_one_or_none()
    
    if not group:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Group not found"
        )
    
    # Check if new name already exists (if name is being updated)
    if group_update.name and group_update.name != group.name:
        existing_result = await db.execute(
            select(Group).where(Group.name == group_update.name)
        )
        if existing_result.scalar_one_or_none():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Group with this name already exists"
            )
    
    # Update group
    update_data = group_update.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(group, field, value)
    
    await db.commit()
    await db.refresh(group)
    
    # Get device count
    device_count_result = await db.execute(
        select(func.count(Device.id)).where(Device.group_id == group_id)
    )
    device_count = device_count_result.scalar() or 0
    
    return GroupResponse(
        id=group.id,
        name=group.name,
        description=group.description,
        disabled=group.disabled,
        created_at=group.created_at,
        updated_at=group.updated_at,
        device_count=device_count
    )

@router.delete("/{group_id}")
async def delete_group(
    group_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Delete a group"""
    result = await db.execute(select(Group).where(Group.id == group_id))
    group = result.scalar_one_or_none()
    
    if not group:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Group not found"
        )
    
    # Check if group has devices
    device_count_result = await db.execute(
        select(func.count(Device.id)).where(Device.group_id == group_id)
    )
    device_count = device_count_result.scalar() or 0
    
    if device_count > 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot delete group with devices. Please move or delete devices first."
        )
    
    await db.delete(group)
    await db.commit()
    
    return {"message": "Group deleted successfully"}

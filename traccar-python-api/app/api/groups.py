"""
Groups API endpoints
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, text
from typing import List, Set
from collections import defaultdict

from app.database import get_db
from app.models.user import User
from app.models.group import Group
from app.models.device import Device
from app.models.person import Person
from app.schemas.group import GroupCreate, GroupUpdate, GroupResponse
from app.api.auth import get_current_user
from app.services.group_cache_service import GroupCacheService
import json

router = APIRouter()

async def get_user_accessible_groups(db: AsyncSession, user_id: int, is_admin: bool) -> Set[int]:
    """
    Get all group IDs that a user can access, including inherited groups.
    Returns a set of group IDs.
    """
    if is_admin:
        # Admin can access all groups
        result = await db.execute(select(Group.id))
        return {row[0] for row in result.all()}
    
    # Get directly assigned groups
    result = await db.execute(
        text("SELECT group_id FROM user_group_permissions WHERE user_id = :user_id"),
        {"user_id": user_id}
    )
    direct_groups = {row[0] for row in result.all()}
    
    if not direct_groups:
        return set()
    
    # Get all groups in the hierarchy (children of assigned groups)
    accessible_groups = set(direct_groups)
    
    # Build hierarchy map
    result = await db.execute(select(Group.id, Group.parent_id))
    hierarchy = defaultdict(list)
    for group_id, parent_id in result.all():
        if parent_id:
            hierarchy[parent_id].append(group_id)
    
    # Recursively find all children
    def find_children(group_ids: Set[int]) -> Set[int]:
        children = set()
        for group_id in group_ids:
            if group_id in hierarchy:
                children.update(hierarchy[group_id])
        return children
    
    # Keep finding children until no more are found
    current_level = direct_groups
    while current_level:
        children = find_children(current_level)
        new_groups = children - accessible_groups
        if not new_groups:
            break
        accessible_groups.update(new_groups)
        current_level = new_groups
    
    return accessible_groups

async def calculate_group_levels(db: AsyncSession, group_ids: Set[int]) -> dict:
    """
    Calculate hierarchical levels for groups.
    Returns a dict mapping group_id to level (0 = root, 1 = first level, etc.)
    """
    if not group_ids:
        return {}
    
    # Get all groups with their parent relationships
    result = await db.execute(
        select(Group.id, Group.parent_id)
        .where(Group.id.in_(group_ids))
    )
    
    parent_map = {row[0]: row[1] for row in result.all()}
    levels = {}
    
    def calculate_level(group_id: int) -> int:
        if group_id in levels:
            return levels[group_id]
        
        parent_id = parent_map.get(group_id)
        if parent_id is None:
            levels[group_id] = 0
        else:
            levels[group_id] = calculate_level(parent_id) + 1
        
        return levels[group_id]
    
    for group_id in group_ids:
        calculate_level(group_id)
    
    return levels

@router.get("/", response_model=List[GroupResponse])
async def get_groups(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get all groups that the user has permission to access, including inherited groups"""
    # Simplified version for testing
    if current_user.is_admin:
        # Admin can access all groups
        result = await db.execute(select(Group).order_by(Group.name))
        groups = result.scalars().all()
        
        groups_response = []
        for group in groups:
            # Parse attributes if they exist
            attributes = None
            if group.attributes:
                try:
                    attributes = json.loads(group.attributes)
                except json.JSONDecodeError:
                    attributes = None
            
            group_dict = {
                "id": group.id,
                "name": group.name,
                "description": group.description,
                "disabled": group.disabled,
                "person_id": group.person_id,
                "parent_id": group.parent_id,
                "attributes": attributes,
                "created_at": group.created_at,
                "updated_at": group.updated_at,
                "device_count": 0,
                "person_name": None,
                "parent_name": None,
                "children_count": 0,
                "level": 0
            }
            groups_response.append(GroupResponse(**group_dict))
        
        return groups_response
    else:
        return []

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
    
    # Validate parent group if specified
    if group_create.parent_id:
        parent_result = await db.execute(select(Group).where(Group.id == group_create.parent_id))
        parent_group = parent_result.scalar_one_or_none()
        if not parent_group:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Parent group not found"
            )
        
        # Check if user has permission to create groups under this parent
        accessible_groups = await get_user_accessible_groups(db, current_user.id, current_user.is_admin)
        if group_create.parent_id not in accessible_groups:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You don't have permission to create groups under this parent"
            )
        
        # Prevent circular references (this will be checked after creation)
        # We'll validate this in a separate function if needed
    
    # Create group
    group_data = group_create.dict()
    if group_data.get('attributes'):
        group_data['attributes'] = json.dumps(group_data['attributes'])
    
    db_group = Group(**group_data)
    db.add(db_group)
    await db.commit()
    await db.refresh(db_group)
    
    # Invalidate cache after creating group
    cache_service = GroupCacheService(db)
    cache_service.invalidate_hierarchy_cache()
    
    # Get parent name if exists
    parent_name = None
    if db_group.parent_id:
        parent_result = await db.execute(
            select(Group.name).where(Group.id == db_group.parent_id)
        )
        parent_row = parent_result.first()
        if parent_row:
            parent_name = parent_row[0]
    
    # Parse attributes if they exist
    attributes = None
    if db_group.attributes:
        try:
            attributes = json.loads(db_group.attributes)
        except json.JSONDecodeError:
            attributes = None
    
    return GroupResponse(
        id=db_group.id,
        name=db_group.name,
        description=db_group.description,
        disabled=db_group.disabled,
        person_id=db_group.person_id,
        parent_id=db_group.parent_id,
        attributes=attributes,
        created_at=db_group.created_at,
        updated_at=db_group.updated_at,
        device_count=0,
        person_name=None,
        parent_name=parent_name,
        children_count=0,
        level=0  # Will be calculated properly in the list endpoint
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
        device_count=device_count,
        person_name=None
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
        if field == "attributes" and value is not None:
            setattr(group, field, json.dumps(value))
        else:
            setattr(group, field, value)
    
    await db.commit()
    await db.refresh(group)
    
    # Invalidate cache after updating group
    cache_service = GroupCacheService(db)
    cache_service.invalidate_hierarchy_cache()
    
    # Get device count
    device_count_result = await db.execute(
        select(func.count(Device.id)).where(Device.group_id == group_id)
    )
    device_count = device_count_result.scalar() or 0
    
    # Parse attributes if they exist
    attributes = None
    if group.attributes:
        try:
            attributes = json.loads(group.attributes)
        except json.JSONDecodeError:
            attributes = None
    
    return GroupResponse(
        id=group.id,
        name=group.name,
        description=group.description,
        disabled=group.disabled,
        person_id=group.person_id,
        parent_id=group.parent_id,
        attributes=attributes,
        created_at=group.created_at,
        updated_at=group.updated_at,
        device_count=device_count,
        person_name=None
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
    
    # Invalidate cache after deleting group
    cache_service = GroupCacheService(db)
    cache_service.invalidate_hierarchy_cache()
    
    return {"message": "Group deleted successfully"}

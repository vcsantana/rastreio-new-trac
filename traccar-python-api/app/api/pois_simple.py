from typing import List, Optional
from datetime import datetime, timedelta
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import and_, func, desc, select

from app.database import get_db
from app.models.poi import POI, POIVisit
from app.models.device import Device
from app.schemas.poi import POICreate, POIUpdate, POIResponse
from app.api.auth import get_current_user
from app.models.user import User

router = APIRouter()

# POI CRUD Operations
@router.get("/", response_model=List[POIResponse])
async def get_pois(
    device_id: Optional[int] = Query(None, description="Filter by device ID"),
    is_active: Optional[bool] = Query(None, description="Filter by active status"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get all POIs with optional filters"""
    query = select(POI)
    
    if device_id:
        query = query.where(POI.device_id == device_id)
    if is_active is not None:
        query = query.where(POI.is_active == is_active)
    
    query = query.order_by(POI.name)
    result = await db.execute(query)
    pois = result.scalars().all()
    
    # Convert to response format
    response_list = []
    for poi in pois:
        poi_dict = {
            "id": poi.id,
            "name": poi.name,
            "description": poi.description,
            "latitude": poi.latitude,
            "longitude": poi.longitude,
            "radius": poi.radius,
            "device_id": poi.device_id,
            "person_id": poi.person_id,
            "group_id": poi.group_id,
            "is_active": poi.is_active,
            "color": poi.color,
            "icon": poi.icon,
            "created_at": poi.created_at,
            "updated_at": poi.updated_at,
            "created_by": poi.created_by,
            "visit_count": 0,
            "last_visit_time": None
        }
        response_list.append(POIResponse(**poi_dict))
    
    return response_list

@router.post("/", response_model=POIResponse)
async def create_poi(
    poi: POICreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Create a new POI"""
    # Verify device exists
    device_query = select(Device).where(Device.id == poi.device_id)
    device_result = await db.execute(device_query)
    device = device_result.scalar_one_or_none()
    
    if not device:
        raise HTTPException(status_code=404, detail="Device not found")
    
    # Create POI
    db_poi = POI(
        name=poi.name,
        description=poi.description,
        latitude=poi.latitude,
        longitude=poi.longitude,
        radius=poi.radius,
        device_id=poi.device_id,
        person_id=poi.person_id,
        group_id=poi.group_id,
        is_active=poi.is_active,
        color=poi.color,
        icon=poi.icon,
        created_by=current_user.id
    )
    
    db.add(db_poi)
    await db.commit()
    await db.refresh(db_poi)
    
    # Convert to response format
    poi_dict = {
        "id": db_poi.id,
        "name": db_poi.name,
        "description": db_poi.description,
        "latitude": db_poi.latitude,
        "longitude": db_poi.longitude,
        "radius": db_poi.radius,
        "device_id": db_poi.device_id,
        "person_id": db_poi.person_id,
        "group_id": db_poi.group_id,
        "is_active": db_poi.is_active,
        "color": db_poi.color,
        "icon": db_poi.icon,
        "created_at": db_poi.created_at,
        "updated_at": db_poi.updated_at,
        "created_by": db_poi.created_by,
        "visit_count": 0,
        "last_visit_time": None
    }
    
    return POIResponse(**poi_dict)

@router.get("/{poi_id}", response_model=POIResponse)
async def get_poi(
    poi_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get a specific POI by ID"""
    query = select(POI).where(POI.id == poi_id)
    result = await db.execute(query)
    poi = result.scalar_one_or_none()
    
    if not poi:
        raise HTTPException(status_code=404, detail="POI not found")
    
    poi_dict = {
        "id": poi.id,
        "name": poi.name,
        "description": poi.description,
        "latitude": poi.latitude,
        "longitude": poi.longitude,
        "radius": poi.radius,
        "device_id": poi.device_id,
        "person_id": poi.person_id,
        "group_id": poi.group_id,
        "is_active": poi.is_active,
        "color": poi.color,
        "icon": poi.icon,
        "created_at": poi.created_at,
        "updated_at": poi.updated_at,
        "created_by": poi.created_by,
        "visit_count": 0,
        "last_visit_time": None
    }
    
    return POIResponse(**poi_dict)

@router.put("/{poi_id}", response_model=POIResponse)
async def update_poi(
    poi_id: int,
    poi_update: POIUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Update a POI"""
    query = select(POI).where(POI.id == poi_id)
    result = await db.execute(query)
    poi = result.scalar_one_or_none()
    
    if not poi:
        raise HTTPException(status_code=404, detail="POI not found")
    
    # Update fields
    update_data = poi_update.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(poi, field, value)
    
    await db.commit()
    await db.refresh(poi)
    
    poi_dict = {
        "id": poi.id,
        "name": poi.name,
        "description": poi.description,
        "latitude": poi.latitude,
        "longitude": poi.longitude,
        "radius": poi.radius,
        "device_id": poi.device_id,
        "person_id": poi.person_id,
        "group_id": poi.group_id,
        "is_active": poi.is_active,
        "color": poi.color,
        "icon": poi.icon,
        "created_at": poi.created_at,
        "updated_at": poi.updated_at,
        "created_by": poi.created_by,
        "visit_count": 0,
        "last_visit_time": None
    }
    
    return POIResponse(**poi_dict)

@router.delete("/{poi_id}")
async def delete_poi(
    poi_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Delete a POI"""
    query = select(POI).where(POI.id == poi_id)
    result = await db.execute(query)
    poi = result.scalar_one_or_none()
    
    if not poi:
        raise HTTPException(status_code=404, detail="POI not found")
    
    await db.delete(poi)
    await db.commit()
    
    return {"message": "POI deleted successfully"}

from typing import List, Optional
from datetime import datetime, timedelta
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import and_, func, desc, select

from app.database import get_async_db
from app.models.poi import POI, POIVisit
from app.models.device import Device
from app.models.position import Position
from app.schemas.poi import (
    POICreate, POIUpdate, POIResponse, 
    POIVisitCreate, POIVisitUpdate, POIVisitResponse,
    POIStats, DevicePOIStats, POIReportRequest, POIReportResponse
)
from app.api.auth import get_current_user
from app.models.user import User

router = APIRouter()

# POI CRUD Operations
@router.get("/", response_model=List[POIResponse])
async def get_pois(
    device_id: Optional[int] = Query(None, description="Filter by device ID"),
    person_id: Optional[int] = Query(None, description="Filter by person ID"),
    group_id: Optional[int] = Query(None, description="Filter by group ID"),
    is_active: Optional[bool] = Query(None, description="Filter by active status"),
    db: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(get_current_user)
):
    """Get all POIs with optional filters"""
    query = select(POI)
    
    if device_id:
        query = query.where(POI.device_id == device_id)
    if person_id:
        query = query.where(POI.person_id == person_id)
    if group_id:
        query = query.where(POI.group_id == group_id)
    if is_active is not None:
        query = query.where(POI.is_active == is_active)
    
    query = query.order_by(POI.name)
    result = await db.execute(query)
    pois = result.scalars().all()
    
    # Add visit statistics
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
            "visit_count": 0,  # Will be calculated separately if needed
            "last_visit_time": None
        }
        response_list.append(POIResponse(**poi_dict))
    
    return response_list

@router.post("/", response_model=POIResponse)
async def create_poi(
    poi: POICreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Create a new POI"""
    # Verify device exists
    device = db.query(Device).filter(Device.id == poi.device_id).first()
    if not device:
        raise HTTPException(status_code=404, detail="Device not found")
    
    # Create POI
    db_poi = POI(
        **poi.dict(),
        created_by=current_user.id
    )
    db.add(db_poi)
    db.commit()
    db.refresh(db_poi)
    
    return POIResponse.from_orm(db_poi)

@router.get("/{poi_id}", response_model=POIResponse)
async def get_poi(
    poi_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get a specific POI by ID"""
    poi = db.query(POI).filter(POI.id == poi_id).first()
    if not poi:
        raise HTTPException(status_code=404, detail="POI not found")
    
    poi_data = POIResponse.from_orm(poi)
    poi_data.visit_count = len(poi.visits)
    poi_data.last_visit_time = poi.last_visit.entry_time if poi.last_visit else None
    
    return poi_data

@router.put("/{poi_id}", response_model=POIResponse)
async def update_poi(
    poi_id: int,
    poi_update: POIUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Update a POI"""
    poi = db.query(POI).filter(POI.id == poi_id).first()
    if not poi:
        raise HTTPException(status_code=404, detail="POI not found")
    
    # Update fields
    for field, value in poi_update.dict(exclude_unset=True).items():
        setattr(poi, field, value)
    
    db.commit()
    db.refresh(poi)
    
    return POIResponse.from_orm(poi)

@router.delete("/{poi_id}")
async def delete_poi(
    poi_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Delete a POI"""
    poi = db.query(POI).filter(POI.id == poi_id).first()
    if not poi:
        raise HTTPException(status_code=404, detail="POI not found")
    
    db.delete(poi)
    db.commit()
    
    return {"message": "POI deleted successfully"}

# POI Visit Operations
@router.get("/{poi_id}/visits", response_model=List[POIVisitResponse])
async def get_poi_visits(
    poi_id: int,
    start_date: Optional[datetime] = Query(None, description="Filter visits from this date"),
    end_date: Optional[datetime] = Query(None, description="Filter visits until this date"),
    is_active: Optional[bool] = Query(None, description="Filter by active status"),
    limit: int = Query(100, description="Limit number of results"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get visits for a specific POI"""
    query = db.query(POIVisit).filter(POIVisit.poi_id == poi_id)
    
    if start_date:
        query = query.filter(POIVisit.entry_time >= start_date)
    if end_date:
        query = query.filter(POIVisit.entry_time <= end_date)
    if is_active is not None:
        query = query.filter(POIVisit.is_active == is_active)
    
    visits = query.order_by(desc(POIVisit.entry_time)).limit(limit).all()
    
    # Enrich with POI and device names
    result = []
    for visit in visits:
        visit_data = POIVisitResponse.from_orm(visit)
        visit_data.poi_name = visit.poi.name if visit.poi else None
        visit_data.device_name = visit.device.name if visit.device else None
        result.append(visit_data)
    
    return result

@router.post("/visits", response_model=POIVisitResponse)
async def create_poi_visit(
    visit: POIVisitCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Create a new POI visit (usually called by position processing)"""
    # Verify POI and device exist
    poi = db.query(POI).filter(POI.id == visit.poi_id).first()
    if not poi:
        raise HTTPException(status_code=404, detail="POI not found")
    
    device = db.query(Device).filter(Device.id == visit.device_id).first()
    if not device:
        raise HTTPException(status_code=404, detail="Device not found")
    
    # Create visit
    db_visit = POIVisit(**visit.dict())
    db.add(db_visit)
    db.commit()
    db.refresh(db_visit)
    
    return POIVisitResponse.from_orm(db_visit)

@router.put("/visits/{visit_id}", response_model=POIVisitResponse)
async def update_poi_visit(
    visit_id: int,
    visit_update: POIVisitUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Update a POI visit (usually to set exit time)"""
    visit = db.query(POIVisit).filter(POIVisit.id == visit_id).first()
    if not visit:
        raise HTTPException(status_code=404, detail="POI visit not found")
    
    # Update fields
    for field, value in visit_update.dict(exclude_unset=True).items():
        setattr(visit, field, value)
    
    # Calculate duration if exit_time is set
    if visit.exit_time and visit.entry_time:
        visit.calculate_duration()
        visit.is_active = False
    
    db.commit()
    db.refresh(visit)
    
    return POIVisitResponse.from_orm(visit)

# POI Statistics and Reports
@router.get("/device/{device_id}/stats", response_model=DevicePOIStats)
async def get_device_poi_stats(
    device_id: int,
    days: int = Query(30, description="Number of days to analyze"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get POI statistics for a specific device"""
    device = db.query(Device).filter(Device.id == device_id).first()
    if not device:
        raise HTTPException(status_code=404, detail="Device not found")
    
    start_date = datetime.utcnow() - timedelta(days=days)
    
    # Get POI count
    total_pois = db.query(POI).filter(POI.device_id == device_id, POI.is_active == True).count()
    
    # Get visit count
    total_visits = db.query(POIVisit).filter(
        POIVisit.device_id == device_id,
        POIVisit.entry_time >= start_date
    ).count()
    
    # Get most visited POI
    most_visited = db.query(
        POI.name,
        func.count(POIVisit.id).label('visit_count')
    ).join(POIVisit).filter(
        POI.device_id == device_id,
        POIVisit.entry_time >= start_date
    ).group_by(POI.id, POI.name).order_by(desc('visit_count')).first()
    
    return DevicePOIStats(
        device_id=device_id,
        device_name=device.name,
        total_pois=total_pois,
        total_visits=total_visits,
        most_visited_poi=most_visited.name if most_visited else None,
        average_visits_per_poi=total_visits / total_pois if total_pois > 0 else 0
    )

@router.post("/reports", response_model=POIReportResponse)
async def generate_poi_report(
    report_request: POIReportRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Generate comprehensive POI report"""
    # Set default date range if not provided
    if not report_request.end_date:
        report_request.end_date = datetime.utcnow()
    if not report_request.start_date:
        report_request.start_date = report_request.end_date - timedelta(days=30)
    
    # Build base query
    visits_query = db.query(POIVisit).filter(
        POIVisit.entry_time >= report_request.start_date,
        POIVisit.entry_time <= report_request.end_date
    )
    
    if report_request.device_ids:
        visits_query = visits_query.filter(POIVisit.device_id.in_(report_request.device_ids))
    if report_request.poi_ids:
        visits_query = visits_query.filter(POIVisit.poi_id.in_(report_request.poi_ids))
    if not report_request.include_active_visits:
        visits_query = visits_query.filter(POIVisit.is_active == False)
    
    # Get device statistics
    device_stats = []
    if report_request.device_ids:
        for device_id in report_request.device_ids:
            stats = await get_device_poi_stats(device_id, 30, db, current_user)
            device_stats.append(stats)
    
    # Get POI statistics
    poi_stats = []
    poi_data = db.query(
        POI.id,
        POI.name,
        func.count(POIVisit.id).label('total_visits'),
        func.sum(POIVisit.duration_minutes).label('total_duration'),
        func.avg(POIVisit.duration_minutes).label('avg_duration'),
        func.max(POIVisit.entry_time).label('last_visit')
    ).join(POIVisit).filter(
        POIVisit.entry_time >= report_request.start_date,
        POIVisit.entry_time <= report_request.end_date
    ).group_by(POI.id, POI.name).all()
    
    for poi in poi_data:
        poi_stats.append(POIStats(
            poi_id=poi.id,
            poi_name=poi.name,
            total_visits=poi.total_visits or 0,
            total_duration_minutes=poi.total_duration or 0,
            average_duration_minutes=poi.avg_duration or 0,
            last_visit=poi.last_visit
        ))
    
    # Calculate totals
    total_visits = visits_query.count()
    total_duration = db.query(func.sum(POIVisit.duration_minutes)).filter(
        POIVisit.entry_time >= report_request.start_date,
        POIVisit.entry_time <= report_request.end_date
    ).scalar() or 0
    
    return POIReportResponse(
        device_stats=device_stats,
        poi_stats=poi_stats,
        total_visits=total_visits,
        total_duration_hours=total_duration / 60,
        report_period=f"{report_request.start_date.date()} to {report_request.end_date.date()}",
        generated_at=datetime.utcnow()
    )

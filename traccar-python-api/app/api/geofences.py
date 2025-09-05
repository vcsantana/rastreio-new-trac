"""
Geofences API endpoints
"""
from datetime import datetime
from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, desc, func

from app.database import get_db
from app.models import Geofence, Event, User
from app.schemas.geofence import (
    GeofenceResponse, 
    GeofenceCreate, 
    GeofenceUpdate, 
    GeofenceListResponse,
    GeofenceStatsResponse,
    GeofenceTestRequest,
    GeofenceTestResponse,
    EXAMPLE_GEOMETRIES
)
from app.api.auth import get_current_user

router = APIRouter(prefix="/geofences", tags=["geofences"])


@router.get("/", response_model=GeofenceListResponse)
async def get_geofences(
    disabled: Optional[bool] = Query(None, description="Filter by disabled status"),
    type: Optional[str] = Query(None, description="Filter by geofence type"),
    search: Optional[str] = Query(None, description="Search in name and description"),
    page: int = Query(1, ge=1, description="Page number"),
    size: int = Query(50, ge=1, le=1000, description="Page size"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get geofences with optional filtering and pagination"""
    
    # Build query
    query = db.query(Geofence)
    
    # Apply filters
    filters = []
    
    if disabled is not None:
        filters.append(Geofence.disabled == disabled)
    
    if type:
        valid_types = ['polygon', 'circle', 'polyline']
        if type not in valid_types:
            raise HTTPException(status_code=400, detail=f"Invalid type: {type}")
        filters.append(Geofence.type == type)
    
    if search:
        search_filter = or_(
            Geofence.name.ilike(f"%{search}%"),
            Geofence.description.ilike(f"%{search}%")
        )
        filters.append(search_filter)
    
    if filters:
        query = query.filter(and_(*filters))
    
    # Get total count
    total = query.count()
    
    # Apply pagination and ordering
    geofences = query.order_by(desc(Geofence.created_at)).offset((page - 1) * size).limit(size).all()
    
    # Transform to response format
    geofence_responses = []
    for geofence in geofences:
        geofence_data = GeofenceResponse.model_validate(geofence)
        geofence_responses.append(geofence_data)
    
    return GeofenceListResponse(
        geofences=geofence_responses,
        total=total,
        page=page,
        size=size,
        has_next=(page * size) < total,
        has_prev=page > 1
    )


@router.get("/{geofence_id}", response_model=GeofenceResponse)
async def get_geofence(
    geofence_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get a specific geofence by ID"""
    
    geofence = db.query(Geofence).filter(Geofence.id == geofence_id).first()
    
    if not geofence:
        raise HTTPException(status_code=404, detail="Geofence not found")
    
    return GeofenceResponse.model_validate(geofence)


@router.post("/", response_model=GeofenceResponse)
async def create_geofence(
    geofence_data: GeofenceCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Create a new geofence"""
    
    # Check if name already exists
    existing = db.query(Geofence).filter(Geofence.name == geofence_data.name).first()
    if existing:
        raise HTTPException(status_code=400, detail="Geofence with this name already exists")
    
    # Create geofence
    geofence = Geofence(
        name=geofence_data.name,
        description=geofence_data.description,
        geometry=geofence_data.geometry,
        type=geofence_data.type,
        disabled=geofence_data.disabled,
        calendar_id=geofence_data.calendar_id,
        attributes=geofence_data.attributes
    )
    
    # Calculate area
    geofence.area = geofence.calculate_area()
    
    db.add(geofence)
    db.commit()
    db.refresh(geofence)
    
    return GeofenceResponse.model_validate(geofence)


@router.put("/{geofence_id}", response_model=GeofenceResponse)
async def update_geofence(
    geofence_id: int,
    geofence_data: GeofenceUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Update a geofence"""
    
    geofence = db.query(Geofence).filter(Geofence.id == geofence_id).first()
    if not geofence:
        raise HTTPException(status_code=404, detail="Geofence not found")
    
    # Check name uniqueness if name is being updated
    if geofence_data.name and geofence_data.name != geofence.name:
        existing = db.query(Geofence).filter(
            Geofence.name == geofence_data.name,
            Geofence.id != geofence_id
        ).first()
        if existing:
            raise HTTPException(status_code=400, detail="Geofence with this name already exists")
    
    # Update fields
    if geofence_data.name is not None:
        geofence.name = geofence_data.name
    if geofence_data.description is not None:
        geofence.description = geofence_data.description
    if geofence_data.geometry is not None:
        geofence.geometry = geofence_data.geometry
        # Recalculate area if geometry changed
        geofence.area = geofence.calculate_area()
    if geofence_data.type is not None:
        geofence.type = geofence_data.type
    if geofence_data.disabled is not None:
        geofence.disabled = geofence_data.disabled
    if geofence_data.calendar_id is not None:
        geofence.calendar_id = geofence_data.calendar_id
    if geofence_data.attributes is not None:
        geofence.attributes = geofence_data.attributes
    
    db.commit()
    db.refresh(geofence)
    
    return GeofenceResponse.model_validate(geofence)


@router.delete("/{geofence_id}")
async def delete_geofence(
    geofence_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Delete a geofence"""
    
    geofence = db.query(Geofence).filter(Geofence.id == geofence_id).first()
    if not geofence:
        raise HTTPException(status_code=404, detail="Geofence not found")
    
    # Check if geofence has associated events
    event_count = db.query(Event).filter(Event.geofence_id == geofence_id).count()
    if event_count > 0:
        raise HTTPException(
            status_code=400, 
            detail=f"Cannot delete geofence with {event_count} associated events"
        )
    
    db.delete(geofence)
    db.commit()
    
    return {"message": "Geofence deleted successfully"}


@router.get("/stats/summary", response_model=GeofenceStatsResponse)
async def get_geofence_stats(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get geofence statistics"""
    
    # Total geofences
    total_geofences = db.query(Geofence).count()
    
    # Active vs disabled
    active_geofences = db.query(Geofence).filter(Geofence.disabled == False).count()
    disabled_geofences = total_geofences - active_geofences
    
    # Geofences by type
    geofences_by_type = {}
    type_counts = db.query(
        Geofence.type, 
        func.count(Geofence.id).label('count')
    ).group_by(Geofence.type).all()
    
    for type_name, count in type_counts:
        geofences_by_type[type_name] = count
    
    # Total area
    total_area = db.query(func.sum(Geofence.area)).scalar() or 0.0
    
    return GeofenceStatsResponse(
        total_geofences=total_geofences,
        active_geofences=active_geofences,
        disabled_geofences=disabled_geofences,
        geofences_by_type=geofences_by_type,
        total_area=total_area
    )


@router.post("/test", response_model=List[GeofenceTestResponse])
async def test_geofences(
    test_request: GeofenceTestRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Test if a point is inside any geofences"""
    
    # Get all active geofences
    geofences = db.query(Geofence).filter(Geofence.disabled == False).all()
    
    results = []
    for geofence in geofences:
        # This is a simplified point-in-polygon test
        # In production, you'd use a proper geospatial library like Shapely
        is_inside = _point_in_geofence(
            test_request.latitude, 
            test_request.longitude, 
            geofence
        )
        
        # Calculate distance (simplified)
        distance = _calculate_distance_to_geofence(
            test_request.latitude,
            test_request.longitude,
            geofence
        )
        
        results.append(GeofenceTestResponse(
            geofence_id=geofence.id,
            geofence_name=geofence.name,
            is_inside=is_inside,
            distance=distance
        ))
    
    return results


@router.get("/examples/geometries")
async def get_example_geometries():
    """Get example GeoJSON geometries for different geofence types"""
    return {
        "examples": EXAMPLE_GEOMETRIES,
        "description": "Example GeoJSON geometries for creating geofences"
    }


def _point_in_geofence(lat: float, lon: float, geofence: Geofence) -> bool:
    """
    Simplified point-in-geofence test.
    In production, use a proper geospatial library like Shapely.
    """
    import json
    
    try:
        geom_data = json.loads(geofence.geometry)
        geom_type = geom_data.get('type')
        coordinates = geom_data.get('coordinates')
        
        if geom_type == 'Polygon' and coordinates:
            # Simplified polygon test (ray casting algorithm would be better)
            return _point_in_polygon(lat, lon, coordinates[0])
        
        elif geom_type == 'Circle' and coordinates:
            # Circle test
            center_lat, center_lon, radius = coordinates
            distance = _haversine_distance(lat, lon, center_lat, center_lon)
            return distance <= radius
        
        return False
        
    except (json.JSONDecodeError, (ValueError, TypeError)):
        return False


def _point_in_polygon(lat: float, lon: float, polygon_coords: list) -> bool:
    """Simplified point-in-polygon test using ray casting"""
    x, y = lon, lat
    n = len(polygon_coords)
    inside = False
    
    p1x, p1y = polygon_coords[0]
    for i in range(1, n + 1):
        p2x, p2y = polygon_coords[i % n]
        if y > min(p1y, p2y):
            if y <= max(p1y, p2y):
                if x <= max(p1x, p2x):
                    if p1y != p2y:
                        xinters = (y - p1y) * (p2x - p1x) / (p2y - p1y) + p1x
                    if p1x == p2x or x <= xinters:
                        inside = not inside
        p1x, p1y = p2x, p2y
    
    return inside


def _calculate_distance_to_geofence(lat: float, lon: float, geofence: Geofence) -> float:
    """Calculate distance to geofence boundary (simplified)"""
    import json
    
    try:
        geom_data = json.loads(geofence.geometry)
        geom_type = geom_data.get('type')
        coordinates = geom_data.get('coordinates')
        
        if geom_type == 'Circle' and coordinates:
            center_lat, center_lon, radius = coordinates
            distance = _haversine_distance(lat, lon, center_lat, center_lon)
            return max(0, distance - radius)
        
        elif geom_type == 'Polygon' and coordinates:
            # Simplified: distance to first vertex
            first_vertex = coordinates[0][0]
            return _haversine_distance(lat, lon, first_vertex[1], first_vertex[0])
        
        return 0.0
        
    except (json.JSONDecodeError, (ValueError, TypeError)):
        return 0.0


def _haversine_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Calculate distance between two points using Haversine formula"""
    import math
    
    R = 6371000  # Earth's radius in meters
    
    lat1_rad = math.radians(lat1)
    lat2_rad = math.radians(lat2)
    delta_lat = math.radians(lat2 - lat1)
    delta_lon = math.radians(lon2 - lon1)
    
    a = (math.sin(delta_lat / 2) ** 2 + 
         math.cos(lat1_rad) * math.cos(lat2_rad) * 
         math.sin(delta_lon / 2) ** 2)
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    
    return R * c


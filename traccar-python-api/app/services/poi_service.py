import math
from datetime import datetime, timedelta
from typing import List, Optional, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import and_, desc

from app.models.poi import POI, POIVisit
from app.models.position import Position
from app.models.device import Device

class POIService:
    """Service for POI detection and visit tracking"""
    
    def __init__(self, db: Session):
        self.db = db
    
    @staticmethod
    def calculate_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
        """
        Calculate distance between two points using Haversine formula
        Returns distance in meters
        """
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
    
    def get_device_pois(self, device_id: int) -> List[POI]:
        """Get all active POIs for a device"""
        return self.db.query(POI).filter(
            POI.device_id == device_id,
            POI.is_active == True
        ).all()
    
    def is_position_in_poi(self, position: Position, poi: POI) -> bool:
        """Check if a position is within a POI's radius"""
        distance = self.calculate_distance(
            position.latitude, position.longitude,
            poi.latitude, poi.longitude
        )
        return distance <= poi.radius
    
    def get_active_visit(self, device_id: int, poi_id: int) -> Optional[POIVisit]:
        """Get active (ongoing) visit for device at POI"""
        return self.db.query(POIVisit).filter(
            POIVisit.device_id == device_id,
            POIVisit.poi_id == poi_id,
            POIVisit.is_active == True
        ).first()
    
    def create_poi_entry(self, device_id: int, poi_id: int, position: Position) -> POIVisit:
        """Create a new POI visit entry"""
        visit = POIVisit(
            poi_id=poi_id,
            device_id=device_id,
            position_entry_id=position.id,
            entry_time=position.device_time or position.server_time,
            entry_latitude=position.latitude,
            entry_longitude=position.longitude,
            is_active=True
        )
        self.db.add(visit)
        self.db.commit()
        self.db.refresh(visit)
        return visit
    
    def complete_poi_exit(self, visit: POIVisit, position: Position) -> POIVisit:
        """Complete a POI visit with exit information"""
        visit.position_exit_id = position.id
        visit.exit_time = position.device_time or position.server_time
        visit.exit_latitude = position.latitude
        visit.exit_longitude = position.longitude
        visit.is_active = False
        visit.calculate_duration()
        
        self.db.commit()
        self.db.refresh(visit)
        return visit
    
    def process_position_for_pois(self, position: Position) -> List[dict]:
        """
        Process a position for POI entry/exit detection
        Returns list of POI events (entries/exits)
        """
        events = []
        
        # Get all POIs for this device
        pois = self.get_device_pois(position.device_id)
        
        for poi in pois:
            is_inside = self.is_position_in_poi(position, poi)
            active_visit = self.get_active_visit(position.device_id, poi.id)
            
            if is_inside and not active_visit:
                # Device entered POI
                visit = self.create_poi_entry(position.device_id, poi.id, position)
                events.append({
                    'type': 'poi_entry',
                    'poi_id': poi.id,
                    'poi_name': poi.name,
                    'visit_id': visit.id,
                    'device_id': position.device_id,
                    'timestamp': visit.entry_time
                })
                
            elif not is_inside and active_visit:
                # Device exited POI
                visit = self.complete_poi_exit(active_visit, position)
                events.append({
                    'type': 'poi_exit',
                    'poi_id': poi.id,
                    'poi_name': poi.name,
                    'visit_id': visit.id,
                    'device_id': position.device_id,
                    'duration_minutes': visit.duration_minutes,
                    'timestamp': visit.exit_time
                })
        
        return events
    
    def get_recent_visits(self, device_id: int, hours: int = 24) -> List[POIVisit]:
        """Get recent POI visits for a device"""
        since = datetime.utcnow() - timedelta(hours=hours)
        return self.db.query(POIVisit).filter(
            POIVisit.device_id == device_id,
            POIVisit.entry_time >= since
        ).order_by(desc(POIVisit.entry_time)).all()
    
    def get_poi_summary(self, device_id: int, days: int = 7) -> dict:
        """Get POI summary statistics for a device"""
        since = datetime.utcnow() - timedelta(days=days)
        
        # Get total visits
        total_visits = self.db.query(POIVisit).filter(
            POIVisit.device_id == device_id,
            POIVisit.entry_time >= since
        ).count()
        
        # Get unique POIs visited
        unique_pois = self.db.query(POIVisit.poi_id).filter(
            POIVisit.device_id == device_id,
            POIVisit.entry_time >= since
        ).distinct().count()
        
        # Get total time spent in POIs
        total_duration = self.db.query(
            self.db.func.sum(POIVisit.duration_minutes)
        ).filter(
            POIVisit.device_id == device_id,
            POIVisit.entry_time >= since,
            POIVisit.is_active == False
        ).scalar() or 0
        
        # Get most visited POI
        most_visited = self.db.query(
            POI.name,
            self.db.func.count(POIVisit.id).label('visits')
        ).join(POIVisit).filter(
            POIVisit.device_id == device_id,
            POIVisit.entry_time >= since
        ).group_by(POI.id, POI.name).order_by(desc('visits')).first()
        
        return {
            'total_visits': total_visits,
            'unique_pois_visited': unique_pois,
            'total_duration_hours': total_duration / 60 if total_duration else 0,
            'most_visited_poi': most_visited.name if most_visited else None,
            'period_days': days
        }
    
    def cleanup_old_active_visits(self, hours: int = 24):
        """
        Cleanup old active visits that might be stuck
        This handles cases where exit wasn't detected properly
        """
        cutoff = datetime.utcnow() - timedelta(hours=hours)
        
        old_visits = self.db.query(POIVisit).filter(
            POIVisit.is_active == True,
            POIVisit.entry_time < cutoff
        ).all()
        
        for visit in old_visits:
            visit.is_active = False
            visit.exit_time = visit.entry_time + timedelta(hours=1)  # Estimate 1 hour duration
            visit.calculate_duration()
        
        if old_visits:
            self.db.commit()
        
        return len(old_visits)

# Utility functions for POI management
def create_home_poi(db: Session, device_id: int, latitude: float, longitude: float, 
                   radius: float = 100.0, user_id: int = None) -> POI:
    """Helper function to create a 'CASA' POI"""
    poi = POI(
        name="CASA",
        description="Residência principal",
        latitude=latitude,
        longitude=longitude,
        radius=radius,
        device_id=device_id,
        color="#4CAF50",
        icon="home",
        created_by=user_id
    )
    db.add(poi)
    db.commit()
    db.refresh(poi)
    return poi

def create_work_poi(db: Session, device_id: int, latitude: float, longitude: float, 
                   radius: float = 150.0, user_id: int = None) -> POI:
    """Helper function to create a 'TRABALHO' POI"""
    poi = POI(
        name="TRABALHO",
        description="Local de trabalho",
        latitude=latitude,
        longitude=longitude,
        radius=radius,
        device_id=device_id,
        color="#2196F3",
        icon="work",
        created_by=user_id
    )
    db.add(poi)
    db.commit()
    db.refresh(poi)
    return poi

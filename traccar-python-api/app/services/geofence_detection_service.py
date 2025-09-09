"""
Geofence Detection Service
Handles real-time geofence detection for position updates
"""
import json
import math
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime
import structlog
from sqlalchemy.orm import Session
from sqlalchemy import select, and_

from app.models.geofence import Geofence
from app.models.position import Position
from app.models.device import Device
from app.models.event import Event
from app.core.cache import cache_manager
from app.services.websocket_service import WebSocketService

logger = structlog.get_logger(__name__)


class GeofenceDetectionService:
    """
    Service for detecting geofence enter/exit events based on position updates
    """
    
    def __init__(self, db: Session):
        self.db = db
        self.cache_key_prefix = "geofence_detection"
        self.cache_ttl = 300  # 5 minutes
    
    async def process_position_for_geofences(self, position: Position, device: Device) -> List[Event]:
        """
        Process a position update for geofence detection
        
        Args:
            position: The new position
            device: The device that generated the position
            
        Returns:
            List of generated geofence events
        """
        try:
            logger.info("Processing position for geofence detection", 
                       position_id=position.id, 
                       device_id=device.id)
            
            # Get active geofences from cache or database
            active_geofences = await self._get_active_geofences()
            
            if not active_geofences:
                logger.debug("No active geofences found")
                return []
            
            # Get previous position for comparison
            previous_position = await self._get_previous_position(device.id, position.id)
            
            generated_events = []
            
            for geofence in active_geofences:
                try:
                    # Check if position is inside geofence
                    is_inside = self._point_in_geofence(position.latitude, position.longitude, geofence)
                    
                    # Check if previous position was inside geofence
                    was_inside = False
                    if previous_position:
                        was_inside = self._point_in_geofence(
                            previous_position.latitude, 
                            previous_position.longitude, 
                            geofence
                        )
                    
                    # Generate events based on state changes
                    if is_inside and not was_inside:
                        # Device entered geofence
                        event = await self._create_geofence_event(
                            position, device, geofence, "geofenceEnter"
                        )
                        if event:
                            generated_events.append(event)
                            logger.info("Geofence enter event created", 
                                       geofence_id=geofence.id, 
                                       device_id=device.id)
                    
                    elif not is_inside and was_inside:
                        # Device exited geofence
                        event = await self._create_geofence_event(
                            position, device, geofence, "geofenceExit"
                        )
                        if event:
                            generated_events.append(event)
                            logger.info("Geofence exit event created", 
                                       geofence_id=geofence.id, 
                                       device_id=device.id)
                    
                except Exception as e:
                    logger.error("Error processing geofence", 
                               geofence_id=geofence.id, 
                               error=str(e))
                    continue
            
            # Broadcast geofence events via WebSocket
            for event in generated_events:
                try:
                    await WebSocketService.broadcast_geofence_alert(
                        device, 
                        event.geofence.name if event.geofence else "Unknown", 
                        event.type.replace("geofence", "").lower(), 
                        position
                    )
                except Exception as e:
                    logger.error("Failed to broadcast geofence alert", error=str(e))
            
            logger.info("Geofence detection completed", 
                       position_id=position.id, 
                       events_generated=len(generated_events))
            
            return generated_events
            
        except Exception as e:
            logger.error("Error in geofence detection", 
                       position_id=position.id, 
                       error=str(e))
            return []
    
    async def _get_active_geofences(self) -> List[Geofence]:
        """Get active geofences from cache or database"""
        cache_key = f"{self.cache_key_prefix}:active_geofences"
        
        # Try to get from cache first
        cached_geofences = await cache_manager.get(cache_key)
        if cached_geofences:
            logger.debug("Retrieved active geofences from cache")
            return cached_geofences
        
        # Get from database
        result = self.db.execute(
            select(Geofence).where(Geofence.disabled == False)
        )
        geofences = result.scalars().all()
        
        # Cache the result
        await cache_manager.set(cache_key, geofences, ttl=self.cache_ttl)
        
        logger.debug("Retrieved active geofences from database", count=len(geofences))
        return geofences
    
    async def _get_previous_position(self, device_id: int, current_position_id: int) -> Optional[Position]:
        """Get the previous position for a device"""
        cache_key = f"{self.cache_key_prefix}:previous_position:{device_id}"
        
        # Try to get from cache first
        cached_position = await cache_manager.get(cache_key)
        if cached_position:
            return cached_position
        
        # Get from database
        result = self.db.execute(
            select(Position)
            .where(and_(
                Position.device_id == device_id,
                Position.id < current_position_id
            ))
            .order_by(Position.id.desc())
            .limit(1)
        )
        position = result.scalar_one_or_none()
        
        # Cache the result
        if position:
            await cache_manager.set(cache_key, position, ttl=60)  # 1 minute cache
        
        return position
    
    def _point_in_geofence(self, latitude: float, longitude: float, geofence: Geofence) -> bool:
        """
        Check if a point is inside a geofence using proper geometric calculations
        
        Args:
            latitude: Point latitude
            longitude: Point longitude
            geofence: Geofence to test against
            
        Returns:
            True if point is inside geofence
        """
        try:
            geom_data = json.loads(geofence.geometry)
            geom_type = geom_data.get('type')
            coordinates = geom_data.get('coordinates')
            
            if not coordinates:
                return False
            
            if geom_type == 'Polygon':
                return self._point_in_polygon(latitude, longitude, coordinates[0])
            
            elif geom_type == 'Circle':
                if len(coordinates) >= 3:
                    center_lon, center_lat, radius = coordinates[:3]
                    distance = self._haversine_distance(latitude, longitude, center_lat, center_lon)
                    return distance <= radius
            
            elif geom_type == 'LineString':
                # For polyline, check if point is within buffer distance
                buffer_distance = geofence.get_double_attribute("bufferDistance", 50.0)  # Default 50m
                return self._point_near_polyline(latitude, longitude, coordinates, buffer_distance)
            
            return False
            
        except (json.JSONDecodeError, (ValueError, TypeError)) as e:
            logger.error("Error parsing geofence geometry", 
                       geofence_id=geofence.id, 
                       error=str(e))
            return False
    
    def _point_in_polygon(self, latitude: float, longitude: float, polygon_coords: List[List[float]]) -> bool:
        """
        Check if a point is inside a polygon using ray casting algorithm
        
        Args:
            latitude: Point latitude
            longitude: Point longitude
            polygon_coords: List of [lon, lat] coordinate pairs
            
        Returns:
            True if point is inside polygon
        """
        x, y = longitude, latitude
        n = len(polygon_coords)
        inside = False
        
        if n < 3:  # Need at least 3 points for a polygon
            return False
        
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
    
    def _point_near_polyline(self, latitude: float, longitude: float, 
                           polyline_coords: List[List[float]], buffer_distance: float) -> bool:
        """
        Check if a point is within buffer distance of a polyline
        
        Args:
            latitude: Point latitude
            longitude: Point longitude
            polyline_coords: List of [lon, lat] coordinate pairs
            buffer_distance: Buffer distance in meters
            
        Returns:
            True if point is within buffer distance
        """
        if len(polyline_coords) < 2:
            return False
        
        # Check distance to each line segment
        for i in range(len(polyline_coords) - 1):
            p1 = polyline_coords[i]
            p2 = polyline_coords[i + 1]
            
            distance = self._point_to_line_distance(
                latitude, longitude, 
                p1[1], p1[0],  # lat, lon
                p2[1], p2[0]   # lat, lon
            )
            
            if distance <= buffer_distance:
                return True
        
        return False
    
    def _point_to_line_distance(self, px: float, py: float, 
                              x1: float, y1: float, x2: float, y2: float) -> float:
        """
        Calculate distance from a point to a line segment
        
        Args:
            px, py: Point coordinates
            x1, y1: Line start coordinates
            x2, y2: Line end coordinates
            
        Returns:
            Distance in meters
        """
        # Convert to meters using approximate conversion
        # This is a simplified calculation - for production use proper projection
        A = px - x1
        B = py - y1
        C = x2 - x1
        D = y2 - y1
        
        dot = A * C + B * D
        len_sq = C * C + D * D
        
        if len_sq == 0:
            return math.sqrt(A * A + B * B) * 111000  # Approximate meters per degree
        
        param = dot / len_sq
        
        if param < 0:
            xx, yy = x1, y1
        elif param > 1:
            xx, yy = x2, y2
        else:
            xx = x1 + param * C
            yy = y1 + param * D
        
        dx = px - xx
        dy = py - yy
        
        return math.sqrt(dx * dx + dy * dy) * 111000  # Approximate meters per degree
    
    def _haversine_distance(self, lat1: float, lon1: float, lat2: float, lon2: float) -> float:
        """
        Calculate distance between two points using Haversine formula
        
        Args:
            lat1, lon1: First point coordinates
            lat2, lon2: Second point coordinates
            
        Returns:
            Distance in meters
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
    
    async def _create_geofence_event(self, position: Position, device: Device, 
                                   geofence: Geofence, event_type: str) -> Optional[Event]:
        """
        Create a geofence event
        
        Args:
            position: Position that triggered the event
            device: Device that generated the position
            geofence: Geofence involved in the event
            event_type: Type of event (geofenceEnter, geofenceExit)
            
        Returns:
            Created event or None if creation failed
        """
        try:
            # Check if similar event already exists recently (avoid duplicates)
            recent_event = self.db.execute(
                select(Event).where(and_(
                    Event.device_id == device.id,
                    Event.geofence_id == geofence.id,
                    Event.type == event_type,
                    Event.event_time >= position.device_time - 300  # 5 minutes ago
                ))
            ).scalar_one_or_none()
            
            if recent_event:
                logger.debug("Similar geofence event already exists recently", 
                           event_id=recent_event.id)
                return None
            
            # Create new event
            event = Event(
                type=event_type,
                event_time=position.device_time,
                device_id=device.id,
                geofence_id=geofence.id,
                position_id=position.id,
                attributes=json.dumps({
                    "geofence_name": geofence.name,
                    "latitude": position.latitude,
                    "longitude": position.longitude,
                    "speed": position.speed,
                    "course": position.course
                })
            )
            
            self.db.add(event)
            self.db.commit()
            self.db.refresh(event)
            
            logger.info("Geofence event created", 
                       event_id=event.id, 
                       event_type=event_type,
                       geofence_id=geofence.id,
                       device_id=device.id)
            
            return event
            
        except Exception as e:
            logger.error("Failed to create geofence event", 
                       error=str(e),
                       geofence_id=geofence.id,
                       device_id=device.id)
            return None
    
    async def invalidate_geofence_cache(self, geofence_id: Optional[int] = None):
        """
        Invalidate geofence detection cache
        
        Args:
            geofence_id: Specific geofence ID to invalidate, or None for all
        """
        try:
            if geofence_id:
                # Invalidate specific geofence cache
                cache_key = f"{self.cache_key_prefix}:geofence:{geofence_id}"
                await cache_manager.delete(cache_key)
            else:
                # Invalidate all geofence detection cache
                await cache_manager.clear_pattern(f"{self.cache_key_prefix}:*")
            
            logger.info("Geofence detection cache invalidated", geofence_id=geofence_id)
            
        except Exception as e:
            logger.error("Failed to invalidate geofence cache", error=str(e))
    
    def get_geofences_for_point(self, latitude: float, longitude: float) -> List[Dict[str, Any]]:
        """
        Get all geofences that contain a specific point
        
        Args:
            latitude: Point latitude
            longitude: Point longitude
            
        Returns:
            List of geofence information dictionaries
        """
        try:
            result = self.db.execute(
                select(Geofence).where(Geofence.disabled == False)
            )
            geofences = result.scalars().all()
            
            matching_geofences = []
            for geofence in geofences:
                if self._point_in_geofence(latitude, longitude, geofence):
                    matching_geofences.append({
                        "id": geofence.id,
                        "name": geofence.name,
                        "type": geofence.type,
                        "area": geofence.area
                    })
            
            return matching_geofences
            
        except Exception as e:
            logger.error("Error getting geofences for point", error=str(e))
            return []

"""
Geofence Cache Service
Handles caching of geofence data for improved performance
"""
import json
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
import structlog
from sqlalchemy.orm import Session
from sqlalchemy import select, and_

from app.models.geofence import Geofence
from app.core.cache import cache_manager

logger = structlog.get_logger(__name__)


class GeofenceCacheService:
    """
    Service for caching geofence data to improve performance
    """
    
    def __init__(self):
        self.cache_prefix = "geofence"
        self.default_ttl = 300  # 5 minutes
        self.active_geofences_ttl = 600  # 10 minutes
        self.geofence_details_ttl = 1800  # 30 minutes
    
    async def get_active_geofences(self, db: Session) -> List[Geofence]:
        """
        Get active geofences from cache or database
        
        Args:
            db: Database session
            
        Returns:
            List of active geofences
        """
        cache_key = f"{self.cache_prefix}:active_geofences"
        
        try:
            # Try to get from cache first
            cached_geofences = await cache_manager.get(cache_key)
            if cached_geofences:
                logger.debug("Retrieved active geofences from cache", count=len(cached_geofences))
                return cached_geofences
            
            # Get from database
            result = db.execute(
                select(Geofence).where(Geofence.disabled == False)
            )
            geofences = result.scalars().all()
            
            # Cache the result
            await cache_manager.set(cache_key, geofences, ttl=self.active_geofences_ttl)
            
            logger.debug("Retrieved active geofences from database", count=len(geofences))
            return geofences
            
        except Exception as e:
            logger.error("Error getting active geofences", error=str(e))
            # Fallback to database
            result = db.execute(
                select(Geofence).where(Geofence.disabled == False)
            )
            return result.scalars().all()
    
    async def get_geofence_by_id(self, geofence_id: int, db: Session) -> Optional[Geofence]:
        """
        Get geofence by ID from cache or database
        
        Args:
            geofence_id: Geofence ID
            db: Database session
            
        Returns:
            Geofence or None if not found
        """
        cache_key = f"{self.cache_prefix}:details:{geofence_id}"
        
        try:
            # Try to get from cache first
            cached_geofence = await cache_manager.get(cache_key)
            if cached_geofence:
                logger.debug("Retrieved geofence from cache", geofence_id=geofence_id)
                return cached_geofence
            
            # Get from database
            result = db.execute(
                select(Geofence).where(Geofence.id == geofence_id)
            )
            geofence = result.scalar_one_or_none()
            
            if geofence:
                # Cache the result
                await cache_manager.set(cache_key, geofence, ttl=self.geofence_details_ttl)
                logger.debug("Retrieved geofence from database", geofence_id=geofence_id)
            
            return geofence
            
        except Exception as e:
            logger.error("Error getting geofence by ID", geofence_id=geofence_id, error=str(e))
            # Fallback to database
            result = db.execute(
                select(Geofence).where(Geofence.id == geofence_id)
            )
            return result.scalar_one_or_none()
    
    async def get_geofences_by_type(self, geofence_type: str, db: Session) -> List[Geofence]:
        """
        Get geofences by type from cache or database
        
        Args:
            geofence_type: Type of geofence (polygon, circle, polyline)
            db: Database session
            
        Returns:
            List of geofences of specified type
        """
        cache_key = f"{self.cache_prefix}:type:{geofence_type}"
        
        try:
            # Try to get from cache first
            cached_geofences = await cache_manager.get(cache_key)
            if cached_geofences:
                logger.debug("Retrieved geofences by type from cache", 
                           type=geofence_type, count=len(cached_geofences))
                return cached_geofences
            
            # Get from database
            result = db.execute(
                select(Geofence).where(and_(
                    Geofence.type == geofence_type,
                    Geofence.disabled == False
                ))
            )
            geofences = result.scalars().all()
            
            # Cache the result
            await cache_manager.set(cache_key, geofences, ttl=self.default_ttl)
            
            logger.debug("Retrieved geofences by type from database", 
                       type=geofence_type, count=len(geofences))
            return geofences
            
        except Exception as e:
            logger.error("Error getting geofences by type", type=geofence_type, error=str(e))
            # Fallback to database
            result = db.execute(
                select(Geofence).where(and_(
                    Geofence.type == geofence_type,
                    Geofence.disabled == False
                ))
            )
            return result.scalars().all()
    
    async def get_geofences_in_area(self, min_lat: float, max_lat: float, 
                                  min_lon: float, max_lon: float, db: Session) -> List[Geofence]:
        """
        Get geofences that intersect with a bounding box
        This is a simplified implementation - in production you'd use spatial indexes
        
        Args:
            min_lat: Minimum latitude
            max_lat: Maximum latitude
            min_lon: Minimum longitude
            max_lon: Maximum longitude
            db: Database session
            
        Returns:
            List of geofences in the area
        """
        cache_key = f"{self.cache_prefix}:area:{min_lat}:{max_lat}:{min_lon}:{max_lon}"
        
        try:
            # Try to get from cache first
            cached_geofences = await cache_manager.get(cache_key)
            if cached_geofences:
                logger.debug("Retrieved geofences in area from cache", count=len(cached_geofences))
                return cached_geofences
            
            # Get all active geofences and filter by area
            # This is a simplified approach - in production you'd use spatial queries
            result = db.execute(
                select(Geofence).where(Geofence.disabled == False)
            )
            all_geofences = result.scalars().all()
            
            # Filter geofences that intersect with the bounding box
            geofences_in_area = []
            for geofence in all_geofences:
                if self._geofence_intersects_bbox(geofence, min_lat, max_lat, min_lon, max_lon):
                    geofences_in_area.append(geofence)
            
            # Cache the result with shorter TTL for area queries
            await cache_manager.set(cache_key, geofences_in_area, ttl=60)  # 1 minute
            
            logger.debug("Retrieved geofences in area from database", count=len(geofences_in_area))
            return geofences_in_area
            
        except Exception as e:
            logger.error("Error getting geofences in area", error=str(e))
            return []
    
    def _geofence_intersects_bbox(self, geofence: Geofence, min_lat: float, max_lat: float, 
                                min_lon: float, max_lon: float) -> bool:
        """
        Check if a geofence intersects with a bounding box
        
        Args:
            geofence: Geofence to check
            min_lat, max_lat: Latitude bounds
            min_lon, max_lon: Longitude bounds
            
        Returns:
            True if geofence intersects with bounding box
        """
        try:
            geom_data = json.loads(geofence.geometry)
            geom_type = geom_data.get('type')
            coordinates = geom_data.get('coordinates')
            
            if not coordinates:
                return False
            
            if geom_type == 'Polygon':
                # Check if any polygon vertex is in the bounding box
                for ring in coordinates:
                    for coord in ring:
                        lon, lat = coord[0], coord[1]
                        if min_lon <= lon <= max_lon and min_lat <= lat <= max_lat:
                            return True
                return False
            
            elif geom_type == 'Circle':
                if len(coordinates) >= 3:
                    center_lon, center_lat, radius = coordinates[:3]
                    # Convert radius to degrees (approximate)
                    radius_deg = radius / 111000  # Approximate meters per degree
                    
                    # Check if circle intersects with bounding box
                    return (center_lon - radius_deg <= max_lon and 
                           center_lon + radius_deg >= min_lon and
                           center_lat - radius_deg <= max_lat and 
                           center_lat + radius_deg >= min_lat)
            
            elif geom_type == 'LineString':
                # Check if any line vertex is in the bounding box
                for coord in coordinates:
                    lon, lat = coord[0], coord[1]
                    if min_lon <= lon <= max_lon and min_lat <= lat <= max_lat:
                        return True
                return False
            
            return False
            
        except (json.JSONDecodeError, (ValueError, TypeError)):
            return False
    
    async def invalidate_geofence_cache(self, geofence_id: Optional[int] = None):
        """
        Invalidate geofence cache entries
        
        Args:
            geofence_id: Specific geofence ID to invalidate, or None for all
        """
        try:
            if geofence_id:
                # Invalidate specific geofence cache entries
                patterns = [
                    f"{self.cache_prefix}:details:{geofence_id}",
                    f"{self.cache_prefix}:type:*",  # Invalidate type caches
                    f"{self.cache_prefix}:area:*",  # Invalidate area caches
                    f"{self.cache_prefix}:active_geofences"  # Invalidate active geofences
                ]
                
                for pattern in patterns:
                    await cache_manager.clear_pattern(pattern)
                
                logger.info("Invalidated geofence cache", geofence_id=geofence_id)
            else:
                # Invalidate all geofence cache entries
                await cache_manager.clear_pattern(f"{self.cache_prefix}:*")
                logger.info("Invalidated all geofence cache")
                
        except Exception as e:
            logger.error("Failed to invalidate geofence cache", error=str(e))
    
    async def warm_geofence_cache(self, db: Session):
        """
        Warm the geofence cache with frequently accessed data
        
        Args:
            db: Database session
        """
        try:
            logger.info("Starting geofence cache warming")
            
            # Warm active geofences cache
            await self.get_active_geofences(db)
            
            # Warm geofences by type
            for geofence_type in ['polygon', 'circle', 'polyline']:
                await self.get_geofences_by_type(geofence_type, db)
            
            logger.info("Geofence cache warming completed")
            
        except Exception as e:
            logger.error("Error warming geofence cache", error=str(e))
    
    async def get_cache_stats(self) -> Dict[str, Any]:
        """
        Get geofence cache statistics
        
        Returns:
            Dictionary with cache statistics
        """
        try:
            # Get cache keys matching geofence pattern
            geofence_keys = await cache_manager.get_keys(f"{self.cache_prefix}:*")
            
            stats = {
                "total_keys": len(geofence_keys),
                "key_types": {},
                "last_updated": datetime.utcnow().isoformat()
            }
            
            # Categorize keys by type
            for key in geofence_keys:
                key_type = key.split(':')[1] if ':' in key else 'unknown'
                stats["key_types"][key_type] = stats["key_types"].get(key_type, 0) + 1
            
            return stats
            
        except Exception as e:
            logger.error("Error getting geofence cache stats", error=str(e))
            return {"error": str(e)}
    
    async def clear_expired_cache(self):
        """
        Clear expired geofence cache entries
        This is handled automatically by Redis, but can be called manually
        """
        try:
            # Redis handles TTL automatically, but we can check for expired keys
            geofence_keys = await cache_manager.get_keys(f"{self.cache_prefix}:*")
            
            expired_count = 0
            for key in geofence_keys:
                ttl = await cache_manager.get_ttl(key)
                if ttl == -2:  # Key doesn't exist (expired)
                    expired_count += 1
            
            logger.info("Checked expired geofence cache entries", expired_count=expired_count)
            return expired_count
            
        except Exception as e:
            logger.error("Error clearing expired geofence cache", error=str(e))
            return 0


# Global instance
geofence_cache_service = GeofenceCacheService()

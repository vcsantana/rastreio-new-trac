"""
Position cache service
Provides caching functionality for position data
"""
import json
import asyncio
from typing import Optional, List, Dict, Any
from datetime import datetime, timedelta
from functools import lru_cache
import redis.asyncio as redis
from app.models.position import Position
from app.database import get_db
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
import logging

logger = logging.getLogger(__name__)

class PositionCacheService:
    """Service for caching position data"""
    
    def __init__(self, redis_client: redis.Redis):
        self.redis = redis_client
        self.cache_ttl = 300  # 5 minutes default TTL
        self.latest_positions_ttl = 60  # 1 minute for latest positions
        self.history_cache_ttl = 600  # 10 minutes for history
    
    async def get_cached_position(self, position_id: int) -> Optional[Dict[str, Any]]:
        """Get cached position by ID"""
        try:
            key = f"position:{position_id}"
            cached_data = await self.redis.get(key)
            if cached_data:
                return json.loads(cached_data)
        except Exception as e:
            logger.error(f"Error getting cached position {position_id}: {e}")
        return None
    
    async def set_cached_position(self, position: Position) -> None:
        """Cache position data"""
        try:
            key = f"position:{position.id}"
            position_data = {
                "id": position.id,
                "device_id": position.device_id,
                "unknown_device_id": position.unknown_device_id,
                "protocol": position.protocol,
                "server_time": position.server_time.isoformat() if position.server_time else None,
                "device_time": position.device_time.isoformat() if position.device_time else None,
                "fix_time": position.fix_time.isoformat() if position.fix_time else None,
                "valid": position.valid,
                "latitude": position.latitude,
                "longitude": position.longitude,
                "altitude": position.altitude,
                "speed": position.speed,
                "course": position.course,
                "address": position.address,
                "accuracy": position.accuracy,
                "network": position.network,
                "attributes": position.attributes,
                # GPS and Satellite Information
                "hdop": position.hdop,
                "vdop": position.vdop,
                "pdop": position.pdop,
                "satellites": position.satellites,
                "satellites_visible": position.satellites_visible,
                # Network and Communication
                "rssi": position.rssi,
                "roaming": position.roaming,
                "network_type": position.network_type,
                "cell_id": position.cell_id,
                "lac": position.lac,
                "mnc": position.mnc,
                "mcc": position.mcc,
                # Fuel and Engine
                "fuel_level": position.fuel_level,
                "fuel_used": position.fuel_used,
                "fuel_consumption": position.fuel_consumption,
                "rpm": position.rpm,
                "engine_load": position.engine_load,
                "engine_temp": position.engine_temp,
                "throttle": position.throttle,
                "coolant_temp": position.coolant_temp,
                "hours": position.hours,
                # Battery and Power
                "battery": position.battery,
                "battery_level": position.battery_level,
                "power": position.power,
                "charge": position.charge,
                "external_power": position.external_power,
                # Odometer and Distance
                "odometer": position.odometer,
                "odometer_service": position.odometer_service,
                "odometer_trip": position.odometer_trip,
                "total_distance": position.total_distance,
                "distance": position.distance,
                "trip_distance": position.trip_distance,
                # Control and Status
                "ignition": position.ignition,
                "motion": position.motion,
                "armed": position.armed,
                "blocked": position.blocked,
                "lock": position.lock,
                "door": position.door,
                "driver_unique_id": position.driver_unique_id,
                # Alarms and Events
                "alarm": position.alarm,
                "event": position.event,
                "status": position.status,
                "alarm_type": position.alarm_type,
                "event_type": position.event_type,
                # Geofences
                "geofence_ids": position.geofence_ids,
                "geofence": position.geofence,
                "geofence_id": position.geofence_id,
                # Additional Sensors
                "temperature": position.temperature,
                "humidity": position.humidity,
                "pressure": position.pressure,
                "light": position.light,
                "proximity": position.proximity,
                "acceleration": position.acceleration,
                "gyroscope": position.gyroscope,
                "magnetometer": position.magnetometer,
                # CAN Bus Data
                "can_data": position.can_data,
                "obd_speed": position.obd_speed,
                "obd_rpm": position.obd_rpm,
                "obd_fuel": position.obd_fuel,
                "obd_temp": position.obd_temp,
                # Maintenance
                "maintenance": position.maintenance,
                "service_due": position.service_due.isoformat() if position.service_due else None,
                "oil_level": position.oil_level,
                "tire_pressure": position.tire_pressure,
                # Driver Behavior
                "hard_acceleration": position.hard_acceleration,
                "hard_braking": position.hard_braking,
                "hard_turning": position.hard_turning,
                "idling": position.idling,
                "overspeed": position.overspeed,
                # Location Quality
                "location_accuracy": position.location_accuracy,
                "gps_accuracy": position.gps_accuracy,
                "network_accuracy": position.network_accuracy,
                # Protocol Specific
                "protocol_version": position.protocol_version,
                "firmware_version": position.firmware_version,
                "hardware_version": position.hardware_version,
                # Time and Status
                "outdated": position.outdated,
                # Custom Attributes
                "custom1": position.custom1,
                "custom2": position.custom2,
                "custom3": position.custom3,
                "custom4": position.custom4,
                "custom5": position.custom5,
            }
            
            await self.redis.setex(
                key, 
                self.cache_ttl, 
                json.dumps(position_data, default=str)
            )
        except Exception as e:
            logger.error(f"Error caching position {position.id}: {e}")
    
    async def get_cached_latest_positions(self, user_id: int) -> Optional[List[Dict[str, Any]]]:
        """Get cached latest positions for user"""
        try:
            key = f"latest_positions:{user_id}"
            cached_data = await self.redis.get(key)
            if cached_data:
                return json.loads(cached_data)
        except Exception as e:
            logger.error(f"Error getting cached latest positions for user {user_id}: {e}")
        return None
    
    async def set_cached_latest_positions(self, user_id: int, positions: List[Dict[str, Any]]) -> None:
        """Cache latest positions for user"""
        try:
            key = f"latest_positions:{user_id}"
            await self.redis.setex(
                key, 
                self.latest_positions_ttl, 
                json.dumps(positions, default=str)
            )
        except Exception as e:
            logger.error(f"Error caching latest positions for user {user_id}: {e}")
    
    async def get_cached_device_history(self, device_id: int, from_time: datetime, to_time: datetime) -> Optional[List[Dict[str, Any]]]:
        """Get cached device history"""
        try:
            key = f"device_history:{device_id}:{from_time.isoformat()}:{to_time.isoformat()}"
            cached_data = await self.redis.get(key)
            if cached_data:
                return json.loads(cached_data)
        except Exception as e:
            logger.error(f"Error getting cached device history for device {device_id}: {e}")
        return None
    
    async def set_cached_device_history(self, device_id: int, from_time: datetime, to_time: datetime, positions: List[Dict[str, Any]]) -> None:
        """Cache device history"""
        try:
            key = f"device_history:{device_id}:{from_time.isoformat()}:{to_time.isoformat()}"
            await self.redis.setex(
                key, 
                self.history_cache_ttl, 
                json.dumps(positions, default=str)
            )
        except Exception as e:
            logger.error(f"Error caching device history for device {device_id}: {e}")
    
    async def invalidate_position_cache(self, position_id: int) -> None:
        """Invalidate cached position"""
        try:
            key = f"position:{position_id}"
            await self.redis.delete(key)
        except Exception as e:
            logger.error(f"Error invalidating position cache {position_id}: {e}")
    
    async def invalidate_device_cache(self, device_id: int) -> None:
        """Invalidate all cache entries for a device"""
        try:
            # Get all keys related to this device
            pattern = f"*device_history:{device_id}:*"
            keys = await self.redis.keys(pattern)
            if keys:
                await self.redis.delete(*keys)
            
            # Also invalidate latest positions cache for all users
            pattern = f"latest_positions:*"
            keys = await self.redis.keys(pattern)
            if keys:
                await self.redis.delete(*keys)
        except Exception as e:
            logger.error(f"Error invalidating device cache {device_id}: {e}")
    
    async def invalidate_user_cache(self, user_id: int) -> None:
        """Invalidate cache entries for a user"""
        try:
            key = f"latest_positions:{user_id}"
            await self.redis.delete(key)
        except Exception as e:
            logger.error(f"Error invalidating user cache {user_id}: {e}")
    
    async def clear_all_cache(self) -> None:
        """Clear all position cache"""
        try:
            patterns = [
                "position:*",
                "latest_positions:*",
                "device_history:*"
            ]
            
            for pattern in patterns:
                keys = await self.redis.keys(pattern)
                if keys:
                    await self.redis.delete(*keys)
        except Exception as e:
            logger.error(f"Error clearing position cache: {e}")
    
    async def get_cache_stats(self) -> Dict[str, Any]:
        """Get cache statistics"""
        try:
            stats = {
                "total_keys": 0,
                "position_keys": 0,
                "latest_positions_keys": 0,
                "device_history_keys": 0,
                "memory_usage": 0
            }
            
            # Count different types of keys
            patterns = {
                "position_keys": "position:*",
                "latest_positions_keys": "latest_positions:*",
                "device_history_keys": "device_history:*"
            }
            
            for stat_key, pattern in patterns.items():
                keys = await self.redis.keys(pattern)
                stats[stat_key] = len(keys)
                stats["total_keys"] += len(keys)
            
            # Get memory usage
            info = await self.redis.info("memory")
            stats["memory_usage"] = info.get("used_memory", 0)
            
            return stats
        except Exception as e:
            logger.error(f"Error getting cache stats: {e}")
            return {}

# Global cache service instance
position_cache_service: Optional[PositionCacheService] = None

async def get_position_cache_service() -> PositionCacheService:
    """Get position cache service instance"""
    global position_cache_service
    if position_cache_service is None:
        # This should be initialized in main.py with Redis connection
        raise RuntimeError("Position cache service not initialized")
    return position_cache_service

def initialize_position_cache_service(redis_client: redis.Redis) -> None:
    """Initialize position cache service"""
    global position_cache_service
    position_cache_service = PositionCacheService(redis_client)

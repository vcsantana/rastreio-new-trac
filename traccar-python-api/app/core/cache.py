"""
Redis cache implementation for Traccar API
"""
import json
import pickle
from typing import Any, Optional, Union, Dict, List
from datetime import datetime, timedelta
import asyncio
import redis.asyncio as redis
from redis.asyncio import Redis
import structlog
from app.config import settings

logger = structlog.get_logger(__name__)


class CacheManager:
    """Redis cache manager with async support"""
    
    def __init__(self):
        self.redis: Optional[Redis] = None
        self._connection_pool = None
    
    async def connect(self):
        """Connect to Redis"""
        try:
            self.redis = redis.from_url(
                settings.REDIS_URL,
                max_connections=20,
                retry_on_timeout=True,
                decode_responses=False
            )
            
            # Test connection
            await self.redis.ping()
            logger.info("Connected to Redis successfully")
            
        except Exception as e:
            logger.error("Failed to connect to Redis", error=str(e))
            raise
    
    async def disconnect(self):
        """Disconnect from Redis"""
        if self.redis:
            await self.redis.close()
        logger.info("Disconnected from Redis")
    
    async def get(self, key: str) -> Optional[Any]:
        """Get value from cache"""
        if not self.redis:
            return None
        
        try:
            value = await self.redis.get(key)
            if value:
                # Try to deserialize as JSON first, then pickle
                try:
                    return json.loads(value)
                except (json.JSONDecodeError, TypeError):
                    return pickle.loads(value)
            return None
        except Exception as e:
            logger.error("Error getting cache value", key=key, error=str(e))
            return None
    
    async def set(
        self, 
        key: str, 
        value: Any, 
        expire: Optional[Union[int, timedelta]] = None
    ) -> bool:
        """Set value in cache"""
        if not self.redis:
            return False
        
        try:
            # Serialize value
            if isinstance(value, (dict, list, str, int, float, bool, type(None))):
                serialized = json.dumps(value, default=str)
            else:
                serialized = pickle.dumps(value)
            
            # Set expiration
            if isinstance(expire, timedelta):
                expire = int(expire.total_seconds())
            
            await self.redis.set(key, serialized, ex=expire)
            return True
        except Exception as e:
            logger.error("Error setting cache value", key=key, error=str(e))
            return False
    
    async def delete(self, key: str) -> bool:
        """Delete key from cache"""
        if not self.redis:
            return False
        
        try:
            result = await self.redis.delete(key)
            return result > 0
        except Exception as e:
            logger.error("Error deleting cache key", key=key, error=str(e))
            return False
    
    async def delete_pattern(self, pattern: str) -> int:
        """Delete keys matching pattern"""
        if not self.redis:
            return 0
        
        try:
            keys = await self.redis.keys(pattern)
            if keys:
                result = await self.redis.delete(*keys)
                logger.info("Deleted cache keys", pattern=pattern, count=result)
                return result
            return 0
        except Exception as e:
            logger.error("Error deleting cache pattern", pattern=pattern, error=str(e))
            return 0
    
    async def exists(self, key: str) -> bool:
        """Check if key exists in cache"""
        if not self.redis:
            return False
        
        try:
            result = await self.redis.exists(key)
            return result > 0
        except Exception as e:
            logger.error("Error checking cache key existence", key=key, error=str(e))
            return False
    
    async def expire(self, key: str, seconds: int) -> bool:
        """Set expiration for key"""
        if not self.redis:
            return False
        
        try:
            result = await self.redis.expire(key, seconds)
            return result
        except Exception as e:
            logger.error("Error setting cache expiration", key=key, error=str(e))
            return False
    
    async def get_many(self, keys: List[str]) -> Dict[str, Any]:
        """Get multiple values from cache"""
        if not self.redis or not keys:
            return {}
        
        try:
            values = await self.redis.mget(keys)
            result = {}
            for key, value in zip(keys, values):
                if value:
                    try:
                        result[key] = json.loads(value)
                    except (json.JSONDecodeError, TypeError):
                        result[key] = pickle.loads(value)
            return result
        except Exception as e:
            logger.error("Error getting multiple cache values", keys=keys, error=str(e))
            return {}
    
    async def set_many(self, mapping: Dict[str, Any], expire: Optional[int] = None) -> bool:
        """Set multiple values in cache"""
        if not self.redis or not mapping:
            return False
        
        try:
            # Serialize values
            serialized = {}
            for key, value in mapping.items():
                if isinstance(value, (dict, list, str, int, float, bool, type(None))):
                    serialized[key] = json.dumps(value, default=str)
                else:
                    serialized[key] = pickle.dumps(value)
            
            await self.redis.mset(serialized)
            
            # Set expiration if provided
            if expire:
                for key in mapping.keys():
                    await self.redis.expire(key, expire)
            
            return True
        except Exception as e:
            logger.error("Error setting multiple cache values", error=str(e))
            return False
    
    async def clear_pattern(self, pattern: str) -> int:
        """Clear all keys matching pattern"""
        if not self.redis:
            return 0
        
        try:
            keys = await self.redis.keys(pattern)
            if keys:
                return await self.redis.delete(*keys)
            return 0
        except Exception as e:
            logger.error("Error clearing cache pattern", pattern=pattern, error=str(e))
            return 0
    
    async def get_stats(self) -> Dict[str, Any]:
        """Get Redis cache statistics"""
        if not self.redis:
            return {}
        
        try:
            info = await self.redis.info()
            return {
                "connected_clients": info.get("connected_clients", 0),
                "used_memory": info.get("used_memory_human", "0B"),
                "total_commands_processed": info.get("total_commands_processed", 0),
                "keyspace_hits": info.get("keyspace_hits", 0),
                "keyspace_misses": info.get("keyspace_misses", 0),
                "uptime_in_seconds": info.get("uptime_in_seconds", 0)
            }
        except Exception as e:
            logger.error("Error getting cache stats", error=str(e))
            return {}


# Global cache manager instance
cache_manager = CacheManager()


# Cache decorators and utilities
def cache_key(*args, **kwargs) -> str:
    """Generate cache key from arguments"""
    key_parts = []
    
    for arg in args:
        if hasattr(arg, 'id'):
            key_parts.append(f"{type(arg).__name__}:{arg.id}")
        else:
            key_parts.append(str(arg))
    
    for k, v in sorted(kwargs.items()):
        key_parts.append(f"{k}:{v}")
    
    return ":".join(key_parts)


def cached(
    key_func: callable = None,
    expire: int = 300,  # 5 minutes default
    prefix: str = "cache"
):
    """Decorator for caching function results"""
    def decorator(func):
        async def wrapper(*args, **kwargs):
            # Generate cache key
            if key_func:
                cache_key_str = f"{prefix}:{key_func(*args, **kwargs)}"
            else:
                cache_key_str = f"{prefix}:{func.__name__}:{cache_key(*args, **kwargs)}"
            
            # Try to get from cache
            cached_result = await cache_manager.get(cache_key_str)
            if cached_result is not None:
                logger.debug("Cache hit", key=cache_key_str, function=func.__name__)
                return cached_result
            
            # Execute function and cache result
            result = await func(*args, **kwargs)
            await cache_manager.set(cache_key_str, result, expire=expire)
            logger.debug("Cache set", key=cache_key_str, function=func.__name__)
            
            return result
        return wrapper
    return decorator


# Cache key generators for common use cases
def device_cache_key(device_id: int) -> str:
    """Generate cache key for device"""
    return f"device:{device_id}"


def user_cache_key(user_id: int) -> str:
    """Generate cache key for user"""
    return f"user:{user_id}"


def position_cache_key(device_id: int, limit: int = 100) -> str:
    """Generate cache key for device positions"""
    return f"positions:{device_id}:{limit}"


def event_cache_key(device_id: int, event_type: str = None) -> str:
    """Generate cache key for device events"""
    if event_type:
        return f"events:{device_id}:{event_type}"
    return f"events:{device_id}"


def geofence_cache_key(geofence_id: int) -> str:
    """Generate cache key for geofence"""
    return f"geofence:{geofence_id}"


def group_cache_key(group_id: int) -> str:
    """Generate cache key for group"""
    return f"group:{group_id}"


def person_cache_key(person_id: int) -> str:
    """Generate cache key for person"""
    return f"person:{person_id}"


# Cache invalidation helpers
async def invalidate_device_cache(device_id: int):
    """Invalidate all cache entries for a device"""
    patterns = [
        f"device:{device_id}",
        f"positions:{device_id}:*",
        f"events:{device_id}*"
    ]
    
    for pattern in patterns:
        await cache_manager.clear_pattern(pattern)
    logger.info("Invalidated device cache", device_id=device_id)


async def invalidate_user_cache(user_id: int):
    """Invalidate all cache entries for a user"""
    patterns = [
        f"user:{user_id}",
        f"user_devices:{user_id}",
        f"user_groups:{user_id}"
    ]
    
    for pattern in patterns:
        await cache_manager.clear_pattern(pattern)
    logger.info("Invalidated user cache", user_id=user_id)


async def invalidate_geofence_cache(geofence_id: int):
    """Invalidate all cache entries for a geofence"""
    patterns = [
        f"geofence:{geofence_id}",
        f"geofence_events:*:{geofence_id}"
    ]
    
    for pattern in patterns:
        await cache_manager.clear_pattern(pattern)
    logger.info("Invalidated geofence cache", geofence_id=geofence_id)


# Cache warming functions
async def warm_device_cache(device_id: int):
    """Warm cache with device data"""
    from app.services.device_service import get_device_by_id
    
    try:
        device = await get_device_by_id(device_id)
        if device:
            await cache_manager.set(
                device_cache_key(device_id), 
                device, 
                expire=600  # 10 minutes
            )
            logger.info("Warmed device cache", device_id=device_id)
    except Exception as e:
        logger.error("Error warming device cache", device_id=device_id, error=str(e))


async def warm_user_cache(user_id: int):
    """Warm cache with user data"""
    from app.services.auth_service import get_user_by_id
    
    try:
        user = await get_user_by_id(user_id)
        if user:
            await cache_manager.set(
                user_cache_key(user_id), 
                user, 
                expire=1800  # 30 minutes
            )
            logger.info("Warmed user cache", user_id=user_id)
    except Exception as e:
        logger.error("Error warming user cache", user_id=user_id, error=str(e))

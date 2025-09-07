"""
Cache management API endpoints
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Dict, Any, List, Optional
import structlog
from app.database import get_db
from app.api.auth import get_current_user
from app.models.user import User
from app.core.cache import cache_manager
from app.core.rate_limiter import get_rate_limit_stats

logger = structlog.get_logger(__name__)

router = APIRouter()


@router.get("/stats")
async def get_cache_stats(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get cache statistics (admin only)"""
    if not current_user.admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required"
        )
    
    try:
        cache_stats = await cache_manager.get_stats()
        rate_limit_stats = await get_rate_limit_stats()
        
        return {
            "cache": cache_stats,
            "rate_limiting": rate_limit_stats,
            "redis_connected": cache_manager.redis is not None
        }
    except Exception as e:
        logger.error("Error getting cache stats", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get cache statistics"
        )


@router.post("/clear")
async def clear_cache(
    pattern: Optional[str] = None,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Clear cache entries (admin only)"""
    if not current_user.admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required"
        )
    
    try:
        if pattern:
            cleared_count = await cache_manager.clear_pattern(pattern)
            logger.info("Cache cleared by pattern", pattern=pattern, count=cleared_count)
            return {
                "message": f"Cleared {cleared_count} cache entries matching pattern: {pattern}",
                "pattern": pattern,
                "cleared_count": cleared_count
            }
        else:
            # Clear all cache entries
            cleared_count = await cache_manager.clear_pattern("*")
            logger.info("All cache cleared", count=cleared_count)
            return {
                "message": f"Cleared all cache entries ({cleared_count} entries)",
                "cleared_count": cleared_count
            }
    except Exception as e:
        logger.error("Error clearing cache", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to clear cache"
        )


@router.post("/clear/device/{device_id}")
async def clear_device_cache(
    device_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Clear cache for a specific device (admin only)"""
    if not current_user.admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required"
        )
    
    try:
        from app.core.cache import invalidate_device_cache
        await invalidate_device_cache(device_id)
        
        logger.info("Device cache cleared", device_id=device_id)
        return {
            "message": f"Cache cleared for device {device_id}",
            "device_id": device_id
        }
    except Exception as e:
        logger.error("Error clearing device cache", device_id=device_id, error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to clear device cache"
        )


@router.post("/clear/user/{user_id}")
async def clear_user_cache(
    user_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Clear cache for a specific user (admin only)"""
    if not current_user.admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required"
        )
    
    try:
        from app.core.cache import invalidate_user_cache
        await invalidate_user_cache(user_id)
        
        logger.info("User cache cleared", user_id=user_id)
        return {
            "message": f"Cache cleared for user {user_id}",
            "user_id": user_id
        }
    except Exception as e:
        logger.error("Error clearing user cache", user_id=user_id, error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to clear user cache"
        )


@router.get("/keys")
async def list_cache_keys(
    pattern: str = "*",
    limit: int = 100,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """List cache keys (admin only)"""
    if not current_user.admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required"
        )
    
    try:
        if not cache_manager.redis:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Redis cache not available"
            )
        
        keys = await cache_manager.redis.keys(pattern)
        keys = [key.decode() if isinstance(key, bytes) else key for key in keys]
        
        # Limit results
        if limit > 0:
            keys = keys[:limit]
        
        return {
            "keys": keys,
            "count": len(keys),
            "pattern": pattern,
            "limit": limit
        }
    except Exception as e:
        logger.error("Error listing cache keys", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to list cache keys"
        )


@router.get("/key/{key}")
async def get_cache_key(
    key: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get cache key value (admin only)"""
    if not current_user.admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required"
        )
    
    try:
        value = await cache_manager.get(key)
        exists = await cache_manager.exists(key)
        
        return {
            "key": key,
            "exists": exists,
            "value": value
        }
    except Exception as e:
        logger.error("Error getting cache key", key=key, error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get cache key"
        )


@router.delete("/key/{key}")
async def delete_cache_key(
    key: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Delete cache key (admin only)"""
    if not current_user.admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required"
        )
    
    try:
        deleted = await cache_manager.delete(key)
        
        return {
            "key": key,
            "deleted": deleted
        }
    except Exception as e:
        logger.error("Error deleting cache key", key=key, error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete cache key"
        )


@router.post("/warm/device/{device_id}")
async def warm_device_cache(
    device_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Warm cache for a specific device (admin only)"""
    if not current_user.admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required"
        )
    
    try:
        from app.core.cache import warm_device_cache
        await warm_device_cache(device_id)
        
        logger.info("Device cache warmed", device_id=device_id)
        return {
            "message": f"Cache warmed for device {device_id}",
            "device_id": device_id
        }
    except Exception as e:
        logger.error("Error warming device cache", device_id=device_id, error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to warm device cache"
        )


@router.post("/warm/user/{user_id}")
async def warm_user_cache(
    user_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Warm cache for a specific user (admin only)"""
    if not current_user.admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required"
        )
    
    try:
        from app.core.cache import warm_user_cache
        await warm_user_cache(user_id)
        
        logger.info("User cache warmed", user_id=user_id)
        return {
            "message": f"Cache warmed for user {user_id}",
            "user_id": user_id
        }
    except Exception as e:
        logger.error("Error warming user cache", user_id=user_id, error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to warm user cache"
        )

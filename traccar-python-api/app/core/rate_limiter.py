"""
Rate limiting implementation using Redis
"""
import time
from typing import Optional, Dict, Any
from fastapi import HTTPException, Request
from fastapi.responses import JSONResponse
import structlog
from app.core.cache import cache_manager

logger = structlog.get_logger(__name__)


class RateLimiter:
    """Redis-based rate limiter"""
    
    def __init__(self, cache_manager):
        self.cache = cache_manager
    
    async def is_allowed(
        self, 
        key: str, 
        limit: int, 
        window: int,
        identifier: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Check if request is allowed based on rate limit
        
        Args:
            key: Rate limit key (e.g., "api:user:123")
            limit: Maximum requests allowed
            window: Time window in seconds
            identifier: Optional identifier for logging
        
        Returns:
            Dict with allowed status and remaining requests
        """
        try:
            current_time = int(time.time())
            window_start = current_time - window
            
            # Get current requests in window
            requests_key = f"rate_limit:{key}:requests"
            current_requests = await self.cache.get(requests_key) or []
            
            # Filter requests within window
            valid_requests = [
                req_time for req_time in current_requests 
                if req_time > window_start
            ]
            
            # Check if limit exceeded
            if len(valid_requests) >= limit:
                return {
                    "allowed": False,
                    "remaining": 0,
                    "reset_time": min(valid_requests) + window,
                    "limit": limit,
                    "window": window
                }
            
            # Add current request
            valid_requests.append(current_time)
            
            # Update cache
            await self.cache.set(requests_key, valid_requests, expire=window)
            
            return {
                "allowed": True,
                "remaining": limit - len(valid_requests),
                "reset_time": current_time + window,
                "limit": limit,
                "window": window
            }
            
        except Exception as e:
            logger.error("Rate limit check failed", key=key, error=str(e))
            # Fail open - allow request if rate limiting fails
            return {
                "allowed": True,
                "remaining": limit,
                "reset_time": int(time.time()) + window,
                "limit": limit,
                "window": window
            }
    
    async def get_remaining(self, key: str, limit: int, window: int) -> int:
        """Get remaining requests for a key"""
        result = await self.is_allowed(key, limit, window)
        return result["remaining"]
    
    async def reset(self, key: str) -> bool:
        """Reset rate limit for a key"""
        try:
            requests_key = f"rate_limit:{key}:requests"
            return await self.cache.delete(requests_key)
        except Exception as e:
            logger.error("Rate limit reset failed", key=key, error=str(e))
            return False


# Global rate limiter instance
rate_limiter = RateLimiter(cache_manager)


# Rate limit configurations
RATE_LIMITS = {
    "auth": {
        "login": {"limit": 5, "window": 300},  # 5 attempts per 5 minutes
        "register": {"limit": 3, "window": 3600},  # 3 attempts per hour
        "password_reset": {"limit": 3, "window": 3600},  # 3 attempts per hour
    },
    "api": {
        "general": {"limit": 1000, "window": 3600},  # 1000 requests per hour
        "devices": {"limit": 500, "window": 3600},  # 500 requests per hour
        "positions": {"limit": 2000, "window": 3600},  # 2000 requests per hour
        "events": {"limit": 1000, "window": 3600},  # 1000 requests per hour
        "reports": {"limit": 100, "window": 3600},  # 100 requests per hour
    },
    "websocket": {
        "connection": {"limit": 10, "window": 60},  # 10 connections per minute
        "messages": {"limit": 100, "window": 60},  # 100 messages per minute
    },
    "protocol": {
        "suntech": {"limit": 10000, "window": 3600},  # 10000 messages per hour
        "osmand": {"limit": 10000, "window": 3600},  # 10000 messages per hour
    }
}


def get_rate_limit_config(category: str, endpoint: str = "general") -> Dict[str, int]:
    """Get rate limit configuration for category and endpoint"""
    return RATE_LIMITS.get(category, {}).get(endpoint, {"limit": 100, "window": 3600})


async def check_rate_limit(
    request: Request,
    category: str,
    endpoint: str = "general",
    user_id: Optional[int] = None,
    device_id: Optional[str] = None
) -> Dict[str, Any]:
    """
    Check rate limit for request
    
    Args:
        request: FastAPI request object
        category: Rate limit category (auth, api, websocket, protocol)
        endpoint: Specific endpoint within category
        user_id: Optional user ID for user-specific limits
        device_id: Optional device ID for device-specific limits
    
    Returns:
        Rate limit result
    """
    # Get client IP
    client_ip = request.client.host if request.client else "unknown"
    
    # Build rate limit key
    key_parts = [category, endpoint]
    
    if user_id:
        key_parts.append(f"user:{user_id}")
    elif device_id:
        key_parts.append(f"device:{device_id}")
    else:
        key_parts.append(f"ip:{client_ip}")
    
    key = ":".join(key_parts)
    
    # Get rate limit configuration
    config = get_rate_limit_config(category, endpoint)
    
    # Check rate limit
    result = await rate_limiter.is_allowed(
        key=key,
        limit=config["limit"],
        window=config["window"]
    )
    
    # Log rate limit check
    logger.info(
        "Rate limit check",
        key=key,
        allowed=result["allowed"],
        remaining=result["remaining"],
        limit=result["limit"],
        category=category,
        endpoint=endpoint
    )
    
    return result


async def rate_limit_middleware(
    request: Request,
    category: str,
    endpoint: str = "general",
    user_id: Optional[int] = None,
    device_id: Optional[str] = None
):
    """
    Middleware function for rate limiting
    
    Raises HTTPException if rate limit exceeded
    """
    result = await check_rate_limit(request, category, endpoint, user_id, device_id)
    
    if not result["allowed"]:
        raise HTTPException(
            status_code=429,
            detail={
                "error": "Rate limit exceeded",
                "limit": result["limit"],
                "window": result["window"],
                "reset_time": result["reset_time"]
            },
            headers={
                "X-RateLimit-Limit": str(result["limit"]),
                "X-RateLimit-Remaining": str(result["remaining"]),
                "X-RateLimit-Reset": str(result["reset_time"])
            }
        )
    
    return result


# FastAPI dependency for rate limiting
async def rate_limit_dependency(
    request: Request,
    category: str,
    endpoint: str = "general"
):
    """FastAPI dependency for rate limiting"""
    return await rate_limit_middleware(request, category, endpoint)


# Rate limit decorators
def rate_limit(category: str, endpoint: str = "general"):
    """Decorator for rate limiting endpoints"""
    def decorator(func):
        async def wrapper(*args, **kwargs):
            # Extract request from args (assuming it's the first argument)
            request = None
            for arg in args:
                if isinstance(arg, Request):
                    request = arg
                    break
            
            if request:
                await rate_limit_middleware(request, category, endpoint)
            
            return await func(*args, **kwargs)
        return wrapper
    return decorator


# Rate limit stats
async def get_rate_limit_stats() -> Dict[str, Any]:
    """Get rate limiting statistics"""
    try:
        # Get all rate limit keys
        pattern = "rate_limit:*:requests"
        keys = await cache_manager.redis.keys(pattern) if cache_manager.redis else []
        
        stats = {
            "total_rate_limit_keys": len(keys),
            "categories": {},
            "top_limited_keys": []
        }
        
        # Analyze rate limit usage by category
        for key in keys:
            key_str = key.decode() if isinstance(key, bytes) else key
            parts = key_str.split(":")
            if len(parts) >= 3:
                category = parts[1]
                if category not in stats["categories"]:
                    stats["categories"][category] = {"keys": 0, "total_requests": 0}
                
                stats["categories"][category]["keys"] += 1
                
                # Get request count for this key
                requests = await cache_manager.get(key_str) or []
                stats["categories"][category]["total_requests"] += len(requests)
        
        return stats
        
    except Exception as e:
        logger.error("Error getting rate limit stats", error=str(e))
        return {"error": str(e)}


# Add method to RateLimiter class
class RateLimiter:
    """Redis-based rate limiter"""
    
    def __init__(self, cache_manager):
        self.cache = cache_manager
    
    async def is_allowed(
        self, 
        key: str, 
        limit: int, 
        window: int,
        identifier: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Check if request is allowed based on rate limit
        
        Args:
            key: Rate limit key (e.g., "api:user:123")
            limit: Maximum requests allowed
            window: Time window in seconds
            identifier: Optional identifier for logging
        
        Returns:
            Dict with allowed status and remaining requests
        """
        try:
            current_time = int(time.time())
            window_start = current_time - window
            
            # Get current requests in window
            requests_key = f"rate_limit:{key}:requests"
            current_requests = await self.cache.get(requests_key) or []
            
            # Filter requests within window
            valid_requests = [
                req_time for req_time in current_requests 
                if req_time > window_start
            ]
            
            # Check if limit exceeded
            if len(valid_requests) >= limit:
                return {
                    "allowed": False,
                    "remaining": 0,
                    "reset_time": min(valid_requests) + window,
                    "limit": limit,
                    "window": window
                }
            
            # Add current request
            valid_requests.append(current_time)
            
            # Update cache
            await self.cache.set(requests_key, valid_requests, expire=window)
            
            return {
                "allowed": True,
                "remaining": limit - len(valid_requests),
                "reset_time": current_time + window,
                "limit": limit,
                "window": window
            }
            
        except Exception as e:
            logger.error("Rate limit check failed", key=key, error=str(e))
            # Fail open - allow request if rate limiting fails
            return {
                "allowed": True,
                "remaining": limit,
                "reset_time": int(time.time()) + window,
                "limit": limit,
                "window": window
            }
    
    async def get_remaining(self, key: str, limit: int, window: int) -> int:
        """Get remaining requests for a key"""
        result = await self.is_allowed(key, limit, window)
        return result["remaining"]
    
    async def reset(self, key: str) -> bool:
        """Reset rate limit for a key"""
        try:
            requests_key = f"rate_limit:{key}:requests"
            return await self.cache.delete(requests_key)
        except Exception as e:
            logger.error("Rate limit reset failed", key=key, error=str(e))
            return False
    
    async def get_rate_limit_stats(self) -> Dict[str, Any]:
        """Get rate limiting statistics"""
        return await get_rate_limit_stats()

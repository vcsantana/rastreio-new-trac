"""
Custom middleware for the Traccar API
"""
from fastapi import Request, Response
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
import time
import structlog
from app.core.rate_limiter import check_rate_limit
from app.core.session import update_session_context

logger = structlog.get_logger(__name__)


class RateLimitMiddleware(BaseHTTPMiddleware):
    """Rate limiting middleware"""
    
    async def dispatch(self, request: Request, call_next):
        """Process request with rate limiting"""
        try:
            # Determine rate limit category based on path
            path = request.url.path
            
            if path.startswith("/api/auth"):
                category = "auth"
                if "login" in path:
                    endpoint = "login"
                elif "register" in path:
                    endpoint = "register"
                else:
                    endpoint = "general"
            elif path.startswith("/api/devices"):
                category = "api"
                endpoint = "devices"
            elif path.startswith("/api/positions"):
                category = "api"
                endpoint = "positions"
            elif path.startswith("/api/events"):
                category = "api"
                endpoint = "events"
            elif path.startswith("/api/reports"):
                category = "api"
                endpoint = "reports"
            elif path.startswith("/ws/"):
                category = "websocket"
                endpoint = "connection"
            else:
                category = "api"
                endpoint = "general"
            
            # Check rate limit
            rate_limit_result = await check_rate_limit(
                request=request,
                category=category,
                endpoint=endpoint
            )
            
            # Add rate limit headers to response
            response = await call_next(request)
            
            response.headers["X-RateLimit-Limit"] = str(rate_limit_result["limit"])
            response.headers["X-RateLimit-Remaining"] = str(rate_limit_result["remaining"])
            response.headers["X-RateLimit-Reset"] = str(rate_limit_result["reset_time"])
            
            return response
            
        except Exception as e:
            logger.error("Rate limit middleware error", error=str(e))
            # Continue without rate limiting if there's an error
            return await call_next(request)


class SessionMiddleware(BaseHTTPMiddleware):
    """Session management middleware"""
    
    async def dispatch(self, request: Request, call_next):
        """Process request with session management"""
        try:
            # Extract session token from Authorization header or cookies
            session_token = None
            
            # Check Authorization header
            auth_header = request.headers.get("Authorization")
            if auth_header and auth_header.startswith("Bearer "):
                session_token = auth_header[7:]
            
            # Check cookies
            if not session_token:
                session_token = request.cookies.get("session_token")
            
            # Update session context if token exists
            if session_token:
                client_ip = request.client.host if request.client else "unknown"
                user_agent = request.headers.get("User-Agent", "unknown")
                
                await update_session_context(session_token, client_ip, user_agent)
            
            response = await call_next(request)
            return response
            
        except Exception as e:
            logger.error("Session middleware error", error=str(e))
            # Continue without session management if there's an error
            return await call_next(request)


class LoggingMiddleware(BaseHTTPMiddleware):
    """Request logging middleware"""
    
    async def dispatch(self, request: Request, call_next):
        """Log request and response"""
        start_time = time.time()
        
        # Log request
        logger.info(
            "Request started",
            method=request.method,
            path=request.url.path,
            client_ip=request.client.host if request.client else "unknown",
            user_agent=request.headers.get("User-Agent", "unknown")
        )
        
        try:
            response = await call_next(request)
            
            # Calculate processing time
            process_time = time.time() - start_time
            
            # Log response
            logger.info(
                "Request completed",
                method=request.method,
                path=request.url.path,
                status_code=response.status_code,
                process_time=round(process_time, 4),
                client_ip=request.client.host if request.client else "unknown"
            )
            
            # Add processing time header
            response.headers["X-Process-Time"] = str(round(process_time, 4))
            
            return response
            
        except Exception as e:
            process_time = time.time() - start_time
            
            logger.error(
                "Request failed",
                method=request.method,
                path=request.url.path,
                error=str(e),
                process_time=round(process_time, 4),
                client_ip=request.client.host if request.client else "unknown"
            )
            
            return JSONResponse(
                status_code=500,
                content={"detail": "Internal server error"},
                headers={"X-Process-Time": str(round(process_time, 4))}
            )


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """Security headers middleware"""
    
    async def dispatch(self, request: Request, call_next):
        """Add security headers to response"""
        response = await call_next(request)
        
        # Add security headers
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        response.headers["Permissions-Policy"] = "geolocation=(), microphone=(), camera=()"
        
        # Add HSTS header for HTTPS
        if request.url.scheme == "https":
            response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
        
        return response

"""
Traccar Python API - Main FastAPI Application
"""
from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.responses import JSONResponse
import structlog
import uvicorn

from app.config import settings
from app.database import init_db
from app.api import auth, devices, positions, websocket, events, geofences, server, protocols, reports, groups, persons, logs, unknown_devices, users, cache, tasks, commands
# Import models to ensure they are registered with SQLAlchemy
from app.models import user, device, position, event, geofence, report, group, person, unknown_device, command
from app.models import server as server_model
# Import protocol server manager
from app.protocols import start_protocol_servers, stop_protocol_servers
# Import cache manager
from app.core.cache import cache_manager
# Import middleware
from app.core.middleware import (
    RateLimitMiddleware, 
    SessionMiddleware, 
    LoggingMiddleware, 
    SecurityHeadersMiddleware
)
# Import Celery app
from app.core.celery_app import celery_app

# Configure structured logging
structlog.configure(
    processors=[
        structlog.stdlib.filter_by_level,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.stdlib.PositionalArgumentsFormatter(),
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
        structlog.processors.UnicodeDecoder(),
        structlog.processors.JSONRenderer()
    ],
    context_class=dict,
    logger_factory=structlog.stdlib.LoggerFactory(),
    wrapper_class=structlog.stdlib.BoundLogger,
    cache_logger_on_first_use=True,
)

logger = structlog.get_logger(__name__)

# Global instances - simplified for now
# websocket_manager = WebSocketManager()
# protocol_server_manager = ProtocolServerManager()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan management"""
    logger.info("Starting Traccar Python API", version=settings.VERSION)
    
    # Initialize database
    await init_db()
    logger.info("Database initialized")
    
    # Initialize Redis cache
    try:
        await cache_manager.connect()
        logger.info("Redis cache connected successfully")
    except Exception as e:
        logger.error("Failed to connect to Redis cache", error=str(e))
        # Continue without cache if Redis is not available
    
    # Initialize Celery (background tasks)
    try:
        # Test Celery connection
        celery_app.control.inspect().ping()
        logger.info("Celery background tasks initialized successfully")
    except Exception as e:
        logger.error("Failed to initialize Celery", error=str(e))
        # Continue without background tasks if Celery is not available
    
    # Start protocol servers
    try:
        await start_protocol_servers()
        logger.info("Protocol servers started successfully")
    except Exception as e:
        logger.error("Failed to start protocol servers", error=str(e))
    
    logger.info("Application started")
    
    yield
    
    # Cleanup
    try:
        await stop_protocol_servers()
        logger.info("Protocol servers stopped successfully")
    except Exception as e:
        logger.error("Error stopping protocol servers", error=str(e))
    
    # Disconnect from Redis
    try:
        await cache_manager.disconnect()
        logger.info("Redis cache disconnected successfully")
    except Exception as e:
        logger.error("Error disconnecting from Redis cache", error=str(e))
    
    logger.info("Application stopped")
    logger.info("Traccar Python API shutdown complete")


# Create FastAPI application
app = FastAPI(
    title="Traccar Python API",
    description="Modern GPS tracking server API built with FastAPI",
    version=settings.VERSION,
    docs_url="/docs" if settings.ENABLE_DOCS else None,
    redoc_url="/redoc" if settings.ENABLE_DOCS else None,
    openapi_url="/openapi.json" if settings.ENABLE_DOCS else None,
    lifespan=lifespan
)

# Add middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_HOSTS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.add_middleware(
    TrustedHostMiddleware,
    allowed_hosts=settings.ALLOWED_HOSTS
)

# Add custom middleware
app.add_middleware(SecurityHeadersMiddleware)
app.add_middleware(LoggingMiddleware)
app.add_middleware(SessionMiddleware)
app.add_middleware(RateLimitMiddleware)

# Global exception handler
@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    logger.error("Unhandled exception", exc_info=exc, path=request.url.path)
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error"}
    )

# Health check endpoint
@app.get("/health")
async def health_check():
    """Health check endpoint"""
    from app.protocols import get_protocol_server_status
    
    protocol_status = get_protocol_server_status()
    active_protocols = sum(1 for server in protocol_status.values() if server.get("running", False))
    
    # Get cache status
    cache_stats = await cache_manager.get_stats()
    cache_connected = cache_manager.redis is not None
    
    # Get Celery status
    celery_connected = False
    celery_workers = 0
    try:
        inspect = celery_app.control.inspect()
        active_tasks = inspect.active()
        celery_connected = True
        celery_workers = len(active_tasks) if active_tasks else 0
    except Exception:
        celery_connected = False
    
    return {
        "status": "healthy",
        "version": settings.VERSION,
        "protocols_active": active_protocols,
        "protocols": protocol_status,
        "cache": {
            "connected": cache_connected,
            "stats": cache_stats
        },
        "celery": {
            "connected": celery_connected,
            "workers": celery_workers
        }
    }

# Include API routers
app.include_router(auth.router, prefix="/api/auth", tags=["Authentication"])
app.include_router(devices.router, prefix="/api/devices", tags=["Devices"])
app.include_router(groups.router, prefix="/api/groups", tags=["Groups"])
app.include_router(persons.router, prefix="/api/persons", tags=["Persons"])
app.include_router(positions.router, prefix="/api/positions", tags=["Positions"])
app.include_router(events.router, prefix="/api", tags=["Events"])
app.include_router(geofences.router, prefix="/api", tags=["Geofences"])
app.include_router(server.router, prefix="/api", tags=["Server"])
app.include_router(protocols.router, prefix="/api/protocols", tags=["Protocols"])
app.include_router(reports.router, prefix="/api/reports", tags=["Reports"])
app.include_router(logs.router, tags=["Logs"])
app.include_router(unknown_devices.router, prefix="/api/unknown-devices", tags=["Unknown Devices"])
app.include_router(users.router, prefix="/api/users", tags=["Users"])
app.include_router(websocket.router, tags=["WebSocket"])
app.include_router(cache.router, prefix="/api/cache", tags=["Cache Management"])
app.include_router(tasks.router, prefix="/api/tasks", tags=["Background Tasks"])
app.include_router(commands.router, tags=["Commands"])

# Startup and shutdown events
@app.on_event("startup")
async def startup_event():
    """Startup event handler."""
    logger.info("Starting Traccar Python API...")
    
    # Initialize database
    await init_db()
    logger.info("Database initialized")
    
    # Start protocol servers (optional, can be started manually via API)
    try:
        await start_protocol_servers()
        logger.info("Protocol servers started")
    except Exception as e:
        logger.error("Failed to start protocol servers", error=str(e))

@app.on_event("shutdown")
async def shutdown_event():
    """Shutdown event handler."""
    logger.info("Shutting down Traccar Python API...")
    
    # Stop protocol servers
    await stop_protocol_servers()
    logger.info("Protocol servers stopped")


if __name__ == "__main__":
    uvicorn.run(
        "app.main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.DEBUG,
        log_config=None,  # Use structlog instead
    )

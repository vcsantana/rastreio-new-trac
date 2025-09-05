"""
Server configuration API endpoints.
"""

from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from sqlalchemy import func, and_

from app.database import get_db
from app.models import Server, User
from app.schemas.server import (
    ServerConfigCreate,
    ServerConfigUpdate,
    ServerConfigResponse,
    ServerConfigList,
    NotificationConfigCreate,
    NotificationConfigUpdate,
    NotificationConfigResponse,
    WebServerConfigCreate,
    WebServerConfigUpdate,
    WebServerConfigResponse,
    ServerStatsResponse,
    ServerHealthResponse,
    ServerInfoResponse,
    MapProviderType,
    NotificationType
)
from app.api.auth import get_current_user
from app.config import settings

router = APIRouter()


@router.get("/server/config", response_model=ServerConfigResponse)
async def get_server_config(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get server configuration."""
    if not current_user.admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required"
        )
    
    server_config = db.query(Server).first()
    if not server_config:
        # Create default configuration if none exists
        default_config = ServerConfigCreate(
            name="Traccar Server",
            registration_enabled=True,
            map_provider=MapProviderType.OPENSTREETMAP,
            timezone="UTC",
            language="en",
            distance_unit="km",
            speed_unit="kmh",
            volume_unit="l",
            zoom=6
        )
        server_config = Server(**default_config.dict())
        db.add(server_config)
        db.commit()
        db.refresh(server_config)
    
    return server_config


@router.put("/server/config", response_model=ServerConfigResponse)
async def update_server_config(
    config_update: ServerConfigUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Update server configuration."""
    if not current_user.admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required"
        )
    
    server_config = db.query(Server).first()
    if not server_config:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Server configuration not found"
        )
    
    # Update only provided fields
    update_data = config_update.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(server_config, field, value)
    
    server_config.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(server_config)
    
    return server_config


@router.post("/server/config", response_model=ServerConfigResponse)
async def create_server_config(
    config_create: ServerConfigCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Create server configuration."""
    if not current_user.admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required"
        )
    
    # Check if configuration already exists
    existing_config = db.query(Server).first()
    if existing_config:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Server configuration already exists"
        )
    
    server_config = Server(**config_create.dict())
    db.add(server_config)
    db.commit()
    db.refresh(server_config)
    
    return server_config


@router.get("/server/notifications", response_model=List[NotificationConfigResponse])
async def get_notification_configs(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get notification configurations."""
    if not current_user.admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required"
        )
    
    # For now, return empty list as notification configs are stored in server config
    # In a full implementation, this would be a separate table
    return []


@router.post("/server/notifications", response_model=NotificationConfigResponse)
async def create_notification_config(
    notification_create: NotificationConfigCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Create notification configuration."""
    if not current_user.admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required"
        )
    
    # For now, store in server config attributes
    # In a full implementation, this would be a separate table
    server_config = db.query(Server).first()
    if not server_config:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Server configuration not found"
        )
    
    if not server_config.attributes:
        server_config.attributes = {}
    
    notification_key = f"notification_{notification_create.type.value}"
    server_config.attributes[notification_key] = notification_create.dict()
    server_config.updated_at = datetime.utcnow()
    
    db.commit()
    db.refresh(server_config)
    
    # Return mock response for now
    return NotificationConfigResponse(
        id=1,
        type=notification_create.type,
        enabled=notification_create.enabled,
        smtp_host=notification_create.smtp_host,
        smtp_port=notification_create.smtp_port,
        smtp_username=notification_create.smtp_username,
        smtp_password=notification_create.smtp_password,
        smtp_encryption=notification_create.smtp_encryption,
        smtp_from=notification_create.smtp_from,
        sms_url=notification_create.sms_url,
        sms_username=notification_create.sms_username,
        sms_password=notification_create.sms_password,
        webhook_url=notification_create.webhook_url,
        webhook_headers=notification_create.webhook_headers,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow()
    )


@router.get("/server/webserver", response_model=WebServerConfigResponse)
async def get_webserver_config(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get web server configuration."""
    if not current_user.admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required"
        )
    
    # Return current settings as webserver config
    return WebServerConfigResponse(
        id=1,
        port=settings.PORT,
        host=settings.HOST,
        ssl_enabled=False,  # Would be from settings
        ssl_cert=None,
        ssl_key=None,
        cors_origins=settings.CORS_ORIGINS,
        cors_methods=["GET", "POST", "PUT", "DELETE"],
        cors_headers=["*"],
        max_request_size=10485760,
        request_timeout=30,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow()
    )


@router.put("/server/webserver", response_model=WebServerConfigResponse)
async def update_webserver_config(
    webserver_update: WebServerConfigUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Update web server configuration."""
    if not current_user.admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required"
        )
    
    # Store webserver config in server attributes
    server_config = db.query(Server).first()
    if not server_config:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Server configuration not found"
        )
    
    if not server_config.attributes:
        server_config.attributes = {}
    
    update_data = webserver_update.dict(exclude_unset=True)
    server_config.attributes["webserver"] = update_data
    server_config.updated_at = datetime.utcnow()
    
    db.commit()
    db.refresh(server_config)
    
    # Return updated config
    current_config = server_config.attributes.get("webserver", {})
    return WebServerConfigResponse(
        id=1,
        port=current_config.get("port", settings.PORT),
        host=current_config.get("host", settings.HOST),
        ssl_enabled=current_config.get("ssl_enabled", False),
        ssl_cert=current_config.get("ssl_cert"),
        ssl_key=current_config.get("ssl_key"),
        cors_origins=current_config.get("cors_origins", settings.CORS_ORIGINS),
        cors_methods=current_config.get("cors_methods", ["GET", "POST", "PUT", "DELETE"]),
        cors_headers=current_config.get("cors_headers", ["*"]),
        max_request_size=current_config.get("max_request_size", 10485760),
        request_timeout=current_config.get("request_timeout", 30),
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow()
    )


@router.get("/server/stats", response_model=ServerStatsResponse)
async def get_server_stats(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get server statistics."""
    if not current_user.admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required"
        )
    
    from app.models import Device, Position, Event, Geofence
    
    # Get counts
    total_users = db.query(func.count(User.id)).scalar()
    total_devices = db.query(func.count(Device.id)).scalar()
    total_positions = db.query(func.count(Position.id)).scalar()
    total_events = db.query(func.count(Event.id)).scalar()
    total_geofences = db.query(func.count(Geofence.id)).scalar()
    
    # Get online/offline device counts
    online_devices = db.query(func.count(Device.id)).filter(
        Device.status == "online"
    ).scalar()
    offline_devices = total_devices - online_devices
    
    # Mock system stats (in real implementation, these would come from system monitoring)
    server_uptime = 3600  # 1 hour in seconds
    memory_usage = 45.2  # 45.2%
    cpu_usage = 12.8  # 12.8%
    disk_usage = 67.5  # 67.5%
    
    return ServerStatsResponse(
        total_users=total_users,
        total_devices=total_devices,
        total_positions=total_positions,
        total_events=total_events,
        total_geofences=total_geofences,
        online_devices=online_devices,
        offline_devices=offline_devices,
        server_uptime=server_uptime,
        memory_usage=memory_usage,
        cpu_usage=cpu_usage,
        disk_usage=disk_usage
    )


@router.get("/server/health", response_model=ServerHealthResponse)
async def get_server_health(
    db: Session = Depends(get_db)
):
    """Get server health status."""
    try:
        # Test database connection
        db.execute("SELECT 1")
        database_status = "healthy"
    except Exception:
        database_status = "unhealthy"
    
    # Mock system stats
    memory_usage = 45.2
    cpu_usage = 12.8
    uptime = 3600  # 1 hour in seconds
    
    return ServerHealthResponse(
        status="healthy" if database_status == "healthy" else "unhealthy",
        timestamp=datetime.utcnow(),
        version="1.0.0",
        database_status=database_status,
        redis_status="not_configured",  # Would check Redis if configured
        uptime=uptime,
        memory_usage=memory_usage,
        cpu_usage=cpu_usage
    )


@router.get("/server/info", response_model=ServerInfoResponse)
async def get_server_info(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get server information."""
    if not current_user.admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required"
        )
    
    server_config = db.query(Server).first()
    
    # Mock system info (in real implementation, these would come from system)
    return ServerInfoResponse(
        name=server_config.name if server_config else "Traccar Server",
        version="1.0.0",
        build_time=datetime.utcnow(),
        java_version=None,  # Not applicable for Python
        os_name="Linux",
        os_version="5.4.0",
        os_arch="x86_64",
        memory_total=8589934592,  # 8GB
        memory_used=3865470566,   # ~3.6GB
        cpu_count=4,
        timezone=server_config.timezone if server_config else "UTC",
        language=server_config.language if server_config else "en",
        distance_unit=server_config.distance_unit if server_config else "km",
        speed_unit=server_config.speed_unit if server_config else "kmh",
        volume_unit=server_config.volume_unit if server_config else "l"
    )


@router.post("/server/restart")
async def restart_server(
    current_user: User = Depends(get_current_user)
):
    """Restart server (mock endpoint)."""
    if not current_user.admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required"
        )
    
    # In a real implementation, this would trigger a server restart
    # For now, just return success
    return {"message": "Server restart initiated", "status": "success"}


@router.post("/server/backup")
async def create_backup(
    current_user: User = Depends(get_current_user)
):
    """Create server backup (mock endpoint)."""
    if not current_user.admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required"
        )
    
    # In a real implementation, this would create a database backup
    backup_filename = f"traccar_backup_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.sql"
    
    return {
        "message": "Backup created successfully",
        "filename": backup_filename,
        "status": "success"
    }


@router.get("/server/logs")
async def get_server_logs(
    lines: int = Query(default=100, ge=1, le=1000, description="Number of log lines to retrieve"),
    level: Optional[str] = Query(default=None, description="Log level filter"),
    current_user: User = Depends(get_current_user)
):
    """Get server logs (mock endpoint)."""
    if not current_user.admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required"
        )
    
    # In a real implementation, this would read actual log files
    mock_logs = [
        f"{datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')} INFO: Server started",
        f"{datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')} INFO: Database connected",
        f"{datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')} INFO: API endpoints loaded",
        f"{datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')} INFO: WebSocket server started",
    ]
    
    return {
        "logs": mock_logs[:lines],
        "total_lines": len(mock_logs),
        "level": level,
        "timestamp": datetime.utcnow()
    }


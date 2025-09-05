"""
Server configuration schemas for Pydantic validation.
"""

from datetime import datetime
from typing import Optional, Dict, Any, List
from pydantic import BaseModel, Field, validator
from enum import Enum


class MapProviderType(str, Enum):
    """Map provider types."""
    BING = "bing"
    MAPBOX = "mapbox"
    OPENSTREETMAP = "openstreetmap"
    GOOGLE = "google"


class NotificationType(str, Enum):
    """Notification types."""
    EMAIL = "email"
    SMS = "sms"
    WEBHOOK = "webhook"


class ServerConfigBase(BaseModel):
    """Base server configuration schema."""
    name: str = Field(..., min_length=1, max_length=100, description="Server name")
    registration_enabled: bool = Field(default=True, description="Enable user registration")
    limit_commands: bool = Field(default=False, description="Limit commands to admin users")
    map_provider: MapProviderType = Field(default=MapProviderType.OPENSTREETMAP, description="Map provider")
    map_url: Optional[str] = Field(default=None, max_length=500, description="Custom map URL")
    bing_key: Optional[str] = Field(default=None, max_length=100, description="Bing Maps API key")
    mapbox_key: Optional[str] = Field(default=None, max_length=100, description="Mapbox API key")
    google_key: Optional[str] = Field(default=None, max_length=100, description="Google Maps API key")
    coordinate_format: str = Field(default="decimal", max_length=20, description="Coordinate format")
    timezone: str = Field(default="UTC", max_length=50, description="Server timezone")
    language: str = Field(default="en", max_length=10, description="Default language")
    distance_unit: str = Field(default="km", max_length=10, description="Distance unit")
    speed_unit: str = Field(default="kmh", max_length=10, description="Speed unit")
    volume_unit: str = Field(default="l", max_length=10, description="Volume unit")
    latitude: Optional[float] = Field(default=None, ge=-90, le=90, description="Default latitude")
    longitude: Optional[float] = Field(default=None, ge=-180, le=180, description="Default longitude")
    zoom: int = Field(default=6, ge=1, le=20, description="Default map zoom level")
    poi_layer: bool = Field(default=False, description="Enable POI layer")
    traffic_layer: bool = Field(default=False, description="Enable traffic layer")
    attributes: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Additional attributes")


class ServerConfigCreate(ServerConfigBase):
    """Schema for creating server configuration."""
    pass


class ServerConfigUpdate(BaseModel):
    """Schema for updating server configuration."""
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    registration_enabled: Optional[bool] = None
    limit_commands: Optional[bool] = None
    map_provider: Optional[MapProviderType] = None
    map_url: Optional[str] = Field(None, max_length=500)
    bing_key: Optional[str] = Field(None, max_length=100)
    mapbox_key: Optional[str] = Field(None, max_length=100)
    google_key: Optional[str] = Field(None, max_length=100)
    coordinate_format: Optional[str] = Field(None, max_length=20)
    timezone: Optional[str] = Field(None, max_length=50)
    language: Optional[str] = Field(None, max_length=10)
    distance_unit: Optional[str] = Field(None, max_length=10)
    speed_unit: Optional[str] = Field(None, max_length=10)
    volume_unit: Optional[str] = Field(None, max_length=10)
    latitude: Optional[float] = Field(None, ge=-90, le=90)
    longitude: Optional[float] = Field(None, ge=-180, le=180)
    zoom: Optional[int] = Field(None, ge=1, le=20)
    poi_layer: Optional[bool] = None
    traffic_layer: Optional[bool] = None
    attributes: Optional[Dict[str, Any]] = None


class ServerConfigResponse(ServerConfigBase):
    """Schema for server configuration response."""
    id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class ServerConfigList(BaseModel):
    """Schema for server configuration list response."""
    items: List[ServerConfigResponse]
    total: int
    page: int
    size: int
    pages: int


class NotificationConfigBase(BaseModel):
    """Base notification configuration schema."""
    type: NotificationType = Field(..., description="Notification type")
    enabled: bool = Field(default=True, description="Enable notifications")
    smtp_host: Optional[str] = Field(default=None, max_length=255, description="SMTP host")
    smtp_port: Optional[int] = Field(default=None, ge=1, le=65535, description="SMTP port")
    smtp_username: Optional[str] = Field(default=None, max_length=255, description="SMTP username")
    smtp_password: Optional[str] = Field(default=None, max_length=255, description="SMTP password")
    smtp_encryption: Optional[str] = Field(default=None, max_length=20, description="SMTP encryption")
    smtp_from: Optional[str] = Field(default=None, max_length=255, description="SMTP from address")
    sms_url: Optional[str] = Field(default=None, max_length=500, description="SMS service URL")
    sms_username: Optional[str] = Field(default=None, max_length=255, description="SMS username")
    sms_password: Optional[str] = Field(default=None, max_length=255, description="SMS password")
    webhook_url: Optional[str] = Field(default=None, max_length=500, description="Webhook URL")
    webhook_headers: Optional[Dict[str, str]] = Field(default_factory=dict, description="Webhook headers")


class NotificationConfigCreate(NotificationConfigBase):
    """Schema for creating notification configuration."""
    pass


class NotificationConfigUpdate(BaseModel):
    """Schema for updating notification configuration."""
    type: Optional[NotificationType] = None
    enabled: Optional[bool] = None
    smtp_host: Optional[str] = Field(None, max_length=255)
    smtp_port: Optional[int] = Field(None, ge=1, le=65535)
    smtp_username: Optional[str] = Field(None, max_length=255)
    smtp_password: Optional[str] = Field(None, max_length=255)
    smtp_encryption: Optional[str] = Field(None, max_length=20)
    smtp_from: Optional[str] = Field(None, max_length=255)
    sms_url: Optional[str] = Field(None, max_length=500)
    sms_username: Optional[str] = Field(None, max_length=255)
    sms_password: Optional[str] = Field(None, max_length=255)
    webhook_url: Optional[str] = Field(None, max_length=500)
    webhook_headers: Optional[Dict[str, str]] = None


class NotificationConfigResponse(NotificationConfigBase):
    """Schema for notification configuration response."""
    id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class WebServerConfigBase(BaseModel):
    """Base web server configuration schema."""
    port: int = Field(default=8000, ge=1, le=65535, description="Web server port")
    host: str = Field(default="0.0.0.0", max_length=255, description="Web server host")
    ssl_enabled: bool = Field(default=False, description="Enable SSL")
    ssl_cert: Optional[str] = Field(default=None, max_length=500, description="SSL certificate path")
    ssl_key: Optional[str] = Field(default=None, max_length=500, description="SSL key path")
    cors_origins: List[str] = Field(default_factory=list, description="CORS allowed origins")
    cors_methods: List[str] = Field(default_factory=lambda: ["GET", "POST", "PUT", "DELETE"], description="CORS allowed methods")
    cors_headers: List[str] = Field(default_factory=lambda: ["*"], description="CORS allowed headers")
    max_request_size: int = Field(default=10485760, ge=1024, description="Max request size in bytes")
    request_timeout: int = Field(default=30, ge=1, le=300, description="Request timeout in seconds")


class WebServerConfigCreate(WebServerConfigBase):
    """Schema for creating web server configuration."""
    pass


class WebServerConfigUpdate(BaseModel):
    """Schema for updating web server configuration."""
    port: Optional[int] = Field(None, ge=1, le=65535)
    host: Optional[str] = Field(None, max_length=255)
    ssl_enabled: Optional[bool] = None
    ssl_cert: Optional[str] = Field(None, max_length=500)
    ssl_key: Optional[str] = Field(None, max_length=500)
    cors_origins: Optional[List[str]] = None
    cors_methods: Optional[List[str]] = None
    cors_headers: Optional[List[str]] = None
    max_request_size: Optional[int] = Field(None, ge=1024)
    request_timeout: Optional[int] = Field(None, ge=1, le=300)


class WebServerConfigResponse(WebServerConfigBase):
    """Schema for web server configuration response."""
    id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class ServerStatsResponse(BaseModel):
    """Schema for server statistics response."""
    total_users: int
    total_devices: int
    total_positions: int
    total_events: int
    total_geofences: int
    online_devices: int
    offline_devices: int
    server_uptime: int
    memory_usage: float
    cpu_usage: float
    disk_usage: float


class ServerHealthResponse(BaseModel):
    """Schema for server health response."""
    status: str
    timestamp: datetime
    version: str
    database_status: str
    redis_status: Optional[str] = None
    uptime: int
    memory_usage: float
    cpu_usage: float


class ServerInfoResponse(BaseModel):
    """Schema for server information response."""
    name: str
    version: str
    build_time: Optional[datetime] = None
    java_version: Optional[str] = None
    os_name: Optional[str] = None
    os_version: Optional[str] = None
    os_arch: Optional[str] = None
    memory_total: Optional[int] = None
    memory_used: Optional[int] = None
    cpu_count: Optional[int] = None
    timezone: str
    language: str
    distance_unit: str
    speed_unit: str
    volume_unit: str


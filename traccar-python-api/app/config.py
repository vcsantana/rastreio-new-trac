"""
Application configuration settings
"""
from typing import List, Optional
from pydantic_settings import BaseSettings
from pydantic import Field


class Settings(BaseSettings):
    """Application settings"""
    
    # Application
    VERSION: str = "1.0.0"
    DEBUG: bool = Field(default=False, env="DEBUG")
    HOST: str = Field(default="0.0.0.0", env="HOST")
    PORT: int = Field(default=8000, env="PORT")
    ENABLE_DOCS: bool = Field(default=True, env="ENABLE_DOCS")
    
    # Security
    SECRET_KEY: str = Field(env="SECRET_KEY")
    ACCESS_TOKEN_EXPIRE_MINUTES: int = Field(default=30, env="ACCESS_TOKEN_EXPIRE_MINUTES")
    REFRESH_TOKEN_EXPIRE_DAYS: int = Field(default=7, env="REFRESH_TOKEN_EXPIRE_DAYS")
    ALGORITHM: str = "HS256"
    
    # CORS
    ALLOWED_HOSTS: List[str] = Field(default=["*"], env="ALLOWED_HOSTS")
    
    # Database
    DATABASE_URL: str = Field(env="DATABASE_URL")
    DATABASE_ECHO: bool = Field(default=False, env="DATABASE_ECHO")
    
    # Redis
    REDIS_URL: str = Field(default="redis://localhost:6379/0", env="REDIS_URL")
    
    # Celery
    CELERY_BROKER_URL: str = Field(default="redis://localhost:6379/1", env="CELERY_BROKER_URL")
    CELERY_RESULT_BACKEND: str = Field(default="redis://localhost:6379/1", env="CELERY_RESULT_BACKEND")
    
    # Protocol Servers
    PROTOCOL_SERVERS: dict = Field(default={
        "suntech": {
            "enabled": True,
            "port": 5001,
            "protocol": "tcp"
        },
        "gt06": {
            "enabled": True,
            "port": 5002,
            "protocol": "tcp"
        },
        "h02": {
            "enabled": True,
            "port": 5003,
            "protocol": "tcp"
        }
    })
    
    # Logging
    LOG_LEVEL: str = Field(default="INFO", env="LOG_LEVEL")
    
    # File Storage
    MEDIA_PATH: Optional[str] = Field(default=None, env="MEDIA_PATH")
    
    # Geofencing
    DEFAULT_GEOFENCE_BUFFER: float = Field(default=100.0, env="DEFAULT_GEOFENCE_BUFFER")
    
    # Position processing
    POSITION_BATCH_SIZE: int = Field(default=100, env="POSITION_BATCH_SIZE")
    POSITION_BATCH_TIMEOUT: int = Field(default=5, env="POSITION_BATCH_TIMEOUT")
    
    # WebSocket
    WEBSOCKET_HEARTBEAT_INTERVAL: int = Field(default=30, env="WEBSOCKET_HEARTBEAT_INTERVAL")
    
    class Config:
        env_file = ".env"
        case_sensitive = True


# Global settings instance
settings = Settings()

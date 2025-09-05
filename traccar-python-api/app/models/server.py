"""
Server model for system configuration
"""
from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime, Text, Boolean, Float
from sqlalchemy.sql import func
from app.database import Base


class Server(Base):
    """
    Server model representing system configuration.
    Migrated from org.traccar.model.Server
    """
    __tablename__ = "servers"

    # Primary key
    id = Column(Integer, primary_key=True, index=True)
    
    # Server identification
    name = Column(String(255), nullable=False, default="Traccar Server")
    registration = Column(Boolean, default=True)
    readonly = Column(Boolean, default=False)
    
    # Network configuration
    map_url = Column(String(512), nullable=True)
    bing_key = Column(String(255), nullable=True)
    mapbox_key = Column(String(255), nullable=True)
    
    # Timezone and locale
    timezone = Column(String(50), default="UTC")
    language = Column(String(10), default="en")
    
    # Distance and speed units
    distance_unit = Column(String(10), default="km")
    speed_unit = Column(String(10), default="kmh")
    
    # Coordinate format
    coordinate_format = Column(String(20), default="decimal")
    
    # Device settings
    device_readonly = Column(Boolean, default=False)
    limit_commands = Column(Boolean, default=False)
    
    # Notification settings
    email_enabled = Column(Boolean, default=False)
    smtp_host = Column(String(255), nullable=True)
    smtp_port = Column(Integer, default=587)
    smtp_username = Column(String(255), nullable=True)
    smtp_password = Column(String(255), nullable=True)
    smtp_encryption = Column(String(20), default="tls")
    smtp_from = Column(String(255), nullable=True)
    
    # SMS settings
    sms_enabled = Column(Boolean, default=False)
    sms_gateway = Column(String(255), nullable=True)
    sms_username = Column(String(255), nullable=True)
    sms_password = Column(String(255), nullable=True)
    
    # Web settings
    web_enabled = Column(Boolean, default=True)
    web_port = Column(Integer, default=8082)
    web_https = Column(Boolean, default=False)
    web_certificate = Column(Text, nullable=True)
    web_private_key = Column(Text, nullable=True)
    
    # Database settings
    database_check_interval = Column(Integer, default=600)
    database_cleanup_interval = Column(Integer, default=24)
    
    # Protocol settings
    protocol_timeout = Column(Integer, default=300)
    protocol_heartbeat_interval = Column(Integer, default=300)
    
    # Additional configuration
    attributes = Column(Text, nullable=True)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    def __init__(self, **kwargs):
        """Initialize Server with default values"""
        super().__init__(**kwargs)
        self.name = kwargs.get('name', 'Traccar Server')
        self.registration = kwargs.get('registration', True)
        self.readonly = kwargs.get('readonly', False)
        self.timezone = kwargs.get('timezone', 'UTC')
        self.language = kwargs.get('language', 'en')
        self.distance_unit = kwargs.get('distance_unit', 'km')
        self.speed_unit = kwargs.get('speed_unit', 'kmh')
        self.coordinate_format = kwargs.get('coordinate_format', 'decimal')

    def is_registration_enabled(self) -> bool:
        """Check if device registration is enabled"""
        return self.registration

    def is_readonly(self) -> bool:
        """Check if server is in read-only mode"""
        return self.readonly

    def is_email_enabled(self) -> bool:
        """Check if email notifications are enabled"""
        return self.email_enabled and bool(self.smtp_host)

    def is_sms_enabled(self) -> bool:
        """Check if SMS notifications are enabled"""
        return self.sms_enabled and bool(self.sms_gateway)

    def is_web_enabled(self) -> bool:
        """Check if web interface is enabled"""
        return self.web_enabled

    def get_map_provider(self) -> str:
        """Get the configured map provider"""
        if self.bing_key:
            return "bing"
        elif self.mapbox_key:
            return "mapbox"
        else:
            return "openstreetmap"

    def get_smtp_config(self) -> dict:
        """Get SMTP configuration"""
        return {
            "host": self.smtp_host,
            "port": self.smtp_port,
            "username": self.smtp_username,
            "password": self.smtp_password,
            "encryption": self.smtp_encryption,
            "from": self.smtp_from
        }

    def get_sms_config(self) -> dict:
        """Get SMS configuration"""
        return {
            "gateway": self.sms_gateway,
            "username": self.sms_username,
            "password": self.sms_password
        }

    def __repr__(self):
        return f"<Server(id={self.id}, name='{self.name}', readonly={self.readonly})>"


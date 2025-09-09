"""
User model
"""
from sqlalchemy import Column, Integer, String, Boolean, DateTime, Text, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from datetime import datetime
from typing import Optional
from app.database import Base

class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(255), unique=True, index=True, nullable=False)
    name = Column(String(255), nullable=False)
    login = Column(String(255), unique=True, index=True, nullable=True)  # Login único (diferente do email)
    password_hash = Column(String(255), nullable=False)
    salt = Column(String(255), nullable=True)  # Salt para hash de senhas
    is_active = Column(Boolean, default=True)
    is_admin = Column(Boolean, default=False)
    readonly = Column(Boolean, default=False)  # Usuário somente leitura
    temporary = Column(Boolean, default=False)  # Usuário temporário
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # User attributes (JSON field for flexibility)
    attributes = Column(Text)  # JSON string for additional attributes
    
    # Additional user settings
    phone = Column(String(20))
    map = Column(String(128))
    latitude = Column(String(20), default="0")
    longitude = Column(String(20), default="0")
    zoom = Column(Integer, default=0)
    coordinate_format = Column(String(128))
    expiration_time = Column(DateTime(timezone=True))
    device_limit = Column(Integer, default=-1)  # -1 = unlimited
    user_limit = Column(Integer, default=0)  # 0 = no management rights
    device_readonly = Column(Boolean, default=False)
    limit_commands = Column(Boolean, default=False)
    disable_reports = Column(Boolean, default=False)
    fixed_email = Column(Boolean, default=False)
    poi_layer = Column(String(512))
    
    # 2FA (Two-Factor Authentication)
    totp_key = Column(String(255), nullable=True)  # Chave TOTP para Google Authenticator
    totp_enabled = Column(Boolean, default=False)  # Status do 2FA
    
    # Relationships
    reports = relationship("Report", back_populates="user", cascade="all, delete-orphan")
    report_templates = relationship("ReportTemplate", back_populates="user", cascade="all, delete-orphan")
    calendars = relationship("Calendar", back_populates="user", cascade="all, delete-orphan")
    commands = relationship("Command", back_populates="user", cascade="all, delete-orphan")
    command_templates = relationship("CommandTemplate", back_populates="user", cascade="all, delete-orphan")
    scheduled_commands = relationship("ScheduledCommand", back_populates="user", cascade="all, delete-orphan")
    
    # Permission relationships (many-to-many)
    device_permissions = relationship(
        "Device", 
        secondary="user_device_permissions", 
        back_populates="user_permissions"
    )
    group_permissions = relationship(
        "Group", 
        secondary="user_group_permissions", 
        back_populates="user_permissions"
    )
    managed_users = relationship(
        "User",
        secondary="user_managed_users",
        primaryjoin="User.id == user_managed_users.c.user_id",
        secondaryjoin="User.id == user_managed_users.c.managed_user_id",
        back_populates="managers"
    )
    managers = relationship(
        "User",
        secondary="user_managed_users",
        primaryjoin="User.id == user_managed_users.c.managed_user_id",
        secondaryjoin="User.id == user_managed_users.c.user_id",
        back_populates="managed_users"
    )
    notifications = relationship("Notification", back_populates="user")
    
    # Methods for dynamic attributes
    def get_string_attribute(self, key: str, default: str = None) -> str:
        """Get string attribute from JSON attributes field"""
        if not self.attributes:
            return default
        try:
            import json
            attrs = json.loads(self.attributes)
            return attrs.get(key, default)
        except (json.JSONDecodeError, TypeError):
            return default
    
    def get_double_attribute(self, key: str, default: float = None) -> float:
        """Get double/float attribute from JSON attributes field"""
        if not self.attributes:
            return default
        try:
            import json
            attrs = json.loads(self.attributes)
            value = attrs.get(key, default)
            return float(value) if value is not None else default
        except (json.JSONDecodeError, TypeError, ValueError):
            return default
    
    def get_boolean_attribute(self, key: str, default: bool = False) -> bool:
        """Get boolean attribute from JSON attributes field"""
        if not self.attributes:
            return default
        try:
            import json
            attrs = json.loads(self.attributes)
            value = attrs.get(key, default)
            return bool(value) if value is not None else default
        except (json.JSONDecodeError, TypeError):
            return default
    
    def get_integer_attribute(self, key: str, default: int = None) -> int:
        """Get integer attribute from JSON attributes field"""
        if not self.attributes:
            return default
        try:
            import json
            attrs = json.loads(self.attributes)
            value = attrs.get(key, default)
            return int(value) if value is not None else default
        except (json.JSONDecodeError, TypeError, ValueError):
            return default
    
    def set_attribute(self, key: str, value) -> None:
        """Set attribute in JSON attributes field"""
        import json
        if not self.attributes:
            attrs = {}
        else:
            try:
                attrs = json.loads(self.attributes)
            except json.JSONDecodeError:
                attrs = {}
        
        attrs[key] = value
        self.attributes = json.dumps(attrs)
    
    def check_disabled(self) -> bool:
        """Check if user is disabled (inactive or expired)"""
        if not self.is_active:
            return True
        if self.expiration_time and datetime.now() > self.expiration_time:
            return True
        return False
    
    def get_manager(self) -> Optional['User']:
        """Get the manager of this user based on user_limit"""
        # This would need to be implemented with a proper query
        # For now, return None as it requires complex logic
        return None
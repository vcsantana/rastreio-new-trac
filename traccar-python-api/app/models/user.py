"""
User model
"""
from sqlalchemy import Column, Integer, String, Boolean, DateTime, Text, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database import Base

class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(255), unique=True, index=True, nullable=False)
    name = Column(String(255), nullable=False)
    password_hash = Column(String(255), nullable=False)
    is_active = Column(Boolean, default=True)
    is_admin = Column(Boolean, default=False)
    
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
    
    # Relationships
    reports = relationship("Report", back_populates="user", cascade="all, delete-orphan")
    report_templates = relationship("ReportTemplate", back_populates="user", cascade="all, delete-orphan")
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
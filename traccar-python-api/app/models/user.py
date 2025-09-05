"""
User model
"""
from sqlalchemy import Column, Integer, String, Boolean, DateTime, Text
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
    
    # Relationships
    reports = relationship("Report", back_populates="user", cascade="all, delete-orphan")
    report_templates = relationship("ReportTemplate", back_populates="user", cascade="all, delete-orphan")
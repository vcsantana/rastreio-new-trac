"""
Report models for SQLAlchemy.
"""

from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime, Boolean, Text, ForeignKey, JSON, Float
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.database import Base


class Report(Base):
    """Report model."""
    __tablename__ = "reports"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    name = Column(String(100), nullable=False)
    description = Column(Text)
    report_type = Column(String(50), nullable=False, index=True)
    format = Column(String(10), nullable=False, default="json")
    period = Column(String(20), nullable=False, default="today")
    from_date = Column(DateTime)
    to_date = Column(DateTime)
    device_ids = Column(JSON)  # List of device IDs
    group_ids = Column(JSON)   # List of group IDs
    include_attributes = Column(Boolean, default=True)
    include_addresses = Column(Boolean, default=True)
    include_events = Column(Boolean, default=True)
    include_geofences = Column(Boolean, default=True)
    parameters = Column(JSON, default=dict)
    status = Column(String(20), default="pending", index=True)  # pending, processing, completed, failed
    file_path = Column(String(500))
    file_size = Column(Integer)
    error_message = Column(Text)
    created_at = Column(DateTime, default=func.now(), nullable=False)
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now(), nullable=False)
    completed_at = Column(DateTime)
    
    # Relationships
    user = relationship("User", back_populates="reports")


class ReportTemplate(Base):
    """Report template model."""
    __tablename__ = "report_templates"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    name = Column(String(100), nullable=False)
    description = Column(Text)
    report_type = Column(String(50), nullable=False, index=True)
    format = Column(String(10), nullable=False, default="json")
    parameters = Column(JSON, default=dict)
    is_public = Column(Boolean, default=False, index=True)
    is_default = Column(Boolean, default=False, index=True)
    created_at = Column(DateTime, default=func.now(), nullable=False)
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now(), nullable=False)
    
    # Relationships
    user = relationship("User", back_populates="report_templates")


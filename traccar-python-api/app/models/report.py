"""
Report models for SQLAlchemy.
"""

from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime, Boolean, Text, ForeignKey, JSON, Float
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.database import Base


class Calendar(Base):
    """Calendar model for report scheduling."""
    __tablename__ = "calendars"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    name = Column(String(100), nullable=False)
    description = Column(Text)
    data = Column(Text)  # iCalendar data
    attributes = Column(JSON, default=dict)
    created_at = Column(DateTime, default=func.now(), nullable=False)
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now(), nullable=False)
    
    # Relationships
    user = relationship("User", back_populates="calendars")
    reports = relationship("Report", back_populates="calendar")


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
    attributes = Column(JSON, default=dict)  # Dynamic attributes like Java ExtendedModel
    status = Column(String(20), default="pending", index=True)  # pending, processing, completed, failed
    file_path = Column(String(500))
    file_size = Column(Integer)
    error_message = Column(Text)
    
    # Scheduling fields
    is_scheduled = Column(Boolean, default=False, index=True)
    schedule_cron = Column(String(100))  # Cron expression for scheduling
    calendar_id = Column(Integer, ForeignKey("calendars.id"), nullable=True)  # Calendar integration
    next_run = Column(DateTime, index=True)  # Next scheduled run
    last_run = Column(DateTime)  # Last execution time
    email_recipients = Column(JSON)  # List of email addresses for automatic sending
    
    created_at = Column(DateTime, default=func.now(), nullable=False)
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now(), nullable=False)
    completed_at = Column(DateTime)
    
    # Relationships
    user = relationship("User", back_populates="reports")
    calendar = relationship("Calendar", back_populates="reports")
    
    def get_string_attribute(self, key: str, default: str = None) -> str:
        """Get string attribute from dynamic attributes."""
        if not self.attributes:
            return default
        return self.attributes.get(key, default)
    
    def get_double_attribute(self, key: str, default: float = None) -> float:
        """Get double attribute from dynamic attributes."""
        if not self.attributes:
            return default
        value = self.attributes.get(key, default)
        try:
            return float(value) if value is not None else default
        except (ValueError, TypeError):
            return default
    
    def get_boolean_attribute(self, key: str, default: bool = None) -> bool:
        """Get boolean attribute from dynamic attributes."""
        if not self.attributes:
            return default
        value = self.attributes.get(key, default)
        if isinstance(value, bool):
            return value
        if isinstance(value, str):
            return value.lower() in ('true', '1', 'yes', 'on')
        return bool(value) if value is not None else default
    
    def get_integer_attribute(self, key: str, default: int = None) -> int:
        """Get integer attribute from dynamic attributes."""
        if not self.attributes:
            return default
        value = self.attributes.get(key, default)
        try:
            return int(value) if value is not None else default
        except (ValueError, TypeError):
            return default
    
    def set_attribute(self, key: str, value):
        """Set attribute in dynamic attributes."""
        if not self.attributes:
            self.attributes = {}
        self.attributes[key] = value
    
    def has_attribute(self, key: str) -> bool:
        """Check if attribute exists in dynamic attributes."""
        return self.attributes and key in self.attributes


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


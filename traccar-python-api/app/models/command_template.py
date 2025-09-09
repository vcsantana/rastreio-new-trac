"""
Command template model for reusable command definitions.
"""

from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from sqlalchemy import Column, Integer, String, DateTime, Text, Boolean, ForeignKey, JSON
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.database import Base
from app.models.command import CommandType, CommandPriority


class CommandTemplate(Base):
    """
    Command template model for reusable command definitions.
    
    Allows users to save frequently used commands as templates for quick reuse.
    """
    __tablename__ = "command_templates"
    
    id = Column(Integer, primary_key=True, index=True)
    
    # Template details
    name = Column(String(255), nullable=False, index=True)
    description = Column(Text, nullable=True)
    
    # Command configuration
    command_type = Column(String(50), nullable=False, index=True)
    priority = Column(String(20), default=CommandPriority.NORMAL, nullable=False)
    parameters = Column(JSON, nullable=True)  # Command-specific parameters
    attributes = Column(JSON, nullable=True)  # Dynamic attributes
    text_channel = Column(Boolean, default=False, nullable=False)
    max_retries = Column(Integer, default=3, nullable=False)
    
    # Template metadata
    is_public = Column(Boolean, default=False, nullable=False)  # Public templates for all users
    is_active = Column(Boolean, default=True, nullable=False, index=True)
    usage_count = Column(Integer, default=0, nullable=False)  # Track template usage
    
    # User relationship
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    user = relationship("User", back_populates="command_templates")
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    last_used_at = Column(DateTime(timezone=True), nullable=True)
    
    def __repr__(self):
        return f"<CommandTemplate(id={self.id}, name={self.name}, type={self.command_type})>"
    
    def increment_usage(self) -> None:
        """Increment usage count and update last used timestamp."""
        self.usage_count += 1
        self.last_used_at = datetime.utcnow()
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert template to dictionary."""
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "command_type": self.command_type,
            "priority": self.priority,
            "parameters": self.parameters,
            "attributes": self.attributes,
            "text_channel": self.text_channel,
            "max_retries": self.max_retries,
            "is_public": self.is_public,
            "is_active": self.is_active,
            "usage_count": self.usage_count,
            "user_id": self.user_id,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "last_used_at": self.last_used_at.isoformat() if self.last_used_at else None
        }


class ScheduledCommand(Base):
    """
    Scheduled command model for delayed command execution.
    
    Allows users to schedule commands for future execution.
    """
    __tablename__ = "scheduled_commands"
    
    id = Column(Integer, primary_key=True, index=True)
    
    # Command relationship
    command_id = Column(Integer, ForeignKey("commands.id"), nullable=False, unique=True, index=True)
    command = relationship("Command", backref="scheduled_entry")
    
    # Scheduling details
    scheduled_at = Column(DateTime(timezone=True), nullable=False, index=True)
    is_executed = Column(Boolean, default=False, nullable=False, index=True)
    executed_at = Column(DateTime(timezone=True), nullable=True)
    
    # Scheduling metadata
    repeat_interval = Column(Integer, nullable=True)  # Repeat interval in seconds (None for one-time)
    repeat_count = Column(Integer, default=0, nullable=False)  # Number of times executed
    max_repeats = Column(Integer, nullable=True)  # Maximum number of repeats (None for infinite)
    is_active = Column(Boolean, default=True, nullable=False, index=True)
    
    # User relationship
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    user = relationship("User", back_populates="scheduled_commands")
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    
    def __repr__(self):
        return f"<ScheduledCommand(id={self.id}, command_id={self.command_id}, scheduled_at={self.scheduled_at})>"
    
    @property
    def is_ready_for_execution(self) -> bool:
        """Check if scheduled command is ready for execution."""
        if not self.is_active or self.is_executed:
            return False
        
        if self.max_repeats and self.repeat_count >= self.max_repeats:
            return False
        
        return datetime.utcnow() >= self.scheduled_at
    
    @property
    def can_repeat(self) -> bool:
        """Check if command can be repeated."""
        if not self.repeat_interval:
            return False
        
        if self.max_repeats and self.repeat_count >= self.max_repeats:
            return False
        
        return True
    
    def mark_executed(self) -> None:
        """Mark command as executed and update repeat count."""
        self.is_executed = True
        self.executed_at = datetime.utcnow()
        self.repeat_count += 1
    
    def schedule_next_repeat(self) -> None:
        """Schedule next repeat if applicable."""
        if self.can_repeat:
            self.scheduled_at = datetime.utcnow() + timedelta(seconds=self.repeat_interval)
            self.is_executed = False
            self.executed_at = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert scheduled command to dictionary."""
        return {
            "id": self.id,
            "command_id": self.command_id,
            "scheduled_at": self.scheduled_at.isoformat(),
            "is_executed": self.is_executed,
            "executed_at": self.executed_at.isoformat() if self.executed_at else None,
            "repeat_interval": self.repeat_interval,
            "repeat_count": self.repeat_count,
            "max_repeats": self.max_repeats,
            "is_active": self.is_active,
            "user_id": self.user_id,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "is_ready_for_execution": self.is_ready_for_execution,
            "can_repeat": self.can_repeat
        }

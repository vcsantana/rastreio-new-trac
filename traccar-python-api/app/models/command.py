"""
Command model for device command management.
"""

from datetime import datetime
from enum import Enum
from typing import Optional, Dict, Any
from sqlalchemy import Column, Integer, String, DateTime, Text, Boolean, ForeignKey, JSON
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.database import Base


class CommandType(str, Enum):
    """Command types supported by the system."""
    
    # Suntech Commands
    REBOOT = "REBOOT"
    SETTIME = "SETTIME"
    SETINTERVAL = "SETINTERVAL"
    SETOVERSPEED = "SETOVERSPEED"
    SETGEOFENCE = "SETGEOFENCE"
    SETOUTPUT = "SETOUTPUT"
    SETINPUT = "SETINPUT"
    SETACCELERATION = "SETACCELERATION"
    SETDECELERATION = "SETDECELERATION"
    SETTURN = "SETTURN"
    SETIDLE = "SETIDLE"
    SETPARKING = "SETPARKING"
    SETMOVEMENT = "SETMOVEMENT"
    SETVIBRATION = "SETVIBRATION"
    SETDOOR = "SETDOOR"
    SETPOWER = "SETPOWER"
    
    # OsmAnd Commands
    SET_INTERVAL = "SET_INTERVAL"
    SET_ACCURACY = "SET_ACCURACY"
    SET_BATTERY_SAVER = "SET_BATTERY_SAVER"
    SET_ALARM = "SET_ALARM"
    SET_GEOFENCE = "SET_GEOFENCE"
    SET_SPEED_LIMIT = "SET_SPEED_LIMIT"
    SET_ENGINE_STOP = "SET_ENGINE_STOP"
    SET_ENGINE_START = "SET_ENGINE_START"
    
    # Generic Commands
    CUSTOM = "CUSTOM"
    PING = "PING"
    STATUS = "STATUS"
    CONFIG = "CONFIG"


class CommandStatus(str, Enum):
    """Command execution status."""
    PENDING = "PENDING"           # Command queued, waiting to be sent
    SENT = "SENT"                 # Command sent to device
    DELIVERED = "DELIVERED"       # Command delivered to device
    EXECUTED = "EXECUTED"         # Command executed successfully
    FAILED = "FAILED"             # Command failed to execute
    TIMEOUT = "TIMEOUT"           # Command timed out
    CANCELLED = "CANCELLED"       # Command cancelled by user
    EXPIRED = "EXPIRED"           # Command expired before execution


class CommandPriority(str, Enum):
    """Command priority levels."""
    LOW = "LOW"
    NORMAL = "NORMAL"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


class Command(Base):
    """
    Command model for device command management.
    
    Represents a command sent to a device with tracking of its execution status.
    """
    __tablename__ = "commands"
    
    id = Column(Integer, primary_key=True, index=True)
    
    # Device relationship
    device_id = Column(Integer, ForeignKey("devices.id"), nullable=False, index=True)
    device = relationship("Device", back_populates="commands")
    
    # User who sent the command
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    user = relationship("User", back_populates="commands")
    
    # Command details
    command_type = Column(String(50), nullable=False, index=True)
    priority = Column(String(20), default=CommandPriority.NORMAL, nullable=False)
    status = Column(String(20), default=CommandStatus.PENDING, nullable=False, index=True)
    
    # Command parameters
    parameters = Column(JSON, nullable=True)  # Command-specific parameters
    raw_command = Column(Text, nullable=True)  # Raw command string for protocols
    
    # Execution tracking
    sent_at = Column(DateTime(timezone=True), nullable=True)
    delivered_at = Column(DateTime(timezone=True), nullable=True)
    executed_at = Column(DateTime(timezone=True), nullable=True)
    failed_at = Column(DateTime(timezone=True), nullable=True)
    
    # Response and error handling
    response = Column(Text, nullable=True)  # Device response
    error_message = Column(Text, nullable=True)  # Error details if failed
    
    # Retry mechanism
    retry_count = Column(Integer, default=0, nullable=False)
    max_retries = Column(Integer, default=3, nullable=False)
    
    # Expiration
    expires_at = Column(DateTime(timezone=True), nullable=True)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    
    def __repr__(self):
        return f"<Command(id={self.id}, device_id={self.device_id}, type={self.command_type}, status={self.status})>"
    
    @property
    def is_expired(self) -> bool:
        """Check if command has expired."""
        if not self.expires_at:
            return False
        return datetime.utcnow() > self.expires_at
    
    @property
    def can_retry(self) -> bool:
        """Check if command can be retried."""
        return (
            self.status in [CommandStatus.FAILED, CommandStatus.TIMEOUT] and
            self.retry_count < self.max_retries and
            not self.is_expired
        )
    
    @property
    def is_final_status(self) -> bool:
        """Check if command has reached a final status."""
        return self.status in [
            CommandStatus.EXECUTED,
            CommandStatus.FAILED,
            CommandStatus.TIMEOUT,
            CommandStatus.CANCELLED,
            CommandStatus.EXPIRED
        ]
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert command to dictionary."""
        return {
            "id": self.id,
            "device_id": self.device_id,
            "user_id": self.user_id,
            "command_type": self.command_type,
            "priority": self.priority,
            "status": self.status,
            "parameters": self.parameters,
            "raw_command": self.raw_command,
            "sent_at": self.sent_at.isoformat() if self.sent_at else None,
            "delivered_at": self.delivered_at.isoformat() if self.delivered_at else None,
            "executed_at": self.executed_at.isoformat() if self.executed_at else None,
            "failed_at": self.failed_at.isoformat() if self.failed_at else None,
            "response": self.response,
            "error_message": self.error_message,
            "retry_count": self.retry_count,
            "max_retries": self.max_retries,
            "expires_at": self.expires_at.isoformat() if self.expires_at else None,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "is_expired": self.is_expired,
            "can_retry": self.can_retry,
            "is_final_status": self.is_final_status
        }


class CommandQueue(Base):
    """
    Command queue for managing command execution order.
    
    Provides priority-based queuing and execution management.
    """
    __tablename__ = "command_queue"
    
    id = Column(Integer, primary_key=True, index=True)
    
    # Command relationship
    command_id = Column(Integer, ForeignKey("commands.id"), nullable=False, unique=True, index=True)
    command = relationship("Command", backref="queue_entry")
    
    # Queue management
    priority = Column(String(20), nullable=False, index=True)
    scheduled_at = Column(DateTime(timezone=True), nullable=True, index=True)
    queued_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False, index=True)
    
    # Execution tracking
    attempts = Column(Integer, default=0, nullable=False)
    last_attempt_at = Column(DateTime(timezone=True), nullable=True)
    next_attempt_at = Column(DateTime(timezone=True), nullable=True)
    
    # Status
    is_active = Column(Boolean, default=True, nullable=False, index=True)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    
    def __repr__(self):
        return f"<CommandQueue(id={self.id}, command_id={self.command_id}, priority={self.priority})>"
    
    @property
    def is_ready_for_execution(self) -> bool:
        """Check if command is ready for execution."""
        if not self.is_active:
            return False
        
        if self.scheduled_at and datetime.utcnow() < self.scheduled_at:
            return False
        
        if self.next_attempt_at and datetime.utcnow() < self.next_attempt_at:
            return False
        
        return True
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert queue entry to dictionary."""
        return {
            "id": self.id,
            "command_id": self.command_id,
            "priority": self.priority,
            "scheduled_at": self.scheduled_at.isoformat() if self.scheduled_at else None,
            "queued_at": self.queued_at.isoformat(),
            "attempts": self.attempts,
            "last_attempt_at": self.last_attempt_at.isoformat() if self.last_attempt_at else None,
            "next_attempt_at": self.next_attempt_at.isoformat() if self.next_attempt_at else None,
            "is_active": self.is_active,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "is_ready_for_execution": self.is_ready_for_execution
        }

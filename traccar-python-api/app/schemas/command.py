"""
Command schemas for API validation and serialization.
"""

from datetime import datetime
from typing import Optional, Dict, Any, List
from pydantic import BaseModel, Field, validator
from enum import Enum

from app.models.command import CommandType, CommandStatus, CommandPriority


class CommandCreate(BaseModel):
    """Schema for creating a new command."""
    
    device_id: int = Field(..., description="ID of the target device")
    command_type: CommandType = Field(..., description="Type of command to send")
    priority: CommandPriority = Field(CommandPriority.NORMAL, description="Command priority")
    parameters: Optional[Dict[str, Any]] = Field(None, description="Command-specific parameters")
    expires_at: Optional[datetime] = Field(None, description="Command expiration time")
    max_retries: int = Field(3, ge=0, le=10, description="Maximum number of retries")
    
    @validator('parameters')
    def validate_parameters(cls, v, values):
        """Validate command parameters based on command type."""
        if 'command_type' not in values:
            return v
        
        command_type = values['command_type']
        
        # Validate parameters for specific command types
        if command_type == CommandType.SETINTERVAL and v:
            if 'interval' not in v:
                raise ValueError("SETINTERVAL command requires 'interval' parameter")
            if not isinstance(v['interval'], int) or v['interval'] < 10:
                raise ValueError("Interval must be an integer >= 10 seconds")
        
        elif command_type == CommandType.SETOVERSPEED and v:
            if 'speed_limit' not in v:
                raise ValueError("SETOVERSPEED command requires 'speed_limit' parameter")
            if not isinstance(v['speed_limit'], (int, float)) or v['speed_limit'] <= 0:
                raise ValueError("Speed limit must be a positive number")
        
        elif command_type == CommandType.SETGEOFENCE and v:
            required_fields = ['latitude', 'longitude', 'radius']
            for field in required_fields:
                if field not in v:
                    raise ValueError(f"SETGEOFENCE command requires '{field}' parameter")
            if not isinstance(v['radius'], (int, float)) or v['radius'] <= 0:
                raise ValueError("Radius must be a positive number")
        
        return v


class CommandUpdate(BaseModel):
    """Schema for updating a command."""
    
    status: Optional[CommandStatus] = Field(None, description="Command status")
    response: Optional[str] = Field(None, description="Device response")
    error_message: Optional[str] = Field(None, description="Error message if failed")
    retry_count: Optional[int] = Field(None, ge=0, description="Number of retries attempted")


class CommandResponse(BaseModel):
    """Schema for command response."""
    
    id: int
    device_id: int
    user_id: int
    command_type: CommandType
    priority: CommandPriority
    status: CommandStatus
    parameters: Optional[Dict[str, Any]]
    raw_command: Optional[str]
    sent_at: Optional[datetime]
    delivered_at: Optional[datetime]
    executed_at: Optional[datetime]
    failed_at: Optional[datetime]
    response: Optional[str]
    error_message: Optional[str]
    retry_count: int
    max_retries: int
    expires_at: Optional[datetime]
    created_at: datetime
    updated_at: datetime
    is_expired: bool
    can_retry: bool
    is_final_status: bool
    
    # Device information
    device_name: Optional[str] = None
    device_unique_id: Optional[str] = None
    
    # User information
    user_name: Optional[str] = None
    user_email: Optional[str] = None
    
    class Config:
        from_attributes = True


class CommandListResponse(BaseModel):
    """Schema for command list response."""
    
    commands: List[CommandResponse]
    total: int
    page: int
    size: int
    pages: int


class CommandQueueResponse(BaseModel):
    """Schema for command queue response."""
    
    id: int
    command_id: int
    priority: CommandPriority
    scheduled_at: Optional[datetime]
    queued_at: datetime
    attempts: int
    last_attempt_at: Optional[datetime]
    next_attempt_at: Optional[datetime]
    is_active: bool
    created_at: datetime
    updated_at: datetime
    is_ready_for_execution: bool
    
    # Command details
    command: Optional[CommandResponse] = None
    
    class Config:
        from_attributes = True


class CommandQueueListResponse(BaseModel):
    """Schema for command queue list response."""
    
    queue: List[CommandQueueResponse]
    total: int
    page: int
    size: int
    pages: int


class CommandStatsResponse(BaseModel):
    """Schema for command statistics response."""
    
    total_commands: int
    pending_commands: int
    sent_commands: int
    executed_commands: int
    failed_commands: int
    cancelled_commands: int
    expired_commands: int
    
    # By priority
    low_priority: int
    normal_priority: int
    high_priority: int
    critical_priority: int
    
    # By command type
    command_type_stats: Dict[str, int]
    
    # By device
    device_stats: Dict[str, int]
    
    # Recent activity
    commands_last_hour: int
    commands_last_day: int
    commands_last_week: int


class CommandBulkCreate(BaseModel):
    """Schema for creating multiple commands at once."""
    
    device_ids: List[int] = Field(..., min_items=1, max_items=100, description="List of device IDs")
    command_type: CommandType = Field(..., description="Type of command to send")
    priority: CommandPriority = Field(CommandPriority.NORMAL, description="Command priority")
    parameters: Optional[Dict[str, Any]] = Field(None, description="Command-specific parameters")
    expires_at: Optional[datetime] = Field(None, description="Command expiration time")
    max_retries: int = Field(3, ge=0, le=10, description="Maximum number of retries")


class CommandBulkResponse(BaseModel):
    """Schema for bulk command creation response."""
    
    created_commands: List[CommandResponse]
    failed_commands: List[Dict[str, Any]]
    total_created: int
    total_failed: int


class CommandRetryRequest(BaseModel):
    """Schema for retrying failed commands."""
    
    command_ids: List[int] = Field(..., min_items=1, description="List of command IDs to retry")
    reset_retry_count: bool = Field(False, description="Reset retry count to 0")


class CommandCancelRequest(BaseModel):
    """Schema for cancelling commands."""
    
    command_ids: List[int] = Field(..., min_items=1, description="List of command IDs to cancel")
    reason: Optional[str] = Field(None, description="Cancellation reason")


class CommandFilter(BaseModel):
    """Schema for filtering commands."""
    
    device_id: Optional[int] = Field(None, description="Filter by device ID")
    user_id: Optional[int] = Field(None, description="Filter by user ID")
    command_type: Optional[CommandType] = Field(None, description="Filter by command type")
    status: Optional[CommandStatus] = Field(None, description="Filter by status")
    priority: Optional[CommandPriority] = Field(None, description="Filter by priority")
    created_after: Optional[datetime] = Field(None, description="Filter by creation date (after)")
    created_before: Optional[datetime] = Field(None, description="Filter by creation date (before)")
    is_expired: Optional[bool] = Field(None, description="Filter by expiration status")
    can_retry: Optional[bool] = Field(None, description="Filter by retry capability")


class CommandSearch(BaseModel):
    """Schema for searching commands."""
    
    query: Optional[str] = Field(None, description="Search query")
    filters: Optional[CommandFilter] = Field(None, description="Additional filters")
    page: int = Field(1, ge=1, description="Page number")
    size: int = Field(20, ge=1, le=100, description="Page size")
    sort_by: str = Field("created_at", description="Sort field")
    sort_order: str = Field("desc", pattern="^(asc|desc)$", description="Sort order")


# Protocol-specific command schemas
class SuntechCommandParams(BaseModel):
    """Suntech protocol specific command parameters."""
    
    # SETINTERVAL parameters
    interval: Optional[int] = Field(None, ge=10, le=86400, description="Interval in seconds")
    
    # SETOVERSPEED parameters
    speed_limit: Optional[float] = Field(None, gt=0, le=200, description="Speed limit in km/h")
    
    # SETGEOFENCE parameters
    latitude: Optional[float] = Field(None, ge=-90, le=90, description="Geofence center latitude")
    longitude: Optional[float] = Field(None, ge=-180, le=180, description="Geofence center longitude")
    radius: Optional[float] = Field(None, gt=0, le=10000, description="Geofence radius in meters")
    
    # SETOUTPUT parameters
    output_id: Optional[int] = Field(None, ge=1, le=8, description="Output ID (1-8)")
    output_state: Optional[bool] = Field(None, description="Output state (on/off)")
    
    # SETINPUT parameters
    input_id: Optional[int] = Field(None, ge=1, le=8, description="Input ID (1-8)")
    input_type: Optional[str] = Field(None, description="Input type")
    
    # SETACCELERATION/SETDECELERATION parameters
    threshold: Optional[float] = Field(None, gt=0, le=10, description="Acceleration/deceleration threshold")
    
    # SETTURN parameters
    angle_threshold: Optional[float] = Field(None, gt=0, le=180, description="Turn angle threshold in degrees")
    
    # SETIDLE parameters
    idle_time: Optional[int] = Field(None, ge=60, le=86400, description="Idle time in seconds")


class OsmAndCommandParams(BaseModel):
    """OsmAnd protocol specific command parameters."""
    
    # SET_INTERVAL parameters
    interval: Optional[int] = Field(None, ge=10, le=86400, description="Tracking interval in seconds")
    
    # SET_ACCURACY parameters
    accuracy: Optional[float] = Field(None, gt=0, le=1000, description="GPS accuracy in meters")
    
    # SET_BATTERY_SAVER parameters
    battery_saver: Optional[bool] = Field(None, description="Enable battery saver mode")
    
    # SET_ALARM parameters
    alarm_type: Optional[str] = Field(None, description="Alarm type")
    alarm_enabled: Optional[bool] = Field(None, description="Enable/disable alarm")
    
    # SET_GEOFENCE parameters
    latitude: Optional[float] = Field(None, ge=-90, le=90, description="Geofence center latitude")
    longitude: Optional[float] = Field(None, ge=-180, le=180, description="Geofence center longitude")
    radius: Optional[float] = Field(None, gt=0, le=10000, description="Geofence radius in meters")
    
    # SET_SPEED_LIMIT parameters
    speed_limit: Optional[float] = Field(None, gt=0, le=200, description="Speed limit in km/h")
    
    # SET_ENGINE_STOP/SET_ENGINE_START parameters
    engine_control: Optional[bool] = Field(None, description="Engine control state")


class CommandProtocolParams(BaseModel):
    """Protocol-specific command parameters."""
    
    suntech: Optional[SuntechCommandParams] = Field(None, description="Suntech protocol parameters")
    osmand: Optional[OsmAndCommandParams] = Field(None, description="OsmAnd protocol parameters")

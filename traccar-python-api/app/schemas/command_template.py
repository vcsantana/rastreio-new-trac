"""
Command template schemas for API validation and serialization.
"""

from datetime import datetime
from typing import Optional, Dict, Any, List
from pydantic import BaseModel, Field, validator

from app.models.command import CommandType, CommandPriority


class CommandTemplateCreate(BaseModel):
    """Schema for creating a new command template."""
    
    name: str = Field(..., min_length=1, max_length=255, description="Template name")
    description: Optional[str] = Field(None, description="Template description")
    command_type: CommandType = Field(..., description="Type of command")
    priority: CommandPriority = Field(CommandPriority.NORMAL, description="Command priority")
    parameters: Optional[Dict[str, Any]] = Field(None, description="Command-specific parameters")
    attributes: Optional[Dict[str, Any]] = Field(None, description="Dynamic attributes")
    text_channel: bool = Field(False, description="Use SMS channel for command")
    max_retries: int = Field(3, ge=0, le=10, description="Maximum number of retries")
    is_public: bool = Field(False, description="Make template public for all users")


class CommandTemplateUpdate(BaseModel):
    """Schema for updating a command template."""
    
    name: Optional[str] = Field(None, min_length=1, max_length=255, description="Template name")
    description: Optional[str] = Field(None, description="Template description")
    command_type: Optional[CommandType] = Field(None, description="Type of command")
    priority: Optional[CommandPriority] = Field(None, description="Command priority")
    parameters: Optional[Dict[str, Any]] = Field(None, description="Command-specific parameters")
    attributes: Optional[Dict[str, Any]] = Field(None, description="Dynamic attributes")
    text_channel: Optional[bool] = Field(None, description="Use SMS channel for command")
    max_retries: Optional[int] = Field(None, ge=0, le=10, description="Maximum number of retries")
    is_public: Optional[bool] = Field(None, description="Make template public for all users")
    is_active: Optional[bool] = Field(None, description="Template active status")


class CommandTemplateResponse(BaseModel):
    """Schema for command template response."""
    
    id: int
    name: str
    description: Optional[str]
    command_type: CommandType
    priority: CommandPriority
    parameters: Optional[Dict[str, Any]]
    attributes: Optional[Dict[str, Any]]
    text_channel: bool
    max_retries: int
    is_public: bool
    is_active: bool
    usage_count: int
    user_id: int
    created_at: datetime
    updated_at: datetime
    last_used_at: Optional[datetime]
    
    # User information
    user_name: Optional[str] = None
    user_email: Optional[str] = None
    
    class Config:
        from_attributes = True


class CommandTemplateListResponse(BaseModel):
    """Schema for command template list response."""
    
    templates: List[CommandTemplateResponse]
    total: int
    page: int
    size: int
    pages: int


class CommandTemplateSearch(BaseModel):
    """Schema for searching command templates."""
    
    query: Optional[str] = Field(None, description="Search query")
    command_type: Optional[CommandType] = Field(None, description="Filter by command type")
    is_public: Optional[bool] = Field(None, description="Filter by public status")
    is_active: Optional[bool] = Field(None, description="Filter by active status")
    page: int = Field(1, ge=1, description="Page number")
    size: int = Field(20, ge=1, le=100, description="Page size")
    sort_by: str = Field("created_at", description="Sort field")
    sort_order: str = Field("desc", pattern="^(asc|desc)$", description="Sort order")


class CommandFromTemplateCreate(BaseModel):
    """Schema for creating a command from a template."""
    
    template_id: int = Field(..., description="Template ID to use")
    device_id: int = Field(..., description="Target device ID")
    parameters_override: Optional[Dict[str, Any]] = Field(None, description="Override template parameters")
    attributes_override: Optional[Dict[str, Any]] = Field(None, description="Override template attributes")
    expires_at: Optional[datetime] = Field(None, description="Command expiration time")


class ScheduledCommandCreate(BaseModel):
    """Schema for creating a scheduled command."""
    
    command_id: int = Field(..., description="Command ID to schedule")
    scheduled_at: datetime = Field(..., description="When to execute the command")
    repeat_interval: Optional[int] = Field(None, ge=60, description="Repeat interval in seconds")
    max_repeats: Optional[int] = Field(None, ge=1, description="Maximum number of repeats")


class ScheduledCommandUpdate(BaseModel):
    """Schema for updating a scheduled command."""
    
    scheduled_at: Optional[datetime] = Field(None, description="When to execute the command")
    repeat_interval: Optional[int] = Field(None, ge=60, description="Repeat interval in seconds")
    max_repeats: Optional[int] = Field(None, ge=1, description="Maximum number of repeats")
    is_active: Optional[bool] = Field(None, description="Scheduled command active status")


class ScheduledCommandResponse(BaseModel):
    """Schema for scheduled command response."""
    
    id: int
    command_id: int
    scheduled_at: datetime
    is_executed: bool
    executed_at: Optional[datetime]
    repeat_interval: Optional[int]
    repeat_count: int
    max_repeats: Optional[int]
    is_active: bool
    user_id: int
    created_at: datetime
    updated_at: datetime
    is_ready_for_execution: bool
    can_repeat: bool
    
    # Command details
    command: Optional[Dict[str, Any]] = None
    
    class Config:
        from_attributes = True


class ScheduledCommandListResponse(BaseModel):
    """Schema for scheduled command list response."""
    
    scheduled_commands: List[ScheduledCommandResponse]
    total: int
    page: int
    size: int
    pages: int


class CommandTemplateStatsResponse(BaseModel):
    """Schema for command template statistics response."""
    
    total_templates: int
    public_templates: int
    private_templates: int
    active_templates: int
    inactive_templates: int
    
    # By command type
    command_type_stats: Dict[str, int]
    
    # Usage statistics
    most_used_templates: List[Dict[str, Any]]
    recent_templates: List[Dict[str, Any]]
    
    # Recent activity
    templates_created_last_week: int
    templates_used_last_week: int

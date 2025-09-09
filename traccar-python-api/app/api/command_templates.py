"""
Command template API endpoints for template management.
"""

from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
import structlog

from app.database import get_db
from app.models.user import User
from app.schemas.command_template import (
    CommandTemplateCreate, CommandTemplateUpdate, CommandTemplateResponse,
    CommandTemplateListResponse, CommandTemplateSearch, CommandFromTemplateCreate,
    ScheduledCommandCreate, ScheduledCommandUpdate, ScheduledCommandResponse,
    ScheduledCommandListResponse, CommandTemplateStatsResponse
)
from app.services.command_template_service import CommandTemplateService
from app.api.auth import get_current_user
from app.core.rate_limiter import rate_limit

logger = structlog.get_logger(__name__)

router = APIRouter(prefix="/api/command-templates", tags=["command-templates"])


@router.post("/", response_model=CommandTemplateResponse, status_code=status.HTTP_201_CREATED)
async def create_command_template(
    template_data: CommandTemplateCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Create a new command template."""
    try:
        template_service = CommandTemplateService(db)
        template = await template_service.create_template(template_data, current_user.id)
        
        logger.info(
            "Command template created via API",
            template_id=template.id,
            template_name=template_data.name,
            command_type=template_data.command_type,
            user_id=current_user.id
        )
        
        return template
        
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        logger.error(f"Error creating command template: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Internal server error")


@router.get("/", response_model=CommandTemplateListResponse)
async def get_command_templates(
    page: int = Query(1, ge=1, description="Page number"),
    size: int = Query(20, ge=1, le=100, description="Page size"),
    command_type: Optional[str] = Query(None, description="Filter by command type"),
    is_public: Optional[bool] = Query(None, description="Filter by public status"),
    is_active: Optional[bool] = Query(None, description="Filter by active status"),
    sort_by: str = Query("created_at", description="Sort field"),
    sort_order: str = Query("desc", pattern="^(asc|desc)$", description="Sort order"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get command templates with filtering and pagination."""
    try:
        # Build search object
        search = CommandTemplateSearch(
            command_type=command_type,
            is_public=is_public,
            is_active=is_active,
            page=page,
            size=size,
            sort_by=sort_by,
            sort_order=sort_order
        )
        
        template_service = CommandTemplateService(db)
        templates, total = await template_service.get_templates(search, current_user.id)
        
        # Calculate pagination
        pages = (total + size - 1) // size
        
        return CommandTemplateListResponse(
            templates=templates,
            total=total,
            page=page,
            size=size,
            pages=pages
        )
        
    except Exception as e:
        logger.error(f"Error getting command templates: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Internal server error")


@router.get("/search", response_model=CommandTemplateListResponse)
async def search_command_templates(
    search: CommandTemplateSearch,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Search command templates with advanced filtering."""
    try:
        template_service = CommandTemplateService(db)
        templates, total = await template_service.get_templates(search, current_user.id)
        
        # Calculate pagination
        pages = (total + search.size - 1) // search.size
        
        return CommandTemplateListResponse(
            templates=templates,
            total=total,
            page=search.page,
            size=search.size,
            pages=pages
        )
        
    except Exception as e:
        logger.error(f"Error searching command templates: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Internal server error")


@router.get("/{template_id}", response_model=CommandTemplateResponse)
async def get_command_template(
    template_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get a specific command template by ID."""
    try:
        template_service = CommandTemplateService(db)
        template = await template_service.get_template(template_id, current_user.id)
        
        if not template:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Command template not found")
        
        return template
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting command template {template_id}: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Internal server error")


@router.put("/{template_id}", response_model=CommandTemplateResponse)
async def update_command_template(
    template_id: int,
    update_data: CommandTemplateUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Update a command template."""
    try:
        template_service = CommandTemplateService(db)
        template = await template_service.update_template(template_id, update_data, current_user.id)
        
        if not template:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Command template not found")
        
        logger.info(
            "Command template updated via API",
            template_id=template_id,
            user_id=current_user.id
        )
        
        return template
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating command template {template_id}: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Internal server error")


@router.delete("/{template_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_command_template(
    template_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Delete a command template."""
    try:
        template_service = CommandTemplateService(db)
        success = await template_service.delete_template(template_id, current_user.id)
        
        if not success:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Command template not found")
        
        logger.info(
            "Command template deleted via API",
            template_id=template_id,
            user_id=current_user.id
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting command template {template_id}: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Internal server error")


@router.post("/{template_id}/use", response_model=CommandTemplateResponse)
async def use_command_template(
    template_id: int,
    command_data: CommandFromTemplateCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Use a command template to create a command."""
    try:
        template_service = CommandTemplateService(db)
        template = await template_service.use_template(template_id, command_data, current_user.id)
        
        if not template:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Command template not found")
        
        logger.info(
            "Command template used via API",
            template_id=template_id,
            device_id=command_data.device_id,
            user_id=current_user.id
        )
        
        return template
        
    except HTTPException:
        raise
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        logger.error(f"Error using command template {template_id}: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Internal server error")


@router.get("/stats/summary", response_model=CommandTemplateStatsResponse)
async def get_command_template_stats(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get command template statistics."""
    try:
        template_service = CommandTemplateService(db)
        stats = await template_service.get_template_stats(current_user.id)
        
        return CommandTemplateStatsResponse(**stats)
        
    except Exception as e:
        logger.error(f"Error getting command template stats: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Internal server error")


# Scheduled Commands endpoints
@router.post("/scheduled", response_model=ScheduledCommandResponse, status_code=status.HTTP_201_CREATED)
async def create_scheduled_command(
    scheduled_data: ScheduledCommandCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Create a scheduled command."""
    try:
        template_service = CommandTemplateService(db)
        scheduled_command = await template_service.create_scheduled_command(scheduled_data, current_user.id)
        
        logger.info(
            "Scheduled command created via API",
            scheduled_command_id=scheduled_command.id,
            command_id=scheduled_data.command_id,
            scheduled_at=scheduled_data.scheduled_at,
            user_id=current_user.id
        )
        
        return scheduled_command
        
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        logger.error(f"Error creating scheduled command: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Internal server error")


@router.get("/scheduled/", response_model=ScheduledCommandListResponse)
async def get_scheduled_commands(
    page: int = Query(1, ge=1, description="Page number"),
    size: int = Query(20, ge=1, le=100, description="Page size"),
    is_active: Optional[bool] = Query(None, description="Filter by active status"),
    is_executed: Optional[bool] = Query(None, description="Filter by executed status"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get scheduled commands with filtering and pagination."""
    try:
        template_service = CommandTemplateService(db)
        scheduled_commands, total = await template_service.get_scheduled_commands(
            page, size, is_active, is_executed, current_user.id
        )
        
        # Calculate pagination
        pages = (total + size - 1) // size
        
        return ScheduledCommandListResponse(
            scheduled_commands=scheduled_commands,
            total=total,
            page=page,
            size=size,
            pages=pages
        )
        
    except Exception as e:
        logger.error(f"Error getting scheduled commands: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Internal server error")


@router.get("/scheduled/{scheduled_id}", response_model=ScheduledCommandResponse)
async def get_scheduled_command(
    scheduled_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get a specific scheduled command by ID."""
    try:
        template_service = CommandTemplateService(db)
        scheduled_command = await template_service.get_scheduled_command(scheduled_id, current_user.id)
        
        if not scheduled_command:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Scheduled command not found")
        
        return scheduled_command
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting scheduled command {scheduled_id}: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Internal server error")


@router.put("/scheduled/{scheduled_id}", response_model=ScheduledCommandResponse)
async def update_scheduled_command(
    scheduled_id: int,
    update_data: ScheduledCommandUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Update a scheduled command."""
    try:
        template_service = CommandTemplateService(db)
        scheduled_command = await template_service.update_scheduled_command(scheduled_id, update_data, current_user.id)
        
        if not scheduled_command:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Scheduled command not found")
        
        logger.info(
            "Scheduled command updated via API",
            scheduled_id=scheduled_id,
            user_id=current_user.id
        )
        
        return scheduled_command
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating scheduled command {scheduled_id}: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Internal server error")


@router.delete("/scheduled/{scheduled_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_scheduled_command(
    scheduled_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Delete a scheduled command."""
    try:
        template_service = CommandTemplateService(db)
        success = await template_service.delete_scheduled_command(scheduled_id, current_user.id)
        
        if not success:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Scheduled command not found")
        
        logger.info(
            "Scheduled command deleted via API",
            scheduled_id=scheduled_id,
            user_id=current_user.id
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting scheduled command {scheduled_id}: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Internal server error")

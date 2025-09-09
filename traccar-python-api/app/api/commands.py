"""
Command API endpoints for device command management.
"""

from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
import structlog

from app.database import get_db
from app.models.user import User
from app.schemas.command import (
    CommandCreate, CommandUpdate, CommandResponse, CommandListResponse,
    CommandBulkCreate, CommandBulkResponse, CommandRetryRequest, CommandCancelRequest,
    CommandSearch, CommandStatsResponse, CommandQueueResponse, CommandQueueListResponse
)
from app.services.command_service import CommandService
from app.api.auth import get_current_user
from app.core.rate_limiter import rate_limit

logger = structlog.get_logger(__name__)

router = APIRouter(prefix="/api/commands", tags=["commands"])


@router.post("/", response_model=CommandResponse, status_code=status.HTTP_201_CREATED)
async def create_command(
    command_data: CommandCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Create a new command for a device."""
    try:
        command_service = CommandService(db)
        command = await command_service.create_command(command_data, current_user.id)
        
        logger.info(
            "Command created via API",
            command_id=command.id,
            device_id=command_data.device_id,
            command_type=command_data.command_type,
            user_id=current_user.id
        )
        
        return command
        
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        logger.error(f"Error creating command: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Internal server error")


@router.post("/bulk", response_model=CommandBulkResponse, status_code=status.HTTP_201_CREATED)
@rate_limit("api", "commands_bulk")
async def create_bulk_commands(
    bulk_data: CommandBulkCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Create multiple commands at once."""
    try:
        command_service = CommandService(db)
        created_commands, failed_commands = await command_service.create_bulk_commands(bulk_data, current_user.id)
        
        logger.info(
            "Bulk commands created via API",
            total_created=len(created_commands),
            total_failed=len(failed_commands),
            user_id=current_user.id
        )
        
        return CommandBulkResponse(
            created_commands=created_commands,
            failed_commands=failed_commands,
            total_created=len(created_commands),
            total_failed=len(failed_commands)
        )
        
    except Exception as e:
        logger.error(f"Error creating bulk commands: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Internal server error")


@router.get("/", response_model=CommandListResponse)
@rate_limit("api", "commands_list")
async def get_commands(
    page: int = Query(1, ge=1, description="Page number"),
    size: int = Query(20, ge=1, le=100, description="Page size"),
    device_id: Optional[int] = Query(None, description="Filter by device ID"),
    command_type: Optional[str] = Query(None, description="Filter by command type"),
    status: Optional[str] = Query(None, description="Filter by status"),
    priority: Optional[str] = Query(None, description="Filter by priority"),
    sort_by: str = Query("created_at", description="Sort field"),
    sort_order: str = Query("desc", pattern="^(asc|desc)$", description="Sort order"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get commands with filtering and pagination."""
    try:
        from app.schemas.command import CommandFilter
        
        # Build search object
        filters = CommandFilter(
            device_id=device_id,
            command_type=command_type,
            status=status,
            priority=priority
        )
        
        search = CommandSearch(
            filters=filters,
            page=page,
            size=size,
            sort_by=sort_by,
            sort_order=sort_order
        )
        
        command_service = CommandService(db)
        commands, total = await command_service.get_commands(search, current_user.id)
        
        # Calculate pagination
        pages = (total + size - 1) // size
        
        return CommandListResponse(
            commands=commands,
            total=total,
            page=page,
            size=size,
            pages=pages
        )
        
    except Exception as e:
        logger.error(f"Error getting commands: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Internal server error")


@router.get("/search", response_model=CommandListResponse)
@rate_limit("api", "commands")
async def search_commands(
    search: CommandSearch,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Search commands with advanced filtering."""
    try:
        command_service = CommandService(db)
        commands, total = await command_service.get_commands(search, current_user.id)
        
        # Calculate pagination
        pages = (total + search.size - 1) // search.size
        
        return CommandListResponse(
            commands=commands,
            total=total,
            page=search.page,
            size=search.size,
            pages=pages
        )
        
    except Exception as e:
        logger.error(f"Error searching commands: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Internal server error")


@router.get("/{command_id}", response_model=CommandResponse)
@rate_limit("api", "commands_detail")
async def get_command(
    command_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get a specific command by ID."""
    try:
        command_service = CommandService(db)
        command = await command_service.get_command(command_id, current_user.id)
        
        if not command:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Command not found")
        
        return command
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting command {command_id}: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Internal server error")


@router.put("/{command_id}", response_model=CommandResponse)
@rate_limit("api", "commands")
async def update_command(
    command_id: int,
    update_data: CommandUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Update a command."""
    try:
        command_service = CommandService(db)
        command = await command_service.update_command(command_id, update_data, current_user.id)
        
        if not command:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Command not found")
        
        logger.info(
            "Command updated via API",
            command_id=command_id,
            user_id=current_user.id
        )
        
        return command
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating command {command_id}: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Internal server error")


@router.post("/retry", response_model=List[CommandResponse])
@rate_limit("api", "commands_retry")
async def retry_commands(
    retry_data: CommandRetryRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Retry failed commands."""
    try:
        command_service = CommandService(db)
        retried_commands = await command_service.retry_commands(retry_data, current_user.id)
        
        logger.info(
            "Commands retried via API",
            command_ids=retry_data.command_ids,
            retried_count=len(retried_commands),
            user_id=current_user.id
        )
        
        return retried_commands
        
    except Exception as e:
        logger.error(f"Error retrying commands: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Internal server error")


@router.post("/cancel", response_model=List[CommandResponse])
@rate_limit("api", "commands_retry")
async def cancel_commands(
    cancel_data: CommandCancelRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Cancel pending commands."""
    try:
        command_service = CommandService(db)
        cancelled_commands = await command_service.cancel_commands(cancel_data, current_user.id)
        
        logger.info(
            "Commands cancelled via API",
            command_ids=cancel_data.command_ids,
            cancelled_count=len(cancelled_commands),
            user_id=current_user.id
        )
        
        return cancelled_commands
        
    except Exception as e:
        logger.error(f"Error cancelling commands: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Internal server error")


@router.get("/stats/summary", response_model=CommandStatsResponse)
@rate_limit("api", "commands")
async def get_command_stats(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get command statistics."""
    try:
        command_service = CommandService(db)
        stats = await command_service.get_command_stats(current_user.id)
        
        return CommandStatsResponse(**stats)
        
    except Exception as e:
        logger.error(f"Error getting command stats: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Internal server error")


@router.get("/queue/", response_model=CommandQueueListResponse)
@rate_limit("api", "commands")
async def get_command_queue(
    page: int = Query(1, ge=1, description="Page number"),
    size: int = Query(20, ge=1, le=100, description="Page size"),
    priority: Optional[str] = Query(None, description="Filter by priority"),
    is_active: Optional[bool] = Query(None, description="Filter by active status"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get command queue entries."""
    try:
        from app.models.command import CommandQueue
        from sqlalchemy import and_
        
        query = db.query(CommandQueue)
        
        # Apply filters
        if priority:
            query = query.filter(CommandQueue.priority == priority)
        
        if is_active is not None:
            query = query.filter(CommandQueue.is_active == is_active)
        
        # Get total count
        total = query.count()
        
        # Apply pagination
        offset = (page - 1) * size
        queue_entries = query.offset(offset).limit(size).all()
        
        # Calculate pagination
        pages = (total + size - 1) // size
        
        return CommandQueueListResponse(
            queue=queue_entries,
            total=total,
            page=page,
            size=size,
            pages=pages
        )
        
    except Exception as e:
        logger.error(f"Error getting command queue: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Internal server error")


@router.get("/device/{device_id}", response_model=CommandListResponse)
@rate_limit("api", "commands_list")
async def get_device_commands(
    device_id: int,
    page: int = Query(1, ge=1, description="Page number"),
    size: int = Query(20, ge=1, le=100, description="Page size"),
    status: Optional[str] = Query(None, description="Filter by status"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get commands for a specific device."""
    try:
        from app.schemas.command import CommandFilter, CommandSearch
        
        # Build search object
        filters = CommandFilter(
            device_id=device_id,
            status=status
        )
        
        search = CommandSearch(
            filters=filters,
            page=page,
            size=size,
            sort_by="created_at",
            sort_order="desc"
        )
        
        command_service = CommandService(db)
        commands, total = await command_service.get_commands(search, current_user.id)
        
        # Calculate pagination
        pages = (total + size - 1) // size
        
        return CommandListResponse(
            commands=commands,
            total=total,
            page=page,
            size=size,
            pages=pages
        )
        
    except Exception as e:
        logger.error(f"Error getting device commands: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Internal server error")


@router.get("/types/", response_model=List[str])
async def get_command_types():
    """Get available command types."""
    try:
        from app.models.command import CommandType
        
        return [cmd_type.value for cmd_type in CommandType]
        
    except Exception as e:
        logger.error(f"Error getting command types: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Internal server error")


@router.get("/statuses/", response_model=List[str])
async def get_command_statuses():
    """Get available command statuses."""
    try:
        from app.models.command import CommandStatus
        
        return [status.value for status in CommandStatus]
        
    except Exception as e:
        logger.error(f"Error getting command statuses: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Internal server error")


@router.get("/priorities/", response_model=List[str])
async def get_command_priorities():
    """Get available command priorities."""
    try:
        from app.models.command import CommandPriority
        
        return [priority.value for priority in CommandPriority]
        
    except Exception as e:
        logger.error(f"Error getting command priorities: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Internal server error")

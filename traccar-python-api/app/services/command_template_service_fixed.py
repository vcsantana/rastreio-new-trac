"""
Command template service for managing command templates and scheduled commands.
"""

from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any, Tuple
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import and_, or_, desc, asc, func, select
import structlog

from app.models.command_template import CommandTemplate, ScheduledCommand
from app.models.command import Command, CommandType, CommandPriority, CommandStatus
from app.models.device import Device
from app.models.user import User
from app.schemas.command_template import (
    CommandTemplateCreate, CommandTemplateUpdate, CommandTemplateSearch,
    CommandFromTemplateCreate, ScheduledCommandCreate, ScheduledCommandUpdate
)
from app.services.command_service import CommandService

logger = structlog.get_logger(__name__)


class CommandTemplateService:
    """Service for managing command templates and scheduled commands."""
    
    def __init__(self, db: AsyncSession):
        self.db = db
        self.command_service = CommandService(db)
    
    async def create_template(self, template_data: CommandTemplateCreate, user_id: int) -> CommandTemplate:
        """Create a new command template."""
        try:
            # Check if template name already exists for this user
            result = await self.db.execute(
                select(CommandTemplate).filter(
                    and_(
                        CommandTemplate.name == template_data.name,
                        CommandTemplate.user_id == user_id,
                        CommandTemplate.is_active == True
                    )
                )
            )
            existing_template = result.scalar_one_or_none()
            
            if existing_template:
                raise ValueError(f"Template with name '{template_data.name}' already exists")
            
            # Create new template
            template = CommandTemplate(
                name=template_data.name,
                description=template_data.description,
                command_type=template_data.command_type.value,
                priority=template_data.priority.value,
                parameters=template_data.parameters,
                attributes=template_data.attributes,
                text_channel=template_data.text_channel,
                max_retries=template_data.max_retries,
                is_public=template_data.is_public,
                user_id=user_id
            )
            
            self.db.add(template)
            await self.db.commit()
            await self.db.refresh(template)
            
            logger.info(
                "Command template created",
                template_id=template.id,
                template_name=template.name,
                user_id=user_id
            )
            
            return template
            
        except Exception as e:
            await self.db.rollback()
            logger.error(f"Error creating command template: {e}")
            raise
    
    async def get_templates(self, search: CommandTemplateSearch, user_id: int) -> Tuple[List[CommandTemplate], int]:
        """Get command templates with filtering and pagination."""
        try:
            # Build base query
            base_query = select(CommandTemplate).filter(
                or_(
                    CommandTemplate.user_id == user_id,
                    CommandTemplate.is_public == True
                )
            )
            
            # Apply filters
            if search.command_type:
                base_query = base_query.filter(CommandTemplate.command_type == search.command_type.value)
            
            if search.is_public is not None:
                base_query = base_query.filter(CommandTemplate.is_public == search.is_public)
            
            if search.is_active is not None:
                base_query = base_query.filter(CommandTemplate.is_active == search.is_active)
            
            # Apply search query
            if search.query:
                base_query = base_query.filter(
                    or_(
                        CommandTemplate.name.ilike(f"%{search.query}%"),
                        CommandTemplate.description.ilike(f"%{search.query}%")
                    )
                )
            
            # Get total count
            count_query = select(func.count()).select_from(base_query.subquery())
            count_result = await self.db.execute(count_query)
            total = count_result.scalar()
            
            # Apply sorting
            if search.sort_by == "name":
                sort_column = CommandTemplate.name
            elif search.sort_by == "command_type":
                sort_column = CommandTemplate.command_type
            elif search.sort_by == "usage_count":
                sort_column = CommandTemplate.usage_count
            elif search.sort_by == "last_used_at":
                sort_column = CommandTemplate.last_used_at
            else:
                sort_column = CommandTemplate.created_at
            
            if search.sort_order == "asc":
                base_query = base_query.order_by(asc(sort_column))
            else:
                base_query = base_query.order_by(desc(sort_column))
            
            # Apply pagination
            offset = (search.page - 1) * search.size
            base_query = base_query.offset(offset).limit(search.size)
            
            # Execute query
            result = await self.db.execute(base_query)
            templates = result.scalars().all()
            
            return list(templates), total
            
        except Exception as e:
            logger.error(f"Error getting command templates: {e}")
            raise
    
    async def get_template(self, template_id: int, user_id: int) -> Optional[CommandTemplate]:
        """Get a specific command template by ID."""
        try:
            result = await self.db.execute(
                select(CommandTemplate).filter(
                    and_(
                        CommandTemplate.id == template_id,
                        or_(
                            CommandTemplate.user_id == user_id,
                            CommandTemplate.is_public == True
                        ),
                        CommandTemplate.is_active == True
                    )
                )
            )
            template = result.scalar_one_or_none()
            
            return template
            
        except Exception as e:
            logger.error(f"Error getting command template {template_id}: {e}")
            raise
    
    async def update_template(self, template_id: int, update_data: CommandTemplateUpdate, user_id: int) -> Optional[CommandTemplate]:
        """Update a command template."""
        try:
            result = await self.db.execute(
                select(CommandTemplate).filter(
                    and_(
                        CommandTemplate.id == template_id,
                        CommandTemplate.user_id == user_id,
                        CommandTemplate.is_active == True
                    )
                )
            )
            template = result.scalar_one_or_none()
            
            if not template:
                return None
            
            # Update fields
            if update_data.name is not None:
                # Check if new name already exists
                existing_result = await self.db.execute(
                    select(CommandTemplate).filter(
                        and_(
                            CommandTemplate.name == update_data.name,
                            CommandTemplate.user_id == user_id,
                            CommandTemplate.id != template_id,
                            CommandTemplate.is_active == True
                        )
                    )
                )
                existing_template = existing_result.scalar_one_or_none()
                
                if existing_template:
                    raise ValueError(f"Template with name '{update_data.name}' already exists")
                
                template.name = update_data.name
            
            if update_data.description is not None:
                template.description = update_data.description
            
            if update_data.command_type is not None:
                template.command_type = update_data.command_type.value
            
            if update_data.priority is not None:
                template.priority = update_data.priority.value
            
            if update_data.parameters is not None:
                template.parameters = update_data.parameters
            
            if update_data.attributes is not None:
                template.attributes = update_data.attributes
            
            if update_data.text_channel is not None:
                template.text_channel = update_data.text_channel
            
            if update_data.max_retries is not None:
                template.max_retries = update_data.max_retries
            
            if update_data.is_public is not None:
                template.is_public = update_data.is_public
            
            if update_data.is_active is not None:
                template.is_active = update_data.is_active
            
            await self.db.commit()
            await self.db.refresh(template)
            
            logger.info(
                "Command template updated",
                template_id=template_id,
                user_id=user_id
            )
            
            return template
            
        except Exception as e:
            await self.db.rollback()
            logger.error(f"Error updating command template {template_id}: {e}")
            raise
    
    async def delete_template(self, template_id: int, user_id: int) -> bool:
        """Delete a command template (soft delete)."""
        try:
            result = await self.db.execute(
                select(CommandTemplate).filter(
                    and_(
                        CommandTemplate.id == template_id,
                        CommandTemplate.user_id == user_id,
                        CommandTemplate.is_active == True
                    )
                )
            )
            template = result.scalar_one_or_none()
            
            if not template:
                return False
            
            # Soft delete
            template.is_active = False
            await self.db.commit()
            
            logger.info(
                "Command template deleted",
                template_id=template_id,
                user_id=user_id
            )
            
            return True
            
        except Exception as e:
            await self.db.rollback()
            logger.error(f"Error deleting command template {template_id}: {e}")
            raise
    
    async def use_template(self, template_id: int, command_data: CommandFromTemplateCreate, user_id: int) -> Optional[CommandTemplate]:
        """Use a command template to create a command."""
        try:
            # Get template
            template = await self.get_template(template_id, user_id)
            if not template:
                return None
            
            # Verify device exists and user has access
            device_result = await self.db.execute(
                select(Device).filter(
                    and_(
                        Device.id == command_data.device_id,
                        Device.user_id == user_id
                    )
                )
            )
            device = device_result.scalar_one_or_none()
            
            if not device:
                raise ValueError("Device not found or access denied")
            
            # Create command from template
            from app.schemas.command import CommandCreate
            
            command_create = CommandCreate(
                device_id=command_data.device_id,
                command_type=CommandType(template.command_type),
                priority=CommandPriority(template.priority),
                parameters=command_data.parameters_override or template.parameters,
                attributes=command_data.attributes_override or template.attributes,
                description=template.description,
                text_channel=template.text_channel,
                expires_at=command_data.expires_at,
                max_retries=template.max_retries
            )
            
            # Create command using command service
            command = await self.command_service.create_command(command_create, user_id)
            
            # Increment template usage
            template.increment_usage()
            await self.db.commit()
            
            logger.info(
                "Command created from template",
                template_id=template_id,
                command_id=command.id,
                device_id=command_data.device_id,
                user_id=user_id
            )
            
            return template
            
        except Exception as e:
            await self.db.rollback()
            logger.error(f"Error using command template {template_id}: {e}")
            raise
    
    async def get_template_stats(self, user_id: int) -> Dict[str, Any]:
        """Get command template statistics."""
        try:
            # Base query for user's templates
            base_query = select(CommandTemplate).filter(
                or_(
                    CommandTemplate.user_id == user_id,
                    CommandTemplate.is_public == True
                )
            )
            
            # Total templates
            total_result = await self.db.execute(select(func.count()).select_from(base_query.subquery()))
            total_templates = total_result.scalar()
            
            # Public vs private
            public_result = await self.db.execute(
                select(func.count()).select_from(
                    base_query.filter(CommandTemplate.is_public == True).subquery()
                )
            )
            public_templates = public_result.scalar()
            
            private_result = await self.db.execute(
                select(func.count()).select_from(
                    base_query.filter(
                        and_(
                            CommandTemplate.is_public == False,
                            CommandTemplate.user_id == user_id
                        )
                    ).subquery()
                )
            )
            private_templates = private_result.scalar()
            
            # Active vs inactive
            active_result = await self.db.execute(
                select(func.count()).select_from(
                    base_query.filter(CommandTemplate.is_active == True).subquery()
                )
            )
            active_templates = active_result.scalar()
            
            inactive_result = await self.db.execute(
                select(func.count()).select_from(
                    base_query.filter(CommandTemplate.is_active == False).subquery()
                )
            )
            inactive_templates = inactive_result.scalar()
            
            # By command type
            command_type_stats = {}
            for cmd_type in CommandType:
                type_result = await self.db.execute(
                    select(func.count()).select_from(
                        base_query.filter(CommandTemplate.command_type == cmd_type.value).subquery()
                    )
                )
                count = type_result.scalar()
                if count > 0:
                    command_type_stats[cmd_type.value] = count
            
            # Most used templates
            most_used_result = await self.db.execute(
                base_query.filter(CommandTemplate.usage_count > 0)
                .order_by(desc(CommandTemplate.usage_count))
                .limit(5)
            )
            most_used = most_used_result.scalars().all()
            
            most_used_templates = [
                {
                    "id": template.id,
                    "name": template.name,
                    "usage_count": template.usage_count,
                    "command_type": template.command_type
                }
                for template in most_used
            ]
            
            # Recent templates
            recent_result = await self.db.execute(
                base_query.order_by(desc(CommandTemplate.created_at)).limit(5)
            )
            recent_templates = recent_result.scalars().all()
            
            recent_templates_list = [
                {
                    "id": template.id,
                    "name": template.name,
                    "created_at": template.created_at.isoformat(),
                    "command_type": template.command_type
                }
                for template in recent_templates
            ]
            
            # Recent activity
            week_ago = datetime.utcnow() - timedelta(days=7)
            
            created_result = await self.db.execute(
                select(func.count()).select_from(
                    base_query.filter(CommandTemplate.created_at >= week_ago).subquery()
                )
            )
            templates_created_last_week = created_result.scalar()
            
            used_result = await self.db.execute(
                select(func.count()).select_from(
                    base_query.filter(CommandTemplate.last_used_at >= week_ago).subquery()
                )
            )
            templates_used_last_week = used_result.scalar()
            
            return {
                "total_templates": total_templates,
                "public_templates": public_templates,
                "private_templates": private_templates,
                "active_templates": active_templates,
                "inactive_templates": inactive_templates,
                "command_type_stats": command_type_stats,
                "most_used_templates": most_used_templates,
                "recent_templates": recent_templates_list,
                "templates_created_last_week": templates_created_last_week,
                "templates_used_last_week": templates_used_last_week
            }
            
        except Exception as e:
            logger.error(f"Error getting template stats: {e}")
            raise
    
    # Scheduled Commands methods
    async def create_scheduled_command(self, scheduled_data: ScheduledCommandCreate, user_id: int) -> ScheduledCommand:
        """Create a scheduled command."""
        try:
            # Verify command exists and user has access
            command_result = await self.db.execute(
                select(Command).filter(
                    and_(
                        Command.id == scheduled_data.command_id,
                        Command.user_id == user_id
                    )
                )
            )
            command = command_result.scalar_one_or_none()
            
            if not command:
                raise ValueError("Command not found or access denied")
            
            # Check if command is already scheduled
            existing_result = await self.db.execute(
                select(ScheduledCommand).filter(
                    ScheduledCommand.command_id == scheduled_data.command_id
                )
            )
            existing_scheduled = existing_result.scalar_one_or_none()
            
            if existing_scheduled:
                raise ValueError("Command is already scheduled")
            
            # Create scheduled command
            scheduled_command = ScheduledCommand(
                command_id=scheduled_data.command_id,
                scheduled_at=scheduled_data.scheduled_at,
                repeat_interval=scheduled_data.repeat_interval,
                max_repeats=scheduled_data.max_repeats,
                user_id=user_id
            )
            
            self.db.add(scheduled_command)
            await self.db.commit()
            await self.db.refresh(scheduled_command)
            
            logger.info(
                "Scheduled command created",
                scheduled_command_id=scheduled_command.id,
                command_id=scheduled_data.command_id,
                scheduled_at=scheduled_data.scheduled_at,
                user_id=user_id
            )
            
            return scheduled_command
            
        except Exception as e:
            await self.db.rollback()
            logger.error(f"Error creating scheduled command: {e}")
            raise
    
    async def get_scheduled_commands(self, page: int, size: int, is_active: Optional[bool], 
                                   is_executed: Optional[bool], user_id: int) -> Tuple[List[ScheduledCommand], int]:
        """Get scheduled commands with filtering and pagination."""
        try:
            base_query = select(ScheduledCommand).filter(
                ScheduledCommand.user_id == user_id
            )
            
            # Apply filters
            if is_active is not None:
                base_query = base_query.filter(ScheduledCommand.is_active == is_active)
            
            if is_executed is not None:
                base_query = base_query.filter(ScheduledCommand.is_executed == is_executed)
            
            # Get total count
            count_result = await self.db.execute(select(func.count()).select_from(base_query.subquery()))
            total = count_result.scalar()
            
            # Apply pagination
            offset = (page - 1) * size
            base_query = base_query.order_by(desc(ScheduledCommand.scheduled_at)).offset(offset).limit(size)
            
            # Execute query
            result = await self.db.execute(base_query)
            scheduled_commands = result.scalars().all()
            
            return list(scheduled_commands), total
            
        except Exception as e:
            logger.error(f"Error getting scheduled commands: {e}")
            raise
    
    async def get_scheduled_command(self, scheduled_id: int, user_id: int) -> Optional[ScheduledCommand]:
        """Get a specific scheduled command by ID."""
        try:
            result = await self.db.execute(
                select(ScheduledCommand).filter(
                    and_(
                        ScheduledCommand.id == scheduled_id,
                        ScheduledCommand.user_id == user_id
                    )
                )
            )
            scheduled_command = result.scalar_one_or_none()
            
            return scheduled_command
            
        except Exception as e:
            logger.error(f"Error getting scheduled command {scheduled_id}: {e}")
            raise
    
    async def update_scheduled_command(self, scheduled_id: int, update_data: ScheduledCommandUpdate, user_id: int) -> Optional[ScheduledCommand]:
        """Update a scheduled command."""
        try:
            result = await self.db.execute(
                select(ScheduledCommand).filter(
                    and_(
                        ScheduledCommand.id == scheduled_id,
                        ScheduledCommand.user_id == user_id
                    )
                )
            )
            scheduled_command = result.scalar_one_or_none()
            
            if not scheduled_command:
                return None
            
            # Update fields
            if update_data.scheduled_at is not None:
                scheduled_command.scheduled_at = update_data.scheduled_at
            
            if update_data.repeat_interval is not None:
                scheduled_command.repeat_interval = update_data.repeat_interval
            
            if update_data.max_repeats is not None:
                scheduled_command.max_repeats = update_data.max_repeats
            
            if update_data.is_active is not None:
                scheduled_command.is_active = update_data.is_active
            
            await self.db.commit()
            await self.db.refresh(scheduled_command)
            
            logger.info(
                "Scheduled command updated",
                scheduled_id=scheduled_id,
                user_id=user_id
            )
            
            return scheduled_command
            
        except Exception as e:
            await self.db.rollback()
            logger.error(f"Error updating scheduled command {scheduled_id}: {e}")
            raise
    
    async def delete_scheduled_command(self, scheduled_id: int, user_id: int) -> bool:
        """Delete a scheduled command."""
        try:
            result = await self.db.execute(
                select(ScheduledCommand).filter(
                    and_(
                        ScheduledCommand.id == scheduled_id,
                        ScheduledCommand.user_id == user_id
                    )
                )
            )
            scheduled_command = result.scalar_one_or_none()
            
            if not scheduled_command:
                return False
            
            await self.db.delete(scheduled_command)
            await self.db.commit()
            
            logger.info(
                "Scheduled command deleted",
                scheduled_id=scheduled_id,
                user_id=user_id
            )
            
            return True
            
        except Exception as e:
            await self.db.rollback()
            logger.error(f"Error deleting scheduled command {scheduled_id}: {e}")
            raise

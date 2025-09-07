"""
Command service for managing device commands.
"""

import asyncio
from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any, Tuple
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import and_, or_, desc, asc, func
import structlog

from app.models.command import Command, CommandQueue, CommandType, CommandStatus, CommandPriority
from app.models.device import Device
from app.models.user import User
from app.schemas.command import (
    CommandCreate, CommandUpdate, CommandFilter, CommandSearch,
    CommandBulkCreate, CommandRetryRequest, CommandCancelRequest
)
from app.core.cache import cache_manager
# from app.tasks.command_tasks import process_command_queue, send_command_to_device

logger = structlog.get_logger(__name__)


class CommandService:
    """Service for managing device commands."""
    
    def __init__(self, db: Session):
        self.db = db
    
    async def create_command(self, command_data: CommandCreate, user_id: int) -> Command:
        """Create a new command."""
        try:
            # Validate device exists and user has permission
            device = self.db.query(Device).filter(Device.id == command_data.device_id).first()
            if not device:
                raise ValueError(f"Device {command_data.device_id} not found")
            
            # Check if user has permission to send commands to this device
            user = self.db.query(User).filter(User.id == user_id).first()
            if not user:
                raise ValueError(f"User {user_id} not found")
            
            # Create command
            command = Command(
                device_id=command_data.device_id,
                user_id=user_id,
                command_type=command_data.command_type,
                priority=command_data.priority,
                parameters=command_data.parameters,
                expires_at=command_data.expires_at,
                max_retries=command_data.max_retries,
                status=CommandStatus.PENDING
            )
            
            # Generate raw command based on protocol
            command.raw_command = await self._generate_raw_command(command)
            
            self.db.add(command)
            self.db.commit()
            self.db.refresh(command)
            
            # Add to command queue
            await self._add_to_queue(command)
            
            # Invalidate cache
            await cache_manager.delete_pattern(f"commands:device:{command_data.device_id}:*")
            await cache_manager.delete_pattern(f"commands:user:{user_id}:*")
            
            logger.info(
                "Command created",
                command_id=command.id,
                device_id=command_data.device_id,
                command_type=command_data.command_type,
                user_id=user_id
            )
            
            return command
            
        except Exception as e:
            self.db.rollback()
            logger.error(
                "Failed to create command",
                error=str(e),
                device_id=command_data.device_id,
                command_type=command_data.command_type,
                user_id=user_id
            )
            raise
    
    async def create_bulk_commands(self, bulk_data: CommandBulkCreate, user_id: int) -> Tuple[List[Command], List[Dict]]:
        """Create multiple commands at once."""
        created_commands = []
        failed_commands = []
        
        for device_id in bulk_data.device_ids:
            try:
                command_data = CommandCreate(
                    device_id=device_id,
                    command_type=bulk_data.command_type,
                    priority=bulk_data.priority,
                    parameters=bulk_data.parameters,
                    expires_at=bulk_data.expires_at,
                    max_retries=bulk_data.max_retries
                )
                
                command = await self.create_command(command_data, user_id)
                created_commands.append(command)
                
            except Exception as e:
                failed_commands.append({
                    "device_id": device_id,
                    "error": str(e)
                })
        
        logger.info(
            "Bulk commands created",
            total_created=len(created_commands),
            total_failed=len(failed_commands),
            user_id=user_id
        )
        
        return created_commands, failed_commands
    
    async def get_command(self, command_id: int, user_id: int) -> Optional[Command]:
        """Get a command by ID."""
        cache_key = f"command:{command_id}:{user_id}"
        cached_command = await cache_manager.get(cache_key)
        
        if cached_command:
            return cached_command
        
        command = (
            self.db.query(Command)
            .options(
                joinedload(Command.device),
                joinedload(Command.user)
            )
            .filter(Command.id == command_id)
            .first()
        )
        
        if command:
            await cache_manager.set(cache_key, command, expire=300)
        
        return command
    
    async def get_commands(
        self, 
        search: CommandSearch, 
        user_id: int
    ) -> Tuple[List[Command], int]:
        """Get commands with filtering and pagination."""
        cache_key = f"commands:search:{hash(str(search.dict()))}:{user_id}"
        cached_result = await cache_manager.get(cache_key)
        
        if cached_result:
            return cached_result["commands"], cached_result["total"]
        
        query = (
            self.db.query(Command)
            .options(
                joinedload(Command.device),
                joinedload(Command.user)
            )
        )
        
        # Apply filters
        if search.filters:
            filters = search.filters
            
            if filters.device_id:
                query = query.filter(Command.device_id == filters.device_id)
            
            if filters.user_id:
                query = query.filter(Command.user_id == filters.user_id)
            
            if filters.command_type:
                query = query.filter(Command.command_type == filters.command_type)
            
            if filters.status:
                query = query.filter(Command.status == filters.status)
            
            if filters.priority:
                query = query.filter(Command.priority == filters.priority)
            
            if filters.created_after:
                query = query.filter(Command.created_at >= filters.created_after)
            
            if filters.created_before:
                query = query.filter(Command.created_at <= filters.created_before)
            
            if filters.is_expired is not None:
                if filters.is_expired:
                    query = query.filter(Command.expires_at < datetime.utcnow())
                else:
                    query = query.filter(
                        or_(
                            Command.expires_at.is_(None),
                            Command.expires_at >= datetime.utcnow()
                        )
                    )
            
            if filters.can_retry is not None:
                if filters.can_retry:
                    query = query.filter(
                        and_(
                            Command.status.in_([CommandStatus.FAILED, CommandStatus.TIMEOUT]),
                            Command.retry_count < Command.max_retries,
                            or_(
                                Command.expires_at.is_(None),
                                Command.expires_at >= datetime.utcnow()
                            )
                        )
                    )
                else:
                    query = query.filter(
                        or_(
                            Command.status.notin_([CommandStatus.FAILED, CommandStatus.TIMEOUT]),
                            Command.retry_count >= Command.max_retries,
                            and_(
                                Command.expires_at.isnot(None),
                                Command.expires_at < datetime.utcnow()
                            )
                        )
                    )
        
        # Apply search query
        if search.query:
            query = query.filter(
                or_(
                    Command.command_type.ilike(f"%{search.query}%"),
                    Command.raw_command.ilike(f"%{search.query}%"),
                    Command.response.ilike(f"%{search.query}%"),
                    Command.error_message.ilike(f"%{search.query}%")
                )
            )
        
        # Get total count
        total = query.count()
        
        # Apply sorting
        if search.sort_by == "created_at":
            sort_column = Command.created_at
        elif search.sort_by == "device_id":
            sort_column = Command.device_id
        elif search.sort_by == "command_type":
            sort_column = Command.command_type
        elif search.sort_by == "status":
            sort_column = Command.status
        elif search.sort_by == "priority":
            sort_column = Command.priority
        else:
            sort_column = Command.created_at
        
        if search.sort_order == "asc":
            query = query.order_by(asc(sort_column))
        else:
            query = query.order_by(desc(sort_column))
        
        # Apply pagination
        offset = (search.page - 1) * search.size
        commands = query.offset(offset).limit(search.size).all()
        
        # Cache result
        result = {"commands": commands, "total": total}
        await cache_manager.set(cache_key, result, expire=60)
        
        return commands, total
    
    async def update_command(self, command_id: int, update_data: CommandUpdate, user_id: int) -> Optional[Command]:
        """Update a command."""
        command = await self.get_command(command_id, user_id)
        if not command:
            return None
        
        # Update fields
        if update_data.status is not None:
            command.status = update_data.status
            
            # Update timestamps based on status
            now = datetime.utcnow()
            if update_data.status == CommandStatus.SENT:
                command.sent_at = now
            elif update_data.status == CommandStatus.DELIVERED:
                command.delivered_at = now
            elif update_data.status == CommandStatus.EXECUTED:
                command.executed_at = now
            elif update_data.status == CommandStatus.FAILED:
                command.failed_at = now
        
        if update_data.response is not None:
            command.response = update_data.response
        
        if update_data.error_message is not None:
            command.error_message = update_data.error_message
        
        if update_data.retry_count is not None:
            command.retry_count = update_data.retry_count
        
        self.db.commit()
        self.db.refresh(command)
        
        # Invalidate cache
        await cache_manager.delete_pattern(f"command:{command_id}:*")
        await cache_manager.delete_pattern(f"commands:*")
        
        logger.info(
            "Command updated",
            command_id=command_id,
            status=command.status,
            user_id=user_id
        )
        
        return command
    
    async def retry_commands(self, retry_data: CommandRetryRequest, user_id: int) -> List[Command]:
        """Retry failed commands."""
        retried_commands = []
        
        for command_id in retry_data.command_ids:
            command = await self.get_command(command_id, user_id)
            if not command:
                continue
            
            if not command.can_retry:
                continue
            
            # Reset retry count if requested
            if retry_data.reset_retry_count:
                command.retry_count = 0
            
            # Reset status to pending
            command.status = CommandStatus.PENDING
            command.sent_at = None
            command.delivered_at = None
            command.executed_at = None
            command.failed_at = None
            command.response = None
            command.error_message = None
            
            self.db.commit()
            
            # Re-add to queue
            await self._add_to_queue(command)
            
            retried_commands.append(command)
        
        # Invalidate cache
        await cache_manager.delete_pattern(f"commands:*")
        
        logger.info(
            "Commands retried",
            command_ids=retry_data.command_ids,
            retried_count=len(retried_commands),
            user_id=user_id
        )
        
        return retried_commands
    
    async def cancel_commands(self, cancel_data: CommandCancelRequest, user_id: int) -> List[Command]:
        """Cancel pending commands."""
        cancelled_commands = []
        
        for command_id in cancel_data.command_ids:
            command = await self.get_command(command_id, user_id)
            if not command:
                continue
            
            if command.status not in [CommandStatus.PENDING, CommandStatus.SENT]:
                continue
            
            command.status = CommandStatus.CANCELLED
            command.error_message = cancel_data.reason or "Cancelled by user"
            
            self.db.commit()
            
            # Remove from queue
            await self._remove_from_queue(command)
            
            cancelled_commands.append(command)
        
        # Invalidate cache
        await cache_manager.delete_pattern(f"commands:*")
        
        logger.info(
            "Commands cancelled",
            command_ids=cancel_data.command_ids,
            cancelled_count=len(cancelled_commands),
            user_id=user_id
        )
        
        return cancelled_commands
    
    async def get_command_stats(self, user_id: int) -> Dict[str, Any]:
        """Get command statistics."""
        cache_key = f"command_stats:{user_id}"
        cached_stats = await cache_manager.get(cache_key)
        
        if cached_stats:
            return cached_stats
        
        # Get basic stats
        total_commands = self.db.query(Command).count()
        pending_commands = self.db.query(Command).filter(Command.status == CommandStatus.PENDING).count()
        sent_commands = self.db.query(Command).filter(Command.status == CommandStatus.SENT).count()
        executed_commands = self.db.query(Command).filter(Command.status == CommandStatus.EXECUTED).count()
        failed_commands = self.db.query(Command).filter(Command.status == CommandStatus.FAILED).count()
        cancelled_commands = self.db.query(Command).filter(Command.status == CommandStatus.CANCELLED).count()
        expired_commands = self.db.query(Command).filter(Command.expires_at < datetime.utcnow()).count()
        
        # Priority stats
        low_priority = self.db.query(Command).filter(Command.priority == CommandPriority.LOW).count()
        normal_priority = self.db.query(Command).filter(Command.priority == CommandPriority.NORMAL).count()
        high_priority = self.db.query(Command).filter(Command.priority == CommandPriority.HIGH).count()
        critical_priority = self.db.query(Command).filter(Command.priority == CommandPriority.CRITICAL).count()
        
        # Command type stats
        command_type_stats = {}
        for cmd_type in CommandType:
            count = self.db.query(Command).filter(Command.command_type == cmd_type).count()
            command_type_stats[cmd_type.value] = count
        
        # Device stats
        device_stats = {}
        device_counts = (
            self.db.query(Command.device_id, func.count(Command.id))
            .group_by(Command.device_id)
            .all()
        )
        for device_id, count in device_counts:
            device = self.db.query(Device).filter(Device.id == device_id).first()
            if device:
                device_stats[device.name] = count
        
        # Recent activity
        now = datetime.utcnow()
        commands_last_hour = self.db.query(Command).filter(
            Command.created_at >= now - timedelta(hours=1)
        ).count()
        commands_last_day = self.db.query(Command).filter(
            Command.created_at >= now - timedelta(days=1)
        ).count()
        commands_last_week = self.db.query(Command).filter(
            Command.created_at >= now - timedelta(weeks=1)
        ).count()
        
        stats = {
            "total_commands": total_commands,
            "pending_commands": pending_commands,
            "sent_commands": sent_commands,
            "executed_commands": executed_commands,
            "failed_commands": failed_commands,
            "cancelled_commands": cancelled_commands,
            "expired_commands": expired_commands,
            "low_priority": low_priority,
            "normal_priority": normal_priority,
            "high_priority": high_priority,
            "critical_priority": critical_priority,
            "command_type_stats": command_type_stats,
            "device_stats": device_stats,
            "commands_last_hour": commands_last_hour,
            "commands_last_day": commands_last_day,
            "commands_last_week": commands_last_week
        }
        
        # Cache stats
        await cache_manager.set(cache_key, stats, expire=300)
        
        return stats
    
    async def _add_to_queue(self, command: Command):
        """Add command to execution queue."""
        queue_entry = CommandQueue(
            command_id=command.id,
            priority=command.priority,
            scheduled_at=datetime.utcnow()  # Execute immediately
        )
        
        self.db.add(queue_entry)
        self.db.commit()
        
        # Trigger queue processing
        # await process_command_queue.delay()  # Will be called by Celery beat
    
    async def _remove_from_queue(self, command: Command):
        """Remove command from execution queue."""
        queue_entry = self.db.query(CommandQueue).filter(
            CommandQueue.command_id == command.id
        ).first()
        
        if queue_entry:
            queue_entry.is_active = False
            self.db.commit()
    
    async def _generate_raw_command(self, command: Command) -> str:
        """Generate raw command string based on protocol."""
        device = self.db.query(Device).filter(Device.id == command.device_id).first()
        if not device or not device.protocol:
            return ""
        
        protocol = device.protocol.lower()
        
        if protocol == "suntech":
            return await self._generate_suntech_command(command)
        elif protocol == "osmand":
            return await self._generate_osmand_command(command)
        else:
            return f"{command.command_type.value}"
    
    async def _generate_suntech_command(self, command: Command) -> str:
        """Generate Suntech protocol command."""
        cmd_type = command.command_type
        params = command.parameters or {}
        
        if cmd_type == CommandType.REBOOT:
            return "REBOOT"
        elif cmd_type == CommandType.SETTIME:
            return "SETTIME"
        elif cmd_type == CommandType.SETINTERVAL:
            interval = params.get("interval", 60)
            return f"SETINTERVAL,{interval}"
        elif cmd_type == CommandType.SETOVERSPEED:
            speed_limit = params.get("speed_limit", 80)
            return f"SETOVERSPEED,{speed_limit}"
        elif cmd_type == CommandType.SETGEOFENCE:
            lat = params.get("latitude", 0)
            lon = params.get("longitude", 0)
            radius = params.get("radius", 100)
            return f"SETGEOFENCE,{lat},{lon},{radius}"
        elif cmd_type == CommandType.SETOUTPUT:
            output_id = params.get("output_id", 1)
            state = "ON" if params.get("output_state", False) else "OFF"
            return f"SETOUTPUT,{output_id},{state}"
        else:
            return cmd_type.value
    
    async def _generate_osmand_command(self, command: Command) -> str:
        """Generate OsmAnd protocol command."""
        cmd_type = command.command_type
        params = command.parameters or {}
        
        if cmd_type == CommandType.SET_INTERVAL:
            interval = params.get("interval", 60)
            return f"SET_INTERVAL:{interval}"
        elif cmd_type == CommandType.SET_ACCURACY:
            accuracy = params.get("accuracy", 10)
            return f"SET_ACCURACY:{accuracy}"
        elif cmd_type == CommandType.SET_BATTERY_SAVER:
            enabled = "1" if params.get("battery_saver", False) else "0"
            return f"SET_BATTERY_SAVER:{enabled}"
        elif cmd_type == CommandType.SET_ALARM:
            alarm_type = params.get("alarm_type", "speed")
            enabled = "1" if params.get("alarm_enabled", True) else "0"
            return f"SET_ALARM:{alarm_type}:{enabled}"
        elif cmd_type == CommandType.SET_GEOFENCE:
            lat = params.get("latitude", 0)
            lon = params.get("longitude", 0)
            radius = params.get("radius", 100)
            return f"SET_GEOFENCE:{lat}:{lon}:{radius}"
        elif cmd_type == CommandType.SET_SPEED_LIMIT:
            speed_limit = params.get("speed_limit", 80)
            return f"SET_SPEED_LIMIT:{speed_limit}"
        elif cmd_type == CommandType.SET_ENGINE_STOP:
            return "SET_ENGINE_STOP"
        elif cmd_type == CommandType.SET_ENGINE_START:
            return "SET_ENGINE_START"
        else:
            return cmd_type.value

"""
Celery tasks for command processing and execution.
"""

import asyncio
from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
import structlog

from app.core.celery_app import celery_app
from app.database import get_db
from app.models.command import Command, CommandQueue, CommandStatus, CommandPriority
from app.models.device import Device
from app.services.command_service import CommandService
from app.api.websocket import manager as websocket_manager

logger = structlog.get_logger(__name__)


@celery_app.task(bind=True, max_retries=3)
def process_command_queue(self):
    """Process pending commands in the queue."""
    try:
        db = next(get_db())
        command_service = CommandService(db)
        
        # Get ready commands from queue
        ready_commands = (
            db.query(CommandQueue)
            .filter(CommandQueue.is_active == True)
            .filter(CommandQueue.is_ready_for_execution == True)
            .order_by(
                # Priority order: CRITICAL, HIGH, NORMAL, LOW
                CommandQueue.priority.desc(),
                CommandQueue.queued_at.asc()
            )
            .limit(10)  # Process up to 10 commands at once
            .all()
        )
        
        if not ready_commands:
            logger.info("No commands ready for processing")
            return {"processed": 0, "message": "No commands to process"}
        
        processed_count = 0
        for queue_entry in ready_commands:
            try:
                # Get command
                command = db.query(Command).filter(Command.id == queue_entry.command_id).first()
                if not command:
                    queue_entry.is_active = False
                    continue
                
                # Check if command is still valid
                if command.status != CommandStatus.PENDING:
                    queue_entry.is_active = False
                    continue
                
                if command.is_expired:
                    command.status = CommandStatus.EXPIRED
                    queue_entry.is_active = False
                    db.commit()
                    continue
                
                # Send command to device
                send_command_to_device.delay(command.id)
                
                # Update queue entry
                queue_entry.attempts += 1
                queue_entry.last_attempt_at = datetime.utcnow()
                queue_entry.next_attempt_at = datetime.utcnow() + timedelta(minutes=1)
                
                processed_count += 1
                
                logger.info(
                    "Command queued for execution",
                    command_id=command.id,
                    device_id=command.device_id,
                    command_type=command.command_type,
                    priority=command.priority
                )
                
            except Exception as e:
                logger.error(
                    "Error processing command in queue",
                    command_id=queue_entry.command_id,
                    error=str(e)
                )
                queue_entry.attempts += 1
                queue_entry.last_attempt_at = datetime.utcnow()
                queue_entry.next_attempt_at = datetime.utcnow() + timedelta(minutes=5)
        
        db.commit()
        
        logger.info(
            "Command queue processed",
            processed_count=processed_count,
            total_ready=len(ready_commands)
        )
        
        return {
            "processed": processed_count,
            "message": f"Processed {processed_count} commands"
        }
        
    except Exception as e:
        logger.error(f"Error processing command queue: {e}")
        raise self.retry(countdown=60, exc=e)
    finally:
        db.close()


@celery_app.task(bind=True, max_retries=3)
def send_command_to_device(self, command_id: int):
    """Send command to device via appropriate protocol."""
    try:
        db = next(get_db())
        command_service = CommandService(db)
        
        # Get command
        command = db.query(Command).filter(Command.id == command_id).first()
        if not command:
            logger.error(f"Command {command_id} not found")
            return {"success": False, "message": "Command not found"}
        
        # Get device
        device = db.query(Device).filter(Device.id == command.device_id).first()
        if not device:
            logger.error(f"Device {command.device_id} not found")
            command.status = CommandStatus.FAILED
            command.error_message = "Device not found"
            db.commit()
            return {"success": False, "message": "Device not found"}
        
        # Check if device is online
        if device.status != "online":
            logger.warning(
                f"Device {device.id} is not online, status: {device.status}"
            )
            command.status = CommandStatus.FAILED
            command.error_message = f"Device is {device.status}"
            db.commit()
            return {"success": False, "message": f"Device is {device.status}"}
        
        # Update command status to sent
        command.status = CommandStatus.SENT
        command.sent_at = datetime.utcnow()
        db.commit()
        
        # Send command based on protocol
        protocol = device.protocol.lower() if device.protocol else "unknown"
        
        if protocol == "suntech":
            success = _send_suntech_command(command, device)
        elif protocol == "osmand":
            success = _send_osmand_command(command, device)
        else:
            logger.warning(f"Unknown protocol: {protocol}")
            command.status = CommandStatus.FAILED
            command.error_message = f"Unknown protocol: {protocol}"
            db.commit()
            return {"success": False, "message": f"Unknown protocol: {protocol}"}
        
        if success:
            command.status = CommandStatus.DELIVERED
            command.delivered_at = datetime.utcnow()
            logger.info(
                "Command sent successfully",
                command_id=command.id,
                device_id=device.id,
                protocol=protocol
            )
        else:
            command.status = CommandStatus.FAILED
            command.error_message = "Failed to send command to device"
            logger.error(
                "Failed to send command",
                command_id=command.id,
                device_id=device.id,
                protocol=protocol
            )
        
        db.commit()
        
        # Broadcast command status update via WebSocket
        _broadcast_command_update(command)
        
        return {
            "success": success,
            "message": "Command sent" if success else "Failed to send command"
        }
        
    except Exception as e:
        logger.error(f"Error sending command {command_id}: {e}")
        
        # Update command status to failed
        try:
            command = db.query(Command).filter(Command.id == command_id).first()
            if command:
                command.status = CommandStatus.FAILED
                command.error_message = str(e)
                command.retry_count += 1
                db.commit()
        except:
            pass
        
        raise self.retry(countdown=60, exc=e)
    finally:
        db.close()


@celery_app.task(bind=True, max_retries=3)
def check_command_timeouts(self):
    """Check for timed out commands and update their status."""
    try:
        db = next(get_db())
        
        # Find commands that have been sent but not responded to within timeout
        timeout_threshold = datetime.utcnow() - timedelta(minutes=5)
        
        timed_out_commands = (
            db.query(Command)
            .filter(Command.status == CommandStatus.SENT)
            .filter(Command.sent_at < timeout_threshold)
            .all()
        )
        
        updated_count = 0
        for command in timed_out_commands:
            # Check if command can be retried
            if command.can_retry:
                command.status = CommandStatus.PENDING
                command.retry_count += 1
                command.sent_at = None
                
                # Re-add to queue
                queue_entry = (
                    db.query(CommandQueue)
                    .filter(CommandQueue.command_id == command.id)
                    .first()
                )
                if queue_entry:
                    queue_entry.is_active = True
                    queue_entry.next_attempt_at = datetime.utcnow() + timedelta(minutes=2)
                
                logger.info(
                    "Command retry scheduled",
                    command_id=command.id,
                    retry_count=command.retry_count
                )
            else:
                command.status = CommandStatus.TIMEOUT
                command.failed_at = datetime.utcnow()
                command.error_message = "Command timed out"
                
                # Remove from queue
                queue_entry = (
                    db.query(CommandQueue)
                    .filter(CommandQueue.command_id == command.id)
                    .first()
                )
                if queue_entry:
                    queue_entry.is_active = False
                
                logger.warning(
                    "Command timed out",
                    command_id=command.id,
                    device_id=command.device_id
                )
            
            updated_count += 1
        
        db.commit()
        
        logger.info(
            "Command timeout check completed",
            timed_out_count=len(timed_out_commands),
            updated_count=updated_count
        )
        
        return {
            "checked": len(timed_out_commands),
            "updated": updated_count,
            "message": f"Checked {len(timed_out_commands)} commands, updated {updated_count}"
        }
        
    except Exception as e:
        logger.error(f"Error checking command timeouts: {e}")
        raise self.retry(countdown=300, exc=e)
    finally:
        db.close()


@celery_app.task(bind=True, max_retries=3)
def cleanup_expired_commands(self):
    """Clean up expired commands and old queue entries."""
    try:
        db = next(get_db())
        
        # Clean up expired commands
        expired_commands = (
            db.query(Command)
            .filter(Command.expires_at < datetime.utcnow())
            .filter(Command.status == CommandStatus.PENDING)
            .all()
        )
        
        expired_count = 0
        for command in expired_commands:
            command.status = CommandStatus.EXPIRED
            command.failed_at = datetime.utcnow()
            command.error_message = "Command expired"
            
            # Remove from queue
            queue_entry = (
                db.query(CommandQueue)
                .filter(CommandQueue.command_id == command.id)
                .first()
            )
            if queue_entry:
                queue_entry.is_active = False
            
            expired_count += 1
        
        # Clean up old queue entries (older than 7 days)
        old_queue_entries = (
            db.query(CommandQueue)
            .filter(CommandQueue.created_at < datetime.utcnow() - timedelta(days=7))
            .filter(CommandQueue.is_active == False)
            .all()
        )
        
        old_count = 0
        for queue_entry in old_queue_entries:
            db.delete(queue_entry)
            old_count += 1
        
        # Clean up old completed commands (older than 30 days)
        old_commands = (
            db.query(Command)
            .filter(Command.created_at < datetime.utcnow() - timedelta(days=30))
            .filter(Command.status.in_([
                CommandStatus.EXECUTED,
                CommandStatus.FAILED,
                CommandStatus.CANCELLED,
                CommandStatus.EXPIRED
            ]))
            .all()
        )
        
        old_commands_count = 0
        for command in old_commands:
            db.delete(command)
            old_commands_count += 1
        
        db.commit()
        
        logger.info(
            "Command cleanup completed",
            expired_commands=expired_count,
            old_queue_entries=old_count,
            old_commands=old_commands_count
        )
        
        return {
            "expired_commands": expired_count,
            "old_queue_entries": old_count,
            "old_commands": old_commands_count,
            "message": f"Cleaned up {expired_count} expired commands, {old_count} old queue entries, {old_commands_count} old commands"
        }
        
    except Exception as e:
        logger.error(f"Error cleaning up commands: {e}")
        raise self.retry(countdown=3600, exc=e)
    finally:
        db.close()


def _send_suntech_command(command: Command, device: Device) -> bool:
    """Send command to Suntech device."""
    try:
        # This would integrate with the actual Suntech protocol server
        # For now, we'll simulate the command sending
        
        logger.info(
            "Sending Suntech command",
            command_id=command.id,
            device_id=device.id,
            raw_command=command.raw_command
        )
        
        # Simulate command sending
        # In real implementation, this would send the command via TCP/UDP
        # to the device through the protocol server
        
        return True
        
    except Exception as e:
        logger.error(f"Error sending Suntech command: {e}")
        return False


def _send_osmand_command(command: Command, device: Device) -> bool:
    """Send command to OsmAnd device."""
    try:
        # This would integrate with the actual OsmAnd protocol server
        # For now, we'll simulate the command sending
        
        logger.info(
            "Sending OsmAnd command",
            command_id=command.id,
            device_id=device.id,
            raw_command=command.raw_command
        )
        
        # Simulate command sending
        # In real implementation, this would send the command via HTTP
        # to the device through the protocol server
        
        return True
        
    except Exception as e:
        logger.error(f"Error sending OsmAnd command: {e}")
        return False


def _broadcast_command_update(command: Command):
    """Broadcast command status update via WebSocket."""
    try:
        # Get device and user information
        db = next(get_db())
        device = db.query(Device).filter(Device.id == command.device_id).first()
        
        if device:
            # Broadcast to device-specific channel
            # Note: In real implementation, this would be async
            # await websocket_manager.broadcast_to_device(...)
            pass
            
            # Broadcast to user-specific channel  
            # Note: In real implementation, this would be async
            # await websocket_manager.broadcast_to_user(...)
            pass
        
    except Exception as e:
        logger.error(f"Error broadcasting command update: {e}")
    finally:
        db.close()

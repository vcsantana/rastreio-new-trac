"""
Position processing background tasks
"""
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
import structlog
from celery import current_task
from app.core.celery_app import celery_app
from app.database import get_db
from app.models.position import Position
from app.models.device import Device
from app.models.event import Event
from app.core.cache import cache_manager, invalidate_device_cache
from app.api.websocket import manager as websocket_manager
from sqlalchemy import select, update, and_, func
from sqlalchemy.orm import selectinload

logger = structlog.get_logger(__name__)


@celery_app.task(bind=True, name="app.tasks.position_tasks.process_position_batch")
def process_position_batch(self, position_data: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Process a batch of positions in background
    
    Args:
        position_data: List of position data dictionaries
    
    Returns:
        Processing results
    """
    try:
        logger.info("Starting position batch processing", 
                   task_id=self.request.id, 
                   batch_size=len(position_data))
        
        processed_count = 0
        error_count = 0
        device_updates = {}
        
        db = next(get_db())
        
        for position_dict in position_data:
            try:
                # Process individual position
                result = _process_single_position(db, position_dict)
                if result["success"]:
                    processed_count += 1
                    device_id = result["device_id"]
                    if device_id not in device_updates:
                        device_updates[device_id] = 0
                    device_updates[device_id] += 1
                else:
                    error_count += 1
                    logger.warning("Position processing failed", 
                                 error=result["error"], 
                                 position=position_dict)
                    
            except Exception as e:
                error_count += 1
                logger.error("Position processing exception", 
                           error=str(e), 
                           position=position_dict)
        
        # Update device last positions
        for device_id, count in device_updates.items():
            try:
                _update_device_last_position(db, device_id)
                # Invalidate device cache
                invalidate_device_cache(device_id)
            except Exception as e:
                logger.error("Failed to update device last position", 
                           device_id=device_id, error=str(e))
        
        # Broadcast updates via WebSocket
        try:
            _broadcast_position_updates(device_updates)
        except Exception as e:
            logger.error("Failed to broadcast position updates", error=str(e))
        
        result = {
            "task_id": self.request.id,
            "processed_count": processed_count,
            "error_count": error_count,
            "device_updates": device_updates,
            "timestamp": datetime.utcnow().isoformat()
        }
        
        logger.info("Position batch processing completed", **result)
        return result
        
    except Exception as e:
        logger.error("Position batch processing failed", 
                   task_id=self.request.id, 
                   error=str(e))
        raise


@celery_app.task(bind=True, name="app.tasks.position_tasks.process_single_position")
def process_single_position(self, position_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Process a single position in background
    
    Args:
        position_data: Position data dictionary
    
    Returns:
        Processing result
    """
    try:
        logger.info("Processing single position", 
                   task_id=self.request.id, 
                   device_id=position_data.get("device_id"))
        
        db = next(get_db())
        result = _process_single_position(db, position_data)
        
        if result["success"]:
            # Update device last position
            _update_device_last_position(db, result["device_id"])
            # Invalidate device cache
            invalidate_device_cache(result["device_id"])
            # Broadcast update
            _broadcast_position_updates({result["device_id"]: 1})
        
        logger.info("Single position processing completed", 
                   task_id=self.request.id, 
                   success=result["success"])
        
        return result
        
    except Exception as e:
        logger.error("Single position processing failed", 
                   task_id=self.request.id, 
                   error=str(e))
        raise


@celery_app.task(bind=True, name="app.tasks.position_tasks.calculate_device_statistics")
def calculate_device_statistics(self, device_id: int) -> Dict[str, Any]:
    """
    Calculate statistics for a device
    
    Args:
        device_id: Device ID
    
    Returns:
        Device statistics
    """
    try:
        logger.info("Calculating device statistics", 
                   task_id=self.request.id, 
                   device_id=device_id)
        
        db = next(get_db())
        
        # Get device
        device = db.execute(
            select(Device).where(Device.id == device_id)
        ).scalar_one_or_none()
        
        if not device:
            return {"error": "Device not found", "device_id": device_id}
        
        # Calculate statistics for last 24 hours
        since = datetime.utcnow() - timedelta(hours=24)
        
        # Get position count
        position_count = db.execute(
            select(Position).where(
                and_(
                    Position.device_id == device_id,
                    Position.fix_time >= since
                )
            )
        ).scalars().count()
        
        # Get event count
        event_count = db.execute(
            select(Event).where(
                and_(
                    Event.device_id == device_id,
                    Event.event_time >= since
                )
            )
        ).scalars().count()
        
        # Get last position
        last_position = db.execute(
            select(Position)
            .where(Position.device_id == device_id)
            .order_by(Position.fix_time.desc())
            .limit(1)
        ).scalar_one_or_none()
        
        # Calculate distance traveled (simplified)
        distance_traveled = 0.0
        if last_position:
            # This is a simplified calculation
            # In a real implementation, you'd calculate actual distance
            distance_traveled = 0.0
        
        statistics = {
            "device_id": device_id,
            "position_count_24h": position_count,
            "event_count_24h": event_count,
            "distance_traveled_24h": distance_traveled,
            "last_position_time": last_position.fix_time.isoformat() if last_position else None,
            "calculated_at": datetime.utcnow().isoformat()
        }
        
        # Cache statistics
        cache_key = f"device_stats:{device_id}"
        cache_manager.set(cache_key, statistics, expire=3600)  # 1 hour
        
        logger.info("Device statistics calculated", 
                   task_id=self.request.id, 
                   device_id=device_id,
                   **statistics)
        
        return statistics
        
    except Exception as e:
        logger.error("Device statistics calculation failed", 
                   task_id=self.request.id, 
                   device_id=device_id,
                   error=str(e))
        raise


@celery_app.task(bind=True, name="app.tasks.position_tasks.update_device_status")
def update_device_status(self, device_id: int) -> Dict[str, Any]:
    """
    Update device online/offline status based on last position
    
    Args:
        device_id: Device ID
    
    Returns:
        Status update result
    """
    try:
        logger.info("Updating device status", 
                   task_id=self.request.id, 
                   device_id=device_id)
        
        db = next(get_db())
        
        # Get device
        device = db.execute(
            select(Device).where(Device.id == device_id)
        ).scalar_one_or_none()
        
        if not device:
            return {"error": "Device not found", "device_id": device_id}
        
        # Get last position
        last_position = db.execute(
            select(Position)
            .where(Position.device_id == device_id)
            .order_by(Position.fix_time.desc())
            .limit(1)
        ).scalar_one_or_none()
        
        # Determine if device is online (last position within 5 minutes)
        is_online = False
        if last_position:
            time_diff = datetime.utcnow() - last_position.fix_time
            is_online = time_diff.total_seconds() < 300  # 5 minutes
        
        # Update device status
        old_status = device.status
        device.status = "online" if is_online else "offline"
        device.last_update = datetime.utcnow()
        
        db.commit()
        
        # Invalidate device cache
        invalidate_device_cache(device_id)
        
        # Broadcast status change if it changed
        if old_status != device.status:
            _broadcast_device_status_change(device_id, device.status)
        
        result = {
            "device_id": device_id,
            "old_status": old_status,
            "new_status": device.status,
            "is_online": is_online,
            "last_position_time": last_position.fix_time.isoformat() if last_position else None,
            "updated_at": datetime.utcnow().isoformat()
        }
        
        logger.info("Device status updated", 
                   task_id=self.request.id, 
                   **result)
        
        return result
        
    except Exception as e:
        logger.error("Device status update failed", 
                   task_id=self.request.id, 
                   device_id=device_id,
                   error=str(e))
        raise


# Helper functions
def _process_single_position(db, position_data: Dict[str, Any]) -> Dict[str, Any]:
    """Process a single position and save to database"""
    try:
        # Create position object
        position = Position(**position_data)
        
        # Save to database
        db.add(position)
        db.commit()
        db.refresh(position)
        
        return {
            "success": True,
            "position_id": position.id,
            "device_id": position.device_id
        }
        
    except Exception as e:
        db.rollback()
        return {
            "success": False,
            "error": str(e)
        }


def _update_device_last_position(db, device_id: int):
    """Update device's last position"""
    try:
        # Get last position for device
        last_position = db.execute(
            select(Position)
            .where(Position.device_id == device_id)
            .order_by(Position.fix_time.desc())
            .limit(1)
        ).scalar_one_or_none()
        
        if last_position:
            # Update device with last position info
            db.execute(
                update(Device)
                .where(Device.id == device_id)
                .values(
                    last_position_id=last_position.id,
                    last_update=datetime.utcnow()
                )
            )
            db.commit()
            
    except Exception as e:
        logger.error("Failed to update device last position", 
                   device_id=device_id, error=str(e))


def _broadcast_position_updates(device_updates: Dict[int, int]):
    """Broadcast position updates via WebSocket"""
    try:
        for device_id, count in device_updates.items():
            message = {
                "type": "position_update",
                "device_id": device_id,
                "position_count": count,
                "timestamp": datetime.utcnow().isoformat()
            }
            # Note: This would need to be called in an async context
            # For now, we'll just log the broadcast
            logger.info("Position update broadcast", device_id=device_id, count=count)
            
    except Exception as e:
        logger.error("Failed to broadcast position updates", error=str(e))


def _broadcast_device_status_change(device_id: int, status: str):
    """Broadcast device status change via WebSocket"""
    try:
        message = {
            "type": "device_status_change",
            "device_id": device_id,
            "status": status,
            "timestamp": datetime.utcnow().isoformat()
        }
        # Note: This would need to be called in an async context
        # For now, we'll just log the broadcast
        logger.info("Device status change broadcast", device_id=device_id, status=status)
        
    except Exception as e:
        logger.error("Failed to broadcast device status change", 
                   device_id=device_id, error=str(e))

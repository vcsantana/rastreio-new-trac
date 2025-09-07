"""
Data cleanup background tasks
"""
from typing import Dict, Any, Optional
from datetime import datetime, timedelta
import structlog
from celery import current_task
from app.core.celery_app import celery_app
from app.database import get_db
from app.models.position import Position
from app.models.event import Event
from app.models.device import Device
from app.core.cache import cache_manager
from app.core.session import session_manager
from sqlalchemy import select, delete, and_, func, text
from sqlalchemy.orm import selectinload

logger = structlog.get_logger(__name__)


@celery_app.task(bind=True, name="app.tasks.cleanup_tasks.cleanup_old_positions")
def cleanup_old_positions(self, days_to_keep: int = 30) -> Dict[str, Any]:
    """
    Clean up old position data
    
    Args:
        days_to_keep: Number of days to keep position data
    
    Returns:
        Cleanup results
    """
    try:
        logger.info("Starting old positions cleanup", 
                   task_id=self.request.id, 
                   days_to_keep=days_to_keep)
        
        db = next(get_db())
        
        # Calculate cutoff date
        cutoff_date = datetime.utcnow() - timedelta(days=days_to_keep)
        
        # Count positions to be deleted
        count_to_delete = db.execute(
            select(func.count(Position.id))
            .where(Position.fix_time < cutoff_date)
        ).scalar()
        
        # Delete old positions
        deleted_count = db.execute(
            delete(Position)
            .where(Position.fix_time < cutoff_date)
        ).rowcount
        
        db.commit()
        
        result = {
            "task_id": self.request.id,
            "cutoff_date": cutoff_date.isoformat(),
            "positions_to_delete": count_to_delete,
            "positions_deleted": deleted_count,
            "cleanup_completed_at": datetime.utcnow().isoformat()
        }
        
        logger.info("Old positions cleanup completed", **result)
        return result
        
    except Exception as e:
        logger.error("Old positions cleanup failed", 
                   task_id=self.request.id, 
                   error=str(e))
        db.rollback()
        raise


@celery_app.task(bind=True, name="app.tasks.cleanup_tasks.cleanup_old_events")
def cleanup_old_events(self, days_to_keep: int = 90) -> Dict[str, Any]:
    """
    Clean up old event data
    
    Args:
        days_to_keep: Number of days to keep event data
    
    Returns:
        Cleanup results
    """
    try:
        logger.info("Starting old events cleanup", 
                   task_id=self.request.id, 
                   days_to_keep=days_to_keep)
        
        db = next(get_db())
        
        # Calculate cutoff date
        cutoff_date = datetime.utcnow() - timedelta(days=days_to_keep)
        
        # Count events to be deleted
        count_to_delete = db.execute(
            select(func.count(Event.id))
            .where(Event.event_time < cutoff_date)
        ).scalar()
        
        # Delete old events
        deleted_count = db.execute(
            delete(Event)
            .where(Event.event_time < cutoff_date)
        ).rowcount
        
        db.commit()
        
        result = {
            "task_id": self.request.id,
            "cutoff_date": cutoff_date.isoformat(),
            "events_to_delete": count_to_delete,
            "events_deleted": deleted_count,
            "cleanup_completed_at": datetime.utcnow().isoformat()
        }
        
        logger.info("Old events cleanup completed", **result)
        return result
        
    except Exception as e:
        logger.error("Old events cleanup failed", 
                   task_id=self.request.id, 
                   error=str(e))
        db.rollback()
        raise


@celery_app.task(bind=True, name="app.tasks.cleanup_tasks.cleanup_expired_sessions")
def cleanup_expired_sessions(self) -> Dict[str, Any]:
    """
    Clean up expired sessions from Redis
    
    Returns:
        Cleanup results
    """
    try:
        logger.info("Starting expired sessions cleanup", task_id=self.request.id)
        
        # Get session statistics before cleanup
        stats_before = session_manager.get_session_stats()
        
        # Clean up expired sessions
        cleaned_count = session_manager.cleanup_expired_sessions()
        
        # Get session statistics after cleanup
        stats_after = session_manager.get_session_stats()
        
        result = {
            "task_id": self.request.id,
            "sessions_cleaned": cleaned_count,
            "stats_before": stats_before,
            "stats_after": stats_after,
            "cleanup_completed_at": datetime.utcnow().isoformat()
        }
        
        logger.info("Expired sessions cleanup completed", **result)
        return result
        
    except Exception as e:
        logger.error("Expired sessions cleanup failed", 
                   task_id=self.request.id, 
                   error=str(e))
        raise


@celery_app.task(bind=True, name="app.tasks.cleanup_tasks.cleanup_cache")
def cleanup_cache(self, pattern: str = "*", max_age_hours: int = 24) -> Dict[str, Any]:
    """
    Clean up old cache entries
    
    Args:
        pattern: Cache key pattern to clean
        max_age_hours: Maximum age of cache entries in hours
    
    Returns:
        Cleanup results
    """
    try:
        logger.info("Starting cache cleanup", 
                   task_id=self.request.id, 
                   pattern=pattern,
                   max_age_hours=max_age_hours)
        
        # Get cache statistics before cleanup
        stats_before = cache_manager.get_stats()
        
        # Clean up cache entries
        cleaned_count = cache_manager.clear_pattern(pattern)
        
        # Get cache statistics after cleanup
        stats_after = cache_manager.get_stats()
        
        result = {
            "task_id": self.request.id,
            "pattern": pattern,
            "max_age_hours": max_age_hours,
            "cache_entries_cleaned": cleaned_count,
            "stats_before": stats_before,
            "stats_after": stats_after,
            "cleanup_completed_at": datetime.utcnow().isoformat()
        }
        
        logger.info("Cache cleanup completed", **result)
        return result
        
    except Exception as e:
        logger.error("Cache cleanup failed", 
                   task_id=self.request.id, 
                   error=str(e))
        raise


@celery_app.task(bind=True, name="app.tasks.cleanup_tasks.cleanup_duplicate_positions")
def cleanup_duplicate_positions(self, device_id: Optional[int] = None) -> Dict[str, Any]:
    """
    Clean up duplicate positions
    
    Args:
        device_id: Optional device ID to clean (if None, clean all devices)
    
    Returns:
        Cleanup results
    """
    try:
        logger.info("Starting duplicate positions cleanup", 
                   task_id=self.request.id, 
                   device_id=device_id)
        
        db = next(get_db())
        
        # Find duplicate positions (same device, same time, same location)
        if device_id:
            duplicates_query = select(
                Position.device_id,
                Position.fix_time,
                Position.latitude,
                Position.longitude,
                func.count(Position.id).label('count')
            ).where(
                Position.device_id == device_id
            ).group_by(
                Position.device_id,
                Position.fix_time,
                Position.latitude,
                Position.longitude
            ).having(
                func.count(Position.id) > 1
            )
        else:
            duplicates_query = select(
                Position.device_id,
                Position.fix_time,
                Position.latitude,
                Position.longitude,
                func.count(Position.id).label('count')
            ).group_by(
                Position.device_id,
                Position.fix_time,
                Position.latitude,
                Position.longitude
            ).having(
                func.count(Position.id) > 1
            )
        
        duplicates = db.execute(duplicates_query).all()
        
        total_duplicates = 0
        cleaned_duplicates = 0
        
        for duplicate in duplicates:
            device_id, fix_time, lat, lon, count = duplicate
            total_duplicates += count - 1  # Keep one, delete the rest
            
            # Delete duplicate positions (keep the first one)
            positions_to_delete = db.execute(
                select(Position.id)
                .where(
                    and_(
                        Position.device_id == device_id,
                        Position.fix_time == fix_time,
                        Position.latitude == lat,
                        Position.longitude == lon
                    )
                )
                .order_by(Position.id.asc())
                .offset(1)  # Skip the first one
            ).scalars().all()
            
            if positions_to_delete:
                deleted_count = db.execute(
                    delete(Position)
                    .where(Position.id.in_(positions_to_delete))
                ).rowcount
                cleaned_duplicates += deleted_count
        
        db.commit()
        
        result = {
            "task_id": self.request.id,
            "device_id": device_id,
            "duplicate_groups": len(duplicates),
            "total_duplicates": total_duplicates,
            "duplicates_cleaned": cleaned_duplicates,
            "cleanup_completed_at": datetime.utcnow().isoformat()
        }
        
        logger.info("Duplicate positions cleanup completed", **result)
        return result
        
    except Exception as e:
        logger.error("Duplicate positions cleanup failed", 
                   task_id=self.request.id, 
                   error=str(e))
        db.rollback()
        raise


@celery_app.task(bind=True, name="app.tasks.cleanup_tasks.cleanup_orphaned_data")
def cleanup_orphaned_data(self) -> Dict[str, Any]:
    """
    Clean up orphaned data (positions without devices, events without devices, etc.)
    
    Returns:
        Cleanup results
    """
    try:
        logger.info("Starting orphaned data cleanup", task_id=self.request.id)
        
        db = next(get_db())
        
        # Clean up positions without devices
        orphaned_positions = db.execute(
            delete(Position)
            .where(
                ~Position.device_id.in_(
                    select(Device.id)
                )
            )
        ).rowcount
        
        # Clean up events without devices
        orphaned_events = db.execute(
            delete(Event)
            .where(
                ~Event.device_id.in_(
                    select(Device.id)
                )
            )
        ).rowcount
        
        db.commit()
        
        result = {
            "task_id": self.request.id,
            "orphaned_positions_cleaned": orphaned_positions,
            "orphaned_events_cleaned": orphaned_events,
            "cleanup_completed_at": datetime.utcnow().isoformat()
        }
        
        logger.info("Orphaned data cleanup completed", **result)
        return result
        
    except Exception as e:
        logger.error("Orphaned data cleanup failed", 
                   task_id=self.request.id, 
                   error=str(e))
        db.rollback()
        raise


@celery_app.task(bind=True, name="app.tasks.cleanup_tasks.optimize_database")
def optimize_database(self) -> Dict[str, Any]:
    """
    Optimize database (vacuum, analyze, etc.)
    
    Returns:
        Optimization results
    """
    try:
        logger.info("Starting database optimization", task_id=self.request.id)
        
        db = next(get_db())
        
        # Get database size before optimization
        size_before = db.execute(
            text("SELECT pg_size_pretty(pg_database_size(current_database()))")
        ).scalar()
        
        # Analyze tables
        db.execute(text("ANALYZE"))
        
        # Vacuum tables
        db.execute(text("VACUUM"))
        
        # Get database size after optimization
        size_after = db.execute(
            text("SELECT pg_size_pretty(pg_database_size(current_database()))")
        ).scalar()
        
        result = {
            "task_id": self.request.id,
            "size_before": size_before,
            "size_after": size_after,
            "optimization_completed_at": datetime.utcnow().isoformat()
        }
        
        logger.info("Database optimization completed", **result)
        return result
        
    except Exception as e:
        logger.error("Database optimization failed", 
                   task_id=self.request.id, 
                   error=str(e))
        raise

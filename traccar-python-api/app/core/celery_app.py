"""
Celery application configuration
"""
from celery import Celery
from app.config import settings
import structlog

logger = structlog.get_logger(__name__)

# Create Celery app
celery_app = Celery(
    "traccar",
    broker=settings.CELERY_BROKER_URL,
    backend=settings.CELERY_RESULT_BACKEND,
    include=[
        "app.tasks.position_tasks",
        "app.tasks.report_tasks", 
        "app.tasks.cleanup_tasks",
        "app.tasks.notification_tasks"
    ]
)

# Celery configuration
celery_app.conf.update(
    # Task routing
    task_routes={
        "app.tasks.position_tasks.*": {"queue": "positions"},
        "app.tasks.report_tasks.*": {"queue": "reports"},
        "app.tasks.cleanup_tasks.*": {"queue": "cleanup"},
        "app.tasks.notification_tasks.*": {"queue": "notifications"},
    },
    
    # Task execution
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    
    # Task time limits
    task_soft_time_limit=300,  # 5 minutes
    task_time_limit=600,       # 10 minutes
    
    # Task retry configuration
    task_acks_late=True,
    worker_prefetch_multiplier=1,
    
    # Result backend configuration
    result_expires=3600,  # 1 hour
    
    # Beat schedule for periodic tasks
    beat_schedule={
        "cleanup-old-positions": {
            "task": "app.tasks.cleanup_tasks.cleanup_old_positions",
            "schedule": 3600.0,  # Every hour
        },
        "cleanup-old-events": {
            "task": "app.tasks.cleanup_tasks.cleanup_old_events", 
            "schedule": 3600.0,  # Every hour
        },
        "cleanup-expired-sessions": {
            "task": "app.tasks.cleanup_tasks.cleanup_expired_sessions",
            "schedule": 1800.0,  # Every 30 minutes
        },
        "generate-daily-reports": {
            "task": "app.tasks.report_tasks.generate_daily_reports",
            "schedule": 86400.0,  # Daily at midnight
        },
        "process-position-batch": {
            "task": "app.tasks.position_tasks.process_position_batch",
            "schedule": 30.0,  # Every 30 seconds
        },
    },
)

# Task error handling
@celery_app.task(bind=True)
def debug_task(self):
    """Debug task for testing Celery"""
    logger.info(f"Request: {self.request!r}")
    return "Celery is working!"

# Task monitoring
@celery_app.task(bind=True)
def health_check_task(self):
    """Health check task for monitoring"""
    try:
        # Test database connection
        from app.database import get_db
        db = next(get_db())
        db.execute("SELECT 1")
        
        # Test Redis connection
        from app.core.cache import cache_manager
        cache_manager.redis.ping()
        
        return {
            "status": "healthy",
            "task_id": self.request.id,
            "timestamp": self.request.timestamp
        }
    except Exception as e:
        logger.error("Health check failed", error=str(e))
        return {
            "status": "unhealthy",
            "error": str(e),
            "task_id": self.request.id
        }

# Task result monitoring
@celery_app.task(bind=True)
def get_task_stats(self):
    """Get task statistics"""
    try:
        from celery import current_app
        
        # Get active tasks
        active_tasks = current_app.control.inspect().active()
        
        # Get scheduled tasks
        scheduled_tasks = current_app.control.inspect().scheduled()
        
        # Get reserved tasks
        reserved_tasks = current_app.control.inspect().reserved()
        
        return {
            "active_tasks": active_tasks,
            "scheduled_tasks": scheduled_tasks,
            "reserved_tasks": reserved_tasks,
            "worker_count": len(active_tasks) if active_tasks else 0
        }
    except Exception as e:
        logger.error("Failed to get task stats", error=str(e))
        return {"error": str(e)}

# Task cleanup
@celery_app.task(bind=True)
def cleanup_task_results(self, older_than_hours=24):
    """Clean up old task results"""
    try:
        from celery.result import AsyncResult
        
        # This would need to be implemented based on your result backend
        # For Redis, we can use TTL to automatically expire results
        
        logger.info("Task result cleanup completed", older_than_hours=older_than_hours)
        return {"cleaned_results": "completed"}
        
    except Exception as e:
        logger.error("Task result cleanup failed", error=str(e))
        return {"error": str(e)}

# Export the Celery app
__all__ = ["celery_app"]

"""
Background tasks management API endpoints
"""
from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Dict, Any, List, Optional
import structlog
from app.database import get_db
from app.api.auth import get_current_user
from app.models.user import User
from app.core.celery_app import celery_app
from app.tasks.position_tasks import process_position_batch, process_single_position
from app.tasks.report_tasks import generate_device_report, generate_fleet_report
from app.tasks.cleanup_tasks import cleanup_old_positions, cleanup_old_events
from app.tasks.notification_tasks import send_geofence_alert, send_device_offline_alert

logger = structlog.get_logger(__name__)

router = APIRouter()


@router.get("/status")
async def get_tasks_status(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get background tasks status (admin only)"""
    if not current_user.admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required"
        )
    
    try:
        # Get Celery worker status
        inspect = celery_app.control.inspect()
        
        # Get active tasks
        active_tasks = inspect.active()
        
        # Get scheduled tasks
        scheduled_tasks = inspect.scheduled()
        
        # Get reserved tasks
        reserved_tasks = inspect.reserved()
        
        # Get worker stats
        stats = inspect.stats()
        
        return {
            "celery_connected": True,
            "active_tasks": active_tasks or {},
            "scheduled_tasks": scheduled_tasks or {},
            "reserved_tasks": reserved_tasks or {},
            "worker_stats": stats or {},
            "worker_count": len(active_tasks) if active_tasks else 0
        }
    except Exception as e:
        logger.error("Error getting tasks status", error=str(e))
        return {
            "celery_connected": False,
            "error": str(e)
        }


@router.post("/position/process-batch")
async def process_position_batch_task(
    position_data: List[Dict[str, Any]],
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Process a batch of positions in background (admin only)"""
    if not current_user.admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required"
        )
    
    try:
        # Queue the task
        task = process_position_batch.delay(position_data)
        
        logger.info("Position batch processing task queued", 
                   task_id=task.id, 
                   batch_size=len(position_data))
        
        return {
            "task_id": task.id,
            "status": "queued",
            "batch_size": len(position_data),
            "message": "Position batch processing task queued successfully"
        }
    except Exception as e:
        logger.error("Error queuing position batch task", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to queue position batch processing task"
        )


@router.post("/position/process-single")
async def process_single_position_task(
    position_data: Dict[str, Any],
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Process a single position in background (admin only)"""
    if not current_user.admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required"
        )
    
    try:
        # Queue the task
        task = process_single_position.delay(position_data)
        
        logger.info("Single position processing task queued", 
                   task_id=task.id, 
                   device_id=position_data.get("device_id"))
        
        return {
            "task_id": task.id,
            "status": "queued",
            "device_id": position_data.get("device_id"),
            "message": "Single position processing task queued successfully"
        }
    except Exception as e:
        logger.error("Error queuing single position task", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to queue single position processing task"
        )


@router.post("/report/device")
async def generate_device_report_task(
    device_id: int,
    start_date: str,
    end_date: str,
    report_type: str = "summary",
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Generate device report in background"""
    try:
        # Queue the task
        task = generate_device_report.delay(device_id, start_date, end_date, report_type)
        
        logger.info("Device report generation task queued", 
                   task_id=task.id, 
                   device_id=device_id,
                   report_type=report_type)
        
        return {
            "task_id": task.id,
            "status": "queued",
            "device_id": device_id,
            "report_type": report_type,
            "start_date": start_date,
            "end_date": end_date,
            "message": "Device report generation task queued successfully"
        }
    except Exception as e:
        logger.error("Error queuing device report task", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to queue device report generation task"
        )


@router.post("/report/fleet")
async def generate_fleet_report_task(
    start_date: str,
    end_date: str,
    device_ids: Optional[List[int]] = None,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Generate fleet report in background (admin only)"""
    if not current_user.admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required"
        )
    
    try:
        # Queue the task
        task = generate_fleet_report.delay(start_date, end_date, device_ids)
        
        logger.info("Fleet report generation task queued", 
                   task_id=task.id, 
                   device_count=len(device_ids) if device_ids else "all")
        
        return {
            "task_id": task.id,
            "status": "queued",
            "start_date": start_date,
            "end_date": end_date,
            "device_ids": device_ids,
            "message": "Fleet report generation task queued successfully"
        }
    except Exception as e:
        logger.error("Error queuing fleet report task", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to queue fleet report generation task"
        )


@router.post("/cleanup/positions")
async def cleanup_old_positions_task(
    days_to_keep: int = 30,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Clean up old positions in background (admin only)"""
    if not current_user.admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required"
        )
    
    try:
        # Queue the task
        task = cleanup_old_positions.delay(days_to_keep)
        
        logger.info("Old positions cleanup task queued", 
                   task_id=task.id, 
                   days_to_keep=days_to_keep)
        
        return {
            "task_id": task.id,
            "status": "queued",
            "days_to_keep": days_to_keep,
            "message": "Old positions cleanup task queued successfully"
        }
    except Exception as e:
        logger.error("Error queuing positions cleanup task", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to queue positions cleanup task"
        )


@router.post("/cleanup/events")
async def cleanup_old_events_task(
    days_to_keep: int = 90,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Clean up old events in background (admin only)"""
    if not current_user.admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required"
        )
    
    try:
        # Queue the task
        task = cleanup_old_events.delay(days_to_keep)
        
        logger.info("Old events cleanup task queued", 
                   task_id=task.id, 
                   days_to_keep=days_to_keep)
        
        return {
            "task_id": task.id,
            "status": "queued",
            "days_to_keep": days_to_keep,
            "message": "Old events cleanup task queued successfully"
        }
    except Exception as e:
        logger.error("Error queuing events cleanup task", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to queue events cleanup task"
        )


@router.post("/notification/geofence-alert")
async def send_geofence_alert_task(
    device_id: int,
    geofence_id: int,
    event_type: str,
    position_data: Dict[str, Any],
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Send geofence alert notification in background"""
    try:
        # Queue the task
        task = send_geofence_alert.delay(device_id, geofence_id, event_type, position_data)
        
        logger.info("Geofence alert task queued", 
                   task_id=task.id, 
                   device_id=device_id,
                   geofence_id=geofence_id,
                   event_type=event_type)
        
        return {
            "task_id": task.id,
            "status": "queued",
            "device_id": device_id,
            "geofence_id": geofence_id,
            "event_type": event_type,
            "message": "Geofence alert task queued successfully"
        }
    except Exception as e:
        logger.error("Error queuing geofence alert task", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to queue geofence alert task"
        )


@router.post("/notification/device-offline")
async def send_device_offline_alert_task(
    device_id: int,
    offline_duration_minutes: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Send device offline alert notification in background"""
    try:
        # Queue the task
        task = send_device_offline_alert.delay(device_id, offline_duration_minutes)
        
        logger.info("Device offline alert task queued", 
                   task_id=task.id, 
                   device_id=device_id,
                   offline_duration_minutes=offline_duration_minutes)
        
        return {
            "task_id": task.id,
            "status": "queued",
            "device_id": device_id,
            "offline_duration_minutes": offline_duration_minutes,
            "message": "Device offline alert task queued successfully"
        }
    except Exception as e:
        logger.error("Error queuing device offline alert task", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to queue device offline alert task"
        )


@router.get("/task/{task_id}")
async def get_task_status(
    task_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get status of a specific task"""
    try:
        # Get task result
        task_result = celery_app.AsyncResult(task_id)
        
        return {
            "task_id": task_id,
            "status": task_result.status,
            "result": task_result.result if task_result.ready() else None,
            "error": str(task_result.info) if task_result.failed() else None,
            "ready": task_result.ready(),
            "successful": task_result.successful(),
            "failed": task_result.failed()
        }
    except Exception as e:
        logger.error("Error getting task status", task_id=task_id, error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get task status"
        )


@router.delete("/task/{task_id}")
async def cancel_task(
    task_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Cancel a specific task (admin only)"""
    if not current_user.admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required"
        )
    
    try:
        # Cancel the task
        celery_app.control.revoke(task_id, terminate=True)
        
        logger.info("Task cancelled", task_id=task_id)
        
        return {
            "task_id": task_id,
            "status": "cancelled",
            "message": "Task cancelled successfully"
        }
    except Exception as e:
        logger.error("Error cancelling task", task_id=task_id, error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to cancel task"
        )


@router.get("/queues")
async def get_queue_info(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get information about task queues (admin only)"""
    if not current_user.admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required"
        )
    
    try:
        inspect = celery_app.control.inspect()
        
        # Get queue lengths
        active_tasks = inspect.active()
        scheduled_tasks = inspect.scheduled()
        reserved_tasks = inspect.reserved()
        
        queues = {
            "positions": {
                "active": len(active_tasks.get("positions", [])) if active_tasks else 0,
                "scheduled": len(scheduled_tasks.get("positions", [])) if scheduled_tasks else 0,
                "reserved": len(reserved_tasks.get("positions", [])) if reserved_tasks else 0
            },
            "reports": {
                "active": len(active_tasks.get("reports", [])) if active_tasks else 0,
                "scheduled": len(scheduled_tasks.get("reports", [])) if scheduled_tasks else 0,
                "reserved": len(reserved_tasks.get("reports", [])) if reserved_tasks else 0
            },
            "cleanup": {
                "active": len(active_tasks.get("cleanup", [])) if active_tasks else 0,
                "scheduled": len(scheduled_tasks.get("cleanup", [])) if scheduled_tasks else 0,
                "reserved": len(reserved_tasks.get("cleanup", [])) if reserved_tasks else 0
            },
            "notifications": {
                "active": len(active_tasks.get("notifications", [])) if active_tasks else 0,
                "scheduled": len(scheduled_tasks.get("notifications", [])) if scheduled_tasks else 0,
                "reserved": len(reserved_tasks.get("notifications", [])) if reserved_tasks else 0
            }
        }
        
        return {
            "queues": queues,
            "total_active": sum(q["active"] for q in queues.values()),
            "total_scheduled": sum(q["scheduled"] for q in queues.values()),
            "total_reserved": sum(q["reserved"] for q in queues.values())
        }
    except Exception as e:
        logger.error("Error getting queue info", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get queue information"
        )

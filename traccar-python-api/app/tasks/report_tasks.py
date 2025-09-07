"""
Report generation background tasks
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
from app.models.report import Report
from app.core.cache import cache_manager
from sqlalchemy import select, and_, func, text
from sqlalchemy.orm import selectinload
import json

logger = structlog.get_logger(__name__)


@celery_app.task(bind=True, name="app.tasks.report_tasks.generate_daily_reports")
def generate_daily_reports(self) -> Dict[str, Any]:
    """
    Generate daily reports for all devices
    
    Returns:
        Report generation results
    """
    try:
        logger.info("Starting daily report generation", task_id=self.request.id)
        
        db = next(get_db())
        generated_reports = []
        error_count = 0
        
        # Get all active devices
        devices = db.execute(
            select(Device).where(Device.disabled == False)
        ).scalars().all()
        
        for device in devices:
            try:
                report_data = _generate_device_daily_report(db, device.id)
                if report_data:
                    generated_reports.append(report_data)
                    
            except Exception as e:
                error_count += 1
                logger.error("Failed to generate daily report for device", 
                           device_id=device.id, error=str(e))
        
        result = {
            "task_id": self.request.id,
            "generated_reports": len(generated_reports),
            "error_count": error_count,
            "reports": generated_reports,
            "timestamp": datetime.utcnow().isoformat()
        }
        
        logger.info("Daily report generation completed", **result)
        return result
        
    except Exception as e:
        logger.error("Daily report generation failed", 
                   task_id=self.request.id, 
                   error=str(e))
        raise


@celery_app.task(bind=True, name="app.tasks.report_tasks.generate_device_report")
def generate_device_report(self, device_id: int, start_date: str, end_date: str, 
                          report_type: str = "summary") -> Dict[str, Any]:
    """
    Generate a report for a specific device
    
    Args:
        device_id: Device ID
        start_date: Start date (ISO format)
        end_date: End date (ISO format)
        report_type: Type of report (summary, detailed, route)
    
    Returns:
        Generated report data
    """
    try:
        logger.info("Generating device report", 
                   task_id=self.request.id, 
                   device_id=device_id,
                   start_date=start_date,
                   end_date=end_date,
                   report_type=report_type)
        
        db = next(get_db())
        
        # Parse dates
        start_dt = datetime.fromisoformat(start_date.replace('Z', '+00:00'))
        end_dt = datetime.fromisoformat(end_date.replace('Z', '+00:00'))
        
        # Get device
        device = db.execute(
            select(Device).where(Device.id == device_id)
        ).scalar_one_or_none()
        
        if not device:
            return {"error": "Device not found", "device_id": device_id}
        
        # Generate report based on type
        if report_type == "summary":
            report_data = _generate_summary_report(db, device_id, start_dt, end_dt)
        elif report_type == "detailed":
            report_data = _generate_detailed_report(db, device_id, start_dt, end_dt)
        elif report_type == "route":
            report_data = _generate_route_report(db, device_id, start_dt, end_dt)
        else:
            return {"error": "Invalid report type", "report_type": report_type}
        
        # Save report to database
        report = Report(
            device_id=device_id,
            report_type=report_type,
            start_date=start_dt,
            end_date=end_dt,
            data=json.dumps(report_data),
            generated_at=datetime.utcnow()
        )
        
        db.add(report)
        db.commit()
        db.refresh(report)
        
        result = {
            "task_id": self.request.id,
            "report_id": report.id,
            "device_id": device_id,
            "report_type": report_type,
            "start_date": start_date,
            "end_date": end_date,
            "data": report_data,
            "generated_at": datetime.utcnow().isoformat()
        }
        
        logger.info("Device report generated", 
                   task_id=self.request.id, 
                   report_id=report.id,
                   device_id=device_id)
        
        return result
        
    except Exception as e:
        logger.error("Device report generation failed", 
                   task_id=self.request.id, 
                   device_id=device_id,
                   error=str(e))
        raise


@celery_app.task(bind=True, name="app.tasks.report_tasks.generate_fleet_report")
def generate_fleet_report(self, start_date: str, end_date: str, 
                         device_ids: Optional[List[int]] = None) -> Dict[str, Any]:
    """
    Generate a fleet-wide report
    
    Args:
        start_date: Start date (ISO format)
        end_date: End date (ISO format)
        device_ids: Optional list of device IDs to include
    
    Returns:
        Generated fleet report data
    """
    try:
        logger.info("Generating fleet report", 
                   task_id=self.request.id, 
                   start_date=start_date,
                   end_date=end_date,
                   device_count=len(device_ids) if device_ids else "all")
        
        db = next(get_db())
        
        # Parse dates
        start_dt = datetime.fromisoformat(start_date.replace('Z', '+00:00'))
        end_dt = datetime.fromisoformat(end_date.replace('Z', '+00:00'))
        
        # Get devices
        if device_ids:
            devices = db.execute(
                select(Device).where(Device.id.in_(device_ids))
            ).scalars().all()
        else:
            devices = db.execute(
                select(Device).where(Device.disabled == False)
            ).scalars().all()
        
        fleet_data = {
            "fleet_summary": {},
            "device_reports": [],
            "total_devices": len(devices),
            "start_date": start_date,
            "end_date": end_date,
            "generated_at": datetime.utcnow().isoformat()
        }
        
        total_positions = 0
        total_events = 0
        total_distance = 0.0
        
        for device in devices:
            try:
                device_report = _generate_summary_report(db, device.id, start_dt, end_dt)
                fleet_data["device_reports"].append({
                    "device_id": device.id,
                    "device_name": device.name,
                    "report": device_report
                })
                
                total_positions += device_report.get("position_count", 0)
                total_events += device_report.get("event_count", 0)
                total_distance += device_report.get("distance_traveled", 0.0)
                
            except Exception as e:
                logger.error("Failed to generate device report for fleet", 
                           device_id=device.id, error=str(e))
        
        fleet_data["fleet_summary"] = {
            "total_positions": total_positions,
            "total_events": total_events,
            "total_distance": total_distance,
            "average_positions_per_device": total_positions / len(devices) if devices else 0,
            "average_events_per_device": total_events / len(devices) if devices else 0
        }
        
        result = {
            "task_id": self.request.id,
            "fleet_data": fleet_data,
            "timestamp": datetime.utcnow().isoformat()
        }
        
        logger.info("Fleet report generated", 
                   task_id=self.request.id, 
                   device_count=len(devices),
                   total_positions=total_positions)
        
        return result
        
    except Exception as e:
        logger.error("Fleet report generation failed", 
                   task_id=self.request.id, 
                   error=str(e))
        raise


@celery_app.task(bind=True, name="app.tasks.report_tasks.export_report_data")
def export_report_data(self, report_id: int, export_format: str = "json") -> Dict[str, Any]:
    """
    Export report data in various formats
    
    Args:
        report_id: Report ID
        export_format: Export format (json, csv, xlsx)
    
    Returns:
        Export result
    """
    try:
        logger.info("Exporting report data", 
                   task_id=self.request.id, 
                   report_id=report_id,
                   export_format=export_format)
        
        db = next(get_db())
        
        # Get report
        report = db.execute(
            select(Report).where(Report.id == report_id)
        ).scalar_one_or_none()
        
        if not report:
            return {"error": "Report not found", "report_id": report_id}
        
        # Parse report data
        report_data = json.loads(report.data) if isinstance(report.data, str) else report.data
        
        # Export based on format
        if export_format == "json":
            export_data = report_data
        elif export_format == "csv":
            export_data = _convert_to_csv(report_data)
        elif export_format == "xlsx":
            export_data = _convert_to_xlsx(report_data)
        else:
            return {"error": "Invalid export format", "export_format": export_format}
        
        result = {
            "task_id": self.request.id,
            "report_id": report_id,
            "export_format": export_format,
            "export_data": export_data,
            "exported_at": datetime.utcnow().isoformat()
        }
        
        logger.info("Report data exported", 
                   task_id=self.request.id, 
                   report_id=report_id,
                   export_format=export_format)
        
        return result
        
    except Exception as e:
        logger.error("Report data export failed", 
                   task_id=self.request.id, 
                   report_id=report_id,
                   error=str(e))
        raise


# Helper functions
def _generate_device_daily_report(db, device_id: int) -> Optional[Dict[str, Any]]:
    """Generate daily report for a device"""
    try:
        # Get yesterday's data
        yesterday = datetime.utcnow().date() - timedelta(days=1)
        start_dt = datetime.combine(yesterday, datetime.min.time())
        end_dt = datetime.combine(yesterday, datetime.max.time())
        
        return _generate_summary_report(db, device_id, start_dt, end_dt)
        
    except Exception as e:
        logger.error("Failed to generate daily report", 
                   device_id=device_id, error=str(e))
        return None


def _generate_summary_report(db, device_id: int, start_dt: datetime, end_dt: datetime) -> Dict[str, Any]:
    """Generate summary report for a device"""
    try:
        # Get position count
        position_count = db.execute(
            select(func.count(Position.id))
            .where(
                and_(
                    Position.device_id == device_id,
                    Position.fix_time >= start_dt,
                    Position.fix_time <= end_dt
                )
            )
        ).scalar()
        
        # Get event count
        event_count = db.execute(
            select(func.count(Event.id))
            .where(
                and_(
                    Event.device_id == device_id,
                    Event.event_time >= start_dt,
                    Event.event_time <= end_dt
                )
            )
        ).scalar()
        
        # Get first and last positions
        first_position = db.execute(
            select(Position)
            .where(
                and_(
                    Position.device_id == device_id,
                    Position.fix_time >= start_dt,
                    Position.fix_time <= end_dt
                )
            )
            .order_by(Position.fix_time.asc())
            .limit(1)
        ).scalar_one_or_none()
        
        last_position = db.execute(
            select(Position)
            .where(
                and_(
                    Position.device_id == device_id,
                    Position.fix_time >= start_dt,
                    Position.fix_time <= end_dt
                )
            )
            .order_by(Position.fix_time.desc())
            .limit(1)
        ).scalar_one_or_none()
        
        # Calculate distance (simplified)
        distance_traveled = 0.0
        if first_position and last_position:
            # This is a simplified calculation
            # In a real implementation, you'd calculate actual distance
            distance_traveled = 0.0
        
        return {
            "device_id": device_id,
            "start_date": start_dt.isoformat(),
            "end_date": end_dt.isoformat(),
            "position_count": position_count,
            "event_count": event_count,
            "distance_traveled": distance_traveled,
            "first_position": {
                "latitude": first_position.latitude,
                "longitude": first_position.longitude,
                "time": first_position.fix_time.isoformat()
            } if first_position else None,
            "last_position": {
                "latitude": last_position.latitude,
                "longitude": last_position.longitude,
                "time": last_position.fix_time.isoformat()
            } if last_position else None
        }
        
    except Exception as e:
        logger.error("Failed to generate summary report", 
                   device_id=device_id, error=str(e))
        return {}


def _generate_detailed_report(db, device_id: int, start_dt: datetime, end_dt: datetime) -> Dict[str, Any]:
    """Generate detailed report for a device"""
    try:
        # Get all positions
        positions = db.execute(
            select(Position)
            .where(
                and_(
                    Position.device_id == device_id,
                    Position.fix_time >= start_dt,
                    Position.fix_time <= end_dt
                )
            )
            .order_by(Position.fix_time.asc())
        ).scalars().all()
        
        # Get all events
        events = db.execute(
            select(Event)
            .where(
                and_(
                    Event.device_id == device_id,
                    Event.event_time >= start_dt,
                    Event.event_time <= end_dt
                )
            )
            .order_by(Event.event_time.asc())
        ).scalars().all()
        
        return {
            "device_id": device_id,
            "start_date": start_dt.isoformat(),
            "end_date": end_dt.isoformat(),
            "positions": [
                {
                    "id": pos.id,
                    "latitude": pos.latitude,
                    "longitude": pos.longitude,
                    "altitude": pos.altitude,
                    "speed": pos.speed,
                    "course": pos.course,
                    "fix_time": pos.fix_time.isoformat()
                }
                for pos in positions
            ],
            "events": [
                {
                    "id": event.id,
                    "type": event.type,
                    "event_time": event.event_time.isoformat(),
                    "attributes": event.attributes
                }
                for event in events
            ]
        }
        
    except Exception as e:
        logger.error("Failed to generate detailed report", 
                   device_id=device_id, error=str(e))
        return {}


def _generate_route_report(db, device_id: int, start_dt: datetime, end_dt: datetime) -> Dict[str, Any]:
    """Generate route report for a device"""
    try:
        # Get positions for route
        positions = db.execute(
            select(Position)
            .where(
                and_(
                    Position.device_id == device_id,
                    Position.fix_time >= start_dt,
                    Position.fix_time <= end_dt
                )
            )
            .order_by(Position.fix_time.asc())
        ).scalars().all()
        
        # Calculate route statistics
        route_points = []
        total_distance = 0.0
        max_speed = 0.0
        
        for pos in positions:
            route_points.append({
                "latitude": pos.latitude,
                "longitude": pos.longitude,
                "altitude": pos.altitude,
                "speed": pos.speed,
                "course": pos.course,
                "fix_time": pos.fix_time.isoformat()
            })
            
            if pos.speed and pos.speed > max_speed:
                max_speed = pos.speed
        
        return {
            "device_id": device_id,
            "start_date": start_dt.isoformat(),
            "end_date": end_dt.isoformat(),
            "route_points": route_points,
            "total_points": len(route_points),
            "total_distance": total_distance,
            "max_speed": max_speed,
            "duration_hours": (end_dt - start_dt).total_seconds() / 3600
        }
        
    except Exception as e:
        logger.error("Failed to generate route report", 
                   device_id=device_id, error=str(e))
        return {}


def _convert_to_csv(data: Dict[str, Any]) -> str:
    """Convert report data to CSV format"""
    # This is a simplified CSV conversion
    # In a real implementation, you'd use a proper CSV library
    return json.dumps(data)


def _convert_to_xlsx(data: Dict[str, Any]) -> bytes:
    """Convert report data to XLSX format"""
    # This is a placeholder for XLSX conversion
    # In a real implementation, you'd use openpyxl or similar
    return json.dumps(data).encode()

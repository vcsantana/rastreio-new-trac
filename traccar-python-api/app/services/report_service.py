"""
Report generation service.
"""

import asyncio
import json
import csv
import io
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Union
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, func, desc

from app.models import Device, Position, Event, Report, ReportTemplate
from app.schemas.report import (
    ReportType, ReportFormat, ReportPeriod,
    RouteReportData, SummaryReportData, EventsReportData,
    StopsReportData, TripsReportData
)
from app.services.websocket_service import websocket_service
from app.services.report_providers import ReportProviderFactory

import logging
logger = logging.getLogger(__name__)


class ReportGenerator:
    """Report generator service."""
    
    def __init__(self, db: Session):
        self.db = db
    
    async def generate_report(self, report: Report) -> Dict[str, Any]:
        """Generate report based on type using specialized providers."""
        try:
            # Update report status
            report.status = "processing"
            self.db.commit()
            
            # Create appropriate provider
            provider = ReportProviderFactory.create_provider(report.report_type, self.db)
            
            # Generate report data
            report_data = await provider.generate_report(report)
            
            # Parse JSON data for response
            data = json.loads(report_data.decode('utf-8'))
            
            # Format and save report
            file_path = await self._save_report(report, report_data)
            
            # Update report status
            report.status = "completed"
            report.completed_at = datetime.utcnow()
            report.file_path = file_path
            report.file_size = len(report_data)
            self.db.commit()
            
            # Broadcast completion via WebSocket
            await websocket_service.broadcast_system_notification(
                f"Report '{report.name}' completed successfully",
                "success",
                report.user_id
            )
            
            return data
            
        except Exception as e:
            logger.error(f"Error generating report {report.id}: {e}")
            
            # Update report status
            report.status = "failed"
            report.error_message = str(e)
            self.db.commit()
            
            # Broadcast error via WebSocket
            await websocket_service.broadcast_system_notification(
                f"Report '{report.name}' failed: {str(e)}",
                "error",
                report.user_id
            )
            
            raise
    
    def _get_date_range(self, period: str, from_date: Optional[datetime], to_date: Optional[datetime]) -> tuple:
        """Get date range based on period."""
        now = datetime.utcnow()
        
        if period == ReportPeriod.TODAY:
            start = now.replace(hour=0, minute=0, second=0, microsecond=0)
            end = now
        elif period == ReportPeriod.YESTERDAY:
            yesterday = now - timedelta(days=1)
            start = yesterday.replace(hour=0, minute=0, second=0, microsecond=0)
            end = yesterday.replace(hour=23, minute=59, second=59, microsecond=999999)
        elif period == ReportPeriod.THIS_WEEK:
            start = now - timedelta(days=now.weekday())
            start = start.replace(hour=0, minute=0, second=0, microsecond=0)
            end = now
        elif period == ReportPeriod.LAST_WEEK:
            start = now - timedelta(days=now.weekday() + 7)
            start = start.replace(hour=0, minute=0, second=0, microsecond=0)
            end = start + timedelta(days=6, hours=23, minutes=59, seconds=59)
        elif period == ReportPeriod.THIS_MONTH:
            start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
            end = now
        elif period == ReportPeriod.LAST_MONTH:
            if now.month == 1:
                start = now.replace(year=now.year-1, month=12, day=1, hour=0, minute=0, second=0, microsecond=0)
            else:
                start = now.replace(month=now.month-1, day=1, hour=0, minute=0, second=0, microsecond=0)
            end = start.replace(day=1) - timedelta(microseconds=1)
        elif period == ReportPeriod.THIS_YEAR:
            start = now.replace(month=1, day=1, hour=0, minute=0, second=0, microsecond=0)
            end = now
        elif period == ReportPeriod.LAST_YEAR:
            start = now.replace(year=now.year-1, month=1, day=1, hour=0, minute=0, second=0, microsecond=0)
            end = now.replace(year=now.year-1, month=12, day=31, hour=23, minute=59, second=59, microsecond=999999)
        else:  # CUSTOM
            start = from_date or now - timedelta(days=1)
            end = to_date or now
        
        return start, end
    
    async def _generate_route_report(self, report: Report, from_date: datetime, to_date: datetime) -> Dict[str, Any]:
        """Generate route report."""
        devices = self._get_devices(report.device_ids)
        report_data = []
        
        for device in devices:
            positions = self.db.query(Position).filter(
                and_(
                    Position.device_id == device.id,
                    Position.device_time >= from_date,
                    Position.device_time <= to_date,
                    Position.valid == True
                )
            ).order_by(Position.device_time).all()
            
            if not positions:
                continue
            
            # Calculate route statistics
            total_distance = 0
            total_time = 0
            max_speed = 0
            speeds = []
            
            for i in range(1, len(positions)):
                prev_pos = positions[i-1]
                curr_pos = positions[i]
                
                # Calculate distance (simplified)
                distance = self._calculate_distance(
                    prev_pos.latitude, prev_pos.longitude,
                    curr_pos.latitude, curr_pos.longitude
                )
                total_distance += distance
                
                # Calculate time difference
                time_diff = (curr_pos.device_time - prev_pos.device_time).total_seconds()
                total_time += time_diff
                
                # Track speeds
                if curr_pos.speed and curr_pos.speed > 0:
                    speeds.append(curr_pos.speed)
                    max_speed = max(max_speed, curr_pos.speed)
            
            avg_speed = sum(speeds) / len(speeds) if speeds else 0
            
            # Prepare position data
            position_data = []
            for pos in positions:
                pos_dict = {
                    "latitude": float(pos.latitude),
                    "longitude": float(pos.longitude),
                    "altitude": float(pos.altitude) if pos.altitude else 0,
                    "speed": float(pos.speed) if pos.speed else 0,
                    "course": float(pos.course) if pos.course else 0,
                    "device_time": pos.device_time.isoformat(),
                    "address": pos.address
                }
                if report.include_attributes and pos.attributes:
                    pos_dict["attributes"] = pos.attributes
                position_data.append(pos_dict)
            
            device_data = {
                "device_id": device.id,
                "device_name": device.name,
                "positions": position_data,
                "total_distance": round(total_distance, 2),
                "total_time": int(total_time),
                "max_speed": round(max_speed, 2),
                "avg_speed": round(avg_speed, 2),
                "start_time": positions[0].device_time.isoformat(),
                "end_time": positions[-1].device_time.isoformat(),
                "start_address": positions[0].address,
                "end_address": positions[-1].address
            }
            
            report_data.append(device_data)
        
        return {
            "report_type": "route",
            "period_start": from_date.isoformat(),
            "period_end": to_date.isoformat(),
            "devices": report_data,
            "total_devices": len(report_data)
        }
    
    async def _generate_summary_report(self, report: Report, from_date: datetime, to_date: datetime) -> Dict[str, Any]:
        """Generate summary report."""
        devices = self._get_devices(report.device_ids)
        report_data = []
        
        for device in devices:
            positions = self.db.query(Position).filter(
                and_(
                    Position.device_id == device.id,
                    Position.device_time >= from_date,
                    Position.device_time <= to_date,
                    Position.valid == True
                )
            ).all()
            
            if not positions:
                continue
            
            # Calculate summary statistics
            total_distance = 0
            total_time = 0
            max_speed = 0
            speeds = []
            idle_time = 0
            driving_time = 0
            
            for i in range(1, len(positions)):
                prev_pos = positions[i-1]
                curr_pos = positions[i]
                
                distance = self._calculate_distance(
                    prev_pos.latitude, prev_pos.longitude,
                    curr_pos.latitude, curr_pos.longitude
                )
                total_distance += distance
                
                time_diff = (curr_pos.device_time - prev_pos.device_time).total_seconds()
                total_time += time_diff
                
                if curr_pos.speed and curr_pos.speed > 0:
                    speeds.append(curr_pos.speed)
                    max_speed = max(max_speed, curr_pos.speed)
                    driving_time += time_diff
                else:
                    idle_time += time_diff
            
            avg_speed = sum(speeds) / len(speeds) if speeds else 0
            
            # Count events and stops
            events_count = self.db.query(Event).filter(
                and_(
                    Event.device_id == device.id,
                    Event.event_time >= from_date,
                    Event.event_time <= to_date
                )
            ).count()
            
            stops_count = self.db.query(Event).filter(
                and_(
                    Event.device_id == device.id,
                    Event.event_time >= from_date,
                    Event.event_time <= to_date,
                    Event.type == "deviceStop"
                )
            ).count()
            
            device_data = {
                "device_id": device.id,
                "device_name": device.name,
                "total_distance": round(total_distance, 2),
                "total_time": int(total_time),
                "max_speed": round(max_speed, 2),
                "avg_speed": round(avg_speed, 2),
                "idle_time": int(idle_time),
                "driving_time": int(driving_time),
                "stops_count": stops_count,
                "events_count": events_count,
                "period_start": from_date.isoformat(),
                "period_end": to_date.isoformat()
            }
            
            report_data.append(device_data)
        
        return {
            "report_type": "summary",
            "period_start": from_date.isoformat(),
            "period_end": to_date.isoformat(),
            "devices": report_data,
            "total_devices": len(report_data)
        }
    
    async def _generate_events_report(self, report: Report, from_date: datetime, to_date: datetime) -> Dict[str, Any]:
        """Generate events report."""
        devices = self._get_devices(report.device_ids)
        report_data = []
        
        for device in devices:
            events = self.db.query(Event).filter(
                and_(
                    Event.device_id == device.id,
                    Event.event_time >= from_date,
                    Event.event_time <= to_date
                )
            ).order_by(Event.event_time).all()
            
            # Group events by type
            events_by_type = {}
            event_data = []
            
            for event in events:
                event_dict = {
                    "id": event.id,
                    "type": event.type,
                    "event_time": event.event_time.isoformat(),
                    "server_time": event.server_time.isoformat(),
                    "position_id": event.position_id,
                    "geofence_id": event.geofence_id
                }
                
                if report.include_attributes and event.attributes:
                    event_dict["attributes"] = event.attributes
                
                event_data.append(event_dict)
                
                # Count by type
                events_by_type[event.type] = events_by_type.get(event.type, 0) + 1
            
            device_data = {
                "device_id": device.id,
                "device_name": device.name,
                "events": event_data,
                "events_by_type": events_by_type,
                "total_events": len(events),
                "period_start": from_date.isoformat(),
                "period_end": to_date.isoformat()
            }
            
            report_data.append(device_data)
        
        return {
            "report_type": "events",
            "period_start": from_date.isoformat(),
            "period_end": to_date.isoformat(),
            "devices": report_data,
            "total_devices": len(report_data)
        }
    
    async def _generate_stops_report(self, report: Report, from_date: datetime, to_date: datetime) -> Dict[str, Any]:
        """Generate stops report."""
        devices = self._get_devices(report.device_ids)
        report_data = []
        
        for device in devices:
            # Get stop events
            stop_events = self.db.query(Event).filter(
                and_(
                    Event.device_id == device.id,
                    Event.event_time >= from_date,
                    Event.event_time <= to_date,
                    Event.type == "deviceStop"
                )
            ).order_by(Event.event_time).all()
            
            stops = []
            total_stop_time = 0
            longest_stop = None
            
            for event in stop_events:
                # Get position for this stop
                position = self.db.query(Position).filter(Position.id == event.position_id).first()
                
                stop_data = {
                    "id": event.id,
                    "start_time": event.event_time.isoformat(),
                    "latitude": float(position.latitude) if position else None,
                    "longitude": float(position.longitude) if position else None,
                    "address": position.address if position else None
                }
                
                if report.include_attributes and event.attributes:
                    stop_data["attributes"] = event.attributes
                
                stops.append(stop_data)
            
            device_data = {
                "device_id": device.id,
                "device_name": device.name,
                "stops": stops,
                "total_stops": len(stops),
                "total_stop_time": total_stop_time,
                "longest_stop": longest_stop,
                "period_start": from_date.isoformat(),
                "period_end": to_date.isoformat()
            }
            
            report_data.append(device_data)
        
        return {
            "report_type": "stops",
            "period_start": from_date.isoformat(),
            "period_end": to_date.isoformat(),
            "devices": report_data,
            "total_devices": len(report_data)
        }
    
    async def _generate_trips_report(self, report: Report, from_date: datetime, to_date: datetime) -> Dict[str, Any]:
        """Generate trips report."""
        devices = self._get_devices(report.device_ids)
        report_data = []
        
        for device in devices:
            # Get trip events (deviceStart/deviceStop pairs)
            trip_events = self.db.query(Event).filter(
                and_(
                    Event.device_id == device.id,
                    Event.event_time >= from_date,
                    Event.event_time <= to_date,
                    or_(Event.type == "deviceStart", Event.type == "deviceStop")
                )
            ).order_by(Event.event_time).all()
            
            trips = []
            total_distance = 0
            total_time = 0
            
            # Process trip pairs
            start_event = None
            for event in trip_events:
                if event.type == "deviceStart":
                    start_event = event
                elif event.type == "deviceStop" and start_event:
                    # Calculate trip
                    trip_time = (event.event_time - start_event.event_time).total_seconds()
                    total_time += trip_time
                    
                    trip_data = {
                        "start_time": start_event.event_time.isoformat(),
                        "end_time": event.event_time.isoformat(),
                        "duration": int(trip_time),
                        "start_position_id": start_event.position_id,
                        "end_position_id": event.position_id
                    }
                    
                    trips.append(trip_data)
                    start_event = None
            
            device_data = {
                "device_id": device.id,
                "device_name": device.name,
                "trips": trips,
                "total_trips": len(trips),
                "total_distance": round(total_distance, 2),
                "total_time": int(total_time),
                "period_start": from_date.isoformat(),
                "period_end": to_date.isoformat()
            }
            
            report_data.append(device_data)
        
        return {
            "report_type": "trips",
            "period_start": from_date.isoformat(),
            "period_end": to_date.isoformat(),
            "devices": report_data,
            "total_devices": len(report_data)
        }
    
    def _get_devices(self, device_ids: Optional[List[int]]) -> List[Device]:
        """Get devices for report."""
        if device_ids:
            return self.db.query(Device).filter(Device.id.in_(device_ids)).all()
        else:
            return self.db.query(Device).all()
    
    def _calculate_distance(self, lat1: float, lon1: float, lat2: float, lon2: float) -> float:
        """Calculate distance between two points (simplified)."""
        # Simplified distance calculation (not accurate for long distances)
        import math
        R = 6371000  # Earth radius in meters
        
        lat1_rad = math.radians(lat1)
        lat2_rad = math.radians(lat2)
        delta_lat = math.radians(lat2 - lat1)
        delta_lon = math.radians(lon2 - lon1)
        
        a = (math.sin(delta_lat / 2) ** 2 + 
             math.cos(lat1_rad) * math.cos(lat2_rad) * math.sin(delta_lon / 2) ** 2)
        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
        
        return R * c / 1000  # Convert to kilometers
    
    async def _save_report(self, report: Report, data: bytes) -> str:
        """Save report to file."""
        # In a real implementation, this would save to actual files
        # For now, just return a mock file path
        timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        filename = f"report_{report.id}_{timestamp}.{report.format}"
        return f"/reports/{filename}"


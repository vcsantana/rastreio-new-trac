"""
Specialized report providers for different report types.
"""

import asyncio
import json
import csv
import io
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Union, BinaryIO
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, func, desc
import logging

from app.models import Device, Position, Event, Report, ReportTemplate
from app.schemas.report import (
    ReportType, ReportFormat, ReportPeriod,
    RouteReportData, SummaryReportData, EventsReportData,
    StopsReportData, TripsReportData
)

logger = logging.getLogger(__name__)


class ReportProvider:
    """Base class for report providers."""
    
    def __init__(self, db: Session):
        self.db = db
    
    async def generate_report(self, report: Report) -> bytes:
        """Generate report data."""
        raise NotImplementedError("Subclasses must implement generate_report")
    
    def _get_devices(self, device_ids: Optional[List[int]]) -> List[Device]:
        """Get devices for report."""
        if device_ids:
            return self.db.query(Device).filter(Device.id.in_(device_ids)).all()
        else:
            return self.db.query(Device).all()
    
    def _get_date_range(self, report: Report) -> tuple:
        """Get date range based on report period."""
        now = datetime.utcnow()
        
        if report.period == ReportPeriod.TODAY:
            start = now.replace(hour=0, minute=0, second=0, microsecond=0)
            end = now
        elif report.period == ReportPeriod.YESTERDAY:
            yesterday = now - timedelta(days=1)
            start = yesterday.replace(hour=0, minute=0, second=0, microsecond=0)
            end = yesterday.replace(hour=23, minute=59, second=59, microsecond=999999)
        elif report.period == ReportPeriod.THIS_WEEK:
            start = now - timedelta(days=now.weekday())
            start = start.replace(hour=0, minute=0, second=0, microsecond=0)
            end = now
        elif report.period == ReportPeriod.LAST_WEEK:
            start = now - timedelta(days=now.weekday() + 7)
            start = start.replace(hour=0, minute=0, second=0, microsecond=0)
            end = start + timedelta(days=6, hours=23, minutes=59, seconds=59)
        elif report.period == ReportPeriod.THIS_MONTH:
            start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
            end = now
        elif report.period == ReportPeriod.LAST_MONTH:
            if now.month == 1:
                start = now.replace(year=now.year-1, month=12, day=1, hour=0, minute=0, second=0, microsecond=0)
            else:
                start = now.replace(month=now.month-1, day=1, hour=0, minute=0, second=0, microsecond=0)
            end = start.replace(day=1) - timedelta(microseconds=1)
        elif report.period == ReportPeriod.THIS_YEAR:
            start = now.replace(month=1, day=1, hour=0, minute=0, second=0, microsecond=0)
            end = now
        elif report.period == ReportPeriod.LAST_YEAR:
            start = now.replace(year=now.year-1, month=1, day=1, hour=0, minute=0, second=0, microsecond=0)
            end = now.replace(year=now.year-1, month=12, day=31, hour=23, minute=59, second=59, microsecond=999999)
        else:  # CUSTOM
            start = report.from_date or now - timedelta(days=1)
            end = report.to_date or now
        
        return start, end
    
    def _calculate_distance(self, lat1: float, lon1: float, lat2: float, lon2: float) -> float:
        """Calculate distance between two points (simplified)."""
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


class CombinedReportProvider(ReportProvider):
    """Provider for combined reports (multiple report types)."""
    
    async def generate_report(self, report: Report) -> bytes:
        """Generate combined report."""
        try:
            from_date, to_date = self._get_date_range(report)
            devices = self._get_devices(report.device_ids)
            
            # Generate data for each report type
            route_data = await self._generate_route_data(devices, from_date, to_date, report)
            summary_data = await self._generate_summary_data(devices, from_date, to_date, report)
            events_data = await self._generate_events_data(devices, from_date, to_date, report)
            stops_data = await self._generate_stops_data(devices, from_date, to_date, report)
            trips_data = await self._generate_trips_data(devices, from_date, to_date, report)
            
            combined_data = {
                "report_type": "combined",
                "period_start": from_date.isoformat(),
                "period_end": to_date.isoformat(),
                "generated_at": datetime.utcnow().isoformat(),
                "route": route_data,
                "summary": summary_data,
                "events": events_data,
                "stops": stops_data,
                "trips": trips_data,
                "total_devices": len(devices)
            }
            
            return self._format_report(combined_data, report.format)
            
        except Exception as e:
            logger.error(f"Error generating combined report: {e}")
            raise
    
    async def _generate_route_data(self, devices: List[Device], from_date: datetime, to_date: datetime, report: Report) -> Dict[str, Any]:
        """Generate route data."""
        provider = RouteReportProvider(self.db)
        return await provider._generate_route_data(devices, from_date, to_date, report)
    
    async def _generate_summary_data(self, devices: List[Device], from_date: datetime, to_date: datetime, report: Report) -> Dict[str, Any]:
        """Generate summary data."""
        provider = SummaryReportProvider(self.db)
        return await provider._generate_summary_data(devices, from_date, to_date, report)
    
    async def _generate_events_data(self, devices: List[Device], from_date: datetime, to_date: datetime, report: Report) -> Dict[str, Any]:
        """Generate events data."""
        provider = EventsReportProvider(self.db)
        return await provider._generate_events_data(devices, from_date, to_date, report)
    
    async def _generate_stops_data(self, devices: List[Device], from_date: datetime, to_date: datetime, report: Report) -> Dict[str, Any]:
        """Generate stops data."""
        provider = StopsReportProvider(self.db)
        return await provider._generate_stops_data(devices, from_date, to_date, report)
    
    async def _generate_trips_data(self, devices: List[Device], from_date: datetime, to_date: datetime, report: Report) -> Dict[str, Any]:
        """Generate trips data."""
        provider = TripsReportProvider(self.db)
        return await provider._generate_trips_data(devices, from_date, to_date, report)
    
    def _format_report(self, data: Dict[str, Any], format_type: str) -> bytes:
        """Format report data."""
        if format_type == "json":
            return json.dumps(data, indent=2, default=str).encode('utf-8')
        elif format_type == "csv":
            return self._to_csv(data).encode('utf-8')
        else:
            return json.dumps(data, indent=2, default=str).encode('utf-8')
    
    def _to_csv(self, data: Dict[str, Any]) -> str:
        """Convert data to CSV format."""
        output = io.StringIO()
        writer = csv.writer(output)
        
        # Write header
        writer.writerow(['Report Type', 'Period Start', 'Period End', 'Total Devices'])
        writer.writerow([
            data.get('report_type', ''),
            data.get('period_start', ''),
            data.get('period_end', ''),
            data.get('total_devices', 0)
        ])
        
        return output.getvalue()


class RouteReportProvider(ReportProvider):
    """Provider for route reports."""
    
    async def generate_report(self, report: Report) -> bytes:
        """Generate route report."""
        try:
            from_date, to_date = self._get_date_range(report)
            devices = self._get_devices(report.device_ids)
            
            data = await self._generate_route_data(devices, from_date, to_date, report)
            return self._format_report(data, report.format)
            
        except Exception as e:
            logger.error(f"Error generating route report: {e}")
            raise
    
    async def _generate_route_data(self, devices: List[Device], from_date: datetime, to_date: datetime, report: Report) -> Dict[str, Any]:
        """Generate route data."""
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
    
    def _format_report(self, data: Dict[str, Any], format_type: str) -> bytes:
        """Format route report."""
        if format_type == "json":
            return json.dumps(data, indent=2, default=str).encode('utf-8')
        elif format_type == "csv":
            return self._to_csv(data).encode('utf-8')
        else:
            return json.dumps(data, indent=2, default=str).encode('utf-8')
    
    def _to_csv(self, data: Dict[str, Any]) -> str:
        """Convert route data to CSV."""
        output = io.StringIO()
        writer = csv.writer(output)
        
        # Write header
        writer.writerow(['Device ID', 'Device Name', 'Total Distance (km)', 'Total Time (s)', 'Max Speed (km/h)', 'Avg Speed (km/h)', 'Start Time', 'End Time'])
        
        # Write data
        for device in data.get('devices', []):
            writer.writerow([
                device.get('device_id', ''),
                device.get('device_name', ''),
                device.get('total_distance', 0),
                device.get('total_time', 0),
                device.get('max_speed', 0),
                device.get('avg_speed', 0),
                device.get('start_time', ''),
                device.get('end_time', '')
            ])
        
        return output.getvalue()


class SummaryReportProvider(ReportProvider):
    """Provider for summary reports."""
    
    async def generate_report(self, report: Report) -> bytes:
        """Generate summary report."""
        try:
            from_date, to_date = self._get_date_range(report)
            devices = self._get_devices(report.device_ids)
            
            data = await self._generate_summary_data(devices, from_date, to_date, report)
            return self._format_report(data, report.format)
            
        except Exception as e:
            logger.error(f"Error generating summary report: {e}")
            raise
    
    async def _generate_summary_data(self, devices: List[Device], from_date: datetime, to_date: datetime, report: Report) -> Dict[str, Any]:
        """Generate summary data."""
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
    
    def _format_report(self, data: Dict[str, Any], format_type: str) -> bytes:
        """Format summary report."""
        if format_type == "json":
            return json.dumps(data, indent=2, default=str).encode('utf-8')
        elif format_type == "csv":
            return self._to_csv(data).encode('utf-8')
        else:
            return json.dumps(data, indent=2, default=str).encode('utf-8')
    
    def _to_csv(self, data: Dict[str, Any]) -> str:
        """Convert summary data to CSV."""
        output = io.StringIO()
        writer = csv.writer(output)
        
        # Write header
        writer.writerow(['Device ID', 'Device Name', 'Total Distance (km)', 'Total Time (s)', 'Max Speed (km/h)', 'Avg Speed (km/h)', 'Idle Time (s)', 'Driving Time (s)', 'Stops Count', 'Events Count'])
        
        # Write data
        for device in data.get('devices', []):
            writer.writerow([
                device.get('device_id', ''),
                device.get('device_name', ''),
                device.get('total_distance', 0),
                device.get('total_time', 0),
                device.get('max_speed', 0),
                device.get('avg_speed', 0),
                device.get('idle_time', 0),
                device.get('driving_time', 0),
                device.get('stops_count', 0),
                device.get('events_count', 0)
            ])
        
        return output.getvalue()


class EventsReportProvider(ReportProvider):
    """Provider for events reports."""
    
    async def generate_report(self, report: Report) -> bytes:
        """Generate events report."""
        try:
            from_date, to_date = self._get_date_range(report)
            devices = self._get_devices(report.device_ids)
            
            data = await self._generate_events_data(devices, from_date, to_date, report)
            return self._format_report(data, report.format)
            
        except Exception as e:
            logger.error(f"Error generating events report: {e}")
            raise
    
    async def _generate_events_data(self, devices: List[Device], from_date: datetime, to_date: datetime, report: Report) -> Dict[str, Any]:
        """Generate events data."""
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
    
    def _format_report(self, data: Dict[str, Any], format_type: str) -> bytes:
        """Format events report."""
        if format_type == "json":
            return json.dumps(data, indent=2, default=str).encode('utf-8')
        elif format_type == "csv":
            return self._to_csv(data).encode('utf-8')
        else:
            return json.dumps(data, indent=2, default=str).encode('utf-8')
    
    def _to_csv(self, data: Dict[str, Any]) -> str:
        """Convert events data to CSV."""
        output = io.StringIO()
        writer = csv.writer(output)
        
        # Write header
        writer.writerow(['Device ID', 'Device Name', 'Event ID', 'Event Type', 'Event Time', 'Server Time', 'Position ID', 'Geofence ID'])
        
        # Write data
        for device in data.get('devices', []):
            for event in device.get('events', []):
                writer.writerow([
                    device.get('device_id', ''),
                    device.get('device_name', ''),
                    event.get('id', ''),
                    event.get('type', ''),
                    event.get('event_time', ''),
                    event.get('server_time', ''),
                    event.get('position_id', ''),
                    event.get('geofence_id', '')
                ])
        
        return output.getvalue()


class StopsReportProvider(ReportProvider):
    """Provider for stops reports."""
    
    async def generate_report(self, report: Report) -> bytes:
        """Generate stops report."""
        try:
            from_date, to_date = self._get_date_range(report)
            devices = self._get_devices(report.device_ids)
            
            data = await self._generate_stops_data(devices, from_date, to_date, report)
            return self._format_report(data, report.format)
            
        except Exception as e:
            logger.error(f"Error generating stops report: {e}")
            raise
    
    async def _generate_stops_data(self, devices: List[Device], from_date: datetime, to_date: datetime, report: Report) -> Dict[str, Any]:
        """Generate stops data."""
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
    
    def _format_report(self, data: Dict[str, Any], format_type: str) -> bytes:
        """Format stops report."""
        if format_type == "json":
            return json.dumps(data, indent=2, default=str).encode('utf-8')
        elif format_type == "csv":
            return self._to_csv(data).encode('utf-8')
        else:
            return json.dumps(data, indent=2, default=str).encode('utf-8')
    
    def _to_csv(self, data: Dict[str, Any]) -> str:
        """Convert stops data to CSV."""
        output = io.StringIO()
        writer = csv.writer(output)
        
        # Write header
        writer.writerow(['Device ID', 'Device Name', 'Stop ID', 'Start Time', 'Latitude', 'Longitude', 'Address'])
        
        # Write data
        for device in data.get('devices', []):
            for stop in device.get('stops', []):
                writer.writerow([
                    device.get('device_id', ''),
                    device.get('device_name', ''),
                    stop.get('id', ''),
                    stop.get('start_time', ''),
                    stop.get('latitude', ''),
                    stop.get('longitude', ''),
                    stop.get('address', '')
                ])
        
        return output.getvalue()


class TripsReportProvider(ReportProvider):
    """Provider for trips reports."""
    
    async def generate_report(self, report: Report) -> bytes:
        """Generate trips report."""
        try:
            from_date, to_date = self._get_date_range(report)
            devices = self._get_devices(report.device_ids)
            
            data = await self._generate_trips_data(devices, from_date, to_date, report)
            return self._format_report(data, report.format)
            
        except Exception as e:
            logger.error(f"Error generating trips report: {e}")
            raise
    
    async def _generate_trips_data(self, devices: List[Device], from_date: datetime, to_date: datetime, report: Report) -> Dict[str, Any]:
        """Generate trips data."""
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
    
    def _format_report(self, data: Dict[str, Any], format_type: str) -> bytes:
        """Format trips report."""
        if format_type == "json":
            return json.dumps(data, indent=2, default=str).encode('utf-8')
        elif format_type == "csv":
            return self._to_csv(data).encode('utf-8')
        else:
            return json.dumps(data, indent=2, default=str).encode('utf-8')
    
    def _to_csv(self, data: Dict[str, Any]) -> str:
        """Convert trips data to CSV."""
        output = io.StringIO()
        writer = csv.writer(output)
        
        # Write header
        writer.writerow(['Device ID', 'Device Name', 'Start Time', 'End Time', 'Duration (s)', 'Start Position ID', 'End Position ID'])
        
        # Write data
        for device in data.get('devices', []):
            for trip in device.get('trips', []):
                writer.writerow([
                    device.get('device_id', ''),
                    device.get('device_name', ''),
                    trip.get('start_time', ''),
                    trip.get('end_time', ''),
                    trip.get('duration', 0),
                    trip.get('start_position_id', ''),
                    trip.get('end_position_id', '')
                ])
        
        return output.getvalue()


class ReportProviderFactory:
    """Factory for creating report providers."""
    
    @staticmethod
    def create_provider(report_type: str, db: Session) -> ReportProvider:
        """Create appropriate provider for report type."""
        if report_type == "combined":
            return CombinedReportProvider(db)
        elif report_type == "route":
            return RouteReportProvider(db)
        elif report_type == "summary":
            return SummaryReportProvider(db)
        elif report_type == "events":
            return EventsReportProvider(db)
        elif report_type == "stops":
            return StopsReportProvider(db)
        elif report_type == "trips":
            return TripsReportProvider(db)
        else:
            raise ValueError(f"Unsupported report type: {report_type}")

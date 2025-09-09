"""
Event report service for generating event reports and analytics
"""
import csv
import io
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import and_, or_, desc, func

from app.models import Event, Device, Position, User
from app.services.event_service import EventService


class EventReportService:
    """Service for generating event reports and analytics"""

    def __init__(self, db: Session):
        self.db = db
        self.event_service = EventService(db)

    def generate_events_report(
        self,
        user: User,
        start_date: datetime,
        end_date: datetime,
        device_ids: Optional[List[int]] = None,
        event_types: Optional[List[str]] = None,
        include_attributes: bool = True
    ) -> List[Dict[str, Any]]:
        """Generate comprehensive events report"""
        
        # Build query
        query = self.db.query(Event).options(
            joinedload(Event.device),
            joinedload(Event.position)
        )
        
        # Apply filters
        filters = [
            Event.event_time >= start_date,
            Event.event_time <= end_date
        ]
        
        if device_ids:
            filters.append(Event.device_id.in_(device_ids))
        
        if event_types:
            filters.append(Event.type.in_(event_types))
        
        query = query.filter(and_(*filters))
        
        # Order by time
        events = query.order_by(Event.event_time.desc()).all()
        
        # Transform to report format
        report_data = []
        for event in events:
            row = {
                "id": event.id,
                "type": event.type,
                "event_time": event.event_time.isoformat(),
                "device_id": event.device_id,
                "device_name": event.device.name if event.device else None,
                "position_id": event.position_id,
                "geofence_id": event.geofence_id,
                "maintenance_id": event.maintenance_id,
                "created_at": event.created_at.isoformat()
            }
            
            # Add position data if available
            if event.position:
                row.update({
                    "latitude": event.position.latitude,
                    "longitude": event.position.longitude,
                    "speed": event.position.speed,
                    "course": event.position.course,
                    "altitude": event.position.altitude,
                    "address": event.position.address
                })
            
            # Add attributes if requested
            if include_attributes and event.attributes:
                attrs = event.get_attributes_dict()
                for key, value in attrs.items():
                    row[f"attr_{key}"] = value
            
            report_data.append(row)
        
        return report_data

    def generate_events_summary_report(
        self,
        user: User,
        start_date: datetime,
        end_date: datetime,
        device_ids: Optional[List[int]] = None
    ) -> Dict[str, Any]:
        """Generate events summary report with statistics"""
        
        # Build base query
        query = self.db.query(Event)
        filters = [
            Event.event_time >= start_date,
            Event.event_time <= end_date
        ]
        
        if device_ids:
            filters.append(Event.device_id.in_(device_ids))
        
        query = query.filter(and_(*filters))
        
        # Total events
        total_events = query.count()
        
        # Events by type
        events_by_type = {}
        type_counts = query.with_entities(
            Event.type,
            func.count(Event.id).label('count')
        ).group_by(Event.type).all()
        
        for type_name, count in type_counts:
            events_by_type[type_name] = count
        
        # Events by device
        events_by_device = {}
        device_counts = query.with_entities(
            Event.device_id,
            func.count(Event.id).label('count')
        ).group_by(Event.device_id).all()
        
        for device_id, count in device_counts:
            # Get device name
            device = self.db.query(Device).filter(Device.id == device_id).first()
            device_name = device.name if device else f"Device {device_id}"
            events_by_device[device_name] = count
        
        # Events by day
        events_by_day = {}
        day_counts = query.with_entities(
            func.date(Event.event_time).label('day'),
            func.count(Event.id).label('count')
        ).group_by(func.date(Event.event_time)).all()
        
        for day, count in day_counts:
            events_by_day[day.isoformat()] = count
        
        # Most active devices
        most_active_devices = sorted(
            events_by_device.items(),
            key=lambda x: x[1],
            reverse=True
        )[:10]
        
        # Most common event types
        most_common_types = sorted(
            events_by_type.items(),
            key=lambda x: x[1],
            reverse=True
        )[:10]
        
        return {
            "summary": {
                "total_events": total_events,
                "date_range": {
                    "start": start_date.isoformat(),
                    "end": end_date.isoformat()
                },
                "unique_devices": len(events_by_device),
                "unique_event_types": len(events_by_type)
            },
            "events_by_type": events_by_type,
            "events_by_device": events_by_device,
            "events_by_day": events_by_day,
            "most_active_devices": most_active_devices,
            "most_common_types": most_common_types
        }

    def generate_alarm_report(
        self,
        user: User,
        start_date: datetime,
        end_date: datetime,
        device_ids: Optional[List[int]] = None
    ) -> List[Dict[str, Any]]:
        """Generate alarm events report"""
        
        return self.generate_events_report(
            user=user,
            start_date=start_date,
            end_date=end_date,
            device_ids=device_ids,
            event_types=["alarm"],
            include_attributes=True
        )

    def generate_geofence_report(
        self,
        user: User,
        start_date: datetime,
        end_date: datetime,
        device_ids: Optional[List[int]] = None
    ) -> List[Dict[str, Any]]:
        """Generate geofence events report"""
        
        return self.generate_events_report(
            user=user,
            start_date=start_date,
            end_date=end_date,
            device_ids=device_ids,
            event_types=["geofenceEnter", "geofenceExit"],
            include_attributes=True
        )

    def generate_motion_report(
        self,
        user: User,
        start_date: datetime,
        end_date: datetime,
        device_ids: Optional[List[int]] = None
    ) -> List[Dict[str, Any]]:
        """Generate motion events report"""
        
        return self.generate_events_report(
            user=user,
            start_date=start_date,
            end_date=end_date,
            device_ids=device_ids,
            event_types=["deviceMoving", "deviceStopped"],
            include_attributes=True
        )

    def generate_overspeed_report(
        self,
        user: User,
        start_date: datetime,
        end_date: datetime,
        device_ids: Optional[List[int]] = None
    ) -> List[Dict[str, Any]]:
        """Generate overspeed events report"""
        
        return self.generate_events_report(
            user=user,
            start_date=start_date,
            end_date=end_date,
            device_ids=device_ids,
            event_types=["deviceOverspeed"],
            include_attributes=True
        )

    def export_events_to_csv(
        self,
        user: User,
        start_date: datetime,
        end_date: datetime,
        device_ids: Optional[List[int]] = None,
        event_types: Optional[List[str]] = None
    ) -> str:
        """Export events to CSV format"""
        
        report_data = self.generate_events_report(
            user=user,
            start_date=start_date,
            end_date=end_date,
            device_ids=device_ids,
            event_types=event_types,
            include_attributes=True
        )
        
        if not report_data:
            return ""
        
        # Create CSV
        output = io.StringIO()
        fieldnames = list(report_data[0].keys())
        writer = csv.DictWriter(output, fieldnames=fieldnames)
        
        writer.writeheader()
        for row in report_data:
            writer.writerow(row)
        
        return output.getvalue()

    def get_event_trends(
        self,
        user: User,
        days: int = 30,
        device_ids: Optional[List[int]] = None
    ) -> Dict[str, Any]:
        """Get event trends over time"""
        
        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=days)
        
        # Build query
        query = self.db.query(Event)
        filters = [
            Event.event_time >= start_date,
            Event.event_time <= end_date
        ]
        
        if device_ids:
            filters.append(Event.device_id.in_(device_ids))
        
        query = query.filter(and_(*filters))
        
        # Events by hour
        events_by_hour = {}
        hour_counts = query.with_entities(
            func.extract('hour', Event.event_time).label('hour'),
            func.count(Event.id).label('count')
        ).group_by(func.extract('hour', Event.event_time)).all()
        
        for hour, count in hour_counts:
            events_by_hour[int(hour)] = count
        
        # Events by day of week
        events_by_dow = {}
        dow_counts = query.with_entities(
            func.extract('dow', Event.event_time).label('dow'),
            func.count(Event.id).label('count')
        ).group_by(func.extract('dow', Event.event_time)).all()
        
        days_of_week = ['Sunday', 'Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday']
        for dow, count in dow_counts:
            events_by_dow[days_of_week[int(dow)]] = count
        
        # Events by type over time
        events_by_type_trend = {}
        type_trends = query.with_entities(
            Event.type,
            func.date(Event.event_time).label('day'),
            func.count(Event.id).label('count')
        ).group_by(Event.type, func.date(Event.event_time)).all()
        
        for event_type, day, count in type_trends:
            if event_type not in events_by_type_trend:
                events_by_type_trend[event_type] = {}
            events_by_type_trend[event_type][day.isoformat()] = count
        
        return {
            "events_by_hour": events_by_hour,
            "events_by_day_of_week": events_by_dow,
            "events_by_type_trend": events_by_type_trend,
            "period": {
                "start": start_date.isoformat(),
                "end": end_date.isoformat(),
                "days": days
            }
        }

    def get_device_event_summary(
        self,
        user: User,
        device_id: int,
        days: int = 7
    ) -> Dict[str, Any]:
        """Get event summary for a specific device"""
        
        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=days)
        
        # Get device
        device = self.db.query(Device).filter(Device.id == device_id).first()
        if not device:
            return {}
        
        # Get events for device
        events = self.db.query(Event).filter(
            Event.device_id == device_id,
            Event.event_time >= start_date,
            Event.event_time <= end_date
        ).all()
        
        # Calculate statistics
        total_events = len(events)
        events_by_type = {}
        for event in events:
            events_by_type[event.type] = events_by_type.get(event.type, 0) + 1
        
        # Get latest events
        latest_events = sorted(events, key=lambda x: x.event_time, reverse=True)[:10]
        latest_events_data = []
        for event in latest_events:
            latest_events_data.append({
                "id": event.id,
                "type": event.type,
                "event_time": event.event_time.isoformat(),
                "attributes": event.get_attributes_dict()
            })
        
        return {
            "device": {
                "id": device.id,
                "name": device.name,
                "unique_id": device.unique_id
            },
            "summary": {
                "total_events": total_events,
                "period_days": days,
                "date_range": {
                    "start": start_date.isoformat(),
                    "end": end_date.isoformat()
                }
            },
            "events_by_type": events_by_type,
            "latest_events": latest_events_data
        }

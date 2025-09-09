"""
Report scheduling service.
"""

import asyncio
from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, func, desc
from croniter import croniter
import logging

from app.models import Report, Calendar, User
from app.services.report_service import ReportGenerator
from app.services.email_service import EmailService

logger = logging.getLogger(__name__)


class ReportScheduler:
    """Report scheduling service."""
    
    def __init__(self, db: Session):
        self.db = db
        self.email_service = EmailService()
    
    async def schedule_report(self, report: Report, schedule_cron: str, email_recipients: Optional[List[str]] = None) -> bool:
        """Schedule a report for automatic execution."""
        try:
            # Validate cron expression
            if not self._validate_cron(schedule_cron):
                raise ValueError(f"Invalid cron expression: {schedule_cron}")
            
            # Calculate next run time
            next_run = self._calculate_next_run(schedule_cron)
            
            # Update report with scheduling information
            report.is_scheduled = True
            report.schedule_cron = schedule_cron
            report.next_run = next_run
            report.email_recipients = email_recipients or []
            
            self.db.commit()
            
            logger.info(f"Scheduled report {report.id} with cron '{schedule_cron}', next run: {next_run}")
            return True
            
        except Exception as e:
            logger.error(f"Error scheduling report {report.id}: {e}")
            self.db.rollback()
            return False
    
    async def unschedule_report(self, report: Report) -> bool:
        """Unschedule a report."""
        try:
            report.is_scheduled = False
            report.schedule_cron = None
            report.next_run = None
            report.email_recipients = []
            
            self.db.commit()
            
            logger.info(f"Unscheduled report {report.id}")
            return True
            
        except Exception as e:
            logger.error(f"Error unscheduling report {report.id}: {e}")
            self.db.rollback()
            return False
    
    async def execute_scheduled_reports(self) -> Dict[str, Any]:
        """Execute all scheduled reports that are due."""
        try:
            now = datetime.utcnow()
            
            # Get reports that are due for execution
            due_reports = self.db.query(Report).filter(
                and_(
                    Report.is_scheduled == True,
                    Report.next_run <= now,
                    Report.status.in_(['pending', 'completed', 'failed'])
                )
            ).all()
            
            results = {
                'executed': 0,
                'failed': 0,
                'errors': []
            }
            
            for report in due_reports:
                try:
                    await self._execute_scheduled_report(report)
                    results['executed'] += 1
                except Exception as e:
                    logger.error(f"Error executing scheduled report {report.id}: {e}")
                    results['failed'] += 1
                    results['errors'].append(f"Report {report.id}: {str(e)}")
            
            logger.info(f"Executed {results['executed']} scheduled reports, {results['failed']} failed")
            return results
            
        except Exception as e:
            logger.error(f"Error executing scheduled reports: {e}")
            return {'executed': 0, 'failed': 0, 'errors': [str(e)]}
    
    async def _execute_scheduled_report(self, report: Report):
        """Execute a single scheduled report."""
        try:
            # Update last run time
            report.last_run = datetime.utcnow()
            
            # Calculate next run time
            if report.schedule_cron:
                report.next_run = self._calculate_next_run(report.schedule_cron)
            
            # Generate report
            generator = ReportGenerator(self.db)
            await generator.generate_report(report)
            
            # Send email if recipients are configured
            if report.email_recipients and report.status == 'completed':
                await self._send_report_email(report)
            
            self.db.commit()
            
        except Exception as e:
            report.status = 'failed'
            report.error_message = str(e)
            self.db.commit()
            raise
    
    async def _send_report_email(self, report: Report):
        """Send report via email."""
        try:
            if not report.email_recipients:
                return
            
            subject = f"Report: {report.name}"
            body = f"""
            Your scheduled report '{report.name}' has been completed.
            
            Report Details:
            - Type: {report.report_type}
            - Period: {report.period}
            - Generated: {report.completed_at}
            - File Size: {report.file_size} bytes
            
            You can download the report from the system.
            """
            
            await self.email_service.send_email(
                recipients=report.email_recipients,
                subject=subject,
                body=body,
                attachments=[report.file_path] if report.file_path else []
            )
            
            logger.info(f"Sent report {report.id} via email to {report.email_recipients}")
            
        except Exception as e:
            logger.error(f"Error sending report {report.id} via email: {e}")
    
    def _validate_cron(self, cron_expression: str) -> bool:
        """Validate cron expression."""
        try:
            croniter(cron_expression)
            return True
        except:
            return False
    
    def _calculate_next_run(self, cron_expression: str, base_time: Optional[datetime] = None) -> datetime:
        """Calculate next run time from cron expression."""
        if base_time is None:
            base_time = datetime.utcnow()
        
        cron = croniter(cron_expression, base_time)
        return cron.get_next(datetime)
    
    async def get_scheduled_reports(self, user_id: Optional[int] = None) -> List[Report]:
        """Get all scheduled reports."""
        query = self.db.query(Report).filter(Report.is_scheduled == True)
        
        if user_id:
            query = query.filter(Report.user_id == user_id)
        
        return query.order_by(Report.next_run).all()
    
    async def get_due_reports(self) -> List[Report]:
        """Get reports that are due for execution."""
        now = datetime.utcnow()
        
        return self.db.query(Report).filter(
            and_(
                Report.is_scheduled == True,
                Report.next_run <= now,
                Report.status.in_(['pending', 'completed', 'failed'])
            )
        ).order_by(Report.next_run).all()
    
    async def update_schedule(self, report: Report, new_cron: str) -> bool:
        """Update report schedule."""
        try:
            if not self._validate_cron(new_cron):
                raise ValueError(f"Invalid cron expression: {new_cron}")
            
            report.schedule_cron = new_cron
            report.next_run = self._calculate_next_run(new_cron)
            
            self.db.commit()
            
            logger.info(f"Updated schedule for report {report.id} to '{new_cron}'")
            return True
            
        except Exception as e:
            logger.error(f"Error updating schedule for report {report.id}: {e}")
            self.db.rollback()
            return False


class CalendarIntegration:
    """Calendar integration service."""
    
    def __init__(self, db: Session):
        self.db = db
    
    async def get_calendar_events(self, calendar_id: int, start_date: datetime, end_date: datetime) -> List[Dict[str, Any]]:
        """Get calendar events for scheduling."""
        try:
            calendar = self.db.query(Calendar).filter(Calendar.id == calendar_id).first()
            if not calendar:
                return []
            
            # In a real implementation, this would parse iCalendar data
            # For now, return mock events
            events = []
            
            # Parse iCalendar data (simplified)
            if calendar.data:
                # This would parse actual iCalendar format
                # For now, return empty list
                pass
            
            return events
            
        except Exception as e:
            logger.error(f"Error getting calendar events for calendar {calendar_id}: {e}")
            return []
    
    async def create_calendar(self, user_id: int, name: str, description: str = None, data: str = None) -> Calendar:
        """Create a new calendar."""
        try:
            calendar = Calendar(
                user_id=user_id,
                name=name,
                description=description,
                data=data
            )
            
            self.db.add(calendar)
            self.db.commit()
            self.db.refresh(calendar)
            
            logger.info(f"Created calendar {calendar.id} for user {user_id}")
            return calendar
            
        except Exception as e:
            logger.error(f"Error creating calendar for user {user_id}: {e}")
            self.db.rollback()
            raise
    
    async def update_calendar(self, calendar_id: int, **kwargs) -> bool:
        """Update calendar."""
        try:
            calendar = self.db.query(Calendar).filter(Calendar.id == calendar_id).first()
            if not calendar:
                return False
            
            for key, value in kwargs.items():
                if hasattr(calendar, key):
                    setattr(calendar, key, value)
            
            calendar.updated_at = datetime.utcnow()
            self.db.commit()
            
            logger.info(f"Updated calendar {calendar_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error updating calendar {calendar_id}: {e}")
            self.db.rollback()
            return False
    
    async def delete_calendar(self, calendar_id: int) -> bool:
        """Delete calendar."""
        try:
            calendar = self.db.query(Calendar).filter(Calendar.id == calendar_id).first()
            if not calendar:
                return False
            
            # Check if calendar is used by any reports
            reports_count = self.db.query(Report).filter(Report.calendar_id == calendar_id).count()
            if reports_count > 0:
                raise ValueError(f"Cannot delete calendar {calendar_id}: {reports_count} reports are using it")
            
            self.db.delete(calendar)
            self.db.commit()
            
            logger.info(f"Deleted calendar {calendar_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error deleting calendar {calendar_id}: {e}")
            self.db.rollback()
            return False

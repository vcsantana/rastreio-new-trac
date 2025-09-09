"""
Extended report endpoints for scheduling, email, and calendar integration.
"""

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, desc, func
from typing import List, Optional
from datetime import datetime

from app.database import get_db
from app.models import User, Report, Calendar
from app.schemas.report import ReportResponse
from app.api.auth import get_current_user
from app.services.report_service import ReportGenerator
from app.services.report_scheduler import ReportScheduler, CalendarIntegration
from app.services.email_service import EmailService

router = APIRouter()


# Scheduling endpoints

@router.post("/{report_id}/schedule")
async def schedule_report(
    report_id: int,
    schedule_cron: str = Query(..., description="Cron expression for scheduling"),
    email_recipients: Optional[List[str]] = Query(None, description="Email addresses for automatic sending"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Schedule a report for automatic execution."""
    report = db.query(Report).filter(
        and_(Report.id == report_id, Report.user_id == current_user.id)
    ).first()
    
    if not report:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Report not found"
        )
    
    scheduler = ReportScheduler(db)
    success = await scheduler.schedule_report(report, schedule_cron, email_recipients)
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Failed to schedule report"
        )
    
    return {"message": "Report scheduled successfully", "next_run": report.next_run}


@router.delete("/{report_id}/schedule")
async def unschedule_report(
    report_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Unschedule a report."""
    report = db.query(Report).filter(
        and_(Report.id == report_id, Report.user_id == current_user.id)
    ).first()
    
    if not report:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Report not found"
        )
    
    scheduler = ReportScheduler(db)
    success = await scheduler.unschedule_report(report)
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Failed to unschedule report"
        )
    
    return {"message": "Report unscheduled successfully"}


@router.get("/scheduled/", response_model=List[ReportResponse])
async def get_scheduled_reports(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get all scheduled reports for the user."""
    scheduler = ReportScheduler(db)
    reports = await scheduler.get_scheduled_reports(current_user.id)
    return reports


@router.post("/execute-scheduled")
async def execute_scheduled_reports(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Execute all scheduled reports that are due (admin only)."""
    # In a real implementation, this would check for admin permissions
    scheduler = ReportScheduler(db)
    results = await scheduler.execute_scheduled_reports()
    return results


# Email endpoints

@router.post("/{report_id}/send-email")
async def send_report_email(
    report_id: int,
    recipients: List[str] = Query(..., description="Email addresses to send report to"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Send report via email."""
    report = db.query(Report).filter(
        and_(Report.id == report_id, Report.user_id == current_user.id)
    ).first()
    
    if not report:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Report not found"
        )
    
    if report.status != "completed":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Report not completed yet"
        )
    
    email_service = EmailService()
    
    # Get report data for email content
    generator = ReportGenerator(db)
    report_data = await generator.generate_report(report)
    
    success = await email_service.send_report_email(
        report_name=report.name,
        recipients=recipients,
        report_data=report_data,
        file_path=report.file_path,
        report_type=report.report_type
    )
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to send email"
        )
    
    return {"message": "Report sent via email successfully"}


@router.post("/test-email")
async def test_email_configuration(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Test email configuration."""
    email_service = EmailService()
    result = await email_service.test_email_configuration()
    return result


# Calendar endpoints

@router.post("/calendars/", response_model=dict)
async def create_calendar(
    name: str = Query(..., description="Calendar name"),
    description: Optional[str] = Query(None, description="Calendar description"),
    data: Optional[str] = Query(None, description="iCalendar data"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Create a new calendar."""
    calendar_service = CalendarIntegration(db)
    calendar = await calendar_service.create_calendar(
        user_id=current_user.id,
        name=name,
        description=description,
        data=data
    )
    return calendar


@router.get("/calendars/", response_model=List[dict])
async def get_calendars(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get user's calendars."""
    calendars = db.query(Calendar).filter(Calendar.user_id == current_user.id).all()
    return calendars


@router.put("/calendars/{calendar_id}")
async def update_calendar(
    calendar_id: int,
    name: Optional[str] = Query(None, description="Calendar name"),
    description: Optional[str] = Query(None, description="Calendar description"),
    data: Optional[str] = Query(None, description="iCalendar data"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Update calendar."""
    calendar = db.query(Calendar).filter(
        and_(Calendar.id == calendar_id, Calendar.user_id == current_user.id)
    ).first()
    
    if not calendar:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Calendar not found"
        )
    
    calendar_service = CalendarIntegration(db)
    update_data = {}
    if name is not None:
        update_data['name'] = name
    if description is not None:
        update_data['description'] = description
    if data is not None:
        update_data['data'] = data
    
    success = await calendar_service.update_calendar(calendar_id, **update_data)
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Failed to update calendar"
        )
    
    return {"message": "Calendar updated successfully"}


@router.delete("/calendars/{calendar_id}")
async def delete_calendar(
    calendar_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Delete calendar."""
    calendar = db.query(Calendar).filter(
        and_(Calendar.id == calendar_id, Calendar.user_id == current_user.id)
    ).first()
    
    if not calendar:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Calendar not found"
        )
    
    calendar_service = CalendarIntegration(db)
    success = await calendar_service.delete_calendar(calendar_id)
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Failed to delete calendar"
        )
    
    return {"message": "Calendar deleted successfully"}

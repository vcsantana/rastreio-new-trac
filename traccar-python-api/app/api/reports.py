"""
Reports API endpoints.
"""

from fastapi import APIRouter, Depends, HTTPException, Query, BackgroundTasks, status
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, desc, func
from typing import List, Optional
from datetime import datetime

from app.database import get_db
from app.models import User, Report, ReportTemplate, Device
from app.schemas.report import (
    ReportCreate, ReportUpdate, ReportResponse, ReportListResponse,
    ReportTemplateCreate, ReportTemplateUpdate, ReportTemplateResponse,
    ReportTemplateListResponse, ReportStatsResponse, ReportDataResponse,
    ReportType, ReportFormat, ReportPeriod
)
from app.api.auth import get_current_user
from app.services.report_service import ReportGenerator
from app.services.report_scheduler import ReportScheduler, CalendarIntegration
from app.services.email_service import EmailService

router = APIRouter()


@router.post("/", response_model=ReportResponse)
async def create_report(
    report_data: ReportCreate,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Create a new report."""
    # Create report record
    report = Report(
        user_id=current_user.id,
        name=report_data.name,
        description=report_data.description,
        report_type=report_data.report_type.value,
        format=report_data.format.value,
        period=report_data.period.value,
        from_date=report_data.from_date,
        to_date=report_data.to_date,
        device_ids=report_data.device_ids,
        group_ids=report_data.group_ids,
        include_attributes=report_data.include_attributes,
        include_addresses=report_data.include_addresses,
        include_events=report_data.include_events,
        include_geofences=report_data.include_geofences,
        parameters=report_data.parameters
    )
    
    db.add(report)
    db.commit()
    db.refresh(report)
    
    # Generate report in background
    background_tasks.add_task(generate_report_task, report.id)
    
    return report


async def generate_report_task(report_id: int):
    """Background task to generate report."""
    db = next(get_db())
    try:
        report = db.query(Report).filter(Report.id == report_id).first()
        if report:
            generator = ReportGenerator(db)
            await generator.generate_report(report)
    except Exception as e:
        # Update report with error
        report = db.query(Report).filter(Report.id == report_id).first()
        if report:
            report.status = "failed"
            report.error_message = str(e)
            db.commit()
    finally:
        db.close()


@router.get("/", response_model=ReportListResponse)
async def get_reports(
    page: int = Query(1, ge=1, description="Page number"),
    size: int = Query(20, ge=1, le=100, description="Page size"),
    report_type: Optional[ReportType] = Query(None, description="Filter by report type"),
    status: Optional[str] = Query(None, description="Filter by status"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get user's reports."""
    query = db.query(Report).filter(Report.user_id == current_user.id)
    
    if report_type:
        query = query.filter(Report.report_type == report_type.value)
    
    if status:
        query = query.filter(Report.status == status)
    
    # Get total count
    total = query.count()
    
    # Get paginated results
    reports = query.order_by(desc(Report.created_at)).offset((page - 1) * size).limit(size).all()
    
    return ReportListResponse(
        items=reports,
        total=total,
        page=page,
        size=size,
        pages=(total + size - 1) // size
    )


@router.get("/{report_id}", response_model=ReportResponse)
async def get_report(
    report_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get a specific report."""
    report = db.query(Report).filter(
        and_(Report.id == report_id, Report.user_id == current_user.id)
    ).first()
    
    if not report:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Report not found"
        )
    
    return report


@router.put("/{report_id}", response_model=ReportResponse)
async def update_report(
    report_id: int,
    report_update: ReportUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Update a report."""
    report = db.query(Report).filter(
        and_(Report.id == report_id, Report.user_id == current_user.id)
    ).first()
    
    if not report:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Report not found"
        )
    
    if report.status == "processing":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot update report while processing"
        )
    
    # Update fields
    update_data = report_update.dict(exclude_unset=True)
    for field, value in update_data.items():
        if hasattr(report, field):
            setattr(report, field, value)
    
    report.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(report)
    
    return report


@router.delete("/{report_id}")
async def delete_report(
    report_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Delete a report."""
    report = db.query(Report).filter(
        and_(Report.id == report_id, Report.user_id == current_user.id)
    ).first()
    
    if not report:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Report not found"
        )
    
    if report.status == "processing":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot delete report while processing"
        )
    
    db.delete(report)
    db.commit()
    
    return {"message": "Report deleted successfully"}


@router.get("/{report_id}/data", response_model=ReportDataResponse)
async def get_report_data(
    report_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get report data."""
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
    
    # In a real implementation, this would read the actual report file
    # For now, return mock data
    mock_data = {
        "report_type": report.report_type,
        "data": {
            "message": "Report data would be here",
            "generated_at": report.completed_at.isoformat() if report.completed_at else None
        },
        "generated_at": report.completed_at.isoformat() if report.completed_at else None,
        "period_start": report.from_date.isoformat() if report.from_date else None,
        "period_end": report.to_date.isoformat() if report.to_date else None
    }
    
    return mock_data


@router.get("/{report_id}/download")
async def download_report(
    report_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Download report file."""
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
    
    # In a real implementation, this would return the actual file
    # For now, return a mock response
    return {
        "message": "Report download would be here",
        "file_path": report.file_path,
        "file_size": report.file_size
    }


@router.get("/stats/summary", response_model=ReportStatsResponse)
async def get_report_stats(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get report statistics."""
    # Get user's reports
    user_reports = db.query(Report).filter(Report.user_id == current_user.id)
    
    # Calculate statistics
    total_reports = user_reports.count()
    
    reports_by_type = {}
    reports_by_status = {}
    total_file_size = 0
    last_generated = None
    most_used_type = None
    
    for report in user_reports.all():
        # Count by type
        reports_by_type[report.report_type] = reports_by_type.get(report.report_type, 0) + 1
        
        # Count by status
        reports_by_status[report.status] = reports_by_status.get(report.status, 0) + 1
        
        # Sum file sizes
        if report.file_size:
            total_file_size += report.file_size
        
        # Track last generated
        if report.completed_at and (not last_generated or report.completed_at > last_generated):
            last_generated = report.completed_at
    
    # Find most used type
    if reports_by_type:
        most_used_type = max(reports_by_type, key=reports_by_type.get)
    
    return ReportStatsResponse(
        total_reports=total_reports,
        reports_by_type=reports_by_type,
        reports_by_status=reports_by_status,
        total_file_size=total_file_size,
        last_generated=last_generated,
        most_used_type=most_used_type
    )


# Report Templates endpoints

@router.post("/templates/", response_model=ReportTemplateResponse)
async def create_report_template(
    template_data: ReportTemplateCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Create a new report template."""
    template = ReportTemplate(
        user_id=current_user.id,
        name=template_data.name,
        description=template_data.description,
        report_type=template_data.report_type.value,
        format=template_data.format.value,
        parameters=template_data.parameters,
        is_public=template_data.is_public,
        is_default=template_data.is_default
    )
    
    db.add(template)
    db.commit()
    db.refresh(template)
    
    return template


@router.get("/templates/", response_model=ReportTemplateListResponse)
async def get_report_templates(
    page: int = Query(1, ge=1, description="Page number"),
    size: int = Query(20, ge=1, le=100, description="Page size"),
    report_type: Optional[ReportType] = Query(None, description="Filter by report type"),
    public_only: bool = Query(False, description="Show only public templates"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get report templates."""
    query = db.query(ReportTemplate).filter(
        or_(
            ReportTemplate.user_id == current_user.id,
            ReportTemplate.is_public == True
        )
    )
    
    if report_type:
        query = query.filter(ReportTemplate.report_type == report_type.value)
    
    if public_only:
        query = query.filter(ReportTemplate.is_public == True)
    
    # Get total count
    total = query.count()
    
    # Get paginated results
    templates = query.order_by(desc(ReportTemplate.created_at)).offset((page - 1) * size).limit(size).all()
    
    return ReportTemplateListResponse(
        items=templates,
        total=total,
        page=page,
        size=size,
        pages=(total + size - 1) // size
    )


@router.get("/templates/{template_id}", response_model=ReportTemplateResponse)
async def get_report_template(
    template_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get a specific report template."""
    template = db.query(ReportTemplate).filter(
        and_(
            ReportTemplate.id == template_id,
            or_(
                ReportTemplate.user_id == current_user.id,
                ReportTemplate.is_public == True
            )
        )
    ).first()
    
    if not template:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Report template not found"
        )
    
    return template


@router.put("/templates/{template_id}", response_model=ReportTemplateResponse)
async def update_report_template(
    template_id: int,
    template_update: ReportTemplateUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Update a report template."""
    template = db.query(ReportTemplate).filter(
        and_(ReportTemplate.id == template_id, ReportTemplate.user_id == current_user.id)
    ).first()
    
    if not template:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Report template not found"
        )
    
    # Update fields
    update_data = template_update.dict(exclude_unset=True)
    for field, value in update_data.items():
        if hasattr(template, field):
            setattr(template, field, value)
    
    template.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(template)
    
    return template


@router.delete("/templates/{template_id}")
async def delete_report_template(
    template_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Delete a report template."""
    template = db.query(ReportTemplate).filter(
        and_(ReportTemplate.id == template_id, ReportTemplate.user_id == current_user.id)
    ).first()
    
    if not template:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Report template not found"
        )
    
    db.delete(template)
    db.commit()
    
    return {"message": "Report template deleted successfully"}


@router.post("/templates/{template_id}/use", response_model=ReportResponse)
async def use_report_template(
    template_id: int,
    background_tasks: BackgroundTasks,
    device_ids: Optional[List[int]] = None,
    period: Optional[ReportPeriod] = None,
    from_date: Optional[datetime] = None,
    to_date: Optional[datetime] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Use a report template to create a report."""
    template = db.query(ReportTemplate).filter(
        and_(
            ReportTemplate.id == template_id,
            or_(
                ReportTemplate.user_id == current_user.id,
                ReportTemplate.is_public == True
            )
        )
    ).first()
    
    if not template:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Report template not found"
        )
    
    # Create report from template
    report = Report(
        user_id=current_user.id,
        name=f"{template.name} - {datetime.utcnow().strftime('%Y-%m-%d %H:%M')}",
        description=template.description,
        report_type=template.report_type,
        format=template.format,
        period=period.value if period else "today",
        from_date=from_date,
        to_date=to_date,
        device_ids=device_ids,
        parameters=template.parameters
    )
    
    db.add(report)
    db.commit()
    db.refresh(report)
    
    # Generate report in background
    background_tasks.add_task(generate_report_task, report.id)
    
    return report


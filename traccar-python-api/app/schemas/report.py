"""
Report schemas for Pydantic validation.
"""

from datetime import datetime, date
from typing import Optional, List, Dict, Any, Union
from pydantic import BaseModel, Field, validator
from enum import Enum


class ReportType(str, Enum):
    """Report types."""
    ROUTE = "route"
    SUMMARY = "summary"
    EVENTS = "events"
    STOPS = "stops"
    TRIPS = "trips"
    MAINTENANCE = "maintenance"
    FUEL = "fuel"
    DRIVER = "driver"
    CUSTOM = "custom"


class ReportFormat(str, Enum):
    """Report formats."""
    JSON = "json"
    CSV = "csv"
    PDF = "pdf"
    XLSX = "xlsx"


class ReportPeriod(str, Enum):
    """Report periods."""
    TODAY = "today"
    YESTERDAY = "yesterday"
    THIS_WEEK = "this_week"
    LAST_WEEK = "last_week"
    THIS_MONTH = "this_month"
    LAST_MONTH = "last_month"
    THIS_YEAR = "this_year"
    LAST_YEAR = "last_year"
    CUSTOM = "custom"


class ReportBase(BaseModel):
    """Base report schema."""
    name: str = Field(..., min_length=1, max_length=100, description="Report name")
    description: Optional[str] = Field(None, max_length=500, description="Report description")
    report_type: ReportType = Field(..., description="Type of report")
    format: ReportFormat = Field(default=ReportFormat.JSON, description="Output format")
    period: ReportPeriod = Field(default=ReportPeriod.TODAY, description="Report period")
    from_date: Optional[datetime] = Field(None, description="Start date for custom period")
    to_date: Optional[datetime] = Field(None, description="End date for custom period")
    device_ids: Optional[List[int]] = Field(None, description="Device IDs to include")
    group_ids: Optional[List[int]] = Field(None, description="Group IDs to include")
    include_attributes: bool = Field(default=True, description="Include device attributes")
    include_addresses: bool = Field(default=True, description="Include address information")
    include_events: bool = Field(default=True, description="Include events")
    include_geofences: bool = Field(default=True, description="Include geofence information")
    parameters: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Custom parameters")


class ReportCreate(ReportBase):
    """Schema for creating a report."""
    pass


class ReportUpdate(BaseModel):
    """Schema for updating a report."""
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    description: Optional[str] = Field(None, max_length=500)
    report_type: Optional[ReportType] = None
    format: Optional[ReportFormat] = None
    period: Optional[ReportPeriod] = None
    from_date: Optional[datetime] = None
    to_date: Optional[datetime] = None
    device_ids: Optional[List[int]] = None
    group_ids: Optional[List[int]] = None
    include_attributes: Optional[bool] = None
    include_addresses: Optional[bool] = None
    include_events: Optional[bool] = None
    include_geofences: Optional[bool] = None
    parameters: Optional[Dict[str, Any]] = None


class ReportResponse(ReportBase):
    """Schema for report response."""
    id: int
    user_id: int
    status: str
    created_at: datetime
    updated_at: datetime
    completed_at: Optional[datetime] = None
    file_path: Optional[str] = None
    file_size: Optional[int] = None
    error_message: Optional[str] = None

    class Config:
        from_attributes = True


class ReportListResponse(BaseModel):
    """Schema for report list response."""
    items: List[ReportResponse]
    total: int
    page: int
    size: int
    pages: int


class RouteReportData(BaseModel):
    """Route report data."""
    device_id: int
    device_name: str
    positions: List[Dict[str, Any]]
    total_distance: float
    total_time: int
    max_speed: float
    avg_speed: float
    start_time: datetime
    end_time: datetime
    start_address: Optional[str] = None
    end_address: Optional[str] = None


class SummaryReportData(BaseModel):
    """Summary report data."""
    device_id: int
    device_name: str
    total_distance: float
    total_time: int
    max_speed: float
    avg_speed: float
    engine_hours: Optional[float] = None
    fuel_consumption: Optional[float] = None
    idle_time: int
    driving_time: int
    stops_count: int
    events_count: int
    period_start: datetime
    period_end: datetime


class EventsReportData(BaseModel):
    """Events report data."""
    device_id: int
    device_name: str
    events: List[Dict[str, Any]]
    events_by_type: Dict[str, int]
    total_events: int
    period_start: datetime
    period_end: datetime


class StopsReportData(BaseModel):
    """Stops report data."""
    device_id: int
    device_name: str
    stops: List[Dict[str, Any]]
    total_stops: int
    total_stop_time: int
    longest_stop: Optional[Dict[str, Any]] = None
    period_start: datetime
    period_end: datetime


class TripsReportData(BaseModel):
    """Trips report data."""
    device_id: int
    device_name: str
    trips: List[Dict[str, Any]]
    total_trips: int
    total_distance: float
    total_time: int
    period_start: datetime
    period_end: datetime


class MaintenanceReportData(BaseModel):
    """Maintenance report data."""
    device_id: int
    device_name: str
    maintenance_items: List[Dict[str, Any]]
    upcoming_maintenance: List[Dict[str, Any]]
    overdue_maintenance: List[Dict[str, Any]]
    total_items: int
    period_start: datetime
    period_end: datetime


class FuelReportData(BaseModel):
    """Fuel report data."""
    device_id: int
    device_name: str
    fuel_entries: List[Dict[str, Any]]
    total_fuel: float
    avg_consumption: float
    fuel_cost: Optional[float] = None
    period_start: datetime
    period_end: datetime


class DriverReportData(BaseModel):
    """Driver report data."""
    driver_id: int
    driver_name: str
    devices: List[Dict[str, Any]]
    total_distance: float
    total_time: int
    max_speed: float
    avg_speed: float
    violations: List[Dict[str, Any]]
    period_start: datetime
    period_end: datetime


class ReportDataResponse(BaseModel):
    """Report data response."""
    report_id: int
    report_type: ReportType
    data: Union[
        RouteReportData,
        SummaryReportData,
        EventsReportData,
        StopsReportData,
        TripsReportData,
        MaintenanceReportData,
        FuelReportData,
        DriverReportData
    ]
    generated_at: datetime
    period_start: datetime
    period_end: datetime


class ReportStatsResponse(BaseModel):
    """Report statistics response."""
    total_reports: int
    reports_by_type: Dict[str, int]
    reports_by_status: Dict[str, int]
    total_file_size: int
    last_generated: Optional[datetime] = None
    most_used_type: Optional[str] = None


class ReportTemplateBase(BaseModel):
    """Base report template schema."""
    name: str = Field(..., min_length=1, max_length=100, description="Template name")
    description: Optional[str] = Field(None, max_length=500, description="Template description")
    report_type: ReportType = Field(..., description="Report type")
    format: ReportFormat = Field(default=ReportFormat.JSON, description="Output format")
    parameters: Dict[str, Any] = Field(default_factory=dict, description="Template parameters")
    is_public: bool = Field(default=False, description="Public template")
    is_default: bool = Field(default=False, description="Default template")


class ReportTemplateCreate(ReportTemplateBase):
    """Schema for creating a report template."""
    pass


class ReportTemplateUpdate(BaseModel):
    """Schema for updating a report template."""
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    description: Optional[str] = Field(None, max_length=500)
    report_type: Optional[ReportType] = None
    format: Optional[ReportFormat] = None
    parameters: Optional[Dict[str, Any]] = None
    is_public: Optional[bool] = None
    is_default: Optional[bool] = None


class ReportTemplateResponse(ReportTemplateBase):
    """Schema for report template response."""
    id: int
    user_id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class ReportTemplateListResponse(BaseModel):
    """Schema for report template list response."""
    items: List[ReportTemplateResponse]
    total: int
    page: int
    size: int
    pages: int


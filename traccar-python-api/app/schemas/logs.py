"""
Logs schemas
"""
from pydantic import BaseModel
from typing import List, Optional, Dict, Any, Union
from datetime import datetime


class LogEntry(BaseModel):
    """Single log entry"""
    id: str
    timestamp: datetime
    device_id: int
    device_name: str
    protocol: str
    type: str  # "position" or event type
    data: Dict[str, Any]


class LogsFilter(BaseModel):
    """Logs filter parameters"""
    device_id: Optional[int] = None
    protocol: Optional[str] = None
    hours: int = 24


class LogsResponse(BaseModel):
    """Logs response with metadata"""
    entries: List[LogEntry]
    total: int
    limit: int
    filters: LogsFilter

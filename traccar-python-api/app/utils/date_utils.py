"""
Date and time utility functions
"""
from datetime import datetime, timezone
from typing import Optional, Union
import re


def parse_date_time(date_str: str, time_str: Optional[str] = None) -> Optional[datetime]:
    """
    Parse date and time strings into a datetime object.
    
    Args:
        date_str: Date string in various formats
        time_str: Optional time string
        
    Returns:
        datetime object or None if parsing fails
    """
    if not date_str:
        return None
    
    # Common date formats
    date_formats = [
        "%Y-%m-%d",
        "%d-%m-%Y", 
        "%m/%d/%Y",
        "%d/%m/%Y",
        "%Y%m%d",
        "%d%m%Y"
    ]
    
    # Common time formats
    time_formats = [
        "%H:%M:%S",
        "%H:%M",
        "%H%M%S",
        "%H%M"
    ]
    
    # Try to parse date
    parsed_date = None
    for fmt in date_formats:
        try:
            parsed_date = datetime.strptime(date_str, fmt).date()
            break
        except ValueError:
            continue
    
    if not parsed_date:
        return None
    
    # Try to parse time if provided
    parsed_time = None
    if time_str:
        for fmt in time_formats:
            try:
                parsed_time = datetime.strptime(time_str, fmt).time()
                break
            except ValueError:
                continue
    
    # Combine date and time
    if parsed_time:
        return datetime.combine(parsed_date, parsed_time, tzinfo=timezone.utc)
    else:
        return datetime.combine(parsed_date, datetime.min.time(), tzinfo=timezone.utc)


def parse_gps_date_time(date_str: str, time_str: str) -> Optional[datetime]:
    """
    Parse GPS date and time format (DDMMYY HHMMSS).
    
    Args:
        date_str: Date string in DDMMYY format
        time_str: Time string in HHMMSS format
        
    Returns:
        datetime object or None if parsing fails
    """
    if not date_str or not time_str:
        return None
    
    try:
        # Parse DDMMYY format
        day = int(date_str[:2])
        month = int(date_str[2:4])
        year = int(date_str[4:6]) + 2000  # Assume 20xx
        
        # Parse HHMMSS format
        hour = int(time_str[:2])
        minute = int(time_str[2:4])
        second = int(time_str[4:6])
        
        return datetime(year, month, day, hour, minute, second, tzinfo=timezone.utc)
    except (ValueError, IndexError):
        return None


def format_iso_datetime(dt: datetime) -> str:
    """
    Format datetime to ISO string.
    
    Args:
        dt: datetime object
        
    Returns:
        ISO formatted string
    """
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    
    return dt.isoformat()


def parse_iso_datetime(iso_str: str) -> Optional[datetime]:
    """
    Parse ISO datetime string.
    
    Args:
        iso_str: ISO formatted datetime string
        
    Returns:
        datetime object or None if parsing fails
    """
    try:
        return datetime.fromisoformat(iso_str.replace('Z', '+00:00'))
    except ValueError:
        return None


def get_timezone_offset() -> int:
    """
    Get the current timezone offset in minutes.
    
    Returns:
        Timezone offset in minutes
    """
    now = datetime.now(timezone.utc)
    local_now = datetime.now()
    offset = local_now.utcoffset()
    
    if offset:
        return int(offset.total_seconds() / 60)
    return 0


def is_valid_date_range(start_date: datetime, end_date: datetime) -> bool:
    """
    Check if the date range is valid.
    
    Args:
        start_date: Start datetime
        end_date: End datetime
        
    Returns:
        True if valid range, False otherwise
    """
    return start_date <= end_date


def add_timezone_if_naive(dt: datetime) -> datetime:
    """
    Add UTC timezone to naive datetime.
    
    Args:
        dt: datetime object
        
    Returns:
        datetime with timezone
    """
    if dt.tzinfo is None:
        return dt.replace(tzinfo=timezone.utc)
    return dt

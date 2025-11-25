"""
Date utility functions for parsing and formatting dates.
Handles multiple date formats used throughout the application.
"""
from datetime import datetime
from typing import Optional
from config.settings import DATE_FORMAT_INPUT, DATE_FORMAT_DISPLAY, DATE_FORMAT_ALTERNATIVE


def parse_date(date_val: any) -> Optional[datetime]:
    """
    Parse a date value from various formats into a datetime object.
    
    Supports:
    - YYYY-MM-DD format (e.g., "2025-01-15")
    - DD/MM/YYYY format (e.g., "15/01/2025")
    - datetime objects (returns as-is)
    - None or empty strings (returns None)
    
    Args:
        date_val: Date value to parse (str, datetime, or None)
        
    Returns:
        datetime object if parsing successful, None otherwise
        
    Examples:
        >>> parse_date("2025-01-15")
        datetime(2025, 1, 15, 0, 0)
        >>> parse_date("15/01/2025")
        datetime(2025, 1, 15, 0, 0)
        >>> parse_date(None)
        None
    """
    if not date_val:
        return None
    
    # If already a datetime object, return it
    if isinstance(date_val, datetime):
        return date_val
    
    try:
        date_str = str(date_val).strip()
        
        # Try YYYY-MM-DD format first
        if '-' in date_str:
            return datetime.strptime(date_str, DATE_FORMAT_INPUT)
        # Try DD/MM/YYYY format
        else:
            return datetime.strptime(date_str, DATE_FORMAT_ALTERNATIVE)
    except (ValueError, AttributeError):
        return None


def format_date(date_obj: Optional[datetime], output_format: str = DATE_FORMAT_DISPLAY) -> str:
    """
    Format a datetime object into a string.
    
    Args:
        date_obj: datetime object to format
        output_format: Output format string (default: DD/MM/YYYY)
        
    Returns:
        Formatted date string, or empty string if date_obj is None
        
    Examples:
        >>> format_date(datetime(2025, 1, 15))
        "15/01/2025"
        >>> format_date(None)
        ""
    """
    if not date_obj:
        return ""
    
    try:
        return date_obj.strftime(output_format)
    except (ValueError, AttributeError):
        return ""


def is_valid_date(date_str: str) -> bool:
    """
    Check if a string is a valid date.
    
    Args:
        date_str: Date string to validate
        
    Returns:
        True if valid date, False otherwise
        
    Examples:
        >>> is_valid_date("2025-01-15")
        True
        >>> is_valid_date("invalid")
        False
    """
    return parse_date(date_str) is not None

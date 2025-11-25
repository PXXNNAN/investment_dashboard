"""
Amount utility functions for parsing and formatting monetary values.
Handles currency symbols, commas, and various number formats.
"""
from typing import Union


def parse_amount(amount_val: Union[str, int, float]) -> float:
    """
    Parse an amount value into a float.
    
    Handles:
    - Numeric values (int, float) - returns as float
    - Strings with commas (e.g., "1,000.50")
    - Strings with currency symbols (e.g., "฿1,000")
    - Empty strings or None - returns 0.0
    
    Args:
        amount_val: Amount value to parse
        
    Returns:
        Float value, or 0.0 if parsing fails
        
    Examples:
        >>> parse_amount(1000)
        1000.0
        >>> parse_amount("1,000.50")
        1000.5
        >>> parse_amount("฿1,000")
        1000.0
        >>> parse_amount("")
        0.0
    """
    # If already numeric, convert to float
    if isinstance(amount_val, (int, float)):
        return float(amount_val)
    
    # Handle string values
    try:
        # Remove common currency symbols and commas
        cleaned = str(amount_val).replace(',', '').replace('฿', '').replace('$', '').strip()
        
        if not cleaned:
            return 0.0
            
        return float(cleaned)
    except (ValueError, AttributeError):
        return 0.0


def format_amount(amount: float, include_symbol: bool = False, decimal_places: int = 2) -> str:
    """
    Format an amount as a string with proper formatting.
    
    Args:
        amount: Amount to format
        include_symbol: Whether to include ฿ symbol (default: False)
        decimal_places: Number of decimal places (default: 2)
        
    Returns:
        Formatted amount string
        
    Examples:
        >>> format_amount(1000.5)
        "1,000.50"
        >>> format_amount(1000.5, include_symbol=True)
        "฿1,000.50"
        >>> format_amount(1000, decimal_places=0)
        "1,000"
    """
    try:
        # Format with commas and specified decimal places
        formatted = f"{amount:,.{decimal_places}f}"
        
        if include_symbol:
            return f"฿{formatted}"
        return formatted
    except (ValueError, TypeError):
        return "0.00"


def is_valid_amount(amount_str: str) -> bool:
    """
    Check if a string represents a valid amount.
    
    Args:
        amount_str: Amount string to validate
        
    Returns:
        True if valid amount, False otherwise
        
    Examples:
        >>> is_valid_amount("1000")
        True
        >>> is_valid_amount("1,000.50")
        True
        >>> is_valid_amount("invalid")
        False
    """
    if not amount_str or not str(amount_str).strip():
        return False
    
    try:
        # Remove common currency symbols and commas
        cleaned = str(amount_str).replace(',', '').replace('฿', '').replace('$', '').strip()
        
        if not cleaned:
            return False
        
        # Try to convert to float
        float(cleaned)
        return True
    except (ValueError, AttributeError):
        return False

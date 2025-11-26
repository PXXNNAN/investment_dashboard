"""
Dividend data model representing a dividend payment record.
"""
from dataclasses import dataclass
from datetime import datetime
from typing import Optional, Dict, Any
from utils.date_utils import parse_date, format_date
from utils.amount_utils import parse_amount


@dataclass
class Dividend:
    """
    Represents a single dividend payment record.
    
    Attributes:
        id: Unique identifier (UUID)
        date: Payment date
        name: Asset name that paid the dividend
        category: Asset category
        amount: Dividend amount received
        reinvested: Whether dividend was reinvested (Yes/No)
        note: Additional notes (optional)
    """
    id: str
    date: datetime
    name: str
    category: str
    amount: float
    reinvested: str = "No"  # "Yes" or "No"
    note: str = ""
    
    def __post_init__(self):
        """Validate and convert data types after initialization."""
        # Ensure date is datetime object
        if not isinstance(self.date, datetime):
            self.date = parse_date(self.date)
            if self.date is None:
                raise ValueError(f"Invalid date value")
        
        # Ensure amount is float
        if not isinstance(self.amount, float):
            self.amount = parse_amount(self.amount)
        
        # Validate required fields
        if not self.id or not self.id.strip():
            raise ValueError("Dividend ID is required")
        if not self.name or not self.name.strip():
            raise ValueError("Asset name is required")
        
        # Validate reinvested value
        if self.reinvested not in ["Yes", "No"]:
            # Try to convert boolean or other values
            if isinstance(self.reinvested, bool):
                self.reinvested = "Yes" if self.reinvested else "No"
            else:
                reinvest_str = str(self.reinvested).strip().lower()
                if reinvest_str in ['yes', 'true', '1']:
                    self.reinvested = "Yes"
                else:
                    self.reinvested = "No"
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Dividend':
        """
        Create a Dividend instance from a dictionary.
        
        Args:
            data: Dictionary containing dividend data
            
        Returns:
            Dividend instance
            
        Example:
            >>> data = {'id': '123', 'date': '2025-01-15', 'name': 'AAPL', 
            ...         'category': 'Stocks', 'amount': '100', 'reinvested': 'Yes'}
            >>> dividend = Dividend.from_dict(data)
        """
        return cls(
            id=str(data.get('id', '')).strip(),
            date=parse_date(data.get('date')),
            name=str(data.get('name', '')).strip(),
            category=str(data.get('category', '')).strip(),
            amount=parse_amount(data.get('amount', 0)),
            reinvested=str(data.get('reinvested', 'No')).strip(),
            note=str(data.get('note', '')).strip()
        )
    
    def to_dict(self) -> Dict[str, Any]:
        """
        Convert Dividend instance to dictionary.
        
        Returns:
            Dictionary representation of the dividend
        """
        return {
            'id': self.id,
            'date': format_date(self.date),
            'name': self.name,
            'category': self.category,
            'amount': self.amount,
            'reinvested': self.reinvested,
            'note': self.note
        }
    
    def to_sheet_row(self) -> list:
        """
        Convert Dividend to a row format for Google Sheets.
        
        Returns:
            List of values in the order: [ID, Date, Asset Name, Category, Amount, Reinvested, Note]
        """
        return [
            self.id,
            format_date(self.date, output_format="%Y-%m-%d"),
            self.name,
            self.category,
            self.amount,
            self.reinvested,
            self.note
        ]
    
    def is_reinvested(self) -> bool:
        """
        Check if the dividend was reinvested.
        
        Returns:
            True if reinvested, False otherwise
        """
        return self.reinvested == "Yes"
    
    def get_monthly_key(self) -> str:
        """
        Get the month key for grouping (YYYY-MM format).
        
        Returns:
            Month key string
        """
        return self.date.strftime("%Y-%m")
    
    def get_year(self) -> int:
        """
        Get the year of the dividend payment.
        
        Returns:
            Year as integer
        """
        return self.date.year
    
    def __str__(self) -> str:
        """String representation of the dividend."""
        reinvest_status = "Reinvested" if self.is_reinvested() else "Received"
        return f"Dividend({self.name}, ฿{self.amount:,.2f} on {format_date(self.date)} - {reinvest_status})"

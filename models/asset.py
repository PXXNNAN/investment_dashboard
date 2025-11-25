"""
Asset data model representing a portfolio asset snapshot.
"""
from dataclasses import dataclass
from datetime import datetime
from typing import Optional, Dict, Any
from utils.date_utils import parse_date, format_date
from utils.amount_utils import parse_amount


@dataclass
class Asset:
    """
    Represents a single asset record in the portfolio.
    
    Attributes:
        id: Unique identifier (UUID)
        date: Date of the asset snapshot
        name: Asset name/description
        category: Asset category (e.g., Stocks, Bonds)
        amount: Asset value
    """
    id: str
    date: datetime
    name: str
    category: str
    amount: float
    
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
            raise ValueError("Asset ID is required")
        if not self.name or not self.name.strip():
            raise ValueError("Asset name is required")
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Asset':
        """
        Create an Asset instance from a dictionary.
        
        Args:
            data: Dictionary containing asset data
            
        Returns:
            Asset instance
            
        Example:
            >>> data = {'id': '123', 'date': '2025-01-15', 'name': 'AAPL', 
            ...         'category': 'Stocks', 'amount': '1000'}
            >>> asset = Asset.from_dict(data)
        """
        return cls(
            id=str(data.get('id', '')).strip(),
            date=parse_date(data.get('date')),
            name=str(data.get('name', '')).strip(),
            category=str(data.get('category', '')).strip(),
            amount=parse_amount(data.get('amount', 0))
        )
    
    def to_dict(self) -> Dict[str, Any]:
        """
        Convert Asset instance to dictionary.
        
        Returns:
            Dictionary representation of the asset
        """
        return {
            'id': self.id,
            'date': format_date(self.date),
            'name': self.name,
            'category': self.category,
            'amount': self.amount
        }
    
    def to_sheet_row(self) -> list:
        """
        Convert Asset to a row format for Google Sheets.
        
        Returns:
            List of values in the order: [ID, Date, Amount, Description, Category]
        """
        return [
            self.id,
            format_date(self.date, output_format="%Y-%m-%d"),
            self.amount,
            self.name,
            self.category
        ]
    
    def __str__(self) -> str:
        """String representation of the asset."""
        return f"Asset({self.name}, {self.category}, ฿{self.amount:,.2f} on {format_date(self.date)})"

"""
Investment data model representing an investment transaction.
"""
from dataclasses import dataclass
from datetime import datetime
from typing import Optional, Dict, Any
from utils.date_utils import parse_date, format_date
from utils.amount_utils import parse_amount


@dataclass
class Investment:
    """
    Represents a single investment transaction.
    
    Attributes:
        id: Unique identifier (UUID)
        date: Transaction date
        action: Transaction type (Deposit, Withdraw, Buy, Sell)
        name: Asset name
        category: Asset category
        quantity: Number of units (optional for Deposit/Withdraw)
        price: Unit price (optional for Deposit/Withdraw)
        amount: Total transaction amount
        note: Additional notes (optional)
    """
    id: str
    date: datetime
    action: str
    name: str
    category: str
    amount: float
    quantity: Optional[float] = None
    price: Optional[float] = None
    note: str = ""
    
    # Valid transaction types
    VALID_ACTIONS = ['Deposit', 'Withdraw', 'Buy', 'Sell']
    
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
        
        # Convert quantity and price if provided
        if self.quantity is not None and not isinstance(self.quantity, float):
            self.quantity = parse_amount(self.quantity) if self.quantity else None
        
        if self.price is not None and not isinstance(self.price, float):
            self.price = parse_amount(self.price) if self.price else None
        
        # Validate required fields
        if not self.id or not self.id.strip():
            raise ValueError("Investment ID is required")
        if not self.name or not self.name.strip():
            raise ValueError("Asset name is required")
        if not self.action or not self.action.strip():
            raise ValueError("Transaction action is required")
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Investment':
        """
        Create an Investment instance from a dictionary.
        
        Args:
            data: Dictionary containing investment data
            
        Returns:
            Investment instance
        """
        return cls(
            id=str(data.get('id', '')).strip(),
            date=parse_date(data.get('date')),
            action=str(data.get('action', '')).strip(),
            name=str(data.get('name', '')).strip(),
            category=str(data.get('category', '')).strip(),
            quantity=parse_amount(data.get('qty')) if data.get('qty') else None,
            price=parse_amount(data.get('price')) if data.get('price') else None,
            amount=parse_amount(data.get('amount', 0)),
            note=str(data.get('note', '')).strip()
        )
    
    def to_dict(self) -> Dict[str, Any]:
        """
        Convert Investment instance to dictionary.
        
        Returns:
            Dictionary representation of the investment
        """
        return {
            'id': self.id,
            'date': format_date(self.date),
            'action': self.action,
            'name': self.name,
            'category': self.category,
            'qty': self.quantity if self.quantity is not None else '',
            'price': self.price if self.price is not None else '',
            'amount': self.amount,
            'note': self.note
        }
    
    def to_sheet_row(self) -> list:
        """
        Convert Investment to a row format for Google Sheets.
        
        Returns:
            List of values in the order: [ID, Date, Action, Asset, Category, Qty, Price, Amount, Note]
        """
        return [
            self.id,
            format_date(self.date, output_format="%Y-%m-%d"),
            self.action,
            self.name,
            self.category,
            self.quantity if self.quantity is not None else '',
            self.price if self.price is not None else '',
            self.amount,
            self.note
        ]
    
    def is_cash_flow(self) -> bool:
        """Check if this is a cash flow transaction (Deposit/Withdraw)."""
        return self.action.lower() in ['deposit', 'withdraw']
    
    def is_trade(self) -> bool:
        """Check if this is a trade transaction (Buy/Sell)."""
        return self.action.lower() in ['buy', 'sell']
    
    def get_flow_amount(self) -> float:
        """
        Get the cash flow amount (positive for deposits, negative for withdrawals).
        
        Returns:
            Flow amount
        """
        if self.action.lower() == 'deposit':
            return abs(self.amount)
        elif self.action.lower() == 'withdraw':
            return -abs(self.amount)
        return 0.0
    
    def __str__(self) -> str:
        """String representation of the investment."""
        return f"Investment({self.action} {self.name}, ฿{self.amount:,.2f} on {format_date(self.date)})"

"""
Unit tests for Investment model.
"""
import pytest
from datetime import datetime
from models.investment import Investment


class TestInvestmentCreation:
    """Tests for Investment creation and initialization."""
    
    def test_create_investment_with_valid_data(self, sample_investment_data):
        """Test creating investment with valid data."""
        investment = Investment.from_dict(sample_investment_data)
        
        assert investment.id == 'test-uuid-456'
        assert investment.name == 'Cash'
        assert investment.action == 'Deposit'
        assert investment.amount == 10000.0
        assert investment.note == 'Initial deposit'
    
    def test_create_investment_with_optional_fields(self):
        """Test creating investment with quantity and price."""
        investment = Investment(
            id='test-123',
            date=datetime(2025, 1, 15),
            action='Buy',
            name='AAPL',
            category='Stocks',
            quantity=10.0,
            price=150.0,
            amount=1500.0,
            note='Buy order'
        )
        
        assert investment.quantity == 10.0
        assert investment.price == 150.0
    
    def test_investment_validates_required_id(self):
        """Test that empty ID raises error."""
        with pytest.raises(ValueError, match="Investment ID is required"):
            Investment(
                id='',
                date=datetime(2025, 1, 15),
                action='Deposit',
                name='Cash',
                category='Cash',
                amount=1000.0
            )
    
    def test_investment_validates_required_name(self):
        """Test that empty name raises error."""
        with pytest.raises(ValueError, match="Asset name is required"):
            Investment(
                id='test-123',
                date=datetime(2025, 1, 15),
                action='Deposit',
                name='',
                category='Cash',
                amount=1000.0
            )
    
    def test_investment_validates_required_action(self):
        """Test that empty action raises error."""
        with pytest.raises(ValueError, match="Transaction action is required"):
            Investment(
                id='test-123',
                date=datetime(2025, 1, 15),
                action='',
                name='Cash',
                category='Cash',
                amount=1000.0
            )


class TestInvestmentBusinessLogic:
    """Tests for Investment business logic methods."""
    
    def test_is_cash_flow_deposit(self):
        """Test is_cash_flow for deposit."""
        investment = Investment(
            id='test-123',
            date=datetime(2025, 1, 15),
            action='Deposit',
            name='Cash',
            category='Cash',
            amount=1000.0
        )
        
        assert investment.is_cash_flow() is True
        assert investment.is_trade() is False
    
    def test_is_cash_flow_withdraw(self):
        """Test is_cash_flow for withdraw."""
        investment = Investment(
            id='test-123',
            date=datetime(2025, 1, 15),
            action='Withdraw',
            name='Cash',
            category='Cash',
            amount=500.0
        )
        
        assert investment.is_cash_flow() is True
        assert investment.is_trade() is False
    
    def test_is_trade_buy(self):
        """Test is_trade for buy."""
        investment = Investment(
            id='test-123',
            date=datetime(2025, 1, 15),
            action='Buy',
            name='AAPL',
            category='Stocks',
            amount=1500.0
        )
        
        assert investment.is_trade() is True
        assert investment.is_cash_flow() is False
    
    def test_get_flow_amount_deposit(self):
        """Test get_flow_amount for deposit (positive)."""
        investment = Investment(
            id='test-123',
            date=datetime(2025, 1, 15),
            action='Deposit',
            name='Cash',
            category='Cash',
            amount=1000.0
        )
        
        assert investment.get_flow_amount() == 1000.0
    
    def test_get_flow_amount_withdraw(self):
        """Test get_flow_amount for withdraw (negative)."""
        investment = Investment(
            id='test-123',
            date=datetime(2025, 1, 15),
            action='Withdraw',
            name='Cash',
            category='Cash',
            amount=500.0
        )
        
        assert investment.get_flow_amount() == -500.0
    
    def test_get_flow_amount_buy(self):
        """Test get_flow_amount for buy (zero)."""
        investment = Investment(
            id='test-123',
            date=datetime(2025, 1, 15),
            action='Buy',
            name='AAPL',
            category='Stocks',
            amount=1500.0
        )
        
        assert investment.get_flow_amount() == 0.0


class TestInvestmentConversion:
    """Tests for Investment conversion methods."""
    
    def test_to_dict(self):
        """Test converting investment to dictionary."""
        investment = Investment(
            id='test-123',
            date=datetime(2025, 1, 15),
            action='Deposit',
            name='Cash',
            category='Cash',
            amount=1000.0,
            note='Test'
        )
        
        result = investment.to_dict()
        
        assert result['id'] == 'test-123'
        assert result['action'] == 'Deposit'
        assert result['name'] == 'Cash'
        assert result['amount'] == 1000.0
    
    def test_to_sheet_row(self):
        """Test converting investment to sheet row format."""
        investment = Investment(
            id='test-123',
            date=datetime(2025, 1, 15),
            action='Deposit',
            name='Cash',
            category='Cash',
            amount=1000.0,
            note='Test'
        )
        
        result = investment.to_sheet_row()
        
        assert result[0] == 'test-123'
        assert result[1] == '2025-01-15'
        assert result[2] == 'Deposit'
        assert result[7] == 1000.0

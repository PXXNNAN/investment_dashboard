"""
Unit tests for Dividend model.
"""
import pytest
from datetime import datetime
from models.dividend import Dividend


class TestDividendCreation:
    """Tests for Dividend creation and initialization."""
    
    def test_create_dividend_with_valid_data(self):
        """Test creating dividend with valid data."""
        dividend = Dividend(
            id='test-123',
            date=datetime(2025, 1, 15),
            name='AAPL',
            category='Stocks',
            amount=100.0,
            reinvested='Yes',
            note='Q1 dividend'
        )
        
        assert dividend.id == 'test-123'
        assert dividend.name == 'AAPL'
        assert dividend.amount == 100.0
        assert dividend.reinvested == 'Yes'
    
    def test_create_dividend_from_dict(self):
        """Test creating dividend from dictionary."""
        data = {
            'id': 'test-456',
            'date': '2025-01-15',
            'name': 'TSLA',
            'category': 'Stocks',
            'amount': '50.50',
            'reinvested': 'No',
            'note': 'Test'
        }
        
        dividend = Dividend.from_dict(data)
        
        assert dividend.id == 'test-456'
        assert dividend.name == 'TSLA'
        assert dividend.amount == 50.50
        assert isinstance(dividend.date, datetime)
    
    def test_dividend_validates_required_id(self):
        """Test that empty ID raises error."""
        with pytest.raises(ValueError, match="Dividend ID is required"):
            Dividend(
                id='',
                date=datetime(2025, 1, 15),
                name='AAPL',
                category='Stocks',
                amount=100.0
            )
    
    def test_dividend_validates_required_name(self):
        """Test that empty name raises error."""
        with pytest.raises(ValueError, match="Asset name is required"):
            Dividend(
                id='test-123',
                date=datetime(2025, 1, 15),
                name='',
                category='Stocks',
                amount=100.0
            )
    
    def test_dividend_converts_string_date(self):
        """Test that string dates are converted to datetime."""
        dividend = Dividend(
            id='test-123',
            date='2025-01-15',
            name='AAPL',
            category='Stocks',
            amount=100.0
        )
        
        assert isinstance(dividend.date, datetime)
        assert dividend.date == datetime(2025, 1, 15)
    
    def test_dividend_converts_string_amount(self):
        """Test that string amounts are converted to float."""
        dividend = Dividend(
            id='test-123',
            date=datetime(2025, 1, 15),
            name='AAPL',
            category='Stocks',
            amount='100.50'
        )
        
        assert isinstance(dividend.amount, float)
        assert dividend.amount == 100.50
    
    def test_dividend_default_reinvested_no(self):
        """Test that default reinvested value is No."""
        dividend = Dividend(
            id='test-123',
            date=datetime(2025, 1, 15),
            name='AAPL',
            category='Stocks',
            amount=100.0
        )
        
        assert dividend.reinvested == 'No'
    
    def test_dividend_converts_boolean_reinvested(self):
        """Test that boolean reinvested is converted to Yes/No."""
        dividend_yes = Dividend(
            id='test-123',
            date=datetime(2025, 1, 15),
            name='AAPL',
            category='Stocks',
            amount=100.0,
            reinvested=True
        )
        
        assert dividend_yes.reinvested == 'Yes'
        
        dividend_no = Dividend(
            id='test-456',
            date=datetime(2025, 1, 15),
            name='TSLA',
            category='Stocks',
            amount=50.0,
            reinvested=False
        )
        
        assert dividend_no.reinvested == 'No'


class TestDividendBusinessLogic:
    """Tests for Dividend business logic methods."""
    
    def test_is_reinvested_yes(self):
        """Test is_reinvested returns True for Yes."""
        dividend = Dividend(
            id='test-123',
            date=datetime(2025, 1, 15),
            name='AAPL',
            category='Stocks',
            amount=100.0,
            reinvested='Yes'
        )
        
        assert dividend.is_reinvested() is True
    
    def test_is_reinvested_no(self):
        """Test is_reinvested returns False for No."""
        dividend = Dividend(
            id='test-123',
            date=datetime(2025, 1, 15),
            name='AAPL',
            category='Stocks',
            amount=100.0,
            reinvested='No'
        )
        
        assert dividend.is_reinvested() is False
    
    def test_get_monthly_key(self):
        """Test get_monthly_key returns correct format."""
        dividend = Dividend(
            id='test-123',
            date=datetime(2025, 1, 15),
            name='AAPL',
            category='Stocks',
            amount=100.0
        )
        
        assert dividend.get_monthly_key() == '2025-01'
    
    def test_get_year(self):
        """Test get_year returns correct year."""
        dividend = Dividend(
            id='test-123',
            date=datetime(2025, 1, 15),
            name='AAPL',
            category='Stocks',
            amount=100.0
        )
        
        assert dividend.get_year() == 2025


class TestDividendConversion:
    """Tests for Dividend conversion methods."""
    
    def test_to_dict(self):
        """Test converting dividend to dictionary."""
        dividend = Dividend(
            id='test-123',
            date=datetime(2025, 1, 15),
            name='AAPL',
            category='Stocks',
            amount=100.50,
            reinvested='Yes',
            note='Test note'
        )
        
        result = dividend.to_dict()
        
        assert result['id'] == 'test-123'
        assert result['name'] == 'AAPL'
        assert result['amount'] == 100.50
        assert result['reinvested'] == 'Yes'
        assert result['date'] == '15/01/2025'
    
    def test_to_sheet_row(self):
        """Test converting dividend to sheet row format."""
        dividend = Dividend(
            id='test-123',
            date=datetime(2025, 1, 15),
            name='AAPL',
            category='Stocks',
            amount=100.50,
            reinvested='Yes',
            note='Test'
        )
        
        result = dividend.to_sheet_row()
        
        assert result == ['test-123', '2025-01-15', 'AAPL', 'Stocks', 100.50, 'Yes', 'Test']
    
    def test_from_dict_with_missing_optional_fields(self):
        """Test creating dividend from dict with missing optional fields."""
        data = {
            'id': 'test-123',
            'date': '2025-01-15',
            'name': 'AAPL',
            'category': 'Stocks',
            'amount': '100'
        }
        
        dividend = Dividend.from_dict(data)
        
        assert dividend.reinvested == 'No'
        assert dividend.note == ''


class TestDividendStringRepresentation:
    """Tests for Dividend string representation."""
    
    def test_str_representation_reinvested(self):
        """Test string representation for reinvested dividend."""
        dividend = Dividend(
            id='test-123',
            date=datetime(2025, 1, 15),
            name='AAPL',
            category='Stocks',
            amount=100.50,
            reinvested='Yes'
        )
        
        result = str(dividend)
        
        assert 'AAPL' in result
        assert '100.50' in result
        assert 'Reinvested' in result
    
    def test_str_representation_received(self):
        """Test string representation for received dividend."""
        dividend = Dividend(
            id='test-123',
            date=datetime(2025, 1, 15),
            name='AAPL',
            category='Stocks',
            amount=100.50,
            reinvested='No'
        )
        
        result = str(dividend)
        
        assert 'AAPL' in result
        assert 'Received' in result

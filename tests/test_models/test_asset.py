"""
Unit tests for Asset model.
"""
import pytest
from datetime import datetime
from models.asset import Asset


class TestAssetCreation:
    """Tests for Asset creation and initialization."""
    
    def test_create_asset_with_valid_data(self, sample_asset_data):
        """Test creating asset with valid data."""
        asset = Asset.from_dict(sample_asset_data)
        
        assert asset.id == 'test-uuid-123'
        assert asset.name == 'AAPL'
        assert asset.category == 'Stocks'
        assert asset.amount == 1000.50
        assert isinstance(asset.date, datetime)
    
    def test_create_asset_directly(self):
        """Test creating asset directly."""
        asset = Asset(
            id='test-123',
            date=datetime(2025, 1, 15),
            name='AAPL',
            category='Stocks',
            amount=1000.0
        )
        
        assert asset.id == 'test-123'
        assert asset.name == 'AAPL'
    
    def test_asset_validates_required_id(self):
        """Test that empty ID raises error."""
        with pytest.raises(ValueError, match="Asset ID is required"):
            Asset(
                id='',
                date=datetime(2025, 1, 15),
                name='AAPL',
                category='Stocks',
                amount=1000.0
            )
    
    def test_asset_validates_required_name(self):
        """Test that empty name raises error."""
        with pytest.raises(ValueError, match="Asset name is required"):
            Asset(
                id='test-123',
                date=datetime(2025, 1, 15),
                name='',
                category='Stocks',
                amount=1000.0
            )
    
    def test_asset_converts_string_date(self):
        """Test that string dates are converted to datetime."""
        asset = Asset(
            id='test-123',
            date='2025-01-15',
            name='AAPL',
            category='Stocks',
            amount=1000.0
        )
        
        assert isinstance(asset.date, datetime)
        assert asset.date == datetime(2025, 1, 15)
    
    def test_asset_converts_string_amount(self):
        """Test that string amounts are converted to float."""
        asset = Asset(
            id='test-123',
            date=datetime(2025, 1, 15),
            name='AAPL',
            category='Stocks',
            amount='1,000.50'
        )
        
        assert isinstance(asset.amount, float)
        assert asset.amount == 1000.50


class TestAssetConversion:
    """Tests for Asset conversion methods."""
    
    def test_to_dict(self):
        """Test converting asset to dictionary."""
        asset = Asset(
            id='test-123',
            date=datetime(2025, 1, 15),
            name='AAPL',
            category='Stocks',
            amount=1000.50
        )
        
        result = asset.to_dict()
        
        assert result['id'] == 'test-123'
        assert result['name'] == 'AAPL'
        assert result['category'] == 'Stocks'
        assert result['amount'] == 1000.50
        assert result['date'] == '15/01/2025'
    
    def test_to_sheet_row(self):
        """Test converting asset to sheet row format."""
        asset = Asset(
            id='test-123',
            date=datetime(2025, 1, 15),
            name='AAPL',
            category='Stocks',
            amount=1000.50
        )
        
        result = asset.to_sheet_row()
        
        assert result == ['test-123', '2025-01-15', 1000.50, 'AAPL', 'Stocks']
    
    def test_from_dict(self, sample_asset_data):
        """Test creating asset from dictionary."""
        asset = Asset.from_dict(sample_asset_data)
        
        assert asset.id == 'test-uuid-123'
        assert asset.name == 'AAPL'
        assert asset.category == 'Stocks'


class TestAssetStringRepresentation:
    """Tests for Asset string representation."""
    
    def test_str_representation(self):
        """Test string representation of asset."""
        asset = Asset(
            id='test-123',
            date=datetime(2025, 1, 15),
            name='AAPL',
            category='Stocks',
            amount=1000.50
        )
        
        result = str(asset)
        
        assert 'AAPL' in result
        assert 'Stocks' in result
        assert '1,000.50' in result

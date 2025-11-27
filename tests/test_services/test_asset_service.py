"""
Unit tests for AssetService.
"""
import pytest
from unittest.mock import Mock, MagicMock, patch
from datetime import datetime
from services.asset_service import AssetService


class TestAssetService:
    """Test cases for AssetService."""
    
    @pytest.fixture
    def mock_sheets_client(self):
        """Create a mock Google Sheets client."""
        return Mock()
    
    @pytest.fixture
    def asset_service(self, mock_sheets_client):
        """Create an AssetService instance with mocked sheets client."""
        return AssetService(sheets_client=mock_sheets_client)
    
    @pytest.fixture
    def sample_asset_records(self):
        """Sample asset records from Google Sheets."""
        return [
            {'ID': '1', 'Date': '01/01/2024', 'Description': 'BTC', 'Category': 'Crypto', 'Amount': '50000'},
            {'ID': '2', 'Date': '01/02/2024', 'Description': 'ETH', 'Category': 'Crypto', 'Amount': '30000'},
            {'ID': '3', 'Date': '01/03/2024', 'Description': 'AAPL', 'Category': 'Stocks', 'Amount': '20000'},
        ]
    
    def test_get_records_basic(self, asset_service, mock_sheets_client, sample_asset_records):
        """Test getting asset records without filters."""
        mock_sheets_client.get_all_records.return_value = sample_asset_records
        
        records = asset_service.get_records()
        
        assert len(records) == 3
        assert records[0]['name'] == 'AAPL'  # Sorted by date descending
        assert records[1]['name'] == 'ETH'
        assert records[2]['name'] == 'BTC'
    
    def test_get_records_with_name_filter(self, asset_service, mock_sheets_client, sample_asset_records):
        """Test filtering asset records by name."""
        mock_sheets_client.get_all_records.return_value = sample_asset_records
        
        records = asset_service.get_records(filter_name='BTC')
        
        assert len(records) == 1
        assert records[0]['name'] == 'BTC'
    
    def test_get_records_with_category_filter(self, asset_service, mock_sheets_client, sample_asset_records):
        """Test filtering asset records by category."""
        mock_sheets_client.get_all_records.return_value = sample_asset_records
        
        records = asset_service.get_records(filter_category='Crypto')
        
        assert len(records) == 2
        assert all(r['category'] == 'Crypto' for r in records)
    
    def test_get_records_with_year_filter(self, asset_service, mock_sheets_client, sample_asset_records):
        """Test filtering asset records by year."""
        mock_sheets_client.get_all_records.return_value = sample_asset_records
        
        records = asset_service.get_records(filter_year=2024)
        
        assert len(records) == 3
    
    def test_add_record(self, asset_service, mock_sheets_client):
        """Test adding a new asset record."""
        mock_sheets_client.append_row.return_value = True
        
        data = {
            'date': '01/01/2024',
            'name': 'BTC',
            'amount': '50000',
            'category': 'Crypto'
        }
        
        result = asset_service.add_record(data)
        
        assert result is True
        mock_sheets_client.append_row.assert_called_once()
    
    def test_delete_record(self, asset_service, mock_sheets_client):
        """Test deleting an asset record."""
        mock_cell = Mock()
        mock_cell.row = 5
        mock_sheets_client.find_cell.return_value = mock_cell
        mock_sheets_client.delete_row.return_value = True
        
        result = asset_service.delete_record('test-id')
        
        assert result is True
        mock_sheets_client.delete_row.assert_called_once()
    
    def test_update_record(self, asset_service, mock_sheets_client):
        """Test updating an asset record."""
        mock_cell = Mock()
        mock_cell.row = 5
        mock_sheets_client.find_cell.return_value = mock_cell
        mock_sheets_client.batch_update.return_value = True
        
        data = {
            'date': '01/01/2024',
            'name': 'BTC',
            'amount': '60000',
            'category': 'Crypto'
        }
        
        result = asset_service.update_record('test-id', data)
        
        assert result is True
        mock_sheets_client.batch_update.assert_called_once()
    
    def test_get_latest_portfolio_value(self, asset_service, mock_sheets_client, sample_asset_records):
        """Test getting latest portfolio value."""
        mock_sheets_client.get_all_records.return_value = sample_asset_records
        
        total_value = asset_service.get_latest_portfolio_value()
        
        assert total_value == 100000  # 50000 + 30000 + 20000

"""
Unit tests for InvestmentService.
"""
import pytest
from unittest.mock import Mock
from services.investment_service import InvestmentService


class TestInvestmentService:
    """Test cases for InvestmentService."""
    
    @pytest.fixture
    def mock_sheets_client(self):
        return Mock()
    
    @pytest.fixture
    def investment_service(self, mock_sheets_client):
        return InvestmentService(sheets_client=mock_sheets_client)
    
    @pytest.fixture
    def sample_investment_records(self):
        return [
            {'ID': '1', 'Date': '01/01/2024', 'Action': 'Buy', 'Asset': 'BTC', 'Category': 'Crypto', 
             'Quantity': '0.1', 'Unit Price': '40000', 'Total Amount': '-4000', 'Note': ''},
            {'ID': '2', 'Date': '01/02/2024', 'Action': 'Sell', 'Asset': 'BTC', 'Category': 'Crypto', 
             'Quantity': '0.05', 'Unit Price': '45000', 'Total Amount': '2250', 'Note': ''},
            {'ID': '3', 'Date': '01/03/2024', 'Action': 'Deposit', 'Asset': 'Cash', 'Category': 'Cash', 
             'Quantity': '', 'Unit Price': '', 'Total Amount': '10000', 'Note': ''},
        ]
    
    def test_get_records_all(self, investment_service, mock_sheets_client, sample_investment_records):
        """Test getting all investment records."""
        mock_sheets_client.get_all_records.return_value = sample_investment_records
        
        records = investment_service.get_records()
        
        assert len(records) == 3
    
    def test_get_records_filter_by_action(self, investment_service, mock_sheets_client, sample_investment_records):
        """Test filtering by action type."""
        mock_sheets_client.get_all_records.return_value = sample_investment_records
        
        records = investment_service.get_records(filter_action='Buy')
        
        assert len(records) == 1
        assert records[0]['action'] == 'Buy'
    
    def test_get_records_filter_by_name(self, investment_service, mock_sheets_client, sample_investment_records):
        """Test filtering by asset name."""
        mock_sheets_client.get_all_records.return_value = sample_investment_records
        
        records = investment_service.get_records(filter_name='BTC')
        
        assert len(records) == 2
    
    def test_add_record(self, investment_service, mock_sheets_client):
        """Test adding investment record."""
        mock_sheets_client.append_row.return_value = True
        
        data = {
            'date': '01/01/2024',
            'action': 'Buy',
            'name': 'BTC',
            'category': 'Crypto',
            'qty': '0.1',
            'price': '40000',
            'amount': '-4000',
            'note': ''
        }
        
        result = investment_service.add_record(data)
        
        assert result is True
    
    def test_delete_record(self, investment_service, mock_sheets_client):
        """Test deleting investment record."""
        mock_cell = Mock()
        mock_cell.row = 5
        mock_sheets_client.find_cell.return_value = mock_cell
        mock_sheets_client.delete_row.return_value = True
        
        result = investment_service.delete_record('test-id')
        
        assert result is True

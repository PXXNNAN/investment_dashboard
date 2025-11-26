"""
Unit tests for DividendService.
"""
import pytest
from unittest.mock import MagicMock, patch
from datetime import datetime
from services.dividend_service import DividendService


@pytest.fixture
def mock_sheets_client():
    """Mock Google Sheets client for testing."""
    mock_client = MagicMock()
    return mock_client


@pytest.fixture
def sample_dividend_records():
    """Sample dividend records from Google Sheets."""
    return [
        {
            'ID': 'uuid-1',
            'Date': '2025-01-15',
            'Asset Name': 'AAPL',
            'Category': 'Stocks',
            'Dividend Amount': 100,
            'Reinvested': 'Yes',
            'Note': 'Q1'
        },
        {
            'ID': 'uuid-2',
            'Date': '2025-02-15',
            'Asset Name': 'TSLA',
            'Category': 'Stocks',
            'Dividend Amount': 50,
            'Reinvested': 'No',
            'Note': ''
        },
        {
            'ID': 'uuid-3',
            'Date': '2024-12-15',
            'Asset Name': 'AAPL',
            'Category': 'Stocks',
            'Dividend Amount': 95,
            'Reinvested': 'Yes',
            'Note': 'Q4'
        }
    ]


class TestDividendServiceGetRecords:
    """Tests for get_records method."""
    
    def test_get_records_no_filter(self, mock_sheets_client, sample_dividend_records):
        """Test getting all dividend records."""
        mock_sheets_client.get_all_records.return_value = sample_dividend_records
        service = DividendService(mock_sheets_client)
        
        records = service.get_records()
        
        assert len(records) == 3
        assert records[0]['name'] == 'TSLA'  # Sorted by date, newest first
        assert records[1]['name'] == 'AAPL'
    
    def test_get_records_filter_by_name(self, mock_sheets_client, sample_dividend_records):
        """Test filtering records by asset name."""
        mock_sheets_client.get_all_records.return_value = sample_dividend_records
        service = DividendService(mock_sheets_client)
        
        records = service.get_records(filter_name='AAPL')
        
        assert len(records) == 2
        assert all(r['name'] == 'AAPL' for r in records)
    
    def test_get_records_filter_by_year(self, mock_sheets_client, sample_dividend_records):
        """Test filtering records by year."""
        mock_sheets_client.get_all_records.return_value = sample_dividend_records
        service = DividendService(mock_sheets_client)
        
        records = service.get_records(filter_year=2025)
        
        assert len(records) == 2
        assert all('2025' in r['date'] for r in records)
    
    def test_get_records_filter_by_name_and_year(self, mock_sheets_client, sample_dividend_records):
        """Test filtering by both name and year."""
        mock_sheets_client.get_all_records.return_value = sample_dividend_records
        service = DividendService(mock_sheets_client)
        
        records = service.get_records(filter_name='AAPL', filter_year=2025)
        
        assert len(records) == 1
        assert records[0]['name'] == 'AAPL'
        assert '2025' in records[0]['date']
    
    def test_get_records_empty_result(self, mock_sheets_client):
        """Test getting records when sheet is empty."""
        mock_sheets_client.get_all_records.return_value = []
        service = DividendService(mock_sheets_client)
        
        records = service.get_records()
        
        assert records == []
    
    def test_get_records_handles_error(self, mock_sheets_client):
        """Test error handling in get_records."""
        mock_sheets_client.get_all_records.side_effect = Exception("Sheet error")
        service = DividendService(mock_sheets_client)
        
        records = service.get_records()
        
        assert records == []


class TestDividendServiceAddRecord:
    """Tests for add_record method."""
    
    def test_add_record_success(self, mock_sheets_client):
        """Test successfully adding a dividend record."""
        mock_sheets_client.append_row.return_value = True
        service = DividendService(mock_sheets_client)
        
        data = {
            'date': '2025-01-15',
            'name': 'AAPL',
            'category': 'Stocks',
            'amount': '100',
            'reinvested': 'Yes',
            'note': 'Test'
        }
        
        result = service.add_record(data)
        
        assert result is True
        mock_sheets_client.append_row.assert_called_once()
    
    def test_add_record_validates_data(self, mock_sheets_client):
        """Test that add_record validates data through model."""
        mock_sheets_client.append_row.return_value = True
        service = DividendService(mock_sheets_client)
        
        # Missing required field (name)
        data = {
            'date': '2025-01-15',
            'name': '',
            'category': 'Stocks',
            'amount': '100'
        }
        
        result = service.add_record(data)
        
        assert result is False
    
    def test_add_record_handles_error(self, mock_sheets_client):
        """Test error handling in add_record."""
        mock_sheets_client.append_row.side_effect = Exception("Sheet error")
        service = DividendService(mock_sheets_client)
        
        data = {
            'date': '2025-01-15',
            'name': 'AAPL',
            'category': 'Stocks',
            'amount': '100'
        }
        
        result = service.add_record(data)
        
        assert result is False


class TestDividendServiceChartData:
    """Tests for get_chart_data method."""
    
    def test_get_chart_data_success(self, mock_sheets_client):
        """Test generating chart data from records."""
        service = DividendService(mock_sheets_client)
        
        records = [
            {'date': '15/01/2025', 'amount': 100},
            {'date': '15/02/2025', 'amount': 50},
            {'date': '15/01/2025', 'amount': 50}  # Same month
        ]
        
        chart_data = service.get_chart_data(records)
        
        assert 'labels' in chart_data
        assert 'datasets' in chart_data
        assert len(chart_data['labels']) == 12  # All months
        assert chart_data['datasets'][0]['data'][0] == 150  # Jan total
        assert chart_data['datasets'][0]['data'][1] == 50   # Feb total
    
    def test_get_chart_data_empty_records(self, mock_sheets_client):
        """Test chart data with empty records."""
        service = DividendService(mock_sheets_client)
        
        chart_data = service.get_chart_data([])
        
        assert chart_data['labels'] == ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 
                                         'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
        assert all(v == 0 for v in chart_data['datasets'][0]['data'])


class TestDividendServiceAnalysisData:
    """Tests for get_analysis_data method."""
    
    def test_get_analysis_data_yearly(self, mock_sheets_client, sample_dividend_records):
        """Test yearly analysis data."""
        mock_sheets_client.get_all_records.return_value = sample_dividend_records
        service = DividendService(mock_sheets_client)
        
        chart_data = service.get_analysis_data(mode='yearly')
        
        assert 'labels' in chart_data
        assert 'datasets' in chart_data
        assert '2024' in chart_data['labels']
        assert '2025' in chart_data['labels']
    
    def test_get_analysis_data_monthly(self, mock_sheets_client, sample_dividend_records):
        """Test monthly analysis data."""
        mock_sheets_client.get_all_records.return_value = sample_dividend_records
        service = DividendService(mock_sheets_client)
        
        chart_data = service.get_analysis_data(mode='monthly')
        
        assert 'labels' in chart_data
        assert len(chart_data['labels']) == 3  # 3 different months
    
    def test_get_analysis_data_with_filter(self, mock_sheets_client, sample_dividend_records):
        """Test analysis data with asset filter."""
        mock_sheets_client.get_all_records.return_value = sample_dividend_records
        service = DividendService(mock_sheets_client)
        
        chart_data = service.get_analysis_data(mode='yearly', filter_name='AAPL')
        
        # Should only include AAPL dividends
        assert chart_data['datasets'][0]['label'] == 'Dividend Income (AAPL)'


class TestDividendServiceCalculations:
    """Tests for calculation methods."""
    
    def test_get_total_dividends(self, mock_sheets_client, sample_dividend_records):
        """Test calculating total dividends."""
        mock_sheets_client.get_all_records.return_value = sample_dividend_records
        service = DividendService(mock_sheets_client)
        
        total = service.get_total_dividends(year=2025)
        
        assert total == 150  # 100 + 50
    
    def test_get_total_dividends_all_time(self, mock_sheets_client, sample_dividend_records):
        """Test total dividends for all time."""
        mock_sheets_client.get_all_records.return_value = sample_dividend_records
        service = DividendService(mock_sheets_client)
        
        total = service.get_total_dividends()
        
        assert total == 245  # 100 + 50 + 95
    
    def test_get_monthly_average(self, mock_sheets_client, sample_dividend_records):
        """Test calculating monthly average."""
        mock_sheets_client.get_all_records.return_value = sample_dividend_records
        service = DividendService(mock_sheets_client)
        
        avg = service.get_monthly_average(year=2025)
        
        assert avg == 150 / 12  # Total / 12 months
    
    def test_get_monthly_average_no_dividends(self, mock_sheets_client):
        """Test monthly average with no dividends."""
        mock_sheets_client.get_all_records.return_value = []
        service = DividendService(mock_sheets_client)
        
        avg = service.get_monthly_average(year=2025)
        
        assert avg == 0.0

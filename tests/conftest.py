"""
Pytest configuration and shared fixtures.
"""
import pytest
from datetime import datetime
from unittest.mock import Mock, MagicMock


@pytest.fixture
def sample_asset_data():
    """Sample asset data for testing."""
    return {
        'id': 'test-uuid-123',
        'date': '2025-01-15',
        'name': 'AAPL',
        'category': 'Stocks',
        'amount': '1000.50'
    }


@pytest.fixture
def sample_investment_data():
    """Sample investment data for testing."""
    return {
        'id': 'test-uuid-456',
        'date': '2025-01-15',
        'action': 'Deposit',
        'name': 'Cash',
        'category': 'Cash',
        'qty': '',
        'price': '',
        'amount': '10000',
        'note': 'Initial deposit'
    }


@pytest.fixture
def mock_google_sheets_client():
    """Mock Google Sheets client for testing."""
    mock_client = MagicMock()
    
    # Mock worksheet
    mock_worksheet = MagicMock()
    mock_worksheet.get_all_records.return_value = []
    mock_worksheet.get_all_values.return_value = []
    mock_worksheet.append_row.return_value = None
    mock_worksheet.append_rows.return_value = None
    
    # Mock sheet
    mock_sheet = MagicMock()
    mock_sheet.worksheet.return_value = mock_worksheet
    
    # Mock client
    mock_client.open.return_value = mock_sheet
    
    return mock_client


@pytest.fixture
def sample_sheet_records():
    """Sample records from Google Sheets."""
    return [
        {
            'ID': 'uuid-1',
            'Date': '2025-01-15',
            'Amount': 1000,
            'Description': 'AAPL',
            'Category': 'Stocks'
        },
        {
            'ID': 'uuid-2',
            'Date': '2025-01-20',
            'Amount': 2000,
            'Description': 'TSLA',
            'Category': 'Stocks'
        }
    ]

"""
Unit tests for SettingsService.
"""
import pytest
from unittest.mock import Mock
from services.settings_service import SettingsService


class TestSettingsService:
    """Test cases for SettingsService."""
    
    @pytest.fixture
    def mock_sheets_client(self):
        return Mock()
    
    @pytest.fixture
    def settings_service(self, mock_sheets_client):
        return SettingsService(sheets_client=mock_sheets_client)
    
    @pytest.fixture
    def sample_settings_data(self):
        return {
            'categories': [
                {'ID': '1', 'Name': 'Crypto', 'Status': 'Active', 'Target %': '50'},
                {'ID': '2', 'Name': 'Stocks', 'Status': 'Active', 'Target %': '30'},
                {'ID': '3', 'Name': 'Bonds', 'Status': 'Inactive', 'Target %': '20'},
            ],
            'assets': [
                {'ID': '1', 'Name': 'BTC', 'Status': 'Active'},
                {'ID': '2', 'Name': 'ETH', 'Status': 'Active'},
                {'ID': '3', 'Name': 'Archived', 'Status': 'Inactive'},
            ]
        }
    
    def test_get_settings_all(self, settings_service, mock_sheets_client):
        """Test getting all settings (active and inactive)."""
        mock_sheets_client.get_all_values.return_value = [
            ['Category', 'Active', 'Target %', 'Asset', 'Active'],  # Header
            ['Crypto', 'TRUE', '50', 'BTC', 'TRUE'],
            ['Stocks', 'TRUE', '30', 'ETH', 'TRUE'],
            ['Bonds', 'FALSE', '20', 'Archived', 'FALSE'],
        ]
        
        settings = settings_service.get_settings(only_active=False)
        
        assert len(settings['categories']) == 3
        assert len(settings['assets']) == 3
    
    def test_get_settings_active_only(self, settings_service, mock_sheets_client):
        """Test getting only active settings."""
        mock_sheets_client.get_all_values.return_value = [
            ['Category', 'Active', 'Target %', 'Asset', 'Active'],  # Header
            ['Crypto', 'TRUE', '50', 'BTC', 'TRUE'],
            ['Stocks', 'TRUE', '30', 'ETH', 'TRUE'],
            ['Bonds', 'FALSE', '20', 'Archived', 'FALSE'],
        ]
        
        settings = settings_service.get_settings(only_active=True)
        
        assert len(settings['categories']) == 2
        assert len(settings['assets']) == 2
        assert all(c['active'] for c in settings['categories'])
        assert all(a['active'] for a in settings['assets'])
    
    def test_update_setting_status_toggle(self, settings_service, mock_sheets_client):
        """Test toggling a setting status."""
        mock_sheets_client.get_all_values.return_value = [
            ['Category', 'Active', 'Target %', 'Asset', 'Active'],
            ['Crypto', 'TRUE', '50', 'BTC', 'TRUE'],
        ]
        mock_sheets_client.update_cell.return_value = True
        
        result = settings_service.update_setting_status('category', 'Crypto', 'toggle')
        
        assert result is True
        mock_sheets_client.update_cell.assert_called_once()
    
    def test_update_setting_target(self, settings_service, mock_sheets_client):
        """Test updating category target percentage."""
        mock_sheets_client.get_all_values.return_value = [
            ['Category', 'Active', 'Target %', 'Asset', 'Active'],
            ['Crypto', 'TRUE', '50', 'BTC', 'TRUE'],
        ]
        mock_sheets_client.update_cell.return_value = True
        
        result = settings_service.update_setting_status('category', 'Crypto', 'update_target', '60')
        
        assert result is True

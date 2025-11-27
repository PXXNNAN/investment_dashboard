"""
Unit tests for DCA (Dollar-Cost Averaging) Dashboard feature.
"""
import pytest
from unittest.mock import Mock, MagicMock
from datetime import datetime
from services.dashboard_service import DashboardService


class TestDCADashboard:
    """Test cases for DCA Dashboard calculations."""
    
    @pytest.fixture
    def mock_sheets_client(self):
        """Create a mock Google Sheets client."""
        return Mock()
    
    @pytest.fixture
    def dashboard_service(self, mock_sheets_client):
        """Create a DashboardService instance with mocked sheets client."""
        return DashboardService(sheets_client=mock_sheets_client)
    
    @pytest.fixture
    def sample_buy_records(self):
        """Sample buy records for testing."""
        return [
            {'ID': '1', 'Date': '2024-01-01', 'Action': 'Buy', 'Asset': 'BTC', 'Category': 'Crypto', 
             'Quantity': 0.1, 'Unit Price': 40000, 'Total Amount': -4000, 'Note': ''},
            {'ID': '2', 'Date': '2024-02-01', 'Action': 'Buy', 'Asset': 'BTC', 'Category': 'Crypto', 
             'Quantity': 0.1, 'Unit Price': 45000, 'Total Amount': -4500, 'Note': ''},
            {'ID': '3', 'Date': '2024-03-01', 'Action': 'Buy', 'Asset': 'ETH', 'Category': 'Crypto', 
             'Quantity': 1.0, 'Unit Price': 3000, 'Total Amount': -3000, 'Note': ''},
            {'ID': '4', 'Date': '2024-04-01', 'Action': 'Deposit', 'Asset': 'Cash', 'Category': 'Cash',
             'Quantity': None, 'Unit Price': None, 'Total Amount': 10000, 'Note': ''},
        ]
    
    @pytest.fixture
    def sample_settings(self):
        """Sample settings data."""
        return {
            'categories': [
                {'name': 'Crypto', 'active': True, 'target': 50},
                {'name': 'Stocks', 'active': True, 'target': 50}
            ],
            'assets': [
                {'name': 'BTC', 'active': True},
                {'name': 'ETH', 'active': True},
                {'name': 'AAPL', 'active': True}
            ]
        }
    
    def test_get_dca_data_basic_calculations(self, dashboard_service, mock_sheets_client, 
                                            sample_buy_records, sample_settings):
        """Test basic DCA calculations with sample data."""
        # Setup mocks
        mock_sheets_client.get_all_records.return_value = sample_buy_records
        dashboard_service.settings_service.get_settings = Mock(return_value=sample_settings)
        
        # Execute
        result = dashboard_service.get_dca_dashboard_data()
        
        # Verify structure
        assert 'metrics' in result
        assert 'breakdown' in result
        assert 'assets' in result
        assert 'cost_vs_market_data' in result
        assert 'monthly_buy_data' in result
        
        # Verify metrics
        metrics = result['metrics']
        assert metrics['total_invested'] == 11500  # 4000 + 4500 + 3000
        assert metrics['total_units'] == 1.2  # 0.1 + 0.1 + 1.0
        assert metrics['avg_cost'] == pytest.approx(9583.33, rel=0.01)  # 11500 / 1.2
        
        # Verify breakdown exists
        assert len(result['breakdown']) == 2  # BTC and ETH
        
        # Verify assets list
        assert len(result['assets']) == 3
        assert 'BTC' in result['assets']
    
    def test_get_dca_data_with_asset_filter(self, dashboard_service, mock_sheets_client,
                                           sample_buy_records, sample_settings):
        """Test DCA calculations with asset filter."""
        # Setup mocks
        mock_sheets_client.get_all_records.return_value = sample_buy_records
        dashboard_service.settings_service.get_settings = Mock(return_value=sample_settings)
        
        # Execute with BTC filter
        result = dashboard_service.get_dca_dashboard_data(selected_asset='BTC')
        
        # Verify only BTC data
        metrics = result['metrics']
        assert metrics['total_invested'] == 8500  # 4000 + 4500
        assert metrics['total_units'] == 0.2  # 0.1 + 0.1
        assert metrics['avg_cost'] == 42500  # 8500 / 0.2
        assert metrics['last_price'] == 45000
        
        # Verify breakdown has only BTC
        assert len(result['breakdown']) == 1
        assert result['breakdown'][0]['name'] == 'BTC'
    
    def test_get_dca_data_empty_records(self, dashboard_service, mock_sheets_client, sample_settings):
        """Test DCA calculations with no buy records."""
        # Setup mocks with empty data
        mock_sheets_client.get_all_records.return_value = []
        dashboard_service.settings_service.get_settings = Mock(return_value=sample_settings)
        
        # Execute
        result = dashboard_service.get_dca_dashboard_data()
        
        # Verify default values
        metrics = result['metrics']
        assert metrics['total_invested'] == 0
        assert metrics['total_units'] == 0
        assert metrics['avg_cost'] == 0
        assert metrics['last_price'] == 0
        assert metrics['unrealized_pl'] == 0
        assert metrics['unrealized_pl_pct'] == 0
        
        assert len(result['breakdown']) == 0
    
    def test_get_dca_data_profit_loss_calculations(self, dashboard_service, mock_sheets_client,
                                                   sample_buy_records, sample_settings):
        """Test profit/loss calculations for DCA."""
        # Setup mocks
        mock_sheets_client.get_all_records.return_value = sample_buy_records
        dashboard_service.settings_service.get_settings = Mock(return_value=sample_settings)
        
        # Execute
        result = dashboard_service.get_dca_dashboard_data()
        
        # Calculate expected values
        # Total invested: 11500
        # Total units: 0.1 + 0.1 + 1.0 = 1.2
        # Last price = 3000 (ETH)
        # Current value = 1.2 * 3000 = 3600
        # Unrealized P/L = 3600 - 11500 = -7900
        # Unrealized P/L % = (-7900 / 11500) * 100 = -68.7%
        
        metrics = result['metrics']
        assert metrics['unrealized_pl'] == pytest.approx(-7900, rel=0.01)
        assert metrics['unrealized_pl_pct'] == pytest.approx(-68.70, rel=0.1)
    
    def test_get_dca_data_breakdown_by_asset(self, dashboard_service, mock_sheets_client,
                                            sample_buy_records, sample_settings):
        """Test breakdown calculations by asset."""
        # Setup mocks
        mock_sheets_client.get_all_records.return_value = sample_buy_records
        dashboard_service.settings_service.get_settings = Mock(return_value=sample_settings)
        
        # Execute
        result = dashboard_service.get_dca_dashboard_data()
        
        # Find BTC in breakdown
        btc_breakdown = next((b for b in result['breakdown'] if b['name'] == 'BTC'), None)
        assert btc_breakdown is not None
        
        # Verify BTC breakdown
        assert btc_breakdown['invested'] == 8500  # 4000 + 4500
        assert btc_breakdown['units'] == 0.2  # 0.1 + 0.1
        assert btc_breakdown['avg_price'] == 42500  # 8500 / 0.2
        assert btc_breakdown['last_price'] == 45000
        
        # Find ETH in breakdown
        eth_breakdown = next((b for b in result['breakdown'] if b['name'] == 'ETH'), None)
        assert eth_breakdown is not None
        assert eth_breakdown['invested'] == 3000
        assert eth_breakdown['units'] == 1.0
    
    def test_get_dca_data_cost_vs_market_chart(self, dashboard_service, mock_sheets_client,
                                               sample_buy_records, sample_settings):
        """Test cost vs market chart data generation."""
        # Setup mocks
        mock_sheets_client.get_all_records.return_value = sample_buy_records
        dashboard_service.settings_service.get_settings = Mock(return_value=sample_settings)
        
        # Execute
        result = dashboard_service.get_dca_dashboard_data()
        
        # Verify chart data structure
        chart_data = result['cost_vs_market_data']
        assert 'labels' in chart_data
        assert 'cost' in chart_data
        assert 'value' in chart_data
        
        # Verify data points (3 Buy records)
        assert len(chart_data['labels']) == 3
        assert len(chart_data['cost']) == 3
        assert len(chart_data['value']) == 3
        
        # Verify cumulative cost
        assert chart_data['cost'][0] == 4000
        assert chart_data['cost'][1] == 8500  # 4000 + 4500
        assert chart_data['cost'][2] == 11500  # 8500 + 3000
    
    def test_get_dca_data_monthly_buy_chart(self, dashboard_service, mock_sheets_client,
                                           sample_buy_records, sample_settings):
        """Test monthly buy chart data generation."""
        # Setup mocks
        mock_sheets_client.get_all_records.return_value = sample_buy_records
        dashboard_service.settings_service.get_settings = Mock(return_value=sample_settings)
        
        # Execute
        result = dashboard_service.get_dca_dashboard_data()
        
        # Verify monthly data structure
        monthly_data = result['monthly_buy_data']
        assert 'labels' in monthly_data
        assert 'amounts' in monthly_data
        
        # Should have 12 months
        assert len(monthly_data['labels']) == 12
        assert len(monthly_data['amounts']) == 12
    
    def test_get_dca_data_handles_invalid_records(self, dashboard_service, mock_sheets_client,
                                                  sample_settings):
        """Test handling of invalid/malformed records."""
        # Setup mocks with some invalid data
        invalid_records = [
            {'ID': '1', 'Date': '2024-01-01', 'Action': 'Buy', 'Asset': 'BTC', 'Category': 'Crypto', 
             'Quantity': 'invalid', 'Unit Price': 40000, 'Total Amount': -4000, 'Note': ''},
            {'ID': '2', 'Date': '2024-02-01', 'Action': 'Buy', 'Asset': 'ETH', 'Category': 'Crypto', 
             'Quantity': 1.0, 'Unit Price': None, 'Total Amount': -3000, 'Note': ''},
            {'ID': '3', 'Date': '2024-03-01', 'Action': 'Buy', 'Asset': 'SOL', 'Category': 'Crypto', 
             'Quantity': 10, 'Unit Price': 100, 'Total Amount': -1000, 'Note': ''},
        ]
        
        mock_sheets_client.get_all_records.return_value = invalid_records
        dashboard_service.settings_service.get_settings = Mock(return_value=sample_settings)
        
        # Execute - should not raise exception
        result = dashboard_service.get_dca_dashboard_data()
        
        # Should only process valid record (SOL)
        assert result['metrics']['total_invested'] > 0
        assert len(result['breakdown']) >= 1
    
    def test_get_dca_data_error_handling(self, dashboard_service, mock_sheets_client, sample_settings):
        """Test error handling when sheets client fails."""
        # Setup mock to raise exception
        mock_sheets_client.get_all_records.side_effect = Exception("Connection error")
        dashboard_service.settings_service.get_settings = Mock(return_value=sample_settings)
        
        # Execute - should return default values instead of crashing
        result = dashboard_service.get_dca_dashboard_data()
        
        # Verify default/empty result
        assert result['metrics']['total_invested'] == 0
        assert len(result['breakdown']) == 0
        assert len(result['assets']) == 0

"""
Dashboard service for handling dashboard analytics and calculations.
"""
from typing import Dict, Any, Optional, List
from collections import defaultdict
from datetime import datetime

from services.google_sheets_service import GoogleSheetsClient
from services.settings_service import SettingsService
from utils.date_utils import parse_date
from utils.amount_utils import parse_amount
from config.settings import WORKSHEET_CURRENT_ASSET, WORKSHEET_INVESTMENT, MONTHS_SHORT


class DashboardService:
    """Service class for dashboard operations."""
    
    def __init__(self, sheets_client: Optional[GoogleSheetsClient] = None):
        """
        Initialize the dashboard service.
        
        Args:
            sheets_client: Google Sheets client instance (optional, creates new if None)
        """
        self.client = sheets_client or GoogleSheetsClient()
        self.settings_service = SettingsService(self.client)
    
    def get_dashboard_data(self, start_date_str: Optional[str] = None, 
                          end_date_str: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """
        Get comprehensive dashboard data including summary, charts, and tables.
        
        Args:
            start_date_str: Start date filter (YYYY-MM-DD format)
            end_date_str: End date filter (YYYY-MM-DD format)
            
        Returns:
            Dictionary containing all dashboard data
        """
        try:
            filter_start = datetime.strptime(start_date_str, "%Y-%m-%d") if start_date_str else None
            filter_end = datetime.strptime(end_date_str, "%Y-%m-%d") if end_date_str else None
            
            # Get active settings
            active_settings = self.settings_service.get_settings(only_active=True)
            category_targets = {c['name']: c['target'] for c in active_settings['categories']}
            active_asset_names = [a['name'] for a in active_settings['assets']]
            active_cat_names = [c['name'] for c in active_settings['categories']]
            
            # Process Current Asset data
            asset_data = self._process_asset_data(filter_start, filter_end, active_cat_names, active_asset_names)
            
            # Process Investment data
            investment_data = self._process_investment_data(filter_start, filter_end)
            
            # Calculate allocation table
            allocation_table = self._calculate_allocation_table(
                category_targets,
                asset_data['category_current_value'],
                asset_data['current_asset_value']
            )
            
            # Calculate main summary table
            main_summary_table = self._calculate_main_summary_table(
                investment_data['monthly_invest_flow'],
                asset_data['monthly_asset_total'],
                asset_data['current_asset_value']
            )
            
            return {
                "total_investment": investment_data['total_invested'],
                "current_asset": asset_data['current_asset_value'],
                "profit_loss": asset_data['current_asset_value'] - investment_data['total_invested'],
                "pie_chart_labels": list(asset_data['category_current_value'].keys()),
                "pie_chart_data": list(asset_data['category_current_value'].values()),
                "line_chart_labels": MONTHS_SHORT,
                "line_chart_data": main_summary_table['investment'],
                "inv_pivot_table": asset_data['inv_pivot_rows'],
                "asset_pivot_table": asset_data['asset_pivot_rows'],
                "main_summary_table": main_summary_table,
                "allocation_table": allocation_table
            }
        except Exception as e:
            print(f"❌ Error in dashboard service: {e}")
            return None
    
    def _process_asset_data(self, filter_start: Optional[datetime], 
                           filter_end: Optional[datetime],
                           active_cat_names: List[str],
                           active_asset_names: List[str]) -> Dict[str, Any]:
        """Process asset data and calculate various metrics."""
        raw_assets = self.client.get_all_records(WORKSHEET_CURRENT_ASSET)
        
        latest_assets_snapshot = {}
        category_current_value = defaultdict(float)
        asset_name_pivot_data = defaultdict(lambda: defaultdict(float))
        category_pivot_data = defaultdict(lambda: defaultdict(float))
        monthly_asset_total = defaultdict(float)
        
        for item in raw_assets:
            clean_item = {str(k).strip(): v for k, v in item.items()}
            date_obj = parse_date(clean_item.get('Date') or clean_item.get('date'))
            
            # Apply date filter
            if date_obj and filter_start and filter_end:
                if not (filter_start <= date_obj <= filter_end):
                    continue
            
            amount = parse_amount(clean_item.get('Amount', 0))
            cat = str(clean_item.get('Category', 'Uncategorized')).strip()
            asset_name = str(clean_item.get('Description') or clean_item.get('Asset') or 'Unknown').strip()
            
            if date_obj:
                # Track latest snapshot
                if asset_name not in latest_assets_snapshot or date_obj > latest_assets_snapshot[asset_name]['date']:
                    latest_assets_snapshot[asset_name] = {'date': date_obj, 'amount': amount, 'category': cat}
                
                # Monthly aggregations
                month_idx = date_obj.strftime("%m")
                asset_name_pivot_data[asset_name][month_idx] += amount
                category_pivot_data[cat][month_idx] += amount
                monthly_asset_total[month_idx] += amount
        
        # Calculate current values
        current_asset_value = sum(item['amount'] for item in latest_assets_snapshot.values())
        for item in latest_assets_snapshot.values():
            category_current_value[item['category']] += item['amount']
        
        # Build pivot tables
        inv_pivot_rows = self._build_category_pivot(
            active_cat_names,
            category_pivot_data,
            latest_assets_snapshot
        )
        
        asset_pivot_rows = self._build_asset_pivot(
            active_asset_names,
            asset_name_pivot_data,
            latest_assets_snapshot
        )
        
        return {
            'current_asset_value': current_asset_value,
            'category_current_value': category_current_value,
            'monthly_asset_total': monthly_asset_total,
            'inv_pivot_rows': inv_pivot_rows,
            'asset_pivot_rows': asset_pivot_rows
        }
    
    def _process_investment_data(self, filter_start: Optional[datetime], 
                                filter_end: Optional[datetime]) -> Dict[str, Any]:
        """Process investment transaction data."""
        raw_txs = self.client.get_all_records(WORKSHEET_INVESTMENT)
        
        total_invested = 0
        monthly_invest_flow = defaultdict(float)
        
        for tx in raw_txs:
            clean_tx = {str(k).strip(): v for k, v in tx.items()}
            date_obj = parse_date(clean_tx.get('Date') or clean_tx.get('date'))
            
            # Apply date filter
            if date_obj and filter_start and filter_end:
                if not (filter_start <= date_obj <= filter_end):
                    continue
            
            amount = parse_amount(clean_tx.get('Total Amount', 0))
            action = str(clean_tx.get('Action', '')).strip().lower()
            
            # Calculate flow
            flow_amount = 0
            if action == 'deposit':
                flow_amount = abs(amount)
            elif action == 'withdraw':
                flow_amount = -abs(amount)
            
            total_invested += flow_amount
            
            if date_obj:
                month_idx = date_obj.strftime("%m")
                monthly_invest_flow[month_idx] += flow_amount
        
        return {
            'total_invested': total_invested,
            'monthly_invest_flow': monthly_invest_flow
        }
    
    def _build_category_pivot(self, active_cat_names: List[str],
                             category_pivot_data: Dict,
                             latest_assets_snapshot: Dict) -> List[Dict]:
        """Build category pivot table."""
        inv_pivot_rows = []
        
        for cat in active_cat_names:
            row_data = {'name': cat, 'months': [], 'total': 0, 'avg': 0}
            cat_total = 0
            cat_latest_val = 0
            
            # Calculate latest value for this category
            for item in latest_assets_snapshot.values():
                if item['category'] == cat:
                    cat_latest_val += item['amount']
            
            # Monthly data
            for i in range(1, 13):
                m_idx = f"{i:02d}"
                val = category_pivot_data[cat][m_idx]
                row_data['months'].append(val)
                cat_total += val
            
            row_data['total'] = cat_latest_val
            row_data['avg'] = cat_total / 12
            inv_pivot_rows.append(row_data)
        
        return inv_pivot_rows
    
    def _build_asset_pivot(self, active_asset_names: List[str],
                          asset_name_pivot_data: Dict,
                          latest_assets_snapshot: Dict) -> List[Dict]:
        """Build asset pivot table."""
        asset_pivot_rows = []
        
        for asset in active_asset_names:
            row_data = {'name': asset, 'months': [], 'total': 0, 'avg': 0}
            asset_total = 0
            latest_asset_val = latest_assets_snapshot.get(asset, {}).get('amount', 0)
            
            # Monthly data
            for i in range(1, 13):
                m_idx = f"{i:02d}"
                val = asset_name_pivot_data[asset][m_idx]
                row_data['months'].append(val)
                asset_total += val
            
            row_data['total'] = latest_asset_val
            row_data['avg'] = asset_total / 12
            asset_pivot_rows.append(row_data)
        
        return asset_pivot_rows
    
    def _calculate_allocation_table(self, category_targets: Dict[str, float],
                                   category_current_value: Dict[str, float],
                                   current_asset_value: float) -> List[Dict]:
        """Calculate portfolio allocation vs target."""
        allocation_table = []
        
        for cat_name, target_pct in category_targets.items():
            actual_val = category_current_value.get(cat_name, 0)
            actual_pct = (actual_val / current_asset_value * 100) if current_asset_value > 0 else 0
            diff_pct = actual_pct - target_pct
            target_val_thb = (target_pct / 100) * current_asset_value
            action_amount = target_val_thb - actual_val
            
            allocation_table.append({
                'category': cat_name,
                'actual_val': actual_val,
                'target_pct': target_pct,
                'actual_pct': actual_pct,
                'diff_pct': diff_pct,
                'action_amount': action_amount,
                'target_val': target_val_thb
            })
        
        return allocation_table
    
    def _calculate_main_summary_table(self, monthly_invest_flow: Dict,
                                     monthly_asset_total: Dict,
                                     current_asset_value: float) -> Dict:
        """Calculate main summary table with running totals."""
        summary_table_data = {
            'investment': [],
            'asset': [],
            'diff': [],
            'diff_percent': [],
            'total_inv': 0,
            'total_asset': 0,
            'total_diff': 0,
            'total_diff_pct': 0
        }
        
        running_inv = 0
        for i in range(1, 13):
            m_idx = f"{i:02d}"
            running_inv += monthly_invest_flow[m_idx]
            curr_asset = monthly_asset_total[m_idx]
            
            if curr_asset == 0 and monthly_invest_flow[m_idx] == 0:
                display_inv = 0
                display_diff = 0
                display_diff_pct = 0
            else:
                display_inv = running_inv
                display_diff = curr_asset - running_inv
                display_diff_pct = (display_diff / running_inv) * 100 if running_inv > 0 else 0.0
            
            summary_table_data['investment'].append(display_inv)
            summary_table_data['asset'].append(curr_asset)
            summary_table_data['diff'].append(display_diff)
            summary_table_data['diff_percent'].append(display_diff_pct)
        
        summary_table_data['total_inv'] = running_inv
        summary_table_data['total_asset'] = current_asset_value
        summary_table_data['total_diff'] = current_asset_value - running_inv
        summary_table_data['total_diff_pct'] = (summary_table_data['total_diff'] / running_inv) * 100 if running_inv > 0 else 0.0
        
        return summary_table_data

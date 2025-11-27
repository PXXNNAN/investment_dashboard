"""
Dashboard service for handling dashboard analytics and calculations.
"""
from typing import Dict, Any, Optional, List
from collections import defaultdict
from datetime import datetime, timedelta

from services.google_sheets_service import GoogleSheetsClient
from services.settings_service import SettingsService
from services.investment_service import InvestmentService
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
        self.investment_service = InvestmentService(self.client)
    
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
            
            # Build investment pivot table for Investment Flow
            inv_pivot_rows = self._build_investment_category_pivot(
                active_cat_names,
                investment_data['category_investment_pivot']
            )
            
            return {
                "total_investment": investment_data['total_invested'],
                "current_asset": asset_data['current_asset_value'],
                "profit_loss": asset_data['current_asset_value'] - investment_data['total_invested'],
                "pie_chart_labels": list(asset_data['category_current_value'].keys()),
                "pie_chart_data": list(asset_data['category_current_value'].values()),
                "line_chart_labels": MONTHS_SHORT,
                "line_chart_data": main_summary_table['investment'],
                "inv_pivot_table": inv_pivot_rows,
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
        category_investment_pivot = defaultdict(lambda: defaultdict(float))
        
        for tx in raw_txs:
            clean_tx = {str(k).strip(): v for k, v in tx.items()}
            date_obj = parse_date(clean_tx.get('Date') or clean_tx.get('date'))
            
            # Apply date filter
            if date_obj and filter_start and filter_end:
                if not (filter_start <= date_obj <= filter_end):
                    continue
            
            amount = parse_amount(clean_tx.get('Total Amount', 0))
            action = str(clean_tx.get('Action', '')).strip().lower()
            category = str(clean_tx.get('Category', 'Uncategorized')).strip()
            
            
            # Calculate flow for total_invested (only Deposit/Withdraw affect this)
            flow_amount = 0
            if action == 'deposit':
                flow_amount = abs(amount)
            elif action == 'withdraw':
                flow_amount = -abs(amount)
            # Note: Buy/Sell don't change total_invested, only convert cash to assets
            
            total_invested += flow_amount
            
            
            if date_obj:
                month_idx = date_obj.strftime("%m")
                monthly_invest_flow[month_idx] += flow_amount
                
                # Track ONLY Buy/Sell for Investment Flow (category pivot)
                # Buy: amount is negative (-300), we want to show positive investment (+300)
                # Sell: amount is positive (+200), we want to show negative divestment (-200)
                if action == 'buy':
                    category_investment_pivot[category][month_idx] -= amount  # -(-300) = +300
                elif action == 'sell':
                    category_investment_pivot[category][month_idx] -= amount  # -(+200) = -200
        
        return {
            'total_invested': total_invested,
            'monthly_invest_flow': monthly_invest_flow,
            'category_investment_pivot': category_investment_pivot
        }
    
    def _build_investment_category_pivot(self, active_cat_names: List[str],
                                         category_investment_pivot: Dict) -> List[Dict]:
        """
        Build investment pivot table showing Buy/Sell transactions by category.
        
        Note: This differs from asset value pivot. It tracks actual investment transactions:
        - Buy: Shows positive investment flow (money going into assets)
        - Sell: Shows negative investment flow (money coming out of assets)
        - Does NOT include Deposit/Withdraw (those affect total_invested but not this pivot)
        
        Args:
            active_cat_names: List of active category names
            category_investment_pivot: Monthly investment data by category
            
        Returns:
            List of pivot row dictionaries with monthly data
        """
        investment_pivot_rows = []
        
        for cat in active_cat_names:
            row_data = {'name': cat, 'months': [], 'total': 0, 'avg': 0}
            cat_total = 0
            
            # Monthly data
            for i in range(1, 13):
                m_idx = f"{i:02d}"
                val = category_investment_pivot[cat][m_idx]
                row_data['months'].append(val)
                cat_total += val
            
            row_data['total'] = cat_total
            row_data['avg'] = cat_total / 12 if cat_total > 0 else 0
            investment_pivot_rows.append(row_data)
        
        return investment_pivot_rows
    
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
    
    def _apply_average_cost_transaction(self, total_invested: float, total_units: float, 
                                        action: str, qty: float, amount: float) -> tuple[float, float]:
        """
        Apply a buy/sell transaction using Average Cost Method.
        
        Args:
            total_invested: Current total invested amount
            total_units: Current total units held
            action: Transaction action ('buy' or 'sell')
            qty: Transaction quantity
            amount: Transaction amount (for buy only)
            
        Returns:
            Tuple of (new_total_invested, new_total_units)
        """
        if action == 'buy':
            return (total_invested + amount, total_units + qty)
        elif action == 'sell':
            avg_cost = total_invested / total_units if total_units > 0 else 0
            return (total_invested - (qty * avg_cost), total_units - qty)
        return (total_invested, total_units)
    
    def _fetch_buy_sell_records(self, selected_asset: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Fetch and parse Buy/Sell records from Google Sheets.
        
        Args:
            selected_asset: Filter by specific asset name (optional)
            
        Returns:
            List of buy/sell records with parsed data
        """
        raw_data = self.client.get_all_records(WORKSHEET_INVESTMENT)
        
        records = []
        for r in raw_data:
            # Clean keys (strip spaces)
            clean_r = {str(k).strip(): v for k, v in r.items()}
            
            # Check for 'Buy' or 'Sell' action (case-insensitive)
            action = str(clean_r.get('Action') or clean_r.get('action') or '').strip().lower()
            
            if action in ['buy', 'sell']:
                try:
                    records.append({
                        'date': clean_r.get('Date') or clean_r.get('date') or '',
                        'action': action,
                        'name': clean_r.get('Asset') or clean_r.get('name') or '',
                        'qty': float(clean_r.get('Quantity') or clean_r.get('qty') or 0),
                        'price': float(clean_r.get('Unit Price') or clean_r.get('price') or 0),
                        'amount': abs(float(clean_r.get('Total Amount') or clean_r.get('amount') or 0))
                    })
                except (ValueError, TypeError):
                    continue
        
        # Filter by selected asset if provided
        if selected_asset:
            records = [r for r in records if r['name'] == selected_asset]
        
        return records
    
    def _calculate_dca_metrics(self, records: List[Dict[str, Any]]) -> Dict[str, float]:
        """
        Calculate DCA metrics from buy/sell records using Average Cost Method.
        
        Buy: Increases units and invested amount
        Sell: Decreases units at average cost (not at sell price)
        
        Args:
            records: List of buy/sell transaction records
            
        Returns:
            Dictionary containing DCA metrics
        """
        total_invested = 0
        total_units = 0
        last_price = 0
        
        # Sort by date to process chronologically
        sorted_records = sorted(records, key=lambda x: x['date'])
        
        for r in sorted_records:
            total_invested, total_units = self._apply_average_cost_transaction(
                total_invested, total_units, r['action'], r['qty'], r['amount']
            )
            
            last_price = r['price']
        
        avg_cost = total_invested / total_units if total_units > 0 else 0
        current_value = total_units * last_price
        unrealized_pl = current_value - total_invested
        unrealized_pl_pct = (unrealized_pl / total_invested * 100) if total_invested > 0 else 0
        
        return {
            'total_invested': total_invested,
            'total_units': total_units,
            'avg_cost': avg_cost,
            'last_price': last_price,
            'unrealized_pl': unrealized_pl,
            'unrealized_pl_pct': unrealized_pl_pct
        }
    
    def _calculate_dca_breakdown(self, records: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Calculate breakdown of investments by asset using Average Cost Method.
        
        Args:
            records: List of buy/sell transaction records
            
        Returns:
            List of asset breakdown dictionaries
        """
        # Group by asset and apply Average Cost Method per asset
        asset_dict = defaultdict(lambda: {'invested': 0, 'units': 0, 'last_price': 0, 'transactions': []})
        
        for r in records:
            asset_dict[r['name']]['transactions'].append(r)
        
        breakdown = []
        for name, data in asset_dict.items():
            total_invested = 0
            total_units = 0
            last_price = 0
            
            # Sort transactions by date
            sorted_txs = sorted(data['transactions'], key=lambda x: x['date'])
            
            for tx in sorted_txs:
                total_invested, total_units = self._apply_average_cost_transaction(
                    total_invested, total_units, tx['action'], tx['qty'], tx['amount']
                )
                last_price = tx['price']
            
            avg_price = total_invested / total_units if total_units > 0 else 0
            current_value_asset = total_units * last_price
            pl = current_value_asset - total_invested
            pl_pct = (pl / total_invested * 100) if total_invested > 0 else 0
            
            breakdown.append({
                'name': name,
                'invested': total_invested,
                'units': total_units,
                'avg_price': avg_price,
                'last_price': last_price,
                'current_value': current_value_asset,
                'pl': pl,
                'pl_pct': pl_pct
            })
        
        breakdown.sort(key=lambda x: x['invested'], reverse=True)
        return breakdown
    
    def _generate_cost_vs_market_data(self, records: List[Dict[str, Any]]) -> Dict[str, List]:
        """
        Generate cost vs market value chart data with Average Cost Method.
        
        Args:
            records: List of buy/sell transaction records
            
        Returns:
            Dictionary containing chart labels and data series
        """
        sorted_records = sorted(records, key=lambda x: x['date'])
        cost_data, value_data, labels = [], [], []
        cumulative_cost, cumulative_units = 0, 0
        
        for r in sorted_records:
            cumulative_cost, cumulative_units = self._apply_average_cost_transaction(
                cumulative_cost, cumulative_units, r['action'], r['qty'], r['amount']
            )
            
            cost_data.append(round(cumulative_cost, 2))
            value_data.append(round(cumulative_units * r['price'], 2))
            labels.append(r['date'])
        
        return {
            'labels': labels,
            'cost': cost_data,
            'value': value_data
        }
    
    def _generate_monthly_buy_data(self, records: List[Dict[str, Any]]) -> Dict[str, List]:
        """
        Generate monthly net flow data (Buy - Sell) for the last 12 months.
        
        Args:
            records: List of buy/sell transaction records
            
        Returns:
            Dictionary containing month labels and net flow amounts
        """
        monthly_data = defaultdict(float)
        for r in records:
            try:
                # Net Flow: Buy is positive, Sell is negative
                if r.get('action') == 'buy':
                    monthly_data[r['date'][:7]] += r['amount']
                elif r.get('action') == 'sell':
                    monthly_data[r['date'][:7]] -= r['amount']
            except (IndexError, TypeError):
                continue
        
        # Generate Current Year (Jan - Dec)
        today = datetime.now()
        current_year = today.year
        months = [f"{current_year}-{m:02d}" for m in range(1, 13)]
        
        return {
            'labels': [m[5:] for m in months],
            'amounts': [monthly_data.get(m, 0) for m in months]
        }
    
    def get_dca_dashboard_data(self, selected_asset: Optional[str] = None) -> Dict[str, Any]:
        """
        Get DCA (Dollar-Cost Averaging) dashboard data.
        
        Args:
            selected_asset: Filter by specific asset name (optional)
            
        Returns:
            Dictionary containing DCA metrics, breakdown, and chart data
        """
        try:
            # Get active asset names
            settings = self.settings_service.get_settings(only_active=True)
            assets = [a['name'] for a in settings['assets']]
            
            # Fetch buy/sell records
            records = self._fetch_buy_sell_records(selected_asset)
            
            # Calculate metrics using Average Cost Method
            metrics = self._calculate_dca_metrics(records)
            
            # Calculate breakdown by asset
            breakdown = self._calculate_dca_breakdown(records)
            
            # Generate chart data
            cost_vs_market_data = self._generate_cost_vs_market_data(records)
            monthly_buy_data = self._generate_monthly_buy_data(records)
            
            return {
                'metrics': metrics,
                'breakdown': breakdown,
                'assets': assets,
                'cost_vs_market_data': cost_vs_market_data,
                'monthly_buy_data': monthly_buy_data
            }
        except Exception as e:
            print(f"❌ Error getting DCA dashboard data: {e}")
            return {
                'metrics': {
                    'total_invested': 0,
                    'total_units': 0,
                    'avg_cost': 0,
                    'last_price': 0,
                    'unrealized_pl': 0,
                    'unrealized_pl_pct': 0
                },
                'breakdown': [],
                'assets': [],
                'cost_vs_market_data': {'labels': [], 'cost': [], 'value': []},
                'monthly_buy_data': {'labels': [], 'amounts': []}
            }

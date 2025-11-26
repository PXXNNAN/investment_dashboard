"""
Asset service for handling asset-related business logic.
"""
from typing import List, Dict, Any, Optional
from collections import defaultdict
from datetime import datetime
import uuid

from services.google_sheets_service import GoogleSheetsClient
from models.asset import Asset
from utils.date_utils import parse_date, format_date
from utils.amount_utils import parse_amount
from config.settings import WORKSHEET_CURRENT_ASSET, MONTHS_SHORT, CHART_COLORS


class AssetService:
    """Service class for asset operations."""
    
    def __init__(self, sheets_client: Optional[GoogleSheetsClient] = None):
        """
        Initialize the asset service.
        
        Args:
            sheets_client: Google Sheets client instance (optional, creates new if None)
        """
        self.client = sheets_client or GoogleSheetsClient()
    
    def get_records(self, filter_name: Optional[str] = None, 
                   filter_category: Optional[str] = None, 
                   filter_year: Optional[int] = None) -> List[Dict[str, Any]]:
        """
        Get asset records with optional filtering.
        
        Args:
            filter_name: Filter by asset name (partial match)
            filter_category: Filter by category
            filter_year: Filter by year
            
        Returns:
            List of asset records as dictionaries
        """
        try:
            raw_data = self.client.get_all_records(WORKSHEET_CURRENT_ASSET)
            records = []
            
            for item in raw_data:
                # Clean keys
                clean_item = {str(k).strip(): v for k, v in item.items()}
                
                # Extract fields
                record_id = str(clean_item.get('ID', '')).strip()
                name = str(clean_item.get('Description') or clean_item.get('Asset') or clean_item.get('Asset Name', '')).strip()
                category = str(clean_item.get('Category', '')).strip()
                date_val = str(clean_item.get('Date') or clean_item.get('date', '')).strip()
                amount = parse_amount(clean_item.get('Amount', 0))
                
                dt_obj = parse_date(date_val)
                
                # Apply filters
                if filter_name and filter_name.lower() not in name.lower():
                    continue
                if filter_category and filter_category != "" and filter_category != category:
                    continue
                if filter_year and dt_obj:
                    if dt_obj.year != int(filter_year):
                        continue
                if filter_year and not dt_obj:
                    continue
                
                # Format date for display
                display_date = format_date(dt_obj) if dt_obj else date_val
                
                records.append({
                    'id': record_id,
                    'date': display_date,
                    'name': name,
                    'category': category,
                    'amount': amount,
                    'dt_obj': dt_obj
                })
            
            # Sort by date (newest first)
            records.sort(key=lambda x: x['dt_obj'] if x['dt_obj'] else datetime.min, reverse=True)
            
            # Remove dt_obj from output
            for r in records:
                if 'dt_obj' in r:
                    del r['dt_obj']
            
            return records
        except Exception as e:
            print(f"❌ Error getting asset records: {e}")
            return []
    
    def add_record(self, data: Dict[str, Any]) -> bool:
        """
        Add a new asset record.
        
        Args:
            data: Dictionary containing asset data
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Create asset model for validation
            asset = Asset(
                id=str(uuid.uuid4()),
                date=parse_date(data.get('date')),
                name=str(data.get('name', '')).strip(),
                category=str(data.get('category', '')).strip(),
                amount=parse_amount(data.get('amount', 0))
            )
            
            # Convert to sheet row and append
            row = asset.to_sheet_row()
            return self.client.append_row(WORKSHEET_CURRENT_ASSET, row)
        except Exception as e:
            print(f"❌ Error adding asset record: {e}")
            return False
    
    def add_records_bulk(self, records: List[Dict[str, Any]]) -> bool:
        """
        Add multiple asset records at once.
        
        Args:
            records: List of asset data dictionaries
            
        Returns:
            True if successful, False otherwise
        """
        try:
            rows_to_add = []
            for rec in records:
                asset = Asset(
                    id=str(uuid.uuid4()),
                    date=parse_date(rec.get('date')),
                    name=str(rec.get('name', '')).strip(),
                    category=str(rec.get('category', '')).strip(),
                    amount=parse_amount(rec.get('amount', 0))
                )
                rows_to_add.append(asset.to_sheet_row())
            
            return self.client.append_rows(WORKSHEET_CURRENT_ASSET, rows_to_add)
        except Exception as e:
            print(f"❌ Error bulk adding asset records: {e}")
            return False
    
    def delete_record(self, record_id: str) -> bool:
        """
        Delete an asset record by ID.
        
        Args:
            record_id: ID of the record to delete
            
        Returns:
            True if successful, False otherwise
        """
        try:
            cell = self.client.find_cell(WORKSHEET_CURRENT_ASSET, record_id, in_column=1)
            if cell:
                return self.client.delete_row(WORKSHEET_CURRENT_ASSET, cell.row)
            return False
        except Exception as e:
            print(f"❌ Error deleting asset record: {e}")
            return False
    
    def update_record(self, record_id: str, new_data: Dict[str, Any]) -> bool:
        """
        Update an existing asset record.
        
        Args:
            record_id: ID of the record to update
            new_data: Dictionary containing updated data
            
        Returns:
            True if successful, False otherwise
        """
        try:
            cell = self.client.find_cell(WORKSHEET_CURRENT_ASSET, record_id, in_column=1)
            if cell:
                row_num = cell.row
                updates = [
                    {'range': f'B{row_num}', 'values': [[new_data['date']]]},
                    {'range': f'C{row_num}', 'values': [[new_data['amount']]]},
                    {'range': f'D{row_num}', 'values': [[new_data['name']]]},
                    {'range': f'E{row_num}', 'values': [[new_data['category']]]}
                ]
                return self.client.batch_update(WORKSHEET_CURRENT_ASSET, updates)
            return False
        except Exception as e:
            print(f"❌ Error updating asset record: {e}")
            return False
    
    def get_latest_portfolio_value(self) -> float:
        """
        Calculate the latest total portfolio value.
        
        Returns:
            Total portfolio value
        """
        try:
            raw_data = self.client.get_all_records(WORKSHEET_CURRENT_ASSET)
            latest_assets = {}
            
            for item in raw_data:
                clean_item = {str(k).strip(): v for k, v in item.items()}
                name = str(clean_item.get('Description') or clean_item.get('Asset') or clean_item.get('Asset Name', '')).strip()
                amount = parse_amount(clean_item.get('Amount', 0))
                date_val = parse_date(clean_item.get('Date') or clean_item.get('date'))
                
                if not name or not date_val:
                    continue
                
                if name not in latest_assets or date_val > latest_assets[name]['date']:
                    latest_assets[name] = {'date': date_val, 'amount': amount}
            
            total_value = sum(item['amount'] for item in latest_assets.values())
            return total_value
        except Exception as e:
            print(f"❌ Error getting latest portfolio value: {e}")
            return 0.0
    
    def get_chart_data(self, records: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Generate chart data from asset records.
        
        Args:
            records: List of asset records
            
        Returns:
            Chart data dictionary for Chart.js
        """
        try:
            asset_data = defaultdict(lambda: defaultdict(float))
            all_assets = set()
            
            for rec in records:
                try:
                    dt = datetime.strptime(rec['date'], "%d/%m/%Y")
                except:
                    continue
                
                month_idx = dt.strftime("%m")
                name = rec['name']
                
                # Keep only the latest value for each month
                if asset_data[name][month_idx] == 0:
                    asset_data[name][month_idx] = rec['amount']
                    all_assets.add(name)
            
            datasets = []
            month_keys = [f"{i:02d}" for i in range(1, 13)]
            
            for i, asset_name in enumerate(sorted(list(all_assets))):
                data_points = []
                for m_key in month_keys:
                    val = asset_data[asset_name][m_key]
                    data_points.append(val if val != 0 else None)
                
                datasets.append({
                    'label': asset_name,
                    'data': data_points,
                    'borderColor': CHART_COLORS[i % len(CHART_COLORS)],
                    'backgroundColor': CHART_COLORS[i % len(CHART_COLORS)],
                    'fill': False,
                    'tension': 0.4
                })
            
            return {'labels': MONTHS_SHORT, 'datasets': datasets}
        except Exception as e:
            print(f"❌ Error generating chart data: {e}")
            return {'labels': [], 'datasets': []}

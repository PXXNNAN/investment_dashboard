"""
Investment service for handling investment transaction business logic.
"""
from typing import List, Dict, Any, Optional
from collections import defaultdict
from datetime import datetime
import uuid

from services.google_sheets_service import GoogleSheetsClient
from models.investment import Investment
from utils.date_utils import parse_date, format_date
from utils.amount_utils import parse_amount
from config.settings import WORKSHEET_INVESTMENT, MONTHS_SHORT


class InvestmentService:
    """Service class for investment operations."""
    
    def __init__(self, sheets_client: Optional[GoogleSheetsClient] = None):
        """
        Initialize the investment service.
        
        Args:
            sheets_client: Google Sheets client instance (optional, creates new if None)
        """
        self.client = sheets_client or GoogleSheetsClient()
    
    def get_records(self, filter_name: Optional[str] = None,
                   filter_category: Optional[str] = None,
                   filter_year: Optional[int] = None,
                   filter_action: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Get investment records with optional filtering.
        
        Args:
            filter_name: Filter by asset name (partial match)
            filter_category: Filter by category
            filter_year: Filter by year
            filter_action: Filter by action type (Deposit, Withdraw, Buy, Sell)
            
        Returns:
            List of investment records as dictionaries
        """
        try:
            raw_data = self.client.get_all_records(WORKSHEET_INVESTMENT)
            records = []
            
            for item in raw_data:
                # Clean keys
                clean_item = {str(k).strip(): v for k, v in item.items()}
                
                # Extract fields
                record_id = str(clean_item.get('ID', '')).strip()
                date_val = str(clean_item.get('Date') or clean_item.get('date', '')).strip()
                action = str(clean_item.get('Action', '')).strip()
                name = str(clean_item.get('Asset') or clean_item.get('Description', '')).strip()
                category = str(clean_item.get('Category', '')).strip()
                qty = clean_item.get('Quantity')
                price = clean_item.get('Unit Price')
                amount = parse_amount(clean_item.get('Total Amount', 0))
                note = str(clean_item.get('Note', '')).strip()
                
                dt_obj = parse_date(date_val)
                
                # Apply filters
                if filter_name and filter_name.lower() not in name.lower():
                    continue
                if filter_category and filter_category != "" and filter_category != category:
                    continue
                if filter_action and filter_action != "" and filter_action != action:
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
                    'action': action,
                    'name': name,
                    'category': category,
                    'qty': qty,
                    'price': price,
                    'amount': amount,
                    'note': note,
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
            print(f"❌ Error getting investment records: {e}")
            return []
    
    def add_record(self, data: Dict[str, Any]) -> bool:
        """
        Add a new investment record.
        
        Args:
            data: Dictionary containing investment data
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Create investment model for validation
            investment = Investment(
                id=str(uuid.uuid4()),
                date=parse_date(data.get('date')),
                action=str(data.get('action', '')).strip(),
                name=str(data.get('name', '')).strip(),
                category=str(data.get('category', '')).strip(),
                quantity=parse_amount(data.get('qty')) if data.get('qty') else None,
                price=parse_amount(data.get('price')) if data.get('price') else None,
                amount=parse_amount(data.get('amount', 0)),
                note=str(data.get('note', '')).strip()
            )
            
            # Convert to sheet row and append
            row = investment.to_sheet_row()
            return self.client.append_row(WORKSHEET_INVESTMENT, row)
        except Exception as e:
            print(f"❌ Error adding investment record: {e}")
            return False
    
    def add_records_bulk(self, records: List[Dict[str, Any]]) -> bool:
        """
        Add multiple investment records at once.
        
        Args:
            records: List of investment data dictionaries
            
        Returns:
            True if successful, False otherwise
        """
        try:
            rows_to_add = []
            for rec in records:
                investment = Investment(
                    id=str(uuid.uuid4()),
                    date=parse_date(rec.get('date')),
                    action=str(rec.get('action', '')).strip(),
                    name=str(rec.get('name', '')).strip(),
                    category=str(rec.get('category', '')).strip(),
                    quantity=parse_amount(rec.get('qty')) if rec.get('qty') else None,
                    price=parse_amount(rec.get('price')) if rec.get('price') else None,
                    amount=parse_amount(rec.get('amount', 0)),
                    note=str(rec.get('note', '')).strip()
                )
                rows_to_add.append(investment.to_sheet_row())
            
            return self.client.append_rows(WORKSHEET_INVESTMENT, rows_to_add)
        except Exception as e:
            print(f"❌ Error bulk adding investment records: {e}")
            return False
    
    def delete_record(self, record_id: str) -> bool:
        """
        Delete an investment record by ID.
        
        Args:
            record_id: ID of the record to delete
            
        Returns:
            True if successful, False otherwise
        """
        try:
            cell = self.client.find_cell(WORKSHEET_INVESTMENT, record_id, in_column=1)
            if cell:
                return self.client.delete_row(WORKSHEET_INVESTMENT, cell.row)
            return False
        except Exception as e:
            print(f"❌ Error deleting investment record: {e}")
            return False
    
    def update_record(self, record_id: str, data: Dict[str, Any]) -> bool:
        """
        Update an existing investment record.
        
        Args:
            record_id: ID of the record to update
            data: Dictionary containing updated data
            
        Returns:
            True if successful, False otherwise
        """
        try:
            cell = self.client.find_cell(WORKSHEET_INVESTMENT, record_id, in_column=1)
            if cell:
                row_num = cell.row
                updates = [
                    {'range': f'B{row_num}', 'values': [[data['date']]]},
                    {'range': f'C{row_num}', 'values': [[data['action']]]},
                    {'range': f'D{row_num}', 'values': [[data['name']]]},
                    {'range': f'E{row_num}', 'values': [[data['category']]]},
                    {'range': f'F{row_num}', 'values': [[data['qty']]]},
                    {'range': f'G{row_num}', 'values': [[data['price']]]},
                    {'range': f'H{row_num}', 'values': [[data['amount']]]},
                    {'range': f'I{row_num}', 'values': [[data['note']]]}
                ]
                return self.client.batch_update(WORKSHEET_INVESTMENT, updates)
            return False
        except Exception as e:
            print(f"❌ Error updating investment record: {e}")
            return False
    
    def get_chart_data(self, records: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Generate chart data from investment records.
        
        Args:
            records: List of investment records
            
        Returns:
            Chart data dictionary for Chart.js
        """
        try:
            monthly_deposit = defaultdict(float)
            monthly_withdraw = defaultdict(float)
            monthly_buy = defaultdict(float)
            
            for rec in records:
                try:
                    dt = datetime.strptime(rec['date'], "%d/%m/%Y")
                except:
                    continue
                
                month_idx = dt.strftime("%m")
                amount = rec['amount']
                action = rec['action'].lower()
                
                if action == 'deposit':
                    monthly_deposit[month_idx] += abs(amount)
                elif action == 'withdraw':
                    monthly_withdraw[month_idx] += abs(amount)
                elif action == 'buy':
                    monthly_buy[month_idx] += abs(amount)
            
            month_keys = [f"{i:02d}" for i in range(1, 13)]
            data_deposit = [monthly_deposit[m] for m in month_keys]
            data_withdraw = [-monthly_withdraw[m] for m in month_keys]
            data_buy = [monthly_buy[m] for m in month_keys]
            
            return {
                'labels': MONTHS_SHORT,
                'datasets': [
                    {
                        'type': 'bar',
                        'label': 'Deposit',
                        'data': data_deposit,
                        'backgroundColor': 'rgba(25, 135, 84, 0.7)',
                        'borderColor': '#198754',
                        'borderWidth': 1
                    },
                    {
                        'type': 'bar',
                        'label': 'Withdraw',
                        'data': data_withdraw,
                        'backgroundColor': 'rgba(220, 53, 69, 0.7)',
                        'borderColor': '#dc3545',
                        'borderWidth': 1
                    },
                    {
                        'type': 'line',
                        'label': 'Buy Volume',
                        'data': data_buy,
                        'borderColor': '#0d6efd',
                        'borderWidth': 2,
                        'fill': False,
                        'tension': 0.4
                    }
                ]
            }
        except Exception as e:
            print(f"❌ Error generating chart data: {e}")
            return {'labels': [], 'datasets': []}

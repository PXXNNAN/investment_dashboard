"""
Dividend service for handling dividend-related business logic.
"""
from typing import List, Dict, Any, Optional
from collections import defaultdict
from datetime import datetime
import uuid

from services.google_sheets_service import GoogleSheetsClient
from models.dividend import Dividend
from utils.date_utils import parse_date, format_date
from utils.amount_utils import parse_amount
from config.settings import WORKSHEET_INVESTMENT, MONTHS_SHORT


# Dividend worksheet name
WORKSHEET_DIVIDENDS = "Dividends"


class DividendService:
    """Service class for dividend operations."""
    
    def __init__(self, sheets_client: Optional[GoogleSheetsClient] = None):
        """
        Initialize the dividend service.
        
        Args:
            sheets_client: Google Sheets client instance (optional, creates new if None)
        """
        self.client = sheets_client or GoogleSheetsClient()
    
    def get_records(self, filter_name: Optional[str] = None, filter_year: Optional[int] = None) -> List[Dict[str, Any]]:
        """
        Get dividend records with optional filtering.
        
        Args:
            filter_name: Filter by asset name (partial match)
            filter_year: Filter by year
            
        Returns:
            List of dividend records as dictionaries
        """
        try:
            raw_data = self.client.get_all_records(WORKSHEET_DIVIDENDS)
            records = []
            
            for item in raw_data:
                # Clean keys
                clean_item = {str(k).strip(): v for k, v in item.items()}
                
                # Extract fields
                record_id = str(clean_item.get('ID', '')).strip()
                date_val = str(clean_item.get('Date') or clean_item.get('date', '')).strip()
                name = str(clean_item.get('Asset Name') or clean_item.get('Asset', '')).strip()
                category = str(clean_item.get('Category', '')).strip()
                amount = parse_amount(clean_item.get('Dividend Amount') or clean_item.get('Amount', 0))
                reinvested = str(clean_item.get('Reinvested', 'No')).strip()
                note = str(clean_item.get('Note', '')).strip()
                
                dt_obj = parse_date(date_val)
                
                # Apply filters
                if filter_name and filter_name.lower() not in name.lower():
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
                    'reinvested': reinvested,
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
            print(f"❌ Error getting dividend records: {e}")
            return []
    
    def add_record(self, data: Dict[str, Any]) -> bool:
        """
        Add a new dividend record.
        
        Args:
            data: Dictionary containing dividend data
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Create dividend model for validation
            dividend = Dividend(
                id=str(uuid.uuid4()),
                date=parse_date(data.get('date')),
                name=str(data.get('name', '')).strip(),
                category=str(data.get('category', '')).strip(),
                amount=parse_amount(data.get('amount', 0)),
                reinvested=str(data.get('reinvested', 'No')).strip(),
                note=str(data.get('note', '')).strip()
            )
            
            # Convert to sheet row and append
            row = dividend.to_sheet_row()
            return self.client.append_row(WORKSHEET_DIVIDENDS, row)
        except Exception as e:
            print(f"❌ Error adding dividend record: {e}")
            return False
    
    def get_chart_data(self, records: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Generate monthly chart data from dividend records.
        
        Args:
            records: List of dividend records
            
        Returns:
            Chart data dictionary for Chart.js
        """
        try:
            monthly_div = defaultdict(float)
            
            for rec in records:
                try:
                    dt = datetime.strptime(rec['date'], "%d/%m/%Y")
                except:
                    continue
                
                month_idx = dt.strftime("%m")
                monthly_div[month_idx] += rec['amount']
            
            month_keys = [f"{i:02d}" for i in range(1, 13)]
            data = [monthly_div[m] for m in month_keys]
            
            return {
                'labels': MONTHS_SHORT,
                'datasets': [{
                    'label': 'Dividend Income',
                    'data': data,
                    'backgroundColor': 'rgba(255, 193, 7, 0.7)',
                    'borderColor': '#ffc107',
                    'borderWidth': 1
                }]
            }
        except Exception as e:
            print(f"❌ Error generating chart data: {e}")
            return {'labels': [], 'datasets': []}
    
    def get_analysis_data(self, mode: str = 'yearly', filter_name: Optional[str] = None) -> Dict[str, Any]:
        """
        Get dividend analysis data (yearly or monthly).
        
        Args:
            mode: 'yearly' or 'monthly'
            filter_name: Optional asset name filter
            
        Returns:
            Chart data dictionary for Chart.js
        """
        try:
            raw_data = self.client.get_all_records(WORKSHEET_DIVIDENDS)
            data_map = defaultdict(float)
            
            for item in raw_data:
                clean_item = {str(k).strip(): v for k, v in item.items()}
                amount = parse_amount(clean_item.get('Dividend Amount') or clean_item.get('Amount', 0))
                date_val = parse_date(clean_item.get('Date') or clean_item.get('date'))
                name = str(clean_item.get('Asset Name') or clean_item.get('Asset', '')).strip()
                
                # Filter by name
                if filter_name and filter_name.lower() not in name.lower():
                    continue
                
                if date_val:
                    if mode == 'monthly':
                        key = date_val.strftime("%Y-%m")
                    else:
                        key = date_val.strftime("%Y")
                    data_map[key] += amount
            
            # Sort keys and prepare labels/data
            sorted_keys = sorted(data_map.keys())
            labels = []
            data = []
            
            for k in sorted_keys:
                if mode == 'monthly':
                    dt = datetime.strptime(k, "%Y-%m")
                    labels.append(dt.strftime("%b %Y"))
                else:
                    labels.append(k)
                data.append(data_map[k])
            
            # Set colors based on mode
            if mode == 'monthly':
                bg_color = 'rgba(255, 193, 7, 0.6)'
                border_color = '#ffc107'
            else:
                bg_color = [
                    'rgba(255, 99, 132, 0.7)',
                    'rgba(54, 162, 235, 0.7)',
                    'rgba(255, 206, 86, 0.7)',
                    'rgba(75, 192, 192, 0.7)',
                    'rgba(153, 102, 255, 0.7)',
                    'rgba(255, 159, 64, 0.7)'
                ]
                border_color = '#fff'
            
            label_text = f'Dividend Income ({filter_name if filter_name else "Total"})'
            
            return {
                'labels': labels,
                'datasets': [{
                    'label': label_text,
                    'data': data,
                    'backgroundColor': bg_color,
                    'borderColor': border_color,
                    'borderWidth': 1
                }]
            }
        except Exception as e:
            print(f"❌ Error generating analysis data: {e}")
            return {'labels': [], 'datasets': []}
    
    def get_total_dividends(self, year: Optional[int] = None) -> float:
        """
        Calculate total dividends for a given year.
        
        Args:
            year: Year to calculate (None for all time)
            
        Returns:
            Total dividend amount
        """
        records = self.get_records(filter_year=year)
        return sum(r['amount'] for r in records)
    
    def get_monthly_average(self, year: int) -> float:
        """
        Calculate average monthly dividend for a year.
        
        Args:
            year: Year to calculate
            
        Returns:
            Average monthly dividend
        """
        total = self.get_total_dividends(year)
        return total / 12 if total > 0 else 0.0

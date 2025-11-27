"""
Settings service for handling application settings business logic.
"""
from typing import List, Dict, Any, Optional

from services.google_sheets_service import GoogleSheetsClient
from config.settings import WORKSHEET_SETTINGS


class SettingsService:
    """Service class for settings operations."""
    
    def __init__(self, sheets_client: Optional[GoogleSheetsClient] = None):
        """
        Initialize the settings service.
        
        Args:
            sheets_client: Google Sheets client instance (optional, creates new if None)
        """
        self.client = sheets_client or GoogleSheetsClient()
    
    def get_settings(self, only_active: bool = False) -> Dict[str, List[Dict[str, Any]]]:
        """
        Get all settings (categories and assets).
        
        Args:
            only_active: If True, return only active items
            
        Returns:
            Dictionary with 'categories' and 'assets' lists
        """
        try:
            all_values = self.client.get_all_values(WORKSHEET_SETTINGS)
            categories = []
            assets = []
            
            for row in all_values[1:]:  # Skip header row
                # Category (columns A, B, C)
                if len(row) >= 1 and row[0].strip():
                    name = row[0].strip()
                    is_active = str(row[1]).upper() == 'TRUE' if len(row) >= 2 else True
                    target_percent = 0.0
                    
                    if len(row) >= 3 and row[2].strip():
                        try:
                            target_percent = float(row[2].strip())
                        except:
                            target_percent = 0.0
                    
                    if not only_active or is_active:
                        categories.append({
                            'name': name,
                            'active': is_active,
                            'target': target_percent
                        })
                
                # Asset (columns D, E)
                if len(row) >= 4 and row[3].strip():
                    name = row[3].strip()
                    is_active = str(row[4]).upper() == 'TRUE' if len(row) >= 5 else True
                    
                    if not only_active or is_active:
                        assets.append({
                            'name': name,
                            'active': is_active
                        })
            
            return {'categories': categories, 'assets': assets}
        except Exception as e:
            print(f"❌ Error getting settings: {e}")
            return {'categories': [], 'assets': []}
    
    def update_setting_status(self, setting_type: str, name: str, action: str, value: Optional[str] = None) -> bool:
        """
        Update setting status (add, toggle, or update target).
        
        Args:
            setting_type: 'category' or 'asset'
            name: Name of the setting
            action: 'add', 'toggle', or 'update_target'
            value: Value for update_target action
            
        Returns:
            True if successful, False otherwise
        """
        try:
            all_values = self.client.get_all_values(WORKSHEET_SETTINGS)
            name_idx = 0 if setting_type == 'category' else 3
            active_idx = 1 if setting_type == 'category' else 4
            target_idx = 2
            search_name = str(name).strip().lower()
            
            if action == 'add':
                # Find first empty row
                row_to_write = len(all_values) + 1
                for i, row in enumerate(all_values):
                    if i == 0:  # Skip header
                        continue
                    if len(row) <= name_idx or row[name_idx] == "":
                        row_to_write = i + 1
                        break
                
                self.client.update_cell(WORKSHEET_SETTINGS, row_to_write, name_idx + 1, name)
                self.client.update_cell(WORKSHEET_SETTINGS, row_to_write, active_idx + 1, "TRUE")
                if setting_type == 'category':
                    self.client.update_cell(WORKSHEET_SETTINGS, row_to_write, target_idx + 1, 0)
            
            elif action == 'toggle':
                for i, row in enumerate(all_values):
                    curr_name = str(row[name_idx]).strip().lower() if len(row) > name_idx else ""
                    if curr_name == search_name:
                        current_status = str(row[active_idx]).upper() == 'TRUE' if len(row) > active_idx else True
                        new_status = "FALSE" if current_status else "TRUE"
                        self.client.update_cell(WORKSHEET_SETTINGS, i + 1, active_idx + 1, new_status)
                        break
            
            elif action == 'update_target' and setting_type == 'category':
                for i, row in enumerate(all_values):
                    curr_name = str(row[name_idx]).strip().lower() if len(row) > name_idx else ""
                    if curr_name == search_name:
                        self.client.update_cell(WORKSHEET_SETTINGS, i + 1, target_idx + 1, value)
                        break
            
            return True
        except Exception as e:
            print(f"❌ Error updating setting status: {e}")
            return False

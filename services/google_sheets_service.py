"""
Google Sheets service for handling all Google Sheets API interactions.
Provides a clean interface for CRUD operations on worksheets.
"""
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from typing import List, Dict, Any, Optional
from config.settings import (
    GOOGLE_SHEETS_SCOPES,
    CREDENTIALS_FILE,
    SHEET_NAME
)


class GoogleSheetsClient:
    """
    Wrapper class for Google Sheets API operations.
    Handles authentication and provides methods for common operations.
    """
    
    def __init__(self, credentials_file: str = CREDENTIALS_FILE, sheet_name: str = SHEET_NAME):
        """
        Initialize the Google Sheets client.
        
        Args:
            credentials_file: Path to service account JSON file
            sheet_name: Name of the Google Sheet to access
        """
        self.credentials_file = credentials_file
        self.sheet_name = sheet_name
        self._client = None
        self._sheet = None
    
    def _get_client(self) -> gspread.Client:
        """
        Get or create the gspread client.
        
        Returns:
            Authorized gspread client
        """
        if self._client is None:
            creds = ServiceAccountCredentials.from_json_keyfile_name(
                self.credentials_file,
                GOOGLE_SHEETS_SCOPES
            )
            self._client = gspread.authorize(creds)
        return self._client
    
    def _get_sheet(self) -> gspread.Spreadsheet:
        """
        Get or open the Google Sheet.
        
        Returns:
            Google Spreadsheet object
        """
        if self._sheet is None:
            client = self._get_client()
            self._sheet = client.open(self.sheet_name)
        return self._sheet
    
    def get_worksheet(self, worksheet_name: str) -> gspread.Worksheet:
        """
        Get a specific worksheet by name.
        
        Args:
            worksheet_name: Name of the worksheet
            
        Returns:
            Worksheet object
        """
        sheet = self._get_sheet()
        return sheet.worksheet(worksheet_name)
    
    def get_all_records(self, worksheet_name: str) -> List[Dict[str, Any]]:
        """
        Get all records from a worksheet as a list of dictionaries.
        
        Args:
            worksheet_name: Name of the worksheet
            
        Returns:
            List of dictionaries, where each dict represents a row
        """
        try:
            worksheet = self.get_worksheet(worksheet_name)
            return worksheet.get_all_records()
        except Exception as e:
            print(f"❌ Error getting records from {worksheet_name}: {e}")
            return []
    
    def get_all_values(self, worksheet_name: str) -> List[List[str]]:
        """
        Get all values from a worksheet as a list of lists.
        
        Args:
            worksheet_name: Name of the worksheet
            
        Returns:
            List of lists, where each inner list represents a row
        """
        try:
            worksheet = self.get_worksheet(worksheet_name)
            return worksheet.get_all_values()
        except Exception as e:
            print(f"❌ Error getting values from {worksheet_name}: {e}")
            return []
    
    def append_row(self, worksheet_name: str, row: List[Any]) -> bool:
        """
        Append a single row to a worksheet.
        
        Args:
            worksheet_name: Name of the worksheet
            row: List of values to append
            
        Returns:
            True if successful, False otherwise
        """
        try:
            worksheet = self.get_worksheet(worksheet_name)
            worksheet.append_row(row)
            return True
        except Exception as e:
            print(f"❌ Error appending row to {worksheet_name}: {e}")
            return False
    
    def append_rows(self, worksheet_name: str, rows: List[List[Any]]) -> bool:
        """
        Append multiple rows to a worksheet.
        
        Args:
            worksheet_name: Name of the worksheet
            rows: List of rows to append
            
        Returns:
            True if successful, False otherwise
        """
        try:
            worksheet = self.get_worksheet(worksheet_name)
            try:
                worksheet.append_rows(rows)
                return True
            except:
                # Fallback to appending one by one
                for row in rows:
                    worksheet.append_row(row)
                return True
        except Exception as e:
            print(f"❌ Error appending rows to {worksheet_name}: {e}")
            return False
    
    def update_cell(self, worksheet_name: str, row: int, col: int, value: Any) -> bool:
        """
        Update a single cell in a worksheet.
        
        Args:
            worksheet_name: Name of the worksheet
            row: Row number (1-indexed)
            col: Column number (1-indexed)
            value: Value to set
            
        Returns:
            True if successful, False otherwise
        """
        try:
            worksheet = self.get_worksheet(worksheet_name)
            worksheet.update_cell(row, col, value)
            return True
        except Exception as e:
            print(f"❌ Error updating cell in {worksheet_name}: {e}")
            return False
    
    def batch_update(self, worksheet_name: str, updates: List[Dict[str, Any]]) -> bool:
        """
        Perform batch update on a worksheet.
        
        Args:
            worksheet_name: Name of the worksheet
            updates: List of update dictionaries with 'range' and 'values' keys
            
        Returns:
            True if successful, False otherwise
        """
        try:
            worksheet = self.get_worksheet(worksheet_name)
            worksheet.batch_update(updates)
            return True
        except Exception as e:
            print(f"❌ Error batch updating {worksheet_name}: {e}")
            return False
    
    def find_cell(self, worksheet_name: str, query: str, in_column: Optional[int] = None) -> Optional[gspread.Cell]:
        """
        Find a cell by its value.
        
        Args:
            worksheet_name: Name of the worksheet
            query: Value to search for
            in_column: Optional column number to search in
            
        Returns:
            Cell object if found, None otherwise
        """
        try:
            worksheet = self.get_worksheet(worksheet_name)
            return worksheet.find(query, in_column=in_column)
        except Exception as e:
            print(f"❌ Error finding cell in {worksheet_name}: {e}")
            return None
    
    def delete_row(self, worksheet_name: str, row_number: int) -> bool:
        """
        Delete a row from a worksheet.
        
        Args:
            worksheet_name: Name of the worksheet
            row_number: Row number to delete (1-indexed)
            
        Returns:
            True if successful, False otherwise
        """
        try:
            worksheet = self.get_worksheet(worksheet_name)
            worksheet.delete_rows(row_number)
            return True
        except Exception as e:
            print(f"❌ Error deleting row from {worksheet_name}: {e}")
            return False

"""
Configuration settings for the Investment Dashboard application.
Centralizes all configuration values for easy management.
"""
import os
from typing import List

# --- Google Sheets Configuration ---
GOOGLE_SHEETS_SCOPES: List[str] = [
    "https://spreadsheets.google.com/feeds",
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive.file",
    "https://www.googleapis.com/auth/drive"
]

CREDENTIALS_FILE: str = os.path.join('credentials', 'service_account.json')
SHEET_NAME: str = "Investment_Db"

# Worksheet names
WORKSHEET_SETTINGS: str = "Settings"
WORKSHEET_CURRENT_ASSET: str = "Current Asset"
WORKSHEET_INVESTMENT: str = "Investment"

# --- Flask Configuration ---
FLASK_SECRET_KEY: str = 'supersecretkey'  # TODO: Move to environment variable in production
FLASK_DEBUG: bool = True
FLASK_HOST: str = '0.0.0.0'
FLASK_PORT: int = 5000

# --- Date Formats ---
DATE_FORMAT_INPUT: str = "%Y-%m-%d"
DATE_FORMAT_DISPLAY: str = "%d/%m/%Y"
DATE_FORMAT_ALTERNATIVE: str = "%d/%m/%Y"

# --- Chart Configuration ---
CHART_COLORS: List[str] = [
    '#4285F4', '#DB4437', '#F4B400', '#0F9D58', '#ab47bc',
    '#00acc1', '#ff7043', '#9e9e9e', '#5c6bc0', '#8d6e63'
]

MONTHS_SHORT: List[str] = [
    "Jan", "Feb", "Mar", "Apr", "May", "Jun",
    "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"
]

# --- Application Settings ---
YEAR_RANGE_PAST: int = 5  # How many years back to show in year filter
YEAR_RANGE_FUTURE: int = 1  # How many years forward to show in year filter

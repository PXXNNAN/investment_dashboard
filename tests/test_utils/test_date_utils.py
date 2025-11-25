"""
Unit tests for date utility functions.
"""
import pytest
from datetime import datetime
from utils.date_utils import parse_date, format_date, is_valid_date


class TestParseDate:
    """Tests for parse_date function."""
    
    def test_parse_date_yyyy_mm_dd_format(self):
        """Test parsing YYYY-MM-DD format."""
        result = parse_date("2025-01-15")
        assert result == datetime(2025, 1, 15)
    
    def test_parse_date_dd_mm_yyyy_format(self):
        """Test parsing DD/MM/YYYY format."""
        result = parse_date("15/01/2025")
        assert result == datetime(2025, 1, 15)
    
    def test_parse_date_with_datetime_object(self):
        """Test that datetime objects are returned as-is."""
        dt = datetime(2025, 1, 15)
        result = parse_date(dt)
        assert result == dt
    
    def test_parse_date_with_none(self):
        """Test that None returns None."""
        result = parse_date(None)
        assert result is None
    
    def test_parse_date_with_empty_string(self):
        """Test that empty string returns None."""
        result = parse_date("")
        assert result is None
    
    def test_parse_date_with_invalid_string(self):
        """Test that invalid date string returns None."""
        result = parse_date("invalid-date")
        assert result is None
    
    def test_parse_date_with_whitespace(self):
        """Test parsing date with whitespace."""
        result = parse_date("  2025-01-15  ")
        assert result == datetime(2025, 1, 15)


class TestFormatDate:
    """Tests for format_date function."""
    
    def test_format_date_default_format(self):
        """Test formatting with default DD/MM/YYYY format."""
        dt = datetime(2025, 1, 15)
        result = format_date(dt)
        assert result == "15/01/2025"
    
    def test_format_date_custom_format(self):
        """Test formatting with custom format."""
        dt = datetime(2025, 1, 15)
        result = format_date(dt, output_format="%Y-%m-%d")
        assert result == "2025-01-15"
    
    def test_format_date_with_none(self):
        """Test that None returns empty string."""
        result = format_date(None)
        assert result == ""
    
    def test_format_date_with_invalid_object(self):
        """Test that invalid object returns empty string."""
        result = format_date("not-a-datetime")
        assert result == ""


class TestIsValidDate:
    """Tests for is_valid_date function."""
    
    def test_is_valid_date_with_valid_date(self):
        """Test valid date string."""
        assert is_valid_date("2025-01-15") is True
        assert is_valid_date("15/01/2025") is True
    
    def test_is_valid_date_with_invalid_date(self):
        """Test invalid date string."""
        assert is_valid_date("invalid") is False
        assert is_valid_date("") is False
        assert is_valid_date(None) is False

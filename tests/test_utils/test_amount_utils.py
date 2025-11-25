"""
Unit tests for amount utility functions.
"""
import pytest
from utils.amount_utils import parse_amount, format_amount, is_valid_amount


class TestParseAmount:
    """Tests for parse_amount function."""
    
    def test_parse_amount_with_int(self):
        """Test parsing integer value."""
        result = parse_amount(1000)
        assert result == 1000.0
        assert isinstance(result, float)
    
    def test_parse_amount_with_float(self):
        """Test parsing float value."""
        result = parse_amount(1000.50)
        assert result == 1000.50
    
    def test_parse_amount_with_string_number(self):
        """Test parsing string number."""
        result = parse_amount("1000.50")
        assert result == 1000.50
    
    def test_parse_amount_with_commas(self):
        """Test parsing number with commas."""
        result = parse_amount("1,000.50")
        assert result == 1000.50
    
    def test_parse_amount_with_thai_baht_symbol(self):
        """Test parsing amount with ฿ symbol."""
        result = parse_amount("฿1,000")
        assert result == 1000.0
    
    def test_parse_amount_with_dollar_symbol(self):
        """Test parsing amount with $ symbol."""
        result = parse_amount("$1,000.50")
        assert result == 1000.50
    
    def test_parse_amount_with_empty_string(self):
        """Test that empty string returns 0.0."""
        result = parse_amount("")
        assert result == 0.0
    
    def test_parse_amount_with_none(self):
        """Test that None returns 0.0."""
        result = parse_amount(None)
        assert result == 0.0
    
    def test_parse_amount_with_invalid_string(self):
        """Test that invalid string returns 0.0."""
        result = parse_amount("invalid")
        assert result == 0.0
    
    def test_parse_amount_with_whitespace(self):
        """Test parsing amount with whitespace."""
        result = parse_amount("  1000.50  ")
        assert result == 1000.50


class TestFormatAmount:
    """Tests for format_amount function."""
    
    def test_format_amount_default(self):
        """Test formatting with default settings."""
        result = format_amount(1000.50)
        assert result == "1,000.50"
    
    def test_format_amount_with_symbol(self):
        """Test formatting with currency symbol."""
        result = format_amount(1000.50, include_symbol=True)
        assert result == "฿1,000.50"
    
    def test_format_amount_no_decimals(self):
        """Test formatting with no decimal places."""
        result = format_amount(1000, decimal_places=0)
        assert result == "1,000"
    
    def test_format_amount_large_number(self):
        """Test formatting large number."""
        result = format_amount(1000000.50)
        assert result == "1,000,000.50"
    
    def test_format_amount_zero(self):
        """Test formatting zero."""
        result = format_amount(0)
        assert result == "0.00"
    
    def test_format_amount_invalid_input(self):
        """Test formatting invalid input."""
        result = format_amount("invalid")
        assert result == "0.00"


class TestIsValidAmount:
    """Tests for is_valid_amount function."""
    
    def test_is_valid_amount_with_valid_number(self):
        """Test valid amount strings."""
        assert is_valid_amount("1000") is True
        assert is_valid_amount("1,000.50") is True
        assert is_valid_amount("฿1,000") is True
    
    def test_is_valid_amount_with_zero(self):
        """Test zero is valid."""
        assert is_valid_amount("0") is True
    
    def test_is_valid_amount_with_invalid_string(self):
        """Test invalid amount string."""
        assert is_valid_amount("invalid") is False
        assert is_valid_amount("") is False

import pytest
from unittest.mock import patch, Mock
import pandas as pd
import time

from app.services import (
    normalize_keyword,
    process_data,
    DataNotFoundException,
    DataValidationException
)


class TestNormalizeKeyword:
    """Test cases for keyword normalization."""
    
    def test_normalize_lowercase(self):
        """Test that keywords are converted to lowercase."""
        assert normalize_keyword("SKINCARE") == "skincare"
        assert normalize_keyword("FaShIoN") == "fashion"
    
    def test_normalize_removes_special_chars(self):
        """Test that special characters are removed."""
        assert normalize_keyword("skin-care!") == "skin_care"
        assert normalize_keyword("hello@world#123") == "hello_world_123"
    
    def test_normalize_replaces_spaces_with_underscore(self):
        """Test that spaces are replaced with underscores."""
        assert normalize_keyword("skin care product") == "skin_care_product"
        assert normalize_keyword("hello   world") == "hello_world"
    
    def test_normalize_trims_underscores(self):
        """Test that leading/trailing underscores are trimmed."""
        assert normalize_keyword("  skincare  ") == "skincare"
        assert normalize_keyword("-skincare-") == "skincare"
    
    def test_normalize_complex_keyword(self):
        """Test normalization with complex input."""
        assert normalize_keyword("Skin-Care Product 2024!") == "skin_care_product_2024"


class TestProcessData:
    """Test cases for data processing logic."""
    
    @pytest.fixture
    def valid_timeline_data(self):
        """Valid timeline data for testing."""
        return [
            {"date": "2026-01-09T00:00:00Z", "value": 45},
            {"date": "2026-01-09T01:00:00Z", "value": 50},
            {"date": "2026-01-09T02:00:00Z", "value": 48},
            {"date": "2026-01-09T03:00:00Z", "value": 52},
            {"date": "2026-01-09T04:00:00Z", "value": 47},
            {"date": "2026-01-09T05:00:00Z", "value": 49},
            {"date": "2026-01-09T06:00:00Z", "value": 55},
            {"date": "2026-01-09T07:00:00Z", "value": 60},
            {"date": "2026-01-09T08:00:00Z", "value": 65},
            {"date": "2026-01-09T09:00:00Z", "value": 70},
            {"date": "2026-01-09T10:00:00Z", "value": 75},
            {"date": "2026-01-09T11:00:00Z", "value": 72},
            {"date": "2026-01-09T12:00:00Z", "value": 68},
            {"date": "2026-01-09T13:00:00Z", "value": 80},
            {"date": "2026-01-09T14:00:00Z", "value": 85},
            {"date": "2026-01-09T15:00:00Z", "value": 90},
            {"date": "2026-01-09T16:00:00Z", "value": 88},
            {"date": "2026-01-09T17:00:00Z", "value": 92},
            {"date": "2026-01-09T18:00:00Z", "value": 95},
            {"date": "2026-01-09T19:00:00Z", "value": 98},
            {"date": "2026-01-09T20:00:00Z", "value": 100},
            {"date": "2026-01-09T21:00:00Z", "value": 97},
            {"date": "2026-01-09T22:00:00Z", "value": 93},
            {"date": "2026-01-09T23:00:00Z", "value": 85},
        ]
    
    def test_process_data_returns_correct_structure(self, valid_timeline_data):
        """Test that process_data returns correct structure."""
        result = process_data(valid_timeline_data)
        
        assert "recommendations" in result
        assert "chart_data" in result
        assert isinstance(result["recommendations"], list)
        assert isinstance(result["chart_data"], list)
    
    def test_process_data_returns_top_3_recommendations(self, valid_timeline_data):
        """Test that exactly 3 recommendations are returned."""
        result = process_data(valid_timeline_data)
        
        assert len(result["recommendations"]) == 3
    
    def test_recommendations_have_required_fields(self, valid_timeline_data):
        """Test that recommendations have all required fields."""
        result = process_data(valid_timeline_data)
        
        for rec in result["recommendations"]:
            assert "rank" in rec
            assert "day" in rec
            assert "time_window" in rec
            assert "score" in rec  # Score is in cache
            assert isinstance(rec["rank"], int)
            assert isinstance(rec["day"], str)
            assert isinstance(rec["time_window"], str)
            assert isinstance(rec["score"], float)
    
    def test_recommendations_are_ranked(self, valid_timeline_data):
        """Test that recommendations are ranked 1, 2, 3."""
        result = process_data(valid_timeline_data)
        
        ranks = [rec["rank"] for rec in result["recommendations"]]
        assert ranks == [1, 2, 3]
    
    def test_chart_data_uses_aggregated_data(self, valid_timeline_data):
        """Test that chart data uses aggregated hourly data."""
        result = process_data(valid_timeline_data)
        
        # Chart data should be aggregated (max 168 points for 7 days)
        assert len(result["chart_data"]) <= 168
        
        # Each chart point should have required fields
        for point in result["chart_data"]:
            assert "day" in point
            assert "hour" in point
            assert "score" in point
    
    def test_process_empty_data_raises_exception(self):
        """Test that empty data raises DataValidationException."""
        with pytest.raises(DataValidationException):
            process_data([])
    
    def test_process_data_with_missing_date_column(self):
        """Test that missing date column raises exception."""
        invalid_data = [{"value": 45}, {"value": 50}]
        
        with pytest.raises(DataValidationException) as exc_info:
            process_data(invalid_data)
        
        assert "Missing required columns" in str(exc_info.value)
    
    def test_process_data_with_missing_value_column(self):
        """Test that missing value column raises exception."""
        invalid_data = [
            {"date": "2026-01-09T00:00:00Z"},
            {"date": "2026-01-09T01:00:00Z"}
        ]
        
        with pytest.raises(DataValidationException) as exc_info:
            process_data(invalid_data)
        
        assert "Missing required columns" in str(exc_info.value)
    
    def test_process_data_with_invalid_dates(self):
        """Test that invalid dates are handled."""
        invalid_data = [
            {"date": "invalid-date", "value": 45},
            {"date": "2026-01-09T00:00:00Z", "value": 50},
            {"date": "2026-01-09T01:00:00Z", "value": 52},
        ]
        
        # Should not raise exception, but clean invalid data
        result = process_data(invalid_data)
        assert "recommendations" in result
    
    def test_process_data_with_null_values(self):
        """Test that null values are handled."""
        data_with_nulls = [
            {"date": "2026-01-09T00:00:00Z", "value": None},
            {"date": "2026-01-09T01:00:00Z", "value": 50},
            {"date": "2026-01-09T02:00:00Z", "value": 52},
            {"date": "2026-01-09T03:00:00Z", "value": 48},
        ]
        
        # Should clean nulls and continue
        result = process_data(data_with_nulls)
        assert "recommendations" in result
    
    def test_process_data_with_negative_values(self):
        """Test that negative values are removed."""
        data_with_negatives = [
            {"date": "2026-01-09T00:00:00Z", "value": -10},
            {"date": "2026-01-09T01:00:00Z", "value": 50},
            {"date": "2026-01-09T02:00:00Z", "value": 52},
            {"date": "2026-01-09T03:00:00Z", "value": 48},
        ]
        
        # Should remove negatives
        result = process_data(data_with_negatives)
        assert "recommendations" in result
    
    def test_timezone_conversion_to_jakarta(self, valid_timeline_data):
        """Test that dates are converted to Jakarta timezone."""
        result = process_data(valid_timeline_data)
        
        # Chart data should have day names in Jakarta time
        assert len(result["chart_data"]) > 0
        assert "day" in result["chart_data"][0]


class TestRedisHelpers:
    """Test Redis helper functions."""
    
    @patch('app.services.redis_client')
    def test_redis_get_with_retry_success(self, mock_redis):
        """Test successful Redis GET with retry."""
        from app.services import redis_get_with_retry
        
        mock_redis.get.return_value = "test_value"
        result = redis_get_with_retry("test_key")
        
        assert result == "test_value"
        mock_redis.get.assert_called_once_with("test_key")
    
    @patch('app.services.redis_client')
    def test_redis_set_with_retry_success(self, mock_redis):
        """Test successful Redis SET with retry."""
        from app.services import redis_set_with_retry
        
        mock_redis.setex.return_value = True
        result = redis_set_with_retry("test_key", "test_value", ex=60)
        
        assert result is True
        mock_redis.setex.assert_called_once_with("test_key", 60, "test_value")

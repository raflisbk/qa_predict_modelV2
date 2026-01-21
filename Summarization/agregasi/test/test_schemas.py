import pytest
from pydantic import ValidationError

from app.schemas import Recommendation, MetaData, PredictionResponse


class TestRecommendationSchema:
    """Test cases for Recommendation model."""
    
    def test_valid_recommendation(self):
        """Test creating valid Recommendation."""
        rec = Recommendation(
            rank=1,
            day="Monday",
            time_window="19:00 - 22:00"
        )
        
        assert rec.rank == 1
        assert rec.day == "Monday"
        assert rec.time_window == "19:00 - 22:00"
    
    def test_recommendation_missing_fields(self):
        """Test that missing required fields raise validation error."""
        with pytest.raises(ValidationError):
            Recommendation(rank=1, day="Monday")
    
    def test_recommendation_invalid_rank_type(self):
        """Test that invalid rank type raises validation error."""
        with pytest.raises(ValidationError):
            Recommendation(
                rank="invalid",
                day="Monday",
                time_window="19:00 - 22:00"
            )


class TestMetaDataSchema:
    """Test cases for MetaData model."""
    
    def test_valid_metadata_with_stats(self):
        """Test creating valid MetaData with stats."""
        meta = MetaData(
            keyword="skincare",
            source="live_apify",
            apify_stats={"duration_ms": 12500, "compute_units": 0.12}
        )
        
        assert meta.keyword == "skincare"
        assert meta.source == "live_apify"
        assert meta.apify_stats["duration_ms"] == 12500
    
    def test_valid_metadata_without_stats(self):
        """Test creating valid MetaData without stats."""
        meta = MetaData(
            keyword="fashion",
            source="cache_fresh"
        )
        
        assert meta.keyword == "fashion"
        assert meta.source == "cache_fresh"
        assert meta.apify_stats is None
    
    def test_metadata_invalid_source(self):
        """Test that invalid source raises validation error."""
        with pytest.raises(ValidationError):
            MetaData(
                keyword="test",
                source="invalid_source"
            )
    
    def test_metadata_valid_sources(self):
        """Test all valid source types."""
        sources = ["live_apify", "cache_fresh"]
        
        for source in sources:
            meta = MetaData(keyword="test", source=source)
            assert meta.source == source


class TestPredictionResponseSchema:
    """Test cases for PredictionResponse model."""
    
    def test_valid_prediction_response(self):
        """Test creating valid PredictionResponse."""
        response = PredictionResponse(
            status="success",
            meta=MetaData(
                keyword="skincare",
                source="live_apify",
                apify_stats={"duration_ms": 12500, "compute_units": 0.12}
            ),
            data={
                "recommendations": [
                    {
                        "rank": 1,
                        "day": "Monday",
                        "time_window": "19:00 - 22:00"
                    }
                ],
                "chart_data": [
                    {"day": "Monday", "hour": "00:00", "score": 45.0}
                ]
            }
        )
        
        assert response.status == "success"
        assert response.meta.keyword == "skincare"
        assert "recommendations" in response.data
        assert "chart_data" in response.data
    
    def test_prediction_response_missing_status(self):
        """Test that missing status raises validation error."""
        with pytest.raises(ValidationError):
            PredictionResponse(
                meta=MetaData(keyword="test", source="live_apify"),
                data={}
            )
    
    def test_prediction_response_missing_meta(self):
        """Test that missing meta raises validation error."""
        with pytest.raises(ValidationError):
            PredictionResponse(
                status="success",
                data={}
            )
    
    def test_prediction_response_missing_data(self):
        """Test that missing data raises validation error."""
        with pytest.raises(ValidationError):
            PredictionResponse(
                status="success",
                meta=MetaData(keyword="test", source="live_apify")
            )

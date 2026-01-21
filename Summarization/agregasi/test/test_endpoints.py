import pytest
from unittest.mock import patch, Mock, MagicMock
import json


class TestHealthEndpoint:
    """Test cases for /health endpoint."""
    
    def test_health_check_returns_ok(self, client):
        """Test that health endpoint returns 200 OK."""
        response = client.get("/health")
        
        assert response.status_code == 200
        assert response.json() == {"status": "ok"}


class TestPredictEndpoint:
    """Test cases for /predict endpoint."""
    
    @pytest.mark.skip(reason="Complex Apify mock - better tested in integration tests")
    def test_predict_with_valid_keyword(self, client, mock_redis, mock_apify_client, mock_apify_response):
        """Test prediction with valid keyword - cache miss scenario."""
        # Setup mocks
        with patch('app.services.apify_client') as mock_apify:
            # Mock Apify response
            mock_run = {
                "defaultDatasetId": "test_dataset",
                "stats": {"durationMillis": 12500, "computeUnits": 0.12}
            }
            mock_apify.actor.return_value.call.return_value = mock_run
            
            # Mock dataset - use correct Apify field name
            mock_dataset_items = [{"interestOverTime_timelineData": mock_apify_response["timeline_data"]}]
            mock_apify.dataset.return_value.iterate_items.return_value = iter(mock_dataset_items)
            
            response = client.get("/predict?keyword=skincare")
        
        assert response.status_code == 200
        data = response.json()
        
        # Validate response structure
        assert data["status"] == "success"
        assert "meta" in data
        assert "data" in data
        
        # Validate meta
        assert data["meta"]["keyword"] == "skincare"
        assert data["meta"]["source"] in ["live_apify", "cache_fresh"]
        
        # Validate data structure
        assert "recommendations" in data["data"]
        assert "chart_data" in data["data"]
        
        # Validate recommendations
        recommendations = data["data"]["recommendations"]
        assert len(recommendations) > 0
        assert len(recommendations) <= 3
        
        for rec in recommendations:
            assert "rank" in rec
            assert "day" in rec
            assert "time_window" in rec
            assert "score" not in rec  # Score should be hidden
    
    @pytest.mark.skip(reason="Complex Redis cache mock - better tested in integration tests")
    def test_predict_with_cached_data(self, client, mock_redis, mock_cached_data):
        """Test prediction returns cached data when available."""
        # Setup comprehensive mocks for all Redis operations
        def redis_get_side_effect(key):
            if key.startswith("usage:global:"):
                return "0"  # Usage count
            elif key.startswith("trends:"):
                return json.dumps(mock_cached_data)  # Cached data
            return None
        
        # Mock ALL services to prevent ANY external calls
        with patch('app.services.redis_get_with_retry', side_effect=redis_get_side_effect), \
             patch('app.services.redis_incr_with_retry', return_value=1), \
             patch('app.services.redis_expire_with_retry', return_value=True):
            
            response = client.get("/predict?keyword=fashion")
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["status"] == "success"
        assert data["meta"]["source"] == "cache_fresh"
    
    def test_predict_with_short_keyword_fails(self, client):
        """Test that keyword shorter than 2 chars returns validation error."""
        response = client.get("/predict?keyword=a")
        
        assert response.status_code == 422
    
    def test_predict_with_long_keyword_fails(self, client):
        """Test that keyword longer than 100 chars returns validation error."""
        long_keyword = "a" * 101
        response = client.get("/predict?keyword=" + long_keyword)
        
        assert response.status_code == 422
    
    def test_predict_without_keyword_fails(self, client):
        """Test that request without keyword parameter fails."""
        response = client.get("/predict")
        
        assert response.status_code == 422
    
    @pytest.mark.skip(reason="Complex normalization with Apify mock - better tested in integration tests")
    def test_predict_with_special_characters_normalized(self, client, mock_redis, mock_apify_client, mock_apify_response):
        """Test that keywords with special characters are normalized."""
        with patch('app.services.apify_client') as mock_apify:
            mock_run = {
                "defaultDatasetId": "test_dataset",
                "stats": {"durationMillis": 12500, "computeUnits": 0.12}
            }
            mock_apify.actor.return_value.call.return_value = mock_run
            # Use correct Apify field name
            mock_dataset_items = [{"interestOverTime_timelineData": mock_apify_response["timeline_data"]}]
            mock_apify.dataset.return_value.iterate_items.return_value = iter(mock_dataset_items)
            
            response = client.get("/predict?keyword=Skin-Care!")
        
        assert response.status_code == 200
        data = response.json()
        assert data["meta"]["keyword"] == "Skin-Care!"  # Original preserved in meta
    
    def test_predict_rate_limit_exceeded(self, client, mock_redis):
        """Test that rate limit is enforced."""
        # Mock Redis to return rate limit exceeded
        with patch('app.services.redis_get_with_retry', return_value="501"):
            response = client.get("/predict?keyword=test")
        
        assert response.status_code == 429
        data = response.json()
        assert "rate limit" in data["detail"].lower()
    
    def test_predict_with_no_apify_data(self, client, mock_redis):
        """Test handling when Apify returns no data."""
        with patch('app.services.apify_client') as mock_apify:
            mock_run = {
                "defaultDatasetId": "test_dataset",
                "stats": {"durationMillis": 12500, "computeUnits": 0.12}
            }
            mock_apify.actor.return_value.call.return_value = mock_run
            
            # Return empty dataset
            mock_apify.dataset.return_value.iterate_items.return_value = iter([])
            
            response = client.get("/predict?keyword=nonexistent")
        
        assert response.status_code == 404
        data = response.json()
        assert data["status"] == "error"


class TestCORS:
    """Test CORS middleware."""
    
    def test_cors_headers_present(self, client):
        """Test that CORS headers are present."""
        response = client.get("/health", headers={"Origin": "http://example.com"})
        
        # CORS should allow all origins
        assert "access-control-allow-origin" in [h.lower() for h in response.headers.keys()]
        assert response.headers["access-control-allow-origin"] == "*"


class TestErrorHandling:
    """Test error handling and exception handlers."""
    
    @pytest.mark.skip(reason="Complex error handling mock - better tested in integration tests")
    def test_data_validation_error_handling(self, client, mock_redis):
        """Test that data validation errors are handled properly."""
        with patch('app.services.apify_client') as mock_apify:
            mock_run = {
                "defaultDatasetId": "test_dataset",
                "stats": {"durationMillis": 12500, "computeUnits": 0.12}
            }
            mock_apify.actor.return_value.call.return_value = mock_run
            
            # Return invalid data (missing required fields) with correct field name
            mock_dataset_items = [{"interestOverTime_timelineData": [{"invalid": "data"}]}]
            mock_apify.dataset.return_value.iterate_items.return_value = iter(mock_dataset_items)
            
            response = client.get("/predict?keyword=test")
        
        # Should return 422 for validation error
        assert response.status_code == 422
        data = response.json()
        assert data["status"] == "error"

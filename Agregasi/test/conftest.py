import pytest
from fastapi.testclient import TestClient
from unittest.mock import Mock, patch
import json
import time

from app.main import app
from app.config import settings


@pytest.fixture
def client():
    """FastAPI test client fixture."""
    return TestClient(app)


@pytest.fixture
def mock_redis():
    """Mock Redis client for testing."""
    with patch('app.services.redis_client') as mock:
        # Setup default behavior
        mock.get.return_value = None
        mock.set.return_value = True
        mock.incr.return_value = 1
        mock.expire.return_value = True
        mock.delete.return_value = 1
        yield mock


@pytest.fixture
def mock_apify_response():
    """Mock Apify response data."""
    return {
        "timeline_data": [
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
        ],
        "stats": {
            "duration_ms": 12500,
            "compute_units": 0.12
        }
    }


@pytest.fixture
def mock_cached_data():
    """Mock cached data structure."""
    return {
        "timestamp": time.time() - 3600,  # 1 hour ago
        "data": {
            "recommendations": [
                {
                    "rank": 1,
                    "day": "Thursday",
                    "time_window": "19:00 - 22:00",
                    "score": 98.5
                },
                {
                    "rank": 2,
                    "day": "Thursday",
                    "time_window": "13:00 - 16:00",
                    "score": 87.2
                },
                {
                    "rank": 3,
                    "day": "Thursday",
                    "time_window": "07:00 - 10:00",
                    "score": 65.3
                }
            ],
            "chart_data": [
                {"day": "Thursday", "hour": "00:00", "score": 45.0},
                {"day": "Thursday", "hour": "01:00", "score": 50.0},
            ]
        },
        "stats": {
            "duration_ms": 12500,
            "compute_units": 0.12
        }
    }


@pytest.fixture
def mock_apify_client():
    """Mock Apify client."""
    with patch('app.services.apify_client') as mock:
        # Setup actor call mock
        mock_run = Mock()
        mock_run.return_value = {
            "defaultDatasetId": "test_dataset_123",
            "stats": {
                "durationMillis": 12500,
                "computeUnits": 0.12
            }
        }
        mock.actor.return_value.call = mock_run
        
        # Setup dataset mock
        mock_dataset = Mock()
        mock.dataset.return_value = mock_dataset
        
        yield mock

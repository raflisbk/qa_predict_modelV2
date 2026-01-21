"""
Comprehensive test suite for async job endpoints.
Tests /predict/async and /job/{job_id} endpoints.
"""
import pytest
import time
import json
from unittest.mock import patch, MagicMock, Mock
from fastapi.testclient import TestClient

from app.main import app
from app.jobs import JobManager, JobStatus


@pytest.fixture
def client():
    """Create test client."""
    return TestClient(app)


@pytest.fixture
def mock_background_tasks(monkeypatch):
    """Mock background tasks to prevent actual execution during tests."""
    mock_task = MagicMock()
    
    # Mock BackgroundTasks.add_task to do nothing
    from fastapi import BackgroundTasks
    original_add_task = BackgroundTasks.add_task
    
    def mock_add_task(self, func, *args, **kwargs):
        # Just record the call but don't execute
        mock_task.called = True
        mock_task.func = func
        mock_task.args = args
        mock_task.kwargs = kwargs
        return None
    
    monkeypatch.setattr(BackgroundTasks, 'add_task', mock_add_task)
    return mock_task


@pytest.fixture
def mock_redis_for_jobs(monkeypatch):
    """Mock Redis for job storage with fakeredis."""
    try:
        from fakeredis import FakeRedis
        fake_redis = FakeRedis(decode_responses=True)
        
        # Patch Redis client in both modules
        from app import jobs, services
        monkeypatch.setattr(jobs, 'redis_client', fake_redis)
        monkeypatch.setattr(services, 'redis_client', fake_redis)
        
        return fake_redis
    except ImportError:
        # Fallback to mock if fakeredis not installed
        job_storage = {}
        
        def mock_setex(key, ttl, value):
            job_storage[key] = value
            return True
        
        def mock_get(key):
            return job_storage.get(key)
        
        def mock_delete(key):
            if key in job_storage:
                del job_storage[key]
            return True
        
        from app import jobs
        mock_redis = MagicMock()
        mock_redis.setex.side_effect = mock_setex
        mock_redis.get.side_effect = mock_get
        mock_redis.delete.side_effect = mock_delete
        
        monkeypatch.setattr(jobs, 'redis_client', mock_redis)
        
        return mock_redis


class TestAsyncJobCreation:
    """Test suite for POST /predict/async endpoint."""
    
    def test_create_async_job_success(self, client, mock_redis_for_jobs, mock_background_tasks):
        """Test successful async job creation."""
        response = client.post("/predict/async?keyword=skincare")
        
        assert response.status_code == 202
        data = response.json()
        
        assert "job_id" in data
        assert data["status"] == "pending"
        assert "Job created" in data["message"]
        assert data["polling_url"].startswith("/job/")
        
    def test_create_async_job_returns_unique_ids(self, client, mock_redis_for_jobs, mock_background_tasks):
        """Test that each job gets unique ID."""
        response1 = client.post("/predict/async?keyword=test1")
        response2 = client.post("/predict/async?keyword=test2")
        
        job_id_1 = response1.json()["job_id"]
        job_id_2 = response2.json()["job_id"]
        
        assert job_id_1 != job_id_2
        
    def test_create_async_job_invalid_keyword_too_short(self, client):
        """Test job creation with too short keyword."""
        response = client.post("/predict/async?keyword=a")
        
        assert response.status_code == 422  # Validation error
        
    def test_create_async_job_invalid_keyword_too_long(self, client):
        """Test job creation with too long keyword."""
        long_keyword = "a" * 101
        response = client.post("/predict/async?keyword=" + long_keyword)
        
        assert response.status_code == 422
        
    def test_create_async_job_missing_keyword(self, client):
        """Test job creation without keyword parameter."""
        response = client.post("/predict/async")
        
        assert response.status_code == 422
        
    def test_create_async_job_stores_in_redis(self, client, mock_redis_for_jobs, mock_background_tasks):
        """Test that job is stored in Redis."""
        response = client.post("/predict/async?keyword=test")
        job_id = response.json()["job_id"]
        
        # Check Redis storage
        job_key = f"job:{job_id}"
        stored_data = mock_redis_for_jobs.get(job_key)
        assert stored_data is not None
        
        stored_job = json.loads(mock_redis_for_jobs[job_key])
        assert stored_job["job_id"] == job_id
        assert stored_job["keyword"] == "test"
        assert stored_job["status"] == JobStatus.PENDING


class TestJobStatusRetrieval:
    """Test suite for GET /job/{job_id} endpoint."""
    
    def test_get_job_status_pending(self, client, mock_redis_for_jobs, mock_background_tasks):
        """Test retrieving pending job status."""
        # Create job
        create_response = client.post("/predict/async?keyword=test")
        job_id = create_response.json()["job_id"]
        
        # Get status
        status_response = client.get(f"/job/{job_id}")
        
        assert status_response.status_code == 200
        data = status_response.json()
        
        assert data["job_id"] == job_id
        assert data["keyword"] == "test"
        assert data["status"] == "pending"
        assert data["progress"] == 0
        assert "created_at" in data
        assert "updated_at" in data
        
    def test_get_job_status_not_found(self, client, mock_redis_for_jobs, mock_background_tasks):
        """Test retrieving non-existent job."""
        fake_job_id = "00000000-0000-0000-0000-000000000000"
        response = client.get(f"/job/{fake_job_id}")
        
        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()
        
    def test_get_job_status_processing(self, client, mock_redis_for_jobs, mock_background_tasks):
        """Test retrieving processing job status."""
        # Create job
        create_response = client.post("/predict/async?keyword=test")
        job_id = create_response.json()["job_id"]
        
        # Simulate processing
        JobManager.set_processing(job_id)
        
        # Get status
        status_response = client.get(f"/job/{job_id}")
        data = status_response.json()
        
        assert data["status"] == "processing"
        assert data["progress"] > 0
        
    def test_get_job_status_completed(self, client, mock_redis_for_jobs, mock_background_tasks):
        """Test retrieving completed job status."""
        # Create job
        create_response = client.post("/predict/async?keyword=test")
        job_id = create_response.json()["job_id"]
        
        # Simulate completion
        result_data = {
            "status": "success",
            "meta": {"keyword": "test", "source": "cache"},
            "data": {"recommendations": [], "chart_data": []}
        }
        JobManager.set_completed(job_id, result_data)
        
        # Get status
        status_response = client.get(f"/job/{job_id}")
        data = status_response.json()
        
        assert data["status"] == "completed"
        assert data["progress"] == 100
        assert "result" in data
        assert data["result"]["status"] == "success"
        
    def test_get_job_status_failed(self, client, mock_redis_for_jobs, mock_background_tasks):
        """Test retrieving failed job status."""
        # Create job
        create_response = client.post("/predict/async?keyword=test")
        job_id = create_response.json()["job_id"]
        
        # Simulate failure
        JobManager.set_failed(job_id, "Data not found")
        
        # Get status
        status_response = client.get(f"/job/{job_id}")
        data = status_response.json()
        
        assert data["status"] == "failed"
        assert "error" in data
        assert "Data not found" in data["error"]


class TestJobLifecycle:
    """Test complete job lifecycle from creation to completion."""
    
    @patch('app.services.fetch_from_apify')
    @patch('app.services.process_data')
    def test_complete_job_lifecycle_success(
        self, 
        mock_process, 
        mock_fetch, 
        client, 
        mock_redis_for_jobs
    ):
        """Test full job lifecycle: create → process → complete."""
        # Mock Apify response
        mock_fetch.return_value = (
            [{"time": "1234567890", "value": [50]}],
            {"computeUnits": 0.5}
        )
        
        # Mock processed data
        mock_process.return_value = {
            "recommendations": [
                {"day": "Monday", "hour": 10, "recommendation": "Best time"}
            ],
            "chart_data": [{"date": "2024-01-01", "value": 50}]
        }
        
        # Create job
        create_response = client.post("/predict/async?keyword=test")
        job_id = create_response.json()["job_id"]
        
        # Wait for background task (small delay)
        time.sleep(1)
        
        # Check status - should be processing or completed
        status_response = client.get(f"/job/{job_id}")
        data = status_response.json()
        
        assert data["status"] in ["processing", "completed"]
        
    @patch('app.services.fetch_from_apify')
    def test_job_lifecycle_with_apify_failure(
        self,
        mock_fetch,
        client,
        mock_redis_for_jobs
    ):
        """Test job lifecycle when Apify fails."""
        from app.services import DataNotFoundException
        
        # Mock Apify failure
        mock_fetch.side_effect = DataNotFoundException("No data available")
        
        # Create job
        create_response = client.post("/predict/async?keyword=test")
        job_id = create_response.json()["job_id"]
        
        # Wait for background task
        time.sleep(1)
        
        # Check status - should be failed
        status_response = client.get(f"/job/{job_id}")
        data = status_response.json()
        
        assert data["status"] == "failed"
        assert "error" in data


class TestJobProgressTracking:
    """Test job progress updates."""
    
    def test_job_progress_updates(self, client, mock_redis_for_jobs, mock_background_tasks):
        """Test that job progress can be updated."""
        # Create job
        create_response = client.post("/predict/async?keyword=test")
        job_id = create_response.json()["job_id"]
        
        # Update progress
        JobManager.set_progress(job_id, 50, "Halfway done")
        
        # Check progress
        status_response = client.get(f"/job/{job_id}")
        data = status_response.json()
        
        assert data["progress"] == 50
        assert data["message"] == "Halfway done"
        
    def test_job_progress_sequence(self, client, mock_redis_for_jobs, mock_background_tasks):
        """Test progress updates in sequence."""
        # Create job
        create_response = client.post("/predict/async?keyword=test")
        job_id = create_response.json()["job_id"]
        
        # Simulate progress sequence
        JobManager.set_processing(job_id)
        status1 = client.get(f"/job/{job_id}").json()
        assert status1["progress"] == 10
        
        JobManager.set_progress(job_id, 30, "Fetching...")
        status2 = client.get(f"/job/{job_id}").json()
        assert status2["progress"] == 30
        
        JobManager.set_progress(job_id, 80, "Processing...")
        status3 = client.get(f"/job/{job_id}").json()
        assert status3["progress"] == 80
        
        result_data = {"status": "success", "data": {}}
        JobManager.set_completed(job_id, result_data)
        status4 = client.get(f"/job/{job_id}").json()
        assert status4["progress"] == 100


class TestConcurrentJobs:
    """Test handling multiple concurrent jobs."""
    
    def test_multiple_jobs_concurrent(self, client, mock_redis_for_jobs, mock_background_tasks):
        """Test creating multiple jobs concurrently."""
        keywords = ["skincare", "makeup", "fashion", "beauty", "health"]
        job_ids = []
        
        # Create multiple jobs
        for keyword in keywords:
            response = client.post(f"/predict/async?keyword={keyword}")
            assert response.status_code == 202
            job_ids.append(response.json()["job_id"])
        
        # Verify all jobs are unique
        assert len(job_ids) == len(set(job_ids))
        
        # Verify all jobs can be retrieved
        for job_id in job_ids:
            status_response = client.get(f"/job/{job_id}")
            assert status_response.status_code == 200
            
    def test_job_isolation(self, client, mock_redis_for_jobs, mock_background_tasks):
        """Test that jobs are isolated from each other."""
        # Create two jobs
        response1 = client.post("/predict/async?keyword=test1")
        response2 = client.post("/predict/async?keyword=test2")
        
        job_id_1 = response1.json()["job_id"]
        job_id_2 = response2.json()["job_id"]
        
        # Update job 1
        JobManager.set_processing(job_id_1)
        
        # Check job 1 is processing, job 2 is still pending
        status1 = client.get(f"/job/{job_id_1}").json()
        status2 = client.get(f"/job/{job_id_2}").json()
        
        assert status1["status"] == "processing"
        assert status2["status"] == "pending"


class TestEdgeCases:
    """Test edge cases and error scenarios."""
    
    def test_special_characters_in_keyword(self, client, mock_redis_for_jobs, mock_background_tasks):
        """Test keywords with special characters."""
        response = client.post("/predict/async?keyword=test%20keyword")
        
        assert response.status_code == 202
        
    def test_unicode_keyword(self, client, mock_redis_for_jobs, mock_background_tasks):
        """Test Unicode characters in keyword."""
        response = client.post("/predict/async?keyword=스킨케어")
        
        assert response.status_code == 202
        
    def test_numeric_keyword(self, client, mock_redis_for_jobs, mock_background_tasks):
        """Test numeric keyword."""
        response = client.post("/predict/async?keyword=12345")
        
        assert response.status_code == 202


class TestResponseSchema:
    """Test response schema compliance."""
    
    def test_job_create_response_schema(self, client, mock_redis_for_jobs, mock_background_tasks):
        """Test JobCreateResponse schema."""
        response = client.post("/predict/async?keyword=test")
        data = response.json()
        
        required_fields = ["job_id", "status", "message", "polling_url"]
        for field in required_fields:
            assert field in data
            
        assert isinstance(data["job_id"], str)
        assert isinstance(data["status"], str)
        assert isinstance(data["message"], str)
        assert isinstance(data["polling_url"], str)
        
    def test_job_status_response_schema(self, client, mock_redis_for_jobs, mock_background_tasks):
        """Test JobStatusResponse schema."""
        # Create job
        create_response = client.post("/predict/async?keyword=test")
        job_id = create_response.json()["job_id"]
        
        # Get status
        status_response = client.get(f"/job/{job_id}")
        data = status_response.json()
        
        required_fields = [
            "job_id", "keyword", "status", "progress", 
            "message", "created_at", "updated_at"
        ]
        for field in required_fields:
            assert field in data
            
        assert isinstance(data["progress"], int)
        assert 0 <= data["progress"] <= 100


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--cov=app", "--cov-report=html"])

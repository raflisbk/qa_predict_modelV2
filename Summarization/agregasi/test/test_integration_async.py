"""
Integration tests for async job workflow.
Tests real end-to-end scenarios.
"""
import pytest
import time
from fastapi.testclient import TestClient

from app.main import app


@pytest.fixture
def client():
    """Create test client."""
    return TestClient(app)


class TestAsyncWorkflowIntegration:
    """Integration tests for complete async workflow."""
    
    @pytest.mark.integration
    def test_full_async_workflow_with_cache(self, client):
        """
        Test complete async workflow:
        1. Create job
        2. Poll status until complete
        3. Verify result structure
        """
        # Step 1: Create async job (using low-traffic keyword)
        create_response = client.post("/predict/async?keyword=pytest")
        assert create_response.status_code == 202
        
        job_data = create_response.json()
        job_id = job_data["job_id"]
        
        # Step 2: Poll job status (max 2 minutes)
        max_attempts = 60
        poll_interval = 2  # seconds
        
        for attempt in range(max_attempts):
            status_response = client.get(f"/job/{job_id}")
            assert status_response.status_code == 200
            
            status_data = status_response.json()
            
            if status_data["status"] == "completed":
                # Step 3: Verify result structure
                assert "result" in status_data
                result = status_data["result"]
                
                assert result["status"] == "success"
                assert "meta" in result
                assert "data" in result
                assert "recommendations" in result["data"]
                assert "chart_data" in result["data"]
                
                print(f"\n✅ Job completed in {attempt * poll_interval}s")
                return
                
            elif status_data["status"] == "failed":
                pytest.fail(f"Job failed: {status_data.get('error')}")
                
            # Wait before next poll
            time.sleep(poll_interval)
        
        pytest.fail(f"Job did not complete within {max_attempts * poll_interval}s")
        
    @pytest.mark.integration
    def test_sync_vs_async_comparison(self, client):
        """
        Compare sync and async endpoints with same keyword.
        Both should return similar results.
        """
        keyword = "pytest"
        
        # Test sync endpoint
        sync_start = time.time()
        sync_response = client.get(f"/predict?keyword={keyword}")
        sync_duration = time.time() - sync_start
        
        assert sync_response.status_code == 200
        sync_data = sync_response.json()
        
        # Test async endpoint
        async_start = time.time()
        create_response = client.post(f"/predict/async?keyword={keyword}")
        create_duration = time.time() - async_start
        
        assert create_response.status_code == 202
        job_id = create_response.json()["job_id"]
        
        # Async creation should be much faster than sync
        assert create_duration < 1.0, "Async job creation should be instant"
        
        # Poll until complete
        max_attempts = 60
        for _ in range(max_attempts):
            status_response = client.get(f"/job/{job_id}")
            status_data = status_response.json()
            
            if status_data["status"] == "completed":
                async_data = status_data["result"]
                
                # Compare results (should be similar since cached)
                assert async_data["status"] == sync_data["status"]
                assert async_data["meta"]["keyword"] == sync_data["meta"]["keyword"]
                
                print(f"\n📊 Sync duration: {sync_duration:.2f}s")
                print(f"📊 Async create: {create_duration:.3f}s")
                print(f"📊 Result match: ✅")
                return
                
            time.sleep(2)
        
        pytest.fail("Async job did not complete")
        
    @pytest.mark.integration
    def test_multiple_concurrent_jobs_integration(self, client):
        """
        Test multiple jobs running concurrently.
        Verify all complete successfully.
        """
        keywords = ["uvicorn", "fastapi", "pytest"]
        jobs = []
        
        # Create all jobs
        create_start = time.time()
        for keyword in keywords:
            response = client.post(f"/predict/async?keyword={keyword}")
            assert response.status_code == 202
            jobs.append({
                "job_id": response.json()["job_id"],
                "keyword": keyword
            })
        create_duration = time.time() - create_start
        
        # All jobs should be created quickly
        assert create_duration < 2.0, "Creating 3 jobs should be instant"
        
        # Poll all jobs until complete
        max_attempts = 120  # 4 minutes
        completed_jobs = set()
        
        for attempt in range(max_attempts):
            for job in jobs:
                if job["job_id"] in completed_jobs:
                    continue
                    
                status_response = client.get(f"/job/{job['job_id']}")
                status_data = status_response.json()
                
                if status_data["status"] == "completed":
                    completed_jobs.add(job["job_id"])
                    print(f"\n✅ Job for '{job['keyword']}' completed")
                elif status_data["status"] == "failed":
                    pytest.fail(f"Job for '{job['keyword']}' failed")
            
            # All completed?
            if len(completed_jobs) == len(jobs):
                print(f"\n🎉 All {len(jobs)} jobs completed!")
                return
                
            time.sleep(2)
        
        pytest.fail(f"Only {len(completed_jobs)}/{len(jobs)} jobs completed")


class TestErrorHandlingIntegration:
    """Integration tests for error scenarios."""
    
    @pytest.mark.integration
    def test_invalid_keyword_apify_failure(self, client):
        """
        Test job with keyword that might fail in Apify.
        Job should fail gracefully with error message.
        """
        # Use very unusual keyword that might not have data
        create_response = client.post("/predict/async?keyword=xyzabc123unlikely")
        assert create_response.status_code == 202
        
        job_id = create_response.json()["job_id"]
        
        # Poll until complete or failed
        max_attempts = 60
        for _ in range(max_attempts):
            status_response = client.get(f"/job/{job_id}")
            status_data = status_response.json()
            
            if status_data["status"] == "failed":
                # Should have error message
                assert "error" in status_data
                assert len(status_data["error"]) > 0
                print(f"\n✅ Job failed gracefully: {status_data['error']}")
                return
                
            elif status_data["status"] == "completed":
                # Might succeed if Apify finds data
                print(f"\n✅ Job completed (Apify found data)")
                return
                
            time.sleep(2)
        
        pytest.fail("Job did not complete or fail within timeout")


class TestCachingBehavior:
    """Test caching behavior with async endpoints."""
    
    @pytest.mark.integration
    def test_second_request_uses_cache(self, client):
        """
        Test that second request for same keyword is much faster.
        Should use cached data.
        """
        keyword = "redisdb"
        
        # First request (fresh fetch)
        create1_start = time.time()
        response1 = client.post(f"/predict/async?keyword={keyword}")
        job_id_1 = response1.json()["job_id"]
        
        # Wait for completion
        max_attempts = 60
        first_completed = False
        
        for _ in range(max_attempts):
            status = client.get(f"/job/{job_id_1}").json()
            if status["status"] == "completed":
                first_duration = time.time() - create1_start
                first_completed = True
                break
            time.sleep(2)
        
        assert first_completed, "First job did not complete"
        
        # Second request (should use cache)
        create2_start = time.time()
        response2 = client.post(f"/predict/async?keyword={keyword}")
        job_id_2 = response2.json()["job_id"]
        
        # Should complete much faster (from cache)
        for attempt in range(10):  # Only 20 seconds max
            status = client.get(f"/job/{job_id_2}").json()
            if status["status"] == "completed":
                second_duration = time.time() - create2_start
                
                # Cached request should be significantly faster
                assert second_duration < first_duration * 0.5
                
                # Should indicate cache as source
                assert status["result"]["meta"]["source"] in ["cache", "cache_fresh"]
                
                print(f"\n📊 First request: {first_duration:.2f}s (Apify fetch)")
                print(f"📊 Second request: {second_duration:.2f}s (Cache)")
                print(f"📊 Speed improvement: {first_duration/second_duration:.1f}x faster")
                return
                
            time.sleep(2)
        
        pytest.fail("Second job did not use cache")


class TestResponseTimeMetrics:
    """Test and measure response time metrics."""
    
    @pytest.mark.integration
    def test_job_creation_response_time(self, client):
        """Test that job creation is consistently fast."""
        response_times = []
        
        for i in range(5):
            start = time.time()
            response = client.post(f"/predict/async?keyword=apitest{i}")
            duration = (time.time() - start) * 1000  # Convert to ms
            
            assert response.status_code == 202
            response_times.append(duration)
        
        avg_time = sum(response_times) / len(response_times)
        max_time = max(response_times)
        
        # Job creation should be consistently fast
        assert avg_time < 500, f"Average response time too slow: {avg_time:.0f}ms"
        assert max_time < 1000, f"Max response time too slow: {max_time:.0f}ms"
        
        print(f"\n⚡ Avg job creation time: {avg_time:.0f}ms")
        print(f"⚡ Max job creation time: {max_time:.0f}ms")
        print(f"⚡ Min job creation time: {min(response_times):.0f}ms")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-m", "integration"])

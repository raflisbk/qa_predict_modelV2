# Example: Async Job Pattern for handling slow Apify calls
# This is a CONCEPT - would require significant refactoring

from fastapi import BackgroundTasks
from typing import Dict
import uuid

# In-memory job storage (production: use Redis)
jobs: Dict[str, dict] = {}

@app.post("/predict/async")
async def predict_async(keyword: str, background_tasks: BackgroundTasks):
    """
    Async endpoint - returns job ID immediately.
    User polls /job/{job_id} for results.
    """
    # Validate keyword
    if len(keyword) < 2:
        raise HTTPException(400, "Keyword too short")
    
    # Check cache first
    cached = redis_get(f"trends:{keyword}")
    if cached:
        return {"status": "completed", "data": json.loads(cached)}
    
    # Create job
    job_id = str(uuid.uuid4())
    jobs[job_id] = {
        "status": "processing",
        "keyword": keyword,
        "created_at": time.time()
    }
    
    # Start background task
    background_tasks.add_task(fetch_and_cache, keyword, job_id)
    
    return {
        "job_id": job_id,
        "status": "processing",
        "message": "Data is being fetched. Poll /job/{job_id} for status.",
        "poll_url": f"/job/{job_id}"
    }

@app.get("/job/{job_id}")
async def get_job_status(job_id: str):
    """Poll endpoint to check job status."""
    if job_id not in jobs:
        raise HTTPException(404, "Job not found")
    
    job = jobs[job_id]
    
    if job["status"] == "completed":
        # Return data and cleanup
        data = job["data"]
        del jobs[job_id]
        return {"status": "completed", "data": data}
    
    elif job["status"] == "failed":
        error = job.get("error", "Unknown error")
        del jobs[job_id]
        raise HTTPException(500, error)
    
    else:
        # Still processing
        elapsed = time.time() - job["created_at"]
        return {
            "status": "processing",
            "elapsed_seconds": int(elapsed),
            "estimated_remaining": max(0, 180 - elapsed)  # Estimate
        }

def fetch_and_cache(keyword: str, job_id: str):
    """Background task to fetch from Apify and cache."""
    try:
        data, source, stats = get_prediction_swr(keyword, None)
        jobs[job_id] = {
            "status": "completed",
            "data": {"status": "success", "meta": {...}, "data": data}
        }
    except Exception as e:
        jobs[job_id] = {
            "status": "failed",
            "error": str(e)
        }

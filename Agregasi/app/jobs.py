"""
Job management for async predictions.
Stores job status and results in Redis.
"""
import uuid
import json
import time
from typing import Optional, Dict, Any
from datetime import datetime

from .services import redis_pool, logger


class JobStatus:
    """Job status constants."""
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


class JobManager:
    """Manage async jobs in Redis."""
    
    JOB_TTL = 3600  # Jobs expire after 1 hour
    JOB_PREFIX = "job:"
    
    @staticmethod
    def create_job(keyword: str) -> str:
        """
        Create a new job and store in Redis.
        
        Args:
            keyword: Search keyword for the job
            
        Returns:
            job_id: Unique identifier for the job
        """
        job_id = str(uuid.uuid4())
        
        job_data = {
            "job_id": job_id,
            "keyword": keyword,
            "status": JobStatus.PENDING,
            "created_at": time.time(),
            "updated_at": time.time(),
            "progress": 0,
            "message": "Job created, waiting to start"
        }
        
        redis_client = redis_pool
        redis_client.setex(
            f"{JobManager.JOB_PREFIX}{job_id}",
            JobManager.JOB_TTL,
            json.dumps(job_data)
        )
        
        logger.info(f"Job created: {job_id} for keyword: {keyword}")
        return job_id
    
    @staticmethod
    def get_job(job_id: str) -> Optional[Dict[str, Any]]:
        """
        Get job data from Redis.
        
        Args:
            job_id: Job identifier
            
        Returns:
            Job data dict or None if not found
        """
        redis_client = redis_pool
        job_data = redis_client.get(f"{JobManager.JOB_PREFIX}{job_id}")
        
        if job_data:
            return json.loads(job_data)
        return None
    
    @staticmethod
    def update_job(job_id: str, updates: Dict[str, Any]) -> None:
        """
        Update job data in Redis.
        
        Args:
            job_id: Job identifier
            updates: Dict of fields to update
        """
        job_data = JobManager.get_job(job_id)
        if not job_data:
            logger.error(f"Job not found: {job_id}")
            return
        
        # Update fields
        job_data.update(updates)
        job_data["updated_at"] = time.time()
        
        # Save back to Redis
        redis_client = redis_pool
        redis_client.setex(
            f"{JobManager.JOB_PREFIX}{job_id}",
            JobManager.JOB_TTL,
            json.dumps(job_data)
        )
        
        logger.info(f"Job updated: {job_id}, status: {job_data.get('status')}")
    
    @staticmethod
    def set_processing(job_id: str) -> None:
        """Mark job as processing."""
        JobManager.update_job(job_id, {
            "status": JobStatus.PROCESSING,
            "progress": 10,
            "message": "Fetching data from Google Trends..."
        })
    
    @staticmethod
    def set_progress(job_id: str, progress: int, message: str) -> None:
        """Update job progress."""
        JobManager.update_job(job_id, {
            "progress": progress,
            "message": message
        })
    
    @staticmethod
    def set_completed(job_id: str, result_data: Dict[str, Any]) -> None:
        """Mark job as completed with results."""
        JobManager.update_job(job_id, {
            "status": JobStatus.COMPLETED,
            "progress": 100,
            "message": "Data processed successfully",
            "result": result_data
        })
    
    @staticmethod
    def set_failed(job_id: str, error: str) -> None:
        """Mark job as failed with error message."""
        JobManager.update_job(job_id, {
            "status": JobStatus.FAILED,
            "progress": 0,
            "message": f"Failed: {error}",
            "error": error
        })

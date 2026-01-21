"""
Pydantic schemas for async job responses.
"""
from pydantic import BaseModel, Field
from typing import Optional, Any, Dict
from enum import Enum


class JobStatusEnum(str, Enum):
    """Job status enumeration."""
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


class JobCreateResponse(BaseModel):
    """Response when creating async job."""
    job_id: str = Field(..., description="Unique job identifier")
    status: str = Field(..., description="Job status (pending)")
    message: str = Field(..., description="Human-readable message")
    polling_url: str = Field(..., description="URL to check job status")
    
    class Config:
        json_schema_extra = {
            "example": {
                "job_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
                "status": "pending",
                "message": "Job created. Use polling_url to check progress.",
                "polling_url": "/job/a1b2c3d4-e5f6-7890-abcd-ef1234567890"
            }
        }


class JobStatusResponse(BaseModel):
    """Response for job status check."""
    job_id: str = Field(..., description="Unique job identifier")
    keyword: str = Field(..., description="Search keyword")
    status: JobStatusEnum = Field(..., description="Current job status")
    progress: int = Field(..., ge=0, le=100, description="Progress percentage (0-100)")
    message: str = Field(..., description="Current status message")
    created_at: float = Field(..., description="Unix timestamp when job was created")
    updated_at: float = Field(..., description="Unix timestamp of last update")
    result: Optional[Dict[str, Any]] = Field(None, description="Result data (only when completed)")
    error: Optional[str] = Field(None, description="Error message (only when failed)")
    
    class Config:
        json_schema_extra = {
            "example": {
                "job_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
                "keyword": "skincare",
                "status": "processing",
                "progress": 50,
                "message": "Processing data...",
                "created_at": 1704844800.0,
                "updated_at": 1704844850.0,
                "result": None,
                "error": None
            }
        }

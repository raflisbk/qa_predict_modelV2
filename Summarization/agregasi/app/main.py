import logging
import sys
from fastapi import FastAPI, Query, BackgroundTasks, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.schemas import PredictionResponse, MetaData
from app.job_schemas import JobCreateResponse, JobStatusResponse
from app.services import get_prediction_swr, DataNotFoundException, DataValidationException
from app.jobs import JobManager, JobStatus

# Setup logging
logger = logging.getLogger(__name__)

# Suppress traceback for reload-related errors in development
sys.tracebacklimit = 0 if "uvicorn" in sys.argv[0] else None

# Initialize FastAPI application
app = FastAPI(
    title="Google Trends Prediction API",
    description="Google Trends Analytics",
    version="1.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Global exception handler for DataNotFoundException
@app.exception_handler(DataNotFoundException)
async def data_not_found_exception_handler(request: Request, exc: DataNotFoundException):
    """Handle DataNotFoundException and return 404 JSON response."""
    logger.error(f"Data not found: {str(exc)}")
    return JSONResponse(
        status_code=404,
        content={
            "status": "error",
            "message": str(exc),
            "detail": "No trend data available for the specified keyword"
        }
    )


# Global exception handler for DataValidationException
@app.exception_handler(DataValidationException)
async def data_validation_exception_handler(request: Request, exc: DataValidationException):
    """Handle DataValidationException and return 422 JSON response."""
    logger.error(f"Data validation failed: {str(exc)}")
    return JSONResponse(
        status_code=422,
        content={
            "status": "error",
            "message": "Data validation failed",
            "detail": str(exc)
        }
    )


@app.get("/health")
async def health_check():
    """
    Health check endpoint.
    
    Returns:
        Dictionary with status
    """
    return {"status": "ok"}


@app.get("/predict", response_model=PredictionResponse)
async def predict(
    keyword: str = Query(..., min_length=2, max_length=100, description="Search keyword"),
    background_tasks: BackgroundTasks = BackgroundTasks()
):
    """
    Get Google Trends prediction.
    
    Args:
        keyword: Search keyword\n
        
    Returns:
        PredictionResponse
    """
    logger.info(f"Predict endpoint called with keyword: {keyword}")
    
    # Get prediction data using SWR pattern
    data, source, stats = get_prediction_swr(keyword, background_tasks)
    
    # Remove score from recommendations before sending to user
    if "recommendations" in data:
        for rec in data["recommendations"]:
            rec.pop("score", None)
    
    # Remove chart_data from response (not needed in API output)
    data.pop("chart_data", None)
    
    # Build response
    response = PredictionResponse(
        status="success",
        meta=MetaData(
            keyword=keyword,
            source=source,
            apify_stats=stats
        ),
        data=data
    )
    
    logger.info(f"Successfully processed prediction for: {keyword}")
    return response


# ====== ASYNC ENDPOINTS ======

def process_job_async(job_id: str, keyword: str):
    """
    Background task to process job asynchronously.
    
    Args:
        job_id: Unique job identifier
        keyword: Search keyword
    """
    try:
        # Mark as processing
        JobManager.set_processing(job_id)
        logger.info(f"Job {job_id} started processing keyword: {keyword}")
        
        # Fetch and process data (this takes 60-180s for viral keywords)
        JobManager.set_progress(job_id, 30, "Fetching from Google Trends...")
        
        # Use existing service (no background tasks needed here)
        from app.services import get_prediction
        data, source, stats = get_prediction(keyword)
        
        JobManager.set_progress(job_id, 80, "Processing data...")
        
        # Remove score from recommendations
        if "recommendations" in data:
            for rec in data["recommendations"]:
                rec.pop("score", None)
        
        # Remove chart_data from response (not needed in API output)
        data.pop("chart_data", None)
        
        # Build result
        result = {
            "status": "success",
            "meta": {
                "keyword": keyword,
                "source": source,
                "apify_stats": stats
            },
            "data": data
        }
        
        # Mark as completed
        JobManager.set_completed(job_id, result)
        logger.info(f"Job {job_id} completed successfully")
        
    except DataNotFoundException as e:
        logger.error(f"Job {job_id} failed: Data not found - {str(e)}")
        JobManager.set_failed(job_id, f"No trend data available: {str(e)}")
        
    except DataValidationException as e:
        logger.error(f"Job {job_id} failed: Validation error - {str(e)}")
        JobManager.set_failed(job_id, f"Data validation failed: {str(e)}")
        
    except Exception as e:
        logger.error(f"Job {job_id} failed: Unexpected error - {str(e)}")
        JobManager.set_failed(job_id, f"Unexpected error: {str(e)}")


@app.post("/predict/async", response_model=JobCreateResponse, status_code=202)
async def predict_async(
    keyword: str = Query(..., min_length=2, max_length=100, description="Search keyword"),
    background_tasks: BackgroundTasks = BackgroundTasks()
):
    """
    Create async job  Google Trends pred.
    
    Args:
        keyword: Search keyword
    Returns:
        JobCreateResponse job_id and polling URL
    """
    logger.info(f"Async predict endpoint called with keyword: {keyword}")
    
    try:
        # Create job
        job_id = JobManager.create_job(keyword)
        logger.info(f"Job created successfully: {job_id}")
        
        # Schedule background processing
        background_tasks.add_task(process_job_async, job_id, keyword)
        
        return JobCreateResponse(
            job_id=job_id,
            status="pending",
            message="Job created. Use polling_url to check progress.",
            polling_url=f"/job/{job_id}"
        )
    except Exception as e:
        logger.error(f"Failed to create async job: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Failed to create job: {str(e)}"
        )


@app.get("/job/{job_id}", response_model=JobStatusResponse)
async def get_job_status(job_id: str):
    """
    Get job status and results.
    
    Args:
        job_id: Unique job identifier from /predict/async
        
    Returns:
        JobStatusResponse with current status and result (if completed)
        
    Raises:
        404: Job not found
    """
    logger.info(f"Job status check for: {job_id}")
    
    job_data = JobManager.get_job(job_id)
    
    if not job_data:
        logger.warning(f"Job not found: {job_id}")
        raise HTTPException(
            status_code=404,
            detail="Job not found. Jobs expire after 1 hour."
        )
    
    return JobStatusResponse(**job_data)

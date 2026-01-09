import logging
from fastapi import FastAPI, Query, BackgroundTasks, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.schemas import PredictionResponse, MetaData
from app.services import get_prediction_swr, DataNotFoundException, DataValidationException

# Setup logging
logger = logging.getLogger(__name__)

# Initialize FastAPI application
app = FastAPI(
    title="Google Trends Prediction API",
    description="High-performance REST API for Google Trends analysis with Redis caching",
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
    Get Google Trends prediction for a keyword with SWR caching.
    
    Args:
        keyword: Search keyword (2-100 characters)
        background_tasks: FastAPI background tasks
        
    Returns:
        PredictionResponse with recommendations and chart data
    """
    logger.info(f"Predict endpoint called with keyword: {keyword}")
    
    # Get prediction data using SWR pattern
    data, source, stats = get_prediction_swr(keyword, background_tasks)
    
    # Remove score from recommendations before sending to user
    if "recommendations" in data:
        for rec in data["recommendations"]:
            rec.pop("score", None)
    
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

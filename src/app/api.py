from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field, validator
from typing import List, Optional, Dict, Any
from dotenv import load_dotenv
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from datetime import datetime, timedelta
import time
import logging
import sys
import os

# Load env
load_dotenv()

# Add path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../')))

from src.inference.lstm_inference import (
    LSTMDailyInference, 
    ModelLoadError, 
    PreprocessingError, 
    InferenceError
)
from src.app.services import ApifyService, ApifyServiceError

# Config vars
MODEL_PATH = os.getenv("MODEL_PATH", "models\\daily\\lstm\\onnx\\lstm_daily.onnx")
SCALER_PATH = os.getenv("SCALER_PATH", "models\\daily\\lstm\\onnx\\minmax_scaler.pkl")
APIFY_API_TOKEN = os.getenv("APIFY_API_TOKEN")

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger("api")

# Rate limiter
limiter = Limiter(key_func=get_remote_address)

# API Metadata
API_TITLE = "Best Time Post"
API_DESCRIPTION = """
API untuk memprediksi waktu terbaik posting berdasarkan tren Google Trends.

## Fitur
- **Auto-Fetch**: Cukup kirim keyword, data diambil otomatis dari Google Trends
- **Manual Mode**: Kirim 14 data point secara manual
- **Best Days Ranking**: Top 3 hari terbaik dengan confidence score
- **Performance Metrics**: Latency dan inference time di setiap response

## Rate Limit
Maksimum 10 request per menit per IP.
"""

API_TAGS = [
    {"name": "Health", "description": "Cek status server"},
    {"name": "Prediction", "description": "Endpoint prediksi tren"}
]

app = FastAPI(
    title=API_TITLE,
    description=API_DESCRIPTION,
    version="1.4.0",
    openapi_tags=API_TAGS
)

# Add rate limiter
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global vars
inference_engine = None
apify_service = None

# --- Schemas ---

class PredictionRequest(BaseModel):
    """Request body untuk prediksi."""
    keyword: Optional[str] = Field(
        None, 
        description="Keyword untuk auto-fetch dari Google Trends",
        example="kopi"
    )
    category: Optional[str] = Field(
        None, 
        description="Kategori keyword (opsional)",
        example="Food & Drink"
    )
    data: Optional[List[float]] = Field(
        None, 
        description="Data manual 14 hari (override auto-fetch)",
        example=[45, 48, 52, 55, 60, 58, 62, 65, 70, 68, 72, 75, 78, 80]
    )
    
    @validator('data')
    def validate_data(cls, v):
        if v is not None:
             if len(v) != 14:
                 raise ValueError("Data harus tepat 14 nilai")
             if any(x < 0 for x in v):
                 raise ValueError("Nilai tidak boleh negatif")
        return v

class BestDay(BaseModel):
    """Info hari terbaik."""
    rank: int = Field(..., example=1)
    date: str = Field(..., example="2024-12-23")
    day_name: str = Field(..., example="Senin")
    interest_value: float = Field(..., example=81.0)
    confidence: str = Field(..., example="100%")

class DayForecast(BaseModel):
    """Forecast per hari."""
    day_index: int = Field(..., example=1)
    date: str = Field(..., example="2024-12-23")
    day_name: str = Field(..., example="Senin")
    interest_value: float = Field(..., example=80.1)

class PerformanceMetrics(BaseModel):
    """Metrics performa."""
    fetch_time_ms: Optional[float] = Field(None, description="Waktu fetch data (ms)")
    inference_time_ms: float = Field(..., description="Waktu inference model (ms)")
    total_time_ms: float = Field(..., description="Total waktu proses (ms)")

class MetaInfo(BaseModel):
    """Metadata request."""
    source: str = Field(..., example="apify")
    keyword: Optional[str] = Field(None, example="kopi")
    category: Optional[str] = Field(None, example="Food & Drink")
    input_length: int = Field(..., example=14)
    cached: bool = Field(..., description="Data dari cache?")

class PredictionResponse(BaseModel):
    """Response prediksi."""
    status: str = Field(..., example="success")
    best_days: List[BestDay] = Field(..., description="Top 3 hari terbaik untuk posting")
    performance: PerformanceMetrics = Field(..., description="Metrics performa")
    meta: MetaInfo = Field(..., description="Metadata")

class HealthResponse(BaseModel):
    """Response health check."""
    status: str = Field(..., example="healthy")
    model_loaded: bool = Field(..., description="Status model ONNX")
    apify_connected: bool = Field(..., description="Status koneksi Apify")

class ErrorResponse(BaseModel):
    """Response error."""
    status: str = Field(default="error")
    message: str = Field(..., example="Model down")
    detail: Optional[str] = None
    error_code: Optional[str] = Field(None, description="Kode error internal")

# Startup event
@app.on_event("startup")
async def startup_event():
    global inference_engine, apify_service
    
    try:
        logger.info("Init model...")
        if not os.path.exists(MODEL_PATH):
             model_path_rel = os.path.join("../../", MODEL_PATH)
             scaler_path_rel = os.path.join("../../", SCALER_PATH)
        else:
             model_path_rel = MODEL_PATH
             scaler_path_rel = SCALER_PATH

        inference_engine = LSTMDailyInference(model_path_rel, scaler_path_rel)
        logger.info("Model ready")
    except Exception as e:
        logger.critical(f"Model failed: {e}")
        inference_engine = None

    try:
        logger.info("Init Apify...")
        apify_service = ApifyService(APIFY_API_TOKEN)
        logger.info("Apify ready")
    except Exception as e:
        logger.error(f"Apify failed: {e}")
        apify_service = None

# Middleware
@app.middleware("http")
async def add_process_time_header(request: Request, call_next):
    start_time = time.time()
    response = await call_next(request)
    process_time = time.time() - start_time
    response.headers["X-Process-Time"] = f"{process_time:.4f}s"
    logger.info(f"{request.method} {request.url.path} - {process_time:.4f}s")
    return response

# --- Exception Handlers ---

@app.exception_handler(ModelLoadError)
async def model_load_error_handler(request, exc):
    return JSONResponse(
        status_code=503, 
        content={"status": "error", "message": "Model gagal dimuat", "detail": str(exc), "error_code": "MODEL_LOAD_ERROR"}
    )

@app.exception_handler(PreprocessingError)
async def preprocessing_error_handler(request, exc):
    return JSONResponse(
        status_code=422, 
        content={"status": "error", "message": "Preprocessing gagal", "detail": str(exc), "error_code": "PREPROCESSING_ERROR"}
    )

@app.exception_handler(InferenceError)
async def inference_error_handler(request, exc):
    return JSONResponse(
        status_code=500, 
        content={"status": "error", "message": "Inference gagal", "detail": str(exc), "error_code": "INFERENCE_ERROR"}
    )

@app.exception_handler(ApifyServiceError)
async def apify_error_handler(request, exc):
    return JSONResponse(
        status_code=502, 
        content={"status": "error", "message": "Fetch data gagal", "detail": str(exc), "error_code": "APIFY_ERROR"}
    )

@app.exception_handler(ValueError)
async def validation_error_handler(request, exc):
    return JSONResponse(
        status_code=400, 
        content={"status": "error", "message": "Input tidak valid", "detail": str(exc), "error_code": "VALIDATION_ERROR"}
    )

# --- Endpoints ---

@app.get(
    "/health",
    tags=["Health"],
    response_model=HealthResponse,
    summary="Cek Status Server",
    description="Mengecek apakah server dan dependency berjalan normal.",
    responses={
        200: {"description": "Server sehat"},
        503: {"description": "Server tidak siap", "model": ErrorResponse}
    }
)
async def health_check():
    status = {
        "status": "healthy",
        "model_loaded": inference_engine is not None,
        "apify_connected": apify_service is not None
    }
    if not status["model_loaded"]:
        raise HTTPException(status_code=503, detail="Model tidak tersedia")
    return status

@app.post(
    "/predict",
    tags=["Prediction"],
    response_model=PredictionResponse,
    summary="Prediksi Tren 7 Hari",
    description="Memprediksi tren dan mengembalikan top 3 hari terbaik untuk posting.",
    responses={
        200: {"description": "Prediksi berhasil", "model": PredictionResponse},
        400: {"description": "Input tidak valid", "model": ErrorResponse},
        422: {"description": "Preprocessing gagal", "model": ErrorResponse},
        429: {"description": "Rate limit exceeded"},
        500: {"description": "Inference gagal", "model": ErrorResponse},
        502: {"description": "Fetch data gagal", "model": ErrorResponse},
        503: {"description": "Model tidak tersedia", "model": ErrorResponse}
    }
)
@limiter.limit("10/minute")
def predict_trend(request: Request, payload: PredictionRequest):
    total_start = time.time()
    
    if inference_engine is None:
        raise HTTPException(status_code=503, detail="Model tidak tersedia")

    input_data = []
    source = "manual"
    fetch_time = None
    cached = False

    # Manual mode
    if payload.data:
        logger.info("Using manual data")
        input_data = payload.data
        source = "manual"

    # Auto mode
    elif payload.keyword:
        if apify_service is None:
            raise HTTPException(status_code=503, detail="Apify tidak tersedia")
            
        logger.info(f"Fetching: {payload.keyword}")
        fetch_start = time.time()
        
        # Check cache
        with apify_service._cache_lock:
            cached = payload.keyword in apify_service._cache
        
        try:
            input_data = apify_service.fetch_last_14_days(payload.keyword)
            source = "apify"
            fetch_time = (time.time() - fetch_start) * 1000
        except ApifyServiceError as e:
            raise HTTPException(status_code=502, detail=str(e))
    else:
        raise HTTPException(status_code=400, detail="Harus kirim 'keyword' atau 'data'")

    # Run inference
    inference_start = time.time()
    try:
        result = inference_engine.predict(input_data)
    except (PreprocessingError, InferenceError) as e:
        raise
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        raise HTTPException(status_code=500, detail=str(e))
    
    inference_time = (time.time() - inference_start) * 1000
    
    # Generate rankings
    forecast = result["forecast_values"]
    today = datetime.now()
    
    days_info = []
    day_names = ["Senin", "Selasa", "Rabu", "Kamis", "Jumat", "Sabtu", "Minggu"]
    
    for i, value in enumerate(forecast):
        future_date = today + timedelta(days=i+1)
        days_info.append({
            "day_index": i + 1,
            "date": future_date.strftime("%Y-%m-%d"),
            "day_name": day_names[future_date.weekday()],
            "interest_value": round(value, 1)
        })
    
    sorted_days = sorted(days_info, key=lambda x: x["interest_value"], reverse=True)
    
    max_val = max(forecast)
    top_3 = []
    for rank, day in enumerate(sorted_days[:3], 1):
        confidence = round((day["interest_value"] / max_val) * 100, 1)
        top_3.append({
            "rank": rank,
            "date": day["date"],
            "day_name": day["day_name"],
            "interest_value": day["interest_value"],
            "confidence": f"{confidence}%"
        })
    
    total_time = (time.time() - total_start) * 1000
    
    # Build clean response
    response = {
        "status": "success",
        "best_days": top_3,
        "performance": {
            "fetch_time_ms": round(fetch_time, 2) if fetch_time else None,
            "inference_time_ms": round(inference_time, 2),
            "total_time_ms": round(total_time, 2)
        },
        "meta": {
            "source": source,
            "keyword": payload.keyword,
            "category": payload.category,
            "input_length": len(input_data),
            "cached": cached
        }
    }
    
    return response

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

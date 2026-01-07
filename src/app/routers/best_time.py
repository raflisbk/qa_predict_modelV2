
from fastapi import APIRouter, HTTPException, Request, BackgroundTasks
from pydantic import BaseModel, Field, validator
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
from enum import Enum
from cachetools import TTLCache
import logging
import sys
import os
import traceback
import pandas as pd
import numpy as np
import joblib
import json
import threading
from sqlalchemy import text

# Add paths
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../..'))
from src.database.db_manager import SessionLocal, engine

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/api/v1/best-time",
    tags=["Best Time Prediction"]
)

# --- Enums ---
class CategoryEnum(str, Enum):
    ECOMMERCE = "E-commerce & Shopping"
    EDUCATION = "Education & Career"
    ENTERTAINMENT = "Entertainment"
    FASHION = "Fashion & Beauty"
    FINANCE = "Finance & Investment"
    FOOD = "Food & Culinary"
    GAMING = "Gaming & Esports"
    HEALTH = "Health & Fitness"
    TECHNOLOGY = "Technology & Gadgets"
    TRAVEL = "Travel & Tourism"

# --- Pydantic Models ---
class BestTimeRequest(BaseModel):
    category: str = Field(
        ..., 
        description="Category name (e.g., 'Food & Culinary')", 
        example="Food & Culinary"
    )
    window_hours: Optional[int] = Field(
        3, 
        description="Duration of posting window in hours", 
        ge=1, 
        le=12,
        example=3
    )
    top_k: Optional[int] = Field(
        3,
        description="Number of best windows to return",
        ge=1,
        le=10,
        example=3
    )
    days_ahead: Optional[int] = Field(
        7,
        description="Number of days to predict ahead",
        ge=1,
        le=14,
        example=7
    )
    
    @validator('category')
    def validate_category(cls, v):
        valid_categories = [e.value for e in CategoryEnum]
        if v not in valid_categories:
            raise ValueError(
                f"Invalid category. Must be one of: {', '.join(valid_categories)}"
            )
        return v

class WindowRecommendation(BaseModel):
    rank: int = Field(..., description="Rank (1 = best)", example=1)
    day_name: str = Field(..., description="Day of week", example="Thursday")
    date: str = Field(..., description="Date (YYYY-MM-DD format)", example="2026-01-09")
    time_window: str = Field(..., description="Time window", example="16:00 - 19:00")
    start_datetime: str = Field(..., description="ISO start datetime", example="2026-01-09T16:00:00")
    end_datetime: str = Field(..., description="ISO end datetime", example="2026-01-09T19:00:00")
    confidence_score: float = Field(..., description="Confidence (0.0-1.0)", example=0.853)

class BestTimeResponse(BaseModel):
    status: str = Field(default="success", example="success")
    category: str = Field(..., example="Food & Culinary")
    recommendations: List[WindowRecommendation] = Field(..., description="Top K best posting windows")
    prediction_window: Dict[str, str] = Field(
        ..., 
        description="Date range for predictions",
        example={"start": "2026-01-07", "end": "2026-01-13"}
    )
    model_info: Dict[str, Any] = Field(
        ...,
        description="Model metadata",
        example={
            "model_type": "LightGBM Regression",
            "version": "1.0",
            "mae": 2.54,
            "r2": 0.9740
        }
    )
    generated_at: datetime = Field(default_factory=datetime.now)
    
    class Config:
        protected_namespaces = ()

class HealthResponse(BaseModel):
    status: str = Field(..., example="healthy")
    model_loaded: bool = Field(..., description="LightGBM model status")
    database_connected: bool = Field(..., description="Apify client ready status")  # Repurposed
    categories_available: int = Field(..., description="Number of available categories")
    model_info: Optional[Dict[str, Any]] = None
    
    class Config:
        protected_namespaces = ()

class ErrorResponse(BaseModel):
    status: str = Field(default="error")
    error_code: str = Field(..., example="MODEL_NOT_LOADED")
    message: str = Field(..., example="Model file not found")
    detail: Optional[str] = None
    timestamp: datetime = Field(default_factory=datetime.now)

# --- Global State ---
class BestTimePredictor:
    def __init__(self):
        self.model = None
        self.feature_cols = None
        self.category_mapping = None
        self.model_metrics = None
        self.category_keywords = None  # Category -> Keywords mapping
        self.db_engine = engine  # Database connection
        
        # Cache configuration (TTL = 10 minutes)
        self.cache = TTLCache(maxsize=100, ttl=600)  # 10 min cache
        self.cache_lock = threading.Lock()
        
        self.model_path = os.path.join("models", "best_time", "lightgbm", "lgb_regression_model.pkl")
        self.feature_path = os.path.join("models", "best_time", "lightgbm", "feature_columns.pkl")
        self.category_path = os.path.join("models", "best_time", "lightgbm", "category_mapping.csv")
        self.metrics_path = os.path.join("models", "best_time", "lightgbm", "model_metrics.json")
        self.categories_config_path = os.path.join("config", "categories.json")
    
    def load_categories_config(self):
        """Load categories.json to map category -> keywords"""
        try:
            if not os.path.exists(self.categories_config_path):
                logger.warning(f"Categories config not found: {self.categories_config_path}")
                self.category_keywords = {}
                return False
            
            with open(self.categories_config_path, 'r') as f:
                config = json.load(f)
            
            # Build category -> keywords mapping
            self.category_keywords = {}
            for cat in config.get('categories', []):
                self.category_keywords[cat['name']] = cat['keywords']
            
            logger.info(f"[OK] Categories config loaded: {len(self.category_keywords)} categories")
            return True
            
        except Exception as e:
            logger.error(f"Failed to load categories config: {e}")
            self.category_keywords = {}
            return False
    
    def init_db_connection(self):
        """Test database connection"""
        try:
            with self.db_engine.connect() as conn:
                result = conn.execute(text("SELECT 1"))
                logger.info("[OK] Database connection established")
            return True
            
        except Exception as e:
            logger.error(f"Failed to connect to database: {e}")
            return False
        
    def load_model(self):
        """Load LightGBM model and artifacts"""
        try:
            logger.info("Loading LightGBM model...")
            
            # Load model
            if not os.path.exists(self.model_path):
                raise FileNotFoundError(f"Model not found: {self.model_path}")
            self.model = joblib.load(self.model_path)
            logger.info(f"[OK] Model loaded: {self.model_path}")
            
            # Load feature columns
            if not os.path.exists(self.feature_path):
                raise FileNotFoundError(f"Feature columns not found: {self.feature_path}")
            self.feature_cols = joblib.load(self.feature_path)
            logger.info(f"[OK] Feature columns loaded: {len(self.feature_cols)} features")
            
            # Load category mapping
            if not os.path.exists(self.category_path):
                raise FileNotFoundError(f"Category mapping not found: {self.category_path}")
            self.category_mapping = pd.read_csv(self.category_path)
            logger.info(f"[OK] Category mapping loaded: {len(self.category_mapping)} categories")
            
            # Load metrics
            if os.path.exists(self.metrics_path):
                import json
                with open(self.metrics_path, 'r') as f:
                    self.model_metrics = json.load(f)
                logger.info("[OK] Model metrics loaded")
            
            # Load categories config (for keywords mapping)
            self.load_categories_config()
            
            # Initialize database connection
            self.init_db_connection()
            
            logger.info("Model initialization complete!")
            return True
            
        except Exception as e:
            logger.error(f"Failed to load model: {e}")
            logger.error(traceback.format_exc())
            return False
    
    def get_latest_data(self, category: str, hours: int = 24):
        """Fetch latest hourly data from database (with caching)"""
        try:
            # Check cache first
            cache_key = f"db_data_{category}_{hours}"
            with self.cache_lock:
                if cache_key in self.cache:
                    logger.info(f"[CACHE] HIT for category '{category}'")
                    return self.cache[cache_key]
            
            logger.info(f"[CACHE] MISS for category '{category}' - querying database...")
            
            # Get keywords for category
            if category not in self.category_keywords:
                raise ValueError(f"Category not found in config: {category}")
            
            keywords = self.category_keywords[category]
            logger.info(f"[DB] Querying category '{category}' (keywords: {', '.join(keywords[:3])}{'...' if len(keywords) > 3 else ''})")
            
            # Query from database (last 48 hours for safety)
            # Get more than needed to ensure we have enough after aggregation
            query = text("""
                SELECT 
                    datetime,
                    EXTRACT(HOUR FROM datetime) as hour,
                    TO_CHAR(datetime, 'Day') as day_of_week,
                    CASE WHEN EXTRACT(DOW FROM datetime) IN (0, 6) THEN true ELSE false END as is_weekend,
                    AVG(interest_value) as interest_value
                FROM hourly_trends
                WHERE category = :category
                    AND datetime >= NOW() - INTERVAL '48 hours'
                GROUP BY datetime
                ORDER BY datetime DESC
                LIMIT :limit
            """)
            
            with self.db_engine.connect() as conn:
                result = conn.execute(query, {"category": category, "limit": hours * 2})
                rows = result.fetchall()
            
            if not rows:
                raise ValueError(f"No data found in database for category: {category}")
            
            # Convert to DataFrame
            df_agg = pd.DataFrame(rows, columns=['datetime', 'hour', 'day_of_week', 'is_weekend', 'interest_value'])
            
            # Keep only last N hours
            df_agg = df_agg.head(hours)
            
            logger.info(f"[DB] Retrieved {len(df_agg)} hourly data points from database")
            
            # Store in cache
            with self.cache_lock:
                self.cache[cache_key] = df_agg
                logger.info(f"[CACHE] Stored data for category '{category}' (TTL: 10 min)")
            
            return df_agg
            
        except Exception as e:
            logger.error(f"Database fetch error: {e}")
            logger.error(traceback.format_exc())
            raise
    
    def predict_best_windows(
        self, 
        category: str, 
        window_hours: int = 3, 
        top_k: int = 3, 
        days_ahead: int = 7
    ):
        """
        Predict best posting windows for category in next N days
        (Exact implementation from notebook)
        """
        try:
            # Validate model loaded
            if self.model is None:
                raise RuntimeError("Model not loaded. Call load_model() first.")
            
            # Get category encoding
            cat_row = self.category_mapping[self.category_mapping['category'] == category]
            if cat_row.empty:
                raise ValueError(f"Category not found: {category}")
            category_encoded = cat_row['category_encoded'].iloc[0]
            
            # Get latest data for lag/rolling features
            latest_data = self.get_latest_data(category, hours=24)
            
            # Calculate lag/rolling features from latest data
            latest_features = self._calculate_latest_features(latest_data)
            
            # Starting from tomorrow
            start_dt = datetime.now() + timedelta(days=1)
            start_dt = start_dt.replace(hour=0, minute=0, second=0, microsecond=0)
            
            # Create features for next N days
            future_hours = []
            all_datetimes = []
            
            for day_offset in range(days_ahead):
                current_dt = start_dt + timedelta(days=day_offset)
                is_weekend = current_dt.weekday() >= 5
                
                for hour in range(24):
                    hour_dt = current_dt + timedelta(hours=hour)
                    
                    features = {
                        'hour': hour,
                        'day_of_week_num': current_dt.weekday(),
                        'day_of_month': current_dt.day,
                        'is_weekend': int(is_weekend),
                        'is_night': int(0 <= hour <= 5),
                        'is_morning': int(6 <= hour <= 11),
                        'is_afternoon': int(12 <= hour <= 17),
                        'is_evening': int(18 <= hour <= 23),
                        'is_peak_morning': int(7 <= hour <= 9),
                        'is_peak_lunch': int(12 <= hour <= 13),
                        'is_peak_evening': int(19 <= hour <= 21),
                        'category_encoded': category_encoded
                    }
                    
                    # Add lag/rolling features from latest data
                    features.update(latest_features)
                    
                    future_hours.append(features)
                    all_datetimes.append(hour_dt)
            
            # Create DataFrame
            X_future = pd.DataFrame(future_hours)
            
            # Ensure all feature columns exist
            for col in self.feature_cols:
                if col not in X_future.columns:
                    X_future[col] = 0
            
            X_future = X_future[self.feature_cols]
            
            # Predict
            predictions = self.model.predict(X_future)
            predictions = np.clip(predictions, 0, 100)
            
            # Calculate window scores
            total_hours = days_ahead * 24
            windows = []
            
            for start_idx in range(total_hours - window_hours + 1):
                end_idx = start_idx + window_hours
                window_interest = predictions[start_idx:end_idx]
                
                avg_interest = window_interest.mean()
                std_interest = window_interest.std()
                
                # Confidence calculation (from notebook)
                base_confidence = 0.85
                interest_strength = 0.6 + (avg_interest / 100) * 0.4
                stability_factor = 1.0 - min(std_interest / 30, 0.25)
                model_error_factor = 1.0 - (2.54 / 100)
                
                confidence = base_confidence * interest_strength * stability_factor * model_error_factor
                confidence = max(0.50, min(0.90, confidence))
                
                # Get datetime
                window_start_dt = all_datetimes[start_idx]
                window_end_dt = all_datetimes[end_idx - 1] + timedelta(hours=1)
                
                windows.append({
                    'category': category,
                    'day_name': window_start_dt.strftime('%A'),
                    'date': window_start_dt.strftime('%Y-%m-%d'),
                    'time_window': f"{window_start_dt.strftime('%H:%M')} - {window_end_dt.strftime('%H:%M')}",
                    'start_datetime': window_start_dt.isoformat(),
                    'end_datetime': window_end_dt.isoformat(),
                    'avg_interest': round(avg_interest, 2),
                    'confidence_score': round(confidence, 3)
                })
            
            # Sort by avg_interest
            windows_sorted = sorted(windows, key=lambda x: x['avg_interest'], reverse=True)
            
            # Filter non-overlapping windows
            selected_windows = []
            for window in windows_sorted:
                is_overlapping = False
                window_start = datetime.fromisoformat(window['start_datetime'])
                window_end = datetime.fromisoformat(window['end_datetime'])
                
                for selected in selected_windows:
                    selected_start = datetime.fromisoformat(selected['start_datetime'])
                    selected_end = datetime.fromisoformat(selected['end_datetime'])
                    
                    if not (window_end <= selected_start or window_start >= selected_end):
                        is_overlapping = True
                        break
                
                if not is_overlapping:
                    selected_windows.append(window)
                    
                if len(selected_windows) >= top_k:
                    break
            
            return selected_windows
            
        except Exception as e:
            logger.error(f"Prediction error: {e}")
            logger.error(traceback.format_exc())
            raise
    
    def _calculate_latest_features(self, df: pd.DataFrame) -> Dict:
        """Calculate lag and rolling features from latest data"""
        # Simple approximation: use last value for lag features
        # In production, calculate properly from time series
        latest_interest = df['interest_value'].iloc[0] if not df.empty else 50.0
        
        features = {}
        # Lag features
        for lag in [1, 2, 3, 6, 12, 24]:
            features[f'interest_lag_{lag}h'] = latest_interest
        
        # Rolling features
        for window in [3, 6, 12, 24]:
            features[f'interest_rolling_mean_{window}h'] = latest_interest
            features[f'interest_rolling_std_{window}h'] = 5.0  # Default std
            features[f'interest_rolling_max_{window}h'] = latest_interest + 10
        
        return features

# Global predictor instance
predictor = BestTimePredictor()

# --- Startup Event ---
@router.on_event("startup")
async def startup():
    """Load model on startup and pre-warm cache"""
    logger.info("Initializing Best Time Predictor...")
    success = predictor.load_model()
    if not success:
        logger.warning("Model failed to load. API will return 503 errors.")
        return

# --- Endpoints ---
@router.get(
    "/health",
    response_model=HealthResponse,
    responses={
        200: {"description": "Service healthy"},
        503: {"description": "Service unavailable", "model": ErrorResponse}
    },
    summary="Health Check",
    description="Check API health status and model availability"
)
async def health_check():
    """Health check endpoint"""
    try:
        # Check model
        model_loaded = predictor.model is not None
        
        # Check database connection
        db_connected = False
        try:
            with predictor.db_engine.connect() as conn:
                conn.execute(text("SELECT 1"))
                db_connected = True
        except:
            pass
        
        # Check categories config
        categories_count = len(predictor.category_mapping) if predictor.category_mapping is not None else 0
        
        # Model info
        model_info = None
        if predictor.model_metrics:
            model_info = {
                "model_type": predictor.model_metrics.get("model_type"),
                "version": predictor.model_metrics.get("model_version"),
                "mae": predictor.model_metrics.get("performance", {}).get("mae"),
                "r2": predictor.model_metrics.get("performance", {}).get("r2")
            }
        
        if not model_loaded:
            raise HTTPException(
                status_code=503,
                detail="Model not loaded"
            )
        
        return HealthResponse(
            status="healthy",
            model_loaded=model_loaded,
            database_connected=db_connected,
            categories_available=categories_count,
            model_info=model_info
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        raise HTTPException(status_code=503, detail=str(e))

@router.post(
    "/predict",
    response_model=BestTimeResponse,
    responses={
        200: {"description": "Prediction successful"},
        400: {"description": "Invalid request", "model": ErrorResponse},
        404: {"description": "Category not found", "model": ErrorResponse},
        500: {"description": "Internal error", "model": ErrorResponse},
        503: {"description": "Service unavailable", "model": ErrorResponse}
    },
    summary="Predict Best Posting Times",
    description="Get top K best posting time windows for next N days (with caching & background pre-fetch)"
)
async def predict_best_time(request: BestTimeRequest, background_tasks: BackgroundTasks):
    """
    Predict best posting times for a category.
    
    Returns top K non-overlapping time windows across next N days,
    ranked by predicted interest with confidence scores.
    """
    try:
        logger.info(f"Prediction request: category={request.category}, "
                   f"window_hours={request.window_hours}, top_k={request.top_k}")
        
        # Validate model loaded
        if predictor.model is None:
            raise HTTPException(
                status_code=503,
                detail="Model not available. Service is initializing or failed to load."
            )
        
        # Check if data is cached (before prediction)
        cache_key = f"apify_data_{request.category}_24"
        was_cached = False
        with predictor.cache_lock:
            was_cached = cache_key in predictor.cache
        
        # Predict (will use cache if available)
        windows = predictor.predict_best_windows(
            category=request.category,
            window_hours=request.window_hours,
            top_k=request.top_k,
            days_ahead=request.days_ahead
        )
        
        if not windows:
            raise HTTPException(
                status_code=404,
                detail=f"No predictions generated for category: {request.category}"
            )
        
        # Format response
        recommendations = [
            WindowRecommendation(
                rank=idx + 1,
                day_name=w['day_name'],
                date=w['date'],
                time_window=w['time_window'],
                start_datetime=w['start_datetime'],
                end_datetime=w['end_datetime'],
                confidence_score=w['confidence_score']
            )
            for idx, w in enumerate(windows)
        ]
        
        # Prediction window
        start_date = (datetime.now() + timedelta(days=1)).strftime('%Y-%m-%d')
        end_date = (datetime.now() + timedelta(days=request.days_ahead)).strftime('%Y-%m-%d')
        
        # Model info
        model_info = {
            "model_type": "LightGBM Regression",
            "version": "1.0",
            "cached": was_cached,
            "cache_ttl_seconds": 600
        }
        if predictor.model_metrics:
            model_info.update({
                "mae": predictor.model_metrics.get("performance", {}).get("mae"),
                "r2": predictor.model_metrics.get("performance", {}).get("r2"),
                "trained_at": predictor.model_metrics.get("trained_at")
            })
        
        return BestTimeResponse(
            status="success",
            category=request.category,
            recommendations=recommendations,
            prediction_window={"start": start_date, "end": end_date},
            model_info=model_info
        )
        
    except HTTPException:
        raise
    except ValueError as e:
        logger.error(f"Validation error: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Prediction failed: {e}")
        logger.error(traceback.format_exc())
        raise HTTPException(
            status_code=500,
            detail=f"Internal server error: {str(e)}"
        )

@router.get(
    "/categories",
    response_model=Dict[str, List[str]],
    summary="List Available Categories",
    description="Get list of all available categories for prediction"
)
async def list_categories():
    """List all available categories"""
    try:
        if predictor.category_mapping is None:
            raise HTTPException(status_code=503, detail="Model not loaded")
        
        categories = predictor.category_mapping['category'].tolist()
        return {"categories": categories}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to list categories: {e}")
        raise HTTPException(status_code=500, detail=str(e))

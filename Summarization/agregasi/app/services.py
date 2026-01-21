import json
import logging
import re
import time
from datetime import datetime, timedelta
from typing import Dict, List, Tuple, Any, Optional

import pandas as pd
import pytz
from pytrends.request import TrendReq
from apify_client import ApifyClient
from fastapi import BackgroundTasks, HTTPException
from redis import Redis, ConnectionPool, RedisError, ConnectionError as RedisConnectionError
from tenacity import retry, stop_after_attempt, wait_fixed, retry_if_exception_type

from app.config import settings

# logging
logging.basicConfig(
    level=logging.INFO,
    format='{"time": "%(asctime)s", "level": "%(levelname)s", "message": "%(message)s"}'
)
logger = logging.getLogger(__name__)


apify_client = ApifyClient(settings.APIFY_TOKEN)

# redis connection pool
redis_pool = ConnectionPool(
    host=settings.REDIS_HOST,
    port=settings.REDIS_PORT,
    db=0,
    decode_responses=True,
    max_connections=50,
    socket_connect_timeout=5,
    socket_timeout=5,
    retry_on_timeout=True
)

redis_client = Redis(connection_pool=redis_pool)


class DataNotFoundException(Exception):
    """Custom exception for when no data is returned from Apify."""
    pass


class RedisUnavailableException(Exception):
    """Custom exception for when Redis is unavailable."""
    pass


class DataValidationException(Exception):
    """Custom exception for data validation errors."""
    pass


class PyTrendsUnavailableException(Exception):
    """Custom exception for when pytrends fails (rate limit, timeout, etc)."""
    pass


@retry(
    retry=retry_if_exception_type((RedisError, RedisConnectionError)),
    stop=stop_after_attempt(3),
    wait=wait_fixed(1),
    reraise=True
)
def redis_get_with_retry(key: str) -> Optional[str]:
    """Get value from Redis with retry logic."""
    try:
        return redis_client.get(key)
    except (RedisError, RedisConnectionError) as e:
        logger.error(f"Redis GET error for key {key}: {str(e)}")
        raise


@retry(
    retry=retry_if_exception_type((RedisError, RedisConnectionError)),
    stop=stop_after_attempt(3),
    wait=wait_fixed(1),
    reraise=True
)
def redis_set_with_retry(key: str, value: str, ex: Optional[int] = None, nx: bool = False) -> bool:
    """Set value in Redis with retry logic."""
    try:
        if nx:
            return redis_client.set(key, value, ex=ex, nx=nx)
        else:
            if ex:
                return redis_client.setex(key, ex, value)
            else:
                return redis_client.set(key, value)
    except (RedisError, RedisConnectionError) as e:
        logger.error(f"Redis SET error for key {key}: {str(e)}")
        raise


@retry(
    retry=retry_if_exception_type((RedisError, RedisConnectionError)),
    stop=stop_after_attempt(3),
    wait=wait_fixed(1),
    reraise=True
)
def redis_incr_with_retry(key: str) -> int:
    """Increment value in Redis with retry logic."""
    try:
        return redis_client.incr(key)
    except (RedisError, RedisConnectionError) as e:
        logger.error(f"Redis INCR error for key {key}: {str(e)}")
        raise


@retry(
    retry=retry_if_exception_type((RedisError, RedisConnectionError)),
    stop=stop_after_attempt(3),
    wait=wait_fixed(1),
    reraise=True
)
def redis_expire_with_retry(key: str, seconds: int) -> bool:
    """Set expiration on Redis key with retry logic."""
    try:
        return redis_client.expire(key, seconds)
    except (RedisError, RedisConnectionError) as e:
        logger.error(f"Redis EXPIRE error for key {key}: {str(e)}")
        raise


@retry(
    retry=retry_if_exception_type((RedisError, RedisConnectionError)),
    stop=stop_after_attempt(3),
    wait=wait_fixed(1),
    reraise=True
)
def redis_delete_with_retry(key: str) -> int:
    """Delete key from Redis with retry logic."""
    try:
        return redis_client.delete(key)
    except (RedisError, RedisConnectionError) as e:
        logger.error(f"Redis DELETE error for key {key}: {str(e)}")
        raise


def normalize_keyword(raw: str) -> str:
    """
    Normalize keyword by converting to lowercase and removing special characters.
    Spaces are replaced with underscores for Redis key compatibility.
    
    Args:
        raw: Raw keyword input
        
    Returns:
        Normalized keyword string with underscores instead of spaces
    """
    keyword = raw.lower()
    keyword = re.sub(r'[^a-z0-9\s]', ' ', keyword)
    keyword = re.sub(r'\s+', '_', keyword)
    return keyword.strip('_')


@retry(stop=stop_after_attempt(2), wait=wait_fixed(3), reraise=True)
def fetch_from_pytrends(keyword: str) -> Tuple[List[Dict[str, Any]], Dict[str, Any]]:
    """
    Fetch Google Trends data from pytrends (fast unofficial API).
    
    Args:
        keyword: Search term to fetch trends for
        
    Returns:
        Tuple of (timeline_data, stats)
        
    Raises:
        PyTrendsUnavailableException: If pytrends fails (rate limit, timeout, error)
    """
    logger.info(f"Fetching data from pytrends for keyword: {keyword}")
    start_time = time.time()
    
    try:
        # Initialize pytrends
        pytrend = TrendReq(hl='id-ID', tz=420, timeout=(5, 10))  # Jakarta timezone offset
        
        # Build payload (last 7 days, Indonesia)
        pytrend.build_payload(
            kw_list=[keyword],
            timeframe='now 7-d',
            geo='ID'
        )
        
        # Get hourly interest over time
        df = pytrend.interest_over_time()
        
        # Validate data
        if df is None or df.empty:
            logger.warning(f"Pytrends returned empty data for keyword: {keyword}")
            raise PyTrendsUnavailableException("No data returned from pytrends")
        
        # Check if keyword column exists
        if keyword not in df.columns:
            logger.warning(f"Keyword '{keyword}' not found in pytrends columns: {df.columns.tolist()}")
            raise PyTrendsUnavailableException(f"Keyword not found in results")
        
        # Convert to timeline format
        timeline_data = []
        for timestamp, row in df.iterrows():
            # timestamp is already a pandas Timestamp (UTC)
            timeline_data.append({
                "date": timestamp.isoformat(),  # Will be converted to Jakarta timezone later
                "value": int(row[keyword])
            })
        
        # Stats
        duration_ms = int((time.time() - start_time) * 1000)
        stats = {
            "duration_ms": duration_ms,
            "compute_units": 0.0,  # Pytrends doesn't charge
            "source": "pytrends"
        }
        
        logger.info(f"Successfully fetched {len(timeline_data)} data points from pytrends in {duration_ms}ms")
        return timeline_data, stats
        
    except Exception as e:
        # Any error with pytrends = fallback to Apify
        logger.warning(f"Pytrends failed for keyword '{keyword}': {str(e)}")
        raise PyTrendsUnavailableException(f"Pytrends unavailable: {str(e)}")


@retry(stop=stop_after_attempt(3), wait=wait_fixed(2), reraise=True)
def fetch_from_apify(keyword: str) -> Tuple[List[Dict[str, Any]], Dict[str, Any]]:
    """
    Fetch Google Trends data from Apify with retry logic.
    
    Args:
        keyword: Search term to fetch trends for
        
    Returns:
        Tuple of (timeline_data, stats)
        
    Raises:
        DataNotFoundException: If no timeline data is returned
    """
    logger.info(f"Fetching data from Apify for keyword: {keyword}")
    
    run = apify_client.actor("apify/google-trends-scraper").call(
        run_input={
            "searchTerms": [keyword],
            "timeRange": "now 7-d",
            "geo": "ID",
            # Optimizations that DON'T sacrifice data quality
            "isPublic": False,  # Private dataset (no impact on data quality)
            # Note: isMultiTimelineSourcesRequired removed - let Apify decide
            # Note: maxItems removed - need all data for accurate aggregation
        },
        # Runtime config - optimized for viral keywords
        memory_mbytes=4096,  # High memory for large datasets (viral keywords)
        timeout_secs=600,  # 10 minutes - handle slow fetches for popular keywords
    )
    
    # Extract dataset items
    dataset_items = list(apify_client.dataset(run["defaultDatasetId"]).iterate_items())
    
    # Extract timeline data (Apify uses 'interestOverTime_timelineData' key)
    timeline_data = []
    if dataset_items:
        for item in dataset_items:
            if "interestOverTime_timelineData" in item and item["interestOverTime_timelineData"]:
                # Apify returns data with structure: {"time": "unix_timestamp", "value": [int], ...}
                # Use Unix timestamp (always UTC) for accurate timezone conversion later
                for data_point in item["interestOverTime_timelineData"]:
                    # Convert Unix timestamp to ISO format datetime string
                    timestamp = int(data_point.get("time", 0))
                    if timestamp > 0:
                        # Convert to datetime (UTC)
                        from datetime import datetime
                        dt = datetime.utcfromtimestamp(timestamp)
                        timeline_data.append({
                            "date": dt.isoformat(),  # Will be converted to Jakarta timezone later
                            "value": data_point.get("value", [0])[0]  # Extract first value from array
                        })
    
    # Validate data
    if not timeline_data:
        logger.error(f"No timeline data returned for keyword: {keyword}")
        raise DataNotFoundException(f"No data found for keyword: {keyword}")
    
    # Extract stats
    stats = {
        "duration_ms": run.get("stats", {}).get("durationMillis", 0),
        "compute_units": run.get("stats", {}).get("computeUnits", 0.0)
    }
    
    logger.info(f"Successfully fetched {len(timeline_data)} data points from Apify")
    return timeline_data, stats


def process_data(timeline_data: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Process timeline data using pandas to generate recommendations and chart data.
    
    Args:
        timeline_data: List of timeline data points from Apify
        
    Returns:
        Dictionary containing recommendations and chart_data
        
    Raises:
        DataValidationException: If data validation fails
    """
    logger.info(f"Processing {len(timeline_data)} data points")
    
    # Validation 1: Check if data is not empty
    if not timeline_data or len(timeline_data) == 0:
        logger.error("Timeline data is empty")
        raise DataValidationException("No timeline data available to process")
    
    try:
        # Convert to DataFrame
        df = pd.DataFrame(timeline_data)
        
        # Validation 2: Check required columns exist
        required_columns = ['date', 'value']
        missing_columns = [col for col in required_columns if col not in df.columns]
        if missing_columns:
            logger.error(f"Missing required columns: {missing_columns}")
            raise DataValidationException(f"Missing required columns: {', '.join(missing_columns)}")
        
        # Validation 3: Check if DataFrame has data
        if df.empty:
            logger.error("DataFrame is empty after conversion")
            raise DataValidationException("No valid data after conversion to DataFrame")
        
        # Validation 4: Check minimum data points (at least 24 hours)
        if len(df) < 24:
            logger.warning(f"Only {len(df)} data points available, may affect accuracy")
        
        # Validation 5: Clean and validate data types
        # Remove rows with null values in critical columns
        df_clean = df.dropna(subset=['date', 'value'])
        if len(df_clean) < len(df):
            logger.warning(f"Dropped {len(df) - len(df_clean)} rows with null values")
        
        if df_clean.empty:
            logger.error("All rows contain null values")
            raise DataValidationException("No valid data after removing nulls")
        
        df = df_clean
        
        # Validation 6: Convert and validate date column
        try:
            df['date'] = pd.to_datetime(df['date'], errors='coerce')
            # Remove rows where date conversion failed
            df = df.dropna(subset=['date'])
            
            if df.empty:
                raise DataValidationException("No valid dates in data")
            
            # Check if dates have timezone info, if not assume UTC
            if df['date'].dt.tz is None:
                df['date'] = df['date'].dt.tz_localize('UTC')
            
            # Convert to Jakarta timezone
            df['date'] = df['date'].dt.tz_convert('Asia/Jakarta')
            
        except Exception as e:
            logger.error(f"Date conversion error: {str(e)}")
            raise DataValidationException(f"Failed to convert dates: {str(e)}")
        
        # Validation 7: Convert and validate value column
        try:
            df['value'] = pd.to_numeric(df['value'], errors='coerce')
            # Remove rows where value conversion failed or is negative
            df = df[df['value'].notna() & (df['value'] >= 0)]
            
            if df.empty:
                raise DataValidationException("No valid values in data")
                
        except Exception as e:
            logger.error(f"Value conversion error: {str(e)}")
            raise DataValidationException(f"Failed to convert values: {str(e)}")
        
        # Extract day name and hour
        df['day_name'] = df['date'].dt.day_name()
        df['hour'] = df['date'].dt.hour
        
        # Aggregate by day and hour
        grouped = df.groupby(['day_name', 'hour'])['value'].mean().reset_index()
        
        # Validation 8: Check if aggregation produced results
        if grouped.empty:
            logger.error("Aggregation produced no results")
            raise DataValidationException("No data after aggregation")
        
        # Calculate rolling score (3-hour window)
        grouped = grouped.sort_values(['day_name', 'hour'])
        grouped['rolling_score'] = grouped.groupby('day_name')['value'].transform(
            lambda x: x.rolling(window=3, min_periods=1).mean()
        )
        
        # Get top 3 recommendations
        top_recommendations = grouped.nlargest(3, 'rolling_score')
        
        recommendations = []
        for idx, row in enumerate(top_recommendations.itertuples(), start=1):
            # Create time window (3-hour window)
            start_hour = row.hour
            end_hour = (row.hour + 3) % 24
            time_window = f"{start_hour:02d}:00 - {end_hour:02d}:00"
            
            recommendations.append({
                "rank": idx,
                "day": row.day_name,
                "time_window": time_window,
                "score": round(row.rolling_score, 2)
            })
        
        # Prepare chart data (hourly breakdown) - use aggregated data for consistency
        chart_data = []
        for row in grouped.itertuples():
            chart_data.append({
                "day": row.day_name,
                "hour": f"{row.hour:02d}:00",
                "score": round(row.value, 2)
            })
        
        # Prepare hourly_summary for model summarization (traceback analysis)
        hourly_summary = []
        for idx, rec in enumerate(recommendations):
            day = rec["day"]
            start_hour = int(rec["time_window"].split(" - ")[0].replace(":00", ""))
            
            # Get hourly data for this day
            day_data = grouped[grouped['day_name'] == day].sort_values('hour')
            
            # Calculate daily average
            daily_avg = round(day_data['value'].mean(), 1)
            
            # Calculate window average (3-hour)
            window_hours = [(start_hour + i) % 24 for i in range(3)]
            window_data = day_data[day_data['hour'].isin(window_hours)]
            window_avg = round(window_data['value'].mean(), 1) if not window_data.empty else rec["score"]
            
            # Find peak hour within window
            if not window_data.empty:
                peak_row = window_data.loc[window_data['value'].idxmax()]
                peak_hour = int(peak_row['hour'])
                peak_value = round(peak_row['value'], 1)
            else:
                peak_hour = start_hour
                peak_value = rec["score"]
            
            # Create hourly breakdown string for model input
            hourly_str = ", ".join([
                f"{int(r.hour):02d}({round(r.value)})" 
                for r in day_data.itertuples()
            ])
            
            hourly_summary.append({
                "rank": rec["rank"],
                "day": day,
                "time_window": rec["time_window"],
                "score": rec["score"],
                "daily_avg": daily_avg,
                "window_avg": window_avg,
                "peak_hour": peak_hour,
                "peak_value": peak_value,
                "hourly": hourly_str
            })
        
        logger.info(f"Generated {len(recommendations)} recommendations and {len(chart_data)} chart points from {len(df)} raw data points")
        
        return {
            "recommendations": recommendations,
            "chart_data": chart_data,
            "hourly_summary": hourly_summary
        }
        
    except DataValidationException:
        # Re-raise our custom exceptions
        raise
    except Exception as e:
        # Catch any unexpected pandas/processing errors
        logger.error(f"Unexpected error during data processing: {str(e)}")
        raise DataValidationException(f"Data processing failed: {str(e)}")


def update_cache_background(keyword: str) -> None:
    """
    Background task to refresh stale cache data.
    Tries pytrends first, falls back to Apify.
    
    Args:
        keyword: Keyword to refresh cache for
    """
    try:
        normalized = normalize_keyword(keyword)
        logger.info(f"Background refresh started for keyword: {normalized}")
        
        # Try pytrends first (fast)
        try:
            timeline_data, stats = fetch_from_pytrends(keyword)
            processed = process_data(timeline_data)
            logger.info(f"Background refresh via pytrends for: {normalized}")
        except PyTrendsUnavailableException:
            # Fallback to Apify
            logger.info(f"Background refresh via Apify fallback for: {normalized}")
            timeline_data, stats = fetch_from_apify(keyword)
            processed = process_data(timeline_data)
        
        # Prepare cache entry
        cache_entry = {
            "timestamp": time.time(),
            "data": processed,
            "stats": stats
        }
        
        # Update cache
        cache_key = f"trend:{normalized}"
        try:
            redis_set_with_retry(cache_key, json.dumps(cache_entry), ex=88200)
            logger.info(f"Background refresh completed for keyword: {normalized}")
        except (RedisError, RedisConnectionError) as e:
            logger.error(f"Failed to update cache for {normalized}: {str(e)}")
    except Exception as e:
        logger.error(f"Background refresh failed for keyword {keyword}: {str(e)}")


def get_prediction(keyword: str) -> Tuple[Dict[str, Any], str, Optional[Dict[str, Any]]]:
    """
    Get prediction data directly (used by async jobs).
    Checks cache first, tries pytrends (fast), falls back to Apify if needed.
    
    Args:
        keyword: Search keyword
        
    Returns:
        Tuple of (processed_data, source, stats)
        
    Raises:
        DataNotFoundException: If no data available
        DataValidationException: If data validation fails
    """
    normalized = normalize_keyword(keyword)
    logger.info(f"Getting prediction for keyword: {normalized}")
    
    # Check cache first
    cache_key = f"trend:{normalized}"
    
    try:
        cached = redis_get_with_retry(cache_key)
        
        if cached:
            cache_data = json.loads(cached)
            timestamp = cache_data.get("timestamp", 0)
            age = time.time() - timestamp
            
            # Cache is fresh (< 24 hours)
            if age < 86400:
                logger.info(f"Cache hit for keyword: {normalized}")
                return cache_data["data"], "cache", cache_data.get("stats")
    except (RedisError, RedisConnectionError) as e:
        logger.warning(f"Redis error during cache check: {str(e)}")
    except json.JSONDecodeError as e:
        logger.warning(f"Invalid JSON in cache for {normalized}: {str(e)}")
    
    # Cache miss - try pytrends first (fast)
    logger.info(f"Cache miss, trying pytrends first for: {normalized}")
    source = "apify"  # Default
    
    try:
        timeline_data, stats = fetch_from_pytrends(keyword)
        processed = process_data(timeline_data)
        source = "pytrends"
        logger.info(f"✅ Pytrends succeeded for: {normalized}")
        
    except PyTrendsUnavailableException as e:
        # Pytrends failed - fallback to Apify
        logger.warning(f"Pytrends failed, falling back to Apify for: {normalized}")
        timeline_data, stats = fetch_from_apify(keyword)
        processed = process_data(timeline_data)
        source = "apify"
        logger.info(f"✅ Apify fallback succeeded for: {normalized}")
    
    # Save to cache
    cache_entry = {
        "timestamp": time.time(),
        "data": processed,
        "stats": stats
    }
    
    try:
        redis_set_with_retry(cache_key, json.dumps(cache_entry), ex=88200)
        logger.info(f"Data cached for: {normalized}")
    except (RedisError, RedisConnectionError) as e:
        logger.warning(f"Failed to cache data for {normalized}: {str(e)}")
    
    return processed, source, stats



def get_prediction_swr(
    keyword: str,
    background_tasks: BackgroundTasks
) -> Tuple[Dict[str, Any], str, Optional[Dict[str, Any]]]:
    """
    Get prediction data using Stale-While-Revalidate pattern.
    
    Args:
        keyword: Search keyword
        background_tasks: FastAPI background tasks
        
    Returns:
        Tuple of (processed_data, source, stats)
        
    Raises:
        HTTPException: For rate limiting or service unavailability
    """
    normalized = normalize_keyword(keyword)
    logger.info(f"Processing request for keyword: {normalized}")
    
    # Step 1: Circuit Breaker - Global Rate Limit
    date_str = datetime.now().strftime("%Y-%m-%d")
    usage_key = f"usage:global:{date_str}"
    
    try:
        current_usage = redis_get_with_retry(usage_key)
        current_usage = int(current_usage) if current_usage else 0
        
        if current_usage >= settings.GLOBAL_RATE_LIMIT:
            logger.warning(f"Global rate limit exceeded: {current_usage}/{settings.GLOBAL_RATE_LIMIT}")
            raise HTTPException(
                status_code=429,
                detail="Global rate limit exceeded. Please try again later."
            )
        
        # Increment usage counter
        redis_incr_with_retry(usage_key)
        redis_expire_with_retry(usage_key, 86400)  # 24 hours
    except (RedisError, RedisConnectionError) as e:
        logger.error(f"Redis unavailable for rate limiting: {str(e)}")
        # Continue without rate limiting if Redis is down (degraded mode)
    
    # Step 2: Check Cache
    cache_key = f"trend:{normalized}"
    
    try:
        cached = redis_get_with_retry(cache_key)
        
        if cached:
            cache_data = json.loads(cached)
            timestamp = cache_data.get("timestamp", 0)
            age = time.time() - timestamp
            
            # Cache is fresh (< 24 hours)
            if age < 86400:
                logger.info(f"Cache hit (fresh) for keyword: {normalized}")
                return cache_data["data"], "cache_fresh", cache_data.get("stats")
            
            # Cache is stale (> 24 hours) - treat as cache miss
            logger.info(f"Cache expired (> 24h) for keyword: {normalized}, treating as cache miss")
    except (RedisError, RedisConnectionError) as e:
        logger.error(f"Redis error during cache check: {str(e)}")
        # Continue to fetch from Apify if Redis is down
    except json.JSONDecodeError as e:
        logger.error(f"Invalid JSON in cache for {normalized}: {str(e)}")
        # Treat as cache miss if data is corrupted
    
    # Step 3: Cache Miss - Acquire Lock
    lock_key = f"lock:{normalized}"
    
    try:
        # Start with 60s lock - will extend before heavy operations
        lock_acquired = redis_set_with_retry(lock_key, "1", nx=True, ex=60)
    except (RedisError, RedisConnectionError) as e:
        logger.error(f"Redis error during lock acquisition: {str(e)}")
        # If Redis is down, proceed without locking (risky but better than total failure)
        lock_acquired = True
    
    if not lock_acquired:
        # Wait for lock holder to populate cache
        logger.info(f"Lock acquisition failed, waiting for cache: {normalized}")
        for attempt in range(10):
            time.sleep(0.5)
            try:
                cached = redis_get_with_retry(cache_key)
                if cached:
                    cache_data = json.loads(cached)
                    logger.info(f"Cache populated by lock holder for: {normalized}")
                    return cache_data["data"], "cache_fresh", cache_data.get("stats")
            except (RedisError, RedisConnectionError) as e:
                logger.warning(f"Redis error while waiting for cache: {str(e)}")
                continue
            except json.JSONDecodeError:
                continue
        
        # Timeout - service unavailable
        logger.error(f"Lock timeout for keyword: {normalized}")
        raise HTTPException(
            status_code=503,
            detail="Service temporarily unavailable. Please try again."
        )
    
    # Lock acquired - fetch and cache data
    try:
        logger.info(f"Lock acquired, fetching data for: {normalized}")
        
        # Try pytrends first (fast, 10-15s)
        source = "apify"  # Default
        
        try:
            logger.info(f"Trying pytrends for: {normalized}")
            timeline_data, stats = fetch_from_pytrends(keyword)
            processed = process_data(timeline_data)
            source = "pytrends"
            logger.info(f"✅ Pytrends succeeded for: {normalized}")
            
        except PyTrendsUnavailableException as e:
            # Pytrends failed - fallback to Apify
            logger.warning(f"Pytrends failed ({str(e)}), falling back to Apify for: {normalized}")
            
            # Extend lock to 120s before heavy Apify operation (dynamic extension)
            try:
                redis_expire_with_retry(lock_key, 120)
                logger.debug(f"Lock extended to 120s for Apify fetch: {normalized}")
            except (RedisError, RedisConnectionError) as e:
                logger.warning(f"Failed to extend lock, continuing with original TTL: {str(e)}")
            
            timeline_data, stats = fetch_from_apify(keyword)
            processed = process_data(timeline_data)
            source = "apify"
            logger.info(f"✅ Apify fallback succeeded for: {normalized}")
        
        # Prepare cache entry
        cache_entry = {
            "timestamp": time.time(),
            "data": processed,
            "stats": stats
        }
        
        # Save to Redis (TTL: 88200 seconds ≈ 24.5 hours)
        try:
            redis_set_with_retry(cache_key, json.dumps(cache_entry), ex=88200)
            logger.info(f"Data cached successfully for: {normalized}")
        except (RedisError, RedisConnectionError) as e:
            logger.error(f"Failed to save to cache for {normalized}: {str(e)}")
            # Continue and return data even if caching fails
        
        return processed, source, stats
        
    finally:
        # Always release lock
        try:
            redis_delete_with_retry(lock_key)
            logger.info(f"Lock released for: {normalized}")
        except (RedisError, RedisConnectionError) as e:
            logger.error(f"Failed to release lock for {normalized}: {str(e)}")

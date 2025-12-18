"""
Test fetch HOURLY data (1 week) dari Apify.

Usage:
    python test_fetch_hourly.py --keyword "shopee" --category "E-commerce & Shopping"
"""

import os
import sys
import uuid
import json
import argparse
from datetime import datetime, timezone, timedelta
from dotenv import load_dotenv
from loguru import logger
from apify_client import ApifyClient
from sqlalchemy import text

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
from src.database.db_manager import SessionLocal, test_connection

load_dotenv()


def fetch_from_apify(keyword, api_token):
    """Fetch hourly data (1 week) dari Apify"""
    client = ApifyClient(api_token)
    
    run_input = {
        "searchTerms": [keyword],
        "geo": "ID",
        "hl":"id",
        "timeRange": "now 7-d",  # 1 week untuk hourly data
        "category": "",
        "isPublic": False
    }
    
    logger.info(f"Running Apify actor for HOURLY data: {keyword}")
    logger.info(f"Time range: 1 week (now 7-d)")
    run = client.actor("apify/google-trends-scraper").call(run_input=run_input)
    
    results = []
    for item in client.dataset(run["defaultDatasetId"]).iterate_items():
        results.append(item)
    
    logger.success(f"Got {len(results)} results from Apify")
    return results


def parse_hourly_data(results, keyword, category):
    """Parse ONLY hourly data"""
    hourly_data = []
    
    # WIB timezone (UTC+7)
    wib_tz = timezone(timedelta(hours=7))
    
    for result in results:
        timeline_data = result.get("interestOverTime_timelineData", [])
        
        if not timeline_data:
            continue
        
        for point in timeline_data:
            timestamp_str = point.get("time")
            if not timestamp_str:
                continue
            
            try:
                timestamp = int(timestamp_str)
                dt_utc = datetime.fromtimestamp(timestamp, tz=timezone.utc)
                dt = dt_utc.astimezone(wib_tz)
            except:
                logger.warning(f"Failed to parse timestamp: {timestamp_str}")
                continue
            
            interest_value = point.get("value", [0])[0] if point.get("value") else 0
            
            # Only collect hourly data (non-midnight)
            if not (dt.hour == 0 and dt.minute == 0):
                hour = dt.hour
                if 0 <= hour < 6:
                    time_of_day = "night"
                elif 6 <= hour < 12:
                    time_of_day = "morning"
                elif 12 <= hour < 18:
                    time_of_day = "afternoon"
                else:
                    time_of_day = "evening"
                
                hourly_data.append({
                    "keyword": keyword,
                    "category": category,
                    "datetime": dt.replace(tzinfo=None),
                    "hour": dt.hour,
                    "day_of_week": dt.strftime("%A"),
                    "interest_value": interest_value,
                    "is_weekend": dt.weekday() >= 5,
                    "time_of_day": time_of_day,
                    "raw_data": point
                })
    
    logger.info(f"Parsed {len(hourly_data)} hourly points")
    return hourly_data


def save_hourly_to_database(hourly_data, test_run_id):
    """Save hourly data ke database"""
    session = SessionLocal()
    
    try:
        for record in hourly_data:
            query = text("""
                INSERT INTO test_hourly_trends (
                    keyword, category, region, datetime, hour, day_of_week,
                    interest_value, is_weekend, time_of_day, raw_data, test_run_id
                ) VALUES (
                    :keyword, :category, :region, :datetime, :hour, :day_of_week,
                    :interest_value, :is_weekend, :time_of_day, :raw_data, :test_run_id
                )
            """)
            
            session.execute(query, {
                **record,
                "region": "ID",
                "raw_data": json.dumps(record.get("raw_data", {})),
                "test_run_id": test_run_id
            })
        
        logger.success(f"Saved {len(hourly_data)} hourly trends")
        session.commit()
        
    except Exception as e:
        session.rollback()
        logger.error(f"Failed to save data: {e}")
        raise
    finally:
        session.close()


def test_fetch_hourly(keyword, category):
    """Main function for hourly data"""
    logger.info("="*60)
    logger.info("Starting HOURLY data fetch (1 week)")
    logger.info(f"Keyword: {keyword}")
    logger.info(f"Category: {category}")
    logger.info("="*60)
    
    # Test database connection
    logger.info("\nTesting database connection...")
    if not test_connection():
        logger.error("Database connection failed")
        return False
    
    # Get API token
    api_token = os.getenv("APIFY_API_TOKEN")
    if not api_token:
        logger.error("APIFY_API_TOKEN not found in .env")
        return False
    
    # Fetch data
    logger.info(f"\nFetching HOURLY data for '{keyword}'...")
    started_at = datetime.now()
    
    try:
        results = fetch_from_apify(keyword, api_token)
        
        if not results:
            logger.warning("No results returned")
            return False
        
        # Parse data
        logger.info("\nParsing hourly data...")
        hourly_data = parse_hourly_data(results, keyword, category)
        
        if not hourly_data:
            logger.warning("No hourly data found")
            return False
        
        # Save to database
        logger.info("\nSaving to database...")
        test_run_id = str(uuid.uuid4())
        save_hourly_to_database(hourly_data, test_run_id)
        
        # Summary
        logger.info("\n" + "="*60)
        logger.success("HOURLY DATA FETCH COMPLETED!")
        logger.info("="*60)
        logger.info(f"Summary:")
        logger.info(f"  Keyword: {keyword}")
        logger.info(f"  Category: {category}")
        logger.info(f"  Test run ID: {test_run_id}")
        logger.info(f"  Hourly records: {len(hourly_data)}")
        logger.info(f"  Time range: 1 week")
        logger.info("="*60)
        
        logger.info("\nCheck data in DBeaver:")
        logger.info(f"   SELECT * FROM test_hourly_trends WHERE test_run_id = '{test_run_id}' ORDER BY datetime;")
        
        return True
        
    except Exception as e:
        logger.error(f"\nError: {e}")
        return False


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Test fetch HOURLY data (1 week) dari Apify")
    parser.add_argument("--keyword", type=str, default="shopee", help="Keyword")
    parser.add_argument("--category", type=str, default="E-commerce & Shopping", help="Category")
    
    args = parser.parse_args()
    
    # Configure logger
    logger.remove()
    logger.add(
        sys.stdout,
        format="<green>{time:HH:mm:ss}</green> | <level>{level: <8}</level> | <level>{message}</level>",
        level="INFO"
    )
    
    # Run test
    success = test_fetch_hourly(args.keyword, args.category)
    sys.exit(0 if success else 1)

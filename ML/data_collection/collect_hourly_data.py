"""
Collect HOURLY data untuk ML training dataset.
Save ke production table: hourly_trends

Usage:
    python collect_hourly_data.py --keyword "shopee" --category "E-commerce & Shopping"
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

# Load .env.local FIRST before importing db_manager
if os.path.exists('.env.local'):
    load_dotenv('.env.local', override=True)
    logger.info("Using .env.local for database connection")
else:
    load_dotenv()
    logger.info("Using .env for database connection")

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
from src.database.db_manager import SessionLocal, test_connection


def fetch_from_apify(keyword, api_token):
    """Fetch hourly data (1 week) dari Apify"""
    client = ApifyClient(api_token)
    
    run_input = {
        "searchTerms": [keyword],
        "geo": "ID",
        "hl": "id",
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
    """Parse hourly trends data"""
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
            
            # Only collect hourly data (exclude midnight for daily data)
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


def save_hourly_to_database(hourly_data, collection_id):
    """Save hourly data ke PRODUCTION table"""
    if not hourly_data:
        logger.warning("No hourly data to save")
        return
    
    session = SessionLocal()
    
    try:
        for record in hourly_data:
            query = text("""
                INSERT INTO hourly_trends (
                    keyword, category, region, datetime, hour, day_of_week,
                    interest_value, is_weekend, time_of_day, raw_data, collection_id
                ) VALUES (
                    :keyword, :category, :region, :datetime, :hour, :day_of_week,
                    :interest_value, :is_weekend, :time_of_day, :raw_data, :collection_id
                )
                ON CONFLICT (keyword, category, region, datetime) 
                DO UPDATE SET
                    interest_value = EXCLUDED.interest_value,
                    raw_data = EXCLUDED.raw_data,
                    collection_id = EXCLUDED.collection_id,
                    collected_at = CURRENT_TIMESTAMP
            """)
            
            session.execute(query, {
                **record,
                "region": "ID",
                "raw_data": json.dumps(record.get("raw_data", {})),
                "collection_id": collection_id
            })
        
        logger.success(f"Saved {len(hourly_data)} hourly trends to PRODUCTION")
        session.commit()
        
    except Exception as e:
        session.rollback()
        logger.error(f"Failed to save hourly data: {e}")
        raise
    finally:
        session.close()


def log_collection(keyword, category, collection_id, status, hourly_count, error_message=None):
    """Log collection activity"""
    session = SessionLocal()
    
    try:
        query = text("""
            INSERT INTO collection_logs (
                collection_id, data_type, keyword, category, status, records_collected,
                started_at, completed_at, error_message
            ) VALUES (
                :collection_id, :data_type, :keyword, :category, :status, :records_collected,
                :started_at, :completed_at, :error_message
            )
        """)
        
        session.execute(query, {
            "collection_id": collection_id,
            "data_type": "hourly",
            "keyword": keyword,
            "category": category,
            "status": status,
            "records_collected": hourly_count,
            "started_at": datetime.now(),
            "completed_at": datetime.now(),
            "error_message": error_message
        })
        
        session.commit()
        
    except Exception as e:
        session.rollback()
        logger.error(f"Failed to log collection: {e}")
    finally:
        session.close()


def collect_hourly_data(keyword, category):
    """Main function for hourly data collection"""
    logger.info("="*60)
    logger.info("PRODUCTION HOURLY DATA COLLECTION")
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
    
    collection_id = str(uuid.uuid4())
    
    try:
        # Fetch data
        logger.info(f"\nFetching HOURLY data for '{keyword}'...")
        results = fetch_from_apify(keyword, api_token)
        
        if not results:
            logger.warning("No results returned")
            log_collection(keyword, category, collection_id, "failed", 0, "No results returned")
            return False
        
        # Parse data
        logger.info("\nParsing hourly data...")
        hourly_data = parse_hourly_data(results, keyword, category)
        
        if not hourly_data:
            logger.warning("No hourly data found")
            log_collection(keyword, category, collection_id, "failed", 0, "No hourly data found")
            return False
        
        # Save to database
        logger.info("\nSaving to PRODUCTION database...")
        save_hourly_to_database(hourly_data, collection_id)
        
        # Log collection
        log_collection(keyword, category, collection_id, "success", len(hourly_data))
        
        # Summary
        logger.info("\n" + "="*60)
        logger.success("HOURLY DATA COLLECTION COMPLETED!")
        logger.info("="*60)
        logger.info(f"Summary:")
        logger.info(f"  Keyword: {keyword}")
        logger.info(f"  Category: {category}")
        logger.info(f"  Collection ID: {collection_id}")
        logger.info(f"  Hourly records: {len(hourly_data)}")
        logger.info(f"  Time range: 1 week")
        logger.info("="*60)
        
        return True
        
    except Exception as e:
        logger.error(f"\nError: {e}")
        log_collection(keyword, category, collection_id, "failed", 0, str(e))
        return False


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Collect HOURLY data for ML training dataset")
    parser.add_argument("--keyword", type=str, help="Keyword to collect (optional if using --all)")
    parser.add_argument("--category", type=str, help="Category name (optional if using --all)")
    parser.add_argument("--all", action="store_true", help="Collect all categories from config")
    
    args = parser.parse_args()
    
    # Configure logger
    logger.remove()
    logger.add(
        sys.stdout,
        format="<green>{time:HH:mm:ss}</green> | <level>{level: <8}</level> | <level>{message}</level>",
        level="INFO"
    )
    
    # If no arguments, default to --all
    if not args.keyword and not args.category and not args.all:
        logger.info("No arguments provided, collecting ALL categories from config...")
        args.all = True
    
    # Collect all categories from config
    if args.all:
        config_path = os.path.join(os.path.dirname(__file__), '..', 'config', 'categories.json')
        
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                config = json.load(f)
            
            categories = config.get('categories', [])
            
            if not categories:
                logger.error("No categories found in config")
                sys.exit(1)
            
            logger.info(f"Found {len(categories)} categories to collect")
            logger.info("="*60)
            
            success_count = 0
            failed_count = 0
            total_keywords = 0
            
            for cat in categories:
                category_name = cat.get('name')
                keywords = cat.get('keywords', [])
                
                if not keywords:
                    logger.warning(f"No keywords for category: {category_name}")
                    continue
                
                logger.info(f"\n{'='*60}")
                logger.info(f"CATEGORY: {category_name}")
                logger.info(f"Keywords to collect: {len(keywords)}")
                logger.info(f"{'='*60}")
                
                # Collect ALL keywords for this category
                for idx, keyword in enumerate(keywords, 1):
                    total_keywords += 1
                    
                    logger.info(f"\n[{idx}/{len(keywords)}] Collecting: {keyword}")
                    
                    success = collect_hourly_data(keyword, category_name)
                    
                    if success:
                        success_count += 1
                        logger.success(f"✓ {keyword} completed")
                    else:
                        failed_count += 1
                        logger.error(f"✗ {keyword} failed")
                    
                    # Small delay between requests
                    import time
                    if idx < len(keywords):  # Don't delay after last keyword
                        time.sleep(2)
                
                logger.info(f"\nCategory '{category_name}' completed: {len(keywords)} keywords processed")
            
            # Final summary
            logger.info("\n" + "="*60)
            logger.info("ALL CATEGORIES COLLECTION COMPLETED!")
            logger.info("="*60)
            logger.info(f"Total categories: {len(categories)}")
            logger.info(f"Total keywords: {total_keywords}")
            logger.info(f"Successful: {success_count}")
            logger.info(f"Failed: {failed_count}")
            logger.info("="*60)
            
            sys.exit(0 if failed_count == 0 else 1)
            
        except FileNotFoundError:
            logger.error(f"Config file not found: {config_path}")
            sys.exit(1)
        except json.JSONDecodeError as e:
            logger.error(f"Invalid JSON in config file: {e}")
            sys.exit(1)
    
    # Single keyword/category collection
    else:
        if not args.keyword or not args.category:
            logger.error("Both --keyword and --category are required (or use --all)")
            sys.exit(1)
        
        success = collect_hourly_data(args.keyword, args.category)
        sys.exit(0 if success else 1)

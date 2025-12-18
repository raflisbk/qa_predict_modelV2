"""
Test fetch DAILY data (1 month) dari Apify.

Usage:
    python test_fetch_daily.py --keyword "shopee" --category "E-commerce & Shopping"
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
    """Fetch daily data (1 month) dari Apify"""
    client = ApifyClient(api_token)
    
    run_input = {
        "searchTerms": [keyword],
        "geo": "ID",
        "timeRange": "today 1-m",  # 1 month untuk daily data
        "category": "",
        "hl":"id",
        "isPublic": False,
    }
    
    logger.info(f"Running Apify actor for DAILY data: {keyword}")
    logger.info(f"Time range: 1 month (today 1-m)")
    run = client.actor("apify/google-trends-scraper").call(run_input=run_input)
    
    results = []
    for item in client.dataset(run["defaultDatasetId"]).iterate_items():
        results.append(item)
    
    logger.success(f"Got {len(results)} results from Apify")
    return results


def parse_daily_data(results, keyword, category):
    """Parse ONLY daily data"""
    daily_data = []
    
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
            
            # For monthly timerange, all data is daily (no need to filter midnight)
            daily_data.append({
                "keyword": keyword,
                "category": category,
                "date": dt.date(),
                "day_of_week": dt.strftime("%A"),
                "interest_value": interest_value,
                "raw_data": point
            })
    
    logger.info(f"Parsed {len(daily_data)} daily points")
    return daily_data


def parse_related_topics(results, keyword, category):
    """Parse related topics (top + rising)"""
    topics_data = []
    
    for result in results:
        # Top topics
        top_topics = result.get("relatedTopics_top", [])
        for topic in top_topics:
            topic_info = topic.get("topic", {})
            topics_data.append({
                "keyword": keyword,
                "category": category,
                "topic_mid": topic_info.get("mid"),
                "topic_title": topic_info.get("title"),
                "topic_type": topic_info.get("type"),
                "value": topic.get("value"),
                "formatted_value": topic.get("formattedValue"),
                "link": topic.get("link"),
                "is_rising": False
            })
        
        # Rising topics
        rising_topics = result.get("relatedTopics_rising", [])
        for topic in rising_topics:
            topic_info = topic.get("topic", {})
            topics_data.append({
                "keyword": keyword,
                "category": category,
                "topic_mid": topic_info.get("mid"),
                "topic_title": topic_info.get("title"),
                "topic_type": topic_info.get("type"),
                "value": topic.get("value"),
                "formatted_value": topic.get("formattedValue"),
                "link": topic.get("link"),
                "is_rising": True
            })
    
    logger.info(f"Parsed {len(topics_data)} related topics")
    return topics_data


def parse_related_queries(results, keyword, category):
    """Parse related queries (top + rising)"""
    queries_data = []
    
    for result in results:
        # Top queries
        top_queries = result.get("relatedQueries_top", [])
        for query in top_queries:
            queries_data.append({
                "keyword": keyword,
                "category": category,
                "query": query.get("query"),
                "value": query.get("value"),
                "formatted_value": query.get("formattedValue"),
                "link": query.get("link"),
                "is_rising": False
            })
        
        # Rising queries
        rising_queries = result.get("relatedQueries_rising", [])
        for query in rising_queries:
            queries_data.append({
                "keyword": keyword,
                "category": category,
                "query": query.get("query"),
                "value": query.get("value"),
                "formatted_value": query.get("formattedValue"),
                "link": query.get("link"),
                "is_rising": True
            })
    
    logger.info(f"Parsed {len(queries_data)} related queries")
    return queries_data


def save_daily_to_database(daily_data, test_run_id):
    """Save daily data ke database"""
    session = SessionLocal()
    
    try:
        for record in daily_data:
            query = text("""
                INSERT INTO test_daily_trends (
                    keyword, category, region, date, day_of_week,
                    interest_value, raw_data, test_run_id
                ) VALUES (
                    :keyword, :category, :region, :date, :day_of_week,
                    :interest_value, :raw_data, :test_run_id
                )
            """)
            
            session.execute(query, {
                **record,
                "region": "ID",
                "raw_data": json.dumps(record.get("raw_data", {})),
                "test_run_id": test_run_id
            })
        
        logger.success(f"Saved {len(daily_data)} daily trends")
        session.commit()
        
    except Exception as e:
        session.rollback()
        logger.error(f"Failed to save data: {e}")
        raise
    finally:
        session.close()


def save_related_topics_to_database(topics_data, test_run_id):
    """Save related topics ke database"""
    if not topics_data:
        logger.info("No related topics to save")
        return
    
    session = SessionLocal()
    
    try:
        for record in topics_data:
            query = text("""
                INSERT INTO test_related_topics (
                    keyword, category, region, topic_mid, topic_title, topic_type,
                    value, formatted_value, link, is_rising, test_run_id
                ) VALUES (
                    :keyword, :category, :region, :topic_mid, :topic_title, :topic_type,
                    :value, :formatted_value, :link, :is_rising, :test_run_id
                )
            """)
            
            session.execute(query, {
                **record,
                "region": "ID",
                "test_run_id": test_run_id
            })
        
        logger.success(f"Saved {len(topics_data)} related topics")
        session.commit()
        
    except Exception as e:
        session.rollback()
        logger.error(f"Failed to save related topics: {e}")
        raise
    finally:
        session.close()


def save_related_queries_to_database(queries_data, test_run_id):
    """Save related queries ke database"""
    if not queries_data:
        logger.info("No related queries to save")
        return
    
    session = SessionLocal()
    
    try:
        for record in queries_data:
            query = text("""
                INSERT INTO test_related_queries (
                    keyword, category, region, query, value, formatted_value,
                    link, is_rising, test_run_id
                ) VALUES (
                    :keyword, :category, :region, :query, :value, :formatted_value,
                    :link, :is_rising, :test_run_id
                )
            """)
            
            session.execute(query, {
                **record,
                "region": "ID",
                "test_run_id": test_run_id
            })
        
        logger.success(f"Saved {len(queries_data)} related queries")
        session.commit()
        
    except Exception as e:
        session.rollback()
        logger.error(f"Failed to save related queries: {e}")
        raise
    finally:
        session.close()


def test_fetch_daily(keyword, category):
    """Main function for daily data"""
    logger.info("="*60)
    logger.info("Starting DAILY data fetch (1 month)")
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
    logger.info(f"\nFetching DAILY data for '{keyword}'...")
    started_at = datetime.now()
    
    try:
        results = fetch_from_apify(keyword, api_token)
        
        if not results:
            logger.warning("No results returned")
            return False
        
        # Parse data
        logger.info("\nParsing daily data...")
        daily_data = parse_daily_data(results, keyword, category)
        
        if not daily_data:
            logger.warning("No daily data found")
            return False
        
        # Parse related topics and queries
        logger.info("\nParsing related topics...")
        topics_data = parse_related_topics(results, keyword, category)
        
        logger.info("\nParsing related queries...")
        queries_data = parse_related_queries(results, keyword, category)
        
        # Save to database
        logger.info("\nSaving to database...")
        test_run_id = str(uuid.uuid4())
        save_daily_to_database(daily_data, test_run_id)
        save_related_topics_to_database(topics_data, test_run_id)
        save_related_queries_to_database(queries_data, test_run_id)
        
        # Summary
        logger.info("\n" + "="*60)
        logger.success("DAILY DATA FETCH COMPLETED!")
        logger.info("="*60)
        logger.info(f"Summary:")
        logger.info(f"  Keyword: {keyword}")
        logger.info(f"  Category: {category}")
        logger.info(f"  Test run ID: {test_run_id}")
        logger.info(f"  Daily records: {len(daily_data)}")
        logger.info(f"  Related topics: {len(topics_data)}")
        logger.info(f"  Related queries: {len(queries_data)}")
        logger.info(f"  Time range: 1 month")
        logger.info("="*60)
        
        logger.info("\nCheck data in DBeaver:")
        logger.info(f"   SELECT * FROM test_daily_trends WHERE test_run_id = '{test_run_id}';")
        logger.info(f"   SELECT * FROM test_related_topics WHERE test_run_id = '{test_run_id}';")
        logger.info(f"   SELECT * FROM test_related_queries WHERE test_run_id = '{test_run_id}';")
        
        return True
        
    except Exception as e:
        logger.error(f"\nError: {e}")
        return False


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Test fetch DAILY data (1 month) dari Apify")
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
    success = test_fetch_daily(args.keyword, args.category)
    sys.exit(0 if success else 1)
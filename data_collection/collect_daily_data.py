import os
import sys
import uuid
import json
import time
import argparse
from datetime import datetime, timezone, timedelta
from dotenv import load_dotenv
from loguru import logger
from apify_client import ApifyClient
from sqlalchemy import text

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
from src.database.db_manager import SessionLocal, test_connection
from src.utils.state_tracker import CollectionStateTracker

load_dotenv()


def fetch_from_apify(keyword, api_token):
    client = ApifyClient(api_token)
    
    run_input = {
        "searchTerms": [keyword],
        "geo": "ID",
        "timeRange": "today 3-m",  # 3 months untuk daily data
        "category": "",
        "hl": "id",
        "isPublic": False
    }
    
    logger.info(f"Running Apify actor for DAILY data: {keyword}")
    logger.info(f"Time range: 3 months (today 3-m)")
    run = client.actor("apify/google-trends-scraper").call(run_input=run_input)
    
    results = []
    for item in client.dataset(run["defaultDatasetId"]).iterate_items():
        results.append(item)
    
    logger.success(f"Got {len(results)} results from Apify")
    
    # Debug: Log available keys in response
    if results:
        logger.debug(f"Available keys in response: {list(results[0].keys())}")
        
        # Check if interestOverTime data exists
        if "interestOverTime_timelineData" in results[0]:
            timeline_count = len(results[0].get("interestOverTime_timelineData", []))
            logger.info(f"Found {timeline_count} timeline data points")
        else:
            logger.warning("No 'interestOverTime_timelineData' found in response!")
            logger.debug(f"Response keys: {list(results[0].keys())}")
    
    return results


def parse_daily_data(results, keyword, category):
    """Parse daily trends data"""
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
            
            # For monthly timerange, all data is daily
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
    queries_data = []
    
    for result in results:
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


def save_daily_to_database(daily_data, collection_id):
    """Save daily data ke PRODUCTION table"""
    if not daily_data:
        logger.warning("No daily data to save")
        return
    
    session = SessionLocal()
    
    try:
        for record in daily_data:
            query = text("""
                INSERT INTO daily_trends (
                    keyword, category, region, date, day_of_week,
                    interest_value, raw_data, collection_id
                ) VALUES (
                    :keyword, :category, :region, :date, :day_of_week,
                    :interest_value, :raw_data, :collection_id
                )
                ON CONFLICT (keyword, category, region, date) 
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
        
        logger.success(f"Saved {len(daily_data)} daily trends to PRODUCTION")
        session.commit()
        
    except Exception as e:
        session.rollback()
        logger.error(f"Failed to save daily data: {e}")
        raise
    finally:
        session.close()


def save_related_topics_to_database(topics_data, collection_id):
    """Save related topics ke PRODUCTION table"""
    if not topics_data:
        logger.info("No related topics to save")
        return
    
    session = SessionLocal()
    
    try:
        for record in topics_data:
            query = text("""
                INSERT INTO related_topics (
                    keyword, category, region, topic_mid, topic_title, topic_type,
                    value, formatted_value, link, is_rising, collection_id
                ) VALUES (
                    :keyword, :category, :region, :topic_mid, :topic_title, :topic_type,
                    :value, :formatted_value, :link, :is_rising, :collection_id
                )
            """)
            
            session.execute(query, {
                **record,
                "region": "ID",
                "collection_id": collection_id
            })
        
        logger.success(f"Saved {len(topics_data)} related topics to PRODUCTION")
        session.commit()
        
    except Exception as e:
        session.rollback()
        logger.error(f"Failed to save related topics: {e}")
        raise
    finally:
        session.close()


def save_related_queries_to_database(queries_data, collection_id):
    """Save related queries ke PRODUCTION table"""
    if not queries_data:
        logger.info("No related queries to save")
        return
    
    session = SessionLocal()
    
    try:
        for record in queries_data:
            query = text("""
                INSERT INTO related_queries (
                    keyword, category, region, query, value, formatted_value,
                    link, is_rising, collection_id
                ) VALUES (
                    :keyword, :category, :region, :query, :value, :formatted_value,
                    :link, :is_rising, :collection_id
                )
            """)
            
            session.execute(query, {
                **record,
                "region": "ID",
                "collection_id": collection_id
            })
        
        logger.success(f"Saved {len(queries_data)} related queries to PRODUCTION")
        session.commit()
        
    except Exception as e:
        session.rollback()
        logger.error(f"Failed to save related queries: {e}")
        raise
    finally:
        session.close()


def log_collection(keyword, category, collection_id, status, daily_count, topics_count, queries_count, error_message=None):
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
            "data_type": "daily",
            "keyword": keyword,
            "category": category,
            "status": status,
            "records_collected": daily_count + topics_count + queries_count,
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


def collect_daily_data(keyword, category, tracker=None):
    """Main function for daily data collection"""
    logger.info("="*60)
    logger.info("PRODUCTION DAILY DATA COLLECTION")
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
        logger.info(f"\nFetching DAILY data for '{keyword}'...")
        results = fetch_from_apify(keyword, api_token)
        
        if not results:
            logger.warning("No results returned")
            log_collection(keyword, category, collection_id, "failed", 0, 0, 0, "No results returned")
            return False
        
        # Parse data
        logger.info("\nParsing daily data...")
        daily_data = parse_daily_data(results, keyword, category)
        
        logger.info("\nParsing related topics...")
        topics_data = parse_related_topics(results, keyword, category)
        
        logger.info("\nParsing related queries...")
        queries_data = parse_related_queries(results, keyword, category)
        
        if not daily_data:
            logger.warning("No daily data found")
            log_collection(keyword, category, collection_id, "failed", 0, 0, 0, "No daily data found")
            return False
        
        # Save to database
        logger.info("\nSaving to PRODUCTION database...")
        save_daily_to_database(daily_data, collection_id)
        save_related_topics_to_database(topics_data, collection_id)
        save_related_queries_to_database(queries_data, collection_id)
        
        # Log collection
        log_collection(keyword, category, collection_id, "success", 
                      len(daily_data), len(topics_data), len(queries_data))
        
        # Mark as success in tracker
        if tracker:
            tracker.mark_keyword_success("daily_collection", category, keyword, collection_id)
        
        # Summary
        logger.info("\n" + "="*60)
        logger.success("DAILY DATA COLLECTION COMPLETED!")
        logger.info("="*60)
        logger.info(f"Summary:")
        logger.info(f"  Keyword: {keyword}")
        logger.info(f"  Category: {category}")
        logger.info(f"  Collection ID: {collection_id}")
        logger.info(f"  Daily records: {len(daily_data)}")
        logger.info(f"  Related topics: {len(topics_data)}")
        logger.info(f"  Related queries: {len(queries_data)}")
        logger.info(f"  Time range: 1 month")
        logger.info("="*60)
        
        return True
        
    except Exception as e:
        logger.error(f"\nError: {e}")
        log_collection(keyword, category, collection_id, "failed", 0, 0, 0, str(e))
        
        # Mark as failed in tracker
        if tracker:
            tracker.mark_keyword_failed("daily_collection", category, keyword, str(e))
        
        return False


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Collect DAILY data for ML training dataset")
    parser.add_argument("--keyword", type=str, help="Keyword to collect (optional if using --all or --category-only)")
    parser.add_argument("--category", type=str, help="Category name (optional if using --all)")
    parser.add_argument("--category-only", type=str, help="Collect all keywords in specific category")
    parser.add_argument("--all", action="store_true", help="Collect all categories from config")
    
    args = parser.parse_args()
    
    # Configure logger
    logger.remove()
    logger.add(
        sys.stdout,
        format="<green>{time:HH:mm:ss}</green> | <level>{level: <8}</level> | <level>{message}</level>",
        level="DEBUG"  # Enable debug logging
    )
    
    # If no arguments, default to --all
    if not args.keyword and not args.category and not args.all and not args.category_only:
        logger.info("No arguments provided, collecting ALL categories from config...")
        args.all = True
    
    # Collect specific category only
    if args.category_only:
        config_path = os.path.join(os.path.dirname(__file__), '..', 'config', 'categories.json')
        
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                config = json.load(f)
            
            categories = config.get('categories', [])
            
            # Find the category
            target_category = None
            for cat in categories:
                if cat.get('name') == args.category_only:
                    target_category = cat
                    break
            
            if not target_category:
                logger.error(f"Category '{args.category_only}' not found in config")
                logger.info(f"Available categories:")
                for cat in categories:
                    logger.info(f"  - {cat.get('name')}")
                sys.exit(1)
            
            # Initialize state tracker
            tracker = CollectionStateTracker()
            tracker.start_collection("daily_collection")
            
            # Show progress if resuming
            progress = tracker.get_progress_summary("daily_collection")
            if progress.get("success_keywords", 0) > 0:
                logger.info(f"\nResuming from previous run:")
                logger.info(f"  Already completed: {progress['success_keywords']} keywords")
                logger.info(f"  Failed: {progress['failed_keywords']} keywords")
                logger.info(f"  Pending: {progress['pending_keywords']} keywords")
            
            category_name = target_category.get('name')
            keywords = target_category.get('keywords', [])
            
            logger.info(f"\n{'='*60}")
            logger.info(f"CATEGORY: {category_name}")
            logger.info(f"Keywords to collect: {len(keywords)}")
            logger.info(f"{'='*60}")
            
            success_count = 0
            failed_count = 0
            skipped_count = 0
            
            # Collect ALL keywords for this category
            for idx, keyword in enumerate(keywords, 1):
                # Check if already completed
                if tracker.is_keyword_completed("daily_collection", category_name, keyword):
                    logger.info(f"\n[{idx}/{len(keywords)}] Skipping: {keyword} (already completed)")
                    skipped_count += 1
                    success_count += 1
                    continue
                
                logger.info(f"\n[{idx}/{len(keywords)}] Collecting: {keyword}")
                
                success = collect_daily_data(keyword, category_name, tracker)
                
                if success:
                    success_count += 1
                    logger.success(f"✓ {keyword} completed")
                else:
                    failed_count += 1
                    logger.error(f"✗ {keyword} failed")
                
                # Small delay between requests
                import time
                if idx < len(keywords):
                    time.sleep(2)
            
            # Mark category as completed
            tracker.mark_category_completed("daily_collection", category_name)
            
            # Summary
            logger.info("\n" + "="*60)
            logger.info(f"CATEGORY '{category_name}' COMPLETED!")
            logger.info("="*60)
            logger.info(f"Total keywords: {len(keywords)}")
            logger.info(f"Skipped (already done): {skipped_count}")
            logger.info(f"Successful: {success_count}")
            logger.info(f"Failed: {failed_count}")
            logger.info(f"\nState file: {tracker.state_file}")
            logger.info("="*60)
            
            sys.exit(0 if failed_count == 0 else 1)
            
        except FileNotFoundError:
            logger.error(f"Config file not found: {config_path}")
            sys.exit(1)
        except json.JSONDecodeError as e:
            logger.error(f"Invalid JSON in config file: {e}")
            sys.exit(1)
    
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
            
            # Initialize state tracker
            tracker = CollectionStateTracker()
            tracker.start_collection("daily_collection")
            
            # Show progress if resuming
            progress = tracker.get_progress_summary("daily_collection")
            if progress.get("success_keywords", 0) > 0:
                logger.info(f"\nResuming from previous run:")
                logger.info(f"  Already completed: {progress['success_keywords']} keywords")
                logger.info(f"  Failed: {progress['failed_keywords']} keywords")
                logger.info(f"  Pending: {progress['pending_keywords']} keywords")
                logger.info("="*60)
            
            success_count = 0
            failed_count = 0
            total_keywords = 0
            skipped_count = 0
            
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
                    
                    # Check if already completed
                    if tracker.is_keyword_completed("daily_collection", category_name, keyword):
                        logger.info(f"\n[{idx}/{len(keywords)}] Skipping: {keyword} (already completed)")
                        skipped_count += 1
                        success_count += 1  # Count as success
                        continue
                    
                    logger.info(f"\n[{idx}/{len(keywords)}] Collecting: {keyword}")
                    
                    success = collect_daily_data(keyword, category_name, tracker)
                    
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
                
                # Mark category as completed
                tracker.mark_category_completed("daily_collection", category_name)
                logger.info(f"\nCategory '{category_name}' completed: {len(keywords)} keywords processed")
            
            # Mark collection as completed
            tracker.complete_collection("daily_collection")
            
            # Final summary
            logger.info("\n" + "="*60)
            logger.info("ALL CATEGORIES COLLECTION COMPLETED!")
            logger.info("="*60)
            logger.info(f"Total categories: {len(categories)}")
            logger.info(f"Total keywords: {total_keywords}")
            logger.info(f"Skipped (already done): {skipped_count}")
            logger.info(f"Successful: {success_count}")
            logger.info(f"Failed: {failed_count}")
            logger.info(f"\nState file: {tracker.state_file}")
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
        
        success = collect_daily_data(args.keyword, args.category)
        sys.exit(0 if success else 1)

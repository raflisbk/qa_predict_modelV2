"""
Apify client wrapper untuk Google Trends scraper.
"""

import time
import uuid
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta

from apify_client import ApifyClient
from loguru import logger
from sqlalchemy import text

from src.database.db_manager import SessionLocal


class ApifyGoogleTrendsClient:
    """Client untuk fetch Google Trends data via Apify"""
    
    def __init__(self, api_token: str, test_mode: bool = False, test_run_id: Optional[str] = None):
        """
        Initialize Apify client
        
        Args:
            api_token: Apify API token
            test_mode: Jika True, simpan ke test tables
            test_run_id: UUID untuk test run (required jika test_mode=True)
        """
        self.client = ApifyClient(api_token)
        self.actor_id = "apify/google-trends-scraper"
        self.test_mode = test_mode
        self.test_run_id = test_run_id
        
        if test_mode and not test_run_id:
            raise ValueError("test_run_id required when test_mode=True")
        
        logger.info(f"Apify client initialized (test_mode={test_mode})")
    
    def _run_actor_with_retry(
        self, 
        run_input: Dict[str, Any], 
        max_retries: int = 3,
        retry_delay: int = 5
    ) -> List[Dict]:
        """
        Run Apify actor dengan retry logic
        
        Args:
            run_input: Input untuk actor
            max_retries: Maksimal retry attempts
            retry_delay: Delay antar retry (seconds)
            
        Returns:
            List of results dari actor
        """
        for attempt in range(max_retries):
            try:
                logger.info(f"Running Apify actor (attempt {attempt + 1}/{max_retries})")
                
                # run actor
                run = self.client.actor(self.actor_id).call(run_input=run_input)
                
                # fetch results
                results = []
                for item in self.client.dataset(run["defaultDatasetId"]).iterate_items():
                    results.append(item)
                
                logger.success(f"✅ Actor run successful, got {len(results)} results")
                return results
                
            except Exception as e:
                logger.error(f"❌ Actor run failed (attempt {attempt + 1}): {e}")
                
                if attempt < max_retries - 1:
                    logger.info(f"Retrying in {retry_delay} seconds...")
                    time.sleep(retry_delay)
                else:
                    logger.error("Max retries reached, giving up")
                    raise
        
        return []
    
    def fetch_trends(
        self,
        search_terms: List[str],
        geo: str = "ID",
        time_range: str = "now 7-d",
        category: int = 0,
        max_retries: int = 3
    ) -> List[Dict]:
        """
        Fetch Google Trends data
        
        Args:
            search_terms: List of keywords to search
            geo: Geographic location (default: ID for Indonesia)
            time_range: Time range (e.g., "now 7-d", "now 1-d")
            category: Google Trends category code (0 = all)
            max_retries: Max retry attempts
            
        Returns:
            List of trend data
        """
        run_input = {
            "searchTerms": search_terms,
            "geo": geo,
            "timeRange": time_range,
            "category": category,
            "isPublic": False,
            "maxItems": 1000
        }
        
        logger.info(f"Fetching trends for: {search_terms}")
        logger.info(f"Geo: {geo}, Time range: {time_range}")
        
        return self._run_actor_with_retry(run_input, max_retries=max_retries)
    
    def log_collection(
        self,
        data_type: str,
        keyword: str,
        category: str,
        status: str,
        records_collected: int = 0,
        error_message: Optional[str] = None,
        started_at: Optional[datetime] = None
    ):
        """Log collection activity ke database"""
        session = SessionLocal()
        try:
            query = text("""
                INSERT INTO collection_logs (
                    collection_id, data_type, keyword, category, status,
                    records_collected, error_message, started_at, completed_at
                ) VALUES (
                    :collection_id, :data_type, :keyword, :category, :status,
                    :records_collected, :error_message, :started_at, :completed_at
                )
            """)
            
            session.execute(query, {
                "collection_id": str(uuid.uuid4()),
                "data_type": data_type,
                "keyword": keyword,
                "category": category,
                "status": status,
                "records_collected": records_collected,
                "error_message": error_message,
                "started_at": started_at or datetime.now(),
                "completed_at": datetime.now()
            })
            session.commit()
            logger.info(f"Logged collection: {data_type} - {keyword} - {status}")
        except Exception as e:
            session.rollback()
            logger.error(f"Failed to log collection: {e}")
        finally:
            session.close()
    
    def parse_interest_over_time(
        self, 
        results: List[Dict],
        keyword: str,
        category: str
    ) -> tuple[List[Dict], List[Dict]]:
        """
        Parse interest over time data dari Apify results
        
        Args:
            results: Results dari Apify actor
            keyword: Keyword yang di-fetch
            category: Category name
            
        Returns:
            Tuple of (daily_data, hourly_data)
        """
        daily_data = []
        hourly_data = []
        
        for result in results:
            if "interestOverTime" not in result:
                continue
            
            timeline_data = result.get("interestOverTime", {}).get("timelineData", [])
            
            for point in timeline_data:
                # parse timestamp
                timestamp_str = point.get("time")
                if not timestamp_str:
                    continue
                
                # convert timestamp (format: "1702857600" unix timestamp)
                try:
                    timestamp = int(timestamp_str)
                    dt = datetime.fromtimestamp(timestamp)
                except:
                    logger.warning(f"Failed to parse timestamp: {timestamp_str}")
                    continue
                
                interest_value = point.get("value", [0])[0] if point.get("value") else 0
                
                # tentukan apakah daily atau hourly berdasarkan time range
                # jika ada jam (hour != 0), maka hourly
                if dt.hour == 0 and dt.minute == 0:
                    # daily data
                    daily_data.append({
                        "keyword": keyword,
                        "category": category,
                        "date": dt.date(),
                        "day_of_week": dt.strftime("%A"),
                        "interest_value": interest_value,
                        "raw_data": point
                    })
                else:
                    # hourly data
                    hourly_data.append({
                        "keyword": keyword,
                        "category": category,
                        "datetime": dt,
                        "hour": dt.hour,
                        "day_of_week": dt.strftime("%A"),
                        "interest_value": interest_value,
                        "is_weekend": dt.weekday() >= 5,
                        "raw_data": point
                    })
        
        logger.info(f"Parsed {len(daily_data)} daily points, {len(hourly_data)} hourly points")
        return daily_data, hourly_data
    
    def parse_related_topics(
        self,
        results: List[Dict],
        keyword: str,
        category: str
    ) -> List[Dict]:
        """Parse related topics dari Apify results"""
        topics = []
        
        for result in results:
            # top topics
            for topic in result.get("relatedTopics", {}).get("top", []):
                topics.append({
                    "keyword": keyword,
                    "category": category,
                    "topic_mid": topic.get("topic", {}).get("mid"),
                    "topic_title": topic.get("topic", {}).get("title"),
                    "topic_type": topic.get("topic", {}).get("type"),
                    "value": topic.get("value"),
                    "formatted_value": topic.get("formattedValue"),
                    "link": topic.get("link"),
                    "is_rising": False
                })
            
            # rising topics
            for topic in result.get("relatedTopics", {}).get("rising", []):
                topics.append({
                    "keyword": keyword,
                    "category": category,
                    "topic_mid": topic.get("topic", {}).get("mid"),
                    "topic_title": topic.get("topic", {}).get("title"),
                    "topic_type": topic.get("topic", {}).get("type"),
                    "value": topic.get("value"),
                    "formatted_value": topic.get("formattedValue"),
                    "link": topic.get("link"),
                    "is_rising": True
                })
        
        logger.info(f"Parsed {len(topics)} related topics")
        return topics
    
    def parse_related_queries(
        self,
        results: List[Dict],
        keyword: str,
        category: str
    ) -> List[Dict]:
        """Parse related queries dari Apify results"""
        queries = []
        
        for result in results:
            # top queries
            for query in result.get("relatedQueries", {}).get("top", []):
                queries.append({
                    "keyword": keyword,
                    "category": category,
                    "query": query.get("query"),
                    "value": query.get("value"),
                    "formatted_value": query.get("formattedValue"),
                    "link": query.get("link"),
                    "is_rising": False
                })
            
            # rising queries
            for query in result.get("relatedQueries", {}).get("rising", []):
                queries.append({
                    "keyword": keyword,
                    "category": category,
                    "query": query.get("query"),
                    "value": query.get("value"),
                    "formatted_value": query.get("formattedValue"),
                    "link": query.get("link"),
                    "is_rising": True
                })
        
        logger.info(f"Parsed {len(queries)} related queries")
        return queries

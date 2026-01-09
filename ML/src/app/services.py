from apify_client import ApifyClient
import os
import logging
from datetime import datetime
from cachetools import TTLCache
from threading import Lock
import json

class ApifyServiceError(Exception):
    """Fetch failed"""
    pass

class ApifyService:
    """Service fetching trends."""
    
    def __init__(self, api_token=None):
        self.api_token = api_token or os.getenv("APIFY_API_TOKEN")
        self.logger = logging.getLogger("api.services")
        
        # Thread-safe cache
        self._cache = TTLCache(maxsize=100, ttl=21600) # 6 hours
        self._cache_lock = Lock()
        
        # Timeout config
        self._timeout_secs = 60  # 60s max
        
        if not self.api_token:
            self.logger.critical("Missing TOKEN")
            raise ValueError("Missing TOKEN")
            
        self.client = ApifyClient(self.api_token)

    def fetch_last_14_days(self, keyword: str) -> list:
        """Fetch 14d data."""
        # Thread-safe read
        with self._cache_lock:
            if keyword in self._cache:
                self.logger.info(f"Cache hit: {keyword}")
                return self._cache[keyword]

        try:
            self.logger.info(f"Fetching: {keyword}")
            
            # Set params
            run_input = {
                "searchTerms": [keyword],
                "geo": "ID",
                "timeRange": "today 1-m", 
                "category": "",
                "hl": "id",
                "isPublic": False
            }
            
            # Start actor (with timeout)
            run = self.client.actor("apify/google-trends-scraper").call(
                run_input=run_input,
                timeout_secs=self._timeout_secs
            )
            
            if not run:
                raise ApifyServiceError("Run failed")

            # Get items
            dataset_items = []
            for item in self.client.dataset(run["defaultDatasetId"]).iterate_items():
                dataset_items.append(item)
                
            if not dataset_items:
                raise ApifyServiceError(f"No data: {keyword}")
                
            # Get timeline
            timeline_data = dataset_items[0].get("interestOverTime_timelineData", [])
            
            if len(timeline_data) < 14:
                raise ApifyServiceError(f"Short data: {len(timeline_data)}")
                
            # Extract last 14
            recent_data = timeline_data[-14:]
            interest_values = []
            
            for point in recent_data:
                valid_value = point.get("value", [0])[0] if point.get("value") else 0
                interest_values.append(float(valid_value))
            
            # Thread-safe write
            with self._cache_lock:
                self._cache[keyword] = interest_values
            
            self.logger.info(f"Fetched {len(interest_values)}")
            return interest_values

        except Exception as e:
            self.logger.error(f"Fetch error: {str(e)}")
            raise ApifyServiceError(f"Fetch error: {str(e)}")

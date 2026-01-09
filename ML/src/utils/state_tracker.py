"""
Collection State Tracker
Tracks progress of data collection to enable resume capability
"""

import json
import os
from datetime import datetime
from typing import Dict, List, Optional
from loguru import logger


class CollectionStateTracker:
    """Track collection progress and enable resume"""
    
    def __init__(self, state_file: str = None):
        # Use absolute path relative to project root (ML folder)
        if state_file is None:
            project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '../..'))
            state_file = os.path.join(project_root, "data/collection_state.json")
        self.state_file = state_file
        self.state = self._load_state()
    
    def _load_state(self) -> Dict:
        """Load state from file or create new"""
        if os.path.exists(self.state_file):
            try:
                with open(self.state_file, 'r', encoding='utf-8') as f:
                    state = json.load(f)
                logger.info(f"Loaded existing state from {self.state_file}")
                return state
            except Exception as e:
                logger.warning(f"Failed to load state: {e}, creating new state")
        
        # Create new state with enhanced metadata
        return {
            "version": "2.0",  # Updated version for enhanced tracking
            "last_updated": None,
            "daily_collection": {
                "script": "collect_daily_data.py",
                "time_range": "today 3-m",
                "started_at": None,
                "completed_at": None,
                "status": "not_started",  # not_started, in_progress, completed
                "categories": {}
            },
            "hourly_collection": {
                "script": "collect_hourly_data.py",
                "time_range": "now 7-d",
                "started_at": None,
                "completed_at": None,
                "status": "not_started",
                "categories": {}
            }
        }
    
    def _save_state(self):
        """Save state to file"""
        try:
            # Create directory if not exists
            os.makedirs(os.path.dirname(self.state_file), exist_ok=True)
            
            self.state["last_updated"] = datetime.now().isoformat()
            
            with open(self.state_file, 'w', encoding='utf-8') as f:
                json.dump(self.state, f, indent=2, ensure_ascii=False)
            
            logger.debug(f"State saved to {self.state_file}")
        except Exception as e:
            logger.error(f"Failed to save state: {e}")
    
    def start_collection(self, collection_type: str):
        """Mark collection as started"""
        if collection_type not in ["daily_collection", "hourly_collection"]:
            raise ValueError(f"Invalid collection type: {collection_type}")
        
        self.state[collection_type]["started_at"] = datetime.now().isoformat()
        self.state[collection_type]["status"] = "in_progress"
        self._save_state()
        
        logger.info(f"Started {collection_type}")
    
    def complete_collection(self, collection_type: str):
        """Mark collection as completed"""
        if collection_type not in ["daily_collection", "hourly_collection"]:
            raise ValueError(f"Invalid collection type: {collection_type}")
        
        self.state[collection_type]["completed_at"] = datetime.now().isoformat()
        self.state[collection_type]["status"] = "completed"
        self._save_state()
        
        logger.success(f"Completed {collection_type}")
    
    def mark_keyword_success(
        self, 
        collection_type: str, 
        category: str, 
        keyword: str, 
        collection_id: str,
        collection_mode: Optional[str] = None,
        records: Optional[Dict[str, int]] = None,
        retry_count: int = 0
    ):
        """Mark keyword as successfully collected with detailed metadata
        
        Args:
            collection_type: 'daily_collection' or 'hourly_collection'
            category: Category name
            keyword: Keyword collected
            collection_id: UUID of collection
            collection_mode: CLI mode used (--all, --category-only, --keyword)
            records: Dict with counts (daily_trends, related_topics, related_queries, hourly_trends)
            retry_count: Number of retries before success
        """
        if collection_type not in ["daily_collection", "hourly_collection"]:
            raise ValueError(f"Invalid collection type: {collection_type}")
        
        # Initialize category if not exists
        if category not in self.state[collection_type]["categories"]:
            self.state[collection_type]["categories"][category] = {
                "started_at": datetime.now().isoformat(),
                "completed_at": None,
                "status": "in_progress",
                "collection_mode": collection_mode,
                "keywords": {}
            }
        
        # Mark keyword as success with enhanced metadata
        keyword_data = {
            "status": "success",
            "collection_id": collection_id,
            "collected_at": datetime.now().isoformat(),
            "retry_count": retry_count
        }
        
        # Add records count if provided
        if records:
            keyword_data["records"] = records
        
        self.state[collection_type]["categories"][category]["keywords"][keyword] = keyword_data
        
        self._save_state()
        logger.debug(f"Marked {keyword} ({category}) as success")
    
    def mark_keyword_failed(
        self, 
        collection_type: str, 
        category: str, 
        keyword: str, 
        error: str,
        retry_count: int = 0,
        collection_mode: Optional[str] = None
    ):
        """Mark keyword as failed with detailed error info
        
        Args:
            collection_type: 'daily_collection' or 'hourly_collection'
            category: Category name
            keyword: Keyword that failed
            error: Error message
            retry_count: Number of retries attempted
            collection_mode: CLI mode used
        """
        if collection_type not in ["daily_collection", "hourly_collection"]:
            raise ValueError(f"Invalid collection type: {collection_type}")
        
        # Initialize category if not exists
        if category not in self.state[collection_type]["categories"]:
            self.state[collection_type]["categories"][category] = {
                "started_at": datetime.now().isoformat(),
                "completed_at": None,
                "status": "in_progress",
                "collection_mode": collection_mode,
                "keywords": {}
            }
        
        # Mark keyword as failed with enhanced metadata
        self.state[collection_type]["categories"][category]["keywords"][keyword] = {
            "status": "failed",
            "error": error,
            "failed_at": datetime.now().isoformat(),
            "retry_count": retry_count
        }
        
        self._save_state()
        logger.debug(f"Marked {keyword} ({category}) as failed")
    
    def mark_category_completed(self, collection_type: str, category: str):
        """Mark category as completed"""
        if collection_type not in ["daily_collection", "hourly_collection"]:
            raise ValueError(f"Invalid collection type: {collection_type}")
        
        if category in self.state[collection_type]["categories"]:
            self.state[collection_type]["categories"][category]["completed_at"] = datetime.now().isoformat()
            self.state[collection_type]["categories"][category]["status"] = "completed"
            self._save_state()
            logger.info(f"Category '{category}' completed")
    
    def is_keyword_completed(self, collection_type: str, category: str, keyword: str) -> bool:
        """Check if keyword is already successfully collected"""
        if collection_type not in ["daily_collection", "hourly_collection"]:
            return False
        
        cat_data = self.state[collection_type]["categories"].get(category, {})
        keyword_data = cat_data.get("keywords", {}).get(keyword, {})
        
        return keyword_data.get("status") == "success"
    
    def get_pending_keywords(self, collection_type: str, category: str, all_keywords: List[str]) -> List[str]:
        """Get list of keywords that need to be collected"""
        pending = []
        
        for keyword in all_keywords:
            if not self.is_keyword_completed(collection_type, category, keyword):
                pending.append(keyword)
        
        return pending
    
    def get_collection_status(self, collection_type: str) -> str:
        """Get current status of collection"""
        if collection_type not in ["daily_collection", "hourly_collection"]:
            return "unknown"
        
        return self.state[collection_type].get("status", "not_started")
    
    def get_progress_summary(self, collection_type: str) -> Dict:
        """Get progress summary"""
        if collection_type not in ["daily_collection", "hourly_collection"]:
            return {}
        
        collection_data = self.state[collection_type]
        
        total_keywords = 0
        success_keywords = 0
        failed_keywords = 0
        
        for category, cat_data in collection_data["categories"].items():
            for keyword, kw_data in cat_data.get("keywords", {}).items():
                total_keywords += 1
                if kw_data.get("status") == "success":
                    success_keywords += 1
                elif kw_data.get("status") == "failed":
                    failed_keywords += 1
        
        return {
            "status": collection_data.get("status", "not_started"),
            "started_at": collection_data.get("started_at"),
            "completed_at": collection_data.get("completed_at"),
            "total_categories": len(collection_data["categories"]),
            "total_keywords": total_keywords,
            "success_keywords": success_keywords,
            "failed_keywords": failed_keywords,
            "pending_keywords": total_keywords - success_keywords - failed_keywords
        }
    
    def reset_collection(self, collection_type: str):
        """Reset collection state (start from scratch)"""
        if collection_type not in ["daily_collection", "hourly_collection"]:
            raise ValueError(f"Invalid collection type: {collection_type}")
        
        self.state[collection_type] = {
            "started_at": None,
            "completed_at": None,
            "status": "not_started",
            "categories": {}
        }
        self._save_state()
        
        logger.warning(f"Reset {collection_type} state")
    
    def reset_all(self):
        """Reset all collection state"""
        self.state = {
            "version": "2.0",
            "last_updated": None,
            "daily_collection": {
                "script": "collect_daily_data.py",
                "time_range": "today 3-m",
                "started_at": None,
                "completed_at": None,
                "status": "not_started",
                "categories": {}
            },
            "hourly_collection": {
                "script": "collect_hourly_data.py",
                "time_range": "now 7-d",
                "started_at": None,
                "completed_at": None,
                "status": "not_started",
                "categories": {}
            }
        }
        self._save_state()
        
        logger.warning("Reset ALL collection state")

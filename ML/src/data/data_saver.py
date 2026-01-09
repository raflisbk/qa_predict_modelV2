"""
Data savers untuk menyimpan trends data ke database.
"""

from typing import List, Dict
from datetime import datetime
from sqlalchemy import text
from loguru import logger

from src.database.db_manager import SessionLocal


class TrendsDataSaver:
    """Saver untuk menyimpan trends data ke database"""
    
    def __init__(self, test_mode: bool = False, test_run_id: str = None):
        """
        Initialize data saver
        
        Args:
            test_mode: Jika True, simpan ke test tables
            test_run_id: UUID untuk test run
        """
        self.test_mode = test_mode
        self.test_run_id = test_run_id
        
        # tentukan table names
        if test_mode:
            self.daily_table = "test_daily_trends"
            self.hourly_table = "test_hourly_trends"
            self.topics_table = "test_related_topics"
            self.queries_table = "test_related_queries"
        else:
            self.daily_table = "daily_trends"
            self.hourly_table = "hourly_trends"
            self.topics_table = "related_topics"
            self.queries_table = "related_queries"
    
    def save_daily_trends(self, data: List[Dict]) -> int:
        """
        Simpan daily trends ke database
        
        Args:
            data: List of daily trend data
            
        Returns:
            Number of records saved
        """
        if not data:
            logger.warning("No daily trends data to save")
            return 0
        
        session = SessionLocal()
        saved_count = 0
        
        try:
            for record in data:
                if self.test_mode:
                    query = text(f"""
                        INSERT INTO {self.daily_table} (
                            keyword, category, region, date, day_of_week,
                            interest_value, raw_data, test_run_id
                        ) VALUES (
                            :keyword, :category, :region, :date, :day_of_week,
                            :interest_value, :raw_data::jsonb, :test_run_id
                        )
                        ON CONFLICT (keyword, category, region, date, test_run_id) 
                        DO UPDATE SET
                            interest_value = EXCLUDED.interest_value,
                            raw_data = EXCLUDED.raw_data
                    """)
                    
                    session.execute(query, {
                        **record,
                        "region": "ID",
                        "raw_data": str(record.get("raw_data", {})),
                        "test_run_id": self.test_run_id
                    })
                else:
                    query = text(f"""
                        INSERT INTO {self.daily_table} (
                            keyword, category, region, date, day_of_week,
                            interest_value, raw_data
                        ) VALUES (
                            :keyword, :category, :region, :date, :day_of_week,
                            :interest_value, :raw_data::jsonb
                        )
                        ON CONFLICT (keyword, category, region, date) 
                        DO UPDATE SET
                            interest_value = EXCLUDED.interest_value,
                            raw_data = EXCLUDED.raw_data
                    """)
                    
                    session.execute(query, {
                        **record,
                        "region": "ID",
                        "raw_data": str(record.get("raw_data", {}))
                    })
                
                saved_count += 1
            
            session.commit()
            logger.success(f"✅ Saved {saved_count} daily trends to {self.daily_table}")
            return saved_count
            
        except Exception as e:
            session.rollback()
            logger.error(f"❌ Failed to save daily trends: {e}")
            raise
        finally:
            session.close()
    
    def save_hourly_trends(self, data: List[Dict]) -> int:
        """
        Simpan hourly trends ke database
        
        Args:
            data: List of hourly trend data
            
        Returns:
            Number of records saved
        """
        if not data:
            logger.warning("No hourly trends data to save")
            return 0
        
        session = SessionLocal()
        saved_count = 0
        
        try:
            for record in data:
                # determine time_of_day
                hour = record.get("hour", 0)
                if 0 <= hour < 6:
                    time_of_day = "night"
                elif 6 <= hour < 12:
                    time_of_day = "morning"
                elif 12 <= hour < 18:
                    time_of_day = "afternoon"
                else:
                    time_of_day = "evening"
                
                if self.test_mode:
                    query = text(f"""
                        INSERT INTO {self.hourly_table} (
                            keyword, category, region, datetime, hour, day_of_week,
                            interest_value, is_weekend, time_of_day, raw_data, test_run_id
                        ) VALUES (
                            :keyword, :category, :region, :datetime, :hour, :day_of_week,
                            :interest_value, :is_weekend, :time_of_day, :raw_data::jsonb, :test_run_id
                        )
                        ON CONFLICT (keyword, category, region, datetime, test_run_id) 
                        DO UPDATE SET
                            interest_value = EXCLUDED.interest_value,
                            raw_data = EXCLUDED.raw_data
                    """)
                    
                    session.execute(query, {
                        **record,
                        "region": "ID",
                        "time_of_day": time_of_day,
                        "raw_data": str(record.get("raw_data", {})),
                        "test_run_id": self.test_run_id
                    })
                else:
                    query = text(f"""
                        INSERT INTO {self.hourly_table} (
                            keyword, category, region, datetime, hour, day_of_week,
                            interest_value, is_weekend, time_of_day, raw_data
                        ) VALUES (
                            :keyword, :category, :region, :datetime, :hour, :day_of_week,
                            :interest_value, :is_weekend, :time_of_day, :raw_data::jsonb
                        )
                        ON CONFLICT (keyword, category, region, datetime) 
                        DO UPDATE SET
                            interest_value = EXCLUDED.interest_value,
                            raw_data = EXCLUDED.raw_data
                    """)
                    
                    session.execute(query, {
                        **record,
                        "region": "ID",
                        "time_of_day": time_of_day,
                        "raw_data": str(record.get("raw_data", {}))
                    })
                
                saved_count += 1
            
            session.commit()
            logger.success(f"✅ Saved {saved_count} hourly trends to {self.hourly_table}")
            return saved_count
            
        except Exception as e:
            session.rollback()
            logger.error(f"❌ Failed to save hourly trends: {e}")
            raise
        finally:
            session.close()
    
    def save_related_topics(self, data: List[Dict]) -> int:
        """Simpan related topics ke database"""
        if not data:
            logger.warning("No related topics data to save")
            return 0
        
        session = SessionLocal()
        saved_count = 0
        
        try:
            for record in data:
                if self.test_mode:
                    query = text(f"""
                        INSERT INTO {self.topics_table} (
                            keyword, category, region, topic_mid, topic_title,
                            topic_type, value, formatted_value, link, is_rising, test_run_id
                        ) VALUES (
                            :keyword, :category, :region, :topic_mid, :topic_title,
                            :topic_type, :value, :formatted_value, :link, :is_rising, :test_run_id
                        )
                    """)
                    
                    session.execute(query, {
                        **record,
                        "region": "ID",
                        "test_run_id": self.test_run_id
                    })
                else:
                    query = text(f"""
                        INSERT INTO {self.topics_table} (
                            keyword, category, region, topic_mid, topic_title,
                            topic_type, value, formatted_value, link, is_rising
                        ) VALUES (
                            :keyword, :category, :region, :topic_mid, :topic_title,
                            :topic_type, :value, :formatted_value, :link, :is_rising
                        )
                    """)
                    
                    session.execute(query, {
                        **record,
                        "region": "ID"
                    })
                
                saved_count += 1
            
            session.commit()
            logger.success(f"✅ Saved {saved_count} related topics to {self.topics_table}")
            return saved_count
            
        except Exception as e:
            session.rollback()
            logger.error(f"❌ Failed to save related topics: {e}")
            raise
        finally:
            session.close()
    
    def save_related_queries(self, data: List[Dict]) -> int:
        """Simpan related queries ke database"""
        if not data:
            logger.warning("No related queries data to save")
            return 0
        
        session = SessionLocal()
        saved_count = 0
        
        try:
            for record in data:
                if self.test_mode:
                    query = text(f"""
                        INSERT INTO {self.queries_table} (
                            keyword, category, region, query, value,
                            formatted_value, link, is_rising, test_run_id
                        ) VALUES (
                            :keyword, :category, :region, :query, :value,
                            :formatted_value, :link, :is_rising, :test_run_id
                        )
                    """)
                    
                    session.execute(query, {
                        **record,
                        "region": "ID",
                        "test_run_id": self.test_run_id
                    })
                else:
                    query = text(f"""
                        INSERT INTO {self.queries_table} (
                            keyword, category, region, query, value,
                            formatted_value, link, is_rising
                        ) VALUES (
                            :keyword, :category, :region, :query, :value,
                            :formatted_value, :link, :is_rising
                        )
                    """)
                    
                    session.execute(query, {
                        **record,
                        "region": "ID"
                    })
                
                saved_count += 1
            
            session.commit()
            logger.success(f"✅ Saved {saved_count} related queries to {self.queries_table}")
            return saved_count
            
        except Exception as e:
            session.rollback()
            logger.error(f"❌ Failed to save related queries: {e}")
            raise
        finally:
            session.close()

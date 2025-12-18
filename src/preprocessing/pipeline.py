"""
Main Preprocessing Pipeline - AC-02 Compliance
Orchestrates data cleaning and normalization for ML training

Usage:
    python src/preprocessing/pipeline.py --data-type daily
    python src/preprocessing/pipeline.py --data-type hourly
    python src/preprocessing/pipeline.py --all
"""

import os
import sys
import argparse
import pandas as pd
from datetime import datetime
from loguru import logger
from sqlalchemy import text

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../..'))
from src.database.db_manager import SessionLocal, test_connection
from src.preprocessing.data_cleaner import DataCleaner
from src.preprocessing.normalizer import DataNormalizer


class PreprocessingPipeline:
    """Main preprocessing pipeline for Google Trends data"""
    
    def __init__(self):
        self.cleaner = DataCleaner()
        self.normalizer = DataNormalizer()
        self.session = SessionLocal()
    
    def process_daily_trends(self) -> pd.DataFrame:
        """
        Process daily trends data
        
        Returns:
            Processed dataframe
        """
        logger.info("="*60)
        logger.info("PROCESSING DAILY TRENDS DATA")
        logger.info("="*60)
        
        # 1. Load raw data from database
        logger.info("\n[1/4] Loading raw data from database...")
        df = self._load_daily_trends()
        
        if df.empty:
            logger.warning("No daily trends data found in database")
            return df
        
        logger.info(f"Loaded {len(df)} raw records")
        
        # 2. Clean data (AC-02)
        logger.info("\n[2/4] Cleaning data (AC-02)...")
        df = self.cleaner.clean_daily_trends(df)
        
        # 3. Normalize data (AC-02)
        logger.info("\n[3/4] Normalizing data (AC-02)...")
        df = self.normalizer.normalize_daily_trends(df)
        
        # 4. Save processed data
        logger.info("\n[4/4] Saving processed data...")
        self._save_processed_daily_trends(df)
        
        # Summary
        logger.info("\n" + "="*60)
        logger.success("DAILY TRENDS PROCESSING COMPLETED!")
        logger.info("="*60)
        logger.info(f"Final records: {len(df)}")
        logger.info(f"Cleaning report: {self.cleaner.get_cleaning_report()}")
        logger.info(f"Normalization report: {self.normalizer.get_normalization_report()}")
        logger.info("="*60)
        
        return df
    
    def process_hourly_trends(self) -> pd.DataFrame:
        """
        Process hourly trends data
        
        Returns:
            Processed dataframe
        """
        logger.info("="*60)
        logger.info("PROCESSING HOURLY TRENDS DATA")
        logger.info("="*60)
        
        # 1. Load raw data
        logger.info("\n[1/4] Loading raw data from database...")
        df = self._load_hourly_trends()
        
        if df.empty:
            logger.warning("No hourly trends data found in database")
            return df
        
        logger.info(f"Loaded {len(df)} raw records")
        
        # 2. Clean data
        logger.info("\n[2/4] Cleaning data (AC-02)...")
        df = self.cleaner.clean_hourly_trends(df)
        
        # 3. Normalize data
        logger.info("\n[3/4] Normalizing data (AC-02)...")
        df = self.normalizer.normalize_hourly_trends(df)
        
        # 4. Save processed data
        logger.info("\n[4/4] Saving processed data...")
        self._save_processed_hourly_trends(df)
        
        # Summary
        logger.info("\n" + "="*60)
        logger.success("HOURLY TRENDS PROCESSING COMPLETED!")
        logger.info("="*60)
        logger.info(f"Final records: {len(df)}")
        logger.info(f"Cleaning report: {self.cleaner.get_cleaning_report()}")
        logger.info(f"Normalization report: {self.normalizer.get_normalization_report()}")
        logger.info("="*60)
        
        return df
    
    def _load_daily_trends(self) -> pd.DataFrame:
        """Load daily trends from database"""
        query = text("""
            SELECT 
                keyword, category, region, date, day_of_week,
                interest_value, is_holiday, holiday_name,
                collection_id, collected_at
            FROM daily_trends
            ORDER BY date DESC
        """)
        
        df = pd.read_sql(query, self.session.bind)
        return df
    
    def _load_hourly_trends(self) -> pd.DataFrame:
        """Load hourly trends from database"""
        query = text("""
            SELECT 
                keyword, category, region, datetime, hour, day_of_week,
                interest_value, is_weekend, time_of_day,
                collection_id, collected_at
            FROM hourly_trends
            ORDER BY datetime DESC
        """)
        
        df = pd.read_sql(query, self.session.bind)
        return df
    
    def _save_processed_daily_trends(self, df: pd.DataFrame):
        """Save processed daily trends to CSV"""
        output_dir = os.path.join(os.path.dirname(__file__), '../../data/processed')
        os.makedirs(output_dir, exist_ok=True)
        
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        output_file = os.path.join(output_dir, f'daily_trends_processed_{timestamp}.csv')
        
        df.to_csv(output_file, index=False)
        logger.success(f"Saved processed data to: {output_file}")
    
    def _save_processed_hourly_trends(self, df: pd.DataFrame):
        """Save processed hourly trends to CSV"""
        output_dir = os.path.join(os.path.dirname(__file__), '../../data/processed')
        os.makedirs(output_dir, exist_ok=True)
        
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        output_file = os.path.join(output_dir, f'hourly_trends_processed_{timestamp}.csv')
        
        df.to_csv(output_file, index=False)
        logger.success(f"Saved processed data to: {output_file}")
    
    def close(self):
        """Close database session"""
        self.session.close()


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(description="Preprocess Google Trends data (AC-02 compliant)")
    parser.add_argument("--data-type", type=str, choices=['daily', 'hourly', 'all'], 
                       help="Type of data to process")
    
    args = parser.parse_args()
    
    # Configure logger
    logger.remove()
    logger.add(
        sys.stdout,
        format="<green>{time:HH:mm:ss}</green> | <level>{level: <8}</level> | <level>{message}</level>",
        level="INFO"
    )
    
    # Test database connection
    logger.info("Testing database connection...")
    if not test_connection():
        logger.error("Database connection failed")
        sys.exit(1)
    
    # Run preprocessing
    pipeline = PreprocessingPipeline()
    
    try:
        if args.data_type == 'daily':
            pipeline.process_daily_trends()
        elif args.data_type == 'hourly':
            pipeline.process_hourly_trends()
        elif args.data_type == 'all' or args.data_type is None:
            logger.info("Processing ALL data types...\n")
            pipeline.process_daily_trends()
            logger.info("\n")
            pipeline.process_hourly_trends()
        
        logger.success("\nAll preprocessing completed!")
        
    except Exception as e:
        logger.error(f"Preprocessing failed: {e}")
        raise
    finally:
        pipeline.close()


if __name__ == "__main__":
    main()

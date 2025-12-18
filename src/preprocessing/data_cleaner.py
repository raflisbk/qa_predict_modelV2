"""
Data Cleaner Module - AC-02 Compliance
Handles cleaning of raw data from database:
- Remove null values
- Remove duplicates
- Fix formatting inconsistencies
"""

import pandas as pd
from loguru import logger
from typing import Dict, List


class DataCleaner:
    """Clean raw Google Trends data according to AC-02 requirements"""
    
    def __init__(self):
        self.cleaning_stats = {
            "null_removed": 0,
            "duplicates_removed": 0,
            "formatting_fixed": 0
        }
    
    def clean_daily_trends(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Clean daily trends data
        
        Args:
            df: Raw daily trends dataframe
            
        Returns:
            Cleaned dataframe
        """
        logger.info(f"Cleaning daily trends data: {len(df)} records")
        
        original_count = len(df)
        
        # 1. Remove null values in critical columns
        df = self._remove_nulls(df, critical_columns=['keyword', 'date', 'interest_value'])
        
        # 2. Remove duplicates
        df = self._remove_duplicates(df, subset=['keyword', 'category', 'region', 'date'])
        
        # 3. Fix formatting inconsistencies
        df = self._fix_formatting(df)
        
        # 4. Validate data types
        df = self._validate_data_types(df)
        
        logger.success(f"Cleaned daily trends: {len(df)} records (removed {original_count - len(df)})")
        logger.info(f"Cleaning stats: {self.cleaning_stats}")
        
        return df
    
    def clean_hourly_trends(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Clean hourly trends data
        
        Args:
            df: Raw hourly trends dataframe
            
        Returns:
            Cleaned dataframe
        """
        logger.info(f"Cleaning hourly trends data: {len(df)} records")
        
        original_count = len(df)
        
        # 1. Remove null values
        df = self._remove_nulls(df, critical_columns=['keyword', 'datetime', 'interest_value'])
        
        # 2. Remove duplicates
        df = self._remove_duplicates(df, subset=['keyword', 'category', 'region', 'datetime'])
        
        # 3. Fix formatting
        df = self._fix_formatting(df)
        
        # 4. Validate data types
        df = self._validate_data_types(df)
        
        logger.success(f"Cleaned hourly trends: {len(df)} records (removed {original_count - len(df)})")
        logger.info(f"Cleaning stats: {self.cleaning_stats}")
        
        return df
    
    def _remove_nulls(self, df: pd.DataFrame, critical_columns: List[str]) -> pd.DataFrame:
        """Remove rows with null values in critical columns"""
        before = len(df)
        
        # Remove nulls in critical columns
        df = df.dropna(subset=critical_columns)
        
        # Fill nulls in non-critical columns with defaults
        if 'day_of_week' in df.columns:
            df['day_of_week'] = df['day_of_week'].fillna('Unknown')
        
        if 'time_of_day' in df.columns:
            df['time_of_day'] = df['time_of_day'].fillna('Unknown')
        
        after = len(df)
        self.cleaning_stats['null_removed'] += (before - after)
        
        return df
    
    def _remove_duplicates(self, df: pd.DataFrame, subset: List[str]) -> pd.DataFrame:
        """Remove duplicate records based on subset columns"""
        before = len(df)
        
        # Keep first occurrence, remove duplicates
        df = df.drop_duplicates(subset=subset, keep='first')
        
        after = len(df)
        self.cleaning_stats['duplicates_removed'] += (before - after)
        
        return df
    
    def _fix_formatting(self, df: pd.DataFrame) -> pd.DataFrame:
        """Fix formatting inconsistencies in string columns"""
        before_count = 0
        
        # Fix keyword formatting
        if 'keyword' in df.columns:
            # Count how many will be changed
            before_count += (df['keyword'] != df['keyword'].str.strip().str.lower()).sum()
            
            # Apply fixes
            df['keyword'] = df['keyword'].str.strip().str.lower()
        
        # Fix category formatting
        if 'category' in df.columns:
            before_count += (df['category'] != df['category'].str.strip()).sum()
            df['category'] = df['category'].str.strip()
        
        # Fix region formatting
        if 'region' in df.columns:
            before_count += (df['region'] != df['region'].str.strip().str.upper()).sum()
            df['region'] = df['region'].str.strip().str.upper()
        
        self.cleaning_stats['formatting_fixed'] += before_count
        
        return df
    
    def _validate_data_types(self, df: pd.DataFrame) -> pd.DataFrame:
        """Validate and convert data types"""
        
        # Ensure interest_value is integer
        if 'interest_value' in df.columns:
            df['interest_value'] = pd.to_numeric(df['interest_value'], errors='coerce')
            df['interest_value'] = df['interest_value'].fillna(0).astype(int)
            
            # Clip to valid range [0, 100]
            df['interest_value'] = df['interest_value'].clip(0, 100)
        
        # Ensure date/datetime columns are proper datetime
        if 'date' in df.columns:
            df['date'] = pd.to_datetime(df['date'], errors='coerce')
        
        if 'datetime' in df.columns:
            df['datetime'] = pd.to_datetime(df['datetime'], errors='coerce')
        
        # Ensure boolean columns
        if 'is_weekend' in df.columns:
            df['is_weekend'] = df['is_weekend'].fillna(False).astype(bool)
        
        if 'is_holiday' in df.columns:
            df['is_holiday'] = df['is_holiday'].fillna(False).astype(bool)
        
        return df
    
    def get_cleaning_report(self) -> Dict:
        """Get cleaning statistics report"""
        return {
            "total_nulls_removed": self.cleaning_stats['null_removed'],
            "total_duplicates_removed": self.cleaning_stats['duplicates_removed'],
            "total_formatting_fixed": self.cleaning_stats['formatting_fixed'],
            "total_cleaned": sum(self.cleaning_stats.values())
        }

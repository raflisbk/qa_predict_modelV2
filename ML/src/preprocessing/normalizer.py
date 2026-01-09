"""
Data Normalizer Module - AC-02 Compliance
Handles normalization of cleaned data:
- Normalize time-series into daily/weekly buckets
- Standardize keywords (lowercase, trimmed, Unicode-normalized)
"""

import pandas as pd
import unicodedata
from loguru import logger
from typing import Dict


class DataNormalizer:
    """Normalize cleaned data according to AC-02 requirements"""
    
    def __init__(self):
        self.normalization_stats = {
            "keywords_normalized": 0,
            "timeseries_normalized": 0
        }
    
    def normalize_daily_trends(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Normalize daily trends data
        
        Args:
            df: Cleaned daily trends dataframe
            
        Returns:
            Normalized dataframe
        """
        logger.info(f"Normalizing daily trends data: {len(df)} records")
        
        # 1. Standardize keywords (AC-02)
        df = self._standardize_keywords(df)
        
        # 2. Normalize time-series into daily buckets
        df = self._normalize_daily_timeseries(df)
        
        # 3. Add derived time features
        df = self._add_time_features(df, granularity='daily')
        
        logger.success(f"Normalized daily trends: {len(df)} records")
        logger.info(f"Normalization stats: {self.normalization_stats}")
        
        return df
    
    def normalize_hourly_trends(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Normalize hourly trends data
        
        Args:
            df: Cleaned hourly trends dataframe
            
        Returns:
            Normalized dataframe
        """
        logger.info(f"Normalizing hourly trends data: {len(df)} records")
        
        # 1. Standardize keywords
        df = self._standardize_keywords(df)
        
        # 2. Normalize time-series into hourly buckets
        df = self._normalize_hourly_timeseries(df)
        
        # 3. Add derived time features
        df = self._add_time_features(df, granularity='hourly')
        
        logger.success(f"Normalized hourly trends: {len(df)} records")
        logger.info(f"Normalization stats: {self.normalization_stats}")
        
        return df
    
    def _standardize_keywords(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Standardize keywords according to AC-02:
        - Lowercase
        - Trimmed
        - Unicode-normalized
        """
        if 'keyword' not in df.columns:
            return df
        
        before = df['keyword'].copy()
        
        # Apply standardization
        df['keyword'] = df['keyword'].apply(self._normalize_text)
        
        # Count changes
        changed = (before != df['keyword']).sum()
        self.normalization_stats['keywords_normalized'] += changed
        
        return df
    
    def _normalize_text(self, text: str) -> str:
        """
        Normalize text:
        1. Unicode normalization (NFD -> NFC)
        2. Lowercase
        3. Strip whitespace
        """
        if pd.isna(text):
            return text
        
        # Unicode normalization
        text = unicodedata.normalize('NFC', str(text))
        
        # Lowercase and strip
        text = text.lower().strip()
        
        # Remove multiple spaces
        text = ' '.join(text.split())
        
        return text
    
    def _normalize_daily_timeseries(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Normalize time-series into daily buckets
        Ensure one record per keyword-category-region-date
        """
        if 'date' not in df.columns:
            return df
        
        # Group by daily bucket and aggregate
        group_cols = ['keyword', 'category', 'region', 'date']
        
        # Aggregate function: take mean of interest_value if duplicates exist
        agg_dict = {
            'interest_value': 'mean',
            'day_of_week': 'first'
        }
        
        # Add optional columns if they exist
        if 'is_holiday' in df.columns:
            agg_dict['is_holiday'] = 'first'
        if 'holiday_name' in df.columns:
            agg_dict['holiday_name'] = 'first'
        
        before = len(df)
        df = df.groupby(group_cols, as_index=False).agg(agg_dict)
        after = len(df)
        
        # Round interest_value to integer
        df['interest_value'] = df['interest_value'].round().astype(int)
        
        self.normalization_stats['timeseries_normalized'] += (before - after)
        
        return df
    
    def _normalize_hourly_timeseries(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Normalize time-series into hourly buckets
        Ensure one record per keyword-category-region-datetime
        """
        if 'datetime' not in df.columns:
            return df
        
        # Round datetime to nearest hour
        df['datetime'] = pd.to_datetime(df['datetime']).dt.floor('H')
        
        # Group by hourly bucket and aggregate
        group_cols = ['keyword', 'category', 'region', 'datetime']
        
        agg_dict = {
            'interest_value': 'mean',
            'hour': 'first',
            'day_of_week': 'first',
            'time_of_day': 'first'
        }
        
        if 'is_weekend' in df.columns:
            agg_dict['is_weekend'] = 'first'
        
        before = len(df)
        df = df.groupby(group_cols, as_index=False).agg(agg_dict)
        after = len(df)
        
        # Round interest_value to integer
        df['interest_value'] = df['interest_value'].round().astype(int)
        
        self.normalization_stats['timeseries_normalized'] += (before - after)
        
        return df
    
    def _add_time_features(self, df: pd.DataFrame, granularity: str = 'daily') -> pd.DataFrame:
        """
        Add derived time features for ML
        
        Args:
            df: Dataframe with date/datetime column
            granularity: 'daily' or 'hourly'
        """
        if granularity == 'daily' and 'date' in df.columns:
            df['year'] = pd.to_datetime(df['date']).dt.year
            df['month'] = pd.to_datetime(df['date']).dt.month
            df['week'] = pd.to_datetime(df['date']).dt.isocalendar().week
            df['day'] = pd.to_datetime(df['date']).dt.day
            df['dayofweek'] = pd.to_datetime(df['date']).dt.dayofweek  # 0=Monday, 6=Sunday
            df['is_weekend'] = df['dayofweek'].isin([5, 6])  # Saturday, Sunday
            
        elif granularity == 'hourly' and 'datetime' in df.columns:
            df['year'] = pd.to_datetime(df['datetime']).dt.year
            df['month'] = pd.to_datetime(df['datetime']).dt.month
            df['week'] = pd.to_datetime(df['datetime']).dt.isocalendar().week
            df['day'] = pd.to_datetime(df['datetime']).dt.day
            df['dayofweek'] = pd.to_datetime(df['datetime']).dt.dayofweek
            
            # Hour is already in the data, but ensure it's correct
            if 'hour' not in df.columns:
                df['hour'] = pd.to_datetime(df['datetime']).dt.hour
        
        return df
    
    def get_normalization_report(self) -> Dict:
        """Get normalization statistics report"""
        return {
            "keywords_normalized": self.normalization_stats['keywords_normalized'],
            "timeseries_normalized": self.normalization_stats['timeseries_normalized'],
            "total_normalized": sum(self.normalization_stats.values())
        }

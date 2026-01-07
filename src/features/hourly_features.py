
import pandas as pd
import numpy as np
from typing import List, Optional
from loguru import logger

class HourlyFeatureEngineer:
    """
    Feature Engineer for Best Time Prediction Model.
    Transforms raw hourly trends data into features for LightGBM.
    """
    
    def __init__(self):
        self.feature_columns = [
            'category', 
            'day_of_week_num', 
            'hour', 
            'is_weekend',
            'hour_sin',
            'hour_cos',
            'day_sin',
            'day_cos'
        ]
        self.target_column = 'interest_value'
        
    def preprocess(self, df: pd.DataFrame, is_training: bool = True) -> pd.DataFrame:
        """
        Main preprocessing method.
        
        Args:
            df: Raw dataframe from hourly_trends table
            is_training: If True, expects target column to be present
            
        Returns:
            Processed dataframe with features
        """
        if df.empty:
            logger.warning("Input dataframe is empty")
            return pd.DataFrame()
            
        df = df.copy()
        
        # 1. Enhance Date/Time Features
        df = self._create_time_features(df)
        
        # 2. Category Handling (ensure string)
        if 'category' in df.columns:
            df['category'] = df['category'].astype(str)
            
        # 3. Handle Target
        if is_training and self.target_column in df.columns:
            # Drop rows where target is missing
            df = df.dropna(subset=[self.target_column])
            # Ensure target is float
            df[self.target_column] = df[self.target_column].astype(float)
            
        return df
        
    def _create_time_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """Create cyclic time features and numeric day representations"""
        
        # Ensure 'datetime' is datetime object
        if not pd.api.types.is_datetime64_any_dtype(df['datetime']):
            df['datetime'] = pd.to_datetime(df['datetime'])
            
        # Basic extractions
        df['hour'] = df['datetime'].dt.hour
        df['day_of_week_num'] = df['datetime'].dt.dayofweek  # 0=Monday, 6=Sunday
        df['is_weekend'] = df['day_of_week_num'].isin([5, 6]).astype(int)
        
        # Cyclic Hour (0-23)
        df['hour_sin'] = np.sin(2 * np.pi * df['hour'] / 24)
        df['hour_cos'] = np.cos(2 * np.pi * df['hour'] / 24)
        
        # Cyclic Day (0-6)
        df['day_sin'] = np.sin(2 * np.pi * df['day_of_week_num'] / 7)
        df['day_cos'] = np.cos(2 * np.pi * df['day_of_week_num'] / 7)
        
        return df

    def get_feature_columns(self) -> List[str]:
        return self.feature_columns

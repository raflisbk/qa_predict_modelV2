
import os
import sys
import joblib
import pandas as pd
import numpy as np
import argparse
from datetime import datetime, timedelta
from loguru import logger

# Add project root to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../..'))
from src.features.hourly_features import HourlyFeatureEngineer

class BestTimePredictor:
    """
    Inference Engine for Best Time to Post Recommendation.
    """
    
    def __init__(self, model_path=None):
        if model_path is None:
            model_path = os.path.join(os.path.dirname(__file__), '../../../models/best_time/lgb_best_time_model.pkl')
            
        self.model_path = model_path
        self.model = None
        self.engineer = HourlyFeatureEngineer()
        
    def load_model(self):
        """Load trained LightGBM model"""
        if not os.path.exists(self.model_path):
            raise FileNotFoundError(f"Model not found at: {self.model_path}")
            
        logger.info(f"Loading model from: {self.model_path}")
        self.model = joblib.load(self.model_path)
        
    def predict_next_24_hours(self, category: str, base_date: datetime = None):
        """
        Predict interest scores for the next 24 hours (starting from tomorrow 00:00).
        """
        if self.model is None:
            self.load_model()
            
        if base_date is None:
            base_date = datetime.now()
            
        # Target date is tomorrow
        target_date = base_date + timedelta(days=1)
        start_time = target_date.replace(hour=0, minute=0, second=0, microsecond=0)
        
        # Generate timestamps for 24 hours
        timestamps = [start_time + timedelta(hours=i) for i in range(24)]
        
        # Create input dataframe
        df = pd.DataFrame({
            'datetime': timestamps,
            'category': [category] * 24
        })
        
        # Feature Engineering
        df_features = self.engineer.preprocess(df, is_training=False)
        
        # Predict
        feature_cols = self.engineer.get_feature_columns()
        X = df_features[feature_cols]
        
        # Ensure category type matches training
        X['category'] = X['category'].astype('category')
        
        predictions = self.model.predict(X)
        df_features['predicted_interest'] = predictions
        
        return df_features
        
    def get_best_window(self, category: str, window_size: int = 3):
        """
        Find the best posting window.
        Returns the start hour and end hour of the best N-hour window.
        """
        df = self.predict_next_24_hours(category)
        
        # Calculate rolling sum of interest
        # shift(-N+1) is needed because rolling window is typically ending at current index, 
        # but we want "start hour" reference.
        # Actually simpler: just iterate manual or use numeric convolution
        
        best_score = -1
        best_start_hour = -1
        
        scores = df['predicted_interest'].values
        hours = df['hour'].values
        
        for i in range(len(scores) - window_size + 1):
            window_score = np.sum(scores[i : i + window_size])
            if window_score > best_score:
                best_score = window_score
                best_start_hour = hours[i]
                
        # Format output
        best_end_hour = (best_start_hour + window_size) % 24
        
        avg_score_in_window = best_score / window_size
        
        return {
            "category": category,
            "best_window_start": int(best_start_hour),
            "best_window_end": int(best_end_hour),
            "window_size": window_size,
            "score": float(best_score),
            "avg_interest": float(avg_score_in_window),
            "target_date": df['datetime'].iloc[0].date().isoformat()
        }

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Predict Best Time to Post")
    parser.add_argument("--category", type=str, required=True, help="Category name")
    parser.add_argument("--window", type=int, default=3, help="Window size in hours (default: 3)")
    
    args = parser.parse_args()
    
    predictor = BestTimePredictor()
    
    try:
        result = predictor.get_best_window(args.category, args.window)
        
        print("\n" + "="*50)
        print(f"BEST TIME RECOMMENDATION ({result['target_date']})")
        print("="*50)
        print(f"Category  : {result['category']}")
        print(f"Window    : {result['best_window_start']:02d}:00 - {result['best_window_end']:02d}:00")
        print(f"Confidence: {result['avg_interest']:.2f} (Predicted Interest Score)")
        print("="*50 + "\n")
        
    except Exception as e:
        logger.error(f"Prediction failed: {e}")

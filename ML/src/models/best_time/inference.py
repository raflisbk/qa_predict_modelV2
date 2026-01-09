
import os
import sys
import joblib
import pandas as pd
import numpy as np
import argparse
from datetime import datetime, timedelta
from loguru import logger
from neuralprophet import NeuralProphet

# Add project root to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../..'))

class BestTimeInference:
    """
    Inference Engine for Best Time to Post Recommendation using NeuralProphet.
    """
    
    def __init__(self, model_path=None):
        if model_path is None:
            # Default to PKL as NP's ONNX support is experimental
            model_path = os.path.join(os.path.dirname(__file__), '../../../models/best_time/neuralprophet_model.pkl')
            
        self.model_path = model_path
        self.model = None
        
    def load_model(self):
        """Load trained NeuralProphet model"""
        if not os.path.exists(self.model_path):
            raise FileNotFoundError(f"Model not found at: {self.model_path}")
            
        logger.info(f"Loading NeuralProphet model from: {self.model_path}")
        self.model = joblib.load(self.model_path)
        
    def predict_next_24_hours(self, category: str, base_date: datetime = None):
        """
        Predict interest scores for the next 24 hours.
        """
        if self.model is None:
            self.load_model()
            
        if base_date is None:
            base_date = datetime.now()
            
        # NeuralProphet requires creating a future dataframe
        # We need to construct a dataframe with 'ds' and 'ID'
        
        # 1. Create future periods
        # We want forecasts for tomorrow (starting 00:00)
        target_date = base_date + timedelta(days=1)
        start_time = target_date.replace(hour=0, minute=0, second=0, microsecond=0)
        
        future_periods = 24
        freq = "H"
        
        # Create a dummy DF with the last known point to allow NP to extend it?
        # Or use make_future_dataframe if available in this NP version.
        # Simpler: Create a distinct dataframe for inference.
        
        timestamps = [start_time + timedelta(hours=i) for i in range(future_periods)]
        
        df_future = pd.DataFrame({
            'ds': timestamps,
            'y': [None] * future_periods, # Dummy
            'ID': [category] * future_periods
        })
        
        # Predict
        forecast = self.model.predict(df_future)
        
        # forecast contains 'ds', 'yhat1' (prediction), etc.
        return forecast
        
    def get_best_window(self, category: str, window_size: int = 3):
        """
        Find the best posting window.
        Returns the start hour and end hour of the best N-hour window.
        """
        forecast = self.predict_next_24_hours(category)
        
        # Extract predictions
        # NeuralProphet 0.7+ usually puts prediction in 'yhat1'
        scores = forecast['yhat1'].fillna(0).values
        timestamps = forecast['ds'].dt.hour.values
        
        if len(scores) < window_size:
            logger.warning("Not enough data to find best window")
            return None
            
        best_score = -float('inf')
        best_start_idx = -1
        
        # Sliding window sum
        for i in range(len(scores) - window_size + 1):
            window_score = np.sum(scores[i : i + window_size])
            if window_score > best_score:
                best_score = window_score
                best_start_idx = i
                
        if best_start_idx == -1:
            return None
            
        best_start_hour = timestamps[best_start_idx]
        best_end_hour = (best_start_hour + window_size) % 24
        
        avg_score_in_window = best_score / window_size
        
        return {
            "category": category,
            "best_window_start": int(best_start_hour),
            "best_window_end": int(best_end_hour),
            "window_size": window_size,
            "score": float(best_score),
            "avg_interest": float(avg_score_in_window),
            "target_date": forecast['ds'].iloc[0].date().isoformat()
        }

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Predict Best Time to Post (NeuralProphet)")
    parser.add_argument("--category", type=str, required=True, help="Category name")
    parser.add_argument("--window", type=int, default=3, help="Window size in hours (default: 3)")
    
    args = parser.parse_args()
    
    predictor = BestTimeInference()
    
    try:
        result = predictor.get_best_window(args.category, args.window)
        
        if result:
            print("\n" + "="*50)
            print(f"BEST TIME RECOMMENDATION ({result['target_date']})")
            print("="*50)
            print(f"Category  : {result['category']}")
            print(f"Window    : {result['best_window_start']:02d}:00 - {result['best_window_end']:02d}:00")
            print(f"Index Score: {result['avg_interest']:.2f} (Predicted Interest)")
            print("="*50 + "\n")
        else:
            logger.error("Failed to generate recommendation")
        
    except Exception as e:
        logger.error(f"Prediction failed: {e}")

import onnxruntime as ort
import numpy as np
import joblib
import os
import logging
from pydantic import BaseModel, Field, validator
from typing import List, Dict, Any

# Custom exceptions
class ModelLoadError(Exception):
    """Load failed"""
    pass

class PreprocessingError(Exception):
    """Preprocessing failed"""
    pass

class InferenceError(Exception):
    """Inference failed"""
    pass

# Validation model
class InferenceInput(BaseModel):
    data: List[float] = Field(..., description="14d interest data", min_items=14, max_items=14)
    
    @validator('data')
    def check_values(cls, v):
        if any(x < 0 for x in v):
            raise ValueError("Negative values")
        return v

class LSTMDailyInference:
    """LSTM daily inference engine."""
    
    def __init__(self, model_path: str, scaler_path: str, lookback: int = 14):
        """Init engine."""
        self.lookback = lookback
        self.logger = logging.getLogger(__name__)
        
        # Check files
        if not os.path.exists(model_path):
            self.logger.error(f"Missing model: {model_path}")
            raise ModelLoadError(f"Missing model: {model_path}")
        
        if not os.path.exists(scaler_path):
            self.logger.error(f"Missing scaler: {scaler_path}")
            raise ModelLoadError(f"Missing scaler: {scaler_path}")

        # Load session
        try:
            self.session = ort.InferenceSession(model_path)
            self.input_name = self.session.get_inputs()[0].name
            self.output_name = self.session.get_outputs()[0].name
            self.logger.info("Model loaded")
        except Exception as e:
            self.logger.critical(f"Session failed: {str(e)}")
            raise ModelLoadError(f"Session failed: {str(e)}")

        # Load scaler
        try:
            self.scaler = joblib.load(scaler_path)
            self.logger.info("Scaler loaded")
        except Exception as e:
            self.logger.critical(f"Scaler failed: {str(e)}")
            raise ModelLoadError(f"Scaler failed: {str(e)}")

    def preprocess(self, input_data: List[float]) -> np.ndarray:
        """Prepare input."""
        try:
            # Flatten data
            data = np.array(input_data).flatten()
            
            if len(data) != self.lookback:
                raise ValueError(f"Valid length: {self.lookback}")
                
            # Reshape scaler
            data_reshaped = data.reshape(-1, 1)
            
            # Scale data
            scaled_data = self.scaler.transform(data_reshaped)
            
            # Reshape tensor
            input_tensor = scaled_data.reshape(1, self.lookback, 1).astype(np.float32)
            
            return input_tensor
            
        except Exception as e:
            self.logger.error(f"Prep error: {str(e)}")
            raise PreprocessingError(f"Prep error: {str(e)}")

    def predict(self, input_data: List[float]) -> Dict[str, Any]:
        """Run predictions."""
        # Validate schema
        try:
            validated_input = InferenceInput(data=input_data)
        except Exception as e:
            self.logger.warning(f"Invalid input: {str(e)}")
            raise ValueError(f"Invalid input: {str(e)}")

        # Run prep
        input_tensor = self.preprocess(validated_input.data)
        
        # Run inference
        try:
            outputs = self.session.run([self.output_name], {self.input_name: input_tensor})
            raw_output = outputs[0]
        except Exception as e:
            self.logger.error(f"Inference failed: {str(e)}")
            raise InferenceError(f"Inference failed: {str(e)}")
        
        # Run postprocess
        try:
            raw_output_reshaped = raw_output.reshape(-1, 1)
            actual_output = self.scaler.inverse_transform(raw_output_reshaped)
            
            # Clip negative
            actual_output = np.maximum(actual_output, 0)

            return {
                "status": "success",
                "forecast_scaled": raw_output.flatten().tolist(),
                "forecast_values": actual_output.flatten().tolist()
            }
        except Exception as e:
            self.logger.error(f"Post error: {str(e)}")
            raise PreprocessingError(f"Post error: {str(e)}")

if __name__ == "__main__":
    # Test run
    logging.basicConfig(level=logging.INFO)
    
    MODEL_PATH = '../models/daily/lstm/onnx/best_time_lstm.onnx'
    SCALER_PATH = '../models/daily/lstm/onnx/minmax_scaler.pkl'
    
    if os.path.exists(MODEL_PATH) and os.path.exists(SCALER_PATH):
        try:
            inference = LSTMDailyInference(MODEL_PATH, SCALER_PATH)
            dummy_input = [float(i) for i in range(14)]
            result = inference.predict(dummy_input)
            print(result)
        except Exception as e:
            print(f"Error: {e}")

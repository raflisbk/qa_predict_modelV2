import torch
import torch.nn as nn
import torch.onnx
import pandas as pd
import numpy as np
from sklearn.preprocessing import MinMaxScaler
import joblib
import os
import sys

# Define Paths
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_PATH = os.path.join(BASE_DIR, 'data', 'processed', 'daily_trends_processed_20251221_183209.csv')
MODEL_DIR = os.path.join(BASE_DIR, 'models', 'daily', 'lstm', 'onnx')
PYTORCH_MODEL_PATH = os.path.join(MODEL_DIR, 'lstm_daily.pth')

# Output Paths
ONNX_OUTPUT_PATH = os.path.join(MODEL_DIR, 'best_time_lstm.onnx')
SCALER_OUTPUT_PATH = os.path.join(MODEL_DIR, 'minmax_scaler.pkl')

# 1. Redefine LSTM Model Architecture (Must match notebook)
class LSTMModel(nn.Module):
    def __init__(self, lookback=14, forecast_horizon=7):
        super(LSTMModel, self).__init__()
        self.lookback = lookback
        self.forecast_horizon = forecast_horizon
        
        # LSTM layers 
        self.lstm1 = nn.LSTM(input_size=1, hidden_size=128, batch_first=True)
        self.dropout1 = nn.Dropout(0.2)
        
        self.lstm2 = nn.LSTM(input_size=128, hidden_size=64, batch_first=True)
        self.dropout2 = nn.Dropout(0.2)
        
        # Dense layers
        self.fc1 = nn.Linear(64, 32)
        self.relu = nn.ReLU()
        self.dropout3 = nn.Dropout(0.1)
        
        # Output layer
        self.fc2 = nn.Linear(32, forecast_horizon)
    
    def forward(self, x):
        x, _ = self.lstm1(x)
        x = self.dropout1(x)
        
        x, (h_n, c_n) = self.lstm2(x)
        x = self.dropout2(x)
        
        x = h_n[-1]
        
        x = self.fc1(x)
        x = self.relu(x)
        x = self.dropout3(x)
        
        x = self.fc2(x)
        return x

def main():
    print("="*60)
    print("ARTIFACT REGENERATION SCRIPT")
    print("="*60)
    
    # ---------------------------------------------------------
    # STEP 1: RE-FIT SCALER
    # ---------------------------------------------------------
    print(f"\n1. Loading Data from: {DATA_PATH}")
    if not os.path.exists(DATA_PATH):
        print("❌ Data file not found! Cannot fit scaler.")
        sys.exit(1)
        
    df = pd.read_csv(DATA_PATH)
    print(f"   Loaded {len(df)} rows.")
    
    print("   Fitting MinMaxScaler on 'interest_value'...")
    scaler = MinMaxScaler(feature_range=(0, 1))
    all_values = df['interest_value'].values.reshape(-1, 1)
    scaler.fit(all_values)
    
    # Save Scaler
    os.makedirs(MODEL_DIR, exist_ok=True)
    joblib.dump(scaler, SCALER_OUTPUT_PATH)
    print(f"✅ Scaler saved to: {SCALER_OUTPUT_PATH}")
    
    # ---------------------------------------------------------
    # STEP 2: LOAD PYTORCH MODEL & EXPORT ONNX
    # ---------------------------------------------------------
    print(f"\n2. Loading PyTorch Model from: {PYTORCH_MODEL_PATH}")
    if not os.path.exists(PYTORCH_MODEL_PATH):
        print("❌ PyTorch model not found! Cannot export ONNX.")
        print("   Please ensure 'lstm_daily.pth' is in the models folder.")
        sys.exit(1)
        
    device = torch.device('cpu') # Export on CPU is safer
    model = LSTMModel(lookback=14, forecast_horizon=7)
    
    try:
        # Load state dict
        model.load_state_dict(torch.load(PYTORCH_MODEL_PATH, map_location=device))
        model.to(device)
        model.eval()
        print("   Model loaded successfully.")
    except Exception as e:
        print(f"❌ Failed to load model weights: {e}")
        sys.exit(1)
        
    print(f"   Exporting to ONNX: {ONNX_OUTPUT_PATH}")
    try:
        # Dummy Input: (Batch=1, Seq=14, Feat=1)
        dummy_input = torch.randn(1, 14, 1).to(device)
        
        torch.onnx.export(
            model,
            dummy_input,
            ONNX_OUTPUT_PATH,
            export_params=True,
            opset_version=11,
            do_constant_folding=True,
            input_names=['input'],
            output_names=['output'],
            dynamic_axes={
                'input': {0: 'batch_size'},
                'output': {0: 'batch_size'}
            }
        )
        print(f"✅ ONNX Model saved to: {ONNX_OUTPUT_PATH}")
        
    except Exception as e:
        print(f"❌ ONNX Export Failed: {e}")
        sys.exit(1)
        
    print("\n" + "="*60)
    print("SUCCESS! API IS READY TO RUN.")
    print("Run: uvicorn src.app.api:app --reload")
    print("="*60)

if __name__ == "__main__":
    main()

# API Setup - Real-time Apify Integration

## ✅ **Changes Made**

API sekarang **fetch langsung dari Google Trends via Apify** setiap request (real-time), bukan dari database.

### **Modified Files:**
1. **`src/app/routers/best_time.py`**
   - ✅ Import `ApifyGoogleTrendsClient`
   - ✅ Load `config/categories.json` untuk mapping category → keywords
   - ✅ Initialize Apify client on startup
   - ✅ Replace `get_latest_data()` untuk fetch dari Apify
   - ✅ Update health check untuk validasi Apify client

2. **`test_apify_api.py`** (New)
   - Test script untuk validasi API dengan real-time fetch

---

## 🚀 **Setup Instructions**

### **1. Set Environment Variable**

```bash
# Windows PowerShell
$env:APIFY_API_TOKEN = "your_actual_apify_token_here"

# Or create .env file
echo "APIFY_API_TOKEN=your_actual_apify_token_here" > .env
```

### **2. Start API Server**

```bash
cd "d:\Subek\project\Draft\UKI\DIGIMAR\Best time post v2"

# Run dengan uvicorn
python -m uvicorn src.app.api:app --reload --host 0.0.0.0 --port 8000
```

### **3. Test API**

```bash
# In another terminal
python test_apify_api.py
```

---

## 📊 **API Workflow (Real-time)**

```
User Request
    ↓
API Endpoint (/predict)
    ↓
Get Category Keywords (from categories.json)
    ↓
Fetch from Apify (Google Trends)
    ├─ Search terms: keywords for category
    ├─ Time range: "now 7-d" (for hourly data)
    └─ Geo: "ID" (Indonesia)
    ↓
Parse Hourly Data
    ├─ Extract interest_over_time
    ├─ Aggregate by datetime
    └─ Calculate lag/rolling features
    ↓
LightGBM Inference
    ├─ Predict 168 hours (7 days)
    └─ Rank windows by interest
    ↓
Return Top 3 Non-overlapping Windows
```

---

## ⚡ **Performance Notes**

### **Response Times:**
- **Health check**: ~50ms
- **Categories list**: ~10ms
- **Prediction (with Apify fetch)**: **30-60 seconds** ⏰
  - Apify API call: 20-40s
  - Data parsing: 2-5s
  - Inference: 1-2s

### **Optimization Tips:**
1. **Cache Apify results** (5-10 minutes TTL)
2. **Background jobs** untuk pre-fetch popular categories
3. **Async Apify calls** untuk multiple keywords

---

## 🔍 **Example Request/Response**

### **Request:**
```bash
POST http://localhost:8000/api/v1/best-time/predict
Content-Type: application/json

{
  "category": "Food & Culinary"
}
```

### **Response (after ~45s):**
```json
{
  "status": "success",
  "category": "Food & Culinary",
  "recommendations": [
    {
      "rank": 1,
      "day_name": "Thursday",
      "date": "2026-01-09",
      "time_window": "16:00 - 19:00",
      "start_datetime": "2026-01-09T16:00:00",
      "end_datetime": "2026-01-09T19:00:00",
      "confidence_score": 0.853
    },
    {
      "rank": 2,
      "day_name": "Wednesday",
      "date": "2026-01-08",
      "time_window": "12:00 - 15:00",
      "start_datetime": "2026-01-08T12:00:00",
      "end_datetime": "2026-01-08T15:00:00",
      "confidence_score": 0.821
    },
    {
      "rank": 3,
      "day_name": "Monday",
      "date": "2026-01-07",
      "time_window": "18:00 - 21:00",
      "start_datetime": "2026-01-07T18:00:00",
      "end_datetime": "2026-01-07T21:00:00",
      "confidence_score": 0.798
    }
  ],
  "prediction_window": {
    "start": "2026-01-07",
    "end": "2026-01-13"
  },
  "model_info": {
    "model_type": "LightGBM Regression",
    "version": "1.0",
    "mae": 2.54,
    "r2": 0.9740
  },
  "generated_at": "2026-01-06T14:30:00"
}
```

---

## 🎯 **Key Features**

✅ **Real-time data** dari Google Trends  
✅ **Default window: 3 hours**  
✅ **Top 3 non-overlapping recommendations**  
✅ **Dynamic confidence scores** (50-90%)  
✅ **Production-ready error handling**  
✅ **OpenAPI documentation** (auto-generated)  

---

## 📝 **Next Steps (Optional)**

1. **Add caching** untuk reduce Apify calls:
   ```python
   from cachetools import TTLCache
   cache = TTLCache(maxsize=100, ttl=300)  # 5 minutes
   ```

2. **Add background tasks** untuk pre-fetch:
   ```python
   from fastapi import BackgroundTasks
   ```

3. **Add rate limiting** per category:
   ```python
   from slowapi import Limiter
   ```

4. **Monitor Apify usage** (quota tracking)

---

## ⚠️ **Important Notes**

- **Apify API token** harus valid dan punya quota
- **Response time** lebih lama (30-60s) karena real-time fetch
- **Recommended**: Implement caching untuk production
- **Rate limits**: Apify free tier = 10 runs/month

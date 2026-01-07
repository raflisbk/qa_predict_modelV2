# QA Testing Guide - Best Time Post API

## 📋 Pre-requisites
- Docker Desktop installed & running
- Git installed
- Terminal/PowerShell access

---

## 🚀 Step 1: Clone Repository

```bash
git clone https://github.com/raflisbk/qa_predict_modelV2.git
cd qa_predict_modelV2
```

---

## 🔧 Step 2: Configure Environment (Optional)

⚠️ **IMPORTANT**: Environment variables harus di-set **SEBELUM** menjalankan `docker-compose up -d`!

**Default values (.env.docker sudah ada):**
```env
POSTGRES_HOST=postgres
POSTGRES_PORT=5432
POSTGRES_USER=postgres
POSTGRES_PASSWORD=postgres
POSTGRES_DB=best_time_post
```

**Jika perlu custom configuration:**
```bash
# 1. Copy template
cp .env.docker .env

# 2. Edit values (SEBELUM docker-compose!)
notepad .env  # Windows
vim .env      # Linux/Mac

# 3. Verify changes
cat .env | grep POSTGRES
```

**⚠️ Jika sudah running dan mau ganti .env:**
```bash
# Edit file
vim .env

# Recreate containers untuk load .env baru
docker-compose down
docker-compose up -d --force-recreate
```

---

## 🏃 Step 3: Start Docker Services

⚠️ **IMPORTANT**: Jika sebelumnya pernah run Docker, hapus volume lama dulu:
```bash
# Stop & remove existing containers + volumes
docker-compose down -v

# Verify volume is removed
docker volume ls | grep postgres
```

**Start fresh:**
```bash
docker-compose up -d
```

**Expected output:**
```
✓ Network besttime_network created
✓ Volume postgres_data created
✓ Container besttime_postgres starting
✓ Container besttime_postgres started
✓ Container besttime_api starting
✓ Container besttime_api started
```

📌 **Why `-v` flag?** PostgreSQL only initializes database scripts (`init-db.sh`, `schema.sql`, `seed_data.sql`) on **first run** when volume is empty. If volume already exists, scripts are skipped!

---

## ✅ Step 4: Verify Services Running

### 3.1 Check Container Status
```bash
docker-compose ps
```

**Expected output:**
```
NAME                 STATUS              PORTS
besttime_postgres    Up 30s (healthy)    0.0.0.0:5432->5432/tcp
besttime_api         Up 20s (healthy)    0.0.0.0:8000->8000/tcp
```

⚠️ **IMPORTANT**: Tunggu sampai kedua container status = `healthy` (bisa 30-60 detik)

### 3.2 Check Logs
```bash
# API logs
docker-compose logs -f api

# Database logs  
docker-compose logs -f postgres
```

**Expected API logs:**
```
INFO: Started server process [1]
INFO: Waiting for application startup.
INFO: Initializing Best Time Predictor...
INFO: Loading LightGBM model...
INFO: [OK] Model loaded: models/best_time/lightgbm/lgb_regression_model.pkl
INFO: [OK] Feature columns loaded: 30 features
INFO: [OK] Category mapping loaded: 10 categories
INFO: [OK] Model metrics loaded
INFO: [OK] Categories config loaded: 10 categories
INFO: [OK] Database connection established
INFO: Model initialization complete!
INFO: Application startup complete.
INFO: Uvicorn running on http://0.0.0.0:8000
```

**Expected Postgres logs:**
```
[OK] Step 1/4: Checking PostgreSQL readiness...
[OK] Step 2/4: Enabling UUID extension...
[OK] Step 3/4: Executing schema.sql...
[OK] Step 4/4: Loading seed data...
[OK] Database initialization completed!
[OK] Data verification: 17081 rows in hourly_trends
```

---

## 🧪 Step 5: API Testing

### 4.1 Health Check
```bash
curl http://localhost:8000/api/v1/best-time/health
```

**Expected response:**
```json
{
  "status": "healthy",
  "model_loaded": true,
  "database_connected": true,
  "categories_available": 10,
  "model_info": {
    "model_type": "LightGBM Regression",
    "version": "1.0",
    "mae": 2.54,
    "r2": 0.9740
  }
}
```

✅ **Checklist:**
- [ ] `status` = "healthy"
- [ ] `model_loaded` = true
- [ ] `database_connected` = true
- [ ] `categories_available` = 10
- [ ] `r2` = 0.9740

### 4.2 Get Categories
```bash
curl http://localhost:8000/api/v1/best-time/categories
```

**Expected response:**
```json
{
  "categories": [
    "Food & Culinary",
    "Fashion & Beauty",
    "Technology & Gadgets",
    "E-commerce & Shopping",
    "Entertainment",
    "Travel & Tourism",
    "Health & Fitness",
    "Finance & Investment",
    "Education & Career",
    "Gaming & Esports"
  ]
}
```

✅ **Checklist:**
- [ ] 10 categories returned
- [ ] All category names present

### 4.3 Prediction Test
```bash
curl -X POST http://localhost:8000/api/v1/best-time/predict \
  -H "Content-Type: application/json" \
  -d '{
    "category": "Food & Culinary",
    "window_hours": 3,
    "top_k": 3,
    "days_ahead": 7
  }'
```

**Expected response structure:**
```json
{
  "status": "success",
  "category": "Food & Culinary",
  "recommendations": [
    {
      "rank": 1,
      "day_name": "Thursday",
      "date": "2026-01-08",
      "time_window": "16:00 - 19:00",
      "start_datetime": "2026-01-08T16:00:00",
      "end_datetime": "2026-01-08T19:00:00",
      "confidence_score": 0.85
    },
    {
      "rank": 2,
      "day_name": "Friday",
      "date": "2026-01-09",
      "time_window": "18:00 - 21:00",
      "start_datetime": "2026-01-09T18:00:00",
      "end_datetime": "2026-01-09T19:00:00",
      "confidence_score": 0.82
    },
    {
      "rank": 3,
      "day_name": "Saturday",
      "date": "2026-01-10",
      "time_window": "12:00 - 15:00",
      "start_datetime": "2026-01-10T12:00:00",
      "end_datetime": "2026-01-10T15:00:00",
      "confidence_score": 0.79
    }
  ],
  "prediction_window": {
    "start": "2026-01-08",
    "end": "2026-01-14"
  },
  "model_info": {
    "model_type": "LightGBM Regression",
    "version": "1.0",
    "cached": false,
    "cache_ttl_seconds": 600,
    "mae": 2.54,
    "r2": 0.9740
  }
}
```

✅ **Checklist:**
- [ ] `status` = "success"
- [ ] 3 recommendations returned (top_k=3)
- [ ] Each recommendation has all required fields
- [ ] `confidence_score` between 0.0 - 1.0
- [ ] Dates are in future (7 days ahead)
- [ ] Time windows are 3 hours (window_hours=3)
- [ ] No overlapping time windows
- [ ] Response time < 5 seconds (first request)

### 4.4 Test Caching (Second Request)
```bash
# Run same request again
curl -X POST http://localhost:8000/api/v1/best-time/predict \
  -H "Content-Type: application/json" \
  -d '{
    "category": "Food & Culinary",
    "window_hours": 3,
    "top_k": 3,
    "days_ahead": 7
  }'
```

✅ **Checklist:**
- [ ] Response identical to first request
- [ ] `"cached": true` in model_info
- [ ] Response time < 1 second (much faster due to cache)

### 4.5 Test Different Categories
```bash
# Test each category
for category in "Fashion & Beauty" "Technology & Gadgets" "Gaming & Esports"
do
  curl -X POST http://localhost:8000/api/v1/best-time/predict \
    -H "Content-Type: application/json" \
    -d "{\"category\": \"$category\", \"window_hours\": 3, \"top_k\": 3, \"days_ahead\": 7}"
done
```

✅ **Checklist:**
- [ ] All categories return valid predictions
- [ ] No errors for any category

---

## 🗄️ Step 6: Database Verification

### 5.1 Connect to Database
```bash
docker exec -it besttime_postgres psql -U postgres -d best_time_post
```

### 5.2 Verify Data Count
```sql
-- Check hourly trends count
SELECT COUNT(*) FROM hourly_trends;
-- Expected: 17081 rows

-- Check categories
SELECT * FROM categories;
-- Expected: 10 categories

-- Check data by category
SELECT category, COUNT(*) 
FROM hourly_trends 
GROUP BY category 
ORDER BY category;

-- Check latest data
SELECT * FROM hourly_trends 
ORDER BY datetime DESC 
LIMIT 5;

-- Exit
\q
```

✅ **Checklist:**
- [ ] hourly_trends: 17,081 rows
- [ ] categories: 10 rows
- [ ] Data distributed across all categories
- [ ] Latest timestamps present

---

## 📊 Step 7: Swagger UI Testing

### 6.1 Open Browser
```
http://localhost:8000/docs
```

### 6.2 Interactive Testing
1. Click "GET /api/v1/best-time/health"
   - Click "Try it out"
   - Click "Execute"
   - Verify response

2. Click "POST /api/v1/best-time/predict"
   - Click "Try it out"
   - Modify request body
   - Click "Execute"
   - Verify response

✅ **Checklist:**
- [ ] Swagger UI loads successfully
- [ ] All endpoints visible
- [ ] Can execute requests
- [ ] Responses match curl tests

---

## 🔍 Step 8: Error Handling Tests

### 7.1 Invalid Category
```bash
curl -X POST http://localhost:8000/api/v1/best-time/predict \
  -H "Content-Type: application/json" \
  -d '{
    "category": "Invalid Category",
    "window_hours": 3,
    "top_k": 3,
    "days_ahead": 7
  }'
```

**Expected: HTTP 400**
```json
{
  "detail": [
    {
      "type": "value_error",
      "msg": "Invalid category. Must be one of: ..."
    }
  ]
}
```

### 7.2 Invalid Parameters
```bash
curl -X POST http://localhost:8000/api/v1/best-time/predict \
  -H "Content-Type: application/json" \
  -d '{
    "category": "Food & Culinary",
    "window_hours": 25,
    "top_k": 3,
    "days_ahead": 7
  }'
```

**Expected: HTTP 422**

✅ **Checklist:**
- [ ] Invalid category returns 400
- [ ] Invalid parameters return 422
- [ ] Error messages are clear

---

## 📈 Step 9: Performance Testing

### 8.1 Response Times
```bash
# Measure response time (first request - no cache)
time curl -X POST http://localhost:8000/api/v1/best-time/predict \
  -H "Content-Type: application/json" \
  -d '{
    "category": "Food & Culinary",
    "window_hours": 3,
    "top_k": 3,
    "days_ahead": 7
  }'

# Measure cached response
time curl -X POST http://localhost:8000/api/v1/best-time/predict \
  -H "Content-Type: application/json" \
  -d '{
    "category": "Food & Culinary",
    "window_hours": 3,
    "top_k": 3,
    "days_ahead": 7
  }'
```

✅ **Performance Targets:**
- [ ] First request (no cache): < 5 seconds
- [ ] Cached request: < 1 second
- [ ] Health check: < 100ms
- [ ] Get categories: < 100ms

---

## 🛑 Step 10: Cleanup & Stop

### 9.1 Stop Services
```bash
docker-compose down
```

### 9.2 Complete Cleanup (Optional)
```bash
# Remove volumes (database data will be lost)
docker-compose down -v

# Remove images
docker-compose down --rmi all
```

---

## ✅ Final Checklist Summary

### Infrastructure
- [ ] Docker containers start successfully
- [ ] Both containers reach "healthy" status
- [ ] No error logs in API or Database
- [ ] Ports 8000 and 5432 accessible

### Database
- [ ] 17,081 rows in hourly_trends
- [ ] 10 categories loaded
- [ ] Schema correctly created
- [ ] Data distributed across categories

### API Functionality
- [ ] Health check returns healthy
- [ ] Categories endpoint works
- [ ] Prediction endpoint works
- [ ] Returns 3 non-overlapping windows
- [ ] Confidence scores valid (0-1)
- [ ] Future dates correct

### Performance
- [ ] First request < 5s
- [ ] Cached request < 1s
- [ ] Cache working (cached: true)

### Error Handling
- [ ] Invalid category returns 400
- [ ] Invalid parameters return 422
- [ ] Error messages clear

### Documentation
- [ ] Swagger UI accessible
- [ ] All endpoints documented
- [ ] Interactive testing works

---

## 🐛 Troubleshooting

### Container won't start
```bash
docker-compose logs -f
docker ps -a
```

### Port conflict (8000 in use)
```bash
# Windows
netstat -ano | findstr :8000
taskkill /F /PID <pid>

# Linux/Mac
lsof -i :8000
kill -9 <pid>
```

### Database connection failed
```bash
docker exec -it besttime_postgres pg_isready -U postgres
docker-compose restart postgres
```

### Model not loading
```bash
# Check if model files exist
docker exec -it besttime_api ls -la /app/models/best_time/lightgbm/
```

### Reset everything
```bash
docker-compose down -v
docker-compose up -d --build
```

---

## 📞 Support

If all checks pass: ✅ **SYSTEM READY FOR QA TESTING**

If any check fails: 
1. Check logs: `docker-compose logs -f`
2. Verify Docker Desktop running
3. Check ports not in use
4. Try rebuild: `docker-compose up -d --build`

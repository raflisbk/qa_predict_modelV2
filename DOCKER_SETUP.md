# Best Time Post API - Docker Setup

Complete Docker environment untuk QA testing dengan database dan API yang sudah ter-configure.

## 🚀 Quick Start (Plug & Play)

### Prerequisites
- Docker Desktop installed
- Docker Compose v2.x

### Cara Menjalankan

1. **Clone repository dan masuk ke direktori:**
```bash
cd "Best time post v2"
```

2. **Start semua services:**
```bash
docker-compose up -d
```

3. **Cek status services:**
```bash
docker-compose ps
```

4. **Akses API:**
- API Docs: http://localhost:8000/docs
- Health Check: http://localhost:8000/api/v1/best-time/health
- Database: localhost:5432

### Stop Services
```bash
docker-compose down
```

### Reset Everything (clean start)
```bash
docker-compose down -v  # Hapus volumes juga
docker-compose up -d
```

---

## 📦 Yang Sudah Include

### ✅ API Service (Port 8000)
- FastAPI application
- LightGBM model (R² 97.4%)
- Semua Python dependencies
- Cache system (10 min TTL)
- Error handling & logging

### ✅ PostgreSQL Database (Port 5432)
- PostgreSQL 15
- Schema lengkap (categories, hourly_trends, dll)
- **Seed data** (semua data historical)
- Auto-initialization scripts

### ✅ Models & Config
- Pre-trained LightGBM model
- Feature columns (30 features)
- Category mappings (10 categories)
- Keywords configuration

---

## 🧪 Testing API

### 1. Health Check
```bash
curl http://localhost:8000/api/v1/best-time/health
```

### 2. Get Categories
```bash
curl http://localhost:8000/api/v1/best-time/categories
```

### 3. Predict Best Time
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

### 4. Via Swagger UI
Buka browser: http://localhost:8000/docs

---

## 📊 Database Access

### Connect ke database:
```bash
docker exec -it besttime_postgres psql -U postgres -d best_time_post
```

### Query examples:
```sql
-- Check categories
SELECT * FROM categories;

-- Check hourly trends (latest)
SELECT * FROM hourly_trends 
ORDER BY datetime DESC 
LIMIT 10;

-- Check data count by category
SELECT category, COUNT(*) 
FROM hourly_trends 
GROUP BY category;
```

---

## 🔧 Troubleshooting

### Logs
```bash
# API logs
docker-compose logs -f api

# Database logs
docker-compose logs -f postgres

# All logs
docker-compose logs -f
```

### Rebuild after code changes
```bash
docker-compose down
docker-compose build --no-cache
docker-compose up -d
```

### Port conflict (8000 already in use)
```bash
# Stop local server first
Stop-Process -Name python -Force

# Or change port in docker-compose.yml:
ports:
  - "8001:8000"  # Use 8001 instead
```

---

## 📁 Structure

```
Best time post v2/
├── docker-compose.yml      # Docker orchestration
├── Dockerfile              # API container image
├── .env.docker             # Environment variables
├── api_start.py           # API entry point
├── requirements.txt       # Python dependencies
├── models/                # ML models (mounted as volume)
│   └── best_time/
│       └── lightgbm/
├── config/                # Configuration files
│   └── categories.json
├── database/              # DB initialization
│   ├── schema.sql        # Database schema
│   ├── seed_data.sql     # Historical data
│   └── init-db.sh        # Init script
└── src/                   # Application code
    ├── app/
    │   └── routers/
    │       └── best_time.py
    └── database/
        └── db_manager.py
```

---

## ⚙️ Configuration

### Environment Variables (.env.docker)

```env
# Database
POSTGRES_HOST=postgres
POSTGRES_PORT=5432
POSTGRES_USER=postgres
POSTGRES_PASSWORD=postgres
POSTGRES_DB=best_time_post

# API
API_HOST=0.0.0.0
API_PORT=8000

# Optional: Apify (for real-time data)
APIFY_API_TOKEN=your_token_here
```

### Custom Configuration

Edit `docker-compose.yml` untuk customize:
- Ports
- Memory limits
- Environment variables
- Volume mappings

---

## 🎯 Expected Results

### Successful Startup:
```
✓ Network besttime_network created
✓ Volume postgres_data created
✓ Container besttime_postgres started (healthy)
✓ Container besttime_api started (healthy)
```

### API Response (Health Check):
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

---

## 🔐 Security Notes

- Default credentials untuk development/QA
- Untuk production, ganti password di `.env.docker`
- Database tidak expose ke public (hanya localhost:5432)
- API CORS enabled untuk testing

---

## 📞 Support

Jika ada issue:
1. Check logs: `docker-compose logs -f`
2. Restart services: `docker-compose restart`
3. Clean restart: `docker-compose down -v && docker-compose up -d`

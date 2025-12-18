# Best Time Post v2 - ML Prediction Model

Prediksi waktu terbaik untuk posting konten berdasarkan Google Trends data menggunakan Machine Learning.

---

## 🚀 Quick Start untuk QA

**Setup database lokal dalam 3 langkah:**

```bash
# 1. Clone repository
git clone https://github.com/raflisbk/qa_predict_modelV2.git
cd qa_predict_modelV2

# 2. Setup environment
cp .env.example .env

# 3. Start database
docker-compose up -d

# 4. Verify (optional)
python scripts/verify_db.py
```

**Connect dengan DBeaver:**

- Host: `localhost`
- Port: `5432`
- Database: `best_time_post`
- User: `postgres`
- Password: `postgres`

📖 **[Panduan lengkap untuk QA →](docs/QA_SETUP.md)**

---

## 📋 Project Overview

Project ini menggunakan data Google Trends untuk memprediksi waktu posting terbaik untuk berbagai kategori konten di Indonesia.

### Features

- ✅ Automated data collection dari Google Trends (daily & hourly)
- ✅ Data preprocessing & cleaning pipeline
- ✅ Multiple ML models (Random Forest, XGBoost, Neural Networks)
- ✅ ONNX export untuk production deployment
- ✅ Comprehensive logging & monitoring
- ✅ Docker-based database setup

### Categories

10 kategori trending di Indonesia:

1. Fashion & Beauty
2. Food & Culinary
3. Technology & Gadgets
4. E-commerce & Shopping
5. Entertainment & K-Pop
6. Travel & Tourism
7. Health & Fitness
8. Finance & Investment
9. Education & Career
10. Gaming & Esports

---

## 🏗️ Project Structure

```
Best time post v2/
├── config/                 # Configuration files
│   └── categories.json     # Category definitions
├── data/                   # Data storage
├── data_collection/        # Data collection scripts
│   ├── collect_daily_data.py
│   ├── collect_hourly_data.py
│   └── test_fetch_*.py
├── database/               # Database schemas & scripts
│   ├── schema.sql          # PostgreSQL schema
│   ├── init-db.sh          # Docker init script
│   └── monitoring_queries.sql
├── docs/                   # Documentation
│   └── QA_SETUP.md         # QA setup guide
├── models/                 # Trained models
├── notebooks/              # Jupyter notebooks for experiments
├── scripts/                # Utility scripts
│   ├── init_db.py          # Manual DB initialization
│   └── verify_db.py        # DB verification
├── src/                    # Source code
│   ├── database/           # Database managers
│   ├── models/             # ML models
│   ├── preprocessing/      # Data preprocessing
│   └── utils/              # Utilities
├── tests/                  # Unit tests
├── docker-compose.yml      # Docker configuration
├── requirements.txt        # Python dependencies
└── .env.example            # Environment template
```

---

## 🛠️ Setup & Installation

### Prerequisites

- Python 3.9+
- Docker Desktop
- PostgreSQL client (DBeaver recommended)
- Git

### Installation

1. **Clone repository**

   ```bash
   git clone https://github.com/raflisbk/qa_predict_modelV2.git
   cd qa_predict_modelV2
   ```

2. **Setup Python environment**

   ```bash
   # Create virtual environment
   python -m venv venv

   # Activate (Windows)
   venv\Scripts\activate

   # Activate (Linux/Mac)
   source venv/bin/activate

   # Install dependencies
   pip install -r requirements.txt
   ```

3. **Setup environment variables**

   ```bash
   cp .env.example .env
   # Edit .env and add your APIFY_API_TOKEN
   ```

4. **Start database**

   ```bash
   docker-compose up -d

   # Verify
   python scripts/verify_db.py
   ```

---

## 📊 Database Schema

### Main Tables

- `categories` - Master kategori (10 categories)
- `daily_trends` - Data trends harian
- `hourly_trends` - Data trends per jam
- `related_topics` - Topik terkait
- `related_queries` - Query pencarian terkait
- `predictions` - Hasil prediksi model

### Logging Tables

- `collection_logs` - Log pengumpulan data
- `processing_logs` - Log preprocessing
- `training_logs` - Log training model
- `experiment_logs` - Log eksperimen Kaggle

### Test Tables

- `test_daily_trends`, `test_hourly_trends`, dll.
- `test_runs` - Metadata test runs

### Views

8 views untuk analisis:

- `v_daily_trends_analysis`
- `v_hourly_trends_analysis`
- `v_top_predictions`
- `v_pipeline_health`
- dll.

---

## 🔄 Data Collection

### Collect Daily Data

```bash
python data_collection/collect_daily_data.py
```

### Collect Hourly Data

```bash
python data_collection/collect_hourly_data.py
```

### Test Data Fetching

```bash
# Test daily data
python data_collection/test_fetch_daily.py

# Test hourly data
python data_collection/test_fetch_hourly.py
```

---

## 🤖 Model Training

```bash
# Train model
python src/models/train_model.py

# Evaluate model
python src/models/evaluate_model.py

# Export to ONNX
python src/models/export_onnx.py
```

---

## 🧪 Testing

```bash
# Run all tests
pytest tests/

# Run specific test
pytest tests/test_data_collection.py

# With coverage
pytest --cov=src tests/
```

---

## 📈 Monitoring

### Check Pipeline Health

```sql
SELECT * FROM v_pipeline_health;
```

### Check Recent Collections

```sql
SELECT * FROM collection_logs
ORDER BY started_at DESC
LIMIT 10;
```

### Check Model Performance

```sql
SELECT * FROM v_training_summary
ORDER BY started_at DESC;
```

---

## 🐳 Docker Commands

```bash
# Start services
docker-compose up -d

# Stop services
docker-compose stop

# View logs
docker-compose logs postgres

# Restart
docker-compose restart

# Fresh start (removes all data)
docker-compose down -v
docker-compose up -d
```

---

## 🔧 Troubleshooting

### Database Connection Issues

**Problem:** Cannot connect to database

**Solution:**

```bash
# Check container status
docker-compose ps

# Check logs
docker-compose logs postgres

# Restart
docker-compose restart

# Verify
python scripts/verify_db.py
```

### Tables Not Created

**Problem:** Tables don't exist after `docker-compose up`

**Solution:**

```bash
# Check initialization logs
docker-compose logs postgres | grep "INITIALIZATION"

# Should see: "DATABASE INITIALIZATION COMPLETED"

# If not, recreate:
docker-compose down -v
docker-compose up -d
```

### UUID Extension Error

**Problem:** `uuid_generate_v4() does not exist`

**Solution:**
This should NOT happen with Docker setup. If it does:

```bash
# Recreate database
docker-compose down -v
docker-compose up -d
```

### Port Already in Use

**Problem:** Port 5432 already in use

**Solution:**

```bash
# Edit .env
POSTGRES_PORT=5433

# Restart
docker-compose down
docker-compose up -d
```

---

## 📚 Documentation

- **[QA Setup Guide](docs/QA_SETUP.md)** - Detailed setup for QA team
- **[Database Schema](database/schema.sql)** - Complete database schema
- **[Monitoring Queries](database/monitoring_queries.sql)** - Useful queries

---

## 🤝 Contributing

1. Create feature branch
2. Make changes
3. Test thoroughly
4. Submit pull request

---

## 📝 Environment Variables

See [`.env.example`](.env.example) for all available variables.

**Required:**

- `APIFY_API_TOKEN` - For Google Trends data collection

**Database (default values work for Docker):**

- `POSTGRES_HOST=localhost`
- `POSTGRES_PORT=5432`
- `POSTGRES_DB=best_time_post`
- `POSTGRES_USER=postgres`
- `POSTGRES_PASSWORD=postgres`

---

## 📞 Support

Jika ada masalah:

1. **Check documentation:** [QA_SETUP.md](docs/QA_SETUP.md)
2. **Run verification:** `python scripts/verify_db.py`
3. **Check logs:** `docker-compose logs postgres`
4. **Contact dev team** dengan error message lengkap

---

## 📄 License

[Add your license here]

---

## 🎯 Roadmap

- [x] Data collection pipeline
- [x] Database schema & initialization
- [x] Docker setup
- [x] QA documentation
- [ ] Model training pipeline
- [ ] API deployment
- [ ] Web dashboard
- [ ] Automated scheduling

---

**Made with ❤️ for predicting best posting times**

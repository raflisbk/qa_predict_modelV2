# ✅ QA Setup Checklist

## Plug-and-Play Database Setup - Best Time Post v2

---

## 📋 Prerequisites

- [ ] Docker Desktop installed dan running
- [ ] Python 3.9+ installed
- [ ] DBeaver installed (atau PostgreSQL client lainnya)
- [ ] Git installed

---

## 🚀 Setup Steps (2 Menit)

### Step 1: Clone Repository

```bash
git clone https://github.com/raflisbk/qa_predict_modelV2.git
cd qa_predict_modelV2
```

- [ ] Repository cloned
- [ ] Masuk ke directory project

### Step 2: Setup Environment

```bash
copy .env.example .env
```

- [ ] File `.env` created
- [ ] **TIDAK PERLU EDIT APAPUN** (default settings sudah siap pakai)

### Step 3: Start Database

```bash
docker-compose up -d
```

- [ ] Command executed
- [ ] Tunggu 30-40 detik untuk initialization

### Step 4: Verify Setup

```bash
python scripts/verify_db.py
```

- [ ] Script executed
- [ ] Output menunjukkan: **`[SUCCESS] ALL CHECKS PASSED!`**

---

## 🔌 DBeaver Connection

### Connection Settings

```
Host:     localhost
Port:     5432
Database: best_time_post
Username: postgres
Password: postgres
```

### Verification Steps

- [ ] Create new PostgreSQL connection di DBeaver
- [ ] Input settings di atas
- [ ] Click "Test Connection" → Should show "Connected"
- [ ] Click "Finish"
- [ ] Expand connection → Schemas → public → Tables
- [ ] **Verify: 16 tables visible**
- [ ] Expand Views
- [ ] **Verify: 8 views visible**

### Test Query

```sql
SELECT * FROM categories;
```

- [ ] Query executed successfully
- [ ] **Verify: 10 rows returned**

---

## ✅ Success Indicators

### Docker Container

```bash
docker-compose ps
```

Expected output:

```
NAME         STATUS
besttimev2   Up (healthy)
```

- [ ] Container status is "healthy"

### Database Tables

Expected tables (16 total):

- [ ] categories
- [ ] daily_trends
- [ ] hourly_trends
- [ ] related_topics
- [ ] related_queries
- [ ] predictions
- [ ] collection_logs
- [ ] model_metrics
- [ ] processing_logs
- [ ] training_logs
- [ ] experiment_logs
- [ ] test_daily_trends
- [ ] test_hourly_trends
- [ ] test_related_topics
- [ ] test_related_queries
- [ ] test_runs

### Database Views

Expected views (8 total):

- [ ] v_daily_trends_analysis
- [ ] v_hourly_trends_analysis
- [ ] v_top_predictions
- [ ] v_processing_pipeline_status
- [ ] v_training_summary
- [ ] v_experiment_tracking
- [ ] v_pipeline_health
- [ ] v_test_runs_summary

### Initial Data

- [ ] 10 categories loaded (Fashion, Food, Technology, etc.)

---

## 🔧 Troubleshooting

### Problem: Port 5432 already in use

**Solution:**

1. Edit `.env` file
2. Change `POSTGRES_PORT=5432` to `POSTGRES_PORT=5433`
3. Restart: `docker-compose down && docker-compose up -d`
4. Update DBeaver connection to use port 5433

### Problem: Docker not running

**Solution:**

1. Open Docker Desktop
2. Wait until Docker is running
3. Retry `docker-compose up -d`

### Problem: Tables not created

**Solution:**

```bash
docker-compose down -v
docker-compose up -d
```

Wait 30 seconds, then verify again.

### Problem: Verification script fails

**Solution:**

1. Check container: `docker-compose ps`
2. Check logs: `docker-compose logs postgres`
3. Look for "DATABASE INITIALIZATION COMPLETED" message
4. If not found, restart: `docker-compose restart`

---

## 📚 Documentation

- **Quick Start:** [QUICK_START_QA.md](QUICK_START_QA.md)
- **Detailed Guide:** [docs/QA_SETUP.md](docs/QA_SETUP.md)
- **Summary:** [QA_READY_SUMMARY.md](QA_READY_SUMMARY.md)
- **Project README:** [README.md](README.md)

---

## 🎯 Automated Validation (Optional)

Untuk automated testing, run:

```powershell
.\scripts\qa_validate.ps1
```

Script ini akan:

- ✅ Check prerequisites
- ✅ Create .env if missing
- ✅ Start database
- ✅ Wait for initialization
- ✅ Run verification
- ✅ Show next steps

---

## ✅ Final Checklist

Setup berhasil jika semua ini ✅:

- [ ] `docker-compose up -d` berhasil tanpa error
- [ ] `docker-compose ps` menunjukkan status "healthy"
- [ ] `python scripts/verify_db.py` menunjukkan "ALL CHECKS PASSED"
- [ ] DBeaver bisa connect ke database
- [ ] Bisa lihat 16 tables di DBeaver
- [ ] Bisa lihat 8 views di DBeaver
- [ ] Query `SELECT * FROM categories;` return 10 rows

---

## 🎉 Setup Complete!

Jika semua checklist di atas ✅, database Anda **READY** untuk:

- Testing data collection scripts
- Running queries
- Development work
- Model training

**Total waktu setup: ~2 menit** ⚡

---

## 📞 Need Help?

Jika ada masalah:

1. Check [docs/QA_SETUP.md](docs/QA_SETUP.md) untuk troubleshooting detail
2. Check Docker logs: `docker-compose logs postgres`
3. Contact dev team dengan error message lengkap

---

**Last Updated:** 2025-12-18  
**Status:** ✅ READY FOR QA

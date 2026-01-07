# ✅ QA PLUG AND PLAY CHECKLIST

**Status:** Ready for deployment  
**Last Updated:** 2026-01-07  
**Repository:** https://github.com/raflisbk/qa_predict_modelV2

---

## 📋 Pre-Deployment Verification

### ✅ All Issues Fixed

1. ✅ **docker-compose.yml** - Clean, no merge conflicts
2. ✅ **requirements.txt** - Clean, 89 packages (no merge conflicts)
3. ✅ **database/init-db.sh** - NOW loads seed_data.sql automatically
4. ✅ **database/seed_data.sql** - 15.9 MB, 17,081 rows (tracked in Git)
5. ✅ **.env.docker** - Complete configuration template
6. ✅ **config/categories.json** - Tracked in Git
7. ✅ **config/indonesia_events.json** - Tracked in Git
8. ✅ **models/** - All required model files tracked

### ✅ Repository Status

```bash
✅ All critical files committed
✅ All changes pushed to origin/main
✅ Documentation complete:
   - QA_TESTING_GUIDE.md
   - TROUBLESHOOTING.md
   - DBEAVER_SETUP.md
   - DATABASE_INIT_FIX.md
   - FIX_QA_DOCKER_ISSUE.md
   - PLUG_AND_PLAY_CHECKLIST.md (this file)
```

---

## 🚀 QA Deployment Steps (Plug and Play)

### Step 1: Clone Repository
```bash
git clone https://github.com/raflisbk/qa_predict_modelV2.git
cd qa_predict_modelV2
```

### Step 2: Setup Environment
```bash
# Copy default Docker environment
cp .env.docker .env

# (Optional) Edit if needed
# notepad .env  # Windows
# vim .env      # Linux/Mac
```

**⚠️ IMPORTANT:** `.env` harus ada SEBELUM `docker-compose up`!

### Step 3: Start Services
```bash
# Clean start (recommended for first time)
docker-compose down -v  # Remove old volumes if exist
docker-compose up -d --build
```

### Step 4: Wait for Initialization
```bash
# Wait 90-120 seconds for:
# - Docker image build (first time: ~2-3 minutes)
# - PostgreSQL initialization
# - Schema creation
# - Seed data loading (17,081 rows)
# - API startup

# Watch logs (optional)
docker-compose logs -f postgres
```

### Step 5: Verify Deployment
```bash
# 1. Check containers running
docker-compose ps

# Expected output:
# NAME                STATUS
# besttime_postgres   Up (healthy)
# besttime_api        Up (healthy)

# 2. Check database data
docker exec -it besttime_postgres psql -U postgres -d best_time_post \
  -c "SELECT COUNT(*) FROM hourly_trends;"
# Expected: 17081

# 3. Check API health
curl http://localhost:8000/api/v1/best-time/health
# Expected: {"status":"healthy","database_connected":true}
```

**That's it!** ✅ Database akan otomatis terisi dengan **17,081 rows** identik dengan development environment.

---

## 📊 Expected Data After Deployment

### Database Tables (16 total)
- ✅ `categories` - 10 categories
- ✅ `hourly_trends` - **17,081 rows**
- ✅ `collection_logs` - 545 rows
- ✅ `daily_trends`
- ✅ `predictions`
- ✅ `related_topics`
- ✅ `related_queries`
- ✅ `test_*` tables (testing)
- ✅ `model_metrics`, `training_logs`, etc.

### Data Verification Queries
```sql
-- Total rows
SELECT COUNT(*) FROM hourly_trends;  -- 17081

-- Unique keywords
SELECT COUNT(DISTINCT keyword) FROM hourly_trends;  -- 47

-- Unique categories
SELECT COUNT(DISTINCT category) FROM hourly_trends;  -- 10

-- Date range
SELECT MIN(datetime), MAX(datetime) FROM hourly_trends;

-- Categories list
SELECT DISTINCT category FROM hourly_trends ORDER BY category;
```

---

## 🔍 What Was Fixed (Summary)

### Issue 1: Container Name Mismatch ✅ FIXED
**Problem:** Container running as `besttimev2` instead of `besttime_postgres`  
**Solution:** QA must use `docker-compose up -d` (not manual docker run)  
**Status:** ✅ Documented in FIX_QA_DOCKER_ISSUE.md

### Issue 2: API Container Not Running ✅ FIXED
**Problem:** QA only started postgres, API container missing  
**Solution:** `docker-compose up -d` starts BOTH services  
**Status:** ✅ QA_TESTING_GUIDE.md updated

### Issue 3: Seed Data Not Loading ✅ FIXED
**Problem:** init-db.sh didn't explicitly load seed_data.sql  
**Solution:** Added Step 5/6 to init-db.sh to load and verify seed data  
**Status:** ✅ Committed (816bc5e)

### Issue 4: Incomplete .env.docker ✅ FIXED
**Problem:** Missing Google Trends, Model Training, ONNX configs  
**Solution:** Added all required environment variables to .env.docker  
**Status:** ✅ Committed (816bc5e)

### Issue 5: requirements.txt Merge Conflicts ✅ FIXED
**Problem:** 35 merge conflict markers preventing Docker build  
**Solution:** Completely rewrote with clean 89 packages  
**Status:** ✅ Committed (c128d5d)

### Issue 6: docker-compose.yml Conflicts ✅ FIXED
**Problem:** Merge conflict markers from besttime branch merge  
**Solution:** Cleaned all conflicts, standardized names  
**Status:** ✅ Committed earlier

---

## ⚠️ Common QA Mistakes to Avoid

### ❌ DON'T: Run postgres manually
```bash
# ❌ WRONG
docker run -d postgres:15-alpine
```

### ✅ DO: Use docker-compose
```bash
# ✅ CORRECT
docker-compose up -d
```

---

### ❌ DON'T: Forget .env file
```bash
# ❌ WRONG
docker-compose up -d  # No .env file!
```

### ✅ DO: Create .env first
```bash
# ✅ CORRECT
cp .env.docker .env
docker-compose up -d
```

---

### ❌ DON'T: Skip volume cleanup
```bash
# ❌ WRONG (if containers ran before)
docker-compose up -d  # Old volume exists, data not loaded!
```

### ✅ DO: Clean volumes first
```bash
# ✅ CORRECT
docker-compose down -v  # Remove old volumes
docker-compose up -d    # Fresh start, data loads
```

---

### ❌ DON'T: Test immediately
```bash
# ❌ WRONG
docker-compose up -d
curl localhost:8000  # Might fail, containers not ready!
```

### ✅ DO: Wait for initialization
```bash
# ✅ CORRECT
docker-compose up -d
sleep 90  # Wait for init
docker-compose logs postgres | grep "Database initialization completed"
curl localhost:8000/api/v1/best-time/health
```

---

## 🎯 Success Criteria

QA deployment is **successful** if:

1. ✅ Both containers running (`docker-compose ps` shows 2 healthy)
2. ✅ Database has 17,081 rows (`SELECT COUNT(*) FROM hourly_trends`)
3. ✅ API responds to health check (`/api/v1/best-time/health`)
4. ✅ Swagger UI accessible (`http://localhost:8000/docs`)
5. ✅ Prediction endpoint works (see QA_TESTING_GUIDE.md)

---

## 📖 Documentation Index

| Document | Purpose |
|----------|---------|
| **PLUG_AND_PLAY_CHECKLIST.md** | This file - Quick deployment guide |
| **QA_TESTING_GUIDE.md** | Step-by-step testing workflow |
| **TROUBLESHOOTING.md** | Common errors and solutions |
| **DATABASE_INIT_FIX.md** | Database initialization deep dive |
| **FIX_QA_DOCKER_ISSUE.md** | Container & API troubleshooting |
| **DBEAVER_SETUP.md** | Database client setup |

---

## 🔧 Troubleshooting Quick Links

**If containers unhealthy:**
- See [TROUBLESHOOTING.md](TROUBLESHOOTING.md) - Docker health checks

**If database empty:**
- See [DATABASE_INIT_FIX.md](DATABASE_INIT_FIX.md) - Volume persistence

**If API not responding:**
- See [FIX_QA_DOCKER_ISSUE.md](FIX_QA_DOCKER_ISSUE.md) - Container dependencies

**If build fails:**
- See [TROUBLESHOOTING.md](TROUBLESHOOTING.md) - Docker build section

---

## 🎉 Final Checklist

Before considering deployment complete:

- [ ] `git clone` successful
- [ ] `.env` file created from `.env.docker`
- [ ] `docker-compose up -d --build` successful
- [ ] Both containers show `(healthy)` in `docker-compose ps`
- [ ] Database verification returns 17,081 rows
- [ ] API health check returns `database_connected: true`
- [ ] Swagger UI loads at `http://localhost:8000/docs`
- [ ] Test prediction endpoint (from QA_TESTING_GUIDE.md)
- [ ] DBeaver connection works (optional, see DBEAVER_SETUP.md)

---

**🎯 Status: PLUG AND PLAY READY**

All inconsistencies resolved.  
All critical files committed and pushed.  
QA can deploy with confidence! ✅

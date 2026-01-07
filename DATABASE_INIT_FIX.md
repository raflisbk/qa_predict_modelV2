# Quick Fix: Database Tables Not Created

## Problem
After `docker-compose up -d`, tables don't exist:
- ❌ `collection_logs` does not exist
- ❌ `hourly_trends` does not exist  
- ❌ Container `besttime_postgres` is unhealthy

## Root Cause
PostgreSQL init scripts (`schema.sql`, `seed_data.sql`) only run on **FIRST START** when volume is empty.

If you ran `docker-compose up` before, volume already exists → scripts are **skipped**!

## Solution

### Step 1: Stop and Remove Everything
```bash
# Stop containers and REMOVE volumes
docker-compose down -v

# Verify volume is gone
docker volume ls | grep postgres
# Should return NOTHING
```

⚠️ **CRITICAL:** The `-v` flag removes volumes. Without it, old empty database remains!

### Step 2: Clean Docker System (Optional but Recommended)
```bash
# Remove dangling images and cache
docker system prune -f
```

### Step 3: Start Fresh
```bash
# Start services
docker-compose up -d
```

### Step 4: Wait for Initialization (IMPORTANT!)
```bash
# Wait 60-90 seconds for init scripts to complete
# Watch the logs
docker-compose logs -f postgres
```

**You should see:**
```
[OK] Step 1/4: Checking PostgreSQL readiness...
[OK] Step 2/4: Enabling UUID extension...
[OK] Step 3/4: Executing schema.sql...
[OK] Step 4/4: Loading seed data...
[OK] Database initialization completed!
[OK] Data verification: 17081 rows in hourly_trends
```

### Step 5: Verify Tables Created
```bash
# Check tables exist
docker exec -it besttime_postgres psql -U postgres -d best_time_post -c "\dt"

# Should show:
# - categories
# - hourly_trends
# - daily_trends
# - collection_logs
# - related_topics
# - related_queries

# Check data loaded
docker exec -it besttime_postgres psql -U postgres -d best_time_post -c "SELECT COUNT(*) FROM hourly_trends;"
# Should return: 17081
```

---

## Why This Happens

### PostgreSQL Volume Persistence
Docker volumes are **persistent**:
- First run: Volume empty → init scripts execute ✅
- Second run: Volume exists → init scripts SKIPPED ❌

### Init Scripts Location
```
./database/
├── init-db.sh        # Runs first
├── schema.sql        # Creates tables
└── seed_data.sql     # Inserts 17,081 rows
```

Mounted to: `/docker-entrypoint-initdb.d/` (read-only)

---

## Verification Checklist

After `docker-compose up -d`, verify:

✅ **1. Containers Healthy**
```bash
docker-compose ps

# Both should show "healthy":
# besttime_postgres   Up (healthy)
# besttime_api        Up (healthy)
```

✅ **2. Init Logs Present**
```bash
docker-compose logs postgres | grep "Database initialization"
# Should show: "[OK] Database initialization completed!"
```

✅ **3. Tables Exist**
```bash
docker exec -it besttime_postgres psql -U postgres -d best_time_post -c "\dt"
# Should list 6 tables
```

✅ **4. Data Loaded**
```bash
docker exec -it besttime_postgres psql -U postgres -d best_time_post -c "SELECT COUNT(*) FROM hourly_trends;"
# Should return: 17081
```

✅ **5. API Connected**
```bash
curl http://localhost:8000/api/v1/best-time/health
# Should return: {"status":"healthy","database_connected":true}
```

---

## Common Mistakes

### ❌ Mistake 1: Forget `-v` Flag
```bash
docker-compose down      # ❌ Volume NOT removed
docker-compose up -d     # Scripts skipped, tables missing!
```

**Correct:**
```bash
docker-compose down -v   # ✅ Volume removed
docker-compose up -d     # Scripts execute, tables created!
```

### ❌ Mistake 2: Don't Wait for Init
```bash
docker-compose up -d
# Immediately test API ❌
curl http://localhost:8000/api/v1/best-time/health
# ERROR: tables don't exist yet!
```

**Correct:**
```bash
docker-compose up -d
sleep 60                 # ✅ Wait for init
docker-compose logs postgres | grep "initialization completed"
# Now test API ✅
```

### ❌ Mistake 3: Edit Files After Container Start
```bash
docker-compose up -d
# Container running with empty DB
vim database/schema.sql  # ❌ Too late! Container already started
```

**Correct:**
```bash
# Edit FIRST
vim database/schema.sql  # ✅ Edit before starting
docker-compose down -v   # Clean slate
docker-compose up -d     # Uses new schema
```

---

## Troubleshooting

### Issue: "Container unhealthy"
```bash
# Check why unhealthy
docker-compose logs postgres | tail -50

# Check health check command
docker inspect besttime_postgres | grep -A 5 Healthcheck
```

### Issue: "Scripts didn't run"
```bash
# Check if volume already exists
docker volume ls | grep postgres

# If exists, remove it
docker volume rm <volume_name>

# Or use docker-compose
docker-compose down -v
```

### Issue: "Permission denied"
```bash
# Check file permissions
ls -la database/

# Scripts should be readable
# If not:
chmod +r database/*.sql database/*.sh
```

---

## Complete Fresh Start Command

One-liner for complete reset:
```bash
docker-compose down -v && docker system prune -f && docker-compose up -d && sleep 60 && docker exec -it besttime_postgres psql -U postgres -d best_time_post -c "SELECT COUNT(*) FROM hourly_trends;"
```

Expected output:
```
 count  
--------
 17081
(1 row)
```

If you see `17081`, everything is working! ✅

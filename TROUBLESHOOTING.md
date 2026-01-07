# Troubleshooting Guide

## Error: Docker build fails on requirements.txt

### Symptoms
```
ERROR: Could not find a version that satisfies the requirement...
ERROR: No matching distribution found for...
```

Or:
```
error: invalid command 'bdist_wheel'
error: Failed building wheel for...
```

### Root Cause
1. **Merge conflict markers** in requirements.txt (<<<<<<, ======, >>>>>>)
2. **Missing system dependencies** (gcc, g++, etc.)
3. **Network issues** downloading packages
4. **Platform incompatibility** (ARM vs x86_64)

### Solutions

#### Fix 1: Verify requirements.txt is clean

```bash
# Check for conflict markers
grep -E "<<<<<<|======|>>>>>>" requirements.txt

# Should return nothing. If it returns lines, file has merge conflicts!
```

**If conflicts found:**
```bash
# Pull latest version
git pull origin main

# Force overwrite local file
git checkout origin/main -- requirements.txt
```

#### Fix 2: Clean Docker cache and rebuild

```bash
# Remove all containers and images
docker-compose down
docker system prune -a -f

# Rebuild from scratch
docker-compose build --no-cache
docker-compose up -d
```

#### Fix 3: Check system dependencies in Dockerfile

Dockerfile should have:
```dockerfile
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    postgresql-client \
    && rm -rf /var/lib/apt/lists/*
```

#### Fix 4: Platform-specific build (ARM Mac)

For Apple Silicon (M1/M2/M3):
```bash
# Build for x86_64 platform
docker-compose build --platform linux/amd64
docker-compose up -d
```

#### Fix 5: Incremental install for debugging

```bash
# Enter a temporary container
docker run -it --rm python:3.11-slim bash

# Install dependencies one by one to find problematic package
pip install fastapi
pip install uvicorn[standard]
pip install pandas
# ... etc
```

---

## Error: "Connection refused" port 5433

### Symptoms
```
Database connection failed: (psycopg2.OperationalError) connection to server at "localhost" (::1), port 5433 failed: Connection refused
```

### Root Cause
Script mencoba connect ke PostgreSQL di **port 5433**, tapi Docker expose database di **port 5432**.

### Solutions

#### Option 1: Pastikan menggunakan file .env yang benar ✅ RECOMMENDED

1. **Hapus file .env.test** (atau rename):
```bash
# Rename to backup
mv .env.test .env.test.backup

# Atau delete
rm .env.test
```

2. **Verify .env file** menggunakan port 5432:
```bash
cat .env | grep POSTGRES_PORT
# Should output: POSTGRES_PORT=5432
```

3. **Restart terminal/VSCode** untuk clear environment variables

4. **Test connection**:
```bash
python data_collection/collect_hourly_data.py --keyword "test" --category "Food & Culinary"
```

---

#### Option 2: Set environment variable explicitly

**PowerShell:**
```powershell
$env:POSTGRES_PORT = "5432"
python data_collection/collect_hourly_data.py --keyword "test" --category "Food & Culinary"
```

**CMD:**
```cmd
set POSTGRES_PORT=5432
python data_collection/collect_hourly_data.py --keyword "test" --category "Food & Culinary"
```

**Bash/Linux:**
```bash
export POSTGRES_PORT=5432
python data_collection/collect_hourly_data.py --keyword "test" --category "Food & Culinary"
```

---

#### Option 3: Verify Docker is running ✅ IMPORTANT

Scripts di luar Docker perlu database **running**:

```bash
# 1. Check Docker containers
docker-compose ps

# Should show:
# besttime_postgres   Up (healthy)

# 2. Check database port
docker-compose ps postgres

# Should show: 0.0.0.0:5432->5432/tcp

# 3. Test connection from host
docker exec -it besttime_postgres psql -U postgres -d best_time_post -c "SELECT 1;"
```

---

#### Option 4: Run script INSIDE Docker container 🐳

Instead of running on host, run inside container:

```bash
# Enter container
docker exec -it besttime_api bash

# Run script
python data_collection/collect_hourly_data.py --keyword "laptop" --category "Technology & Gadgets"
```

Inside container, `POSTGRES_HOST=postgres` (container name, not localhost).

---

## Error: "localhost:5433 refused" with VSCode

### Symptoms
VSCode popup: "Connection refused: getsockopt"

### Root Cause
VSCode Python extension menggunakan `.env.test` instead of `.env`

### Solution

1. **Check VSCode settings** (`.vscode/settings.json`):
```json
{
  "python.envFile": "${workspaceFolder}/.env"
}
```

2. **Delete or rename `.env.test`**:
```bash
rm .env.test
```

3. **Reload VSCode window**: `Ctrl+Shift+P` → "Reload Window"

---

## Error: Docker init scripts not running

### Symptoms
```sql
SELECT COUNT(*) FROM hourly_trends;
-- Returns: 0 (should be 17,081)
```

### Root Cause
PostgreSQL volume already exists, init scripts only run on **first start**

### Solution

```bash
# 1. Stop and remove containers + volumes
docker-compose down -v

# 2. Verify volume removed
docker volume ls | grep postgres
# Should be empty

# 3. Start fresh
docker-compose up -d

# 4. Wait 60 seconds, then check logs
docker-compose logs postgres | grep "Database initialization"
# Should see: "[OK] Database initialization completed!"

# 5. Verify data
docker exec -it besttime_postgres psql -U postgres -d best_time_post -c "SELECT COUNT(*) FROM hourly_trends;"
# Should return: 17081
```

---

## Error: Port 5432 already in use

### Symptoms
```
Error starting userland proxy: listen tcp 0.0.0.0:5432: bind: address already in use
```

### Root Cause
Local PostgreSQL already running on port 5432

### Solution

**Option A: Stop local PostgreSQL**
```bash
# Windows
net stop postgresql-x64-15

# Linux/Mac
sudo systemctl stop postgresql
```

**Option B: Change Docker port** (in `.env`):
```
POSTGRES_PORT=5433
```

Then restart:
```bash
docker-compose down
docker-compose up -d
```

---

## Quick Checklist for QA

✅ Docker Desktop is running  
✅ `docker-compose ps` shows both containers as "healthy"  
✅ File `.env` exists with `POSTGRES_PORT=5432`  
✅ No `.env.test` file in project root  
✅ Volume was cleared before first run (`docker-compose down -v`)  
✅ Database has 17,081 rows: `docker exec -it besttime_postgres psql -U postgres -d best_time_post -c "SELECT COUNT(*) FROM hourly_trends;"`

---

## Still Having Issues?

1. **Collect debug info**:
```bash
# Environment variables
cat .env

# Docker status
docker-compose ps

# Docker logs
docker-compose logs --tail=50

# Database connection test
docker exec -it besttime_postgres psql -U postgres -d best_time_post -c "\dt"
```

2. **Check GitHub Issues**: https://github.com/raflisbk/qa_predict_modelV2/issues

3. **Contact Developer** dengan info:
   - OS version
   - Docker version (`docker --version`)
   - Error screenshots
   - Output dari debug commands di atas

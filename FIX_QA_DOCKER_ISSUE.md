# Fix: Database Tidak Ter-initialize & API Tidak Jalan

## Diagnosa Masalah

Saya sudah check docker container QA. Hasilnya:

### ✅ Yang Sudah Benar:
- ✅ PostgreSQL container **running** (container: `besttimev2`)
- ✅ Database **sudah ada** (`best_time_post`)
- ✅ Tables **sudah dibuat** (16 tables)
- ✅ Data **sudah terisi** (17,081 rows di `hourly_trends`, 545 rows di `collection_logs`)

### ❌ Yang Salah:
- ❌ Container name **tidak sesuai** (`besttimev2` seharusnya `besttime_postgres`)
- ❌ **API container tidak running** (tidak ada container `besttime_api`)
- ❌ QA cuma jalankan postgres saja, tidak jalankan API

---

## Root Cause

QA menggunakan **docker-compose.yml LAMA** atau **manual docker run**:
- Container postgres dibuat dengan nama `besttimev2`
- API service tidak pernah di-build/start
- Ini sebabnya script Python error: **API tidak jalan, tapi nyoba akses database**

---

## Solusi

### Step 1: Stop Container Lama
```bash
# Stop container lama
docker stop besttimev2
docker rm besttimev2

# Atau langsung paksa remove
docker rm -f besttimev2
```

### Step 2: Pull Latest Code
```bash
# Pastikan code terbaru
git pull origin main

# Verify docker-compose.yml
cat docker-compose.yml | grep "container_name"
# Harus muncul:
# container_name: besttime_postgres
# container_name: besttime_api
```

### Step 3: Start Semua Services
```bash
# PENTING: Pakai -d untuk detached mode
docker-compose up -d --build

# Atau kalau mau lihat logs realtime (tanpa -d):
docker-compose up --build
```

**Tunggu 2-3 menit** untuk:
- Build API image (pertama kali)
- Start postgres
- Initialize database (kalau volume baru)
- Start API
- Health checks

### Step 4: Verify Containers Running
```bash
docker-compose ps

# Expected output:
NAME                IMAGE                          STATUS
besttime_postgres   postgres:15-alpine             Up (healthy)
besttime_api        best-time-post-v2-api:latest   Up (healthy)
```

### Step 5: Test API
```bash
# Health check
curl http://localhost:8000/api/v1/best-time/health

# Expected:
{
  "status": "healthy",
  "database_connected": true,
  "timestamp": "2026-01-07T12:00:00",
  "version": "2.0.0"
}
```

### Step 6: Test Database Connection
```bash
# Check tables
docker exec -it besttime_postgres psql -U postgres -d best_time_post -c "\dt"

# Check data
docker exec -it besttime_postgres psql -U postgres -d best_time_post -c "SELECT COUNT(*) FROM hourly_trends;"
# Expected: 17081
```

---

## Penjelasan Error QA

### Error 1: "container besttime_postgres is unhealthy"
**Sebab:** Container name tidak match
- docker-compose.yml mencari: `besttime_postgres`
- Yang running: `besttimev2`
- **Fix:** Stop container lama, start dengan docker-compose

### Error 2: "relation collection_logs does not exist"
**Sebab:** Python script nyoba akses database tanpa API container
- Script: `collect_hourly_data.py`  
- Akses: Langsung ke database via psycopg2
- Masalah: Jalan **OUTSIDE Docker**, sedangkan database **INSIDE Docker**

**2 Opsi Fix:**

#### Opsi A: Jalankan Script INSIDE Docker Container (Recommended)
```bash
# Masuk ke API container
docker exec -it besttime_api bash

# Jalankan script dari dalam
python ./data_collection/collect_hourly_data.py --keyword "laptop" --category "Technology & Gadgets"
```

#### Opsi B: Update .env untuk Koneksi External
```bash
# File: .env
POSTGRES_HOST=localhost  # Bukan 'postgres' (itu DNS internal Docker)
POSTGRES_PORT=5432
POSTGRES_USER=postgres
POSTGRES_PASSWORD=postgres
POSTGRES_DB=best_time_post
```

Lalu jalankan script dari host:
```bash
python ./data_collection/collect_hourly_data.py --keyword "laptop" --category "Technology & Gadgets"
```

---

## Verification Checklist

Setelah docker-compose up -d, verify:

### ✅ 1. Containers Running
```bash
docker ps

# Check 2 containers:
# - besttime_postgres (healthy)
# - besttime_api (healthy)
```

### ✅ 2. Networks Created
```bash
docker network ls | grep besttime

# Should show:
# besttime_network
```

### ✅ 3. Volumes Created
```bash
docker volume ls | grep postgres

# Should show:
# best-time-post-v2_postgres_data
```

### ✅ 4. Database Initialized
```bash
docker-compose logs postgres | grep "Database initialization"

# Should show:
# [OK] Database initialization completed!
# [OK] Data verification: 17081 rows in hourly_trends
```

### ✅ 5. API Responding
```bash
curl http://localhost:8000/docs

# Should open Swagger UI (HTML response)
```

### ✅ 6. Database Connected
```bash
curl http://localhost:8000/api/v1/best-time/health | jq

# Should show:
# "database_connected": true
```

---

## Troubleshooting

### Issue: "Port 5432 already in use"
```bash
# Check apa yang pakai port
netstat -ano | findstr :5432

# Stop container lama
docker stop besttimev2
```

### Issue: "API container unhealthy"
```bash
# Check API logs
docker-compose logs api

# Common issues:
# - requirements.txt error → rebuild: docker-compose build --no-cache api
# - Database not ready → wait longer, check postgres logs
# - Missing models → check ./models directory exists
```

### Issue: "Build fails on requirements.txt"
```bash
# Make sure requirements.txt clean (no merge conflicts)
grep -E "<<<<<<|======|>>>>>>" requirements.txt

# If found, pull latest:
git pull origin main

# Force rebuild:
docker-compose build --no-cache
```

### Issue: "Tables tidak ada setelah up"
```bash
# Check volume sudah kosong atau belum
docker volume inspect best-time-post-v2_postgres_data

# If volume exists from before:
docker-compose down -v  # Remove volumes
docker-compose up -d    # Recreate with init scripts
```

---

## Quick Commands

### Full Reset (Clean Slate)
```bash
# Stop everything
docker-compose down -v

# Remove old containers (if exist)
docker rm -f besttimev2 2>/dev/null || true

# Clean Docker system
docker system prune -f

# Start fresh
docker-compose up -d --build

# Wait & verify
sleep 90
docker-compose ps
curl http://localhost:8000/api/v1/best-time/health
```

### Check Logs (Realtime)
```bash
# All services
docker-compose logs -f

# Only postgres
docker-compose logs -f postgres

# Only API
docker-compose logs -f api

# Last 100 lines
docker-compose logs --tail=100
```

### Restart Single Service
```bash
# Restart postgres
docker-compose restart postgres

# Restart API (rebuild if code changed)
docker-compose up -d --build api
```

---

## Next Steps After Fix

Setelah semua container running, QA bisa:

1. **Test API Endpoints** - Ikuti [QA_TESTING_GUIDE.md](QA_TESTING_GUIDE.md)
2. **Use DBeaver** - Ikuti [DBEAVER_SETUP.md](DBEAVER_SETUP.md)  
3. **Run Data Collection** - Jalankan script INSIDE container:
   ```bash
   docker exec -it besttime_api python ./data_collection/collect_hourly_data.py \
     --keyword "laptop" --category "Technology & Gadgets"
   ```

---

## Summary

**Yang Harus QA Lakukan:**

```bash
# 1. Stop container lama
docker rm -f besttimev2

# 2. Pull latest code
git pull origin main

# 3. Start dengan docker-compose
docker-compose up -d --build

# 4. Wait 2 menit

# 5. Verify
docker-compose ps
curl http://localhost:8000/api/v1/best-time/health

# 6. DONE! ✅
```

**Expected Result:**
- ✅ 2 containers running (postgres + api)
- ✅ Database ada 17,081 rows
- ✅ API health check return `database_connected: true`
- ✅ Script bisa jalan di dalam container

---

## Error Yang Sudah Fixed

1. ✅ **Container name mismatch** - Fixed dengan restart menggunakan docker-compose.yml
2. ✅ **API tidak running** - Fixed dengan `docker-compose up -d` (start semua services)
3. ✅ **Database initialization** - Sudah OK, data sudah ada (17,081 rows)
4. ✅ **collection_logs error** - Fixed karena table sudah ada, cuma script salah connect

**Root cause sebenarnya:** QA tidak pakai `docker-compose up`, tapi manual start postgres saja.

**Solusinya:** Selalu pakai `docker-compose up -d` untuk start semua services sekaligus.

# QA Setup Guide - Best Time Post v2

## 🚀 Quick Start (Plug and Play)

Panduan ini untuk QA team yang ingin setup database lokal menggunakan Docker dan connect via DBeaver.

---

## Prerequisites

Pastikan sudah terinstall:

- ✅ Docker Desktop (Windows/Mac) atau Docker Engine (Linux)
- ✅ DBeaver (atau PostgreSQL client lainnya)
- ✅ Python 3.9+ (untuk verification script)
- ✅ Git

---

## Step 1: Clone Repository

```bash
git clone https://github.com/raflisbk/qa_predict_modelV2.git
cd qa_predict_modelV2
```

---

## Step 2: Setup Environment File

Copy file `.env.example` menjadi `.env`:

```bash
# Windows PowerShell
copy .env.example .env

# Linux/Mac
cp .env.example .env
```

**Default settings sudah siap pakai!** Tidak perlu edit apapun untuk local development.

Isi default `.env`:

```env
POSTGRES_USER=postgres
POSTGRES_PASSWORD=postgres
POSTGRES_DB=best_time_post
POSTGRES_HOST=localhost
POSTGRES_PORT=5432
```

> 💡 **Catatan:** Jika port 5432 sudah dipakai, ubah `POSTGRES_PORT` ke port lain (misal 5433)

---

## Step 3: Start Database dengan Docker

Jalankan command berikut:

```bash
docker-compose up -d
```

**Apa yang terjadi:**

1. ✅ Docker download PostgreSQL image (hanya pertama kali)
2. ✅ Container database dibuat dan dijalankan
3. ✅ UUID extension otomatis di-enable
4. ✅ Semua tables otomatis dibuat (16 tables)
5. ✅ Semua views otomatis dibuat (8 views)
6. ✅ Initial data kategori otomatis di-load (10 categories)

**Tunggu ~30 detik** untuk proses initialization selesai.

---

## Step 4: Verify Database (Recommended)

Jalankan verification script untuk memastikan semua setup dengan benar:

```bash
python scripts/verify_db.py
```

**Expected output:**

```
============================================================
DATABASE VERIFICATION FOR QA
============================================================

Step 1/4: Testing database connection...
✓ Database connection successful

Step 2/4: Checking UUID extension...
✓ UUID extension enabled (version: 1.1)

Step 3/4: Checking tables...
Found 16 tables:
  ✓ categories
  ✓ collection_logs
  ✓ daily_trends
  ...
✓ All 16 expected tables exist

Step 4/4: Checking views...
Found 8 views:
  ✓ v_daily_trends_analysis
  ...
✓ All 8 expected views exist

============================================================
VERIFICATION SUMMARY
============================================================
Connection          : ✓ PASS
UUID Extension      : ✓ PASS
Tables              : ✓ PASS
Views               : ✓ PASS
Initial Data        : ✓ PASS
============================================================

🎉 ALL CHECKS PASSED!
```

---

## Step 5: Connect dengan DBeaver

### 5.1 Buka DBeaver dan Create New Connection

1. Klik **Database** → **New Database Connection**
2. Pilih **PostgreSQL**
3. Klik **Next**

### 5.2 Configure Connection

Masukkan settings berikut (sesuai `.env`):

| Field        | Value            |
| ------------ | ---------------- |
| **Host**     | `localhost`      |
| **Port**     | `5432`           |
| **Database** | `best_time_post` |
| **Username** | `postgres`       |
| **Password** | `postgres`       |

### 5.3 Test Connection

1. Klik **Test Connection**
2. Jika pertama kali, DBeaver akan download PostgreSQL driver (klik **Download**)
3. Seharusnya muncul **"Connected"** ✅

### 5.4 Finish Setup

1. Klik **Finish**
2. Database connection akan muncul di sidebar
3. Expand connection untuk melihat:
   - **Schemas** → **public** → **Tables** (16 tables)
   - **Schemas** → **public** → **Views** (8 views)

---

## Step 6: Verify Tables in DBeaver

Run query ini untuk test:

```sql
-- Check categories
SELECT * FROM categories;

-- Check table count
SELECT
    schemaname,
    COUNT(*) as table_count
FROM pg_tables
WHERE schemaname = 'public'
GROUP BY schemaname;

-- Check views
SELECT
    schemaname,
    COUNT(*) as view_count
FROM pg_views
WHERE schemaname = 'public'
GROUP BY schemaname;
```

**Expected results:**

- 10 categories
- 16 tables
- 8 views

---

## 🎉 Setup Complete!

Database Anda sudah siap digunakan untuk:

- ✅ Testing data collection scripts
- ✅ Running queries
- ✅ Development
- ✅ Model training

---

## 🔧 Troubleshooting

### Problem: `docker-compose up -d` gagal

**Solution:**

```bash
# Check Docker is running
docker --version

# Check if port 5432 is available
netstat -an | findstr 5432

# If port is used, change POSTGRES_PORT in .env to 5433
```

---

### Problem: Verification script gagal connect

**Solution:**

```bash
# Check container is running
docker-compose ps

# Should show:
# NAME         STATUS
# besttimev2   Up (healthy)

# Check logs
docker-compose logs postgres

# Restart if needed
docker-compose restart
```

---

### Problem: DBeaver connection refused

**Checklist:**

1. ✅ Container running? → `docker-compose ps`
2. ✅ Port correct? → Check `.env` POSTGRES_PORT
3. ✅ Host is `localhost` not `127.0.0.1`?
4. ✅ Firewall blocking? → Disable temporarily

---

### Problem: Tables tidak ada di DBeaver

**Solution:**

```bash
# Check initialization logs
docker-compose logs postgres | findstr "INITIALIZATION"

# Should see:
# DATABASE INITIALIZATION COMPLETED
# Status: READY ✓

# If not, recreate database:
docker-compose down -v
docker-compose up -d

# Wait 30 seconds, then verify
python scripts/verify_db.py
```

---

### Problem: Permission error untuk UUID extension

Ini **tidak akan terjadi** dengan Docker setup karena user `postgres` punya full permissions.

Jika tetap terjadi, berarti ada masalah dengan Docker image:

```bash
# Use official PostgreSQL image
docker-compose down -v
docker-compose up -d
```

---

## 📚 Useful Commands

### Docker Commands

```bash
# Start database
docker-compose up -d

# Stop database
docker-compose stop

# Stop and remove (data tetap ada)
docker-compose down

# Stop and remove ALL data (fresh start)
docker-compose down -v

# View logs
docker-compose logs postgres

# Follow logs (real-time)
docker-compose logs -f postgres

# Check status
docker-compose ps

# Restart
docker-compose restart
```

### Database Commands

```bash
# Verify database
python scripts/verify_db.py

# Initialize database (if needed manually)
python scripts/init_db.py

# Access PostgreSQL CLI
docker exec -it besttimev2 psql -U postgres -d best_time_post
```

---

## 🔐 Security Notes

**Default credentials** (`postgres/postgres`) hanya untuk **local development**.

Untuk production/staging:

1. Ubah `POSTGRES_PASSWORD` di `.env`
2. Jangan commit `.env` ke Git
3. Use environment variables atau secrets management

---

## 📞 Need Help?

Jika masih ada masalah:

1. **Check logs:** `docker-compose logs postgres`
2. **Run verification:** `python scripts/verify_db.py`
3. **Fresh start:** `docker-compose down -v && docker-compose up -d`
4. **Contact dev team** dengan error message lengkap

---

## ✅ Checklist Setup Berhasil

- [ ] Docker Desktop running
- [ ] `docker-compose up -d` success
- [ ] `python scripts/verify_db.py` all checks passed
- [ ] DBeaver connection success
- [ ] Can see 16 tables in DBeaver
- [ ] Can query `SELECT * FROM categories;`

Jika semua ✅, setup Anda **BERHASIL!** 🎉

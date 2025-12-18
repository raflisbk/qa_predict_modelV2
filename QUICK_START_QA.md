# 🚀 UNTUK QA - Step-by-Step Setup Database

## ⚡ Quick Start (2 Menit)

### Step 1: Clone Repository

```bash
git clone https://github.com/raflisbk/qa_predict_modelV2.git
cd qa_predict_modelV2
```

### Step 2: Setup Environment

```bash
copy .env.example .env
```

**TIDAK PERLU EDIT APAPUN!** Default settings sudah siap pakai.

### Step 3: Start Database

```bash
docker-compose up -d
```

### Step 4: Tunggu Initialization (30-40 detik)

```bash
# Optional: Monitor logs
docker-compose logs -f postgres

# Tunggu sampai muncul:
# "DATABASE INITIALIZATION COMPLETED"
# "Status: READY ✓"

# Tekan Ctrl+C untuk stop monitoring
```

### Step 5: Verify (Optional tapi Recommended)

```bash
python scripts/verify_db.py
```

**Expected output:**

```
============================================================
VERIFICATION SUMMARY
============================================================
Connection          : [PASS]
UUID Extension      : [PASS]
Tables              : [PASS]
Views               : [PASS]
Initial Data        : [PASS]
============================================================

[SUCCESS] ALL CHECKS PASSED!
```

---

## 🔌 Connect dengan DBeaver

### Connection Settings:

```
Host:     localhost
Port:     5432
Database: best_time_post
Username: postgres
Password: postgres
```

### Steps:

1. **Database** → **New Database Connection**
2. **PostgreSQL** → **Next**
3. Masukkan settings di atas
4. **Test Connection** → Should show "Connected"
5. **Finish**

### Verify:

- Expand: **Databases** → **best_time_post** → **Schemas** → **public** → **Tables**
- Seharusnya ada **16 tables**
- Expand **Views** → Seharusnya ada **8 views**

### Test Query:

```sql
-- Should return 10 rows
SELECT * FROM categories;
```

---

## ✅ Success Checklist

- [ ] `docker-compose up -d` berhasil tanpa error
- [ ] `docker-compose ps` menunjukkan status "healthy"
- [ ] `python scripts/verify_db.py` menunjukkan "ALL CHECKS PASSED"
- [ ] DBeaver bisa connect ke database
- [ ] Bisa lihat 16 tables di DBeaver
- [ ] Bisa lihat 8 views di DBeaver
- [ ] Query `SELECT * FROM categories;` return 10 rows

**Jika semua ✅, setup BERHASIL!** 🎉

---

## 🔧 Troubleshooting

### Problem: Port 5432 sudah dipakai

**Solution:**

1. Edit `.env`
2. Ubah `POSTGRES_PORT=5432` jadi `POSTGRES_PORT=5433`
3. Restart: `docker-compose down && docker-compose up -d`
4. Connect DBeaver pakai port 5433

### Problem: Tables tidak ada

**Solution:**

```bash
# Fresh start
docker-compose down -v
docker-compose up -d

# Tunggu 30 detik
# Verify lagi
python scripts/verify_db.py
```

### Problem: Verification script gagal

**Solution:**

```bash
# Check logs
docker-compose logs postgres

# Restart
docker-compose restart
```

---

## 📚 Dokumentasi Lengkap

- **Quick Start:** [QUICK_START_QA.md](QUICK_START_QA.md)
- **Detailed Guide:** [docs/QA_SETUP.md](docs/QA_SETUP.md)
- **Checklist:** [QA_CHECKLIST.md](QA_CHECKLIST.md)
- **Project README:** [README.md](README.md)

---

## 🎯 Summary Commands

```bash
# Start database
docker-compose up -d

# Check status
docker-compose ps

# View logs
docker-compose logs postgres

# Verify setup
python scripts/verify_db.py

# Stop database
docker-compose stop

# Restart database
docker-compose restart

# Fresh start (remove all data)
docker-compose down -v
docker-compose up -d
```

---

**Total waktu setup: ~2 menit** ⚡  
**Hasil: 16 tables + 8 views + 10 categories ready!** 🎉

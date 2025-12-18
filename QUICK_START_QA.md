# 🚀 QUICK START - QA Team

## Setup Database (2 Menit)

### Step 1: Clone & Setup

```bash
git clone https://github.com/raflisbk/qa_predict_modelV2.git
cd qa_predict_modelV2
copy .env.example .env
```

### Step 2: Start Database

```bash
docker-compose up -d
```

⏳ **Tunggu 30 detik** untuk initialization selesai.

### Step 3: Verify (Optional)

```bash
python scripts/verify_db.py
```

Seharusnya muncul: **`[SUCCESS] ALL CHECKS PASSED!`**

---

## Connect dengan DBeaver

1. **New Connection** → **PostgreSQL**
2. **Masukkan settings:**
   - Host: `localhost`
   - Port: `5432`
   - Database: `best_time_post`
   - Username: `postgres`
   - Password: `postgres`
3. **Test Connection** → Klik **Finish**

✅ **DONE!** Anda sekarang bisa lihat 16 tables dan 8 views.

---

## Troubleshooting

### Masalah: Port 5432 sudah dipakai

**Solusi:**

1. Edit `.env`
2. Ubah `POSTGRES_PORT=5432` jadi `POSTGRES_PORT=5433`
3. Restart: `docker-compose down && docker-compose up -d`
4. Connect DBeaver pakai port 5433

### Masalah: Docker tidak jalan

**Solusi:**

1. Buka Docker Desktop
2. Tunggu sampai Docker running
3. Ulangi `docker-compose up -d`

### Masalah: Tables tidak ada

**Solusi:**

```bash
docker-compose down -v
docker-compose up -d
```

Tunggu 30 detik, lalu verify lagi.

---

## Cek Status Database

```bash
# Lihat container status
docker-compose ps

# Lihat logs
docker-compose logs postgres

# Verify database
python scripts/verify_db.py
```

---

## 📖 Dokumentasi Lengkap

Untuk troubleshooting detail, lihat: [docs/QA_SETUP.md](docs/QA_SETUP.md)

---

## ✅ Checklist Setup Berhasil

- [ ] `docker-compose up -d` berhasil
- [ ] `python scripts/verify_db.py` → ALL CHECKS PASSED
- [ ] DBeaver bisa connect
- [ ] Bisa lihat 16 tables
- [ ] Query `SELECT * FROM categories;` berhasil (10 rows)

**Jika semua ✅, setup BERHASIL!** 🎉

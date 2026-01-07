# DBeaver Setup Guide

## PostgreSQL Connection untuk Best Time Post API

### 📋 Connection Details

Gunakan settings berikut untuk connect ke PostgreSQL Docker container:

```
Host: localhost
Port: 5432
Database: best_time_post
Username: postgres
Password: postgres
```

---

## 🔧 Step-by-Step Setup

### 1. Create New Connection

1. Open DBeaver
2. Click **Database** → **New Database Connection**
3. Select **PostgreSQL**
4. Click **Next**

### 2. Configure Connection

**Main tab:**
- **Host:** `localhost`
- **Port:** `5432` ⚠️ **IMPORTANT: Harus 5432, bukan 5433!**
- **Database:** `best_time_post`
- **Username:** `postgres`
- **Password:** `postgres`
- **Show all databases:** ☑️ (checked)

**PostgreSQL tab:**
- Show non-default databases: ☑️

### 3. Test Connection

1. Click **Test Connection** button
2. If first time, DBeaver akan download PostgreSQL driver → Click **Download**
3. Should show: ✅ **"Connected"**

**If connection fails:**
- Check Docker is running: `docker-compose ps`
- Verify port: Container should show `0.0.0.0:5432->5432/tcp`
- Check firewall/antivirus tidak block port 5432

### 4. Save Connection

1. Click **Finish**
2. Connection akan muncul di **Database Navigator**

---

## 🗂️ Database Structure

Setelah connect, kamu akan lihat:

```
best_time_post/
├── Schemas/
│   └── public/
│       ├── Tables/
│       │   ├── categories (10 rows)
│       │   ├── hourly_trends (17,081 rows) ⭐
│       │   ├── daily_trends
│       │   ├── related_topics
│       │   ├── related_queries
│       │   └── collection_logs
│       └── Views/
```

---

## ✅ Verification Queries

Run these queries untuk verify database setup:

### Check Row Counts
```sql
-- Should return: 17081
SELECT COUNT(*) FROM hourly_trends;

-- Should return: 10
SELECT COUNT(*) FROM categories;

-- Check data distribution by category
SELECT category, COUNT(*) as total_records
FROM hourly_trends
GROUP BY category
ORDER BY total_records DESC;
```

### Check Recent Data
```sql
-- Latest 10 records
SELECT * FROM hourly_trends
ORDER BY datetime DESC
LIMIT 10;

-- Date range
SELECT 
    MIN(datetime) as earliest_date,
    MAX(datetime) as latest_date,
    COUNT(*) as total_records
FROM hourly_trends;
```

### Check Categories
```sql
-- All categories
SELECT * FROM categories
ORDER BY name;
```

---

## 🚨 Common Issues

### Issue 1: "Connection refused" port 5433

**Symptom:**
```
Connection to localhost:5433 refused
```

**Solution:**
DBeaver menggunakan port yang salah. Edit connection:
1. Right-click connection → **Edit Connection**
2. Change port dari `5433` ke `5432`
3. Click **Test Connection**
4. Click **OK**

---

### Issue 2: "Database does not exist"

**Symptom:**
```
FATAL: database "best_time_post" does not exist
```

**Solution:**
Database belum di-initialize. Run:
```bash
# Stop and remove volumes
docker-compose down -v

# Start fresh (will initialize database)
docker-compose up -d

# Wait 60 seconds for init scripts
sleep 60

# Verify
docker exec -it besttime_postgres psql -U postgres -d best_time_post -c "SELECT COUNT(*) FROM hourly_trends;"
```

---

### Issue 3: Empty Tables (0 rows)

**Symptom:**
```sql
SELECT COUNT(*) FROM hourly_trends;
-- Returns: 0 (should be 17081)
```

**Solution:**
Init scripts tidak jalan. Follow **Issue 2** solution di atas.

---

### Issue 4: "Connection timed out"

**Symptom:**
DBeaver stuck pada "Opening connection..."

**Solution:**
1. Check Docker container running:
   ```bash
   docker-compose ps
   # besttime_postgres should be "Up (healthy)"
   ```

2. Check port accessible:
   ```bash
   # Windows PowerShell
   Test-NetConnection -ComputerName localhost -Port 5432
   ```

3. Restart Docker container:
   ```bash
   docker-compose restart postgres
   ```

---

## 🔐 Security Note

Default credentials (`postgres/postgres`) hanya untuk **development/QA**.

Untuk production, gunakan strong password dan update di `.env`:
```
POSTGRES_PASSWORD=your_strong_password_here
```

---

## 📊 Useful Queries untuk QA Testing

### 1. Category Performance
```sql
SELECT 
    category,
    COUNT(*) as total_records,
    AVG(interest_value) as avg_interest,
    MAX(interest_value) as max_interest,
    MIN(datetime) as earliest_data,
    MAX(datetime) as latest_data
FROM hourly_trends
GROUP BY category
ORDER BY avg_interest DESC;
```

### 2. Time of Day Analysis
```sql
SELECT 
    time_of_day,
    COUNT(*) as total_records,
    AVG(interest_value) as avg_interest
FROM hourly_trends
GROUP BY time_of_day
ORDER BY 
    CASE time_of_day
        WHEN 'morning' THEN 1
        WHEN 'afternoon' THEN 2
        WHEN 'evening' THEN 3
        WHEN 'night' THEN 4
    END;
```

### 3. Weekend vs Weekday
```sql
SELECT 
    CASE WHEN is_weekend THEN 'Weekend' ELSE 'Weekday' END as day_type,
    COUNT(*) as total_records,
    AVG(interest_value) as avg_interest
FROM hourly_trends
GROUP BY is_weekend;
```

### 4. Hourly Distribution
```sql
SELECT 
    hour,
    COUNT(*) as total_records,
    AVG(interest_value) as avg_interest
FROM hourly_trends
GROUP BY hour
ORDER BY hour;
```

---

## 🎯 Expected Results

Setelah setup correct, QA harus bisa:

✅ Connect to database successfully  
✅ See 17,081 rows in `hourly_trends`  
✅ See 10 categories in `categories`  
✅ Run queries without errors  
✅ View data from last 7 days  
✅ See data distributed across all 10 categories  

---

## 🆘 Still Having Issues?

1. **Check Docker logs:**
   ```bash
   docker-compose logs postgres | grep -i error
   ```

2. **Verify environment variables:**
   ```bash
   docker exec -it besttime_postgres env | grep POSTGRES
   ```

3. **Test connection from terminal:**
   ```bash
   docker exec -it besttime_postgres psql -U postgres -d best_time_post -c "\dt"
   ```

4. **Screenshot DBeaver error** dan share untuk troubleshooting

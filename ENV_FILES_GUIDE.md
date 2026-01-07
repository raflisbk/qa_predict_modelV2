# Environment Files Guide

## 📁 File Inventory

| File | Purpose | Git Tracked | Used By |
|------|---------|-------------|---------|
| `.env` | **Developer local** | ❌ No (gitignored) | You (DEV) |
| `.env.docker` | **QA template** | ✅ Yes | QA (Docker) |
| `.env.example` | Reference template | ✅ Yes | Documentation |
| `.env.test` | Testing only | ❌ No (gitignored) | Local tests |

---

## 🎯 Quick Answer

### **Developer (You):**
```bash
File: .env
POSTGRES_HOST=localhost  # ← Connect to Docker from outside
```

### **QA (Docker):**
```bash
File: .env (copied from .env.docker)
POSTGRES_HOST=postgres   # ← Container DNS name
```

---

## 📋 Detailed Explanation

### 1️⃣ **`.env` - Your Development File**

**Location:** Project root (NOT in Git)  
**Used by:** You, running Python scripts directly on host machine  
**Key difference:**
```env
POSTGRES_HOST=localhost  # ← You connect from OUTSIDE Docker
POSTGRES_PORT=5432
APIFY_API_TOKEN=YOUR_TOKEN_HERE  # Your actual Apify token (kept secret)
```

**Why `localhost`?**
- You run `python api_start.py` on Windows
- Database is in Docker container, exposed to host port 5432
- Connection: `localhost:5432` → `besttimev2` container

---

### 2️⃣ **`.env.docker` - QA Template (IN GIT)**

**Location:** Project root (tracked in Git)  
**Used by:** QA, as template to create their `.env`  
**Key difference:**
```env
POSTGRES_HOST=postgres   # ← Container DNS name (internal Docker network)
POSTGRES_PORT=5432       # ← Internal port
APIFY_API_TOKEN=PLACEHOLDER_TOKEN  # Placeholder, not real token
```

**Why `postgres`?**
- QA runs everything INSIDE Docker
- API container connects to postgres container via Docker network
- Connection: `postgres:5432` (DNS resolved by Docker)

---

### 3️⃣ **`.env.example` - Reference Template**

**Location:** Project root (tracked in Git)  
**Used by:** Documentation, showing all available variables  
**Purpose:** Help others understand what variables exist

---

### 4️⃣ **`.env.test` - Testing Only**

**Location:** Project root (NOT in Git)  
**Used by:** Local testing with different port  
**Note:** Only exists on your machine, QA won't have this

---

## 🔄 QA Setup Workflow

### Step 1: Clone Repository
```bash
git clone https://github.com/raflisbk/qa_predict_modelV2.git
cd qa_predict_modelV2
```

**What QA gets:**
- ✅ `.env.docker` (template)
- ✅ `.env.example` (reference)
- ❌ `.env` (NOT in Git, they must create it)
- ❌ `.env.test` (NOT in Git)

### Step 2: Create `.env` from Template
```bash
# QA must do this BEFORE docker-compose up
cp .env.docker .env
```

**Result:**
- `.env` created locally (gitignored)
- Contains `POSTGRES_HOST=postgres` (correct for Docker)
- Contains placeholder Apify token (they can add real one if needed)

### Step 3: Start Docker
```bash
docker-compose up -d
```

**Docker Compose reads:**
- `.env` file (just created from `.env.docker`)
- Uses `POSTGRES_HOST=postgres` (internal DNS)

---

## ⚠️ Key Differences

### Developer (You) - Running on Host

**File:** `.env` (custom, not in Git)
```env
POSTGRES_HOST=localhost          # ← Outside Docker
APIFY_API_TOKEN=your_real_token  # Your actual token (kept secret)
```

**Command:**
```bash
# Run on Windows directly
python api_start.py

# Connects to: localhost:5432 (Docker exposed port)
```

---

### QA - Running in Docker

**File:** `.env` (copied from `.env.docker`)
```env
POSTGRES_HOST=postgres           # ← Inside Docker network
APIFY_API_TOKEN=PLACEHOLDER_TOKEN  # Placeholder
```

**Command:**
```bash
# Everything runs in containers
docker-compose up -d

# API container connects to: postgres:5432 (internal DNS)
```

---

## 🚨 Common Mistakes

### ❌ Mistake 1: QA forgets to create `.env`
```bash
# ❌ WRONG
docker-compose up -d  # No .env file!
# Result: Uses default values, might fail
```

**✅ Fix:**
```bash
# ✅ CORRECT
cp .env.docker .env
docker-compose up -d
```

---

### ❌ Mistake 2: QA uses your `.env` file
```bash
# ❌ WRONG (if QA somehow gets your .env)
POSTGRES_HOST=localhost  # Wrong! Containers can't resolve "localhost" to postgres container
```

**✅ Fix:**
```bash
# ✅ CORRECT (from .env.docker)
POSTGRES_HOST=postgres  # Docker DNS resolves this
```

---

### ❌ Mistake 3: You commit `.env` to Git
```bash
# ❌ WRONG
git add .env
git commit -m "Add env file"
# Result: Your APIFY token exposed in Git!
```

**✅ Fix:**
```bash
# ✅ CORRECT - .env is gitignored
# Only commit .env.docker (with placeholder token)
git add .env.docker
git commit -m "Update Docker template"
```

---

## 📊 File Comparison

| Variable | `.env` (DEV) | `.env.docker` (QA Template) |
|----------|--------------|---------------------------|
| `POSTGRES_HOST` | `localhost` | `postgres` |
| `APIFY_API_TOKEN` | Real token | `PLACEHOLDER_TOKEN` |
| **Git Tracked** | ❌ No | ✅ Yes |
| **Used for** | Local dev | Docker template |

---

## 🎯 Summary

### **For You (Developer):**
- ✅ Keep using `.env` with `POSTGRES_HOST=localhost`
- ✅ Your file is gitignored (safe)
- ✅ Don't change `.env.docker` (QA needs it)

### **For QA:**
- ✅ Copy `.env.docker` to `.env` BEFORE docker-compose
- ✅ File has `POSTGRES_HOST=postgres` (correct for Docker)
- ✅ Can add real APIFY token if needed (optional)

### **Files to Update:**
- **Never commit:** `.env`, `.env.test`
- **Safe to commit:** `.env.docker`, `.env.example`

---

## 🔧 Verification

### Check Current Setup
```bash
# See which .env files exist
ls -la | grep "\.env"

# Check what's in Git
git ls-files | grep env

# Expected in Git:
# .env.docker  ✅
# .env.example ✅
```

### Verify Gitignore
```bash
# Check .gitignore rules
cat .gitignore | grep "\.env"

# Expected:
# .env           ← Your file (ignored)
# .env.local     ← Ignored
# .env.*.local   ← Ignored
# .env.test      ← Ignored
```

---

## 💡 Best Practices

1. **Developer:**
   - Use `.env` for local development
   - Never commit `.env` to Git
   - Keep real API tokens in `.env` only

2. **QA:**
   - Always run: `cp .env.docker .env` before first Docker start
   - Can modify `.env` locally (add real tokens if needed)
   - Their `.env` stays local (gitignored)

3. **Team:**
   - Update `.env.docker` when adding new required variables
   - Update `.env.example` for documentation
   - Never commit real credentials

---

## 🚀 QA Quick Start (One-Liner)

```bash
git clone https://github.com/raflisbk/qa_predict_modelV2.git && \
cd qa_predict_modelV2 && \
cp .env.docker .env && \
docker-compose up -d
```

**That's it!** ✅

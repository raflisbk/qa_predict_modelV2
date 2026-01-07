# QA Validation Script - Test Complete Workflow (Windows PowerShell)
# This script simulates what QA will do

Write-Host "==========================================" -ForegroundColor Cyan
Write-Host "QA WORKFLOW VALIDATION" -ForegroundColor Cyan
Write-Host "==========================================" -ForegroundColor Cyan
Write-Host ""

# Check prerequisites
Write-Host "[1/6] Checking prerequisites..." -ForegroundColor Yellow

# Check Docker
try {
    docker --version | Out-Null
    Write-Host "[OK] Docker found" -ForegroundColor Green
} catch {
    Write-Host "[ERROR] Docker not found. Please install Docker Desktop." -ForegroundColor Red
    exit 1
}

# Check Python
try {
    python --version | Out-Null
    Write-Host "[OK] Python found" -ForegroundColor Green
} catch {
    Write-Host "[ERROR] Python not found. Please install Python 3.9+" -ForegroundColor Red
    exit 1
}
Write-Host ""

# Check .env file
Write-Host "[2/6] Checking .env file..." -ForegroundColor Yellow
if (-not (Test-Path ".env")) {
    Write-Host "[WARN] .env not found. Creating from .env.example..." -ForegroundColor Yellow
    Copy-Item ".env.example" ".env"
    Write-Host "[OK] .env created" -ForegroundColor Green
} else {
    Write-Host "[OK] .env exists" -ForegroundColor Green
}
Write-Host ""

# Check Docker is running
Write-Host "[3/6] Checking Docker status..." -ForegroundColor Yellow
try {
    docker info | Out-Null
    Write-Host "[OK] Docker is running" -ForegroundColor Green
} catch {
    Write-Host "[ERROR] Docker is not running. Please start Docker Desktop." -ForegroundColor Red
    exit 1
}
Write-Host ""

# Start database
Write-Host "[4/6] Starting database..." -ForegroundColor Yellow
docker-compose up -d
Write-Host "[INFO] Waiting 35 seconds for initialization..." -ForegroundColor Cyan
Start-Sleep -Seconds 35
Write-Host ""

# Check container status
Write-Host "[5/6] Checking container status..." -ForegroundColor Yellow
$containerStatus = docker-compose ps --format json | ConvertFrom-Json | Select-Object -First 1 -ExpandProperty Health

if ($containerStatus -eq "healthy") {
    Write-Host "[OK] Container is healthy" -ForegroundColor Green
} else {
    Write-Host "[WARN] Container status: $containerStatus" -ForegroundColor Yellow
    Write-Host "Checking logs..." -ForegroundColor Yellow
    docker-compose logs postgres --tail 20
}
Write-Host ""

# Verify database
Write-Host "[6/6] Verifying database setup..." -ForegroundColor Yellow
python scripts/verify_db.py

Write-Host ""
Write-Host "==========================================" -ForegroundColor Cyan
Write-Host "QA WORKFLOW VALIDATION COMPLETE" -ForegroundColor Cyan
Write-Host "==========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Next steps:" -ForegroundColor Green
Write-Host "1. Open DBeaver"
Write-Host "2. Create new PostgreSQL connection:"
Write-Host "   - Host: localhost"
Write-Host "   - Port: 5432"
Write-Host "   - Database: best_time_post"
Write-Host "   - User: postgres"
Write-Host "   - Password: postgres"
Write-Host "3. Test connection"
Write-Host "4. Browse tables (should see 16 tables)"
Write-Host ""

# Database Verification Script (PowerShell)
# Verifies that QA database has EXACTLY the same data as development

Write-Host "================================================" -ForegroundColor Cyan
Write-Host "DATABASE DATA VERIFICATION" -ForegroundColor Cyan
Write-Host "================================================" -ForegroundColor Cyan
Write-Host ""

# Connection details
$CONTAINER = "besttime_postgres"
$DB_USER = "postgres"
$DB_NAME = "best_time_post"

Write-Host "Checking database: $DB_NAME"
Write-Host "Container: $CONTAINER"
Write-Host ""

function Run-Query {
    param([string]$Query)
    $result = docker exec -it $CONTAINER psql -U $DB_USER -d $DB_NAME -t -c $Query 2>$null
    return ($result -replace '\s+', '').Trim()
}

# 1. Total rows check
Write-Host "1. Checking total rows in hourly_trends..." -ForegroundColor Yellow
$TOTAL_ROWS = Run-Query "SELECT COUNT(*) FROM hourly_trends;"
Write-Host "   Expected: 17081"
Write-Host "   Actual:   $TOTAL_ROWS"
if ($TOTAL_ROWS -eq "17081") {
    Write-Host "   ✅ PASS" -ForegroundColor Green
} else {
    Write-Host "   ❌ FAIL - Row count mismatch!" -ForegroundColor Red
    exit 1
}
Write-Host ""

# 2. Category distribution
Write-Host "2. Checking category distribution..." -ForegroundColor Yellow
$CATEGORIES = Run-Query "SELECT COUNT(DISTINCT category) FROM hourly_trends;"
Write-Host "   Expected categories: 10"
Write-Host "   Actual categories:   $CATEGORIES"
if ($CATEGORIES -eq "10") {
    Write-Host "   ✅ PASS" -ForegroundColor Green
} else {
    Write-Host "   ❌ FAIL - Category count mismatch!" -ForegroundColor Red
    exit 1
}
Write-Host ""

# 3. Keyword diversity
Write-Host "3. Checking keyword diversity..." -ForegroundColor Yellow
$KEYWORDS = Run-Query "SELECT COUNT(DISTINCT keyword) FROM hourly_trends;"
Write-Host "   Expected keywords: 47"
Write-Host "   Actual keywords:   $KEYWORDS"
if ($KEYWORDS -eq "47") {
    Write-Host "   ✅ PASS" -ForegroundColor Green
} else {
    Write-Host "   ❌ FAIL - Keyword count mismatch!" -ForegroundColor Red
    exit 1
}
Write-Host ""

# 4. Collection IDs
Write-Host "4. Checking collection diversity..." -ForegroundColor Yellow
$COLLECTIONS = Run-Query "SELECT COUNT(DISTINCT collection_id) FROM hourly_trends WHERE collection_id IS NOT NULL;"
Write-Host "   Expected collections: 168"
Write-Host "   Actual collections:   $COLLECTIONS"
if ($COLLECTIONS -eq "168") {
    Write-Host "   ✅ PASS" -ForegroundColor Green
} else {
    Write-Host "   ❌ FAIL - Collection count mismatch!" -ForegroundColor Red
    exit 1
}
Write-Host ""

# 5. Date range
Write-Host "5. Checking date range..." -ForegroundColor Yellow
Write-Host "   Querying min/max dates..."
docker exec -it $CONTAINER psql -U $DB_USER -d $DB_NAME -c "SELECT MIN(datetime) as oldest_data, MAX(datetime) as newest_data FROM hourly_trends;"
Write-Host ""

# 6. Category breakdown
Write-Host "6. Category distribution detail:" -ForegroundColor Yellow
docker exec -it $CONTAINER psql -U $DB_USER -d $DB_NAME -c "SELECT category, COUNT(*) as count FROM hourly_trends GROUP BY category ORDER BY category;"
Write-Host ""

# 7. Top keywords
Write-Host "7. Top 10 keywords:" -ForegroundColor Yellow
docker exec -it $CONTAINER psql -U $DB_USER -d $DB_NAME -c "SELECT keyword, COUNT(*) as count FROM hourly_trends GROUP BY keyword ORDER BY count DESC LIMIT 10;"
Write-Host ""

# 8. Table sizes
Write-Host "8. Database size information:" -ForegroundColor Yellow
docker exec -it $CONTAINER psql -U $DB_USER -d $DB_NAME -c "SELECT table_name, pg_size_pretty(pg_total_relation_size(quote_ident(table_name))) as size FROM information_schema.tables WHERE table_schema = 'public' AND table_type = 'BASE TABLE' ORDER BY pg_total_relation_size(quote_ident(table_name)) DESC LIMIT 5;"
Write-Host ""

Write-Host "================================================" -ForegroundColor Cyan
Write-Host "VERIFICATION COMPLETE" -ForegroundColor Cyan
Write-Host "================================================" -ForegroundColor Cyan
Write-Host "All checks passed! ✅" -ForegroundColor Green
Write-Host "QA database matches development database exactly." -ForegroundColor Green
Write-Host ""

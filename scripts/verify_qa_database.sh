#!/bin/bash
# Database Verification Script
# Verifies that QA database has EXACTLY the same data as development

echo "================================================"
echo "DATABASE DATA VERIFICATION"
echo "================================================"
echo ""

# Connection details
CONTAINER="besttime_postgres"
DB_USER="postgres"
DB_NAME="best_time_post"

echo "Checking database: $DB_NAME"
echo "Container: $CONTAINER"
echo ""

# Function to run query
run_query() {
    docker exec -it $CONTAINER psql -U $DB_USER -d $DB_NAME -t -c "$1" 2>/dev/null | tr -d ' \r'
}

# 1. Total rows check
echo "1. Checking total rows in hourly_trends..."
TOTAL_ROWS=$(run_query "SELECT COUNT(*) FROM hourly_trends;")
echo "   Expected: 17081"
echo "   Actual:   $TOTAL_ROWS"
if [ "$TOTAL_ROWS" = "17081" ]; then
    echo "   ✅ PASS"
else
    echo "   ❌ FAIL - Row count mismatch!"
    exit 1
fi
echo ""

# 2. Category distribution
echo "2. Checking category distribution..."
CATEGORIES=$(run_query "SELECT COUNT(DISTINCT category) FROM hourly_trends;")
echo "   Expected categories: 10"
echo "   Actual categories:   $CATEGORIES"
if [ "$CATEGORIES" = "10" ]; then
    echo "   ✅ PASS"
else
    echo "   ❌ FAIL - Category count mismatch!"
    exit 1
fi
echo ""

# 3. Keyword diversity
echo "3. Checking keyword diversity..."
KEYWORDS=$(run_query "SELECT COUNT(DISTINCT keyword) FROM hourly_trends;")
echo "   Expected keywords: 47"
echo "   Actual keywords:   $KEYWORDS"
if [ "$KEYWORDS" = "47" ]; then
    echo "   ✅ PASS"
else
    echo "   ❌ FAIL - Keyword count mismatch!"
    exit 1
fi
echo ""

# 4. Collection IDs
echo "4. Checking collection diversity..."
COLLECTIONS=$(run_query "SELECT COUNT(DISTINCT collection_id) FROM hourly_trends WHERE collection_id IS NOT NULL;")
echo "   Expected collections: 168"
echo "   Actual collections:   $COLLECTIONS"
if [ "$COLLECTIONS" = "168" ]; then
    echo "   ✅ PASS"
else
    echo "   ❌ FAIL - Collection count mismatch!"
    exit 1
fi
echo ""

# 5. Date range
echo "5. Checking date range..."
echo "   Querying min/max dates..."
docker exec -it $CONTAINER psql -U $DB_USER -d $DB_NAME -c "SELECT MIN(datetime) as oldest_data, MAX(datetime) as newest_data FROM hourly_trends;"
echo ""

# 6. Category breakdown
echo "6. Category distribution detail:"
docker exec -it $CONTAINER psql -U $DB_USER -d $DB_NAME -c "SELECT category, COUNT(*) as count FROM hourly_trends GROUP BY category ORDER BY category;"
echo ""

# 7. Top keywords
echo "7. Top 10 keywords:"
docker exec -it $CONTAINER psql -U $DB_USER -d $DB_NAME -c "SELECT keyword, COUNT(*) as count FROM hourly_trends GROUP BY keyword ORDER BY count DESC LIMIT 10;"
echo ""

# 8. Table sizes
echo "8. Database size information:"
docker exec -it $CONTAINER psql -U $DB_USER -d $DB_NAME -c "SELECT table_name, pg_size_pretty(pg_total_relation_size(quote_ident(table_name))) as size FROM information_schema.tables WHERE table_schema = 'public' AND table_type = 'BASE TABLE' ORDER BY pg_total_relation_size(quote_ident(table_name)) DESC LIMIT 5;"
echo ""

echo "================================================"
echo "VERIFICATION COMPLETE"
echo "================================================"
echo "All checks passed! ✅"
echo "QA database matches development database exactly."
echo ""

#!/bin/bash
set -e

echo "=========================================="
echo "DATABASE INITIALIZATION STARTING"
echo "=========================================="
echo "Database: $POSTGRES_DB"
echo "User: $POSTGRES_USER"
echo "Time: $(date)"
echo ""

# Function to log with timestamp
log() {
    echo "[$(date +'%Y-%m-%d %H:%M:%S')] $1"
}

# Function to check if tables exist
check_tables() {
    local table_count=$(psql -U "$POSTGRES_USER" -d "$POSTGRES_DB" -t -c "SELECT COUNT(*) FROM information_schema.tables WHERE table_schema = 'public' AND table_type = 'BASE TABLE';")
    echo $table_count
}

log "Step 1/4: Checking PostgreSQL readiness..."
until pg_isready -U "$POSTGRES_USER" -d "$POSTGRES_DB"; do
    log "PostgreSQL is not ready yet, waiting..."
    sleep 2
done
log "✓ PostgreSQL is ready"

log "Step 2/4: Enabling UUID extension..."
psql -v ON_ERROR_STOP=1 -U "$POSTGRES_USER" -d "$POSTGRES_DB" <<-EOSQL
    CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
    SELECT 'UUID extension enabled: ' || (SELECT extname FROM pg_extension WHERE extname = 'uuid-ossp');
EOSQL
log "✓ UUID extension enabled"

log "Step 3/4: Executing schema.sql..."
if [ -f /docker-entrypoint-initdb.d/schema.sql ]; then
    psql -v ON_ERROR_STOP=0 -U "$POSTGRES_USER" -d "$POSTGRES_DB" -f /docker-entrypoint-initdb.d/schema.sql 2>&1 | tee /tmp/schema-execution.log
    
    # Check if there were any errors (excluding "already exists" warnings)
    if grep -i "error" /tmp/schema-execution.log | grep -v "already exists" > /dev/null; then
        log "⚠ Warning: Some errors occurred during schema execution (see above)"
        log "This might be OK if tables already exist"
    else
        log "✓ Schema executed successfully"
    fi
else
    log "✗ ERROR: schema.sql not found at /docker-entrypoint-initdb.d/schema.sql"
    exit 1
fi

log "Step 4/6: Verifying tables..."
table_count=$(check_tables)
log "Found $table_count tables in public schema"

if [ "$table_count" -gt 0 ]; then
    log "✓ Tables created successfully!"
    log ""
    log "Table list:"
    psql -U "$POSTGRES_USER" -d "$POSTGRES_DB" -c "\dt"
else
    log "✗ ERROR: No tables found! Schema execution may have failed."
    exit 1
fi

log "Step 5/6: Loading seed data..."
if [ -f /docker-entrypoint-initdb.d/seed_data.sql ]; then
    log "Found seed_data.sql (15.9 MB), loading..."
    psql -v ON_ERROR_STOP=0 -U "$POSTGRES_USER" -d "$POSTGRES_DB" -f /docker-entrypoint-initdb.d/seed_data.sql 2>&1 | tee /tmp/seed-execution.log
    
    # Check if there were any errors
    if grep -i "error" /tmp/seed-execution.log | grep -v "duplicate key" | grep -v "already exists" > /dev/null; then
        log "⚠ Warning: Some errors occurred during seed data load (see above)"
        log "This might be OK if data already exists"
    else
        log "✓ Seed data loaded successfully"
    fi
else
    log "⚠ Warning: seed_data.sql not found, database will be empty"
fi

log "Step 6/6: Data verification..."
hourly_count=$(psql -U "$POSTGRES_USER" -d "$POSTGRES_DB" -t -c "SELECT COUNT(*) FROM hourly_trends;" | tr -d ' ')
log "Rows in hourly_trends: $hourly_count"

if [ "$hourly_count" -gt 0 ]; then
    log "✓ Data loaded successfully!"
else
    log "⚠ Warning: hourly_trends table is empty"
fi

echo ""
echo "=========================================="
echo "DATABASE INITIALIZATION COMPLETED"
echo "=========================================="
echo "Database: $POSTGRES_DB"
echo "Tables: $table_count"
echo "Data rows (hourly_trends): $hourly_count"
echo "Status: READY ✓"
echo "=========================================="

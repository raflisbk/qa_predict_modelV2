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

log "Step 4/4: Verifying tables..."
table_count=$(check_tables)
log "Found $table_count tables in public schema"

if [ "$table_count" -gt 0 ]; then
    log "✓ Tables created successfully!"
    log ""
    log "Table list:"
    psql -U "$POSTGRES_USER" -d "$POSTGRES_DB" -c "\dt"
    log ""
    log "View list:"
    psql -U "$POSTGRES_USER" -d "$POSTGRES_DB" -c "\dv"
else
    log "✗ ERROR: No tables found! Schema execution may have failed."
    exit 1
fi

echo ""
echo "=========================================="
echo "DATABASE INITIALIZATION COMPLETED"
echo "=========================================="
echo "Database: $POSTGRES_DB"
echo "Tables: $table_count"
echo "Status: READY ✓"
echo "=========================================="

#!/bin/bash
# QA Validation Script - Test Complete Workflow
# This script simulates what QA will do

echo "=========================================="
echo "QA WORKFLOW VALIDATION"
echo "=========================================="
echo ""

# Check prerequisites
echo "[1/6] Checking prerequisites..."
if ! command -v docker &> /dev/null; then
    echo "❌ Docker not found. Please install Docker Desktop."
    exit 1
fi

if ! command -v python &> /dev/null; then
    echo "❌ Python not found. Please install Python 3.9+"
    exit 1
fi

echo "✓ Docker found"
echo "✓ Python found"
echo ""

# Check .env file
echo "[2/6] Checking .env file..."
if [ ! -f ".env" ]; then
    echo "⚠ .env not found. Creating from .env.example..."
    cp .env.example .env
    echo "✓ .env created"
else
    echo "✓ .env exists"
fi
echo ""

# Check Docker is running
echo "[3/6] Checking Docker status..."
if ! docker info &> /dev/null; then
    echo "❌ Docker is not running. Please start Docker Desktop."
    exit 1
fi
echo "✓ Docker is running"
echo ""

# Start database
echo "[4/6] Starting database..."
docker-compose up -d
echo "⏳ Waiting 30 seconds for initialization..."
sleep 30
echo ""

# Check container status
echo "[5/6] Checking container status..."
CONTAINER_STATUS=$(docker-compose ps --format json | python -c "import sys, json; data = json.loads(sys.stdin.read()); print(data[0]['Health'] if isinstance(data, list) and len(data) > 0 else 'unknown')" 2>/dev/null || echo "unknown")

if [ "$CONTAINER_STATUS" = "healthy" ]; then
    echo "✓ Container is healthy"
else
    echo "⚠ Container status: $CONTAINER_STATUS"
    echo "Checking logs..."
    docker-compose logs postgres | tail -20
fi
echo ""

# Verify database
echo "[6/6] Verifying database setup..."
python scripts/verify_db.py

echo ""
echo "=========================================="
echo "QA WORKFLOW VALIDATION COMPLETE"
echo "=========================================="
echo ""
echo "Next steps:"
echo "1. Open DBeaver"
echo "2. Create new PostgreSQL connection:"
echo "   - Host: localhost"
echo "   - Port: 5432"
echo "   - Database: best_time_post"
echo "   - User: postgres"
echo "   - Password: postgres"
echo "3. Test connection"
echo "4. Browse tables (should see 16 tables)"
echo ""

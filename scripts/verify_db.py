"""
Database Verification Script for QA
Verifies that Docker database is properly initialized

Usage:
    python scripts/verify_db.py
"""

import os
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.database.db_manager import SessionLocal, test_connection
from sqlalchemy import text


def log_success(msg):
    """Print success message"""
    print(f"[OK] {msg}")


def log_error(msg):
    """Print error message"""
    print(f"[ERROR] {msg}")


def log_warning(msg):
    """Print warning message"""
    print(f"[WARN] {msg}")


def log_info(msg):
    """Print info message"""
    print(f"[INFO] {msg}")


def check_connection():
    """Check database connection"""
    log_info("Step 1/5: Testing database connection...")
    if test_connection():
        log_success("Database connection successful")
        return True
    else:
        log_error("Database connection failed")
        log_error("Please check:")
        log_error("  - Docker container is running: docker-compose ps")
        log_error("  - .env settings match docker-compose.yml")
        log_error("  - POSTGRES_HOST=localhost (for local Docker)")
        log_error("  - POSTGRES_PORT=5432 (default)")
        return False


def check_uuid_extension():
    """Check if UUID extension is enabled"""
    log_info("\nStep 2/5: Checking UUID extension...")
    session = SessionLocal()
    
    try:
        result = session.execute(text("""
            SELECT extname, extversion 
            FROM pg_extension 
            WHERE extname = 'uuid-ossp'
        """))
        
        row = result.fetchone()
        if row:
            log_success(f"UUID extension enabled (version: {row[1]})")
            return True
        else:
            log_error("UUID extension not found")
            log_error("This is required for uuid_generate_v4() function")
            return False
            
    except Exception as e:
        log_error(f"Error checking UUID extension: {e}")
        return False
    finally:
        session.close()


def check_tables():
    """Check if all expected tables exist"""
    log_info("\nStep 3/5: Checking tables...")
    session = SessionLocal()
    
    expected_tables = [
        'categories',
        'daily_trends',
        'hourly_trends',
        'related_topics',
        'related_queries',
        'predictions',
        'collection_logs',
        'model_metrics',
        'processing_logs',
        'training_logs',
        'experiment_logs',
        'test_daily_trends',
        'test_hourly_trends',
        'test_related_topics',
        'test_related_queries',
        'test_runs'
    ]
    
    try:
        result = session.execute(text("""
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = 'public' 
            AND table_type = 'BASE TABLE'
            ORDER BY table_name
        """))
        
        actual_tables = [row[0] for row in result]
        
        log_info(f"Found {len(actual_tables)} tables:")
        for table in actual_tables:
            log_info(f"  - {table}")
        
        # Check for missing tables
        missing = set(expected_tables) - set(actual_tables)
        if missing:
            log_warning(f"\nMissing tables: {', '.join(missing)}")
            return False
        
        log_success(f"\nAll {len(expected_tables)} expected tables exist")
        return True
        
    except Exception as e:
        log_error(f"Error checking tables: {e}")
        return False
    finally:
        session.close()


def check_views():
    """Check if views exist"""
    log_info("\nStep 4/5: Checking views...")
    session = SessionLocal()
    
    expected_views = [
        'v_daily_trends_analysis',
        'v_hourly_trends_analysis',
        'v_top_predictions',
        'v_processing_pipeline_status',
        'v_training_summary',
        'v_experiment_tracking',
        'v_pipeline_health',
        'v_test_runs_summary'
    ]
    
    try:
        result = session.execute(text("""
            SELECT table_name 
            FROM information_schema.views 
            WHERE table_schema = 'public'
            ORDER BY table_name
        """))
        
        actual_views = [row[0] for row in result]
        
        log_info(f"Found {len(actual_views)} views:")
        for view in actual_views:
            log_info(f"  - {view}")
        
        # Check for missing views
        missing = set(expected_views) - set(actual_views)
        if missing:
            log_warning(f"\nMissing views: {', '.join(missing)}")
            return False
        
        log_success(f"\nAll {len(expected_views)} expected views exist")
        return True
        
    except Exception as e:
        log_error(f"Error checking views: {e}")
        return False
    finally:
        session.close()


def check_initial_data():
    """Check if initial category data exists"""
    log_info("\nStep 5/5: Checking initial data...")
    session = SessionLocal()
    
    try:
        result = session.execute(text("SELECT COUNT(*) FROM categories"))
        count = result.scalar()
        
        if count > 0:
            log_success(f"Found {count} categories")
            
            # Show sample data
            result = session.execute(text("""
                SELECT category_name, category_code 
                FROM categories 
                LIMIT 3
            """))
            
            log_info("Sample categories:")
            for row in result:
                log_info(f"  - {row[0]} ({row[1]})")
            
            return True
        else:
            log_warning("No categories found (initial data not loaded)")
            return False
            
    except Exception as e:
        log_error(f"Error checking initial data: {e}")
        return False
    finally:
        session.close()


def main():
    """Main verification flow"""
    print("=" * 60)
    print("DATABASE VERIFICATION FOR QA")
    print("=" * 60)
    print()
    
    checks = [
        ("Connection", check_connection),
        ("UUID Extension", check_uuid_extension),
        ("Tables", check_tables),
        ("Views", check_views),
        ("Initial Data", check_initial_data)
    ]
    
    results = {}
    for name, check_func in checks:
        try:
            results[name] = check_func()
        except Exception as e:
            log_error(f"{name} check failed: {e}")
            results[name] = False
    
    # Summary
    print()
    print("=" * 60)
    print("VERIFICATION SUMMARY")
    print("=" * 60)
    
    all_passed = True
    for name, passed in results.items():
        status = "[PASS]" if passed else "[FAIL]"
        print(f"{name:20s}: {status}")
        if not passed:
            all_passed = False
    
    print("=" * 60)
    
    if all_passed:
        print("\n[SUCCESS] ALL CHECKS PASSED!")
        print("\nYou can now:")
        print("  1. Connect with DBeaver using settings from .env")
        print("  2. Run data collection scripts")
        print("  3. Start development")
        print()
        return 0
    else:
        print("\n[FAILED] SOME CHECKS FAILED")
        print("\nTroubleshooting:")
        print("  1. Check Docker logs: docker-compose logs postgres")
        print("  2. Restart containers: docker-compose restart")
        print("  3. Fresh start: docker-compose down -v && docker-compose up -d")
        print("  4. Check .env settings match docker-compose.yml")
        print()
        return 1


if __name__ == "__main__":
    sys.exit(main())


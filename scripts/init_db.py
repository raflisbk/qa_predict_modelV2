"""
Database Initialization Script
Executes schema.sql to create all tables

Usage:
    python scripts/init_db.py
"""

import os
import sys
from pathlib import Path
from loguru import logger
from sqlalchemy import text

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.database.db_manager import SessionLocal, engine, test_connection


def read_schema_file():
    """Read schema.sql file"""
    schema_path = project_root / "database" / "schema.sql"
    
    if not schema_path.exists():
        logger.error(f"Schema file not found: {schema_path}")
        return None
    
    logger.info(f"Reading schema from: {schema_path}")
    
    with open(schema_path, 'r', encoding='utf-8') as f:
        return f.read()


def execute_schema(schema_sql):
    """Execute schema SQL"""
    session = SessionLocal()
    
    try:
        logger.info("Executing schema.sql...")
        
        # Split by semicolon and execute each statement
        statements = [s.strip() for s in schema_sql.split(';') if s.strip()]
        
        for i, statement in enumerate(statements, 1):
            if statement:
                try:
                    session.execute(text(statement))
                    logger.debug(f"Executed statement {i}/{len(statements)}")
                except Exception as e:
                    # Skip if table already exists
                    if "already exists" in str(e):
                        logger.debug(f"Statement {i} skipped (already exists)")
                    else:
                        logger.warning(f"Statement {i} failed: {e}")
        
        session.commit()
        logger.success("Schema executed successfully!")
        
    except Exception as e:
        session.rollback()
        logger.error(f"Failed to execute schema: {e}")
        raise
    finally:
        session.close()


def verify_tables():
    """Verify tables were created"""
    session = SessionLocal()
    
    try:
        logger.info("Verifying tables...")
        
        # Query to get all tables
        result = session.execute(text("""
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = 'public' 
            ORDER BY table_name
        """))
        
        tables = [row[0] for row in result]
        
        if tables:
            logger.success(f"Found {len(tables)} tables:")
            for table in tables:
                logger.info(f"  - {table}")  # Changed from ✓ to -
            return True
        else:
            logger.error("No tables found!")
            return False
            
    except Exception as e:
        logger.error(f"Failed to verify tables: {e}")
        return False
    finally:
        session.close()


def main():
    """Main entry point"""
    logger.remove()
    logger.add(
        sys.stdout,
        format="<green>{time:HH:mm:ss}</green> | <level>{level: <8}</level> | <level>{message}</level>",
        level="INFO"
    )
    
    logger.info("="*60)
    logger.info("DATABASE INITIALIZATION")
    logger.info("="*60)
    
    # Test connection
    logger.info("\n[1/3] Testing database connection...")
    if not test_connection():
        logger.error("Database connection failed!")
        logger.error("Make sure Docker is running: docker-compose up -d")
        sys.exit(1)
    
    logger.success("Database connection OK")
    
    # Read schema
    logger.info("\n[2/3] Reading schema.sql...")
    schema_sql = read_schema_file()
    
    if not schema_sql:
        logger.error("Failed to read schema file")
        sys.exit(1)
    
    logger.success(f"Schema loaded ({len(schema_sql)} characters)")
    
    # Execute schema
    logger.info("\n[3/3] Executing schema...")
    try:
        execute_schema(schema_sql)
    except Exception as e:
        logger.error(f"Schema execution failed: {e}")
        sys.exit(1)
    
    # Verify
    logger.info("\n[Verification] Checking tables...")
    if verify_tables():
        logger.info("\n" + "="*60)
        logger.success("DATABASE INITIALIZATION COMPLETED!")
        logger.info("="*60)
        logger.info("\nYou can now run:")
        logger.info("  python data_collection/test_fetch_daily.py")
        logger.info("  python data_collection/test_fetch_hourly.py")
        logger.info("="*60)
    else:
        logger.error("\nDatabase initialization failed!")
        sys.exit(1)


if __name__ == "__main__":
    main()

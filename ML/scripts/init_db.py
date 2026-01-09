"""
Database Initialization Script - Fixed for PostgreSQL Functions
Executes schema.sql properly handling dollar-quoted strings

Usage:
    python scripts/init_db.py
"""

import os
import sys
from pathlib import Path
from loguru import logger

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.database.db_manager import SessionLocal, test_connection


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
    """Execute schema SQL - handles PostgreSQL functions properly"""
    session = SessionLocal()
    
    try:
        logger.info("Executing schema.sql...")
        
        # Use raw connection to execute entire schema at once
        # This preserves dollar-quoted strings in functions
        connection = session.connection().connection
        cursor = connection.cursor()
        
        try:
            cursor.execute(schema_sql)
            connection.commit()
            logger.success("Schema executed successfully!")
        except Exception as e:
            connection.rollback()
            # Log error but don't fail if tables already exist
            if "already exists" in str(e).lower():
                logger.warning("Some objects already exist (this is OK)")
                connection.commit()
            else:
                logger.error(f"Schema execution failed: {e}")
                raise
        finally:
            cursor.close()
        
    except Exception as e:
        logger.error(f"Failed to execute schema: {e}")
        raise
    finally:
        session.close()


def verify_tables():
    """Verify tables were created"""
    session = SessionLocal()
    
    try:
        logger.info("Verifying tables...")
        
        # Get all schemas
        from sqlalchemy import text
        schema_result = session.execute(text("""
            SELECT schema_name 
            FROM information_schema.schemata 
            WHERE schema_name NOT IN ('pg_catalog', 'information_schema')
            ORDER BY schema_name
        """))
        
        schemas = [row[0] for row in schema_result]
        logger.debug(f"Available schemas: {', '.join(schemas)}")
        
        # Find tables in any schema
        all_tables = []
        for schema in schemas:
            result = session.execute(text(f"""
                SELECT table_name 
                FROM information_schema.tables 
                WHERE table_schema = '{schema}'
                ORDER BY table_name
            """))
            
            schema_tables = [row[0] for row in result]
            if schema_tables:
                logger.debug(f"Schema '{schema}': {len(schema_tables)} tables found")
                all_tables.extend([(schema, table) for table in schema_tables])
        
        if all_tables:
            logger.success(f"Found {len(all_tables)} tables/views:")
            for schema, table in all_tables:
                logger.info(f"  - {schema}.{table}")
            return True
        else:
            logger.error("No tables found in any schema!")
            logger.error(f"Checked schemas: {', '.join(schemas)}")
            return False
            
    except Exception as e:
        logger.error(f"Failed to verify tables: {e}")
        import traceback
        logger.error(traceback.format_exc())
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
        logger.error("Check your .env settings:")
        logger.error("  - POSTGRES_HOST")
        logger.error("  - POSTGRES_DB")
        logger.error("  - POSTGRES_USER")
        logger.error("  - POSTGRES_PASSWORD")
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
        logger.error("Please check:")
        logger.error("  1. Database permissions (user can CREATE TABLE)")
        logger.error("  2. Database name in .env matches actual database")
        logger.error("  3. Schema.sql syntax is correct")
        sys.exit(1)


if __name__ == "__main__":
    main()

import sys
import os

# Add project root (ML folder) to path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.insert(0, project_root)

from src.database.db_manager import SessionLocal, text
import pandas as pd

session = SessionLocal()

# 1. Sample data
print("=" * 60)
print("SAMPLE HOURLY TRENDS DATA")
print("=" * 60)
query = text("""
    SELECT datetime, interest_value, category, keyword
    FROM hourly_trends
    ORDER BY datetime DESC
    LIMIT 10
""")
df = pd.read_sql(query, session.bind)
print(df.to_string())

# 2. Data distribution
print("\n" + "=" * 60)
print("DATA DISTRIBUTION PER CATEGORY")
print("=" * 60)
query = text("""
    SELECT 
        category, 
        COUNT(*) as count,
        MIN(datetime) as min_date,
        MAX(datetime) as max_date,
        AVG(interest_value) as avg_interest,
        COUNT(DISTINCT keyword) as unique_keywords
    FROM hourly_trends
    GROUP BY category
    ORDER BY count DESC
""")
df = pd.read_sql(query, session.bind)
print(df.to_string())

# 3. Data quality check
print("\n" + "=" * 60)
print("DATA QUALITY CHECK")
print("=" * 60)
query = text("""
    SELECT 
        COUNT(*) as total_records,
        COUNT(DISTINCT category) as unique_categories,
        COUNT(DISTINCT keyword) as unique_keywords,
        SUM(CASE WHEN interest_value IS NULL THEN 1 ELSE 0 END) as null_values,
        MIN(interest_value) as min_interest,
        MAX(interest_value) as max_interest,
        AVG(interest_value) as avg_interest
    FROM hourly_trends
""")
df = pd.read_sql(query, session.bind)
print(df.to_string())

# 4. Check for gaps in data
print("\n" + "=" * 60)
print("DATE RANGE ANALYSIS")
print("=" * 60)
query = text("""
    SELECT 
        MIN(datetime) as first_record,
        MAX(datetime) as last_record,
        MAX(datetime) - MIN(datetime) as date_span
    FROM hourly_trends
""")
df = pd.read_sql(query, session.bind)
print(df.to_string())

session.close()
print("\n✓ Database check completed")

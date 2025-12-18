#!/usr/bin/env python3
"""
Run migration 0025: Admin RLS Bypass

Updates RLS policies to allow admin users to see all data.
"""
import os
import sys
from pathlib import Path

# Add the api src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "apps" / "api" / "src"))

import psycopg
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")
if not DATABASE_URL:
    print("ERROR: DATABASE_URL not set")
    sys.exit(1)

migration_sql = Path(__file__).parent.parent / "db" / "migrations" / "0025_admin_rls_bypass.sql"

if not migration_sql.exists():
    print(f"ERROR: Migration file not found: {migration_sql}")
    sys.exit(1)

print(f"Running migration: {migration_sql.name}")
print(f"Database: {DATABASE_URL.split('@')[1] if '@' in DATABASE_URL else 'local'}")

with psycopg.connect(DATABASE_URL) as conn:
    with conn.cursor() as cur:
        sql = migration_sql.read_text()
        cur.execute(sql)
        conn.commit()
        print("✓ Migration completed successfully!")
        
        # Verify the policies were updated
        cur.execute("""
            SELECT tablename, policyname 
            FROM pg_policies 
            WHERE policyname LIKE '%rls%'
            ORDER BY tablename
        """)
        policies = cur.fetchall()
        print(f"\nUpdated RLS policies ({len(policies)}):")
        for table, policy in policies:
            print(f"  - {table}: {policy}")



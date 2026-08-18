#!/usr/bin/env python3
"""Run migration 0037_property_report_stats.sql on staging database."""

import psycopg2
import os
import sys

DB_URL = os.environ.get('DATABASE_URL')
if not DB_URL:
    raise SystemExit(
        "ERROR: DATABASE_URL is not set. This script has no default target; "
        "set it explicitly, e.g. DATABASE_URL=postgresql://user:pass@host/db"
    )

def main():
    print("Connecting to staging database...")
    conn = psycopg2.connect(DB_URL)
    conn.autocommit = True
    cur = conn.cursor()
    
    print("Reading migration file...")
    with open("db/migrations/0037_property_report_stats.sql", "r") as f:
        sql = f.read()
    
    print("Executing migration 0037_property_report_stats.sql...")
    try:
        cur.execute(sql)
        print("[OK] Migration executed successfully!")
    except Exception as e:
        print(f"[ERROR] Migration failed: {e}")
        sys.exit(1)
    
    # Verify tables created
    print("\nVerifying tables created...")
    cur.execute("""
        SELECT table_name 
        FROM information_schema.tables 
        WHERE table_schema = 'public'
        AND (table_name LIKE 'property_report_stats%' OR table_name = 'platform_property_stats')
        ORDER BY table_name
    """)
    tables = cur.fetchall()
    print(f"[OK] Tables: {[t[0] for t in tables]}")
    
    # Verify functions created
    print("\nVerifying functions created...")
    cur.execute("""
        SELECT routine_name 
        FROM information_schema.routines 
        WHERE routine_schema = 'public'
        AND routine_name LIKE '%property_stats%'
        ORDER BY routine_name
    """)
    functions = cur.fetchall()
    print(f"[OK] Functions: {[f[0] for f in functions]}")
    
    # Check platform_property_stats singleton
    cur.execute("SELECT * FROM platform_property_stats WHERE id = 1")
    row = cur.fetchone()
    if row:
        print("[OK] Platform stats singleton initialized")
    
    cur.close()
    conn.close()
    print("\n[OK] Migration 0037 completed successfully!")

if __name__ == "__main__":
    main()


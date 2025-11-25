#!/usr/bin/env python3
"""
Run migration 0008: Create affiliate_branding table

This table is required for the branding service to work.
"""
import os
import sys
import psycopg

def main():
    database_url = os.environ.get("DATABASE_URL")
    if not database_url:
        print("[!] DATABASE_URL environment variable not set")
        sys.exit(1)
    
    print("[*] Running migration 0008_create_affiliate_branding.sql...")
    
    # Read the migration file
    migration_path = os.path.join(os.path.dirname(__file__), "..", "db", "migrations", "0008_create_affiliate_branding.sql")
    with open(migration_path, "r") as f:
        sql = f.read()
    
    # Execute the migration
    try:
        with psycopg.connect(database_url, autocommit=True) as conn:
            with conn.cursor() as cur:
                cur.execute(sql)
        print("[+] Migration completed successfully!")
    except Exception as e:
        print(f"[-] Migration failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()


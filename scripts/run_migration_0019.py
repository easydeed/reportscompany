#!/usr/bin/env python3
"""
Run migration 0019 to add email_logo_url column to affiliate_branding table.

Usage:
    python scripts/run_migration_0019.py

Or with explicit connection string:
    python scripts/run_migration_0019.py "postgresql://user:pass@host/db"
"""
import sys
import psycopg

# Default to staging database
DEFAULT_DB_URL = "postgresql://mr_staging_db_user:vlFYf9ykajrJC7y62as6RKazBSr37fUU@dpg-d474qiqli9vc738g17e0-a.oregon-postgres.render.com/mr_staging_db"

MIGRATION_SQL = """
-- Migration 0019: Add email_logo_url to affiliate_branding
-- Allows affiliates to specify a separate logo for email headers (light version for gradient backgrounds)

ALTER TABLE affiliate_branding
ADD COLUMN IF NOT EXISTS email_logo_url TEXT;

COMMENT ON COLUMN affiliate_branding.email_logo_url IS 'Separate logo URL for email headers (light version for gradient backgrounds)';
"""

def run_migration(db_url: str):
    print(f"Connecting to database...")
    
    with psycopg.connect(db_url) as conn:
        with conn.cursor() as cur:
            print("Running migration 0019: Add email_logo_url column...")
            cur.execute(MIGRATION_SQL)
            conn.commit()
            print("✅ Migration completed successfully!")
            
            # Verify the column exists
            cur.execute("""
                SELECT column_name, data_type 
                FROM information_schema.columns 
                WHERE table_name = 'affiliate_branding' 
                AND column_name = 'email_logo_url'
            """)
            result = cur.fetchone()
            if result:
                print(f"✅ Verified: Column '{result[0]}' exists with type '{result[1]}'")
            else:
                print("⚠️ Warning: Column verification failed")

if __name__ == "__main__":
    db_url = sys.argv[1] if len(sys.argv) > 1 else DEFAULT_DB_URL
    run_migration(db_url)


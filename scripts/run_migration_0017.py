#!/usr/bin/env python3
"""
Run migration 0017: Add user profile fields

This migration adds the following columns to the users table:
- first_name VARCHAR(100)
- last_name VARCHAR(100)
- company_name VARCHAR(200)
- phone VARCHAR(50)
- avatar_url VARCHAR(500)
- password_changed_at TIMESTAMP

Usage:
    DATABASE_URL=postgresql://... python scripts/run_migration_0017.py
"""

import os
import sys

def run_migration():
    database_url = os.environ.get("DATABASE_URL")
    if not database_url:
        print("ERROR: DATABASE_URL environment variable not set")
        sys.exit(1)

    try:
        import psycopg
    except ImportError:
        print("ERROR: psycopg not installed. Run: pip install psycopg[binary]")
        sys.exit(1)

    print("Connecting to database...")
    
    try:
        with psycopg.connect(database_url) as conn:
            with conn.cursor() as cur:
                print("Running migration 0017_user_profile_fields.sql...")
                
                # Add profile fields to users table
                statements = [
                    "ALTER TABLE users ADD COLUMN IF NOT EXISTS first_name VARCHAR(100)",
                    "ALTER TABLE users ADD COLUMN IF NOT EXISTS last_name VARCHAR(100)",
                    "ALTER TABLE users ADD COLUMN IF NOT EXISTS company_name VARCHAR(200)",
                    "ALTER TABLE users ADD COLUMN IF NOT EXISTS phone VARCHAR(50)",
                    "ALTER TABLE users ADD COLUMN IF NOT EXISTS avatar_url VARCHAR(500)",
                    "ALTER TABLE users ADD COLUMN IF NOT EXISTS password_changed_at TIMESTAMP",
                    "CREATE INDEX IF NOT EXISTS idx_users_email ON users(email)",
                ]
                
                for stmt in statements:
                    print(f"  Executing: {stmt[:60]}...")
                    cur.execute(stmt)
                
                conn.commit()
                print("")
                print("Migration 0017_user_profile_fields.sql applied successfully!")
                
                # Verify columns exist
                cur.execute("""
                    SELECT column_name, data_type 
                    FROM information_schema.columns 
                    WHERE table_name = 'users' 
                    AND column_name IN ('first_name', 'last_name', 'company_name', 'phone', 'avatar_url', 'password_changed_at')
                    ORDER BY column_name
                """)
                columns = cur.fetchall()
                print(f"Verified {len(columns)} new columns added:")
                for col in columns:
                    print(f"  - {col[0]}: {col[1]}")
                    
    except Exception as e:
        print(f"ERROR: Migration failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    run_migration()



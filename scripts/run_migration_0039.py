#!/usr/bin/env python3
"""
Run migration 0039: Lead Pages Feature

Usage:
    python scripts/run_migration_0039.py

Requires:
    - DATABASE_URL environment variable or external DB connection string
    - psycopg2 library
"""

import os
import sys

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

try:
    import psycopg2
except ImportError:
    print("ERROR: psycopg2 not installed. Run: pip install psycopg2-binary")
    sys.exit(1)


def get_db_url():
    """Get database URL from environment or use default."""
    url = os.environ.get("DATABASE_URL")
    if url:
        return url
    
    # Try external DB if no env var
    return input("Enter database connection string: ").strip()


def run_migration():
    """Execute the migration SQL."""
    db_url = get_db_url()
    
    if not db_url:
        print("ERROR: No database URL provided")
        sys.exit(1)
    
    # Read migration file
    migration_path = os.path.join(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
        "db", "migrations", "0039_lead_pages.sql"
    )
    
    if not os.path.exists(migration_path):
        print(f"ERROR: Migration file not found: {migration_path}")
        sys.exit(1)
    
    with open(migration_path, 'r', encoding='utf-8') as f:
        migration_sql = f.read()
    
    print(f"[INFO] Connecting to database...")
    
    try:
        conn = psycopg2.connect(db_url)
        conn.autocommit = True
        cur = conn.cursor()
        
        print("[INFO] Running migration 0039_lead_pages.sql...")
        
        # Execute the migration
        cur.execute(migration_sql)
        
        print("[OK] Migration completed successfully!")
        
        # Verify by checking for agent_code column
        cur.execute("""
            SELECT column_name FROM information_schema.columns 
            WHERE table_name = 'users' AND column_name = 'agent_code'
        """)
        if cur.fetchone():
            print("[OK] Verified: agent_code column exists in users table")
        else:
            print("[WARN] Could not verify agent_code column")
        
        # Check sms_logs table
        cur.execute("""
            SELECT table_name FROM information_schema.tables 
            WHERE table_name = 'sms_logs'
        """)
        if cur.fetchone():
            print("[OK] Verified: sms_logs table exists")
        else:
            print("[WARN] Could not verify sms_logs table")
        
        # Check if agent codes were generated for existing users
        cur.execute("SELECT COUNT(*) FROM users WHERE agent_code IS NOT NULL")
        count = cur.fetchone()[0]
        print(f"[INFO] {count} users have agent codes")
        
        cur.close()
        conn.close()
        
        print("[DONE] Migration 0039 complete!")
        
    except psycopg2.Error as e:
        print(f"[ERROR] Database error: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"[ERROR] Unexpected error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    print("=" * 60)
    print("Migration 0039: Lead Pages Feature")
    print("=" * 60)
    run_migration()


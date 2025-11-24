#!/usr/bin/env python3
"""
Run migration 0015: Add timezone to schedules
"""
import os
import psycopg

def run_migration():
    database_url = os.getenv("DATABASE_URL")
    if not database_url:
        print("❌ DATABASE_URL environment variable not set")
        return False
    
    print("🔄 Running migration 0015: Add timezone to schedules...")
    
    try:
        with psycopg.connect(database_url) as conn:
            with conn.cursor() as cur:
                # Read migration file
                migration_path = os.path.join(
                    os.path.dirname(os.path.dirname(__file__)),
                    "db", "migrations", "0015_add_timezone_to_schedules.sql"
                )
                
                with open(migration_path, "r") as f:
                    migration_sql = f.read()
                
                # Execute migration
                cur.execute(migration_sql)
                conn.commit()
                
                print("✅ Migration 0015 completed successfully")
                
                # Verify column exists
                cur.execute("""
                    SELECT column_name, data_type, column_default
                    FROM information_schema.columns
                    WHERE table_name = 'schedules' AND column_name = 'timezone'
                """)
                result = cur.fetchone()
                
                if result:
                    print(f"   Column added: {result[0]} ({result[1]}) DEFAULT {result[2]}")
                else:
                    print("   ⚠️ Warning: Column verification failed")
                
                return True
                
    except Exception as e:
        print(f"❌ Migration failed: {e}")
        return False

if __name__ == "__main__":
    success = run_migration()
    exit(0 if success else 1)


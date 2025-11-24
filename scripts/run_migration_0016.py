#!/usr/bin/env python3
"""
Run migration 0016: Add failure tracking to schedules
"""
import os
import psycopg

def run_migration():
    database_url = os.getenv("DATABASE_URL")
    if not database_url:
        print("❌ DATABASE_URL environment variable not set")
        return False
    
    print("🔄 Running migration 0016: Add failure tracking to schedules...")
    
    try:
        with psycopg.connect(database_url) as conn:
            with conn.cursor() as cur:
                # Read migration file
                migration_path = os.path.join(
                    os.path.dirname(os.path.dirname(__file__)),
                    "db", "migrations", "0016_add_failure_tracking_to_schedules.sql"
                )
                
                with open(migration_path, "r") as f:
                    migration_sql = f.read()
                
                # Execute migration
                cur.execute(migration_sql)
                conn.commit()
                
                print("✅ Migration 0016 completed successfully")
                
                # Verify columns exist
                cur.execute("""
                    SELECT column_name, data_type
                    FROM information_schema.columns
                    WHERE table_name = 'schedules' 
                      AND column_name IN ('consecutive_failures', 'last_error', 'last_error_at')
                    ORDER BY column_name
                """)
                results = cur.fetchall()
                
                if len(results) == 3:
                    print("   Columns added:")
                    for col, dtype in results:
                        print(f"     - {col} ({dtype})")
                else:
                    print(f"   ⚠️ Warning: Expected 3 columns, found {len(results)}")
                
                return True
                
    except Exception as e:
        print(f"❌ Migration failed: {e}")
        return False

if __name__ == "__main__":
    success = run_migration()
    exit(0 if success else 1)


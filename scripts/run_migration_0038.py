"""
Run migration 0038_mobile_reports.sql against the database
"""
import psycopg
import os
import sys

# Database connection string
DATABASE_URL = "postgresql://mr_staging_db_user:vlFYf9ykajrJC7y62as6RKazBSr37fUU@dpg-d474qiqli9vc738g17e0-a.oregon-postgres.render.com/mr_staging_db"

# Read migration file
migration_path = os.path.join(os.path.dirname(__file__), "..", "db", "migrations", "0038_mobile_reports.sql")

print("[*] Running migration 0038_mobile_reports.sql")
print(f"[*] Migration file: {migration_path}")

try:
    with open(migration_path, "r") as f:
        migration_sql = f.read()
except FileNotFoundError:
    print(f"[FAIL] Migration file not found: {migration_path}")
    sys.exit(1)

print("[*] Connecting to database...")

try:
    with psycopg.connect(DATABASE_URL) as conn:
        with conn.cursor() as cur:
            print("[*] Executing migration...")
            cur.execute(migration_sql)
            conn.commit()
            print("[OK] Migration completed successfully!")
            
            # Verify tables exist
            cur.execute("""
                SELECT table_name FROM information_schema.tables 
                WHERE table_schema = 'public' AND table_name IN ('consumer_reports', 'report_analytics')
                ORDER BY table_name
            """)
            tables = cur.fetchall()
            print(f"[OK] Created tables: {[t[0] for t in tables]}")
            
            # Verify views exist
            cur.execute("""
                SELECT table_name FROM information_schema.views 
                WHERE table_schema = 'public' AND table_name LIKE 'admin_%'
                ORDER BY table_name
            """)
            views = cur.fetchall()
            print(f"[OK] Created views: {[v[0] for v in views]}")
            
except Exception as e:
    print(f"[FAIL] Migration failed: {e}")
    sys.exit(1)

print("\n[OK] All done!")


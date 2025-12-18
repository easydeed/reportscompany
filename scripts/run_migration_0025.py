#!/usr/bin/env python3
"""Run migration 0025 to add admin RLS bypass."""
import psycopg

DATABASE_URL = "postgresql://mr_staging_db_user:vlFYf9ykajrJC7y62as6RKazBSr37fUU@dpg-d474qiqli9vc738g17e0-a.oregon-postgres.render.com/mr_staging_db"

def main():
    print("Connecting to database...")
    conn = psycopg.connect(DATABASE_URL)
    cur = conn.cursor()

    print("Reading migration file...")
    with open("db/migrations/0025_admin_rls_bypass.sql", "r") as f:
        sql = f.read()

    print("Executing migration...")
    cur.execute(sql)
    conn.commit()
    print("✅ Migration 0025_admin_rls_bypass.sql applied successfully!")

    # Verify policies
    cur.execute("""
        SELECT tablename, policyname 
        FROM pg_policies 
        WHERE policyname LIKE '%rls%'
        ORDER BY tablename
    """)
    print("\nActive RLS Policies:")
    for row in cur.fetchall():
        print(f"  {row[0]}: {row[1]}")

    # Quick data check
    cur.execute("SELECT COUNT(*) FROM accounts")
    accounts = cur.fetchone()[0]
    cur.execute("SELECT COUNT(*) FROM users")
    users = cur.fetchone()[0]
    cur.execute("SELECT COUNT(*) FROM report_generations")
    reports = cur.fetchone()[0]
    
    print(f"\nDatabase stats:")
    print(f"  Accounts: {accounts}")
    print(f"  Users: {users}")
    print(f"  Reports: {reports}")

    conn.close()
    print("\n✅ Done!")

if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""Check database schema and run missing migrations."""
import psycopg

DATABASE_URL = "postgresql://mr_staging_db_user:vlFYf9ykajrJC7y62as6RKazBSr37fUU@dpg-d474qiqli9vc738g17e0-a.oregon-postgres.render.com/mr_staging_db"

def main():
    conn = psycopg.connect(DATABASE_URL)
    cur = conn.cursor()

    print("=== ACCOUNTS TABLE COLUMNS ===")
    cur.execute("""
        SELECT column_name, data_type 
        FROM information_schema.columns 
        WHERE table_name = 'accounts'
        ORDER BY ordinal_position
    """)
    accounts_cols = [row[0] for row in cur.fetchall()]
    for col in accounts_cols:
        print(f"  {col}")

    print()
    print("=== PLANS TABLE COLUMNS ===")
    cur.execute("""
        SELECT column_name, data_type 
        FROM information_schema.columns 
        WHERE table_name = 'plans'
        ORDER BY ordinal_position
    """)
    plans_cols = [row[0] for row in cur.fetchall()]
    for col in plans_cols:
        print(f"  {col}")

    # Check missing columns
    print()
    print("=== MISSING COLUMNS CHECK ===")
    
    if "is_active" not in accounts_cols:
        print("  ❌ accounts.is_active MISSING - running migration 0010...")
        cur.execute("""
            ALTER TABLE accounts
            ADD COLUMN IF NOT EXISTS is_active boolean NOT NULL DEFAULT TRUE
        """)
        conn.commit()
        print("  ✅ accounts.is_active added!")
    else:
        print("  ✅ accounts.is_active exists")

    if "plan_slug" not in plans_cols:
        print("  ❌ plans.plan_slug MISSING - need migration 0013")
    else:
        print("  ✅ plans.plan_slug exists")

    if "plan_name" not in plans_cols:
        print("  ❌ plans.plan_name MISSING - need migration 0013")
    else:
        print("  ✅ plans.plan_name exists")

    conn.close()
    print()
    print("Done!")

if __name__ == "__main__":
    main()








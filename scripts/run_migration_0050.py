#!/usr/bin/env python3
"""
Run migration 0050: Promote Pacific Coast Title to TITLE_COMPANY

Usage:
    python scripts/run_migration_0050.py

Requires:
    - DATABASE_URL environment variable or prompted connection string
    - psycopg2 library

After running, the PCT admin must log out and log back in to get a fresh JWT.
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

try:
    import psycopg2
except ImportError:
    print("ERROR: psycopg2 not installed. Run: pip install psycopg2-binary")
    sys.exit(1)


def get_db_url():
    url = os.environ.get("DATABASE_URL")
    if url:
        return url
    return input("Enter database connection string: ").strip()


def run_migration():
    db_url = get_db_url()
    if not db_url:
        print("ERROR: No database URL provided")
        sys.exit(1)

    migration_path = os.path.join(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
        "db", "migrations", "0050_pct_to_title_company.sql",
    )

    if not os.path.exists(migration_path):
        print(f"ERROR: Migration file not found: {migration_path}")
        sys.exit(1)

    with open(migration_path, "r", encoding="utf-8") as f:
        migration_sql = f.read()

    print("[INFO] Connecting to database...")

    try:
        conn = psycopg2.connect(db_url)
        conn.autocommit = False
        cur = conn.cursor()

        # Show current state first
        print("[INFO] Looking for Pacific Coast Title account...")
        cur.execute("""
            SELECT id::text, name, account_type, plan_slug
            FROM accounts
            WHERE name ILIKE '%%pacific coast%%' OR slug ILIKE '%%pacific-coast%%'
        """)
        rows = cur.fetchall()
        if not rows:
            print("[WARN] No account matching 'pacific coast' found. Aborting.")
            conn.close()
            sys.exit(1)

        for row in rows:
            print(f"  Found: id={row[0]}, name={row[1]}, type={row[2]}, plan={row[3]}")

        print("[INFO] Running migration 0050_pct_to_title_company.sql...")
        cur.execute(migration_sql)

        result = cur.fetchone()
        if result:
            print(f"[OK] Updated: id={result[0]}, name={result[1]}, new_type={result[2]}, plan={result[3]}")
        else:
            print("[WARN] No rows were updated — account may already be TITLE_COMPANY.")

        conn.commit()
        print("[OK] Migration committed successfully!")
        print("[NOTE] The PCT admin must log out and log back in to refresh their JWT.")

        cur.close()
        conn.close()

    except psycopg2.Error as e:
        print(f"[ERROR] Database error: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"[ERROR] Unexpected error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    run_migration()

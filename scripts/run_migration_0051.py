#!/usr/bin/env python3
"""
Run migration 0051: Add per-product limit columns to plans and accounts.

Usage:
    DATABASE_URL=postgresql://... python scripts/run_migration_0051.py
"""

import os
import sys

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


STATEMENTS = [
    # 1. Per-product limit columns on plans
    "ALTER TABLE plans ADD COLUMN IF NOT EXISTS market_reports_limit INTEGER",
    "ALTER TABLE plans ADD COLUMN IF NOT EXISTS schedules_limit INTEGER",
    # 2. Populate new columns (only where still NULL)
    """
    UPDATE plans SET
        market_reports_limit = CASE plan_slug
            WHEN 'free'            THEN 3
            WHEN 'sponsored_free'  THEN 3
            WHEN 'starter'         THEN 25
            WHEN 'pro'             THEN 99999
            WHEN 'team'            THEN 99999
            WHEN 'affiliate'       THEN 5000
            WHEN 'solo'            THEN 25
            ELSE 3
        END,
        schedules_limit = CASE plan_slug
            WHEN 'free'            THEN 1
            WHEN 'sponsored_free'  THEN 1
            WHEN 'starter'         THEN 3
            WHEN 'pro'             THEN 99999
            WHEN 'team'            THEN 99999
            WHEN 'affiliate'       THEN 99999
            WHEN 'solo'            THEN 3
            ELSE 1
        END,
        property_reports_per_month = CASE plan_slug
            WHEN 'free'            THEN 1
            WHEN 'sponsored_free'  THEN 1
            WHEN 'starter'         THEN 5
            WHEN 'pro'             THEN 25
            WHEN 'team'            THEN 25
            WHEN 'affiliate'       THEN 100
            WHEN 'solo'            THEN 5
            ELSE 1
        END
    WHERE market_reports_limit IS NULL
    """,
    # 3. Per-product override columns on accounts
    "ALTER TABLE accounts ADD COLUMN IF NOT EXISTS market_reports_limit_override INTEGER",
    "ALTER TABLE accounts ADD COLUMN IF NOT EXISTS schedules_limit_override INTEGER",
    "ALTER TABLE accounts ADD COLUMN IF NOT EXISTS property_reports_limit_override INTEGER",
    # 4. Migrate existing single override → market reports override
    """
    UPDATE accounts
    SET market_reports_limit_override = monthly_report_limit_override
    WHERE monthly_report_limit_override IS NOT NULL
      AND market_reports_limit_override IS NULL
    """,
    # 5. Upsert starter plan
    """
    INSERT INTO plans (plan_slug, plan_name, monthly_report_limit,
                       market_reports_limit, schedules_limit, property_reports_per_month)
    VALUES ('starter', 'Starter', 25, 25, 3, 5)
    ON CONFLICT (plan_slug) DO UPDATE SET
        market_reports_limit       = 25,
        schedules_limit            = 3,
        property_reports_per_month = 5
    """,
    # 6. Insert trial plan if missing
    """
    INSERT INTO plans (plan_slug, plan_name, monthly_report_limit,
                       market_reports_limit, schedules_limit, property_reports_per_month)
    VALUES ('trial', 'Trial', 3, 3, 1, 1)
    ON CONFLICT (plan_slug) DO NOTHING
    """,
]

VERIFY_SQL = """
    SELECT plan_slug, plan_name, market_reports_limit, schedules_limit, property_reports_per_month
    FROM plans
    ORDER BY plan_slug
"""


def run_migration():
    db_url = get_db_url()
    if not db_url:
        print("ERROR: No database URL provided")
        sys.exit(1)

    print("[INFO] Connecting to database...")

    try:
        conn = psycopg2.connect(db_url)
        conn.autocommit = False
        cur = conn.cursor()

        print("[INFO] Running migration 0051 — per-product limits...\n")

        for sql in STATEMENTS:
            stmt = sql.strip()
            label = stmt[:80].replace("\n", " ")
            try:
                cur.execute(stmt)
                print(f"  [OK] {label}...")
            except psycopg2.Error as e:
                if "already exists" in str(e).lower():
                    print(f"  [SKIP] Already exists: {label}")
                    conn.rollback()
                else:
                    print(f"  [ERROR] {e}")
                    conn.rollback()
                    raise

        conn.commit()
        print("\n[OK] Migration 0051 committed.\n")

        # Verify
        print("Verification — plans table:")
        print(f"  {'plan_slug':<20} {'plan_name':<15} {'market':<8} {'scheds':<8} {'prop'}")
        print("  " + "-" * 65)
        cur.execute(VERIFY_SQL)
        for row in cur.fetchall():
            slug, name, mkt, sch, prop = row
            print(f"  {(slug or ''):<20} {(name or ''):<15} {str(mkt):<8} {str(sch):<8} {prop}")

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

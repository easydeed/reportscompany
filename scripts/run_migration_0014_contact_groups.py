#!/usr/bin/env python3
"""
Run migration 0014: create contact_groups and contact_group_members tables.

This script connects directly to the staging database (or DATABASE_URL override)
and applies the schema changes needed for People Groups.
"""

import os
import sys

try:
    import psycopg
except ImportError:
    print("Error: psycopg not installed")
    print("Install with: pip install psycopg")
    sys.exit(1)


DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql://mr_staging_db_user:vlFYf9ykajrJC7y62as6RKazBSr37fUU@dpg-d474qiqli9vc738g17e0-a.oregon-postgres.render.com/mr_staging_db",
)


def run_sql(conn, sql: str, description: str) -> bool:
    """Execute SQL and print a short status line."""
    try:
        with conn.cursor() as cur:
            cur.execute(sql)
        conn.commit()
        print(f"[OK] {description}")
        return True
    except Exception as e:
        print(f"[WARN] {description}: {e}")
        return False


def main():
    print("\n" + "=" * 80)
    print("Migration 0014: Contact Groups for People & Schedules")
    print("=" * 80 + "\n")

    try:
        print("Connecting to database...")
        with psycopg.connect(DATABASE_URL) as conn:
            print("[OK] Connected\n")

            # Step 1: Create contact_groups
            print("Step 1: Creating contact_groups table...")
            run_sql(
                conn,
                """
                CREATE TABLE IF NOT EXISTS contact_groups (
                  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
                  account_id uuid NOT NULL REFERENCES accounts(id) ON DELETE CASCADE,
                  name text NOT NULL,
                  description text,
                  created_at timestamptz NOT NULL DEFAULT now(),
                  updated_at timestamptz NOT NULL DEFAULT now()
                )
                """,
                "Created contact_groups table",
            )

            run_sql(
                conn,
                """
                CREATE INDEX IF NOT EXISTS idx_contact_groups_account_id
                  ON contact_groups(account_id)
                """,
                "Created idx_contact_groups_account_id index",
            )

            # Enable RLS and policy
            run_sql(
                conn,
                "ALTER TABLE contact_groups ENABLE ROW LEVEL SECURITY",
                "Enabled RLS on contact_groups",
            )
            run_sql(
                conn,
                """
                DO $$
                BEGIN
                  IF NOT EXISTS (
                    SELECT 1 FROM pg_policies
                    WHERE schemaname = 'public'
                      AND tablename = 'contact_groups'
                      AND policyname = 'contact_groups_account_isolation'
                  ) THEN
                    CREATE POLICY contact_groups_account_isolation ON contact_groups
                      FOR ALL
                      USING (account_id::text = current_setting('app.current_account_id', TRUE));
                  END IF;
                END $$;
                """,
                "Created contact_groups_account_isolation policy",
            )

            # Attach updated_at trigger if function exists
            run_sql(
                conn,
                """
                DO $$
                BEGIN
                  IF EXISTS (
                    SELECT 1 FROM pg_proc WHERE proname = 'update_updated_at_column'
                  ) THEN
                    DROP TRIGGER IF EXISTS update_contact_groups_updated_at ON contact_groups;
                    CREATE TRIGGER update_contact_groups_updated_at
                      BEFORE UPDATE ON contact_groups
                      FOR EACH ROW
                      EXECUTE FUNCTION update_updated_at_column();
                  END IF;
                END $$;
                """,
                "Attached updated_at trigger to contact_groups (if function exists)",
            )

            # Step 2: Create contact_group_members
            print("\nStep 2: Creating contact_group_members table...")
            run_sql(
                conn,
                """
                CREATE TABLE IF NOT EXISTS contact_group_members (
                  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
                  group_id uuid NOT NULL REFERENCES contact_groups(id) ON DELETE CASCADE,
                  account_id uuid NOT NULL REFERENCES accounts(id) ON DELETE CASCADE,
                  member_type text NOT NULL CHECK (member_type IN ('contact', 'sponsored_agent')),
                  member_id uuid NOT NULL,
                  created_at timestamptz NOT NULL DEFAULT now()
                )
                """,
                "Created contact_group_members table",
            )

            run_sql(
                conn,
                """
                ALTER TABLE contact_group_members
                  ADD CONSTRAINT contact_group_members_unique_member
                  UNIQUE (group_id, member_type, member_id)
                """,
                "Added unique constraint on (group_id, member_type, member_id)",
            )

            run_sql(
                conn,
                """
                CREATE INDEX IF NOT EXISTS idx_contact_group_members_group_id
                  ON contact_group_members(group_id)
                """,
                "Created idx_contact_group_members_group_id index",
            )

            run_sql(
                conn,
                """
                CREATE INDEX IF NOT EXISTS idx_contact_group_members_account_id
                  ON contact_group_members(account_id)
                """,
                "Created idx_contact_group_members_account_id index",
            )

            # Enable RLS and policy
            run_sql(
                conn,
                "ALTER TABLE contact_group_members ENABLE ROW LEVEL SECURITY",
                "Enabled RLS on contact_group_members",
            )

            run_sql(
                conn,
                """
                DO $$
                BEGIN
                  IF NOT EXISTS (
                    SELECT 1 FROM pg_policies
                    WHERE schemaname = 'public'
                      AND tablename = 'contact_group_members'
                      AND policyname = 'contact_group_members_account_isolation'
                  ) THEN
                    CREATE POLICY contact_group_members_account_isolation ON contact_group_members
                      FOR ALL
                      USING (account_id::text = current_setting('app.current_account_id', TRUE));
                  END IF;
                END $$;
                """,
                "Created contact_group_members_account_isolation policy",
            )

            # Verification: show tables
            print("\n" + "=" * 80)
            print("Verification: contact_groups")
            print("=" * 80)
            with conn.cursor() as cur:
                cur.execute(
                    """
                    SELECT column_name, data_type, is_nullable, column_default
                    FROM information_schema.columns
                    WHERE table_name = 'contact_groups'
                    ORDER BY ordinal_position
                    """
                )
                print(f"\n{'Column':<25} {'Type':<20} {'Nullable':<10} {'Default':<30}")
                print("-" * 85)
                for col_name, data_type, nullable, default in cur.fetchall():
                    default_str = (default or "")[:30]
                    print(f"{col_name:<25} {data_type:<20} {nullable:<10} {default_str:<30}")

            print("\n" + "=" * 80)
            print("Verification: contact_group_members")
            print("=" * 80)
            with conn.cursor() as cur:
                cur.execute(
                    """
                    SELECT column_name, data_type, is_nullable, column_default
                    FROM information_schema.columns
                    WHERE table_name = 'contact_group_members'
                    ORDER BY ordinal_position
                    """
                )
                print(f"\n{'Column':<25} {'Type':<20} {'Nullable':<10} {'Default':<30}")
                print("-" * 85)
                for col_name, data_type, nullable, default in cur.fetchall():
                    default_str = (default or "")[:30]
                    print(f"{col_name:<25} {data_type:<20} {nullable:<10} {default_str:<30}")

            print("\n" + "=" * 80)
            print("[SUCCESS] Migration 0014 completed successfully!")
            print("=" * 80 + "\n")

    except Exception as e:
        print(f"\n[ERROR] {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()



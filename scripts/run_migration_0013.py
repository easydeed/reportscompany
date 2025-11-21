#!/usr/bin/env python3
"""
Run migration 0013 to unify plans table with Stripe integration.

This script adds the remaining columns and renames existing ones for consistency.
"""

import os
import sys

try:
    import psycopg
except ImportError:
    print("❌ Error: psycopg not installed")
    print("   Install with: pip install psycopg")
    sys.exit(1)

# Database URL (can be overridden via env var)
DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql://mr_staging_db_user:vlFYf9ykajrJC7y62as6RKazBSr37fUU@dpg-d474qiqli9vc738g17e0-a.oregon-postgres.render.com/mr_staging_db"
)

def run_sql(conn, sql, description):
    """Execute SQL and print result."""
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
    print("\n" + "="*80)
    print("Migration 0013: Unify plans table with Stripe integration")
    print("="*80 + "\n")
    
    try:
        print("Connecting to database...")
        with psycopg.connect(DATABASE_URL) as conn:
            print("[OK] Connected\n")
            
            # Step 1: Add missing columns
            print("Step 1: Adding missing columns...")
            run_sql(conn, """
                ALTER TABLE plans
                ADD COLUMN IF NOT EXISTS is_active BOOLEAN NOT NULL DEFAULT TRUE
            """, "Added is_active column")
            
            run_sql(conn, """
                ALTER TABLE plans
                ADD COLUMN IF NOT EXISTS created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
            """, "Added created_at column")
            
            run_sql(conn, """
                ALTER TABLE plans
                ADD COLUMN IF NOT EXISTS updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
            """, "Added updated_at column")
            
            # Step 2: Rename columns for consistency
            print("\nStep 2: Renaming columns...")
            run_sql(conn, """
                DO $$ 
                BEGIN
                    IF EXISTS (
                        SELECT 1 FROM information_schema.columns 
                        WHERE table_name = 'plans' AND column_name = 'slug'
                    ) THEN
                        ALTER TABLE plans RENAME COLUMN slug TO plan_slug;
                    END IF;
                END $$
            """, "Renamed slug to plan_slug")
            
            run_sql(conn, """
                DO $$ 
                BEGIN
                    IF EXISTS (
                        SELECT 1 FROM information_schema.columns 
                        WHERE table_name = 'plans' AND column_name = 'name'
                    ) THEN
                        ALTER TABLE plans RENAME COLUMN name TO plan_name;
                    END IF;
                END $$
            """, "Renamed name to plan_name")
            
            # Step 3: Create indexes
            print("\nStep 3: Creating indexes...")
            run_sql(conn, """
                CREATE INDEX IF NOT EXISTS idx_plans_stripe_price_id 
                ON plans(stripe_price_id) 
                WHERE stripe_price_id IS NOT NULL
            """, "Created index on stripe_price_id")
            
            run_sql(conn, """
                CREATE INDEX IF NOT EXISTS idx_plans_active 
                ON plans(is_active) 
                WHERE is_active = TRUE
            """, "Created index on is_active")
            
            # Step 4: Create trigger function and trigger
            print("\nStep 4: Creating updated_at trigger...")
            run_sql(conn, """
                CREATE OR REPLACE FUNCTION update_updated_at_column()
                RETURNS TRIGGER AS $$
                BEGIN
                    NEW.updated_at = NOW();
                    RETURN NEW;
                END;
                $$ LANGUAGE plpgsql
            """, "Created trigger function")
            
            run_sql(conn, """
                DROP TRIGGER IF EXISTS update_plans_updated_at ON plans
            """, "Dropped existing trigger (if any)")
            
            run_sql(conn, """
                CREATE TRIGGER update_plans_updated_at
                    BEFORE UPDATE ON plans
                    FOR EACH ROW
                    EXECUTE FUNCTION update_updated_at_column()
            """, "Created update trigger")
            
            # Step 5: Add comments
            print("\nStep 5: Adding table/column comments...")
            run_sql(conn, """
                COMMENT ON TABLE plans IS 'Central catalog of subscription plans with Stripe integration and usage limits'
            """, "Added table comment")
            
            run_sql(conn, """
                COMMENT ON COLUMN plans.plan_slug IS 'Plan identifier: free, pro, team, affiliate, sponsored_free'
            """, "Added plan_slug comment")
            
            run_sql(conn, """
                COMMENT ON COLUMN plans.plan_name IS 'Human-readable plan name displayed in UI'
            """, "Added plan_name comment")
            
            run_sql(conn, """
                COMMENT ON COLUMN plans.stripe_price_id IS 'Stripe Price ID (price_...). NULL for free/internal plans.'
            """, "Added stripe_price_id comment")
            
            run_sql(conn, """
                COMMENT ON COLUMN plans.is_active IS 'Whether plan is currently available for new subscriptions'
            """, "Added is_active comment")
            
            run_sql(conn, """
                COMMENT ON COLUMN plans.description IS 'Marketing description of plan features'
            """, "Added description comment")
            
            # Step 6: Verify final schema
            print("\n" + "="*80)
            print("Verification: Current plans table schema")
            print("="*80)
            
            with conn.cursor() as cur:
                cur.execute("""
                    SELECT column_name, data_type, is_nullable, column_default
                    FROM information_schema.columns 
                    WHERE table_name = 'plans' 
                    ORDER BY ordinal_position
                """)
                
                print(f"\n{'Column':<25} {'Type':<20} {'Nullable':<10} {'Default':<30}")
                print("-" * 85)
                for row in cur.fetchall():
                    col_name, data_type, nullable, default = row
                    default_str = (default or "")[:30]
                    print(f"{col_name:<25} {data_type:<20} {nullable:<10} {default_str:<30}")
            
            # Show current plans
            print("\n" + "="*80)
            print("Current plans in database")
            print("="*80 + "\n")
            
            with conn.cursor() as cur:
                cur.execute("""
                    SELECT plan_slug, plan_name, stripe_price_id, monthly_report_limit, is_active
                    FROM plans
                    ORDER BY plan_slug
                """)
                
                print(f"{'Slug':<20} {'Name':<25} {'Stripe Price ID':<40} {'Limit':<10} {'Active'}")
                print("-" * 120)
                for row in cur.fetchall():
                    slug, name, price_id, limit, active = row
                    price_display = (price_id or "NULL")[:40]
                    print(f"{slug:<20} {name:<25} {price_display:<40} {limit:<10} {active}")
            
            print("\n" + "="*80)
            print("[SUCCESS] Migration 0013 completed successfully!")
            print("="*80 + "\n")
            
    except Exception as e:
        print(f"\n[ERROR] {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()


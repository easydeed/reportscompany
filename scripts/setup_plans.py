#!/usr/bin/env python3
"""
Setup plans table with Solo and Affiliate plans

Usage:
    DATABASE_URL=postgresql://... python scripts/setup_plans.py
"""

import os
import sys
import psycopg2


def main():
    database_url = os.environ.get("DATABASE_URL")
    
    if not database_url:
        print("Error: DATABASE_URL environment variable not set", file=sys.stderr)
        sys.exit(1)
    
    try:
        conn = psycopg2.connect(database_url)
        conn.autocommit = False  # Use transactions
        cur = conn.cursor()
        
        print("Connected to database\n")
        
        # Step 1: Create plans table
        print("Creating plans table...")
        cur.execute("""
            CREATE TABLE IF NOT EXISTS plans (
              plan_slug text PRIMARY KEY,
              plan_name text NOT NULL,
              stripe_price_id text,
              description text,
              created_at timestamptz NOT NULL DEFAULT now(),
              updated_at timestamptz NOT NULL DEFAULT now()
            )
        """)
        conn.commit()  # Commit table creation
        print("[OK] Plans table created\n")
        
        # Step 2: Create index
        print("Creating index...")
        try:
            cur.execute("""
                CREATE INDEX IF NOT EXISTS idx_plans_stripe_price_id 
                ON plans(stripe_price_id) 
                WHERE stripe_price_id IS NOT NULL
            """)
            conn.commit()  # Commit index creation
            print("[OK] Index created\n")
        except psycopg2.Error as e:
            print(f"[SKIP] Index: {e}\n")
            conn.rollback()
        
        # Step 3: Insert plans
        print("Inserting plans...")
        cur.execute("""
            INSERT INTO plans (plan_slug, plan_name, stripe_price_id, description)
            VALUES
              ('solo', 'Solo Agent', 'price_1SO4sDBKYbtiKxfsUnKeJiox', 'Solo plan for individual agents - $19/month'),
              ('affiliate', 'Affiliate', 'price_1STMtfBKYbtiKxfsqQ4r29Cw', 'Affiliate plan for industry partners - $99/month')
            ON CONFLICT (plan_slug) DO UPDATE SET
              plan_name = EXCLUDED.plan_name,
              stripe_price_id = EXCLUDED.stripe_price_id,
              description = EXCLUDED.description,
              updated_at = NOW()
        """)
        conn.commit()  # Commit plan inserts
        print("[OK] Plans inserted\n")
        
        # Step 4: Verify
        print("Current plans:")
        print("-" * 100)
        cur.execute("SELECT plan_slug, plan_name, stripe_price_id, description FROM plans ORDER BY plan_slug")
        for row in cur.fetchall():
            print(f"  {row[0]:<12} {row[1]:<20} {row[2]:<40} {row[3]}")
        print("-" * 100)
        
        print("\n[SUCCESS] Plans setup completed!")
        
        cur.close()
        conn.close()
        
    except psycopg2.Error as e:
        print(f"Database error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()


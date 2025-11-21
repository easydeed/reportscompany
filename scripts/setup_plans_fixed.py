#!/usr/bin/env python3
"""
Setup plans table with Stripe integration

The plans table already exists from migration 0007, so we just need to:
1. Add stripe_price_id column
2. Update the two plans we need: solo and affiliate

Usage:
    DATABASE_URL=postgresql://... python scripts/setup_plans_fixed.py
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
        conn.autocommit = False
        cur = conn.cursor()
        
        print("Connected to database\n")
        
        # Step 1: Add stripe_price_id column if it doesn't exist
        print("Adding stripe_price_id column...")
        try:
            cur.execute("""
                ALTER TABLE plans 
                ADD COLUMN IF NOT EXISTS stripe_price_id text
            """)
            conn.commit()
            print("[OK] Column added\n")
        except psycopg2.Error as e:
            print(f"[INFO] Column might already exist: {e}\n")
            conn.rollback()
        
        # Step 2: Add description column if it doesn't exist  
        print("Adding description column...")
        try:
            cur.execute("""
                ALTER TABLE plans 
                ADD COLUMN IF NOT EXISTS description text
            """)
            conn.commit()
            print("[OK] Column added\n")
        except psycopg2.Error as e:
            print(f"[INFO] Column might already exist: {e}\n")
            conn.rollback()
        
        # Step 3: Update/insert solo plan
        print("Setting up Solo plan...")
        cur.execute("""
            INSERT INTO plans (slug, name, monthly_report_limit, allow_overage, overage_price_cents, stripe_price_id, description)
            VALUES ('solo', 'Solo Agent', 500, false, 0, 'price_1SO4sDBKYbtiKxfsUnKeJiox', 'Solo plan for individual agents - $19/month')
            ON CONFLICT (slug) DO UPDATE SET
              name = EXCLUDED.name,
              stripe_price_id = EXCLUDED.stripe_price_id,
              description = EXCLUDED.description
        """)
        conn.commit()
        print("[OK] Solo plan configured\n")
        
        # Step 4: Update/insert affiliate plan
        print("Setting up Affiliate plan...")
        cur.execute("""
            INSERT INTO plans (slug, name, monthly_report_limit, allow_overage, overage_price_cents, stripe_price_id, description)
            VALUES ('affiliate', 'Affiliate', 10000, false, 0, 'price_1STMtfBKYbtiKxfsqQ4r29Cw', 'Affiliate plan for industry partners - $99/month')
            ON CONFLICT (slug) DO UPDATE SET
              name = EXCLUDED.name,
              stripe_price_id = EXCLUDED.stripe_price_id,
              description = EXCLUDED.description
        """)
        conn.commit()
        print("[OK] Affiliate plan configured\n")
        
        # Step 5: Verify
        print("Current plans with Stripe integration:")
        print("-" * 120)
        print(f"{'slug':<15} {'name':<25} {'limit':<10} {'stripe_price_id':<42} {'description'}")
        print("-" * 120)
        cur.execute("""
            SELECT slug, name, monthly_report_limit, stripe_price_id, description 
            FROM plans 
            ORDER BY slug
        """)
        for row in cur.fetchall():
            price_id = row[3] if row[3] else "NULL"
            desc = row[4] if row[4] else ""
            print(f"{row[0]:<15} {row[1]:<25} {row[2]:<10} {price_id:<42} {desc}")
        print("-" * 120)
        
        print("\n[SUCCESS] Plans setup completed!")
        print("\nNext steps:")
        print("1. Restart your API service on Render")
        print("2. Visit /app/billing to see Stripe prices")
        print("3. Call GET /v1/dev/stripe-prices to verify Stripe integration")
        
        cur.close()
        conn.close()
        
    except psycopg2.Error as e:
        print(f"Database error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()


#!/usr/bin/env python3
"""
Seed Demo Accounts Script
Executes db/seed_demo_accounts.sql against the Render staging database
"""

import os
import sys
import psycopg2
from pathlib import Path

def main():
    # Database connection string
    # You can pass this as an environment variable or command line arg
    db_url = os.environ.get('DATABASE_URL')
    
    if not db_url:
        print("❌ ERROR: DATABASE_URL environment variable not set")
        print("Usage: DATABASE_URL='postgresql://...' python scripts/seed_demo_accounts.py")
        sys.exit(1)
    
    # Read the SQL seed script
    seed_file = Path(__file__).parent.parent / 'db' / 'seed_demo_accounts_v2.sql'
    
    if not seed_file.exists():
        print(f"❌ ERROR: Seed file not found at {seed_file}")
        sys.exit(1)
    
    print(f"📖 Reading seed script from: {seed_file}")
    sql_script = seed_file.read_text()
    
    # Connect to database
    print(f"🔌 Connecting to database...")
    try:
        conn = psycopg2.connect(db_url)
        conn.autocommit = True
        cur = conn.cursor()
        print("✅ Connected successfully")
    except Exception as e:
        print(f"❌ Connection failed: {e}")
        sys.exit(1)
    
    # Execute seed script
    print("\n🌱 Seeding demo accounts...")
    try:
        cur.execute(sql_script)
        print("✅ Seed script executed successfully")
    except Exception as e:
        print(f"❌ Seed script failed: {e}")
        conn.close()
        sys.exit(1)
    
    # Verify accounts were created
    print("\n🔍 Verifying demo accounts...")
    verification_query = """
    SELECT 
        u.email,
        u.role AS user_role,
        a.name AS account_name,
        a.account_type,
        a.plan_slug,
        a.sponsor_account_id IS NOT NULL AS is_sponsored,
        au.role AS account_role
    FROM users u
    JOIN account_users au ON u.id = au.user_id
    JOIN accounts a ON au.account_id = a.id
    WHERE u.email LIKE '%@trendyreports-demo.com'
    ORDER BY u.email;
    """
    
    try:
        cur.execute(verification_query)
        rows = cur.fetchall()
        
        if not rows:
            print("⚠️  WARNING: No demo accounts found!")
        else:
            print(f"✅ Found {len(rows)} demo accounts:\n")
            print(f"{'Email':<45} {'User Role':<10} {'Account Name':<25} {'Account Type':<20} {'Plan':<15} {'Sponsored':<10}")
            print("-" * 140)
            for row in rows:
                email, user_role, acc_name, acc_type, plan, sponsored, acc_role = row
                sponsored_str = "Yes" if sponsored else "No"
                print(f"{email:<45} {user_role:<10} {acc_name:<25} {acc_type:<20} {plan:<15} {sponsored_str:<10}")
    except Exception as e:
        print(f"❌ Verification query failed: {e}")
        conn.close()
        sys.exit(1)
    
    # Verify affiliate branding
    print("\n🎨 Verifying affiliate branding...")
    branding_query = """
    SELECT 
        a.name AS account_name,
        ab.brand_name,
        ab.brand_tagline,
        ab.brand_primary_color
    FROM affiliate_branding ab
    JOIN accounts a ON ab.account_id = a.id
    WHERE a.account_type = 'INDUSTRY_AFFILIATE';
    """
    
    try:
        cur.execute(branding_query)
        branding_rows = cur.fetchall()
        
        if not branding_rows:
            print("⚠️  WARNING: No affiliate branding found!")
        else:
            print(f"✅ Found {len(branding_rows)} affiliate branding entries:\n")
            for row in branding_rows:
                acc_name, brand_name, tagline, color = row
                print(f"  • Account: {acc_name}")
                print(f"    Brand: {brand_name}")
                print(f"    Tagline: {tagline}")
                print(f"    Color: {color}")
    except Exception as e:
        print(f"⚠️  Branding verification failed (table may not exist yet): {e}")
    
    # Close connection
    cur.close()
    conn.close()
    
    print("\n" + "="*80)
    print("🎉 DEMO ACCOUNTS SEEDED SUCCESSFULLY!")
    print("="*80)
    print("\n📖 Next steps:")
    print("  1. Test login at: https://reportscompany-web.vercel.app/login")
    print("  2. See docs/DEMO_ACCOUNTS.md for the 5-minute investor demo walkthrough")
    print("  3. All accounts use password: DemoAdmin123! or DemoAgent123! or DemoAff123!")
    print("\n")

if __name__ == '__main__':
    main()


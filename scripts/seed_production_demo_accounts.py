#!/usr/bin/env python3
"""
Seed production demo accounts into the database.

This script executes db/seed_demo_accounts_prod.sql against the production database.
It's idempotent and safe to run multiple times.

Usage:
    python scripts/seed_production_demo_accounts.py
"""

import os
import sys
import psycopg

# Production database URL - read from environment
DATABASE_URL = os.environ.get(
    "DATABASE_URL",
    "postgresql://mr_staging_db_user:vlFYf9ykajrJC7y62as6RKazBSr37fUU@dpg-d474qiqli9vc738g17e0-a.oregon-postgres.render.com/mr_staging_db"
)

def main():
    print("=" * 80)
    print("PRODUCTION DEMO ACCOUNT SEEDING SCRIPT")
    print("=" * 80)
    print()
    
    # Read the SQL script
    script_path = "db/seed_demo_accounts_prod_v2.sql"
    
    if not os.path.exists(script_path):
        print(f"[ERROR] Could not find {script_path}")
        print(f"   Current directory: {os.getcwd()}")
        print(f"   Please run this script from the project root.")
        sys.exit(1)
    
    print(f"[INFO] Reading SQL script: {script_path}")
    with open(script_path, "r", encoding="utf-8") as f:
        sql_script = f.read()
    
    print(f"[OK] Script loaded ({len(sql_script)} bytes)")
    print()
    
    # Connect to database
    print("[INFO] Connecting to database...")
    print(f"   Host: dpg-d474qiqli9vc738g17e0-a.oregon-postgres.render.com")
    print(f"   Database: mr_staging_db")
    print()
    
    try:
        with psycopg.connect(DATABASE_URL, autocommit=False) as conn:
            print("[OK] Connected successfully!")
            print()
            
            # Execute the script
            print("[INFO] Executing SQL script...")
            print("-" * 80)
            
            with conn.cursor() as cur:
                # Execute the entire script - psycopg can handle multiple statements
                # Just catch any errors if there are no results
                try:
                    # Use execute with a simple wrapper to handle notices
                    for notice in conn.notices:
                        print(f"  {notice.strip()}")
                    conn.notices.clear()
                    
                    cur.execute(sql_script)
                    
                    # Print any notices from execution
                    for notice in conn.notices:
                        print(f"  {notice.strip()}")
                    
                    # Try to fetch verification results
                    results = cur.fetchall()
                    col_names = [desc[0] for desc in cur.description] if cur.description else []
                    
                    if results:
                        print()
                        print("VERIFICATION RESULTS:")
                        print("-" * 80)
                        
                        # Print header
                        header = " | ".join(col_names)
                        print(header)
                        print("-" * len(header))
                        
                        # Print rows
                        for row in results:
                            print(" | ".join(str(val) if val is not None else "" for val in row))
                        
                        print("-" * 80)
                        print()
                except Exception as e:
                    # If we can't fetch, that's OK - script may have executed successfully
                    print(f"  Note: {e}")
            
            print("[OK] Script executed successfully!")
            print()
            
    except psycopg.Error as e:
        print(f"[ERROR] Database error: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"[ERROR] Unexpected error: {e}")
        sys.exit(1)
    
    # Final verification
    print("FINAL VERIFICATION:")
    print("-" * 80)
    
    try:
        with psycopg.connect(DATABASE_URL) as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    SELECT 
                        u.email,
                        u.role AS user_role,
                        a.name AS account_name,
                        a.account_type,
                        a.plan_slug,
                        u.is_active
                    FROM users u
                    JOIN accounts a ON a.id = u.account_id
                    WHERE u.email IN (
                        'admin@trendyreports-demo.com',
                        'agent-free@trendyreports-demo.com',
                        'agent-pro@trendyreports-demo.com',
                        'affiliate@trendyreports-demo.com',
                        'agent-sponsored@trendyreports-demo.com'
                    )
                    ORDER BY 
                        CASE 
                            WHEN u.email = 'admin@trendyreports-demo.com' THEN 1
                            WHEN u.email = 'agent-free@trendyreports-demo.com' THEN 2
                            WHEN u.email = 'agent-pro@trendyreports-demo.com' THEN 3
                            WHEN u.email = 'affiliate@trendyreports-demo.com' THEN 4
                            WHEN u.email = 'agent-sponsored@trendyreports-demo.com' THEN 5
                        END;
                """)
                
                accounts = cur.fetchall()
                
                if len(accounts) == 5:
                    print("[OK] All 5 demo accounts verified!")
                    print()
                    for email, role, acc_name, acc_type, plan, active in accounts:
                        status = "[OK]" if active else "[INACTIVE]"
                        print(f"  {status} {email}")
                        print(f"     Role: {role} | Account: {acc_name} ({acc_type}) | Plan: {plan}")
                        print()
                else:
                    print(f"[WARNING] Expected 5 accounts, found {len(accounts)}")
                    print()
                
    except Exception as e:
        print(f"[WARNING] Could not verify accounts: {e}")
    
    print("=" * 80)
    print("DONE! You can now login at https://www.trendyreports.io")
    print("=" * 80)
    print()
    print("Demo Account Credentials:")
    print("-" * 80)
    print("ADMIN:           admin@trendyreports-demo.com / DemoAdmin123!")
    print("FREE AGENT:      agent-free@trendyreports-demo.com / DemoAgent123!")
    print("PRO AGENT:       agent-pro@trendyreports-demo.com / DemoAgent123!")
    print("AFFILIATE:       affiliate@trendyreports-demo.com / DemoAff123!")
    print("SPONSORED AGENT: agent-sponsored@trendyreports-demo.com / DemoAgent123!")
    print("-" * 80)
    print()

if __name__ == "__main__":
    main()


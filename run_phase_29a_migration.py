"""
Phase 29A Migration Runner

Run this script to apply the Phase 29A migration to your Render Postgres database.
"""

import os
import sys
import psycopg

# Fix Windows console encoding
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')

# Database connection string
DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql://mr_staging_db_user:vlFYf9ykajrJC7y62as6RKazBSr37fUU@dpg-d474qiqli9vc738g17e0-a.oregon-postgres.render.com/mr_staging_db"
)

def run_migration():
    """Run the Phase 29A migration"""
    print("🚀 Starting Phase 29A Migration...")
    print(f"📊 Database: {DATABASE_URL.split('@')[1].split('/')[0]}")
    
    # Read migration file
    migration_file = "db/migrations/0007_phase_29a_plans_and_account_types.sql"
    print(f"📄 Reading migration: {migration_file}")
    
    try:
        with open(migration_file, 'r', encoding='utf-8') as f:
            sql = f.read()
    except FileNotFoundError:
        print(f"❌ ERROR: Migration file not found: {migration_file}")
        print("   Make sure you're running this from the project root directory.")
        return False
    
    # Connect and execute
    try:
        print("🔌 Connecting to database...")
        with psycopg.connect(DATABASE_URL) as conn:
            with conn.cursor() as cur:
                print("✅ Connected!")
                print("🔧 Running migration SQL...")
                
                # Execute migration
                cur.execute(sql)
                
                conn.commit()
                print("✅ Migration committed successfully!")
                
                # Verify results
                print("\n📊 Verification:")
                
                # Count plans
                cur.execute("SELECT COUNT(*) FROM plans")
                plan_count = cur.fetchone()[0]
                print(f"   Plans in database: {plan_count}")
                
                # Count accounts with account_type
                cur.execute("SELECT COUNT(*) FROM accounts WHERE account_type IS NOT NULL")
                account_count = cur.fetchone()[0]
                print(f"   Accounts migrated: {account_count}")
                
                # Count account_users
                cur.execute("SELECT COUNT(*) FROM account_users")
                account_user_count = cur.fetchone()[0]
                print(f"   Account users: {account_user_count}")
                
                # Show sample plans
                print("\n📋 Sample Plans:")
                cur.execute("""
                    SELECT slug, name, monthly_report_limit, allow_overage 
                    FROM plans 
                    ORDER BY monthly_report_limit
                """)
                for row in cur.fetchall():
                    print(f"   - {row[1]:20s} ({row[0]:15s}): {row[2]:4d} reports/month, overage: {row[3]}")
                
                print("\n🎉 Phase 29A Migration Complete!")
                return True
                
    except psycopg.Error as e:
        print(f"\n❌ Database Error: {e}")
        return False
    except Exception as e:
        print(f"\n❌ Unexpected Error: {e}")
        return False

if __name__ == "__main__":
    print("=" * 70)
    print("PHASE 29A MIGRATION RUNNER")
    print("Plans, Account Types, Usage Limits & Billing")
    print("=" * 70)
    print()
    
    success = run_migration()
    
    print()
    print("=" * 70)
    if success:
        print("✅ MIGRATION SUCCESSFUL!")
        print("\nNext Steps:")
        print("1. Redeploy API service (already has the new code)")
        print("2. Redeploy Worker service (already has the new code)")
        print("3. Test usage limits via admin endpoint:")
        print("   GET /v1/admin/accounts/{account_id}/plan-usage")
    else:
        print("❌ MIGRATION FAILED!")
        print("\nTroubleshooting:")
        print("1. Check that you're in the project root directory")
        print("2. Verify database credentials are correct")
        print("3. Ensure psycopg package is installed: pip install psycopg")
    print("=" * 70)


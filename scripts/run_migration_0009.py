#!/usr/bin/env python3
"""
Run migration 0009 to create contacts table.
"""

import os
import sys

try:
    import psycopg
except ImportError:
    print("[ERROR] psycopg not installed")
    print("   Install with: pip install psycopg")
    sys.exit(1)

DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql://mr_staging_db_user:vlFYf9ykajrJC7y62as6RKazBSr37fUU@dpg-d474qiqli9vc738g17e0-a.oregon-postgres.render.com/mr_staging_db"
)

def main():
    print("\n" + "="*80)
    print("Migration 0009: Create contacts table")
    print("="*80 + "\n")
    
    try:
        print("Connecting to database...")
        with psycopg.connect(DATABASE_URL) as conn:
            print("[OK] Connected\n")
            
            with conn.cursor() as cur:
                # Create contacts table
                print("Creating contacts table...")
                cur.execute("""
                    CREATE TABLE IF NOT EXISTS contacts (
                      id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
                      account_id uuid NOT NULL REFERENCES accounts(id) ON DELETE CASCADE,
                      name text NOT NULL,
                      email text NOT NULL,
                      type text NOT NULL CHECK (type IN ('client', 'list', 'agent')),
                      notes text,
                      created_at timestamptz NOT NULL DEFAULT now(),
                      updated_at timestamptz NOT NULL DEFAULT now()
                    )
                """)
                print("[OK] Table created")
                
                # Create indexes
                print("\nCreating indexes...")
                cur.execute("CREATE INDEX IF NOT EXISTS idx_contacts_account_id ON contacts(account_id)")
                print("[OK] Created idx_contacts_account_id")
                
                cur.execute("CREATE INDEX IF NOT EXISTS idx_contacts_email ON contacts(email)")
                print("[OK] Created idx_contacts_email")
                
                # Enable RLS
                print("\nEnabling RLS...")
                cur.execute("ALTER TABLE contacts ENABLE ROW LEVEL SECURITY")
                print("[OK] RLS enabled")
                
                # Create policy
                print("\nCreating RLS policy...")
                cur.execute("""
                    DROP POLICY IF EXISTS contacts_account_isolation ON contacts
                """)
                cur.execute("""
                    CREATE POLICY contacts_account_isolation ON contacts
                      FOR ALL
                      USING (account_id::text = current_setting('app.current_account_id', TRUE))
                """)
                print("[OK] Policy created")
                
                # Add comments
                print("\nAdding table comments...")
                cur.execute("""
                    COMMENT ON TABLE contacts IS 'Client contacts, recipients, and lists for scheduling and People view'
                """)
                cur.execute("""
                    COMMENT ON COLUMN contacts.type IS 'Type of contact: client (individual), list (group), agent (external)'
                """)
                print("[OK] Comments added")
                
                conn.commit()
            
            # Verify
            print("\n" + "="*80)
            print("Verification: contacts table schema")
            print("="*80 + "\n")
            
            with conn.cursor() as cur:
                cur.execute("""
                    SELECT column_name, data_type, is_nullable
                    FROM information_schema.columns 
                    WHERE table_name = 'contacts' 
                    ORDER BY ordinal_position
                """)
                
                print(f"{'Column':<20} {'Type':<30} {'Nullable'}")
                print("-" * 60)
                for row in cur.fetchall():
                    col_name, data_type, nullable = row
                    print(f"{col_name:<20} {data_type:<30} {nullable}")
            
            print("\n" + "="*80)
            print("[SUCCESS] Migration 0009 completed successfully!")
            print("="*80 + "\n")
            
    except Exception as e:
        print(f"\n[ERROR] {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()


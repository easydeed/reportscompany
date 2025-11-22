#!/usr/bin/env python3
"""
Run migration 0014: Add phone and group type to contacts
"""
import os
import sys
import psycopg

# Ensure UTF-8 encoding for Windows
sys.stdout.reconfigure(encoding='utf-8')

# Get database URL from environment
DATABASE_URL = os.getenv("DATABASE_URL")
if not DATABASE_URL:
    print("ERROR: DATABASE_URL environment variable not set")
    sys.exit(1)

# Read migration file
migration_file = "db/migrations/0014_add_phone_and_group_to_contacts.sql"
with open(migration_file, "r", encoding="utf-8") as f:
    migration_sql = f.read()

print(f"Running migration: {migration_file}")
print("=" * 60)

try:
    # Connect and run migration
    with psycopg.connect(DATABASE_URL) as conn:
        with conn.cursor() as cur:
            # Execute migration
            cur.execute(migration_sql)
            conn.commit()
            
            print("✓ Migration executed successfully!")
            
            # Verify changes
            print("\nVerifying changes:")
            
            # Check phone column exists
            cur.execute("""
                SELECT column_name, data_type, is_nullable
                FROM information_schema.columns
                WHERE table_name = 'contacts' AND column_name = 'phone'
            """)
            phone_col = cur.fetchone()
            if phone_col:
                print(f"✓ phone column: {phone_col[1]}, nullable={phone_col[2]}")
            else:
                print("✗ phone column not found!")
            
            # Check email is nullable
            cur.execute("""
                SELECT is_nullable
                FROM information_schema.columns
                WHERE table_name = 'contacts' AND column_name = 'email'
            """)
            email_nullable = cur.fetchone()
            if email_nullable:
                print(f"✓ email column: nullable={email_nullable[0]}")
            
            # Check type constraint includes 'group'
            cur.execute("""
                SELECT conname, pg_get_constraintdef(oid)
                FROM pg_constraint
                WHERE conname = 'contacts_type_check'
            """)
            constraint = cur.fetchone()
            if constraint and 'group' in constraint[1]:
                print(f"✓ type constraint: includes 'group'")
            
            print("\n" + "=" * 60)
            print("Migration 0014 completed successfully!")

except Exception as e:
    print(f"\n✗ Migration failed: {e}")
    sys.exit(1)


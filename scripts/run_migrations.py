#!/usr/bin/env python3
"""
Run database migrations

Usage:
    DATABASE_URL=postgresql://... python scripts/run_migrations.py
"""

import os
import sys
import psycopg2
from pathlib import Path


def run_migration(cur, migration_file):
    """Run a single migration file"""
    print(f"Running {migration_file.name}...")
    sql = migration_file.read_text()
    
    # Split by semicolons and execute each statement separately
    # This handles multi-statement migrations better
    statements = [s.strip() for s in sql.split(';') if s.strip() and not s.strip().startswith('--')]
    
    for statement in statements:
        if statement:
            try:
                cur.execute(statement)
            except Exception as e:
                # If it's a "relation already exists" error, that's OK
                if "already exists" in str(e).lower():
                    print(f"  [SKIP] Object already exists, continuing...")
                else:
                    raise
    
    print(f"[OK] {migration_file.name} completed")


def main():
    database_url = os.environ.get("DATABASE_URL")
    
    if not database_url:
        print("Error: DATABASE_URL environment variable not set", file=sys.stderr)
        print("Usage: DATABASE_URL=postgresql://... python scripts/run_migrations.py", file=sys.stderr)
        sys.exit(1)
    
    # Get migrations directory
    migrations_dir = Path(__file__).parent.parent / "db" / "migrations"
    
    if not migrations_dir.exists():
        print(f"Error: Migrations directory not found: {migrations_dir}", file=sys.stderr)
        sys.exit(1)
    
    # Get migration files (sorted)
    migration_files = sorted(migrations_dir.glob("*.sql"))
    
    if not migration_files:
        print("No migration files found", file=sys.stderr)
        sys.exit(1)
    
    print(f"Found {len(migration_files)} migration files\n")
    
    # Connect to database
    try:
        conn = psycopg2.connect(database_url)
        conn.autocommit = False
        cur = conn.cursor()
        
        print("Connected to database\n")
        
        # Run migrations
        for migration_file in migration_files:
            try:
                run_migration(cur, migration_file)
            except psycopg2.Error as e:
                print(f"[ERROR] Error in {migration_file.name}: {e}", file=sys.stderr)
                print("Rolling back...", file=sys.stderr)
                conn.rollback()
                sys.exit(1)
        
        # Commit all migrations
        conn.commit()
        print(f"\n[SUCCESS] All {len(migration_files)} migrations completed successfully!")
        
        # Show plans
        cur.execute("SELECT plan_slug, plan_name, stripe_price_id FROM plans ORDER BY plan_slug")
        print("\nCurrent plans:")
        print("-" * 80)
        for row in cur.fetchall():
            price_id = row[2] if row[2] else "NULL"
            print(f"  {row[0]:<15} {row[1]:<25} {price_id}")
        
        cur.close()
        conn.close()
        
    except psycopg2.Error as e:
        print(f"Database connection error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()


#!/usr/bin/env python3
"""
Test database connection and insert Phase 27A test schedule.
"""

import sys

# Check if psycopg2 is available
try:
    import psycopg2
    from psycopg2.extras import RealDictCursor
except ImportError:
    print("❌ psycopg2 not installed.")
    print("\nInstall it with:")
    print("  pip install psycopg2-binary")
    sys.exit(1)

def test_connection(connection_string):
    """Test the database connection."""
    try:
        conn = psycopg2.connect(connection_string)
        cur = conn.cursor()
        cur.execute("SELECT version();")
        version = cur.fetchone()[0]
        print(f"[OK] Connected successfully!")
        print(f"   PostgreSQL version: {version[:50]}...")
        cur.close()
        conn.close()
        return True
    except Exception as e:
        print(f"[ERROR] Connection failed: {e}")
        return False

def insert_test_schedule(connection_string):
    """Insert the Phase 27A test schedule."""
    INSERT_SQL = """
    INSERT INTO schedules (
      account_id,
      name,
      report_type,
      city,
      lookback_days,
      cadence,
      weekly_dow,
      send_hour,
      send_minute,
      recipients,
      active,
      created_at,
      next_run_at
    ) VALUES (
      '912014c3-6deb-4b40-a28d-489ef3923a3a',
      'Phase 27A Email Test - Gerard',
      'market_snapshot',
      'Houston',
      30,
      'weekly',
      1,
      14,
      0,
      ARRAY['gerardoh@gmail.com'],
      true,
      NOW(),
      NOW() - INTERVAL '1 minute'
    )
    RETURNING id, name, next_run_at;
    """
    
    try:
        conn = psycopg2.connect(connection_string)
        cur = conn.cursor()
        cur.execute(INSERT_SQL)
        result = cur.fetchone()
        conn.commit()
        
        schedule_id = result[0]
        schedule_name = result[1]
        next_run = result[2]
        
        print("\n[SUCCESS] Schedule created successfully!")
        print(f"   ID: {schedule_id}")
        print(f"   Name: {schedule_name}")
        print(f"   Next Run: {next_run}")
        
        cur.close()
        conn.close()
        
        return schedule_id
        
    except Exception as e:
        print(f"\n[ERROR] Insert failed: {e}")
        return None

def check_schedule_runs(connection_string, schedule_id):
    """Check schedule run status."""
    QUERY = f"""
    SELECT id, status, started_at, finished_at, report_run_id, created_at
    FROM schedule_runs
    WHERE schedule_id = '{schedule_id}'
    ORDER BY created_at DESC
    LIMIT 5;
    """
    
    try:
        conn = psycopg2.connect(connection_string)
        cur = conn.cursor(cursor_factory=RealDictCursor)
        cur.execute(QUERY)
        rows = cur.fetchall()
        
        if rows:
            print("\n[SCHEDULE RUNS]")
            for row in rows:
                print(f"   Status: {row['status']} | Started: {row['started_at']} | Finished: {row['finished_at']}")
        else:
            print("\n[SCHEDULE RUNS] No runs yet (ticker will pick it up within 60 seconds)")
        
        cur.close()
        conn.close()
        
    except Exception as e:
        print(f"[ERROR] Query failed: {e}")

def check_email_log(connection_string):
    """Check email log."""
    QUERY = """
    SELECT provider, to_emails, response_code, error, subject, created_at
    FROM email_log
    ORDER BY created_at DESC
    LIMIT 5;
    """
    
    try:
        conn = psycopg2.connect(connection_string)
        cur = conn.cursor(cursor_factory=RealDictCursor)
        cur.execute(QUERY)
        rows = cur.fetchall()
        
        if rows:
            print("\n[EMAIL LOG]")
            for row in rows:
                status = "[OK]" if row['response_code'] == 202 else "[FAIL]"
                print(f"   {status} Provider: {row['provider']} | To: {row['to_emails']} | Code: {row['response_code']}")
                if row['error']:
                    print(f"      Error: {row['error']}")
        else:
            print("\n[EMAIL LOG] No emails sent yet")
        
        cur.close()
        conn.close()
        
    except Exception as e:
        print(f"[ERROR] Query failed: {e}")

def main():
    print("=" * 70)
    print("Phase 27A - Schedule Email Test")
    print("=" * 70)
    
    if len(sys.argv) > 1:
        connection_string = sys.argv[1]
    else:
        print("\nUsage: python test_db_connection.py 'postgresql://user:pass@host/db'")
        print("\nOr enter connection string now:")
        connection_string = input("> ").strip()
    
    if not connection_string:
        print("[ERROR] No connection string provided")
        sys.exit(1)
    
    # Test connection
    print("\n1. Testing connection...")
    if not test_connection(connection_string):
        sys.exit(1)
    
    # Insert schedule
    print("\n2. Inserting test schedule...")
    schedule_id = insert_test_schedule(connection_string)
    
    if not schedule_id:
        sys.exit(1)
    
    # Check initial status
    print("\n3. Checking initial status...")
    check_schedule_runs(connection_string, schedule_id)
    check_email_log(connection_string)
    
    print("\n" + "=" * 70)
    print("[SUCCESS] Setup complete!")
    print("=" * 70)
    print("\nNext steps:")
    print("1. Wait 5-10 minutes for ticker -> worker -> email")
    print("2. Check gerardoh@gmail.com for the report email")
    print("3. Run this script again to check status:")
    print(f"   python test_db_connection.py '{connection_string}'")
    print("\nOr check manually with SQL queries in PHASE_27A_MONITORING.md")
    print(f"\nSchedule ID for reference: {schedule_id}")

if __name__ == "__main__":
    main()


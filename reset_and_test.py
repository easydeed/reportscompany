#!/usr/bin/env python3
"""
Delete old test schedule and create a new one after the ticker fix.
"""

import psycopg2
from psycopg2.extras import RealDictCursor

CONNECTION_STRING = "postgresql://mr_staging_db_user:vlFYf9ykajrJC7y62as6RKazBSr37fUU@dpg-d474qiqli9vc738g17e0-a.oregon-postgres.render.com/mr_staging_db"
OLD_SCHEDULE_ID = "a61d14d6-c634-440f-9da6-fd9bd488f165"

def main():
    conn = psycopg2.connect(CONNECTION_STRING)
    cur = conn.cursor()
    
    print("=" * 70)
    print("Phase 27A - Reset and Create New Test Schedule")
    print("=" * 70)
    
    # Delete old schedule (cascades to schedule_runs)
    print(f"\n1. Deleting old schedule {OLD_SCHEDULE_ID}...")
    cur.execute("DELETE FROM schedules WHERE id = %s", (OLD_SCHEDULE_ID,))
    conn.commit()
    print("   [OK] Old schedule deleted")
    
    # Create new test schedule
    print("\n2. Creating new test schedule...")
    cur.execute("""
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
          'Phase 27A Email Test - Gerard (v2)',
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
    """)
    
    result = cur.fetchone()
    conn.commit()
    
    schedule_id = result[0]
    schedule_name = result[1]
    next_run = result[2]
    
    print(f"   [SUCCESS] New schedule created!")
    print(f"   ID: {schedule_id}")
    print(f"   Name: {schedule_name}")
    print(f"   Next Run: {next_run}")
    
    cur.close()
    conn.close()
    
    print("\n" + "=" * 70)
    print("Ready to test! Ticker will pick this up within 60 seconds.")
    print("=" * 70)
    print(f"\nSchedule ID: {schedule_id}")
    print("\nMonitor with:")
    print("  python check_schedule_status.py")
    print("\nOr update check_schedule_status.py with the new schedule ID.")

if __name__ == "__main__":
    main()


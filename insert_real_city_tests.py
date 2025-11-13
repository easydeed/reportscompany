#!/usr/bin/env python3
"""
Insert Test Schedules for Real California Cities - Phase 28

Uses actual cities with live SimplyRETS MLS data coverage.

Usage:
    python insert_real_city_tests.py

Environment Variables Required:
    DATABASE_URL=postgresql://user:pass@host/db
"""

import psycopg2
import os
import sys
from datetime import datetime

# Real cities with live SimplyRETS data (California)
REAL_CITIES = [
    {"name": "Southgate", "state": "CA", "reason": "Real MLS data - LA area"},
    {"name": "La Verne", "state": "CA", "reason": "Real MLS data - San Gabriel Valley"},
    {"name": "San Dimas", "state": "CA", "reason": "Real MLS data - Los Angeles County"},
    {"name": "Downey", "state": "CA", "reason": "Real MLS data - LA County"},
    {"name": "Orange", "state": "CA", "reason": "Real MLS data - Orange County"},
]

def main():
    db_url = os.getenv("DATABASE_URL")
    if not db_url:
        print("[ERROR] DATABASE_URL environment variable not set")
        sys.exit(1)
    
    # Hardcoded account ID for demo account
    ACCOUNT_ID = "912014c3-6deb-4b40-a28d-489ef3923a3a"
    RECIPIENT = "gerardoh@gmail.com"
    
    print("\n" + "="*80)
    print("PHASE 28: Real California Cities Test Schedule Insertion")
    print("="*80 + "\n")
    
    print(f"Account ID: {ACCOUNT_ID}")
    print(f"Recipient: {RECIPIENT}")
    print(f"Cities to test: {len(REAL_CITIES)}\n")
    
    try:
        conn = psycopg2.connect(db_url)
        cur = conn.cursor()
        
        # First, clean up previous Phase 28 test schedules
        print("Cleaning up previous Phase 28 test schedules...")
        cur.execute("DELETE FROM schedules WHERE name LIKE 'Phase 28 Test -%';")
        deleted_count = cur.rowcount
        print(f"  Deleted {deleted_count} old test schedule(s)\n")
        
        inserted_ids = []
        
        for city_info in REAL_CITIES:
            city_name = city_info["name"]
            state = city_info["state"]
            reason = city_info["reason"]
            
            print(f"Inserting schedule for {city_name}, {state}...")
            print(f"  Reason: {reason}")
            
            # Insert schedule
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
                    %s,                                          -- account_id
                    %s,                                          -- name
                    'market_snapshot',                           -- report_type
                    %s,                                          -- city
                    30,                                          -- lookback_days
                    'weekly',                                    -- cadence
                    1,                                           -- weekly_dow (Monday)
                    14,                                          -- send_hour (2 PM)
                    0,                                           -- send_minute
                    ARRAY[%s],                                   -- recipients
                    true,                                        -- active
                    NOW(),                                       -- created_at
                    NOW() - INTERVAL '1 minute'                  -- next_run_at (fire immediately)
                ) RETURNING id, name, next_run_at;
            """, (
                ACCOUNT_ID,
                f"Phase 28 Real Data - {city_name}, {state}",
                city_name,
                RECIPIENT
            ))
            
            result = cur.fetchone()
            if result:
                schedule_id, schedule_name, next_run = result
                inserted_ids.append({
                    "id": schedule_id,
                    "name": schedule_name,
                    "city": city_name,
                    "next_run": next_run
                })
                print(f"  [OK] Created: {schedule_id}")
                print(f"  Next run: {next_run}")
            
            print()
        
        # Commit all changes
        conn.commit()
        
        # Summary
        print("="*80)
        print(f"[SUCCESS] Inserted {len(inserted_ids)} real city schedules")
        print("="*80 + "\n")
        
        print("Schedule IDs for Monitoring:")
        for item in inserted_ids:
            print(f"  {item['city']}: {item['id']}")
        
        print("\nNext Steps:")
        print("  1. Wait 60-90 seconds for ticker to pick up schedules")
        print("  2. Monitor worker logs for report generation")
        print("  3. Run: python check_multi_city_test.py")
        print(f"  4. Check email inbox for {len(REAL_CITIES)} emails")
        print("  5. Verify each PDF shows REAL DATA for California cities")
        print("  6. Check active/closed counts are non-zero")
        
        print("\nTo clean up test schedules after testing:")
        print("  DELETE FROM schedules WHERE name LIKE 'Phase 28 Real Data -%';")
        
        print("\n" + "="*80 + "\n")
        
        conn.close()
        
    except Exception as e:
        print(f"\n[ERROR] Failed to insert test schedules: {e}")
        if conn:
            conn.rollback()
            conn.close()
        sys.exit(1)

if __name__ == "__main__":
    main()


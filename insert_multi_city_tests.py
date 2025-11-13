#!/usr/bin/env python3
"""
Insert Test Schedules for Multiple Cities - Phase 28

This script creates test schedules for multiple US cities to verify
production SimplyRETS integration.

Usage:
    python insert_multi_city_tests.py

Environment Variables Required:
    DATABASE_URL=postgresql://user:pass@host/db
"""

import psycopg2
import os
import sys
from datetime import datetime

# Test cities for Phase 28 certification
TEST_CITIES = [
    {"name": "Houston", "state": "TX", "reason": "Baseline - demo data"},
    {"name": "Austin", "state": "TX", "reason": "Production - major metro"},
    {"name": "Dallas", "state": "TX", "reason": "Production - large market"},
    {"name": "Phoenix", "state": "AZ", "reason": "Production - fast growing"},
    {"name": "Miami", "state": "FL", "reason": "Production - coastal market"},
    {"name": "Seattle", "state": "WA", "reason": "Production - tech hub"},
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
    print("PHASE 28: Multi-City Test Schedule Insertion")
    print("="*80 + "\n")
    
    print(f"Account ID: {ACCOUNT_ID}")
    print(f"Recipient: {RECIPIENT}")
    print(f"Cities to test: {len(TEST_CITIES)}\n")
    
    try:
        conn = psycopg2.connect(db_url)
        cur = conn.cursor()
        
        inserted_ids = []
        
        for city_info in TEST_CITIES:
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
                f"Phase 28 Test - {city_name}, {state}",
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
                print(f"  ✅ Created: {schedule_id}")
                print(f"  Next run: {next_run}")
            
            print()
        
        # Commit all inserts
        conn.commit()
        
        # Summary
        print("="*80)
        print(f"✅ Successfully inserted {len(inserted_ids)} test schedules")
        print("="*80 + "\n")
        
        print("📋 Schedule IDs for Monitoring:")
        for item in inserted_ids:
            print(f"  {item['city']}: {item['id']}")
        
        print("\n📊 Next Steps:")
        print("  1. Wait 60-90 seconds for ticker to pick up schedules")
        print("  2. Monitor worker logs for report generation")
        print("  3. Run: python check_multi_city_test.py")
        print("  4. Check email inbox for {len(TEST_CITIES)} emails")
        print("  5. Verify each PDF shows correct city data")
        
        print("\n🧪 To clean up test schedules after testing:")
        print(f"  DELETE FROM schedules WHERE name LIKE 'Phase 28 Test -%';")
        
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


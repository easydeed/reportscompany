#!/usr/bin/env python3
"""
Quick script to insert a test schedule directly into Postgres.
No need to install psql - just uses Python + psycopg2.
"""

import os
import sys

try:
    import psycopg2
except ImportError:
    print("❌ psycopg2 not installed.")
    print("Install with: pip install psycopg2-binary")
    sys.exit(1)

# Get connection string from environment or prompt
DATABASE_URL = os.getenv("DATABASE_URL")

if not DATABASE_URL:
    print("Enter your Render Postgres connection string:")
    print("(Format: postgresql://user:password@host/database)")
    DATABASE_URL = input("> ").strip()

# Connect
try:
    conn = psycopg2.connect(DATABASE_URL)
    print("✅ Connected to database")
except Exception as e:
    print(f"❌ Connection failed: {e}")
    sys.exit(1)

# Insert test schedule
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
    cur = conn.cursor()
    cur.execute(INSERT_SQL)
    result = cur.fetchone()
    conn.commit()
    
    print("\n✅ Schedule created successfully!")
    print(f"   ID: {result[0]}")
    print(f"   Name: {result[1]}")
    print(f"   Next Run: {result[2]}")
    print(f"\n📋 Save this ID for monitoring: {result[0]}")
    
except Exception as e:
    print(f"❌ Insert failed: {e}")
    conn.rollback()
    sys.exit(1)
finally:
    cur.close()
    conn.close()

print("\n✅ Done! Now monitor execution with these queries:\n")
print(f"-- Check schedule run status")
print(f"SELECT id, status, started_at, finished_at")
print(f"FROM schedule_runs")
print(f"WHERE schedule_id = '{result[0]}'")
print(f"ORDER BY created_at DESC LIMIT 5;\n")

print(f"-- Check email log")
print(f"SELECT provider, to_emails, response_code, error, created_at")
print(f"FROM email_log")
print(f"ORDER BY created_at DESC LIMIT 5;\n")


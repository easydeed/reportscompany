#!/usr/bin/env python3
"""
Quick status checker for Phase 27A schedule.
"""

import sys
import psycopg2
from psycopg2.extras import RealDictCursor

SCHEDULE_ID = "48d923da-be17-4d3d-b413-5bf1bc16a504"
CONNECTION_STRING = "postgresql://mr_staging_db_user:vlFYf9ykajrJC7y62as6RKazBSr37fUU@dpg-d474qiqli9vc738g17e0-a.oregon-postgres.render.com/mr_staging_db"

def check_status():
    """Check schedule status."""
    conn = psycopg2.connect(CONNECTION_STRING)
    
    print("=" * 70)
    print("Phase 27A Status Check")
    print("=" * 70)
    print(f"Schedule ID: {SCHEDULE_ID}")
    print()
    
    # Check schedule runs
    print("[1] SCHEDULE RUNS:")
    cur = conn.cursor(cursor_factory=RealDictCursor)
    cur.execute("""
        SELECT id, status, started_at, finished_at, report_run_id, created_at
        FROM schedule_runs
        WHERE schedule_id = %s
        ORDER BY created_at DESC
        LIMIT 5;
    """, (SCHEDULE_ID,))
    
    runs = cur.fetchall()
    if runs:
        for run in runs:
            print(f"   Status: {run['status']}")
            print(f"   Started: {run['started_at']}")
            print(f"   Finished: {run['finished_at']}")
            print(f"   Report Run ID: {run['report_run_id']}")
            print()
    else:
        print("   [WAITING] No runs yet - ticker should pick it up soon")
        print()
    
    # Check email log
    print("[2] EMAIL LOG (last 5):")
    cur.execute("""
        SELECT provider, to_emails, response_code, error, subject, created_at
        FROM email_log
        ORDER BY created_at DESC
        LIMIT 5;
    """)
    
    emails = cur.fetchall()
    if emails:
        for email in emails:
            status = "[OK]" if email['response_code'] == 202 else "[FAIL]"
            print(f"   {status} To: {email['to_emails']}")
            print(f"   Provider: {email['provider']} | Code: {email['response_code']}")
            print(f"   Subject: {email['subject']}")
            if email['error']:
                print(f"   Error: {email['error']}")
            print(f"   Sent: {email['created_at']}")
            print()
    else:
        print("   [WAITING] No emails sent yet")
        print()
    
    # Check report generations
    print("[3] REPORT GENERATIONS (last 5):")
    cur.execute("""
        SELECT id, status, pdf_url, result_json->>'city' as city
        FROM report_generations
        ORDER BY id DESC
        LIMIT 5;
    """)
    
    reports = cur.fetchall()
    if reports:
        for report in reports:
            print(f"   Status: {report['status']} | City: {report['city']}")
            if report['pdf_url']:
                print(f"   PDF: {report['pdf_url'][:80]}...")
            print()
    else:
        print("   [WAITING] No reports generated yet")
        print()
    
    cur.close()
    conn.close()
    
    print("=" * 70)
    print("Re-run this script to refresh status:")
    print("  python check_schedule_status.py")
    print("=" * 70)

if __name__ == "__main__":
    try:
        check_status()
    except Exception as e:
        print(f"[ERROR] {e}")
        sys.exit(1)


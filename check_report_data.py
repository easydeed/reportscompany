#!/usr/bin/env python3
"""
Check what's in the report_generations result_json for the specific report.
"""

import psycopg2
import json
from psycopg2.extras import RealDictCursor

CONNECTION_STRING = "postgresql://mr_staging_db_user:vlFYf9ykajrJC7y62as6RKazBSr37fUU@dpg-d474qiqli9vc738g17e0-a.oregon-postgres.render.com/mr_staging_db"
REPORT_ID = "e5bbf66a-803f-4e6e-b0c6-81c0960f0818"

def main():
    conn = psycopg2.connect(CONNECTION_STRING)
    cur = conn.cursor(cursor_factory=RealDictCursor)
    
    print("=" * 70)
    print("Report Data Check")
    print("=" * 70)
    print(f"Report ID: {REPORT_ID}\n")
    
    # Get report data
    cur.execute("""
        SELECT id, report_type, status, pdf_url, result_json, input_params
        FROM report_generations
        WHERE id = %s
    """, (REPORT_ID,))
    
    report = cur.fetchone()
    
    if not report:
        print("[ERROR] Report not found")
        return
    
    print(f"Status: {report['status']}")
    print(f"Report Type: {report['report_type']}")
    print(f"PDF URL: {report['pdf_url'][:80]}...")
    print()
    
    print("Input Params:")
    if report['input_params']:
        print(json.dumps(report['input_params'], indent=2))
    else:
        print("  None")
    print()
    
    print("Result JSON:")
    if report['result_json']:
        result = report['result_json']
        print(f"  City: {result.get('city', 'MISSING')}")
        print(f"  Report Type: {result.get('report_type', 'MISSING')}")
        print(f"  Lookback Days: {result.get('lookback_days', 'MISSING')}")
        print(f"  Has Counts: {'counts' in result}")
        print(f"  Has Metrics: {'metrics' in result}")
        print(f"  Has Listings Sample: {'listings_sample' in result}")
        print()
        print("Full result_json structure:")
        print(json.dumps(result, indent=2)[:500] + "...")
    else:
        print("  [ERROR] result_json is NULL")
    
    cur.close()
    conn.close()

if __name__ == "__main__":
    main()


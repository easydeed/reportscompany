#!/usr/bin/env python3
"""
Multi-City Testing Monitor for Phase 28

This script monitors recent report generations across multiple cities
to verify production SimplyRETS integration is working correctly.

Usage:
    python check_multi_city_test.py

Environment Variables Required:
    DATABASE_URL=postgresql://user:pass@host/db
"""

import psycopg2
import os
import sys
from datetime import datetime, timedelta

def main():
    db_url = os.getenv("DATABASE_URL")
    if not db_url:
        print("[ERROR] DATABASE_URL environment variable not set")
        sys.exit(1)
    
    print("\n" + "="*80)
    print("PHASE 28: Multi-City Testing Monitor")
    print("="*80 + "\n")
    
    try:
        conn = psycopg2.connect(db_url)
        cur = conn.cursor()
        
        # Check recent reports by city
        print("📊 Recent Reports by City (Last 2 Hours)")
        print("-" * 80)
        cur.execute("""
            SELECT 
                rg.id::text,
                rg.status,
                rg.input_params->>'city' as city,
                rg.result_json->>'active_count' as active,
                rg.result_json->>'pending_count' as pending,
                rg.result_json->>'closed_count' as closed,
                rg.result_json->>'median_price' as median_price,
                rg.pdf_url,
                rg.created_at
            FROM report_generations rg
            WHERE rg.created_at > NOW() - INTERVAL '2 hours'
            ORDER BY rg.created_at DESC
            LIMIT 20;
        """)
        
        reports = cur.fetchall()
        if not reports:
            print("No reports generated in the last 2 hours.")
        else:
            for row in reports:
                report_id, status, city, active, pending, closed, median, pdf_url, created_at = row
                print(f"\n[{created_at}] {city or 'Unknown City'}")
                print(f"  ID: {report_id}")
                print(f"  Status: {status}")
                print(f"  Active: {active}, Pending: {pending}, Closed: {closed}")
                print(f"  Median Price: ${median}" if median else "  Median Price: N/A")
                print(f"  PDF: {pdf_url[:80]}..." if pdf_url else "  PDF: (none)")
        
        # City breakdown
        print("\n" + "-" * 80)
        print("📍 Reports by City (Last 24 Hours)")
        print("-" * 80)
        cur.execute("""
            SELECT 
                COALESCE(rg.input_params->>'city', 'Unknown') as city,
                COUNT(*) as report_count,
                SUM(CASE WHEN rg.status = 'completed' THEN 1 ELSE 0 END) as completed,
                SUM(CASE WHEN rg.status = 'failed' THEN 1 ELSE 0 END) as failed
            FROM report_generations rg
            WHERE rg.created_at > NOW() - INTERVAL '24 hours'
            GROUP BY city
            ORDER BY report_count DESC;
        """)
        
        city_stats = cur.fetchall()
        if not city_stats:
            print("No reports generated in the last 24 hours.")
        else:
            print(f"\n{'City':<20} {'Total':<8} {'Completed':<12} {'Failed':<8}")
            print("-" * 50)
            for city, total, completed, failed in city_stats:
                print(f"{city:<20} {total:<8} {completed:<12} {failed:<8}")
        
        # Recent schedule runs
        print("\n" + "-" * 80)
        print("📅 Recent Schedule Runs (Last 2 Hours)")
        print("-" * 80)
        cur.execute("""
            SELECT 
                sr.id::text,
                s.name,
                sr.status,
                sr.started_at,
                sr.finished_at,
                sr.report_run_id::text
            FROM schedule_runs sr
            JOIN schedules s ON s.id = sr.schedule_id
            WHERE sr.created_at > NOW() - INTERVAL '2 hours'
            ORDER BY sr.created_at DESC
            LIMIT 10;
        """)
        
        runs = cur.fetchall()
        if not runs:
            print("No schedule runs in the last 2 hours.")
        else:
            for run_id, name, status, started, finished, report_id in runs:
                print(f"\n{name}")
                print(f"  Run ID: {run_id}")
                print(f"  Status: {status}")
                print(f"  Started: {started}")
                print(f"  Finished: {finished}" if finished else "  Finished: (in progress)")
                print(f"  Report: {report_id}" if report_id else "  Report: (none)")
        
        # Email delivery
        print("\n" + "-" * 80)
        print("📧 Email Delivery Log (Last 2 Hours)")
        print("-" * 80)
        cur.execute("""
            SELECT 
                el.created_at,
                el.provider,
                el.to_emails,
                el.status,
                el.response_code,
                el.error
            FROM email_log el
            WHERE el.created_at > NOW() - INTERVAL '2 hours'
            ORDER BY el.created_at DESC
            LIMIT 10;
        """)
        
        emails = cur.fetchall()
        if not emails:
            print("No emails sent in the last 2 hours.")
        else:
            for created, provider, recipients, status, code, error in emails:
                print(f"\n[{created}] {provider}")
                print(f"  To: {', '.join(recipients)}")
                print(f"  Status: {status} (HTTP {code})")
                if error:
                    print(f"  Error: {error}")
        
        # Data quality checks
        print("\n" + "-" * 80)
        print("✅ Data Quality Checks (Last 24 Hours)")
        print("-" * 80)
        cur.execute("""
            SELECT 
                COUNT(*) as total_reports,
                COUNT(CASE WHEN rg.status = 'completed' THEN 1 END) as completed,
                COUNT(CASE WHEN rg.status = 'failed' THEN 1 END) as failed,
                COUNT(CASE WHEN rg.pdf_url IS NOT NULL THEN 1 END) as has_pdf,
                COUNT(CASE WHEN (rg.result_json->>'active_count')::int > 0 THEN 1 END) as has_data,
                AVG(CASE 
                    WHEN rg.status = 'completed' AND (rg.result_json->>'active_count')::int > 0 
                    THEN (rg.result_json->>'active_count')::int 
                    ELSE NULL 
                END) as avg_active
            FROM report_generations rg
            WHERE rg.created_at > NOW() - INTERVAL '24 hours';
        """)
        
        stats = cur.fetchone()
        if stats:
            total, completed, failed, has_pdf, has_data, avg_active = stats
            print(f"\nTotal Reports: {total}")
            print(f"Completed: {completed} ({100*completed//total if total > 0 else 0}%)")
            print(f"Failed: {failed}")
            print(f"With PDF: {has_pdf}")
            print(f"With Data: {has_data}")
            print(f"Avg Active Listings: {avg_active:.1f}" if avg_active else "Avg Active Listings: N/A")
            
            # Quality assessment
            print("\n" + "="*80)
            if total == 0:
                print("⚠️  STATUS: No reports to evaluate")
            elif completed == total and has_pdf == total and has_data == total:
                print("✅ STATUS: All systems working perfectly!")
            elif completed > 0 and has_data > 0:
                print("⚠️  STATUS: Mostly working, some issues detected")
            else:
                print("❌ STATUS: System issues detected, investigation needed")
            print("="*80 + "\n")
        
        conn.close()
        
    except Exception as e:
        print(f"\n[ERROR] Database query failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()


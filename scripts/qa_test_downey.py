#!/usr/bin/env python3
"""
QA Test Script - Downey Reports with Email Delivery

Creates scheduled reports for Downey, CA that will:
1. Generate all report types
2. Send email to gerardoh@gmail.com

Usage:
    # You'll need your session token from the browser
    # 1. Log into https://www.trendyreports.io
    # 2. Open DevTools (F12) → Application → Cookies
    # 3. Copy the value of 'mr_token' cookie
    
    python scripts/qa_test_downey.py --token "your-mr_token-here"
    
    # Or set as environment variable:
    export MR_TOKEN="your-mr_token-here"
    python scripts/qa_test_downey.py
"""

import os
import sys
import time
import json
import argparse
from datetime import datetime, timedelta
from typing import Dict, List, Optional

try:
    import requests
except ImportError:
    print("❌ Missing dependency. Run: pip install requests")
    sys.exit(1)

# ============================================================================
# CONFIGURATION
# ============================================================================

API_BASE = "https://api.trendyreports.io/v1"
CITY = "Downey"
EMAIL = "gerardoh@gmail.com"
LOOKBACK_DAYS = 30

# Report configurations
REPORTS_TO_TEST = [
    # New Listings with all audiences
    {"type": "new_listings_gallery", "name": "New Listings - All Buyers", "audience": None},
    {"type": "new_listings_gallery", "name": "First-Time Buyer", "audience": "first_time_buyer", 
     "price_strategy": {"mode": "relative_to_median", "value": 0.70, "position": "max"}},
    {"type": "new_listings_gallery", "name": "Luxury Buyer", "audience": "luxury_buyer",
     "price_strategy": {"mode": "relative_to_median", "value": 1.75, "position": "min"}},
    {"type": "new_listings_gallery", "name": "Investor", "audience": "investor",
     "price_strategy": {"mode": "relative_to_median", "value": 0.85, "position": "max"}},
    {"type": "new_listings_gallery", "name": "Condo Buyer", "audience": "condo_buyer"},
    {"type": "new_listings_gallery", "name": "Family Buyer", "audience": "family_buyer",
     "price_strategy": {"mode": "relative_to_median", "value": 1.10, "position": "max"}},
    
    # Market Update
    {"type": "market_snapshot", "name": "Market Update"},
    
    # Closed Sales
    {"type": "closed", "name": "Closed Sales"},
]


def get_headers(token: str) -> Dict:
    """Build auth headers using session token."""
    return {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
    }


def create_one_time_report(token: str, config: Dict) -> Optional[str]:
    """Create a one-time report (no email)."""
    filters = {}
    
    if config.get("audience"):
        filters["preset_key"] = config["audience"]
        filters["preset_display_name"] = config["name"]
    
    if config.get("price_strategy"):
        filters["price_strategy"] = config["price_strategy"]
    
    payload = {
        "report_type": config["type"],
        "city": CITY,
        "lookback_days": LOOKBACK_DAYS,
        "filters": filters if filters else None,
    }
    
    print(f"\n  📤 Creating: {config['name']}...")
    
    try:
        resp = requests.post(
            f"{API_BASE}/reports",
            headers=get_headers(token),
            json=payload,
            timeout=30
        )
        
        if resp.status_code in (200, 201, 202):
            data = resp.json()
            report_id = data.get("id")
            print(f"     ✅ Created report: {report_id}")
            return report_id
        else:
            print(f"     ❌ Failed ({resp.status_code}): {resp.text[:200]}")
            return None
            
    except Exception as e:
        print(f"     ❌ Error: {e}")
        return None


def create_scheduled_report(token: str, config: Dict, email: str) -> Optional[str]:
    """Create a scheduled report with immediate run and email delivery."""
    
    # Build filters
    filters = {}
    if config.get("audience"):
        filters["preset_key"] = config["audience"]
        filters["preset_display_name"] = config["name"]
    if config.get("price_strategy"):
        filters["price_strategy"] = config["price_strategy"]
    
    # Calculate next run time (5 minutes from now to allow processing)
    next_run = datetime.utcnow() + timedelta(minutes=2)
    
    payload = {
        "name": f"QA Test - {config['name']} - {CITY}",
        "report_type": config["type"],
        "city": CITY,
        "lookback_days": LOOKBACK_DAYS,
        "cadence": "once",  # One-time schedule
        "filters": filters if filters else None,
        "recipients": [
            {"type": "manual_email", "email": email}
        ],
        # Schedule for immediate run
        "run_at_time": next_run.strftime("%H:%M"),
        "run_on_days": [next_run.strftime("%A").lower()],
        "is_active": True
    }
    
    print(f"\n  📤 Creating schedule: {config['name']} → {email}")
    
    try:
        resp = requests.post(
            f"{API_BASE}/schedules",
            headers=get_headers(token),
            json=payload,
            timeout=30
        )
        
        if resp.status_code in (200, 201, 202):
            data = resp.json()
            schedule_id = data.get("id")
            print(f"     ✅ Schedule created: {schedule_id}")
            print(f"     📧 Email will be sent to: {email}")
            return schedule_id
        else:
            print(f"     ❌ Failed ({resp.status_code}): {resp.text[:300]}")
            return None
            
    except Exception as e:
        print(f"     ❌ Error: {e}")
        return None


def wait_and_check_reports(token: str, report_ids: List[str], max_wait: int = 180) -> Dict:
    """Wait for reports to complete and return URLs."""
    print(f"\n  ⏳ Waiting for {len(report_ids)} reports to complete...")
    
    results = {}
    start = time.time()
    pending = set(report_ids)
    
    while pending and (time.time() - start) < max_wait:
        for report_id in list(pending):
            try:
                resp = requests.get(
                    f"{API_BASE}/reports/{report_id}",
                    headers=get_headers(token),
                    timeout=30
                )
                
                if resp.status_code == 200:
                    data = resp.json()
                    status = data.get("status", "unknown")
                    
                    if status == "completed":
                        results[report_id] = {
                            "status": "completed",
                            "pdf_url": data.get("pdf_url"),
                            "html_url": data.get("html_url"),
                        }
                        pending.remove(report_id)
                        print(f"     ✅ Report {report_id[:8]}... completed")
                    elif status == "failed":
                        results[report_id] = {"status": "failed", "error": data.get("error_message")}
                        pending.remove(report_id)
                        print(f"     ❌ Report {report_id[:8]}... failed")
                        
            except Exception as e:
                pass  # Keep trying
        
        if pending:
            time.sleep(5)
            elapsed = int(time.time() - start)
            print(f"     ... {len(pending)} reports still processing ({elapsed}s elapsed)")
    
    # Mark remaining as timeout
    for report_id in pending:
        results[report_id] = {"status": "timeout"}
    
    return results


def poll_report_status(token: str, report_id: str, max_wait: int = 300) -> Dict:
    """Poll for report completion."""
    start = time.time()
    
    while time.time() - start < max_wait:
        try:
            resp = requests.get(
                f"{API_BASE}/reports/{report_id}",
                headers=get_headers(token),
                timeout=30
            )
            
            if resp.status_code == 200:
                data = resp.json()
                status = data.get("status", "unknown")
                
                if status == "completed":
                    return {
                        "status": "completed",
                        "pdf_url": data.get("pdf_url"),
                        "html_url": data.get("html_url"),
                    }
                elif status == "failed":
                    return {"status": "failed", "error": data.get("error_message")}
                    
        except Exception as e:
            print(f"     ⚠️ Poll error: {e}")
        
        time.sleep(5)
    
    return {"status": "timeout"}


def main():
    parser = argparse.ArgumentParser(description="QA Test - Downey Reports")
    parser.add_argument("--token", type=str, help="mr_token from browser cookies")
    parser.add_argument("--email", type=str, default=EMAIL, help=f"Email for delivery (default: {EMAIL})")
    parser.add_argument("--mode", choices=["reports", "schedules", "both"], default="reports",
                        help="reports=one-time (no email), schedules=with email, both=all")
    parser.add_argument("--quick", action="store_true", help="Quick mode: only essential reports")
    
    args = parser.parse_args()
    
    # Get token
    token = args.token or os.getenv("MR_TOKEN")
    
    if not token:
        print("=" * 60)
        print("  HOW TO GET YOUR TOKEN")
        print("=" * 60)
        print("""
1. Open https://www.trendyreports.io in your browser
2. Log in with your account
3. Open DevTools: Press F12 (or Cmd+Option+I on Mac)
4. Go to: Application → Cookies → trendyreports.io
5. Find 'mr_token' and copy its value
6. Run this script with: --token "paste-token-here"

Or set environment variable:
  export MR_TOKEN="paste-token-here"
  python scripts/qa_test_downey.py
        """)
        sys.exit(1)
    
    # Select reports
    reports = REPORTS_TO_TEST
    if args.quick:
        # Just 3 essential: All Buyers, Market Update, Closed Sales
        reports = [r for r in REPORTS_TO_TEST if r["name"] in 
                   ["New Listings - All Buyers", "Market Update", "Closed Sales"]]
    
    print("\n" + "=" * 60)
    print("  TRENDY REPORTS - QA TEST: DOWNEY, CA")
    print("=" * 60)
    print(f"  Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"  City: {CITY}")
    print(f"  Email: {args.email}")
    print(f"  Mode: {args.mode}")
    print(f"  Reports: {len(reports)}")
    print("=" * 60)
    
    results = []
    
    if args.mode in ("reports", "both"):
        print("\n" + "-" * 60)
        print("  ONE-TIME REPORTS (no email)")
        print("-" * 60)
        
        for config in reports:
            report_id = create_one_time_report(token, config)
            if report_id:
                results.append({
                    "name": config["name"],
                    "type": "report",
                    "id": report_id,
                    "status": "created"
                })
    
    if args.mode in ("schedules", "both"):
        print("\n" + "-" * 60)
        print(f"  SCHEDULED REPORTS (email → {args.email})")
        print("-" * 60)
        print("  Note: Schedules run on ticker (every 1-5 min). Email will arrive shortly.")
        
        for config in reports:
            schedule_id = create_scheduled_report(token, config, args.email)
            if schedule_id:
                results.append({
                    "name": config["name"],
                    "type": "schedule",
                    "id": schedule_id,
                    "status": "scheduled"
                })
    
    # Wait for one-time reports to complete
    report_ids = [r["id"] for r in results if r["type"] == "report"]
    if report_ids:
        report_results = wait_and_check_reports(token, report_ids)
        
        # Update results with URLs
        for r in results:
            if r["type"] == "report" and r["id"] in report_results:
                r.update(report_results[r["id"]])
    
    # Summary
    print("\n" + "=" * 60)
    print("  SUMMARY")
    print("=" * 60)
    
    completed = [r for r in results if r.get("status") == "completed"]
    scheduled = [r for r in results if r.get("type") == "schedule"]
    
    print(f"\n  ✅ Completed reports: {len(completed)}")
    print(f"  📅 Scheduled for email: {len(scheduled)}")
    
    if completed:
        print("\n  📄 REPORT LINKS (open in browser):")
        print("  " + "-" * 50)
        for r in completed:
            print(f"\n  {r['name']}:")
            if r.get("pdf_url"):
                print(f"    PDF:  {r['pdf_url']}")
            if r.get("html_url"):
                print(f"    HTML: {r['html_url']}")
    
    if scheduled:
        print(f"\n  📧 Email will be sent to: {args.email}")
        print("     (Schedules run every 1-5 minutes)")
    
    print(f"\n  🌐 View all at: https://www.trendyreports.io/app")
    
    # Save results
    output_file = "qa_downey_results.json"
    with open(output_file, "w") as f:
        json.dump({
            "city": CITY,
            "email": args.email,
            "timestamp": datetime.now().isoformat(),
            "results": results
        }, f, indent=2)
    
    print(f"\n  📁 Results saved to: {output_file}")


if __name__ == "__main__":
    main()

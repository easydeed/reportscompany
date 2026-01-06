#!/usr/bin/env python3
"""
qa_deliver_reports.py — TrendyReports

Creates temporary schedules for SIMPLIFIED PRODUCT report types and delivers
them to an email so QA can validate output WITHOUT using the UI.

SIMPLIFIED PRODUCT (Jan 2026):
  1. New Listings (gallery) - with 6 audience filters
  2. Market Update (snapshot)
  3. Closed Sales

Supports JWT token auth (--token) or email/password login.

Docs: docs/SCHEDULES.md, docs/PRODUCT_SIMPLIFICATION_STRATEGY.md
"""

from __future__ import annotations

import argparse
import json
import sys
import time
from dataclasses import dataclass
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

import requests


# ============================================================================
# SIMPLIFIED PRODUCT - Report Type Configurations
# ============================================================================
# Based on PRODUCT_SIMPLIFICATION_STRATEGY.md and AUDIENCE_OPTIONS in types.ts
# ============================================================================

REPORT_CONFIGS = [
    # Market Update (no filters)
    {
        "report_type": "market_snapshot",
        "name_suffix": "Market Update",
        "filters": {},
    },
    # Closed Sales (no filters)
    {
        "report_type": "closed",
        "name_suffix": "Closed Sales",
        "filters": {},
    },
    # New Listings Gallery - All Audiences
    {
        "report_type": "new_listings_gallery",
        "name_suffix": "New Listings - All",
        "filters": {},
    },
    {
        "report_type": "new_listings_gallery",
        "name_suffix": "New Listings - First-Time Buyers",
        "filters": {
            "minbeds": 2,
            "minbaths": 2,
            "subtype": "SingleFamilyResidence",
            "price_strategy": {
                "mode": "maxprice_pct_of_median_list",
                "value": 0.70
            },
            "preset_display_name": "First-Time Buyer"
        },
    },
    {
        "report_type": "new_listings_gallery",
        "name_suffix": "New Listings - Luxury",
        "filters": {
            "subtype": "SingleFamilyResidence",
            "price_strategy": {
                "mode": "minprice_pct_of_median_list",
                "value": 1.50
            },
            "preset_display_name": "Luxury Showcase"
        },
    },
    {
        "report_type": "new_listings_gallery",
        "name_suffix": "New Listings - Families",
        "filters": {
            "minbeds": 3,
            "minbaths": 2,
            "subtype": "SingleFamilyResidence",
            "preset_display_name": "Family Homes"
        },
    },
    {
        "report_type": "new_listings_gallery",
        "name_suffix": "New Listings - Condo",
        "filters": {
            "subtype": "Condominium",
            "preset_display_name": "Condo Watch"
        },
    },
    {
        "report_type": "new_listings_gallery",
        "name_suffix": "New Listings - Investors",
        "filters": {
            "price_strategy": {
                "mode": "maxprice_pct_of_median_list",
                "value": 0.50
            },
            "preset_display_name": "Investor Deals"
        },
    },
]


@dataclass
class CreatedSchedule:
    report_type: str
    schedule_id: str
    name: str


def _weekly_dow_for_api(dt: datetime) -> int:
    """
    SCHEDULES.md uses Monday=1 in examples.
    We assume 0=Sunday, 1=Monday ... 6=Saturday.
    Python weekday(): Monday=0 ... Sunday=6
    """
    return (dt.weekday() + 1) % 7


def login(session: requests.Session, base_url: str, email: str, password: str) -> None:
    url = f"{base_url.rstrip('/')}/v1/auth/login"
    resp = session.post(url, json={"email": email, "password": password}, timeout=30)
    if resp.status_code >= 400:
        raise RuntimeError(f"Login failed {resp.status_code}: {resp.text[:400]}")
    # Cookie-based auth should now be in session.cookies
    if not session.cookies:
        try:
            data = resp.json()
        except Exception:
            data = {}
        if "token" in data:
            session.headers["Authorization"] = f"Bearer {data['token']}"


def create_schedule(
    session: requests.Session,
    base_url: str,
    *,
    name: str,
    report_type: str,
    city: str,
    lookback_days: int,
    timezone: str,
    send_dt: datetime,
    deliver_to: str,
    filters: dict | None = None,
) -> str:
    url = f"{base_url.rstrip('/')}/v1/schedules"

    payload = {
        "name": name,
        "report_type": report_type,
        "city": city,
        "lookback_days": lookback_days,
        "cadence": "weekly",
        "weekly_dow": _weekly_dow_for_api(send_dt),
        "send_hour": send_dt.hour,
        "send_minute": send_dt.minute,
        "timezone": timezone,
        "recipients": [{"type": "manual_email", "email": deliver_to}],
        "active": True,
    }
    
    # Add filters if provided (for Smart Presets / Audience targeting)
    if filters:
        payload["filters"] = filters

    resp = session.post(url, json=payload, timeout=30)
    if resp.status_code >= 400:
        raise RuntimeError(f"Create schedule failed ({report_type}) {resp.status_code}: {resp.text[:600]}")

    data = resp.json()
    schedule_id = data.get("id") or data.get("schedule_id") or data.get("data", {}).get("id")
    if not schedule_id:
        raise RuntimeError(f"Could not find schedule id in response: {json.dumps(data)[:800]}")
    return schedule_id


def list_runs(session: requests.Session, base_url: str, schedule_id: str, limit: int = 10) -> list[dict]:
    url = f"{base_url.rstrip('/')}/v1/schedules/{schedule_id}/runs"
    resp = session.get(url, params={"limit": limit}, timeout=30)
    if resp.status_code >= 400:
        raise RuntimeError(f"List runs failed {resp.status_code}: {resp.text[:400]}")
    data = resp.json()
    if isinstance(data, list):
        return data
    return data.get("runs") or data.get("data") or []


def delete_schedule(session: requests.Session, base_url: str, schedule_id: str) -> None:
    url = f"{base_url.rstrip('/')}/v1/schedules/{schedule_id}"
    resp = session.delete(url, timeout=30)
    if resp.status_code >= 400:
        raise RuntimeError(f"Delete schedule failed {resp.status_code}: {resp.text[:400]}")


def main() -> int:
    ap = argparse.ArgumentParser(
        description="QA: Deliver simplified product emails (New Listings, Market Update, Closed Sales)"
    )
    ap.add_argument("--base-url", required=True, help="API base, e.g. https://reportscompany.onrender.com")
    
    # Auth options - token OR email/password
    auth_group = ap.add_mutually_exclusive_group(required=True)
    auth_group.add_argument("--token", help="JWT token for auth (skips login)")
    auth_group.add_argument("--login-email", help="Login email for TrendyReports")
    ap.add_argument("--login-password", help="Login password (required if using --login-email)")
    
    ap.add_argument("--deliver-to", required=True, help="Email address to receive the test reports")
    ap.add_argument("--city", default="Irvine", help="City for testing (default Irvine)")
    ap.add_argument("--lookback", type=int, default=30, help="Lookback days (default 30)")
    ap.add_argument("--timezone", default="America/Los_Angeles", help="Timezone for schedule send time")
    ap.add_argument("--poll-seconds", type=int, default=10, help="Poll interval")
    ap.add_argument("--timeout-seconds", type=int, default=900, help="Overall timeout for polling")
    ap.add_argument("--keep-schedules", action="store_true", help="Do not delete temporary schedules")
    ap.add_argument("--quick", action="store_true", help="Quick mode: only test 3 core reports (no audience filters)")
    args = ap.parse_args()

    # Validate email/password combo
    if args.login_email and not args.login_password:
        ap.error("--login-password is required when using --login-email")

    tz = ZoneInfo(args.timezone)
    now = datetime.now(tz)

    # Send at next minute + 2 minutes buffer
    send_dt = (now + timedelta(minutes=2)).replace(second=0, microsecond=0)

    session = requests.Session()
    session.headers["Content-Type"] = "application/json"

    # Auth: JWT token or email/password login
    if args.token:
        print(f"[QA] Using JWT token for auth...")
        session.headers["Authorization"] = f"Bearer {args.token}"
    else:
        print(f"[QA] Logging in as {args.login_email}...")
        login(session, args.base_url, args.login_email, args.login_password)

    # Select report configs based on --quick flag
    if args.quick:
        # Quick mode: just the 3 core reports (no audience variations)
        configs = [c for c in REPORT_CONFIGS if c["name_suffix"] in 
                   ["Market Update", "Closed Sales", "New Listings - All"]]
        print(f"[QA] Quick mode: testing 3 core reports only")
    else:
        configs = REPORT_CONFIGS
        print(f"[QA] Full mode: testing all {len(configs)} report configurations")

    created: list[CreatedSchedule] = []
    try:
        print(f"[QA] Creating schedules to deliver to {args.deliver_to} at {send_dt.isoformat()}...")
        ts = now.strftime("%Y%m%d-%H%M%S")
        
        for cfg in configs:
            name = f"QA {args.city} {cfg['name_suffix']} {ts}"
            sid = create_schedule(
                session,
                args.base_url,
                name=name,
                report_type=cfg["report_type"],
                city=args.city,
                lookback_days=args.lookback,
                timezone=args.timezone,
                send_dt=send_dt,
                deliver_to=args.deliver_to,
                filters=cfg.get("filters"),
            )
            created.append(CreatedSchedule(
                report_type=cfg["report_type"], 
                schedule_id=sid, 
                name=cfg["name_suffix"]
            ))
            print(f"  + {cfg['name_suffix']}: {sid}")

        print(f"\n[QA] Waiting for {len(created)} runs to complete...")
        print("[QA] (Ticker runs every 60s, worker processes reports)\n")
        
        start = time.time()
        done = set()

        while True:
            elapsed = int(time.time() - start)
            if elapsed > args.timeout_seconds:
                raise RuntimeError("Timed out waiting for schedule runs.")

            for s in created:
                if s.schedule_id in done:
                    continue

                runs = list_runs(session, args.base_url, s.schedule_id, limit=5)
                if not runs:
                    continue

                latest = runs[0]
                status = (latest.get("status") or "").lower()
                err = latest.get("error")
                if status in ("completed", "failed", "failed_email"):
                    done.add(s.schedule_id)
                    status_icon = "[OK]" if status == "completed" else "[FAIL]"
                    print(f"  {status_icon} {s.name}: {status}" + (f" | {err}" if err else ""))

            if len(done) == len(created):
                break

            # Progress indicator
            remaining = len(created) - len(done)
            print(f"  ... waiting ({remaining} remaining, {elapsed}s elapsed)", end="\r")
            time.sleep(args.poll_seconds)

        print("\n")
        print("=" * 60)
        print("[QA] All schedules reached terminal status!")
        print(f"[QA] Check inbox: {args.deliver_to}")
        print("=" * 60)
        return 0

    finally:
        if created and not args.keep_schedules:
            print("\n[QA] Cleaning up temporary schedules...")
            for s in created:
                try:
                    delete_schedule(session, args.base_url, s.schedule_id)
                    print(f"  - deleted {s.name}")
                except Exception as e:
                    print(f"  ! failed deleting {s.schedule_id}: {e}", file=sys.stderr)


if __name__ == "__main__":
    raise SystemExit(main())

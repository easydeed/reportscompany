#!/usr/bin/env python3
"""
QA-RUN-ALL-REPORTS — Generate one PDF for each of the 8 market report types.

Hits the live production API (or whatever QA_API_BASE points at) using Jerry's
JWT, queues one report of every type for the same city/lookback, polls until
each PDF is uploaded to R2, then prints a clean summary table of pdf_urls so
the themes can be reviewed side-by-side.

USAGE
-----
    export QA_TOKEN="<paste JWT here>"
    # optional — defaults to production
    export QA_API_BASE="https://reportscompany-api.onrender.com"
    python scripts/qa_generate_all_reports.py

HOW TO GET A JWT
----------------
    1. Log in at https://trendyreports.io
    2. Open DevTools → Network tab
    3. Click any page that loads data (e.g. /app/reports)
    4. Find a request to /v1/... and copy the value of the
       Authorization: Bearer <token> header (everything after "Bearer ")
    5. Paste it into QA_TOKEN

CONFIG TWEAKS
-------------
    --city <name>          Override CITY (default: Irvine)
    --lookback <days>      Override LOOKBACK (default: 30)
    --theme <id>           Override theme_id (default: 1 — teal)
    --timeout <seconds>    Per-report poll timeout (default: 120)
    --json <path>          Also dump full results to a JSON file
"""

from __future__ import annotations

import argparse
import os
import sys
import time
from dataclasses import asdict, dataclass, field
from datetime import datetime
from typing import Optional

try:
    import requests
except ImportError:
    print("ERROR: 'requests' is not installed.")
    print("       Install it with:  pip install requests")
    sys.exit(1)


# ─────────────────────────────────────────────────────────────────────────────
# Ticket constants
# ─────────────────────────────────────────────────────────────────────────────

REPORT_TYPES = [
    "market_snapshot",
    "new_listings_gallery",
    "new_listings",
    "closed",
    "inventory",
    "featured_listings",
    "open_houses",
    "price_bands",
]

DEFAULT_API_BASE = "https://reportscompany-api.onrender.com"
DEFAULT_CITY = "Irvine"
DEFAULT_LOOKBACK = 30
DEFAULT_THEME_ID = 1            # 1 = teal
DEFAULT_TIMEOUT_SECONDS = 120   # per-report poll budget
POLL_INTERVAL_SECONDS = 5

# Widest type-name we expect to render — used to right-pad the summary table.
_TYPE_COL_WIDTH = max(len(t) for t in REPORT_TYPES)


@dataclass
class Result:
    report_type: str
    report_id: Optional[str] = None
    status: str = "pending"
    pdf_url: Optional[str] = None
    error: Optional[str] = None
    duration_seconds: float = 0.0
    pdf_size_bytes: Optional[int] = None
    notes: list = field(default_factory=list)


# ─────────────────────────────────────────────────────────────────────────────
# API helpers
# ─────────────────────────────────────────────────────────────────────────────

def _headers(token: str) -> dict:
    return {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
    }


def create_report(
    api_base: str,
    token: str,
    report_type: str,
    city: str,
    lookback: int,
    theme_id: int,
) -> tuple[Optional[str], Optional[str]]:
    """POST /v1/reports → (report_id, error)."""
    payload = {
        "report_type": report_type,
        "city": city,
        "lookback_days": lookback,
        "theme_id": str(theme_id),
    }
    try:
        resp = requests.post(
            f"{api_base}/v1/reports",
            headers=_headers(token),
            json=payload,
            timeout=30,
        )
    except requests.RequestException as exc:
        return None, f"network error on POST /v1/reports: {exc}"

    if resp.status_code not in (200, 201, 202):
        return None, f"POST returned {resp.status_code}: {resp.text[:300]}"

    try:
        data = resp.json()
    except ValueError:
        return None, f"non-JSON response: {resp.text[:300]}"

    # The /v1/reports endpoint returns {"report_id": ..., "status": ...}
    report_id = data.get("report_id") or data.get("id")
    if not report_id:
        return None, f"response had no report_id: {data}"
    return str(report_id), None


def poll_report(
    api_base: str,
    token: str,
    report_id: str,
    timeout: int,
) -> dict:
    """Poll GET /v1/reports/{id} until terminal state or timeout."""
    deadline = time.monotonic() + timeout
    last_payload: dict = {}
    while time.monotonic() < deadline:
        try:
            resp = requests.get(
                f"{api_base}/v1/reports/{report_id}",
                headers=_headers(token),
                timeout=30,
            )
        except requests.RequestException as exc:
            time.sleep(POLL_INTERVAL_SECONDS)
            last_payload = {"_poll_error": str(exc)}
            continue

        if resp.status_code != 200:
            time.sleep(POLL_INTERVAL_SECONDS)
            last_payload = {"_poll_error": f"{resp.status_code}: {resp.text[:200]}"}
            continue

        try:
            data = resp.json()
        except ValueError:
            time.sleep(POLL_INTERVAL_SECONDS)
            continue

        last_payload = data
        status = (data.get("status") or "").lower()
        if status == "completed":
            return data
        if status in ("failed", "error"):
            return data
        # Still pending / processing — wait and retry
        time.sleep(POLL_INTERVAL_SECONDS)

    last_payload["status"] = last_payload.get("status") or "timeout"
    last_payload["_timed_out"] = True
    return last_payload


def fetch_pdf_size(pdf_url: str) -> Optional[int]:
    """HEAD the PDF to get its size in bytes (best effort)."""
    if not pdf_url:
        return None
    try:
        resp = requests.head(pdf_url, timeout=15, allow_redirects=True)
        size = resp.headers.get("Content-Length")
        return int(size) if size else None
    except (requests.RequestException, ValueError):
        return None


# ─────────────────────────────────────────────────────────────────────────────
# Per-report runner
# ─────────────────────────────────────────────────────────────────────────────

def run_one(
    api_base: str,
    token: str,
    report_type: str,
    city: str,
    lookback: int,
    theme_id: int,
    timeout: int,
) -> Result:
    result = Result(report_type=report_type)
    t0 = time.monotonic()

    print(f"  → {report_type:<{_TYPE_COL_WIDTH}}  creating…", flush=True)
    report_id, err = create_report(api_base, token, report_type, city, lookback, theme_id)
    if err or not report_id:
        result.status = "create_failed"
        result.error = err or "no report_id returned"
        result.duration_seconds = time.monotonic() - t0
        print(f"     {report_type}: create failed — {result.error}", flush=True)
        return result

    result.report_id = report_id
    print(
        f"     {report_type}: queued ({report_id}); polling every "
        f"{POLL_INTERVAL_SECONDS}s up to {timeout}s…",
        flush=True,
    )

    final = poll_report(api_base, token, report_id, timeout)
    result.duration_seconds = time.monotonic() - t0
    status = (final.get("status") or "unknown").lower()
    result.status = status
    result.pdf_url = final.get("pdf_url")

    if status == "completed" and result.pdf_url:
        result.pdf_size_bytes = fetch_pdf_size(result.pdf_url)
    elif status == "completed":
        result.error = "completed but no pdf_url in response"
    elif final.get("_timed_out"):
        result.error = f"timed out after {timeout}s (last status: {final.get('status')})"
    else:
        result.error = (
            final.get("error_message")
            or final.get("error")
            or final.get("_poll_error")
            or f"non-completed status: {status}"
        )

    return result


# ─────────────────────────────────────────────────────────────────────────────
# Summary printing
# ─────────────────────────────────────────────────────────────────────────────

def _fmt_size(n: Optional[int]) -> str:
    if not n:
        return "?"
    kb = n / 1024.0
    if kb < 1024:
        return f"{kb:.1f} KB"
    return f"{kb / 1024:.2f} MB"


def print_summary(results: list[Result]) -> None:
    print()
    print("=" * 78)
    print("  QA-RUN-ALL-REPORTS — Summary")
    print("=" * 78)

    succeeded = 0
    for r in results:
        if r.status == "completed" and r.pdf_url:
            succeeded += 1
            size_str = _fmt_size(r.pdf_size_bytes)
            print(
                f"  ✅ {r.report_type:<{_TYPE_COL_WIDTH}} → {r.pdf_url}  "
                f"({size_str}, {r.duration_seconds:.0f}s)"
            )
        else:
            err = (r.error or r.status or "unknown").strip()
            print(
                f"  ❌ {r.report_type:<{_TYPE_COL_WIDTH}} → FAILED: {err}  "
                f"({r.duration_seconds:.0f}s)"
            )

    print()
    print(f"  Total: {succeeded}/{len(results)} succeeded")
    print("=" * 78)


# ─────────────────────────────────────────────────────────────────────────────
# Entrypoint
# ─────────────────────────────────────────────────────────────────────────────

def main() -> int:
    parser = argparse.ArgumentParser(
        description="Generate one PDF for each of the 8 market report types.",
    )
    parser.add_argument("--city", default=DEFAULT_CITY, help=f"City (default: {DEFAULT_CITY})")
    parser.add_argument("--lookback", type=int, default=DEFAULT_LOOKBACK,
                        help=f"Lookback days (default: {DEFAULT_LOOKBACK})")
    parser.add_argument("--theme", type=int, default=DEFAULT_THEME_ID,
                        help=f"theme_id (default: {DEFAULT_THEME_ID})")
    parser.add_argument("--timeout", type=int, default=DEFAULT_TIMEOUT_SECONDS,
                        help=f"Per-report poll timeout in seconds (default: {DEFAULT_TIMEOUT_SECONDS})")
    parser.add_argument("--json", dest="json_path", default=None,
                        help="Optional path to dump full results JSON")
    args = parser.parse_args()

    token = os.getenv("QA_TOKEN")
    if not token:
        print("ERROR: QA_TOKEN is not set.")
        print()
        print("Set it before running, e.g.:")
        print("    export QA_TOKEN=\"<paste JWT here>\"")
        print()
        print("How to get a JWT:")
        print("  1. Log in to https://trendyreports.io")
        print("  2. Open DevTools → Network tab")
        print("  3. Click any in-app page that loads data")
        print("  4. Pick any /v1/... request and copy the")
        print("     'Authorization: Bearer <token>' value (just the part after 'Bearer ')")
        print("  5. export QA_TOKEN=\"<token>\"")
        return 2

    api_base = (os.getenv("QA_API_BASE") or DEFAULT_API_BASE).rstrip("/")

    print("=" * 78)
    print("  QA-RUN-ALL-REPORTS")
    print("=" * 78)
    print(f"  Start    : {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"  API base : {api_base}")
    print(f"  City     : {args.city}")
    print(f"  Lookback : {args.lookback} days")
    print(f"  theme_id : {args.theme}")
    print(f"  Timeout  : {args.timeout}s per report")
    print(f"  Reports  : {len(REPORT_TYPES)} types")
    print("=" * 78)
    print()

    results: list[Result] = []
    for report_type in REPORT_TYPES:
        results.append(run_one(
            api_base=api_base,
            token=token,
            report_type=report_type,
            city=args.city,
            lookback=args.lookback,
            theme_id=args.theme,
            timeout=args.timeout,
        ))

    print_summary(results)

    if args.json_path:
        payload = {
            "generated_at": datetime.now().isoformat(),
            "api_base": api_base,
            "city": args.city,
            "lookback_days": args.lookback,
            "theme_id": args.theme,
            "results": [asdict(r) for r in results],
        }
        try:
            import json
            with open(args.json_path, "w", encoding="utf-8") as fh:
                json.dump(payload, fh, indent=2)
            print(f"  JSON written to: {args.json_path}")
        except OSError as exc:
            print(f"  WARN: could not write JSON to {args.json_path}: {exc}")

    failures = [r for r in results if r.status != "completed" or not r.pdf_url]
    return 0 if not failures else 1


if __name__ == "__main__":
    sys.exit(main())

#!/usr/bin/env python3
"""
QA-SIMPLE-GENERATE — Generate one of each report type using the worker directly.

No API. No JWT. No HTTP. This script seeds a `report_generations` row for each
of the 8 market report types and then runs the existing Celery task body
synchronously in-process. The task does the full data fetch + themed
MarketReportBuilder render + PDFShift + R2 upload pipeline — same code path
as a scheduled report.

Requirements:
    - DATABASE_URL set (same DB the worker uses)
    - PDFSHIFT_API_KEY / R2 creds set (same as worker)
    - SIMPLYRETS_* credentials set
    - Run from a place where the worker package is importable. This script
      adds apps/worker/src to sys.path automatically.

Usage:
    python scripts/qa_generate_one_of_each.py
    python scripts/qa_generate_one_of_each.py --city "La Verne"
    python scripts/qa_generate_one_of_each.py --city Irvine --theme 4 --lookback 30

    # Override the account used to own the test runs:
    export QA_ACCOUNT_ID="<uuid>"
    python scripts/qa_generate_one_of_each.py

The script prints a clean summary table of pdf_urls and exits 0 if all 8
succeeded, 1 otherwise.
"""

from __future__ import annotations

import argparse
import os
import sys
import time
import uuid
from pathlib import Path
from typing import Optional

# ─────────────────────────────────────────────────────────────────────────────
# Path setup — must come BEFORE worker imports
# ─────────────────────────────────────────────────────────────────────────────

SCRIPT_DIR = Path(__file__).resolve().parent
REPO_ROOT = SCRIPT_DIR.parent
WORKER_SRC = REPO_ROOT / "apps" / "worker" / "src"
API_SRC = REPO_ROOT / "apps" / "api" / "src"
for p in (WORKER_SRC, API_SRC):
    if p.exists() and str(p) not in sys.path:
        sys.path.insert(0, str(p))

# Optionally load .env so DATABASE_URL etc. are populated when running locally.
for env_path in (REPO_ROOT / "apps" / "worker" / ".env",
                 REPO_ROOT / "apps" / "api" / ".env",
                 REPO_ROOT / ".env"):
    if env_path.exists():
        try:
            from dotenv import load_dotenv  # type: ignore
            load_dotenv(env_path, override=False)
        except ImportError:
            # Manual fallback — no hard dep on python-dotenv
            with open(env_path, encoding="utf-8") as fh:
                for line in fh:
                    line = line.strip()
                    if line and not line.startswith("#") and "=" in line:
                        k, _, v = line.partition("=")
                        os.environ.setdefault(k.strip(), v.strip().strip('"').strip("'"))


# ─────────────────────────────────────────────────────────────────────────────
# Worker imports (after path/env setup)
# ─────────────────────────────────────────────────────────────────────────────

try:
    import psycopg  # type: ignore
except ImportError:
    print("ERROR: psycopg is not installed. Run: pip install 'psycopg[binary]'")
    sys.exit(2)

try:
    from worker.tasks import generate_report, DATABASE_URL  # type: ignore
except Exception as exc:
    print(f"ERROR: could not import worker.tasks.generate_report: {exc}")
    print("       Make sure the worker dependencies are installed and DATABASE_URL is set.")
    sys.exit(2)


# ─────────────────────────────────────────────────────────────────────────────
# Constants
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

_TYPE_COL_WIDTH = max(len(t) for t in REPORT_TYPES)


# ─────────────────────────────────────────────────────────────────────────────
# DB helpers
# ─────────────────────────────────────────────────────────────────────────────

def resolve_account_id(explicit: Optional[str]) -> str:
    """Resolve which account owns these test runs.

    Priority:
      1. --account-id CLI arg
      2. QA_ACCOUNT_ID env var
      3. First active account whose name looks like Jerry/admin
      4. First active account at all (last resort)
    """
    if explicit:
        return explicit
    env_val = os.environ.get("QA_ACCOUNT_ID")
    if env_val:
        return env_val

    with psycopg.connect(DATABASE_URL, autocommit=True) as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT id::text FROM accounts
                WHERE is_active = true
                  AND (name ILIKE '%jerry%' OR name ILIKE '%admin%')
                ORDER BY created_at ASC
                LIMIT 1
                """
            )
            row = cur.fetchone()
            if row:
                return row[0]
            cur.execute(
                """
                SELECT id::text FROM accounts
                WHERE is_active = true
                ORDER BY created_at ASC
                LIMIT 1
                """
            )
            row = cur.fetchone()
            if row:
                print(
                    f"  WARN: no jerry/admin account found, falling back to first "
                    f"active account: {row[0]}",
                )
                return row[0]

    print("ERROR: No active account found in the database.")
    print("       Set QA_ACCOUNT_ID=<uuid> to point at the account you want to use.")
    sys.exit(2)


def seed_report_row(
    account_id: str,
    report_type: str,
    city: str,
    lookback_days: int,
    theme_id: str,
) -> tuple[str, dict]:
    """Insert a pending report_generations row mirroring what POST /v1/reports does.

    Returns (run_id, params_dict_for_task).
    """
    run_id = str(uuid.uuid4())
    params: dict = {
        "city": city,
        "zips": None,
        "lookback_days": lookback_days,
        "filters": {},
        "additional_params": {},
    }

    import json
    with psycopg.connect(DATABASE_URL, autocommit=True) as conn:
        with conn.cursor() as cur:
            cur.execute(f"SET LOCAL app.current_account_id TO '{account_id}'")
            cur.execute(
                """
                INSERT INTO report_generations
                  (id, account_id, report_type, input_params, status, theme_id, accent_color)
                VALUES (%s::uuid, %s::uuid, %s, %s::jsonb, 'pending', %s, NULL)
                """,
                (run_id, account_id, report_type, json.dumps(params), str(theme_id)),
            )
    return run_id, params


def fetch_completed_row(run_id: str) -> dict:
    """SELECT the final state of the row after the task ran."""
    with psycopg.connect(DATABASE_URL, autocommit=True) as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT status, pdf_url, html_url, error, error_message,
                       processing_time_ms
                FROM report_generations
                WHERE id = %s::uuid
                """,
                (run_id,),
            )
            row = cur.fetchone()
            if not row:
                return {"status": "missing", "pdf_url": None,
                        "html_url": None, "error": "row vanished",
                        "error_message": None, "processing_time_ms": None}
            return {
                "status": row[0],
                "pdf_url": row[1],
                "html_url": row[2],
                "error": row[3],
                "error_message": row[4],
                "processing_time_ms": row[5],
            }


# ─────────────────────────────────────────────────────────────────────────────
# Runner
# ─────────────────────────────────────────────────────────────────────────────

def run_one(account_id: str, report_type: str, city: str,
            lookback: int, theme_id: str) -> dict:
    start = time.perf_counter()
    print(f"\n→ {report_type:<{_TYPE_COL_WIDTH}}  seeding…", flush=True)

    try:
        run_id, params = seed_report_row(
            account_id=account_id,
            report_type=report_type,
            city=city,
            lookback_days=lookback,
            theme_id=theme_id,
        )
    except Exception as exc:
        elapsed = int(time.perf_counter() - start)
        msg = f"DB insert failed: {exc}"
        print(f"   ❌ {msg} ({elapsed}s)")
        return {"report_type": report_type, "status": "seed_failed",
                "pdf_url": None, "error": msg, "elapsed": elapsed}

    print(f"   queued run_id={run_id}; running task body in-process…", flush=True)

    task_error: Optional[str] = None
    try:
        # .apply() executes the task body synchronously in this process,
        # bypasses the broker, and (importantly) does NOT honor autoretry —
        # we get a single attempt with any exception captured on the result.
        async_result = generate_report.apply(
            args=[run_id, account_id, report_type, params]
        )
        # Surface task-level errors but don't re-raise: we still want to
        # read the DB row so we can report what actually happened.
        if async_result.failed():
            task_error = repr(async_result.result)
    except Exception as exc:
        task_error = f"task crashed: {exc}"

    elapsed = int(time.perf_counter() - start)
    final = fetch_completed_row(run_id)

    record = {
        "report_type": report_type,
        "run_id": run_id,
        "status": final["status"],
        "pdf_url": final["pdf_url"],
        "elapsed": elapsed,
        "error": (final["error_message"] or final["error"] or task_error),
    }

    if final["status"] == "completed" and final["pdf_url"]:
        print(f"   ✅ {final['pdf_url']} ({elapsed}s)")
    else:
        err = record["error"] or final["status"] or "unknown"
        print(f"   ❌ FAILED: {err} ({elapsed}s)")

    return record


def print_summary(results: list[dict]) -> int:
    print()
    print("=" * 78)
    print("  QA-SIMPLE-GENERATE — Summary")
    print("=" * 78)

    succeeded = 0
    for r in results:
        if r["status"] == "completed" and r["pdf_url"]:
            succeeded += 1
            print(f"  ✅ {r['report_type']:<{_TYPE_COL_WIDTH}}  "
                  f"{r['pdf_url']}  ({r['elapsed']}s)")
        else:
            err = (r.get("error") or r["status"] or "unknown").strip()
            print(f"  ❌ {r['report_type']:<{_TYPE_COL_WIDTH}}  "
                  f"FAILED: {err}  ({r['elapsed']}s)")
    print()
    print(f"  Total: {succeeded}/{len(results)} succeeded")
    print("=" * 78)
    return 0 if succeeded == len(results) else 1


# ─────────────────────────────────────────────────────────────────────────────
# Entrypoint
# ─────────────────────────────────────────────────────────────────────────────

def main() -> int:
    parser = argparse.ArgumentParser(
        description="Generate one of each market report type via the worker (no API).",
    )
    parser.add_argument("--city", default="Irvine", help="City name (default: Irvine)")
    parser.add_argument("--lookback", type=int, default=30,
                        help="Lookback days (default: 30)")
    parser.add_argument("--theme", default="1",
                        help="theme_id stored on report_generations (default: 1 = teal)")
    parser.add_argument("--account-id", default=None,
                        help="Account UUID to own the test runs "
                             "(default: QA_ACCOUNT_ID env, then first jerry/admin "
                             "active account, then first active account)")
    parser.add_argument("--only", default=None,
                        help="Comma-separated subset of report types to run "
                             "(default: all 8)")
    args = parser.parse_args()

    account_id = resolve_account_id(args.account_id)

    types = REPORT_TYPES
    if args.only:
        requested = [t.strip() for t in args.only.split(",") if t.strip()]
        unknown = [t for t in requested if t not in REPORT_TYPES]
        if unknown:
            print(f"ERROR: unknown report types: {unknown}")
            print(f"       Valid types: {REPORT_TYPES}")
            return 2
        types = requested

    print("=" * 78)
    print("  QA-SIMPLE-GENERATE")
    print("=" * 78)
    print(f"  Account  : {account_id}")
    print(f"  City     : {args.city}")
    print(f"  Lookback : {args.lookback} days")
    print(f"  theme_id : {args.theme}")
    print(f"  Reports  : {len(types)} type(s)")
    print("=" * 78)

    results = [run_one(account_id, t, args.city, args.lookback, args.theme)
               for t in types]
    return print_summary(results)


if __name__ == "__main__":
    sys.exit(main())

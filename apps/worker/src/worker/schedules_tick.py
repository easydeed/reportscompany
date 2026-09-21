"""
Schedules Ticker: Background process that finds due schedules and enqueues reports.

Runs every 60 seconds, finds schedules where next_run_at <= NOW() or NULL,
computes next run time, enqueues report to Celery, creates audit record.

PASS S2: Timezone-aware - interprets send_hour/send_minute in schedule's timezone,
converts to UTC for next_run_at storage.

Deploy as a separate Render Background Worker:
  Start command: PYTHONPATH=./src poetry run python -m worker.schedules_tick
"""

import os
import time
import logging
import json
import httpx
from datetime import datetime, timedelta, date
from typing import Optional, Dict, Any
from zoneinfo import ZoneInfo
import psycopg
import ssl
from celery import Celery
from .limit_checker import check_usage_limit

# Create a separate Celery instance for ticker (no result backend needed)
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")

# Strip SSL parameters for Celery
if "ssl_cert_reqs=" in REDIS_URL:
    BROKER = REDIS_URL.split("?")[0]
    SSL_CONFIG = {
        'ssl_cert_reqs': ssl.CERT_REQUIRED,
        'ssl_ca_certs': None,
        'ssl_certfile': None,
        'ssl_keyfile': None
    }
else:
    BROKER = REDIS_URL
    SSL_CONFIG = None

celery = Celery(
    "market_reports_ticker",
    broker=BROKER,
    backend=None,  # No result backend needed for ticker
)

config_updates = {
    "task_serializer": "json",
    "accept_content": ["json"],
    "result_serializer": "json",
    "timezone": "UTC",
    "enable_utc": True,
    "task_ignore_result": True,  # Don't track results
}

if SSL_CONFIG:
    config_updates["broker_use_ssl"] = SSL_CONFIG

celery.conf.update(**config_updates)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# JSON serialization helper for datetime objects
def safe_json_dumps(obj):
    """JSON serializer that handles datetime objects."""
    def default_handler(o):
        if isinstance(o, (datetime, date)):
            return o.isoformat()
        raise TypeError(f"Object of type {type(o).__name__} is not JSON serializable")
    return json.dumps(obj, default=default_handler)

# Database connection
DATABASE_URL = os.getenv("DATABASE_URL")
if not DATABASE_URL:
    raise ValueError("DATABASE_URL environment variable is required")

# Ticker interval (seconds)
TICK_INTERVAL = int(os.getenv("TICK_INTERVAL", "60"))

# API keep-alive settings
API_BASE_URL = os.getenv("API_BASE_URL", "https://reportscompany.onrender.com")
KEEP_ALIVE_INTERVAL = int(os.getenv("KEEP_ALIVE_INTERVAL", "300"))  # 5 minutes default
_last_keep_alive = 0  # Track last ping time


def keep_api_warm():
    """
    Ping the API health endpoint to prevent Render cold starts.
    Called periodically from the ticker loop.
    """
    global _last_keep_alive
    
    now = time.time()
    
    # Only ping every KEEP_ALIVE_INTERVAL seconds
    if now - _last_keep_alive < KEEP_ALIVE_INTERVAL:
        return
    
    _last_keep_alive = now
    
    try:
        response = httpx.get(f"{API_BASE_URL}/health", timeout=10.0)
        logger.info(f"🔥 API keep-alive ping: {response.status_code}")
    except httpx.TimeoutException:
        logger.warning("⚠️ API keep-alive ping timed out")
    except Exception as e:
        logger.warning(f"⚠️ API keep-alive ping failed: {e}")


def compute_next_run(
    cadence: str,
    weekly_dow: Optional[int],
    monthly_dom: Optional[int],
    send_hour: int,
    send_minute: int,
    timezone: str = "UTC",
    from_time: Optional[datetime] = None
) -> datetime:
    """
    Compute the next run time for a schedule based on its cadence (PASS S2: Timezone-aware).
    
    ROBUST DST HANDLING:
    - During "spring forward" (e.g., 2:30 AM doesn't exist), we skip to the next valid time
    - During "fall back" (e.g., 1:30 AM exists twice), we use the first occurrence
    - ZoneInfo handles this automatically when we use fold=0 (default)
    
    Args:
        cadence: 'weekly' or 'monthly'
        weekly_dow: Day of week (0=Sun, 6=Sat) for weekly schedules
        monthly_dom: Day of month (1-28) for monthly schedules
        send_hour: Hour to send (0-23) in schedule's local timezone
        send_minute: Minute to send (0-59) in schedule's local timezone
        timezone: IANA timezone (e.g., 'America/Los_Angeles')
        from_time: Base time to compute from (defaults to now UTC)
    
    Returns:
        Next run datetime in UTC
    """
    if from_time is None:
        from_time = datetime.now(ZoneInfo("UTC"))
    
    # Convert from_time to schedule's local timezone
    try:
        tz = ZoneInfo(timezone)
    except Exception:
        logger.warning(f"Invalid timezone '{timezone}', falling back to UTC")
        tz = ZoneInfo("UTC")
    
    now_local = from_time.astimezone(tz)
    
    def safe_local_datetime(year: int, month: int, day: int, hour: int, minute: int) -> datetime:
        """
        Create a timezone-aware datetime, handling DST edge cases.
        
        During DST transitions:
        - "Spring forward": If time doesn't exist (e.g., 2:30 AM), move to next valid time
        - "Fall back": If time exists twice, use first occurrence (fold=0)
        """
        # Create a naive datetime first
        naive = datetime(year, month, day, hour, minute, 0, 0)
        
        # Make it timezone-aware with fold=0 (first occurrence during ambiguous times)
        try:
            local_dt = naive.replace(tzinfo=tz, fold=0)
            # Verify the time exists by round-tripping through UTC
            utc_dt = local_dt.astimezone(ZoneInfo("UTC"))
            roundtrip = utc_dt.astimezone(tz)
            
            # If the hour changed, the original time didn't exist (DST spring forward)
            if roundtrip.hour != hour:
                # Skip to the next valid hour (typically 3 AM after spring forward from 2 AM)
                logger.info(f"DST gap detected: {hour}:{minute:02d} doesn't exist on {year}-{month:02d}-{day:02d}, using {roundtrip.hour}:{roundtrip.minute:02d}")
                return roundtrip
            
            return local_dt
        except Exception as e:
            logger.warning(f"Error creating local datetime: {e}, using naive approach")
            return naive.replace(tzinfo=tz)
    
    if cadence == "weekly":
        if weekly_dow is None:
            raise ValueError("weekly_dow required for weekly cadence")
        
        # Find next occurrence of the target day of week
        # Python weekday: 0=Mon, 6=Sun; our weekly_dow: 0=Sun, 6=Sat
        # Convert our format to Python format
        target_weekday = (weekly_dow - 1) % 7  # Sun(0) -> 6, Mon(1) -> 0, etc.
        current_weekday = now_local.weekday()
        
        days_ahead = (target_weekday - current_weekday) % 7
        
        # Calculate target date
        target_date = now_local.date() + timedelta(days=days_ahead)
        next_local = safe_local_datetime(
            target_date.year, target_date.month, target_date.day,
            send_hour, send_minute
        )
        
        # If the time has already passed today, move to next week
        if next_local <= now_local:
            target_date = target_date + timedelta(days=7)
            next_local = safe_local_datetime(
                target_date.year, target_date.month, target_date.day,
                send_hour, send_minute
            )
        
        # Convert to UTC
        next_utc = next_local.astimezone(ZoneInfo("UTC"))
        return next_utc.replace(tzinfo=None)  # Return naive UTC datetime for DB storage
    
    elif cadence == "monthly":
        if monthly_dom is None:
            raise ValueError("monthly_dom required for monthly cadence")
        
        # Cap at 28 to avoid issues with different month lengths
        target_dom = min(monthly_dom, 28)
        
        # Start with this month
        year = now_local.year
        month = now_local.month
        
        # Create target datetime for this month
        next_local = safe_local_datetime(year, month, target_dom, send_hour, send_minute)
        
        # If that time has already passed this month, move to next month
        if next_local <= now_local:
            # Move to next month
            if month == 12:
                year += 1
                month = 1
            else:
                month += 1
            next_local = safe_local_datetime(year, month, target_dom, send_hour, send_minute)
        
        # Convert to UTC
        next_utc = next_local.astimezone(ZoneInfo("UTC"))
        return next_utc.replace(tzinfo=None)  # Return naive UTC datetime for DB storage
    
    else:
        raise ValueError(f"Unknown cadence: {cadence}")


# ── enqueue, split in two on purpose (D-072) ────────────────────────────────
#
# These were one function, `enqueue_report`, which wrote the generation row AND
# handed the task to Celery. The caller then inserted `schedule_runs`, advanced
# `next_run_at`, and committed — so the task was DISPATCHED AT STEP 1 AND THE
# WORK WAS RECORDED AT STEP 4.
#
# A rollback of steps 2-4 does not recall a Celery message. It is already in
# Redis, and the worker runs it and sends the email. What is left behind is a
# report in someone's inbox with no `schedule_runs` row, and a `next_run_at`
# that was never advanced — so the next tick, sixty seconds later, enqueues the
# same send again. Both halves of that are shapes this project has chased:
# the missing row is one of D-064's signatures, and the duplicate is what the
# #61 guard now refuses.
#
# Split so the ordering can be the fix, rather than another guard on top of it:
# record everything in ONE transaction, commit, and only then dispatch. The
# residual failure mode is inverted into the harmless one — rows committed at
# 'queued' with no task — which `sweep_stale_runs` already catches and reports
# as "never picked up". That is a sweep doing the job it was built for, rather
# than an email nobody can recall.


def create_report_generation(
    cur,
    schedule_id: str,
    account_id: str,
    report_type: str,
    city: Optional[str],
    zip_codes: Optional[list],
    lookback_days: int,
    filters: Optional[Dict[str, Any]] = None
) -> tuple[str, Dict[str, Any]]:
    """
    Write the `report_generations` row INSIDE THE CALLER'S TRANSACTION.

    Takes a cursor rather than opening its own connection, which is the whole
    point: this row must commit or roll back together with the `schedule_runs`
    row and the `next_run_at` advance. Previously it committed on a connection
    of its own and could survive a rollback of both.

    Dispatches nothing. See `dispatch_report`.
    """
    params = {
        "city": city,
        "zips": zip_codes,
        "lookback_days": lookback_days,
        "filters": filters or {},
        "schedule_id": schedule_id  # Link back to schedule for audit
    }

    # `set_config(..., is_local => true)` rather than `SET LOCAL app.… TO
    # '<id>'`: the old form interpolated account_id straight into SQL text.
    # The value comes from a uuid column so nothing could be smuggled through
    # it today, but a parameterised form costs nothing and does not depend on
    # that staying true. Same call the delivery guard uses.
    #
    # SCOPE CHANGED WITH THAT MOVE, AND IT MATTERS IF THIS IS REUSED. The old
    # call ran on a connection this function opened and closed, so the RLS
    # context died with it. This one runs on the CALLER'S transaction, so
    # `app.current_account_id` stays set for everything the caller does after
    # this returns — in the ticker that is the `schedule_runs` insert and the
    # `schedules` update, both on the same account, which is why it is fine
    # here. A caller that goes on to touch a DIFFERENT account in the same
    # transaction would be reading rows under this account's RLS context.
    # Set it again for that account, or use a separate transaction.
    cur.execute(
        "SELECT set_config('app.current_account_id', %s, true)",
        (str(account_id),),
    )

    cur.execute("""
        SELECT COALESCE(default_theme_id, 1), secondary_color
        FROM accounts
        WHERE id = %s::uuid
    """, (account_id,))
    acct = cur.fetchone()
    theme_id = acct[0] if acct else 1
    accent_color = acct[1] if acct else None

    cur.execute("""
        INSERT INTO report_generations
          (account_id, report_type, input_params, status, theme_id, accent_color)
        VALUES (%s::uuid, %s, %s::jsonb, 'queued', %s, %s)
        RETURNING id::text
    """, (account_id, report_type, safe_json_dumps(params), theme_id, accent_color))
    return cur.fetchone()[0], params


def dispatch_report(
    run_id: str,
    account_id: str,
    report_type: str,
    params: Dict[str, Any],
    schedule_id: str,
) -> Optional[str]:
    """
    Hand the task to Celery. **Call this only after the caller has committed.**

    Touches no database. That is enforced by nothing but this function's
    contents, so keep it that way: the moment it writes, the ordering this
    split exists to create is gone.

    Returns the Celery task id, or None if the dispatch failed. A failure is
    not raised, because by the time it can happen the run is already committed
    and the exception would only obscure that: the row sits at 'queued' with no
    task, which `sweep_stale_runs` marks failed with "never picked up" — the
    outcome that class of failure should have.
    """
    try:
        task = celery.send_task(
            "generate_report",
            args=[run_id, account_id, report_type, params],
            queue="celery"
        )
    except Exception as e:
        logger.error(
            "DISPATCH FAILED after commit for schedule %s, run_id=%s: %s — "
            "the run is recorded as 'queued' and the stale sweep will mark it "
            "failed; no report was generated and nothing was sent",
            schedule_id, run_id, e, exc_info=True,
        )
        return None

    logger.info(f"Enqueued report for schedule {schedule_id}, run_id={run_id}, task_id={task.id}")
    return task.id


# ── D-019, at the point where the send actually happens ─────────────────────
#
# The API gate (api/verification.py) stops an unverified account SETTING UP a
# send. It cannot stop one that is already set up: a schedule created before
# this shipped, or by an account that was verified and then had the flag
# cleared, is a row in `schedules` that the ticker will pick up sixty seconds
# later and mail to whoever it names. Enforcement that lives only in the API is
# enforcement of the request, not of the rule.
#
# So the check is repeated here, against the same column, in the same shape as
# the usage-limit pre-check immediately below it — skip, record, advance
# `next_run_at`, move on. Not DRY, and it cannot be: the API and the worker are
# separately deployed services that do not import each other, which is why
# `check_usage_limit` already exists in this package alongside
# `get_full_plan_usage` in the other one. The duplication is the deployment
# boundary, not carelessness. If the rule changes, both change — the two places
# name each other so that is findable.


# `email_log.status` for a scheduled send refused because the account is
# unverified. Must stay the same string as `BLOCKED_STATUS` in
# apps/api/src/api/verification.py — one vocabulary, two services. Named here
# rather than inlined in the SQL so both the value and the fact that it is
# shared are visible at the top of the change.
BLOCKED_STATUS = "blocked_unverified"


def account_can_send(cur, account_id: str) -> bool:
    """
    Does this account have any active user with a confirmed email address?

    Must stay identical in meaning to `sender_verification` in
    apps/api/src/api/verification.py — see the note above for why there are two.
    Raises on a database error rather than guessing; the caller's handler
    already treats an exception as "do not send this tick".
    """
    cur.execute(
        """
        SELECT COALESCE(bool_or(COALESCE(email_verified, FALSE)), FALSE)
        FROM users
        WHERE account_id = %s::uuid
          AND COALESCE(is_active, TRUE) = TRUE
        """,
        (account_id,),
    )
    row = cur.fetchone()
    return bool(row and row[0])


def record_unverified_skip(cur, account_id: str, schedule_id: str, recipients) -> None:
    """
    Leave the refusal in `email_log`, same as the API gate does.

    A skipped tick is otherwise indistinguishable from a tick that never came
    due: `next_run_at` advances either way and `schedule_runs` gets no row,
    because no run was created. Without this the owner's evidence that their
    schedule is not sending is a gap in a table — which is D-064's shape, and
    the reason #61's `duplicate_suppressed` exists.

    Non-fatal on its own failure. The skip stands regardless.
    """
    try:
        cur.execute(
            """
            SELECT set_config('app.current_account_id', %s, true)
            """,
            (str(account_id),),
        )
        cur.execute(
            """
            INSERT INTO email_log
                (account_id, schedule_id, report_id, provider,
                 to_emails, subject, response_code, error, status)
            VALUES
                (%s::uuid, %s::uuid, NULL, NULL,
                 %s, %s, NULL, %s, %s)
            """,
            (
                account_id,
                schedule_id,
                # The stored recipients are JSON-encoded typed references, not
                # addresses — resolving them would mean loading contacts for a
                # send that is not happening. Recorded as the strings they are,
                # which is what `schedules.recipients` holds.
                [str(r) for r in (recipients or [])] or None,
                "[refused] scheduled send",
                "no user on this account has confirmed their email address "
                "(users.email_verified is false for all of them)",
                BLOCKED_STATUS,
            ),
        )
    except Exception as e:
        logger.error(
            "Could not record the unverified skip for schedule %s: %s — "
            "the send was still skipped",
            schedule_id, e, exc_info=True,
        )


def process_due_schedules():
    """
    Find all due schedules and enqueue them.
    
    A schedule is due if:
    - active = true
    - next_run_at IS NULL (never computed) OR next_run_at <= NOW()
    
    RACE CONDITION FIX: Uses atomic UPDATE...RETURNING to claim schedules,
    preventing multiple ticker instances from processing the same schedule.
    Stale locks (>5 minutes) are automatically released.
    """
    try:
        with psycopg.connect(DATABASE_URL) as conn:
            with conn.cursor() as cur:
                # ATOMIC CLAIM: Update and return due schedules in one operation.
                # This prevents race conditions when multiple tickers are running.
                # Uses processing_locked_at to claim schedules atomically.
                # Stale locks (>5 min) are considered abandoned and reclaimed.
                cur.execute("""
                    WITH due AS (
                        SELECT id
                        FROM schedules
                        WHERE active = true
                          AND (next_run_at IS NULL OR next_run_at <= NOW())
                          AND (processing_locked_at IS NULL 
                               OR processing_locked_at < NOW() - INTERVAL '5 minutes')
                        ORDER BY COALESCE(next_run_at, '1970-01-01'::timestamptz) ASC
                        LIMIT 100
                        FOR UPDATE SKIP LOCKED
                    )
                    UPDATE schedules s
                    SET processing_locked_at = NOW()
                    FROM due
                    WHERE s.id = due.id
                    RETURNING s.id::text, s.account_id::text, s.name, s.report_type,
                              s.city, s.zip_codes, s.lookback_days,
                              s.cadence, s.weekly_dow, s.monthly_dom,
                              s.send_hour, s.send_minute, s.timezone,
                              s.recipients, s.include_attachment, s.filters
                """)
                
                due_schedules = cur.fetchall()
                
                if not due_schedules:
                    logger.debug("No due schedules found")
                    return
                
                logger.info(f"Found {len(due_schedules)} due schedule(s)")
                
                for row in due_schedules:
                    schedule_id = row[0]
                    account_id = row[1]
                    name = row[2]
                    report_type = row[3]
                    city = row[4]
                    zip_codes = row[5]  # PostgreSQL array
                    lookback_days = row[6]
                    cadence = row[7]
                    weekly_dow = row[8]
                    monthly_dom = row[9]
                    send_hour = row[10]
                    send_minute = row[11]
                    timezone = row[12]  # PASS S2
                    recipients = row[13]
                    include_attachment = row[14]
                    filters = row[15]  # NEW: Smart Preset filters (JSONB → dict or None)
                    
                    try:
                        # Pre-check: D-019. An unverified account does not send,
                        # including from a schedule that already exists. First,
                        # because it is the more fundamental refusal and the
                        # cheapest — one aggregate against `users`.
                        if not account_can_send(cur, account_id):
                            logger.warning(
                                "Skipping schedule %s — account %s has no user "
                                "with a confirmed email address; recorded in "
                                "email_log as blocked_unverified",
                                schedule_id, account_id,
                            )
                            record_unverified_skip(
                                cur, account_id, schedule_id, recipients
                            )
                            next_run_at = compute_next_run(
                                cadence, weekly_dow, monthly_dom,
                                send_hour, send_minute, timezone
                            )
                            cur.execute("""
                                UPDATE schedules
                                SET next_run_at = %s, processing_locked_at = NULL
                                WHERE id = %s::uuid
                            """, (next_run_at, schedule_id))
                            conn.commit()
                            continue

                        # Pre-check: skip if account is at market report limit (DB-backed, per-plan)
                        limit_result = check_usage_limit(account_id, product="market_reports")
                        if not limit_result["can_proceed"]:
                            logger.info(
                                f"Skipping schedule {schedule_id} — account {account_id} "
                                f"at market report limit "
                                f"({limit_result.get('used', '?')}/{limit_result.get('limit', '?')})"
                            )
                            # Advance next_run_at so we don't re-check every tick
                            next_run_at = compute_next_run(
                                cadence, weekly_dow, monthly_dom,
                                send_hour, send_minute, timezone
                            )
                            cur.execute("""
                                UPDATE schedules
                                SET next_run_at = %s, processing_locked_at = NULL
                                WHERE id = %s::uuid
                            """, (next_run_at, schedule_id))
                            conn.commit()
                            continue

                        # Compute next run time (PASS S2: timezone-aware)
                        next_run_at = compute_next_run(
                            cadence, weekly_dow, monthly_dom,
                            send_hour, send_minute, timezone
                        )
                        
                        # RECORD EVERYTHING FIRST, DISPATCH AFTER THE COMMIT.
                        # The order of these four steps is the fix for D-072
                        # and is the only thing keeping a rolled-back tick from
                        # leaving a report in someone's inbox. Do not move the
                        # dispatch back above the commit.

                        # 1. generation row — now on THIS cursor, so it rolls
                        #    back with everything else rather than surviving on
                        #    a connection of its own
                        report_gen_id, task_params = create_report_generation(
                            cur,
                            schedule_id, account_id, report_type,
                            city, zip_codes, lookback_days,
                            filters=filters
                        )

                        # 2. schedule_runs audit record linked to the generation
                        cur.execute("""
                            INSERT INTO schedule_runs (schedule_id, report_run_id, status, created_at)
                            VALUES (%s::uuid, %s::uuid, 'queued', NOW())
                            RETURNING id::text
                        """, (schedule_id, report_gen_id))
                        
                        schedule_run_id = cur.fetchone()[0]
                        
                        # 3. last_run_at, next_run_at, and clear the lock
                        cur.execute("""
                            UPDATE schedules
                            SET last_run_at = NOW(),
                                next_run_at = %s,
                                processing_locked_at = NULL
                            WHERE id = %s::uuid
                        """, (next_run_at, schedule_id))
                        
                        # 4. commit — everything above is now durable, and any
                        #    failure up to this point has left no task behind
                        conn.commit()

                        # 5. and only now, the dispatch
                        task_id = dispatch_report(
                            report_gen_id, account_id, report_type,
                            task_params, schedule_id,
                        )
                        
                        logger.info(
                            f"Processed schedule '{name}' (ID: {schedule_id}): "
                            f"schedule_run_id={schedule_run_id}, report_gen_id={report_gen_id}, "
                            f"task_id={task_id}, next_run_at={next_run_at.isoformat()}"
                        )
                    
                    except Exception as e:
                        logger.error(f"Failed to process schedule {schedule_id}: {e}", exc_info=True)
                        # Clear the lock on failure so another ticker can retry
                        try:
                            cur.execute("""
                                UPDATE schedules 
                                SET processing_locked_at = NULL 
                                WHERE id = %s::uuid
                            """, (schedule_id,))
                            conn.commit()
                        except Exception:
                            pass
                        conn.rollback()
                        continue
    
    except Exception as e:
        logger.error(f"Failed to query due schedules: {e}", exc_info=True)


# Two windows, because the two failure modes have different safe margins and a
# single number is wrong for one of them.
#
# STARTED BUT NEVER FINISHED — the task is running, or was. Celery's
# task_time_limit is 300s, so a task CANNOT still be alive past that: the hard
# kill guarantees it. 6 minutes clears the ceiling with margin and is race-free
# by construction. Production timings corroborate the headroom: over n=1067
# completed runs, p95 32s, p99 41s, max 80s — nothing is near the limit, which
# is also what rules out "these were timeouts".
STALE_STARTED_MINUTES = int(os.getenv("STALE_STARTED_MINUTES", "6"))

# ENQUEUED AND NEVER STARTED — no task is running, so there is nothing to race;
# the risk runs the other way, marking work that is legitimately still queued.
# That is not governed by render duration but by QUEUE DEPTH. The ticker
# enqueues every due schedule in one pass — 26 in a single pass on 2026-04-12 —
# and the worker runs at Celery's default concurrency (no --concurrency flag is
# set anywhere), so a burst drains roughly serially: 26 x ~41s is about 18
# minutes before the last task even begins.
#
# A window derived from p99 render time alone would be ~2 minutes, and would
# mark most of a burst failed while the worker was working through it normally
# — turning a backlog into fabricated failures, in exactly the scenario this
# sweep exists for. 30 minutes covers a full burst drain with margin.
STALE_QUEUED_MINUTES = int(os.getenv("STALE_QUEUED_MINUTES", "30"))


def sweep_stale_runs():
    """
    Mark schedule runs that were enqueued and never finished as failed.

    WHY THIS EXISTS
    ---------------
    58 runs sat at `status='queued'` in production across ten months, in
    bursts, with no error, no notification and no timeout — the system was told
    to send those reports and simply did not. Nothing ever noticed, because
    every status write lives on a success path inside the worker: if the task
    is never consumed, or is killed mid-flight, no code runs to record
    anything. (An earlier version of this comment said Celery acks on receipt
    so a restart discards prefetched work. Measured, that is wrong: prefetched
    messages are unacknowledged either way and come back. What the default
    loses is the task that was RUNNING — which is what `task_acks_late`, now
    enabled in app.py, recovers. The sweep is still needed, because D-068's
    child-loss case is not recovered by it.)

    A sweep is the only thing that can catch that class, because by definition
    the process that would have reported it is gone. See D-062.

    Deliberately conservative:
      - two windows, and the started one is measured from started_at rather
        than created_at, so a task that waited out a backlog and then ran
        normally is never condemned for the wait;
      - writes a terminal status and an explicit reason rather than deleting,
        so the history stays auditable;
      - distinguishes 'never picked up' from 'died while running' using
        started_at, which is now actually written (tasks.py, persist_status).
    """
    try:
        with psycopg.connect(DATABASE_URL) as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    UPDATE schedule_runs
                    SET status = 'failed',
                        error = CASE
                            WHEN started_at IS NULL
                                THEN 'never picked up: enqueued but no worker started it within '
                                     || %s || ' minutes'
                            ELSE 'died while running: started but never reached a terminal status'
                        END,
                        finished_at = NOW()
                    WHERE status IN ('queued', 'processing')
                      AND (
                            -- never started: measured from enqueue, and wide
                            -- enough to let a burst drain.
                            (started_at IS NULL
                             AND created_at < NOW() - (%s || ' minutes')::interval)
                         OR
                            -- started: measured from the START, not from
                            -- enqueue. A task that waited 20 minutes in a
                            -- backlog and then ran for 40s is healthy, and
                            -- measuring from created_at would condemn it.
                            (started_at IS NOT NULL
                             AND started_at < NOW() - (%s || ' minutes')::interval)
                      )
                    RETURNING id::text, schedule_id::text, (started_at IS NULL)
                """, (STALE_QUEUED_MINUTES, STALE_QUEUED_MINUTES, STALE_STARTED_MINUTES))
                swept = cur.fetchall()
            conn.commit()

        if swept:
            never_started = sum(1 for row in swept if row[2])
            logger.error(
                "Stale run sweep: marked %d run(s) failed (%d never picked up, "
                "%d died while running). Schedules affected: %s",
                len(swept), never_started, len(swept) - never_started,
                sorted({row[1] for row in swept}),
            )
    except Exception as e:
        logger.error(f"Stale run sweep failed: {e}", exc_info=True)


def run_forever():
    """
    Main ticker loop: process due schedules every TICK_INTERVAL seconds.
    Also pings the API periodically to prevent cold starts.
    """
    logger.info(f"Schedules ticker started (interval: {TICK_INTERVAL}s)")
    logger.info(f"Database: {DATABASE_URL.split('@')[-1]}")  # Log host without credentials
    logger.info(f"API keep-alive target: {API_BASE_URL} (every {KEEP_ALIVE_INTERVAL}s)")
    
    while True:
        try:
            # Keep API warm to prevent Render cold starts
            keep_api_warm()
            
            logger.debug("Tick: Checking for due schedules...")
            process_due_schedules()

            # Runs that were enqueued and never finished. Nothing inside the
            # worker can report these — see sweep_stale_runs.
            sweep_stale_runs()
        except Exception as e:
            logger.error(f"Ticker error: {e}", exc_info=True)
        
        time.sleep(TICK_INTERVAL)


if __name__ == "__main__":
    run_forever()


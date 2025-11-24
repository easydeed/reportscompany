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
from datetime import datetime, timedelta, date
from typing import Optional, Dict, Any
from zoneinfo import ZoneInfo
import psycopg
import ssl
from celery import Celery

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
    
    if cadence == "weekly":
        if weekly_dow is None:
            raise ValueError("weekly_dow required for weekly cadence")
        
        # Start with today at the desired local time
        next_local = now_local.replace(hour=send_hour, minute=send_minute, second=0, microsecond=0)
        
        # Find next occurrence of the target day of week
        # Python weekday: 0=Mon, 6=Sun; our weekly_dow: 0=Sun, 6=Sat
        # Convert our format to Python format
        target_weekday = (weekly_dow - 1) % 7  # Sun(0) -> 6, Mon(1) -> 0, etc.
        current_weekday = now_local.weekday()
        
        days_ahead = (target_weekday - current_weekday) % 7
        
        # If the day is today but the time has passed, move to next week
        if days_ahead == 0 and next_local <= now_local:
            days_ahead = 7
        
        next_local = next_local + timedelta(days=days_ahead)
        
        # Convert to UTC
        next_utc = next_local.astimezone(ZoneInfo("UTC"))
        return next_utc.replace(tzinfo=None)  # Return naive UTC datetime for DB storage
    
    elif cadence == "monthly":
        if monthly_dom is None:
            raise ValueError("monthly_dom required for monthly cadence")
        
        # Cap at 28 to avoid issues with different month lengths
        target_dom = min(monthly_dom, 28)
        
        # Start with this month at the target day and time in local timezone
        try:
            next_local = now_local.replace(day=target_dom, hour=send_hour, minute=send_minute, second=0, microsecond=0)
        except ValueError:
            # If target day doesn't exist in current month (shouldn't happen with cap at 28)
            # Move to next month's first day, then set target day
            next_month = now_local.replace(day=1) + timedelta(days=32)
            next_local = next_month.replace(day=target_dom, hour=send_hour, minute=send_minute, second=0, microsecond=0)
        
        # If that time has already passed this month, move to next month
        if next_local <= now_local:
            # Move to next month
            if next_local.month == 12:
                next_local = next_local.replace(year=next_local.year + 1, month=1)
            else:
                next_local = next_local.replace(month=next_local.month + 1)
        
        # Convert to UTC
        next_utc = next_local.astimezone(ZoneInfo("UTC"))
        return next_utc.replace(tzinfo=None)  # Return naive UTC datetime for DB storage
    
    else:
        raise ValueError(f"Unknown cadence: {cadence}")


def enqueue_report(
    schedule_id: str,
    account_id: str,
    report_type: str,
    city: Optional[str],
    zip_codes: Optional[list],
    lookback_days: int,
    filters: Optional[Dict[str, Any]] = None
) -> tuple[str, str]:
    """
    Enqueue a report generation task to Celery.
    
    Returns:
        Tuple of (report_generation_id, celery_task_id)
    """
    # Build params dict matching the format expected by generate_report task
    params = {
        "city": city,
        "zips": zip_codes,
        "lookback_days": lookback_days,
        "filters": filters or {},
        "schedule_id": schedule_id  # Link back to schedule for audit
    }
    
    # Create report_generation record first (worker expects run_id)
    with psycopg.connect(DATABASE_URL) as conn:
        with conn.cursor() as cur:
            cur.execute(f"SET LOCAL app.current_account_id TO '{account_id}'")
            cur.execute("""
                INSERT INTO report_generations (account_id, report_type, input_params, status)
                VALUES (%s::uuid, %s, %s::jsonb, 'queued')
                RETURNING id::text
            """, (account_id, report_type, safe_json_dumps(params)))
            run_id = cur.fetchone()[0]
        conn.commit()
    
    # Send task to Celery with all 4 required arguments
    task = celery.send_task(
        "generate_report",
        args=[run_id, account_id, report_type, params],
        queue="celery"
    )
    
    logger.info(f"Enqueued report for schedule {schedule_id}, run_id={run_id}, task_id={task.id}")
    return run_id, task.id


def process_due_schedules():
    """
    Find all due schedules and enqueue them.
    
    A schedule is due if:
    - active = true
    - next_run_at IS NULL (never computed) OR next_run_at <= NOW()
    """
    try:
        with psycopg.connect(DATABASE_URL) as conn:
            with conn.cursor() as cur:
                # Find due schedules (PASS S2: include timezone)
                cur.execute("""
                    SELECT id::text, account_id::text, name, report_type,
                           city, zip_codes, lookback_days,
                           cadence, weekly_dow, monthly_dom,
                           send_hour, send_minute, timezone,
                           recipients, include_attachment
                    FROM schedules
                    WHERE active = true
                      AND (next_run_at IS NULL OR next_run_at <= NOW())
                    ORDER BY COALESCE(next_run_at, '1970-01-01'::timestamptz) ASC
                    LIMIT 100
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
                    
                    try:
                        # Compute next run time (PASS S2: timezone-aware)
                        next_run_at = compute_next_run(
                            cadence, weekly_dow, monthly_dom,
                            send_hour, send_minute, timezone
                        )
                        
                        # Enqueue report generation (creates report_generations record + Celery task)
                        report_gen_id, task_id = enqueue_report(
                            schedule_id, account_id, report_type,
                            city, zip_codes, lookback_days
                        )
                        
                        # Create schedule_runs audit record linked to report_generation
                        cur.execute("""
                            INSERT INTO schedule_runs (schedule_id, report_run_id, status, created_at)
                            VALUES (%s::uuid, %s::uuid, 'queued', NOW())
                            RETURNING id::text
                        """, (schedule_id, report_gen_id))
                        
                        schedule_run_id = cur.fetchone()[0]
                        
                        # Update schedule with last_run_at and next_run_at
                        cur.execute("""
                            UPDATE schedules
                            SET last_run_at = NOW(),
                                next_run_at = %s
                            WHERE id = %s::uuid
                        """, (next_run_at, schedule_id))
                        
                        conn.commit()
                        
                        logger.info(
                            f"Processed schedule '{name}' (ID: {schedule_id}): "
                            f"schedule_run_id={schedule_run_id}, report_gen_id={report_gen_id}, "
                            f"task_id={task_id}, next_run_at={next_run_at.isoformat()}"
                        )
                    
                    except Exception as e:
                        logger.error(f"Failed to process schedule {schedule_id}: {e}", exc_info=True)
                        conn.rollback()
                        continue
    
    except Exception as e:
        logger.error(f"Failed to query due schedules: {e}", exc_info=True)


def run_forever():
    """
    Main ticker loop: process due schedules every TICK_INTERVAL seconds.
    """
    logger.info(f"Schedules ticker started (interval: {TICK_INTERVAL}s)")
    logger.info(f"Database: {DATABASE_URL.split('@')[-1]}")  # Log host without credentials
    
    while True:
        try:
            logger.debug("Tick: Checking for due schedules...")
            process_due_schedules()
        except Exception as e:
            logger.error(f"Ticker error: {e}", exc_info=True)
        
        time.sleep(TICK_INTERVAL)


if __name__ == "__main__":
    run_forever()


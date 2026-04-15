"""
Schedule utility functions shared between the schedules route and admin route.

Extracted here to avoid circular imports and ensure both callers use
identical next_run_at computation logic.
"""

from datetime import datetime, timedelta
from typing import Optional
import calendar as _calendar
from zoneinfo import ZoneInfo


def compute_next_run(
    cadence: str,
    weekly_dow: Optional[int],
    monthly_dom: Optional[int],
    send_hour: int,
    send_minute: int,
    timezone: str = "UTC",
) -> datetime:
    """
    Compute the first upcoming run time for a new or updated schedule.
    Returns a UTC-aware datetime.

    Mirrors the worker's compute_next_run logic so schedules always get a valid
    next_run_at on creation/update and never fire immediately on the next tick.

    Args:
        cadence:     "weekly" | "monthly" | other (defaults to +1 hour)
        weekly_dow:  0=Sun … 6=Sat (required for weekly cadence)
        monthly_dom: 1–28 day-of-month (required for monthly cadence)
        send_hour:   0–23 in local timezone
        send_minute: 0–59 in local timezone
        timezone:    IANA timezone name (e.g. "America/Los_Angeles")
    """
    try:
        tz = ZoneInfo(timezone)
    except Exception:
        tz = ZoneInfo("UTC")

    now_utc = datetime.now(ZoneInfo("UTC"))
    now_local = now_utc.astimezone(tz)

    if cadence == "weekly":
        if weekly_dow is None:
            weekly_dow = 0
        # Our DOW: 0=Sun, 6=Sat  →  Python weekday: 0=Mon, 6=Sun
        target_weekday = (weekly_dow - 1) % 7
        current_weekday = now_local.weekday()
        days_ahead = target_weekday - current_weekday
        if days_ahead < 0:
            days_ahead += 7
        candidate = now_local.replace(
            hour=send_hour, minute=send_minute, second=0, microsecond=0
        ) + timedelta(days=days_ahead)
        # Same day but time already passed → push one week
        if days_ahead == 0 and candidate <= now_local:
            candidate += timedelta(weeks=1)

    elif cadence == "monthly":
        dom = monthly_dom if monthly_dom else 1
        try:
            candidate = now_local.replace(
                day=dom, hour=send_hour, minute=send_minute, second=0, microsecond=0
            )
        except ValueError:
            last_day = _calendar.monthrange(now_local.year, now_local.month)[1]
            candidate = now_local.replace(
                day=last_day, hour=send_hour, minute=send_minute, second=0, microsecond=0
            )
        if candidate <= now_local:
            if now_local.month == 12:
                next_month = now_local.replace(year=now_local.year + 1, month=1)
            else:
                next_month = now_local.replace(month=now_local.month + 1)
            try:
                candidate = next_month.replace(
                    day=dom, hour=send_hour, minute=send_minute, second=0, microsecond=0
                )
            except ValueError:
                last_day = _calendar.monthrange(next_month.year, next_month.month)[1]
                candidate = next_month.replace(
                    day=last_day, hour=send_hour, minute=send_minute, second=0, microsecond=0
                )
    else:
        # Unknown cadence — schedule one hour from now as a safe default
        candidate = now_local + timedelta(hours=1)

    return candidate.astimezone(ZoneInfo("UTC"))

"""Timestamps as the browser must read them."""
from datetime import datetime, timezone
from typing import Optional


def utc_iso(ts: Optional[datetime]) -> Optional[str]:
    """`report_generations.generated_at` is `timestamp without time zone`,
    written by NOW() on a UTC database. Sent bare, a browser reads it as its
    own local time — seven or eight hours late in California, so a report
    made last night reads "Today" (D-318, D-319). Say it is UTC. A value that
    already carries a zone is sent as it is."""
    if ts is None:
        return None
    return (ts.replace(tzinfo=timezone.utc) if ts.tzinfo is None else ts).isoformat()

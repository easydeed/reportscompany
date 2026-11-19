"""LR-027 heartbeats (design section 3). Imported by the ticker; no Celery app here.

Production runs no Celery Beat, so the standalone ticker is the producer:
  * after each loop that completes, it writes `ops:heartbeat:ticker`;
  * it publishes the `ops_heartbeat` work item, and whichever worker consumes
    it writes `ops:heartbeat:worker`. A fresh worker key proves the queue is
    being consumed.

What the ticker key proves: the loop is running. `process_due_schedules`
catches its own database errors, so a fresh ticker key does not mean the
database is reachable. That is `/ready`'s database check, and the monitor's
`schedule_overdue` signal (LR-027 slice 2).

Both keys hold Redis server time (TIME), the same clock `/ready` reads, so
host clock skew between services never shows up as staleness. The API carries
the same key names (apps/api/src/api/routes/ready.py); a test holds them equal.
Every failure here is logged and swallowed: a heartbeat must never stop the
ticker or fail a worker for real work.
"""
import logging
import os
from typing import Optional

logger = logging.getLogger(__name__)

TICKER_KEY = "ops:heartbeat:ticker"
WORKER_KEY = "ops:heartbeat:worker"
CELERY_QUEUE = "celery"
TASK_NAME = "ops_heartbeat"

TICKER_TTL_S = 600
# Longer than the 30-minute backlog horizon, so /ready can still tell a long
# backlog (queue non-empty, heartbeat 5-30 minutes old) from a missing key.
WORKER_TTL_S = 3600
# A heartbeat that waited longer than this is dropped by the worker, not run late.
HEARTBEAT_EXPIRES_S = 120
REDIS_TIMEOUT_S = 1.0

_client = None


def _redis():
    global _client
    if _client is None:
        from .redis_utils import create_redis_connection
        _client = create_redis_connection(
            os.getenv("REDIS_URL", "redis://localhost:6379/0"),
            socket_connect_timeout=REDIS_TIMEOUT_S,
            socket_timeout=REDIS_TIMEOUT_S,
        )
    return _client


def beat(key: str, ttl_s: int, client=None) -> Optional[int]:
    """Write Redis server time to `key`; return it, or None when Redis failed."""
    try:
        r = client or _redis()
        now = int(r.time()[0])
        r.set(key, now, ex=ttl_s)
        return now
    except Exception as exc:  # noqa: BLE001
        logger.warning("ops heartbeat %s not written: %s", key, type(exc).__name__)
        return None


def after_tick(celery_app, client=None) -> None:
    """Called by the ticker after a loop that completed."""
    beat(TICKER_KEY, TICKER_TTL_S, client)
    try:
        celery_app.send_task(TASK_NAME, queue=CELERY_QUEUE, expires=HEARTBEAT_EXPIRES_S)
    except Exception as exc:  # noqa: BLE001
        logger.warning("ops heartbeat work item not published: %s", type(exc).__name__)

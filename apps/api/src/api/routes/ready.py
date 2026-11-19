"""GET /ready: can this deployment do work right now? (LR-027, design section 3.)

`/health` stays the liveness check and Render's health-check path. If Render
restarted on readiness, a database or Redis outage would become a restart loop
that fixes nothing. `/ready` is for humans and the external pinger.

Every wait is bounded, so the worst case is about three seconds:
  * database: pool acquisition 1 s, then `statement_timeout` 1 s and
    `lock_timeout` 250 ms per statement;
  * Redis: a dedicated client with 0.5 s connect and read timeouts. The shared
    client in `cache.py` allows 2 s for each.
Evaluations are single-flight per process, on their own thread, and cached for
10 s, so the pinger, or anyone else, cannot turn this into load. A caller waits
at most EVAL_BUDGET_S (4 s); an evaluation that has not finished by then is a
503, and an expired result is never served.

The schema check is `schema_guard.check`, the function that gates startup:
"the required migration is recorded". A database AHEAD of this binary (a
newer compatible migration, or this binary rolled back) is therefore ready.

The endpoint is public, so the body says only which part is not ready. It never
contains hostnames, DSNs, exception text, IDs or queue contents.
"""
import logging
import threading
import time
from typing import Optional

import redis as _redis
from fastapi import APIRouter
from fastapi.responses import JSONResponse

from ..schema_guard import REQUIRED_MIGRATION, SchemaBehind, check as schema_check
from ..settings import settings

logger = logging.getLogger(__name__)
router = APIRouter()

# Written by the ticker and by the worker's `ops_heartbeat` task, in Redis
# server time (TIME). The worker module apps/worker/src/worker/ops_heartbeat.py
# carries the same names; tests/test_ops_heartbeat_contract.py holds them equal.
TICKER_KEY = "ops:heartbeat:ticker"
WORKER_KEY = "ops:heartbeat:worker"
CELERY_QUEUE = "celery"

TICKER_STALE_S = 180          # three missed ticks
WORKER_STALE_S = 300          # with nothing queued: the worker is down
WORKER_BACKLOG_LIMIT_S = 1800  # STALE_QUEUED_MINUTES: past this, a backlog is an outage

POOL_TIMEOUT_S = 1.0
REDIS_TIMEOUT_S = 0.5
CACHE_S = 10.0

_redis_client: Optional[_redis.Redis] = None
_cached: Optional[tuple[float, int, dict]] = None  # (monotonic time, status, body)


def _readiness_redis() -> _redis.Redis:
    global _redis_client
    if _redis_client is None:
        _redis_client = _redis.from_url(
            settings.REDIS_URL,
            decode_responses=True,
            socket_connect_timeout=REDIS_TIMEOUT_S,
            socket_timeout=REDIS_TIMEOUT_S,
            retry_on_timeout=False,
        )
    return _redis_client


def _check_database() -> dict:
    from psycopg.pq import TransactionStatus
    from psycopg_pool import PoolTimeout
    from ..db import get_pool

    try:
        with get_pool().connection(timeout=POOL_TIMEOUT_S) as conn:
            # SET LOCAL only holds inside a transaction, and PostgreSQL silently
            # ignores it outside one. The pool hands back connections in
            # whatever autocommit state their last borrower left
            # (db_conn_autocommit sets True), so open the transaction
            # explicitly: valid in either state, and always rolled back, so no
            # setting reaches the next borrower (Codex review of #322).
            if conn.info.transaction_status != TransactionStatus.IDLE:
                conn.rollback()
            with conn.transaction(force_rollback=True):
                with conn.cursor() as cur:
                    cur.execute("SET LOCAL statement_timeout = '1000ms'")
                    cur.execute("SET LOCAL lock_timeout = '250ms'")
                    schema_check(cur)
        return {"status": "ok"}
    except SchemaBehind:
        return {"status": "behind"}
    except PoolTimeout:
        # No connection within 1 s: requests would fail the same way.
        return {"status": "failing"}
    except Exception as exc:  # noqa: BLE001 - any failure is "not ready"
        logger.warning("ready: database check failed: %s", type(exc).__name__)
        return {"status": "failing"}


def worker_state(age_s: Optional[int], queued: int) -> str:
    """Design section 3: tell a dead worker from a backlog."""
    if age_s is not None and age_s <= WORKER_STALE_S:
        return "ok"
    if queued == 0:
        return "stale"        # nothing waiting, yet nothing ran
    if age_s is not None and age_s <= WORKER_BACKLOG_LIMIT_S:
        return "backlog"      # reports are delayed, not stopped
    return "stale"


def _check_redis_and_heartbeats() -> dict:
    try:
        r = _readiness_redis()
        r.ping()
        pipe = r.pipeline(transaction=False)
        pipe.time()
        pipe.mget(TICKER_KEY, WORKER_KEY)
        pipe.llen(CELERY_QUEUE)
        (now, _), (ticker_at, worker_at), queued = pipe.execute()
    except Exception as exc:  # noqa: BLE001
        logger.warning("ready: redis check failed: %s", type(exc).__name__)
        unknown = {"status": "stale", "age_s": None}
        return {"redis": {"status": "failing"}, "ticker": dict(unknown), "worker": dict(unknown)}

    def age(value) -> Optional[int]:
        try:
            return max(0, int(now) - int(value))
        except (TypeError, ValueError):
            return None

    ticker_age, worker_age = age(ticker_at), age(worker_at)
    ticker_ok = ticker_age is not None and ticker_age <= TICKER_STALE_S
    return {
        "redis": {"status": "ok"},
        "ticker": {"status": "ok" if ticker_ok else "stale", "age_s": ticker_age},
        "worker": {"status": worker_state(worker_age, int(queued or 0)), "age_s": worker_age},
    }


def evaluate() -> tuple[int, dict]:
    checks = {"database": _check_database(), **_check_redis_and_heartbeats()}
    # `backlog` is reported but not critical: reports are delayed, not stopped.
    ready = all(c["status"] in ("ok", "backlog") for c in checks.values())
    return (200 if ready else 503), {"ready": ready, "schema": REQUIRED_MIGRATION, "checks": checks}


def _respond(status: int, body: dict) -> JSONResponse:
    return JSONResponse(status_code=status, content=body, headers={"Cache-Control": "no-store"})


# A caller waits at most this long for an evaluation. The checks' own bounds
# make ~3 s the expected worst case; this is the hard ceiling the pinger sees.
EVAL_BUDGET_S = 4.0
_state_lock = threading.Lock()
_inflight: Optional[threading.Thread] = None


def _fresh(cached) -> bool:
    return bool(cached) and time.monotonic() - cached[0] < CACHE_S


def _evaluate_and_store() -> None:
    global _cached, _inflight
    try:
        status, body = evaluate()
        with _state_lock:
            _cached = (time.monotonic(), status, body)
    except Exception as exc:  # noqa: BLE001
        logger.warning("ready: evaluation failed: %s", type(exc).__name__)
    finally:
        with _state_lock:
            _inflight = None


@router.get("/ready")
def ready():
    """Fresh result, or 503. Never an expired one (Codex review of #322).

    One evaluation at a time, on its own thread; every caller, the first
    included, waits at most EVAL_BUDGET_S for it. A result is served only
    while it is younger than CACHE_S. If the evaluation has not finished
    inside the budget, the answer is 503 "evaluation incomplete": a stalled
    dependency must show up at the pinger, not hide behind the last green.
    """
    global _inflight
    with _state_lock:
        cached = _cached
        if _fresh(cached):
            return _respond(cached[1], cached[2])
        if _inflight is None:
            _inflight = threading.Thread(target=_evaluate_and_store, name="ready-evaluate", daemon=True)
            _inflight.start()
        thread = _inflight
    thread.join(EVAL_BUDGET_S)
    with _state_lock:
        cached = _cached
    if _fresh(cached):
        return _respond(cached[1], cached[2])
    return _respond(503, {"ready": False, "schema": REQUIRED_MIGRATION, "checks": {},
                          "reason": "evaluation_incomplete"})

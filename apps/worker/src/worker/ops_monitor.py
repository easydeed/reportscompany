"""LR-027 monitor (design #317 rev 3, sections 3-5, 8). Observe-only by default.

Every 5 minutes, on its own thread in the ticker process, the monitor reads
each signal (ops_signals.SIGNALS plus the heartbeats) and keeps one incident
per tripped signal in ops_alerts, with its complete membership in
ops_alert_members. It writes a count-only log line for what it WOULD send:

    OPS_ALERT mode=observe key=<key> event=<open|new_members|grew|resolved> ...

With OPS_ALERTS_ENABLED unset or 0 (the default, until Jerry approves the
thresholds) that is all it does: it sends nothing and queues nothing. With 1,
each announced event is also handed to `ops_notify`, which queues one row per
configured channel in the same transaction and delivers it after the signals
(claim before the call, never resend an uncertain outcome). This module itself
never calls a provider.

Why on the ticker and not a Celery task: production runs no Beat, and a task
in the render queue would wait behind a burst and could never report a dead
worker. Singleton: a Redis lease (SET NX EX 290) per 5-minute run, so any
number of tickers run it at most once per window. Bounded: 5 s per statement,
5 s connect, a 90 s budget per run, and a new run never starts while the
previous thread is alive. Isolated: the dispatch loop never waits on it, and
nothing it raises reaches the loop.

Without the 0069 tables (an emergency start under SCHEMA_BEHIND_ACKNOWLEDGED)
it logs once per run and does nothing.
"""
import logging
import threading
import time
import uuid
from typing import Optional

from . import ops_heartbeat
from . import ops_notify
from . import ops_signals
from .ops_signals import MEMBER_LIMIT, Reading

logger = logging.getLogger(__name__)

INTERVAL_S = 300
LEASE_KEY = "ops:monitor:lease"
LEASE_S = 290
BUDGET_S = 90.0
STATEMENT_TIMEOUT_MS = 5000
FLAP_WINDOW_MIN = 30
SAMPLE = 5

# Heartbeat thresholds. The API's /ready uses the same numbers
# (apps/api/src/api/routes/ready.py); a test holds them equal.
TICKER_STALE_S = 180
WORKER_STALE_S = 300
WORKER_BACKLOG_LIMIT_S = 1800


def worker_state(age_s: Optional[int], queued: int) -> str:
    if age_s is not None and age_s <= WORKER_STALE_S:
        return "ok"
    if queued == 0:
        return "stale"
    if age_s is not None and age_s <= WORKER_BACKLOG_LIMIT_S:
        return "backlog"
    return "stale"


def heartbeat_readings(client) -> dict:
    """ticker_stale / worker_stale / worker_backlog from the heartbeat keys."""
    pipe = client.pipeline(transaction=False)
    pipe.time()
    pipe.mget(ops_heartbeat.TICKER_KEY, ops_heartbeat.WORKER_KEY)
    pipe.llen(ops_heartbeat.CELERY_QUEUE)
    (now, _), (ticker_at, worker_at), queued = pipe.execute()

    def age(v):
        try:
            return max(0, int(now) - int(v))
        except (TypeError, ValueError):
            return None

    ticker_age, worker_age = age(ticker_at), age(worker_at)
    state = worker_state(worker_age, int(queued or 0))
    ticker_stale = ticker_age is None or ticker_age > TICKER_STALE_S

    def reading(tripped, ident, **value):
        return Reading(tripped=tripped, identities=[ident] if tripped else [],
                       count=1 if tripped else 0, value=value)

    return {
        "ticker_stale": reading(ticker_stale, "heartbeat:ticker", age_s=ticker_age),
        "worker_stale": reading(state == "stale", "heartbeat:worker", age_s=worker_age, queued=int(queued or 0)),
        "worker_backlog": reading(state == "backlog", "heartbeat:worker", age_s=worker_age, queued=int(queued or 0)),
    }


HEARTBEAT_SIGNALS = {
    "ticker_stale": (True, "Scheduled sends have stopped."),
    "worker_stale": (True, "Reports are not being processed."),
    "worker_backlog": (False, "Reports are delayed behind a backlog."),
}

# LR-027 slice 4: an admin's test alert (POST /v1/admin/ops/test-alert) is a
# short-lived Redis key. The run that consumes it opens `ops_test_alert`
# through the real incident and delivery path; the next run, finding no
# request, resolves it. The API names the same key (contract test).
#
# One test lifecycle at a time (Codex #329 P2): a request that arrives while a
# test incident is still open is NOT consumed by that run. Consuming it would
# add a member to the open incident (an email-only update, no opening text)
# and hold back the first test's recovery. It waits in Redis instead; the run
# resolves the open test, and the next run opens a fresh incident for it.
TEST_ALERT_KEY = "ops:test_alert:requested"
TEST_SIGNALS = {
    "ops_test_alert": (True, "Test alert requested by an admin. No action is needed."),
}


def test_alert_read(client):
    """The monitor's read for `ops_test_alert`: consume a request only when no test is open."""
    def read(cur) -> Reading:
        cur.execute("SELECT 1 FROM ops_alerts WHERE key = 'ops_test_alert' AND resolved_at IS NULL LIMIT 1")
        if cur.fetchone() is not None:
            return Reading(tripped=False, identities=[], count=0, value={})
        try:
            return test_alert_reading(client)
        except Exception as exc:  # noqa: BLE001 - Redis unreachable: no reading, nothing recorded
            logger.warning("OPS_MONITOR test-alert check skipped: %s", type(exc).__name__)
            return None
    return read


def test_alert_reading(client) -> Reading:
    """Consume a pending test request atomically (GET + DEL in one MULTI)."""
    pipe = client.pipeline(transaction=True)
    pipe.get(TEST_ALERT_KEY)
    pipe.delete(TEST_ALERT_KEY)
    request_id, _ = pipe.execute()
    if not request_id:
        return Reading(tripped=False, identities=[], count=0, value={})
    if isinstance(request_id, bytes):
        request_id = request_id.decode("utf-8", "replace")
    ident = f"test:{str(request_id)[:64]}"
    return Reading(tripped=True, identities=[ident], count=1, value={"test": True})


def _observe(key: str, event: str, count: int, new: int, sample, **extra) -> None:
    # Counts, identities (UUID-based references) and timings only.
    detail = " ".join(f"{k}={v}" for k, v in extra.items())
    logger.warning("OPS_ALERT mode=observe key=%s event=%s count=%d new=%d sample=%s%s",
                   key, event, count, new, list(sample)[:SAMPLE], (" " + detail) if detail else "")


def record(cur, key: str, reading: Reading) -> Optional[str]:
    """Advance one signal's incident. Returns the event logged, if any."""
    import json
    cur.execute("SELECT id, member_count, members_truncated, notified_count "
                "FROM ops_alerts WHERE key = %s AND resolved_at IS NULL FOR UPDATE", (key,))
    row = cur.fetchone()
    if not reading.tripped:
        if row is None:
            return None
        cur.execute("UPDATE ops_alerts SET resolved_at = now(), last_evaluated_at = now() "
                    "WHERE id = %s RETURNING round(extract(epoch FROM resolved_at - opened_at) / 60)",
                    (row[0],))
        minutes = int(cur.fetchone()[0])
        _observe(key, "resolved", 0, 0, [], after_min=minutes)
        ops_notify.announce(cur, row[0], key, "resolved")
        return "resolved"

    truncated = reading.count > len(reading.identities)
    event = None
    if row is None:
        cur.execute("""SELECT EXISTS (SELECT 1 FROM ops_alerts WHERE key = %s
                       AND resolved_at > now() - make_interval(mins => %s))""", (key, FLAP_WINDOW_MIN))
        flapping = cur.fetchone()[0]
        cur.execute("INSERT INTO ops_alerts (key) VALUES (%s) RETURNING id", (key,))
        alert_id, notified = cur.fetchone()[0], 0
        event = "open"
    else:
        alert_id, _, _, notified = row
        flapping = False

    cur.execute("""
        INSERT INTO ops_alert_members (alert_id, identity)
        SELECT %s, unnest(%s::text[])
        ON CONFLICT (alert_id, identity) DO UPDATE SET last_seen_at = now()
        RETURNING identity, (xmax = 0) AS inserted
    """, (alert_id, reading.identities))
    new_ids = [ident for ident, inserted in cur.fetchall() if inserted]

    if event is None:
        if truncated:
            # Beyond the stored bound "new" can't be judged per identity: it
            # means the outstanding count grew past the last announcement.
            if reading.count > notified:
                event = "grew"
        elif new_ids:
            event = "new_members"
    announce = event is not None
    cur.execute("""
        UPDATE ops_alerts SET member_count = %s, members_truncated = %s, last_value = %s::jsonb,
               last_evaluated_at = now(), notified_count = CASE WHEN %s THEN %s ELSE notified_count END
        WHERE id = %s
    """, (reading.count, truncated, json.dumps(reading.value), announce, reading.count, alert_id))
    if announce:
        _observe(key, event, reading.count, len(new_ids), new_ids or reading.identities,
                 truncated=str(truncated).lower(), flap=str(flapping).lower())
        ops_notify.announce(cur, alert_id, key, event, flapping=flapping)
    return event


def run_once(db_url: str, redis_client=None, clock=time.monotonic) -> dict:
    """One monitor pass. Never raises. Returns {key: event or None or 'error'}."""
    import psycopg

    started = clock()
    results: dict = {}
    try:
        conn = psycopg.connect(db_url, connect_timeout=5,
                               options=f"-c statement_timeout={STATEMENT_TIMEOUT_MS}")
    except Exception as exc:  # noqa: BLE001
        logger.warning("OPS_MONITOR skipped: database unreachable (%s)", type(exc).__name__)
        return results
    with conn:
        with conn.cursor() as cur:
            cur.execute("SELECT to_regclass('ops_alerts') IS NOT NULL AND to_regclass('ops_alert_members') IS NOT NULL")
            if not cur.fetchone()[0]:
                conn.rollback()
                logger.warning("OPS_MONITOR skipped: migration 0069 (ops_alerts) is not applied")
                return results
            conn.commit()

        readings = []
        try:
            # First, so a spent budget never defers it. A request is consumed
            # inside its read, and only when no test incident is open.
            readings.append(("ops_test_alert", test_alert_read(redis_client or ops_heartbeat._redis())))
        except Exception as exc:  # noqa: BLE001 - no Redis client at all
            logger.warning("OPS_MONITOR test-alert check skipped: %s", type(exc).__name__)
        for sig in ops_signals.SIGNALS:
            readings.append((sig.key, sig.read))
        try:
            hb = heartbeat_readings(redis_client or ops_heartbeat._redis())
            readings.extend((key, (lambda _cur, r=r: r)) for key, r in hb.items())
        except Exception as exc:  # noqa: BLE001
            logger.warning("OPS_MONITOR heartbeat signals skipped: %s", type(exc).__name__)

        for key, read in readings:
            if clock() - started > BUDGET_S:
                logger.warning("OPS_MONITOR budget spent; deferred: %s", key)
                results[key] = "deferred"
                continue
            try:
                with conn.cursor() as cur:
                    reading = read(cur)
                    if reading is None:     # the source could not be read; record nothing
                        conn.rollback()
                        continue
                    results[key] = record(cur, key, reading)
                conn.commit()
            except Exception as exc:  # noqa: BLE001 - one signal never stops the others
                conn.rollback()
                logger.warning("OPS_MONITOR signal %s failed: %s", key, type(exc).__name__)
                results[key] = "error"

        # Delivery (inert unless OPS_ALERTS_ENABLED=1): renotify marks, then
        # the claimable rows, inside what is left of this run's budget.
        try:
            with conn.cursor() as cur:
                ops_notify.enqueue_renotifications(cur)
            conn.commit()
            ops_notify.dispatch(conn, clock, started + BUDGET_S)
        except Exception as exc:  # noqa: BLE001 - never reaches the ticker
            conn.rollback()
            logger.warning("OPS_MONITOR delivery step failed: %s", type(exc).__name__)
    return results


class MonitorRunner:
    """Started from the ticker loop. Never blocks it, never raises into it."""

    def __init__(self, db_url: str, clock=time.monotonic):
        self.db_url = db_url
        self.clock = clock
        self.thread: Optional[threading.Thread] = None
        self.last_start: Optional[float] = None
        self.token = str(uuid.uuid4())

    def maybe_start(self, redis_client=None) -> bool:
        """Start this window's run on its own thread. Touches nothing external.

        Even the lease is taken on the monitor's thread: a Redis call here
        could cost the ticker its full timeout on every tick while Redis
        hangs, and nothing the monitor does may ever hold up scheduling
        (Codex review of #322).
        """
        try:
            if self.thread is not None and self.thread.is_alive():
                return False
            now = self.clock()
            if self.last_start is not None and now - self.last_start < INTERVAL_S:
                return False
            self.last_start = now
            self.thread = threading.Thread(target=self._leased_run, args=(redis_client,),
                                           name="ops-monitor", daemon=True)
            self.thread.start()
            return True
        except Exception as exc:  # noqa: BLE001
            logger.warning("OPS_MONITOR not started: %s", type(exc).__name__)
            return False

    def _leased_run(self, redis_client) -> None:
        try:
            client = redis_client or ops_heartbeat._redis()
            if not client.set(LEASE_KEY, self.token, nx=True, ex=LEASE_S):
                return          # another ticker holds this window
        except Exception as exc:  # noqa: BLE001
            logger.warning("OPS_MONITOR skipped: no lease (%s)", type(exc).__name__)
            return
        run_once(self.db_url, client)


def enabled_mode() -> str:
    """For the startup log line: the mode and which channels have a destination."""
    if not ops_notify.enabled():
        return "observe"
    channels = [name for name, ok in ops_notify.channels_configured().items() if ok]
    return f"send ({', '.join(channels) or 'no destination set: nothing sends'})"

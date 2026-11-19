"""GET /ready (LR-027 slice 1): bounded, public, and honest about which part is down.

Real app, real middleware, real pool against the migrated database, real Redis
(database 15, so the heartbeat keys and the queue are the test's own).
"""
import os
import threading
import time

import pytest

DB = os.getenv("DATABASE_URL")
psycopg = pytest.importorskip("psycopg")
pytestmark = pytest.mark.skipif(not DB or "fake" in (DB or ""), reason="Set DATABASE_URL to run this test")
REDIS_URL = "redis://127.0.0.1:6379/15"


@pytest.fixture(scope="module")
def client():
    from fastapi.testclient import TestClient
    from api.main import app
    return TestClient(app, raise_server_exceptions=False)


@pytest.fixture
def r():
    import redis
    conn = redis.from_url(REDIS_URL, decode_responses=True)
    try:
        conn.ping()
    except redis.exceptions.ConnectionError:
        pytest.skip("Redis on 127.0.0.1:6379 is needed")
    conn.flushdb()
    yield conn
    conn.flushdb()


@pytest.fixture(autouse=True)
def fresh(monkeypatch):
    from api.routes import ready
    from api.settings import settings
    monkeypatch.setattr(settings, "REDIS_URL", REDIS_URL)
    monkeypatch.setattr(ready, "_redis_client", None)
    monkeypatch.setattr(ready, "_cached", None)
    yield


def beat(r, key, age_s=0):
    r.set(key, int(r.time()[0]) - age_s)


def healthy(r):
    from api.routes import ready
    beat(r, ready.TICKER_KEY)
    beat(r, ready.WORKER_KEY)


def test_ready_when_everything_works(client, r):
    healthy(r)
    res = client.get("/ready")
    assert res.status_code == 200, res.text
    body = res.json()
    assert body["ready"] is True
    assert {k: v["status"] for k, v in body["checks"].items()} == {
        "database": "ok", "redis": "ok", "ticker": "ok", "worker": "ok"}
    assert res.headers["cache-control"] == "no-store"


def test_the_public_body_names_no_host_dsn_or_exception(client, r, monkeypatch):
    from api.settings import settings
    monkeypatch.setattr(settings, "REDIS_URL", "redis://127.0.0.1:1/0")
    text = client.get("/ready").text
    for secret in ("127.0.0.1", "5433", "6379", ":1/", "postgres", "redis://", "Error", "Traceback"):
        assert secret not in text, secret


def test_it_is_public_and_only_the_exact_path_is(client, r):
    healthy(r)
    assert client.get("/ready").status_code == 200        # no credential, never 401
    assert client.get("/readyz").status_code == 401       # not a prefix
    assert client.get("/ready/x").status_code == 401


def test_health_is_unchanged(client):
    from api.schema_guard import REQUIRED_MIGRATION
    res = client.get("/health")
    assert res.status_code == 200 and res.json()["ok"] is True
    assert res.json()["schema"] == REQUIRED_MIGRATION


def test_no_ticker_heartbeat_is_not_ready(client, r):
    from api.routes import ready
    beat(r, ready.WORKER_KEY)
    res = client.get("/ready")
    assert res.status_code == 503
    assert res.json()["checks"]["ticker"] == {"status": "stale", "age_s": None}


def test_a_ticker_three_ticks_late_is_stale(client, r):
    from api.routes import ready
    beat(r, ready.WORKER_KEY)
    beat(r, ready.TICKER_KEY, age_s=181)
    res = client.get("/ready")
    assert res.status_code == 503
    assert res.json()["checks"]["ticker"]["status"] == "stale"


@pytest.mark.parametrize("age, queued, state", [
    (0, 0, "ok"), (300, 0, "ok"), (300, 9, "ok"),
    (301, 0, "stale"),            # nothing waiting, nothing ran: the worker is down
    (301, 1, "backlog"),          # waiting behind a burst
    (1800, 5, "backlog"),
    (1801, 5, "stale"),           # past the queued-run horizon
    (None, 0, "stale"), (None, 3, "stale"),
])
def test_worker_state_tells_a_dead_worker_from_a_backlog(age, queued, state):
    from api.routes.ready import worker_state
    assert worker_state(age, queued) == state


def test_a_backlog_is_reported_but_still_ready(client, r):
    from api.routes import ready
    beat(r, ready.TICKER_KEY)
    beat(r, ready.WORKER_KEY, age_s=600)
    r.rpush(ready.CELERY_QUEUE, "a", "b", "c")
    res = client.get("/ready")
    assert res.status_code == 200
    assert res.json()["checks"]["worker"] == {"status": "backlog", "age_s": 600}


def test_a_dead_worker_with_nothing_queued_is_not_ready(client, r):
    from api.routes import ready
    beat(r, ready.TICKER_KEY)
    beat(r, ready.WORKER_KEY, age_s=600)
    res = client.get("/ready")
    assert res.status_code == 503
    assert res.json()["checks"]["worker"]["status"] == "stale"


def test_a_database_ahead_of_the_binary_is_ready(client, r, monkeypatch):
    """Rollback, or a newer compatible migration: the required row is present."""
    from api import schema_guard
    monkeypatch.setattr(schema_guard, "REQUIRED_MIGRATION", "0001_base.sql")
    healthy(r)
    res = client.get("/ready")
    assert res.status_code == 200, res.text
    assert res.json()["checks"]["database"]["status"] == "ok"


def test_a_database_behind_the_binary_is_not_ready(client, r, monkeypatch):
    from api import schema_guard
    monkeypatch.setattr(schema_guard, "REQUIRED_MIGRATION", "9999_not_applied.sql")
    healthy(r)
    res = client.get("/ready")
    assert res.status_code == 503
    assert res.json()["checks"]["database"]["status"] == "behind"


def test_an_exhausted_pool_fails_within_its_budget(client, r, monkeypatch):
    from psycopg_pool import ConnectionPool
    from api import db
    healthy(r)
    pool = ConnectionPool(conninfo=DB, min_size=1, max_size=1, timeout=10, open=True)
    monkeypatch.setattr(db, "_pool", pool)
    try:
        with pool.connection():           # the only connection, held
            started = time.monotonic()
            res = client.get("/ready")
            elapsed = time.monotonic() - started
    finally:
        pool.close()
    assert res.status_code == 503
    assert res.json()["checks"]["database"]["status"] == "failing"
    assert elapsed < 2.5, elapsed         # the 1 s acquisition budget, not the pool's 10 s


def test_redis_down_fails_within_its_budget(client, monkeypatch):
    from api.settings import settings
    monkeypatch.setattr(settings, "REDIS_URL", "redis://127.0.0.1:1/0")
    started = time.monotonic()
    res = client.get("/ready")
    elapsed = time.monotonic() - started
    assert res.status_code == 503
    checks = res.json()["checks"]
    assert checks["redis"]["status"] == "failing"
    assert checks["ticker"]["status"] == checks["worker"]["status"] == "stale"
    assert elapsed < 2.5, elapsed


def test_one_evaluation_per_ten_seconds_however_many_callers(monkeypatch):
    from api.routes import ready
    calls = []

    def slow_evaluate():
        calls.append(1)
        time.sleep(0.3)
        return 200, {"ready": True, "schema": "x", "checks": {}}

    clock = [1000.0]
    monkeypatch.setattr(ready, "evaluate", slow_evaluate)
    monkeypatch.setattr(ready.time, "monotonic", lambda: clock[0])
    threads = [threading.Thread(target=ready.ready) for _ in range(10)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()
    assert len(calls) == 1                # single flight
    clock[0] += 9.9
    ready.ready()
    assert len(calls) == 1                # still cached
    clock[0] += 0.2
    ready.ready()
    assert len(calls) == 2                # re-evaluated after 10 s


def test_readiness_uses_its_own_short_timeout_redis_client():
    """A refused port fails instantly, so the timeouts need their own check:
    the shared client in cache.py waits 2 s per connect and per read."""
    from api.routes import ready
    from api import cache
    kwargs = ready._readiness_redis().connection_pool.connection_kwargs
    assert kwargs["socket_connect_timeout"] <= 0.5
    assert kwargs["socket_timeout"] <= 0.5
    assert ready._readiness_redis() is not cache.get_redis()

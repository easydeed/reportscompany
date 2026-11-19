"""GET /ready (LR-027 slice 1): bounded, public, and honest about which part is down.

Real app, real middleware, real pool against the migrated database, real Redis
(database 15, so the heartbeat keys and the queue are the test's own).
"""
import json
import os
import threading
import time

import pytest

DB = os.getenv("DATABASE_URL")
psycopg = pytest.importorskip("psycopg")
pytestmark = pytest.mark.skipif(not DB or "fake" in (DB or ""), reason="Set DATABASE_URL to run this test")
# An explicitly disposable Redis, never a default: CI sets TEST_REDIS_URL to
# its own service. Cleanup deletes only the keys these tests own (Codex #322).
REDIS_URL = os.getenv("TEST_REDIS_URL")
OWNED = ("ops:heartbeat:ticker", "ops:heartbeat:worker", "celery")


def clean_owned(conn):
    conn.delete(*OWNED)


@pytest.fixture(scope="module")
def client():
    from fastapi.testclient import TestClient
    from api.main import app
    return TestClient(app, raise_server_exceptions=False)


@pytest.fixture
def r():
    import redis
    if not REDIS_URL:
        if os.getenv("REQUIRE_REDIS_TESTS") == "1":
            pytest.fail("REQUIRE_REDIS_TESTS=1 but TEST_REDIS_URL is not set")
        pytest.skip("Set TEST_REDIS_URL to a disposable Redis database")
    conn = redis.from_url(REDIS_URL, decode_responses=True)
    try:
        conn.ping()
    except redis.exceptions.ConnectionError:
        # CI provides Redis and sets REQUIRE_REDIS_TESTS=1: there, a missing
        # Redis is a failure, never a silently skipped proof.
        if os.getenv("REQUIRE_REDIS_TESTS") == "1":
            pytest.fail("REQUIRE_REDIS_TESTS=1 but TEST_REDIS_URL is unreachable")
        pytest.skip("TEST_REDIS_URL is unreachable")
    clean_owned(conn)
    yield conn
    clean_owned(conn)


@pytest.fixture(autouse=True)
def fresh(monkeypatch):
    from api.routes import ready
    from api.settings import settings
    monkeypatch.setattr(settings, "REDIS_URL", REDIS_URL or "redis://127.0.0.1:1/0")
    monkeypatch.setattr(ready, "_redis_client", None)
    monkeypatch.setattr(ready, "_cached", None)
    monkeypatch.setattr(ready, "_inflight", None, raising=False)
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


# ── Codex #322 P1: the timeouts hold whatever state the pooled connection is in ──

@pytest.fixture
def warmed_autocommit_pool(monkeypatch):
    """One connection, last borrowed through db_conn_autocommit, so it comes
    back to /ready with autocommit=True: the state Codex reproduced."""
    from psycopg_pool import ConnectionPool
    from api import db
    pool = ConnectionPool(conninfo=DB, min_size=1, max_size=1, timeout=10, open=True)
    monkeypatch.setattr(db, "_pool", pool)
    with db.db_conn_autocommit() as cur:
        cur.execute("SELECT 1")
    with pool.connection() as conn:
        assert conn.autocommit is True
    yield pool
    pool.close()


def _timed(fn, limit):
    out, done = {}, threading.Event()

    def run():
        started = time.monotonic()
        out["result"] = fn()
        out["elapsed"] = time.monotonic() - started
        done.set()

    threading.Thread(target=run, daemon=True).start()
    return out if done.wait(limit) else None


def test_lock_timeout_applies_on_an_autocommit_connection(warmed_autocommit_pool):
    from api.routes import ready
    holder = psycopg.connect(DB)
    try:
        holder.execute("LOCK TABLE schema_migrations IN ACCESS EXCLUSIVE MODE")
        out = _timed(ready._check_database, 4)
        assert out is not None, "the schema probe waited on the lock without a timeout"
        assert out["result"] == {"status": "failing"} and out["elapsed"] < 1.5
    finally:
        holder.rollback()
        holder.close()


def test_statement_timeout_applies_on_an_autocommit_connection(warmed_autocommit_pool, monkeypatch):
    from api.routes import ready
    monkeypatch.setattr(ready, "schema_check", lambda cur: cur.execute("SELECT pg_sleep(3)"))
    out = _timed(ready._check_database, 5)
    assert out is not None
    assert out["result"] == {"status": "failing"} and out["elapsed"] < 2.0, out


def test_the_check_leaves_the_connection_as_it_found_it(warmed_autocommit_pool):
    from api.routes import ready
    assert ready._check_database() == {"status": "ok"}
    with warmed_autocommit_pool.connection() as conn:
        assert conn.info.transaction_status.name == "IDLE"
        row = conn.execute("SELECT current_setting('statement_timeout'), current_setting('lock_timeout')").fetchone()
        assert row == ("0", "0")                    # nothing leaked into the next borrower


# ── Codex #322 P1: an expired green result is never served ──────────────────

GREEN = {"ready": True, "schema": "x", "checks": {"database": {"status": "ok"}}}


@pytest.fixture
def stalled(monkeypatch):
    """evaluate() blocks until released; an hour-old green result is cached."""
    from api.routes import ready
    gate, calls = threading.Event(), []

    def stuck():
        calls.append(1)
        gate.wait(10)
        return 200, GREEN

    monkeypatch.setattr(ready, "evaluate", stuck)
    monkeypatch.setattr(ready, "EVAL_BUDGET_S", 0.3, raising=False)
    monkeypatch.setattr(ready, "_cached", (time.monotonic() - 3600, 200, GREEN))
    yield gate, calls
    # Let the stalled evaluation finish BEFORE monkeypatch restores the module
    # state, or its late write would leak a fresh green into the next test.
    gate.set()
    thread = ready._inflight
    if thread is not None:
        thread.join(5)


def _status(response):
    return response.status_code, json.loads(response.body)


def test_a_stalled_evaluation_never_serves_an_expired_green(stalled):
    from api.routes import ready
    out = _timed(ready.ready, 3)
    assert out is not None, "/ready waited on the stalled evaluation without a budget"
    status, body = _status(out["result"])
    assert status == 503 and body["ready"] is False
    assert out["elapsed"] < 1.0


def test_callers_during_a_stall_get_503_and_start_no_second_evaluation(stalled):
    from api.routes import ready
    gate, calls = stalled
    results = [_timed(ready.ready, 3) for _ in range(4)]
    assert all(r is not None and _status(r["result"])[0] == 503 for r in results)
    assert len(calls) == 1


def test_after_the_stall_clears_the_next_caller_gets_a_fresh_result(stalled):
    from api.routes import ready
    gate, calls = stalled
    assert _status(ready.ready())[0] == 503
    gate.set()
    for _ in range(50):
        if ready._inflight is None:
            break
        time.sleep(0.02)
    status, body = _status(ready.ready())
    assert status == 200 and body == GREEN


# ── Codex #322 P2: tests never wipe a Redis they do not own ─────────────────

def test_cleanup_removes_only_test_owned_keys(r):
    r.set("unrelated:sentinel", "keep me")
    try:
        r.set("ops:heartbeat:ticker", 1)
        r.rpush("celery", "x")
        clean_owned(r)
        assert r.get("unrelated:sentinel") == "keep me"
        assert not r.exists("ops:heartbeat:ticker", "celery")
    finally:
        r.delete("unrelated:sentinel")


def test_no_redis_fixture_flushes_a_database():
    from pathlib import Path
    root = Path(__file__).resolve().parents[3]
    for path in [*root.glob("apps/*/tests/*.py"), *root.glob("tests/*.py")]:
        code = path.read_text()
        for call in (".flush" + "db(", ".flush" + "all("):
            assert call not in code, (path, call)

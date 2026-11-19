"""LR-027 slice 1: the ticker produces both heartbeats; nothing here can stop it."""
import os
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
redis = pytest.importorskip("redis")

from worker import ops_heartbeat  # noqa: E402


# An explicitly disposable Redis (TEST_REDIS_URL, set by CI); cleanup deletes
# only the keys these tests own, never the database (Codex #322).
OWNED = (ops_heartbeat.TICKER_KEY, ops_heartbeat.WORKER_KEY, ops_heartbeat.CELERY_QUEUE)


@pytest.fixture
def r():
    url = os.getenv("TEST_REDIS_URL")
    if not url:
        if os.getenv("REQUIRE_REDIS_TESTS") == "1":
            pytest.fail("REQUIRE_REDIS_TESTS=1 but TEST_REDIS_URL is not set")
        pytest.skip("Set TEST_REDIS_URL to a disposable Redis database")
    conn = redis.from_url(url, decode_responses=True)
    try:
        conn.ping()
    except redis.exceptions.ConnectionError:
        if os.getenv("REQUIRE_REDIS_TESTS") == "1":
            pytest.fail("REQUIRE_REDIS_TESTS=1 but TEST_REDIS_URL is unreachable")
        pytest.skip("TEST_REDIS_URL is unreachable")
    conn.delete(*OWNED)
    yield conn
    conn.delete(*OWNED)


class FakeCelery:
    def __init__(self, fail=False):
        self.sent, self.fail = [], fail

    def send_task(self, name, **kwargs):
        if self.fail:
            raise ConnectionError("broker down")
        self.sent.append((name, kwargs))


def test_beat_writes_redis_server_time_with_a_ttl(r):
    now = int(r.time()[0])
    written = ops_heartbeat.beat(ops_heartbeat.TICKER_KEY, ops_heartbeat.TICKER_TTL_S, r)
    assert abs(written - now) <= 1
    assert int(r.get(ops_heartbeat.TICKER_KEY)) == written
    assert 0 < r.ttl(ops_heartbeat.TICKER_KEY) <= ops_heartbeat.TICKER_TTL_S


def test_beat_never_raises_when_redis_is_down():
    down = redis.from_url("redis://127.0.0.1:1/0", socket_connect_timeout=0.2, socket_timeout=0.2)
    assert ops_heartbeat.beat(ops_heartbeat.TICKER_KEY, 600, down) is None


def test_after_tick_writes_the_ticker_key_and_publishes_the_work_item(r):
    app = FakeCelery()
    ops_heartbeat.after_tick(app, r).join(2)
    assert r.get(ops_heartbeat.TICKER_KEY)
    assert app.sent == [("ops_heartbeat", {"queue": "celery", "expires": 120, "retry": False})]


def test_after_tick_survives_a_broker_failure(r):
    ops_heartbeat.after_tick(FakeCelery(fail=True), r).join(2)   # must not raise
    assert r.get(ops_heartbeat.TICKER_KEY)


def test_only_one_heartbeat_is_ever_in_flight(r):
    import threading
    gate = threading.Event()

    class Stuck(FakeCelery):
        def send_task(self, name, **kwargs):
            gate.wait(5)
            super().send_task(name, **kwargs)

    app = Stuck()
    first = ops_heartbeat.after_tick(app, r)
    assert first is not None
    assert all(ops_heartbeat.after_tick(app, r) is None for _ in range(5))   # skipped, not queued
    gate.set()
    first.join(2)
    assert len(app.sent) == 1
    assert ops_heartbeat.after_tick(app, r) is not None                     # free again


def test_the_worker_task_writes_the_worker_key(r, monkeypatch):
    monkeypatch.setattr(ops_heartbeat, "_client", r)
    from worker import ops_tasks
    ops_tasks.ops_heartbeat()
    assert r.get(ops_heartbeat.WORKER_KEY)
    assert r.ttl(ops_heartbeat.WORKER_KEY) > 1800        # outlives the backlog horizon


def test_the_worker_registers_the_task_the_ticker_publishes():
    from worker.app import celery
    assert ops_heartbeat.TASK_NAME in celery.tasks


@pytest.fixture
def ticker(monkeypatch):
    from worker import schedules_tick
    beats = []
    for name in ("keep_api_warm", "process_due_schedules", "sweep_stale_runs"):
        monkeypatch.setattr(schedules_tick, name, lambda: None)
    monkeypatch.setattr(schedules_tick.ops_heartbeat, "after_tick", lambda app: beats.append(app))
    return schedules_tick, beats


def test_a_completed_loop_refreshes_the_heartbeats(ticker):
    schedules_tick, beats = ticker
    assert schedules_tick.tick_once() is True
    assert beats == [schedules_tick.celery]


def test_a_loop_that_raises_leaves_the_heartbeat_to_go_stale(ticker, monkeypatch):
    schedules_tick, beats = ticker

    def boom():
        raise RuntimeError("sweep failed")

    monkeypatch.setattr(schedules_tick, "sweep_stale_runs", boom)
    assert schedules_tick.tick_once() is False
    assert beats == []


# ── Codex #322 P1: a broker that never answers must never hold up the ticker ──

@pytest.fixture
def silent_broker():
    """A TCP listener that accepts connections and never replies."""
    import socket
    import threading
    server = socket.socket()
    server.bind(("127.0.0.1", 0))
    server.listen(64)
    held = []

    def accept():
        while True:
            try:
                held.append(server.accept()[0])
            except OSError:
                return

    threading.Thread(target=accept, daemon=True).start()
    yield f"redis://127.0.0.1:{server.getsockname()[1]}/0"
    server.close()
    for conn in held:
        conn.close()


def _within(seconds, fn):
    import threading
    finished = threading.Event()

    def run():
        fn()
        finished.set()

    threading.Thread(target=run, daemon=True).start()
    return finished.wait(seconds)


def test_a_broker_that_never_answers_never_holds_up_a_tick(silent_broker, r):
    from celery import Celery
    app = Celery("silent", broker=silent_broker)
    assert _within(2.0, lambda: [ops_heartbeat.after_tick(app, r) for _ in range(3)]), \
        "the heartbeat publish blocked the ticker"


def test_the_real_ticker_keeps_ticking_against_a_silent_broker(silent_broker, monkeypatch):
    from celery import Celery
    from worker import schedules_tick
    for name in ("keep_api_warm", "process_due_schedules", "sweep_stale_runs"):
        monkeypatch.setattr(schedules_tick, name, lambda: None)
    monkeypatch.setattr(schedules_tick, "celery", Celery("silent", broker=silent_broker))
    assert _within(2.0, lambda: [schedules_tick.tick_once() for _ in range(5)]), \
        "tick_once blocked on the heartbeat publish"

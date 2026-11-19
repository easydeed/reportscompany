"""LR-027 slice 1: the ticker produces both heartbeats; nothing here can stop it."""
import os
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
redis = pytest.importorskip("redis")

from worker import ops_heartbeat  # noqa: E402


@pytest.fixture
def r():
    conn = redis.from_url("redis://127.0.0.1:6379/15", decode_responses=True)
    try:
        conn.ping()
    except redis.exceptions.ConnectionError:
        # CI provides Redis and sets REQUIRE_REDIS_TESTS=1: there, a missing
        # Redis is a failure, never a silently skipped proof.
        if os.getenv("REQUIRE_REDIS_TESTS") == "1":
            pytest.fail("REQUIRE_REDIS_TESTS=1 but Redis on 127.0.0.1:6379 is unreachable")
        pytest.skip("Redis on 127.0.0.1:6379 is needed")
    conn.flushdb()
    yield conn
    conn.flushdb()


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
    ops_heartbeat.after_tick(app, r)
    assert r.get(ops_heartbeat.TICKER_KEY)
    assert app.sent == [("ops_heartbeat", {"queue": "celery", "expires": 120})]


def test_after_tick_survives_a_broker_failure(r):
    ops_heartbeat.after_tick(FakeCelery(fail=True), r)   # must not raise
    assert r.get(ops_heartbeat.TICKER_KEY)


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

"""LR-027 threshold report: replaying the monitor's own queries at past instants.

Real PostgreSQL, one rolled-back transaction per test (as test_ops_monitor.py).
"""
import importlib.util
import json
import os
import sys
import uuid
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
DB = os.getenv("DATABASE_URL")
psycopg = pytest.importorskip("psycopg")
pytestmark = pytest.mark.skipif(not DB or "fake" in (DB or ""), reason="Set DATABASE_URL to run this test")

from worker import ops_signals  # noqa: E402

spec = importlib.util.spec_from_file_location("ops_threshold_report",
                                              ROOT.parents[1] / "scripts" / "ops_threshold_report.py")
report_mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(report_mod)

TABLES = ("schedules", "schedule_runs", "report_generations", "email_log",
          "consumer_reports", "webhook_deliveries", "ops_alert_members", "ops_alerts")


def u():
    return str(uuid.uuid4())


@pytest.fixture
def conn():
    c = psycopg.connect(DB)
    try:
        cur = c.cursor()
        cur.execute("SET LOCAL session_replication_role = replica")
        for t in TABLES:
            cur.execute(f"DELETE FROM {t}")
        yield c
    finally:
        c.rollback()
        c.close()


def db_now(cur):
    cur.execute("SELECT now()")
    return cur.fetchone()[0]


def report_row(cur, status, ago):
    cur.execute(f"""INSERT INTO report_generations (id, account_id, report_type, status, generated_at)
                    VALUES (%s, %s, 'market_snapshot', %s, LOCALTIMESTAMP - interval '{ago}')""",
                (u(), u(), status))


def email_row(cur, *, code, error=None, status="failed", ago="5 minutes"):
    cur.execute(f"""INSERT INTO email_log (id, account_id, provider, status, response_code, error,
                    created_at, subject) VALUES (%s, %s, 'sendgrid', %s, %s, %s, now() - interval '{ago}', 's')""",
                (u(), u(), status, code, error))


def test_live_readings_are_unchanged_by_the_replay_clock(conn):
    """at=None is exactly the live query: same readings as before the change."""
    cur = conn.cursor()
    for _ in range(5):
        report_row(cur, "failed", "10 minutes")
    report_row(cur, "completed", "10 minutes")
    report_row(cur, "failed", "2 hours")
    live = ops_signals.report_failures(cur)
    assert live.tripped and live.value == {"failed": 5, "total": 6}
    assert ops_signals.report_failures(cur, at=db_now(cur)).value == live.value


def test_a_past_burst_trips_when_replayed_at_its_hour_and_not_now(conn):
    cur = conn.cursor()
    for _ in range(5):
        report_row(cur, "failed", "3 hours")
    report_row(cur, "completed", "3 hours")
    for _ in range(10):
        email_row(cur, code=403, ago="3 hours")
    for _ in range(3):
        email_row(cur, code=400, error="No recipients", ago="3 hours")
    then = db_now(cur) - timedelta(hours=3) + timedelta(minutes=5)
    assert not ops_signals.report_failures(cur).tripped
    assert ops_signals.report_failures(cur, at=then).tripped
    assert not ops_signals.provider_refusals(cur).tripped
    assert ops_signals.provider_refusals(cur, at=then).value == {"refused": 10, "deliveries": 13}
    assert ops_signals.send_not_attempted(cur, at=then).tripped
    # Rows newer than the replay instant are not counted: the window has an upper edge.
    before = db_now(cur) - timedelta(hours=3) - timedelta(minutes=5)
    assert ops_signals.report_failures(cur, at=before).value == {"failed": 0, "total": 0}


def test_replay_counts_trips_hours_and_near_misses(conn):
    cur = conn.cursor()
    for _ in range(5):
        report_row(cur, "failed", "90 minutes")
    for _ in range(3):
        report_row(cur, "failed", "5 hours")                  # a near miss: 3 >= 5/2, not tripped
    now = db_now(cur)
    out = report_mod.replay(cur, now - timedelta(hours=8), now, timedelta(minutes=30))
    rf = out["report_failures"]
    assert rf["evaluations"] == 16 and rf["trips"] == 2 and rf["max"] == 5
    assert rf["near_misses"] == 2


def at(h):
    return datetime(2026, 11, 20, 0, 0, tzinfo=timezone.utc) + timedelta(hours=h)


def test_message_load_follows_the_sender_rules():
    rows = [
        # SMS signal: open + resolved texts; one update email; resolved 1 h later.
        {"key": "report_stuck", "opened": at(0), "resolved": at(1), "members": 2, "truncated": False, "batches": 2},
        # Re-opened 10 min after resolving: the open is email only (flap rule).
        {"key": "report_stuck", "opened": at(1) + timedelta(minutes=10), "resolved": at(2),
         "members": 1, "truncated": False, "batches": 1},
        # Open 13 h: two 6-hour renotifies (texts), plus open and resolved.
        {"key": "dispatch_stranded", "opened": at(3), "resolved": at(16), "members": 1, "truncated": False,
         "batches": 1},
        # Email-only signal, still open.
        {"key": "schedule_blocked", "opened": at(4), "resolved": None, "members": 1, "truncated": False,
         "batches": 1},
    ]
    load = report_mod.message_load(rows, at(5))
    assert load["by_key"]["report_stuck"] == {"emails": 5, "texts": 3, "flapped_opens": 1}
    assert load["by_key"]["dispatch_stranded"] == {"emails": 4, "texts": 4, "flapped_opens": 0}
    assert load["by_key"]["schedule_blocked"] == {"emails": 1, "texts": 0, "flapped_opens": 0}
    assert load["max_texts_in_an_hour"] == 1 and load["hours_over_cap"] == 0       # no two in one clock hour


def test_the_report_carries_counts_never_identities(conn):
    cur = conn.cursor()
    cur.execute("INSERT INTO ops_alerts (key, opened_at, resolved_at, member_count) "
                "VALUES ('report_stuck', now() - interval '3 hours', now() - interval '2 hours', 1) RETURNING id")
    alert = cur.fetchone()[0]
    secret = f"report:{u()}"
    cur.execute("INSERT INTO ops_alert_members (alert_id, identity) VALUES (%s, %s)", (alert, secret))
    out = report_mod.report(conn, 24, 60)
    assert "| `report_stuck` | yes | 1 | 0 | 0 | 60 min | 60 min | 1 | 2 | 2 |" in out
    assert secret not in out and secret.split(":")[1] not in out and str(alert) not in out


def test_the_script_runs_read_only(monkeypatch, capsys):
    """main() opens a read-only connection: any write in report() would fail."""
    seen = {}
    real = report_mod.report

    def spy(conn, hours, step):
        with conn.cursor() as cur:
            cur.execute("SHOW transaction_read_only")
            seen["ro"] = cur.fetchone()[0]
            with pytest.raises(psycopg.errors.ReadOnlySqlTransaction):
                cur.execute("CREATE TEMP TABLE nope (x int)")
        conn.rollback()
        return real(conn, 1, 60)
    monkeypatch.setattr(report_mod, "report", spy)
    assert report_mod.main(["--hours", "1"]) == 0
    assert seen["ro"] == "on"
    assert "LR-027 observe-mode threshold report" in capsys.readouterr().out

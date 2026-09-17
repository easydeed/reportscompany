"""
D-019 at the point where the send actually happens.

WHY THE TICKER NEEDS ITS OWN TEST
---------------------------------
The API gate refuses to CREATE a sending schedule. It cannot refuse one that
already exists, and the API is not what sends: sixty seconds after a schedule
comes due, `process_due_schedules` picks the row up and hands it to Celery,
having consulted nothing but `active` and `next_run_at`. An enforcement that
lives only in the API enforces the request, not the rule — so the check is
repeated here, and so is the test.

BEHAVIOURAL, not structural. `psycopg.connect` is replaced with a fake feed of
due schedules that answers the two queries the ticker asks and records the
writes. What is asserted is whether a task was dispatched, which is the only
thing that decides whether mail leaves the building.

Run:
    PYTHONPATH=apps/worker/src pytest apps/worker/tests/test_ticker_unverified.py -v
"""
import os
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

os.environ.setdefault("DATABASE_URL", "postgresql://fake/fake")
os.environ.setdefault("REDIS_URL", "redis://localhost:6379/0")

from worker import schedules_tick  # noqa: E402


DUE_ROW = (
    "sched-1",                    # id
    "acct-1",                     # account_id
    "Weekly Update",              # name
    "market_snapshot",            # report_type
    "Glendora",                   # city
    None,                         # zip_codes
    7,                            # lookback_days
    "weekly",                     # cadence
    1,                            # weekly_dow
    None,                         # monthly_dom
    9,                            # send_hour
    0,                            # send_minute
    "America/Los_Angeles",        # timezone
    ['{"type":"manual_email","email":"someone@example.com"}'],  # recipients
    True,                         # include_attachment
    None,                         # filters
)


class FakeCursor:
    def __init__(self, world):
        self.world = world
        self._rows = []

    def execute(self, query, params=None):
        text = " ".join(str(query).split())
        self.world["statements"].append(text)

        if "UPDATE schedules s" in text or "WITH due AS" in text:
            # The atomic claim. Served once, so the loop does not spin.
            self._rows = [] if self.world["claimed"] else [DUE_ROW]
            self.world["claimed"] = True
            return

        if "email_verified" in text and "FROM users" in text:
            self._rows = [(self.world["any_verified"],)]
            return

        if "INSERT INTO email_log" in text:
            self.world["email_log"].append(params)
            self._rows = []
            return

        if "INSERT INTO report_generations" in text:
            self.world["generations"] += 1
            self._rows = [("run-1",)]
            return

        if "INSERT INTO schedule_runs" in text:
            self.world["schedule_runs"] += 1
            self._rows = [("schedrun-1",)]
            return

        if "UPDATE schedules" in text:
            self.world["schedule_updates"].append(params)
            self._rows = []
            return

        if "set_config(" in text or "SET LOCAL" in text:
            self._rows = [(None,)]
            return

        if "SELECT COALESCE(default_theme_id" in text or "default_theme_id" in text:
            self._rows = [(1, None)]
            return

        self._rows = []

    def fetchone(self):
        return self._rows[0] if self._rows else None

    def fetchall(self):
        return list(self._rows)

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        return False


class FakeConn:
    def __init__(self, world):
        self.world = world
        self._cur = FakeCursor(world)

    def cursor(self):
        return self._cur

    def commit(self):
        self.world["commits"] += 1

    def rollback(self):
        self.world["rollbacks"] += 1

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        return False


@pytest.fixture
def ticker(monkeypatch):
    def install(*, any_verified, limit_ok=True):
        world = {
            "any_verified": any_verified,
            "claimed": False,
            "statements": [],
            "email_log": [],
            "schedule_updates": [],
            "generations": 0,
            "schedule_runs": 0,
            "commits": 0,
            "rollbacks": 0,
            "dispatched": [],
        }
        monkeypatch.setattr(
            schedules_tick.psycopg, "connect", lambda *a, **kw: FakeConn(world)
        )
        monkeypatch.setattr(
            schedules_tick, "check_usage_limit",
            lambda account_id, product=None: {"can_proceed": limit_ok},
        )
        monkeypatch.setattr(
            schedules_tick, "dispatch_report",
            lambda *a, **kw: world["dispatched"].append(a) or "task-1",
        )
        return world
    return install


# ── the refusal ─────────────────────────────────────────────────────────────

def test_a_due_schedule_on_an_unverified_account_is_not_dispatched(ticker):
    """
    THE REGRESSION, and the one the API gate cannot cover: this schedule already
    exists. Nothing about `active`, `next_run_at` or the plan limit stops it.
    """
    world = ticker(any_verified=False)
    schedules_tick.process_due_schedules()
    assert world["dispatched"] == [], (
        "the ticker dispatched a scheduled send for an account with no "
        "confirmed email address"
    )
    assert world["generations"] == 0, "a report generation row was still created"
    assert world["schedule_runs"] == 0


def test_a_due_schedule_on_a_verified_account_still_goes(ticker):
    """The gate must not break the normal path."""
    world = ticker(any_verified=True)
    schedules_tick.process_due_schedules()
    assert len(world["dispatched"]) == 1, "a verified account's schedule did not send"
    assert world["generations"] == 1


def test_the_skip_advances_next_run_at(ticker):
    """
    Otherwise the same schedule is due again in sixty seconds, forever: a row
    re-examined every tick, a log line every tick, and a refusal record every
    tick. Same reasoning as the usage-limit skip immediately below it.
    """
    world = ticker(any_verified=False)
    schedules_tick.process_due_schedules()
    assert world["schedule_updates"], "next_run_at was never advanced"
    assert world["commits"] >= 1, "the skip was never committed"


def test_the_skip_is_recorded_in_email_log(ticker):
    """
    A skipped tick is otherwise indistinguishable from a tick that never came
    due — `next_run_at` moves either way and no `schedule_runs` row exists,
    because no run was created. The absence of evidence is the defect.
    """
    world = ticker(any_verified=False)
    schedules_tick.process_due_schedules()
    assert world["email_log"], "the skip left no record anywhere"
    assert "blocked_unverified" in str(world["email_log"][0])


def test_the_verification_check_runs_before_the_usage_check(ticker):
    """
    Order, asserted rather than assumed. An unverified account at its plan limit
    should be told the fundamental thing, and the cheaper query should be the
    one that runs first — but the real reason to pin it is that a later edit
    moving the usage check above could leave the verification check unreachable
    on the skip path without any test noticing.
    """
    world = ticker(any_verified=False, limit_ok=False)
    schedules_tick.process_due_schedules()
    assert world["dispatched"] == []
    assert world["email_log"], (
        "an account that is both unverified and over its limit was skipped as "
        "over-limit, leaving no record that it is also unverified"
    )

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
from datetime import datetime, timedelta
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


# ── a feed that honours next_run_at, for the flood question ─────────────────
#
# The fixture above serves the due row ONCE, via a `claimed` flag. That is fine
# for asking what a single tick does and useless for asking what the NEXT tick
# does, because it sidesteps the only thing that decides: whether the skip moved
# the schedule out of the due set.
#
# The question is not hypothetical. If a verification-blocked schedule stayed
# due, the ticker would re-examine it every 60 seconds and write a
# `blocked_unverified` row each time — 1,440 rows a day, per blocked schedule,
# into the table that D-061 through D-065 spent five branches making
# trustworthy. A refusal log that floods is worse than no refusal log, because
# it buries the rows it sits next to.


class StatefulCursor(FakeCursor):
    """
    Same fake, except `schedules.next_run_at` is real state and the claim query
    respects it. The UPDATE the ticker issues actually takes effect here, so a
    second call to `process_due_schedules` sees what the first one left behind.
    """

    def execute(self, query, params=None):
        text = " ".join(str(query).split())

        if "UPDATE schedules s" in text or "WITH due AS" in text:
            self.world["claim_attempts"] += 1
            nxt = self.world["next_run_at"]
            due = nxt is None or nxt <= datetime.utcnow()
            self._rows = [DUE_ROW] if due else []
            return

        if text.startswith("UPDATE schedules") and "next_run_at" in text:
            # (new_next_run_at, schedule_id)
            self.world["next_run_at"] = params[0]
            self.world["schedule_updates"].append(params)
            self._rows = []
            return

        return super().execute(query, params)


@pytest.fixture
def stateful_ticker(monkeypatch):
    def install(*, any_verified, next_run_at=None):
        world = {
            "any_verified": any_verified,
            "claimed": False,
            "claim_attempts": 0,
            "next_run_at": next_run_at,
            "statements": [],
            "email_log": [],
            "schedule_updates": [],
            "generations": 0,
            "schedule_runs": 0,
            "commits": 0,
            "rollbacks": 0,
            "dispatched": [],
        }

        class _Conn(FakeConn):
            def __init__(self, w):
                self.world = w
                self._cur = StatefulCursor(w)

        monkeypatch.setattr(
            schedules_tick.psycopg, "connect", lambda *a, **kw: _Conn(world)
        )
        monkeypatch.setattr(
            schedules_tick, "check_usage_limit",
            lambda account_id, product=None: {"can_proceed": True},
        )
        monkeypatch.setattr(
            schedules_tick, "dispatch_report",
            lambda *a, **kw: world["dispatched"].append(a) or "task-1",
        )
        return world
    return install


def test_a_blocked_schedule_ticked_twice_writes_one_refusal_row(stateful_ticker):
    """
    THE FLOOD QUESTION, asked as behaviour rather than as an assertion about the
    UPDATE statement.

    `test_the_skip_advances_next_run_at` below checks that the write HAPPENS.
    This checks that it WORKS — that the value written actually removes the
    schedule from the due set. Those are different claims, and only the second
    one answers "does this write a row a minute, forever".
    """
    world = stateful_ticker(any_verified=False, next_run_at=None)

    schedules_tick.process_due_schedules()   # due (next_run_at IS NULL)
    schedules_tick.process_due_schedules()   # must no longer be due

    assert world["claim_attempts"] == 2, "the second tick never ran"
    assert len(world["email_log"]) == 1, (
        f"a blocked schedule wrote {len(world['email_log'])} refusal rows across "
        f"two ticks; at 60s per tick that is "
        f"{len(world['email_log']) * 1440} a day, per schedule"
    )


def test_the_skip_leaves_next_run_at_in_the_future(stateful_ticker):
    """
    The property the test above depends on, named separately so a failure says
    which half broke.

    `compute_next_run` adds a week (or a month) when the computed time has
    already passed, so it returns a strictly future instant — but that is a
    claim about a function this skip now relies on for a new reason, and it was
    not previously load-bearing for anything but scheduling.
    """
    world = stateful_ticker(any_verified=False, next_run_at=None)
    schedules_tick.process_due_schedules()

    assert world["next_run_at"] is not None, "next_run_at was left NULL — still due"
    assert world["next_run_at"] > datetime.utcnow() + timedelta(minutes=5), (
        f"next_run_at advanced only to {world['next_run_at']}, which is inside "
        f"the tick interval — the schedule comes straight back"
    )


def test_an_already_due_past_timestamp_is_also_moved_forward(stateful_ticker):
    """
    The realistic case. A schedule blocked on merge does not have a NULL
    `next_run_at` — it has one in the past, possibly well in the past if the
    ticker was down. The `% 7` arithmetic in `compute_next_run` works from NOW,
    not from the stale value, so how far behind it was does not matter.
    """
    world = stateful_ticker(
        any_verified=False,
        next_run_at=datetime.utcnow() - timedelta(days=30),
    )
    schedules_tick.process_due_schedules()
    schedules_tick.process_due_schedules()

    assert len(world["email_log"]) == 1
    assert world["next_run_at"] > datetime.utcnow()


def test_a_verified_schedule_also_advances_and_does_not_re_dispatch(stateful_ticker):
    """
    The control. If the fake's due logic were broken in the permissive
    direction, the flood test above would pass for the wrong reason — so the
    same two ticks are run against an account that CAN send, where one dispatch
    and not two is the correct answer.
    """
    world = stateful_ticker(any_verified=True, next_run_at=None)
    schedules_tick.process_due_schedules()
    schedules_tick.process_due_schedules()

    assert len(world["dispatched"]) == 1, (
        f"{len(world['dispatched'])} dispatches across two ticks — the fake's "
        f"due logic is not honouring next_run_at, which would make the flood "
        f"test meaningless"
    )
    assert world["email_log"] == []


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

    THIS TEST USED TO PASS AGAINST ITS OWN REGRESSION, and the correction is
    the interesting part. It asserted `world["schedule_updates"]` was non-empty
    — "an UPDATE to `schedules` happened". Deleting the `compute_next_run` call
    and the `next_run_at = %s` assignment leaves the lock-clearing
    `UPDATE schedules SET processing_locked_at = NULL` on the same path, which
    lands in the same list. So the regression this test is named after left it
    **green**.

    Fourth instance of §0.6's "a test you have not seen fail is a test you have
    not seen" — and the same shape as D-072's ordering test, which matched an
    unrelated `conn.commit()` on the usage-limit skip path. Found by applying
    the regression, not by rereading the assertion.

    Now asserts the CONTENT of the update. The consequence — that the value
    written removes the schedule from the due set — is
    `test_a_blocked_schedule_ticked_twice_writes_one_refusal_row` above; this
    one only claims the column was targeted.
    """
    world = ticker(any_verified=False)
    schedules_tick.process_due_schedules()
    assert world["commits"] >= 1, "the skip was never committed"
    assert any(
        "next_run_at = %s" in st
        for st in world["statements"]
        if st.startswith("UPDATE schedules")
    ), (
        "no UPDATE set next_run_at; clearing processing_locked_at alone leaves "
        "the schedule due on the next tick"
    )


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

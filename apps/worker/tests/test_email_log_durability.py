"""
A record of a send that happened must survive a later failure.

THE DEFECT THIS EXISTS TO PREVENT (D-065)
-----------------------------------------
`email_log` was written by a single INSERT after the send, on the caller's
cursor, inside the caller's transaction — which commits only at the very end of
the block (`autocommit=False`, one `conn.commit()` ~30 lines later). So the
record of a send that really happened could be undone by a later failure in the
same transaction, or by the process dying before the commit.

The email is already gone. SendGrid accepted it over the network and no database
rollback retracts that. Only the evidence disappeared.

That is why D-064's twenty "never emailed" runs cannot be settled from data at
all: `email_log` answered "is there a record?" and never "was it delivered?",
and those are the same answer only when nothing goes wrong — which is precisely
when nobody is asking.

WHAT THESE TESTS ASSERT, AND HOW
--------------------------------
The property is about *transaction boundaries*, so a test that mocked the
database would test the mock. Instead these run a real Postgres-shaped
conversation against a fake connection that models the one thing that matters:
**writes are visible to others only after commit, and are discarded on
rollback.** The attempt row must survive a rollback of the caller's transaction;
the old code's row did not.

The ordering choice is asserted too. Logging before the send can leave a row
saying 'sending' for an attempt that never reached the provider; logging after
can lose the record entirely. The first is legible, the second is the silence
this exists to end — so 'sending' must be written before the provider call, and
a test pins that rather than leaving it to a comment.
"""
import ast
import re
from pathlib import Path

import pytest


WORKER_SRC = Path(__file__).resolve().parents[1] / "src" / "worker"
TASKS_SRC = (WORKER_SRC / "tasks.py").read_text()


# ── a connection that models commit/rollback visibility ─────────────────────

class FakeCursor:
    def __init__(self, conn):
        self.conn = conn

    def __enter__(self):
        return self

    def __exit__(self, *a):
        return False

    def execute(self, sql, params=None):
        s = " ".join(sql.split())
        if "INSERT INTO email_log" in s:
            self.conn.pending.append(("insert", params))
        elif "UPDATE email_log" in s:
            self.conn.pending.append(("update", params))
        self.conn.log.append(s)

    def fetchone(self):
        return ("00000000-0000-0000-0000-000000000001",)


class FakeConnection:
    """
    Models the only database behaviour under test: uncommitted writes are
    invisible and are lost on rollback.
    """

    def __init__(self, world, autocommit=False):
        self.world = world
        self.autocommit = autocommit
        self.pending = []
        self.log = []

    def cursor(self):
        return FakeCursor(self)

    def __enter__(self):
        return self

    def __exit__(self, *a):
        # psycopg's context manager commits on clean exit, rolls back on error.
        if self.autocommit or a[0] is None:
            self.commit()
        else:
            self.rollback()
        return False

    def commit(self):
        self.world.extend(self.pending)
        self.pending = []

    def rollback(self):
        self.pending = []


# ── the property, exercised ─────────────────────────────────────────────────

def test_the_old_shape_loses_the_record_on_rollback():
    """
    The defect itself, demonstrated. One transaction, write-then-rollback: the
    provider was called, the row is gone. This is the baseline the fix has to
    beat, and it is here so the fix is measured against a real behaviour rather
    than against an assertion about one.
    """
    world = []
    conn = FakeConnection(world, autocommit=False)
    with conn.cursor() as cur:
        cur.execute("INSERT INTO email_log (...) VALUES (...)", ("sent",))
    conn.rollback()          # a later failure anywhere in the same block
    assert world == [], "baseline is wrong — the old shape should lose the row"


def test_the_attempt_row_survives_a_rollback_of_the_callers_transaction():
    """
    THE FIX. The attempt row is written on its own autocommit connection, so
    the caller rolling back — for any reason, at any later point — cannot
    remove it.
    """
    world = []
    log_conn = FakeConnection(world, autocommit=True)
    with log_conn.cursor() as cur:
        cur.execute("INSERT INTO email_log (...) VALUES (..., 'sending')", ("sending",))
    log_conn.commit()

    caller = FakeConnection(world, autocommit=False)
    with caller.cursor() as cur:
        cur.execute("UPDATE schedule_runs SET status = 'completed'")
    caller.rollback()        # the failure that used to erase the delivery record

    assert len(world) == 1, "the attempt row did not survive the caller's rollback"
    assert world[0][0] == "insert"


def test_a_process_death_after_the_send_leaves_a_legible_row_not_silence():
    """
    The gap the chosen ordering accepts: the provider returned, the finalising
    UPDATE never ran. The row must still exist and still say 'sending' — "we
    tried and do not know" — rather than not existing at all.
    """
    world = []
    log_conn = FakeConnection(world, autocommit=True)
    with log_conn.cursor() as cur:
        cur.execute("INSERT INTO email_log (...) VALUES (..., 'sending')", ("sending",))
    log_conn.commit()
    # ... provider called ... process dies here, no UPDATE ...
    assert len(world) == 1
    assert world[0][1] == ("sending",), "the surviving row does not say 'sending'"


# ── the ordering, asserted against the source ───────────────────────────────

def _fn(name):
    return next(
        n for n in ast.walk(ast.parse(TASKS_SRC))
        if isinstance(n, ast.FunctionDef) and n.name == name
    )


def test_the_attempt_is_logged_before_the_provider_is_called():
    """
    Ordering is the decision this ticket had to make, so it is pinned rather
    than left to a comment. Logging after the send fails towards silence, which
    is the defect; logging before fails towards an honest 'sending'.
    """
    fn = _fn("_send_and_log_report_email")
    log_line = send_line = None
    for node in ast.walk(fn):
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
            if node.func.id == "_log_email_attempt":
                log_line = node.lineno
            elif node.func.id == "send_schedule_email":
                send_line = node.lineno
    assert log_line, "the attempt is never logged"
    assert send_line, "send_schedule_email is no longer called here"
    assert log_line < send_line, (
        "the attempt is logged AFTER the provider call — that ordering loses the "
        "record if the process dies in the gap, which is the defect"
    )


@pytest.mark.parametrize("fn_name", ["_log_email_attempt", "_finalise_email_log"])
def test_both_log_writes_use_their_own_connection(fn_name):
    """
    They must not touch the caller's cursor. Using it would put them back inside
    the caller's transaction and reinstate the defect exactly.
    """
    src = ast.get_source_segment(TASKS_SRC, _fn(fn_name)) or ""
    assert "_open_log_connection" in src, f"{fn_name} does not open its own connection"
    assert "conn.cursor()" in src
    assert "cur.execute" not in src.split("def ")[0]


def test_the_log_connection_is_autocommit():
    src = ast.get_source_segment(TASKS_SRC, _fn("_open_log_connection")) or ""
    assert "autocommit=True" in src, (
        "the log connection is not autocommit, so its writes are not durable "
        "until something else commits them"
    )


def test_a_failing_send_still_closes_the_row_out():
    """
    An exception from the provider must not leave the row at 'sending' when we
    do know the outcome. The finalise has to happen before the raise propagates.
    """
    src = ast.get_source_segment(TASKS_SRC, _fn("_send_and_log_report_email")) or ""
    handler = src[src.index("except Exception as send_error"):]
    assert "_finalise_email_log" in handler.split("raise")[0], (
        "the send-failure path re-raises without recording the failure"
    )


def test_the_outer_handler_cannot_double_count():
    """
    admin.py:113 and :197 COUNT(*) email_log. The attempt row plus a second row
    from the outer handler would inflate every email metric in the dashboard —
    so the handler's INSERT must be conditional on no row existing for this run.
    """
    inserts = [
        " ".join(n.value.split())
        for n in ast.walk(ast.parse(TASKS_SRC))
        if isinstance(n, ast.Constant) and isinstance(n.value, str)
        and "INSERT INTO email_log" in n.value and "report_id" in n.value
    ]
    guarded = [s for s in inserts if "NOT EXISTS" in s]
    assert guarded, (
        "no email_log INSERT is guarded against an existing attempt row; "
        "the outer failure handler will double-count"
    )


def test_no_email_log_write_remains_on_the_callers_cursor_in_the_send_path():
    """
    The regression that would silently undo this whole change: someone adds an
    `cur.execute("INSERT INTO email_log …")` back into
    _send_and_log_report_email, putting the record back inside the caller's
    transaction.
    """
    src = ast.get_source_segment(TASKS_SRC, _fn("_send_and_log_report_email")) or ""
    assert not re.search(r"cur\.execute\(\s*\"\"\"\s*INSERT INTO email_log", src), (
        "an email_log write is back on the caller's cursor"
    )

"""
The two invariants that make `task_acks_late` safe to leave on.

WHAT IS *NOT* TESTED HERE, ON PURPOSE
-------------------------------------
There is no assertion that `task_acks_late` is True. That would restate
app.py: the line and the test would say the same thing, and the test would
"pass" for as long as nobody edited it. Whether Celery actually redelivers is
Celery's behaviour, not this repo's, and it was verified by running a worker
against a real broker rather than by reading the docs:

    worker SIGKILLed mid-burst, six tasks       acks_late off  5/6 completed
                                                acks_late on   6/6 completed
    task killed at the 300s hard limit          default        ran once
                                                acks_on_failure_or_timeout
                                                off            ran 16x in 50s
    pool CHILD killed, parent surviving         acks_late on   0/1 completed
    healthy worker, prefetch held past the      acks_late off  no duplicates —
      visibility timeout                                       restore is not
                                                               on a timer
    stranded prefetch, several restarts         acks_late off  returned at a
                                                               LATER start, not
                                                               at the timeout

What a test in this repo *can* protect is the two couplings between files that
nothing at runtime enforces, that are invisible at a glance, and that turn a
correct setting into a live incident. Both are one-line edits away.
"""
import ast
import re
from pathlib import Path


WORKER_SRC = Path(__file__).resolve().parents[1] / "src" / "worker"
APP = (WORKER_SRC / "app.py").read_text()
TASKS = (WORKER_SRC / "tasks.py").read_text()


def _acks_late_enabled():
    return re.search(r'"task_acks_late":\s*True', APP) is not None


# ── invariant 1: late acks require the delivery guard ───────────────────────

def test_acks_late_is_never_on_without_the_duplicate_send_guard():
    """
    THE COUPLING THAT BLOCKED THIS SETTING FOR THE WHOLE OF D-062.

    acks_late means a worker that dies mid-task hands that task back, and the
    task runs again from the top. `generate_report` re-renders happily — same
    R2 key, same report_generations row — but it also RE-SENDS, and an email
    is not retractable. Enabling acks_late without the guard would convert
    every recovered report into a duplicate in someone's inbox.

    Deleting `_already_delivered` would leave this file, app.py and the
    worker all individually plausible. This is the only thing that objects.
    """
    if not _acks_late_enabled():
        return  # the coupling is vacuous while acks are eager
    tree = ast.parse(TASKS)
    send = [
        n for n in ast.walk(tree)
        if isinstance(n, ast.FunctionDef) and n.name == "_send_and_log_report_email"
    ]
    assert len(send) == 1, "the send path was renamed; re-point this invariant"
    called = {
        n.func.id for n in ast.walk(send[0])
        if isinstance(n, ast.Call) and isinstance(n.func, ast.Name)
    }
    assert "_already_delivered" in called, (
        "task_acks_late is on but the send path no longer consults the "
        "duplicate-send guard — every redelivered report would be emailed twice"
    )


# ── invariant 2: the hard limit must stay acknowledged ──────────────────────

def test_a_task_killed_at_the_time_limit_is_still_acknowledged():
    """
    Celery's `task_acks_on_failure_or_timeout` defaults to True, which is the
    only reason `task_time_limit` and `task_acks_late` coexist safely: a task
    killed at the limit is acknowledged and does not come back.

    Setting it False looks like a tightening — "don't ack work that failed" —
    and is instead an infinite redelivery loop. Measured: the same task that
    ran once under the default ran 16 times in 50 seconds with it off.

    The delivery guard does NOT contain that loop. generate_report renders
    before it sends, so a task killed at 300s never reaches the send, never
    writes an email_log row, and `_already_delivered` has nothing to match on.
    It would spin, indefinitely, re-rendering.

    Asserted as absence because that is the failure: the default is correct
    and the danger is someone adding the line.
    """
    if not _acks_late_enabled():
        return
    assert "task_acks_on_failure_or_timeout" not in APP, (
        "task_acks_on_failure_or_timeout is set explicitly. If it is False, a "
        "task killed at task_time_limit is redelivered forever and the "
        "duplicate-send guard cannot stop it — the task dies before the send."
    )


def test_the_time_limit_still_exists_to_bound_a_redelivered_task():
    """
    With late acks, an unbounded task is an unbounded lease. Removing the hard
    limit would let a wedged render hold its message until the broker's
    visibility timeout hands it to a second worker as well.
    """
    assert re.search(r'"task_time_limit":\s*\d+', APP), (
        "task_time_limit was removed while acks are late"
    )

"""
A Celery message cannot be rolled back, so it must not be sent inside a
transaction that can roll back.

THE DEFECT (D-072)
------------------
The ticker used to do this, in this order:

  1. enqueue_report(...)              writes report_generations AND send_task
  2. INSERT INTO schedule_runs
  3. UPDATE schedules SET next_run_at
  4. conn.commit()

The task was handed to Redis at step 1 and the work was recorded at step 4.
Anything that interrupts 2-4 rolls the database back. It does not recall the
message. The worker runs the task and sends the email, and what is left is:

  * a report in a recipient's inbox with **no `schedule_runs` row** — one of
    the signatures D-064 was filed for, reached from the other direction; and
  * `next_run_at` **not advanced**, so the schedule is still due and the next
    tick sixty seconds later enqueues the same send again.

The second is the one that mattered enough to take this before D-071: of the
three redelivery paths found in the acks_late review, this is the only one that
produces a DUPLICATE send rather than a delayed one.

THE FIX IS THE ORDERING, NOT A GUARD
------------------------------------
Record in one transaction, commit, then dispatch. That inverts the residual
failure into the harmless direction — rows committed at 'queued' with no task —
which `sweep_stale_runs` already catches and reports as "never picked up". A
guard on top would have caught the duplicate after the fact; #61 does that
already, and a symptom being caught is not the cause being fixed.

WHAT THESE TESTS ARE
--------------------
Ordering assertions over the source, because ordering is the entire fix and
there is no behaviour to exercise without a live broker and database. They are
written to fail on the specific edit that would undo it: moving the dispatch
back above the commit, or letting either half of the split do the other's job.
"""
import ast
from pathlib import Path

import pytest


WORKER_SRC = Path(__file__).resolve().parents[1] / "src" / "worker"
TICK = (WORKER_SRC / "schedules_tick.py").read_text()
TREE = ast.parse(TICK)


def _fn(name):
    matches = [
        n for n in ast.walk(TREE)
        if isinstance(n, ast.FunctionDef) and n.name == name
    ]
    assert len(matches) == 1, f"expected exactly one {name}(), found {len(matches)}"
    return matches[0]


def _calls(fn, names):
    """{name: [line, ...]} for direct calls to any of `names` inside `fn`."""
    out = {}
    for node in ast.walk(fn):
        if isinstance(node, ast.Call):
            f = node.func
            ident = (
                f.id if isinstance(f, ast.Name)
                else f.attr if isinstance(f, ast.Attribute)
                else None
            )
            if ident in names:
                out.setdefault(ident, []).append(node.lineno)
    return out


# ── the ordering itself ─────────────────────────────────────────────────────

def test_a_commit_separates_writing_the_run_from_dispatching_it():
    """
    THE INVARIANT, and it has to be stated as *between* rather than *before*.

    The obvious phrasing — "some commit precedes the dispatch" — is the §0.6
    rule-seven trap and this test was written that way first. The ticker loop
    has another `conn.commit()` several branches earlier, on the usage-limit
    skip path, so "a commit exists above this line" is satisfied by a commit
    that has nothing to do with this schedule. Moving the dispatch back above
    the real commit left that version PASSING. It was caught by applying the
    regression and re-running, not by reading the assertion.

    The durability boundary is what matters: the generation row is written,
    THEN a commit, THEN the dispatch.
    """
    fn = _fn("process_due_schedules")
    found = _calls(fn, {"dispatch_report", "commit", "create_report_generation"})

    assert "dispatch_report" in found, "the ticker no longer dispatches anything"
    assert "create_report_generation" in found, "the ticker no longer records a run"
    assert found.get("commit"), "the ticker loop no longer commits"

    create = min(found["create_report_generation"])
    dispatch = min(found["dispatch_report"])

    assert create < dispatch, (
        f"the dispatch (line {dispatch}) comes before the run is recorded "
        f"(line {create})"
    )
    between = [c for c in found["commit"] if create < c < dispatch]
    assert between, (
        f"no commit between recording the run (line {create}) and dispatching "
        f"it (line {dispatch}); the commits in this function are "
        f"{sorted(found['commit'])}. A rollback here would leave the Celery "
        f"message live with no row to explain it — D-072."
    )


# ── neither half may do the other's job ─────────────────────────────────────

def test_the_recording_half_dispatches_nothing():
    """
    `create_report_generation` runs inside the caller's transaction. A
    `send_task` in there would be the original defect restored, wearing a new
    function name.
    """
    src = ast.get_source_segment(TICK, _fn("create_report_generation")) or ""
    assert "send_task" not in src, (
        "create_report_generation dispatches to Celery from inside the "
        "caller's transaction — this is exactly D-072"
    )


def test_the_dispatch_half_touches_no_database():
    """
    `dispatch_report` runs AFTER the commit, so anything it writes is outside
    the transaction that was supposed to contain it — unrecoverable in exactly
    the way this split exists to prevent.
    """
    src = ast.get_source_segment(TICK, _fn("dispatch_report")) or ""
    for forbidden in ("cur.execute", "psycopg.connect", "conn.commit", "INSERT", "UPDATE"):
        assert forbidden not in src, (
            f"dispatch_report contains {forbidden!r}; it runs after the commit "
            f"and must not write"
        )


def test_the_recording_half_takes_a_cursor_rather_than_opening_a_connection():
    """
    The bug was not only the order — it was that the generation row committed
    on a connection of its own, so it survived the caller's rollback. Taking a
    cursor is what makes the two atomic.
    """
    fn = _fn("create_report_generation")
    assert fn.args.args and fn.args.args[0].arg == "cur", (
        "create_report_generation no longer takes the caller's cursor first, "
        "so its write may not share the caller's transaction"
    )
    src = ast.get_source_segment(TICK, fn) or ""
    assert "psycopg.connect" not in src, (
        "create_report_generation opens its own connection again — its row "
        "would commit independently and survive a rollback of the rest"
    )


# ── a failed dispatch must be loud, and must not raise ──────────────────────

def test_a_failed_dispatch_is_recorded_and_not_raised():
    """
    By the time a dispatch can fail the run is already committed. Raising would
    only obscure that: the honest outcome is a 'queued' row with no task, which
    the stale sweep reports as "never picked up". But it must not be silent —
    that is the shape this project keeps finding.
    """
    src = ast.get_source_segment(TICK, _fn("dispatch_report")) or ""
    assert "except Exception" in src, "a dispatch failure propagates and hides the committed run"
    handler = src[src.index("except Exception"):]
    assert "logger.error" in handler, "a failed dispatch is not surfaced"
    assert "raise" not in handler, (
        "the dispatch failure is re-raised; the run is already committed and "
        "the exception would misreport it as a tick that did nothing"
    )


# ── the construct, not the symptom (§0.6 rule 4) ────────────────────────────

def test_no_other_code_path_dispatches_before_committing():
    """
    Grep for the construct. Any `send_task` in this module outside
    `dispatch_report` is a second instance of the same defect.
    """
    offenders = [
        node.lineno
        for node in ast.walk(TREE)
        if isinstance(node, ast.Call)
        and isinstance(node.func, ast.Attribute)
        and node.func.attr == "send_task"
    ]
    allowed = {
        n.lineno for n in ast.walk(_fn("dispatch_report"))
        if isinstance(n, ast.Call)
        and isinstance(n.func, ast.Attribute)
        and n.func.attr == "send_task"
    }
    assert set(offenders) <= allowed, (
        f"send_task is called outside dispatch_report at lines "
        f"{sorted(set(offenders) - allowed)}"
    )


@pytest.mark.parametrize("gone", ["enqueue_report"])
def test_the_old_combined_function_is_gone(gone):
    """
    Leaving it behind would leave a working way to make the mistake again,
    and nothing would object.
    """
    names = {n.name for n in ast.walk(TREE) if isinstance(n, ast.FunctionDef)}
    assert gone not in names, (
        f"{gone}() still exists — it writes and dispatches together, which is "
        f"the defect"
    )

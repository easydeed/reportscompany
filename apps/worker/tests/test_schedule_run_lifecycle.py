"""
A schedule run must always reach a terminal status.

THE DEFECTS THESE EXIST TO PREVENT
----------------------------------
58 runs sat at `status='queued'` in production across ten months — in bursts,
with no error, no notification and no timeout. Reports the system was told to
send and did not. The join against `report_generations` split them four ways:

    completed  + pdf     27   the work succeeded; only the status write was lost
    processing + no pdf  18   consumed, killed mid-flight — REAL delivery loss
    failed     + no pdf   8   generation failed correctly, run status not updated
    queued     + no pdf   3   never consumed
    no gen row            1   dangling report_run_id

Two distinct defects produced them:

D-061  Of the three writers of schedule_runs.status, two keyed on
       report_run_id and the third keyed on "the newest queued row for this
       schedule". That third one updates a different row than the run that is
       finishing, so once any row was stranded no later run reclaimed it — the
       35 rows above over work that had completed. Separately, the email
       handler caught its own exception and wrote only email_log, so a crash on
       that path left the run at 'queued' with the traceback nowhere the
       failed-runs table could see it.

D-062  Runs consumed and killed mid-flight, or never consumed at all. By
       definition no code inside the worker runs to record those, so only a
       sweep can catch them.

WHY THESE ARE STRUCTURAL TESTS
------------------------------
The writers live inside `run_report`, a Celery task that needs Postgres, Redis,
SimplyRETS and R2 to execute — none available here, and stubbing all four would
test the stubs. What is testable without them is the property that actually
broke: *which row each writer addresses*. Every writer must key on
report_run_id, because keying on anything else is what stranded 35 rows. That
is a fact about the source, so it is asserted against the parsed source.

The sweep's SQL is asserted the same way, plus the parts of its behaviour that
are pure logic.
"""
import ast
import re
from pathlib import Path

import pytest


WORKER_SRC = Path(__file__).resolve().parents[1] / "src" / "worker"
TASKS = (WORKER_SRC / "tasks.py").read_text()
TICKER = (WORKER_SRC / "schedules_tick.py").read_text()


def _schedule_run_updates(source: str):
    """Every `UPDATE schedule_runs …` statement in a module, as raw SQL."""
    found = []
    for node in ast.walk(ast.parse(source)):
        if isinstance(node, ast.Constant) and isinstance(node.value, str):
            if "UPDATE schedule_runs" in node.value:
                found.append(" ".join(node.value.split()))
    return found


# ── D-061: every writer must address the run that is finishing ──────────────

def test_every_schedule_run_writer_keys_on_report_run_id():
    """
    THE REGRESSION THIS PINS. A writer that selects by schedule_id and
    `status='queued'` updates the newest queued row, not this run's row — which
    is how a stranded row becomes permanent, and how 35 rows accumulated over
    ten months of otherwise-successful sends.
    """
    updates = _schedule_run_updates(TASKS)
    assert updates, "no UPDATE schedule_runs found — did the module move?"
    for sql in updates:
        assert "report_run_id" in sql, (
            "a schedule_runs writer does not key on report_run_id: " + sql
        )
        assert not re.search(r"ORDER BY\s+created_at\s+DESC\s+LIMIT\s+1", sql, re.I), (
            "a writer still selects the newest queued row rather than this run: " + sql
        )


def test_no_writer_relies_on_started_at_being_null():
    """
    `started_at` was never written by anything until this change, so
    `AND started_at IS NULL` silently matched every row that had ever existed.
    A predicate that is always true is worse than no predicate: it reads like a
    guard.
    """
    for sql in _schedule_run_updates(TASKS):
        assert "started_at IS NULL" not in sql or "SET status = 'processing'" in sql, (
            "a writer guards on started_at IS NULL, which matched everything: " + sql
        )


def test_started_at_is_actually_written():
    """The sweep can only distinguish 'never picked up' from 'died running' if
    this is honest."""
    assert re.search(r"UPDATE schedule_runs\s+SET status = 'processing', started_at = NOW\(\)", TASKS), (
        "nothing marks a schedule run as started"
    )


def test_the_email_handler_records_a_terminal_status():
    """
    The handler catches before the outer one sees anything, so without its own
    write the run stays 'queued' and the traceback lives only in email_log —
    which is why a crash on the email path was invisible in the failed-runs
    table.
    """
    # Selected by PROPERTY, not by position. There are two handlers named
    # `email_error` — the scheduled path's and the ad-hoc path's — and the
    # ad-hoc one correctly writes neither table, because an ad-hoc run has no
    # schedule row. This test originally took handlers[0] and passed only
    # because ast.walk happened to reach the scheduled one first; adding the
    # D-063 branch changed the nesting and it silently began asserting against
    # the wrong handler. Picking the one that writes email_log is stable under
    # that kind of edit.
    bodies = [
        ast.get_source_segment(TASKS, h) or ""
        for node in ast.walk(ast.parse(TASKS))
        if isinstance(node, ast.Try) for h in node.handlers
        if h.name == "email_error"
    ]
    assert bodies, "the email exception handler is gone — did the block move?"
    scheduled = [b for b in bodies if "email_log" in b]
    assert len(scheduled) == 1, (
        f"expected exactly one email_error handler that logs to email_log, found {len(scheduled)}"
    )
    assert "UPDATE schedule_runs" in scheduled[0], (
        "the email handler still writes only email_log; a crash there leaves the run queued"
    )


# ── D-062: the sweep ────────────────────────────────────────────────────────

def test_the_ticker_sweeps_stale_runs_every_tick():
    """A sweep that exists but is never called is not a safety net."""
    tree = ast.parse(TICKER)
    assert any(
        isinstance(n, ast.FunctionDef) and n.name == "sweep_stale_runs"
        for n in ast.walk(tree)
    ), "sweep_stale_runs is not defined"
    loop = next(
        n for n in ast.walk(tree)
        if isinstance(n, ast.FunctionDef) and n.name == "run_forever"
    )
    called = {
        n.func.id for n in ast.walk(loop)
        if isinstance(n, ast.Call) and isinstance(n.func, ast.Name)
    }
    assert "sweep_stale_runs" in called, "the ticker never calls the sweep"


def test_the_sweep_only_touches_non_terminal_rows():
    """
    It must never overwrite a run that already reached a real status —
    a sweep that rewrites history is worse than one that misses rows.
    """
    sql = " ".join(_schedule_run_updates(TICKER)[0].split())
    assert "status IN ('queued', 'processing')" in sql, (
        "the sweep does not restrict itself to non-terminal rows: " + sql
    )


def test_the_sweep_respects_a_staleness_window():
    """Without the age condition it would steal runs from a live worker."""
    sql = _schedule_run_updates(TICKER)[0]
    assert "created_at <" in sql and "interval" in sql, (
        "the sweep has no age condition and would mark in-flight runs failed"
    )


def test_the_started_window_clears_the_task_time_limit():
    """
    A task cannot be alive past task_time_limit — Celery hard-kills it — so a
    window above that ceiling is race-free by construction. Below it, the sweep
    could mark a running task failed, which is the D-059 mistake again:
    converting a latency problem into a fabricated failure.

    Read from source rather than imported: schedules_tick pulls in httpx, and
    the rest of this file is deliberately dependency-free.
    """
    window = int(re.search(r'STALE_STARTED_MINUTES = int\(os\.getenv\("STALE_STARTED_MINUTES", "(\d+)"\)\)', TICKER).group(1))
    limit = int(re.search(r'"task_time_limit":\s*(\d+)', (WORKER_SRC / "app.py").read_text()).group(1))
    assert window * 60 > limit, (
        f"started-window {window}m does not clear task_time_limit ({limit}s)"
    )


def test_the_queued_window_is_wide_enough_for_a_burst_to_drain():
    """
    The never-started window is governed by QUEUE DEPTH, not render duration.
    The ticker enqueues every due schedule in one pass — 26 in one pass on
    2026-04-12 — and no --concurrency is configured, so a burst drains roughly
    serially. At the observed p99 of 41s, 26 tasks is ~18 minutes before the
    last one starts.

    A window set from render timings alone (~2 minutes) would mark most of a
    burst failed while the worker was working through it normally. This is the
    assertion that catches that: fabricating failures during a backlog is worse
    than reporting the loss a few minutes later.
    """
    window = int(re.search(r'STALE_QUEUED_MINUTES = int\(os\.getenv\("STALE_QUEUED_MINUTES", "(\d+)"\)\)', TICKER).group(1))
    OBSERVED_P99_SECONDS = 41      # n=1067 completed runs
    LARGEST_OBSERVED_BURST = 26    # 2026-04-12 ticker pass
    assert window * 60 > OBSERVED_P99_SECONDS * LARGEST_OBSERVED_BURST, (
        f"queued-window {window}m is shorter than a serial drain of the largest "
        f"observed burst ({LARGEST_OBSERVED_BURST} x {OBSERVED_P99_SECONDS}s)"
    )


def test_the_started_window_is_measured_from_started_at_not_created_at():
    """
    A task that waited 20 minutes in a backlog and then ran for 40 seconds is
    healthy. Measuring its window from created_at would condemn it for the wait
    — which is the same fabricated-failure trap, arriving by a different route.
    """
    sql = _schedule_run_updates(TICKER)[0]
    assert "started_at IS NOT NULL" in sql and "started_at < NOW()" in sql, (
        "the started-window is not measured from started_at: " + sql
    )


def test_the_sweep_distinguishes_never_started_from_died_running():
    """
    The two causes need different fixes — one is a consumer problem, the other
    is a crash — so collapsing them into one error string loses the signal that
    took a production read to recover.
    """
    sql = _schedule_run_updates(TICKER)[0]
    assert "started_at IS NULL" in sql
    assert "never picked up" in sql
    assert "died while running" in sql


def test_the_sweep_writes_a_terminal_status_rather_than_deleting():
    sql = _schedule_run_updates(TICKER)[0]
    assert "status = 'failed'" in sql
    assert "finished_at = NOW()" in sql
    assert "DELETE" not in sql.upper()


# ── the backfill proposal ───────────────────────────────────────────────────

BACKFILL = Path(__file__).resolve().parents[3] / "scripts" / "reconcile_stranded_schedule_runs.sql"


def test_the_backfill_is_not_a_migration():
    """
    A one-off correction of historical rows must never end up in db/migrations/,
    where the runner would apply it to every environment forever.
    """
    assert BACKFILL.exists(), "the backfill proposal is missing"
    migrations = (Path(__file__).resolve().parents[3] / "db" / "migrations")
    assert not any(
        "reconcile_stranded" in p.name for p in migrations.glob("*.sql")
    ), "the backfill was filed as a migration"


def test_the_backfill_preserves_real_timestamps_for_completed_runs():
    """
    Stamping NOW() would make ten months of history look like it finished on
    the day the backfill ran, which destroys the only evidence of when the
    bursts happened.
    """
    sql = BACKFILL.read_text()
    assert "finished_at = g.generated_at" in sql

# ── D-063: a missing PDF must be an outcome, not a fall-through ─────────────

def test_a_missing_pdf_url_is_recorded_rather_than_skipped():
    """
    The whole email block used to sit behind `if schedule_id and pdf_url:`, so a
    falsy pdf_url skipped the send entirely — no email, no exception, nothing
    logged, and (before D-061) no status update. A scheduled report would read
    as `completed` while the recipient got nothing.

    NOT CURRENTLY REACHABLE, and this test does not pretend otherwise: it
    asserts the guard exists, not that the bug fires. `upload_to_r2` returns a
    public URL, a presigned URL, or a dev stub and raises on failure — it has no
    path returning None or "". The guard is defence against one plausible
    refactor of that function, and the value of pinning it is that the refactor
    would otherwise reintroduce silent non-delivery with nothing in any table to
    show for it.
    """
    fn = next(
        n for n in ast.walk(ast.parse(TASKS))
        if isinstance(n, ast.FunctionDef) and n.name == "generate_report"
    )
    src = ast.get_source_segment(TASKS, fn) or ""
    assert "if schedule_id and not pdf_url:" in src, (
        "the missing-PDF case is not handled explicitly — it falls through the "
        "combined `if schedule_id and pdf_url:` guard and sends nothing, silently"
    )
    branch = src[src.index("if schedule_id and not pdf_url:"):]
    branch = branch[:branch.index("elif schedule_id and pdf_url:")]
    assert "UPDATE schedule_runs" in branch, "the missing-PDF case records no status"
    assert "'failed'" in branch, "the missing-PDF case does not record a failure"
    assert "logger.error" in branch, "the missing-PDF case is not logged"


def test_the_send_path_is_still_reached_when_a_pdf_exists():
    """
    The guard must not have turned the normal case off. Restructuring a
    condition into if/elif is exactly the kind of edit that can drop a branch.
    """
    src = ast.get_source_segment(
        TASKS,
        next(n for n in ast.walk(ast.parse(TASKS))
             if isinstance(n, ast.FunctionDef) and n.name == "generate_report"),
    ) or ""
    assert "elif schedule_id and pdf_url:" in src
    after = src[src.index("elif schedule_id and pdf_url:"):]
    assert "_send_and_log_report_email" in after, (
        "the send is no longer reachable from the pdf_url branch"
    )

"""
A report must not be sent twice, and a refusal must not be silent.

WHY THIS EXISTS (the acks_late blocker)
---------------------------------------
`generate_report` sets `report_generations.status='processing'` unconditionally
with no already-completed check, so a second run of the same task re-renders and
**re-sends**. That is why `acks_late` could not be turned on: a worker that dies
mid-task loses that task (D-062's 18 lost reports), and the obvious fix —
acknowledge late so lost tasks are redelivered — would have turned every
redelivery into a duplicate email.

`acks_late` is on as of `fix/acks-late`, so this guard is now load-bearing
rather than preparatory. Its precondition is asserted in `test_acks_late.py`:
remove `_already_delivered` and that file fails.

(This docstring previously said Celery acks on receipt and that a restart
discards prefetched work. Measured against a real broker, that is wrong —
prefetched messages are unacknowledged in both modes and are redelivered either
way. The default loses only the task that was executing. The conclusion held;
the stated reason did not.)

SCOPE: DELIVERY, NOT THE TASK
-----------------------------
Asked directly: if this task runs twice for the same `report_run_id`, what must
not happen twice?

  rendering    wasteful, harmless. It overwrites its own R2 object, reuses the
               same report_generations row, and check_usage_limit excludes rows
               that have a schedule_runs row — so nothing double-counts.
  sending      not retractable. The recipient has the email.

So the guard sits at the delivery boundary and nowhere else.

THE REFUSAL IS RECORDED, WHICH IS THE POINT
-------------------------------------------
A guard that silently declines would be the seventh instance of the shape this
project keeps finding — correct behaviour, no trace. D-064 established that a
log line is not a record: retention is short and logs cannot be queried beside
the rows they explain. So a refusal writes an `email_log` row of its own.

WHAT THIS DOES NOT BLOCK ON, WHICH IS AS IMPORTANT
--------------------------------------------------
Blocking on a stale `'sending'` row would mean one crashed process permanently
barred an account's reports — §0.6: a guard that refuses input is a guard that
can refuse legitimate input. So `'sending'` blocks only inside a window,
`'failed'` never blocks (a retry is exactly what it is for), and `'suppressed'`
never blocks (nothing was delivered).
"""
import ast
import re
from pathlib import Path

import pytest


WORKER_SRC = Path(__file__).resolve().parents[1] / "src" / "worker"
TASKS = (WORKER_SRC / "tasks.py").read_text()
TREE = ast.parse(TASKS)


def _fn(name):
    matches = [
        n for n in ast.walk(TREE)
        if isinstance(n, ast.FunctionDef) and n.name == name
    ]
    assert len(matches) == 1, f"expected exactly one {name}, found {len(matches)}"
    return matches[0]


def _src(name):
    return ast.get_source_segment(TASKS, _fn(name)) or ""


def _sql_in(name, must_contain):
    """The one SQL literal in `name` containing `must_contain`, asserted unique."""
    stmts = [
        " ".join(n.value.split())
        for n in ast.walk(_fn(name))
        if isinstance(n, ast.Constant) and isinstance(n.value, str)
        and must_contain in n.value
    ]
    assert len(stmts) == 1, (
        f"expected exactly one {must_contain!r} statement in {name}, found {len(stmts)}"
    )
    return stmts[0]


# ── the guard runs, and runs before the send ────────────────────────────────

def test_the_guard_is_checked_before_the_provider_is_called():
    """
    Checking after the send would be theatre. Ordering asserted, not assumed.
    """
    fn = _fn("_send_and_log_report_email")
    lines = {}
    for node in ast.walk(fn):
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
            if node.func.id in ("_already_delivered", "_log_email_attempt", "send_schedule_email"):
                lines[node.func.id] = node.lineno
    assert "_already_delivered" in lines, "the delivery guard is never consulted"
    assert lines["_already_delivered"] < lines["_log_email_attempt"], (
        "the guard runs after the attempt row is written, which would leave a "
        "'sending' row for a send that is about to be refused"
    )
    assert lines["_already_delivered"] < lines["send_schedule_email"]


def test_a_refusal_returns_before_reaching_the_send():
    src = _src("_send_and_log_report_email")
    head = src[:src.index("log_id = _log_email_attempt")]
    assert "return" in head, "a refusal does not short-circuit; the send still happens"


# ── what it blocks on ───────────────────────────────────────────────────────

def test_sent_blocks_unconditionally():
    """No elapsed time makes it safe to send a second copy."""
    sql = _sql_in("_already_delivered", "FROM email_log")
    assert "status = 'sent'" in sql
    sent_clause = sql[sql.index("status = 'sent'"):sql.index("OR (status = 'sending'")]
    assert "interval" not in sent_clause, (
        "the 'sent' check is time-limited, so an old delivery would stop blocking "
        "and the report could be sent twice: " + sent_clause
    )


def test_an_in_flight_send_blocks_but_only_within_a_window():
    """
    A recent 'sending' row is a concurrent duplicate. An old one is debris from
    a process that died in D-065's window — and blocking on it forever would
    mean one crash permanently barred an account's reports.
    """
    sql = _sql_in("_already_delivered", "FROM email_log")
    assert "status = 'sending'" in sql
    assert "interval" in sql and "created_at >" in sql, (
        "the in-flight check has no window, so a stranded 'sending' row would "
        "block that report's delivery permanently"
    )


@pytest.mark.parametrize("status", ["failed", "suppressed"])
def test_non_delivering_statuses_never_block(status):
    """
    'failed' is exactly what a retry is for. 'suppressed' delivered nothing.
    Blocking on either would withhold a report for no reason.
    """
    sql = _sql_in("_already_delivered", "FROM email_log")
    assert f"'{status}'" not in sql, (
        f"'{status}' appears in the blocking query; a {status} send must not "
        f"prevent a retry"
    )


def test_the_window_clears_the_task_time_limit():
    """
    Shorter than task_time_limit and a send that is genuinely in flight could
    be mistaken for debris, letting a real concurrent duplicate through — the
    exact case the window exists to catch.
    """
    window = int(re.search(
        r'DUPLICATE_SEND_WINDOW_MINUTES = int\(os\.getenv\("DUPLICATE_SEND_WINDOW_MINUTES", "(\d+)"\)\)',
        TASKS).group(1))
    limit = int(re.search(r'"task_time_limit":\s*(\d+)', (WORKER_SRC / "app.py").read_text()).group(1))
    assert window * 60 > limit, (
        f"duplicate window {window}m does not clear task_time_limit ({limit}s)"
    )


def test_the_check_fails_open():
    """
    If the check itself cannot run we do not know whether the report was sent.
    Withholding a scheduled report on a database hiccup is worse than a rare
    duplicate — the product's promise is that reports go out.
    """
    src = _src("_already_delivered")
    handler = src[src.index("except Exception"):]
    assert "return None" in handler, (
        "the guard fails closed: a transient database error would withhold the report"
    )


# ── the refusal is observable ───────────────────────────────────────────────

def test_a_refused_send_writes_a_record():
    """
    THE REQUIREMENT. Correct behaviour with no trace is the shape this project
    keeps finding; a refusal that only logs is the seventh instance of it.
    """
    src = _src("_record_refused_send")
    assert "INSERT INTO email_log" in src, "a refusal leaves no durable record"
    assert "duplicate_suppressed" in src, "the refusal is not distinguishable by status"
    assert "reason" in src, "the refusal record does not say why"


def test_the_refusal_record_is_committed_independently():
    """
    Same reasoning as D-065: a record written inside the caller's transaction
    can be rolled back by a later failure, and then the refusal never happened
    as far as the table is concerned.
    """
    src = _src("_record_refused_send")
    assert "_open_log_connection" in src, (
        "the refusal record shares the caller's transaction and is rollback-able"
    )


def test_the_refusal_is_also_logged_loudly():
    """The row is the record; the log is what a person notices."""
    src = _src("_send_and_log_report_email")
    head = src[:src.index("log_id = _log_email_attempt")]
    assert "logger.error" in head, "a refused duplicate is not surfaced in the logs"


def test_a_refusal_does_not_mark_the_run_as_failed():
    """
    From the caller's point of view the report HAS been delivered. Returning a
    failure would make the run record itself as failed_email for a report
    sitting in the recipient's inbox — a false negative in the table D-061 and
    D-062 exist to make trustworthy.
    """
    src = _src("_send_and_log_report_email")
    head = src[:src.index("log_id = _log_email_attempt")]
    returns = re.findall(r"return \((\d+),", head)
    assert returns, "the refusal path does not return a status code"
    assert all(int(code) == 200 for code in returns), (
        f"a refused duplicate returns {returns}, which the caller maps to "
        f"failed_email; it should read as delivered"
    )


# ── the guard must not touch rendering ──────────────────────────────────────

def test_the_guard_is_scoped_to_delivery_only():
    """
    Scope check, asserted rather than promised: nothing in generate_report
    short-circuits the render on an already-completed run. Rendering twice is
    wasteful and harmless; widening the guard to the whole task would change
    behaviour this ticket did not agree to.
    """
    src = _src("generate_report")
    assert "_already_delivered" not in src, (
        "the delivery guard leaked into the task body — scope was delivery only"
    )

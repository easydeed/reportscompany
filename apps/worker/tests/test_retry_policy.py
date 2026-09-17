"""
A retry policy must describe what the code actually does.

THE DEFECT (D-071)
------------------
`generate_report` was decorated `autoretry_for=(Exception,)` with three retries
and exponential backoff, and had never retried once. Its body is a single `try`
whose handler **returns** a dict instead of raising, so nothing ever escaped for
`autoretry_for` to catch. Four lines of resilience config describing behaviour
the code prevented.

`generate_property_report` carries the same decorator and ends its handler with
a bare `raise`. Same intent; one letter of difference in outcome. That task
retries. This one is the one that sends email.

THE ONE ROUTE THAT REACHED IT WAS THE WORST ONE
-----------------------------------------------
The failure handler was itself unguarded — it opened a database connection and
ran four UPDATEs. If that raised, and an unreachable database is exactly what
tends to put a task in its own error handler, the exception escaped, autoretry
fired, and the task re-ran from the top: re-render, re-upload, **re-send**.

A retry path that opens only when the error handler fails is a guard that arms
exactly when everything else has already gone wrong. The inverse of the shape
this project keeps finding: not "silent when it works", but "active only when
nothing else is".

WHY THE DECORATOR WAS REMOVED RATHER THAN MADE TO WORK
-----------------------------------------------------
Because making retries real is not a decorator change. The failure bookkeeping
runs on every attempt, and it:

  * increments `schedules.consecutive_failures`, which AUTO-PAUSES the schedule
    at 3 — so four attempts at one transient failure would pause the schedule;
  * writes terminal status to `report_generations` and `schedule_runs`, so a run
    that failed twice and then succeeded would be recorded as failed.

Both are false negatives in the tables D-061 and D-062 exist to make
trustworthy. The last test here is the one that matters: it fails if someone
turns retries back on without fixing that first.
"""
import ast
import re
from pathlib import Path

import pytest


WORKER_SRC = Path(__file__).resolve().parents[1] / "src" / "worker"
TASKS = (WORKER_SRC / "tasks.py").read_text()
TREE = ast.parse(TASKS)


def _fn(name, tree=None, src=None):
    tree = tree if tree is not None else TREE
    matches = [
        n for n in ast.walk(tree)
        if isinstance(n, ast.FunctionDef) and n.name == name
    ]
    assert len(matches) == 1, f"expected exactly one {name}(), found {len(matches)}"
    return matches[0]


def _decorator_of(name):
    for d in _fn(name).decorator_list:
        text = ast.unparse(d)
        if "celery.task" in text:
            return text
    raise AssertionError(f"{name} is not a celery task")


def _handler_of(name):
    """The `except Exception` handler of the task's outermost try."""
    fn = _fn(name)
    tries = [n for n in fn.body if isinstance(n, ast.Try)]
    assert len(tries) == 1, (
        f"{name} no longer has exactly one top-level try; this file's "
        f"assumptions about its shape need revisiting"
    )
    handlers = tries[0].handlers
    assert len(handlers) == 1, f"{name} has {len(handlers)} top-level handlers"
    return handlers[0]


# ── the decorator tells the truth ───────────────────────────────────────────

def test_generate_report_does_not_claim_retries_it_cannot_perform():
    """
    Either the failures propagate or the decorator goes. What must not exist is
    a decorator describing behaviour the body prevents.
    """
    decorator = _decorator_of("generate_report")
    handler = _handler_of("generate_report")
    reraises = any(
        isinstance(n, ast.Raise) and n.exc is None
        for n in ast.walk(handler)
    )
    claims_retries = "autoretry_for" in decorator

    assert claims_retries == reraises, (
        f"generate_report's decorator and its handler disagree. Decorator: "
        f"{decorator}. Handler re-raises: {reraises}. A task that swallows "
        f"every exception cannot autoretry, and saying it does is D-071."
    )


def test_the_same_disagreement_does_not_exist_in_any_other_worker_task():
    """
    Grep for the construct, not the symptom (§0.6 rule 4). Any task in the
    worker that declares `autoretry_for` and then swallows its exceptions has
    the same defect — `generate_property_report` carries the same decorator and
    is correct only because its handler ends in a bare `raise`.
    """
    offenders = []
    for path in sorted(WORKER_SRC.rglob("*.py")):
        src = path.read_text()
        if "autoretry_for" not in src:
            continue
        tree = ast.parse(src)
        for node in ast.walk(tree):
            if not isinstance(node, ast.FunctionDef):
                continue
            decs = " ".join(ast.unparse(d) for d in node.decorator_list)
            if "autoretry_for" not in decs:
                continue
            tries = [n for n in node.body if isinstance(n, ast.Try)]
            if not tries:
                continue
            reraises = any(
                isinstance(n, ast.Raise)
                for t in tries for h in t.handlers for n in ast.walk(h)
            )
            if not reraises:
                offenders.append(f"{path.name}:{node.lineno} {node.name}")
    assert not offenders, (
        f"these tasks declare autoretry_for but never let an exception escape, "
        f"so they cannot retry: {offenders}"
    )


# ── the perverse route is closed ────────────────────────────────────────────

def test_the_failure_handler_cannot_raise():
    """
    THE ROUTE THAT RE-SENT REPORTS. Every call the handler makes at its own
    level must be inside a `try`, or be to a function that guards itself — and
    the second half of that is checked too, below, rather than assumed.
    """
    handler = _handler_of("generate_report")
    guarded_lines = {
        n.lineno
        for stmt in handler.body if isinstance(stmt, ast.Try)
        for n in ast.walk(stmt) if hasattr(n, "lineno")
    }

    # No exemptions. An earlier version of this test exempted
    # `_send_failure_notification` as "guards itself" — and then the companion
    # test checking that claim found its first three statements sit OUTSIDE its
    # own try. The exemption was removed by guarding the call site instead,
    # which is cheaper than being right about another function's internals.
    TRIVIAL = {"get", "str", "format"}

    unguarded = []
    for stmt in handler.body:
        for node in ast.walk(stmt):
            if not isinstance(node, ast.Call):
                continue
            name = getattr(node.func, "id", None) or getattr(node.func, "attr", None)
            if name in TRIVIAL:
                continue
            if node.lineno not in guarded_lines:
                unguarded.append(f"{name} (line {node.lineno})")

    assert not unguarded, (
        f"these calls in the failure handler are not inside a try: {unguarded}. "
        f"An exception here escapes the task — which, with a retry decorator, "
        f"re-sends the report."
    )


def test_recording_the_failure_is_attempted_and_its_own_failure_is_logged():
    """
    Guarding must not become swallowing. A run that failed, and then failed to
    record that it failed, has to be visible somewhere or it is the seventh
    instance of the shape again.
    """
    handler = _handler_of("generate_report")
    src = ast.get_source_segment(TASKS, handler) or ""
    assert "_record_generation_failure" in src, (
        "the handler no longer records terminal state; a failed run would sit "
        "mid-flight until the stale sweep found it"
    )
    tries = [n for n in handler.body if isinstance(n, ast.Try)]
    assert tries, "the bookkeeping call is not guarded"
    for t in tries:
        for h in t.handlers:
            h_src = ast.get_source_segment(TASKS, h) or ""
            assert "logger." in h_src, (
                "a guard in the failure handler discards its exception "
                "silently: " + h_src[:120]
            )


def test_the_handler_still_returns_rather_than_falling_through():
    handler = _handler_of("generate_report")
    assert any(isinstance(n, ast.Return) for n in ast.walk(handler)), (
        "the failure handler no longer returns a result; the caller would see "
        "None and could not distinguish failure from success"
    )


# ── the coupling that guards the next change ────────────────────────────────

def test_retries_are_not_enabled_while_the_bookkeeping_counts_every_attempt():
    """
    THE ONE THAT MATTERS LATER.

    Turning `autoretry_for` back on is a one-line edit that looks harmless and
    is not. `_record_generation_failure` runs on every attempt: it increments
    `schedules.consecutive_failures`, which auto-pauses the schedule at 3, so
    four attempts at a single transient failure would pause it. It also writes
    terminal status to `report_generations` and `schedule_runs`, so a run that
    failed twice and then succeeded reads as failed.

    If someone enables retries, this fails until the bookkeeping learns the
    difference between "this attempt failed" and "the task failed".
    """
    if "autoretry_for" not in _decorator_of("generate_report"):
        return  # nothing to couple to yet

    src = ast.get_source_segment(TASKS, _fn("_record_generation_failure")) or ""
    aware_of_attempts = any(
        marker in src
        for marker in ("max_retries", "request.retries", "is_last_attempt", "final_attempt")
    )
    assert aware_of_attempts, (
        "retries are enabled on generate_report but _record_generation_failure "
        "still runs unconditionally on every attempt: consecutive_failures "
        "would increment up to 4x per logical failure (auto-pause fires at 3), "
        "and schedule_runs would be marked failed for runs that later succeed"
    )


@pytest.mark.parametrize("threshold_marker", ["consecutive_failures >= 3"])
def test_the_auto_pause_threshold_is_where_this_test_thinks_it_is(threshold_marker):
    """
    The argument above rests on the schedule pausing at 3. If that number or
    its shape changes, the reasoning in this file needs rechecking rather than
    silently continuing to cite a threshold that moved.
    """
    src = ast.get_source_segment(TASKS, _fn("_record_generation_failure")) or ""
    assert threshold_marker in src, (
        f"the auto-pause threshold is no longer {threshold_marker!r}; D-071's "
        f"reasoning about retries quadrupling the count needs revisiting"
    )

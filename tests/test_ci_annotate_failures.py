"""The CI failure reporter, including the case where there is nothing to report.

D-191's remedy, gated. The reporter exists because a red check carried no
information for two weeks; a reporter that itself goes quiet, or that dresses
up a collection error as a list of failed tests, would be the same defect one
level out.

THE POSITIVE CONTROL IS THE IMPORTANT TEST HERE. `test_a_real_pytest_tail_is
_matched` feeds it output captured from this repository's own suite, because
the extractor is a pattern match against another tool's human-readable output
and the way it breaks is pytest changing the wording — which no amount of
hand-written fixture will notice.
"""
import subprocess
import sys
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[1]
SCRIPT = REPO / "scripts/ci_annotate_failures.py"
sys.path.insert(0, str(REPO / "scripts"))

from ci_annotate_failures import (  # noqa: E402
    encode, failure_count, failure_lines, outcome_counts, report,
)

GREEN = """============================= test session starts ==============================
collected 2901 items
.......................................................................
2901 passed, 67 skipped, 20 xfailed, 12 warnings in 372.56s (0:06:12)
"""

RED = """=================================== FAILURES ===================================
____________________________ test_one ____________________________
    assert 1 == 2
E   AssertionError
=========================== short test summary info ============================
FAILED tests/test_a.py::test_one - AssertionError: assert 1 == 2
FAILED apps/worker/tests/test_b.py::test_two - KeyError: 'theme'
ERROR apps/api/tests/test_c.py
SKIPPED [1] apps/api/tests/test_d.py: needs a database
XFAIL apps/worker/tests/test_e.py::test_five - D-183
3 failed, 2898 passed, 67 skipped in 372.56s (0:06:12)
"""

COLLECTION_ERROR = """============================= test session starts ==============================
ImportError while loading conftest '/home/runner/work/x/apps/api/tests/conftest.py'.
apps/api/tests/conftest.py:7: in <module>
    import psycopg
E   ModuleNotFoundError: No module named 'psycopg'
"""


def test_a_green_run_is_reported_as_nothing():
    """The half that keeps this from becoming noise.

    A reporter that annotates every run makes the annotation meaningless, which
    is D-142's own lesson about the `pages_dropped` line: the PRESENCE of the
    message has to be the signal.
    """
    assert report(GREEN) == ""


def test_xfailed_is_not_read_as_failed():
    """The bug this file's green-run test caught, pinned.

    The first version of the guard asked `"failed" not in counts`, and this
    repository's GREEN counts line is
    `2901 passed, 67 skipped, 20 xfailed, 12 warnings` — **"xfailed" ends in
    "failed"**, so every passing run reported itself red. §0.6's
    substring-is-not-a-construct rule, instantiated inside the script written
    to make a red check say something.

    Both directions, because a tokeniser that counts nothing is the other way
    to pass this.
    """
    assert failure_count("2901 passed, 67 skipped, 20 xfailed, 12 warnings") == 0
    assert failure_count("20 xpassed, 3 xfailed") == 0
    assert failure_count("3 failed, 2898 passed") == 3
    assert failure_count("1 failed, 5 errors, 10 passed") == 6
    assert failure_count("1 error in 0.10s") == 1
    assert outcome_counts("3 failed, 2898 passed, 20 xfailed") == {
        "failed": 3, "passed": 2898, "xfailed": 20}


def test_the_failed_and_error_lines_are_named():
    body = report(RED)
    assert "FAILED tests/test_a.py::test_one" in body
    assert "ERROR apps/api/tests/test_c.py" in body
    assert "3 failed, 2898 passed" in body


def test_skips_and_xfails_are_not_reported_as_failures():
    """`SKIPPED` and `XFAIL` sit in the same summary block.

    This suite has 67 skips and 20 strict xfails on a GREEN run — a reporter
    that swept the whole block would announce 87 failures on a passing build.
    """
    body = report(RED)
    assert "SKIPPED" not in body
    assert "XFAIL" not in body
    assert len(failure_lines(RED)) == 3


def test_a_run_with_no_summary_says_that_is_what_happened():
    """The case where `exit code 1` is least informative and most likely."""
    body = report(COLLECTION_ERROR)
    assert "pytest wrote no failure summary" in body
    assert "not a list of failed tests" in body
    assert "ModuleNotFoundError" in body


def test_the_list_is_capped_and_says_it_was():
    many = ("=========================== short test summary info ===========================\n"
            + "\n".join(f"FAILED tests/test_{i}.py::test_x - boom" for i in range(50)))
    body = report(many, max_lines=10)
    assert body.count("FAILED") == 10
    assert "and 40 more" in body, (
        "a cap that does not say it capped turns 50 failures into a list of 10 "
        "that reads as complete"
    )


def test_newlines_and_percent_are_encoded_for_the_workflow_command():
    """A raw newline ends the workflow command, so everything after it is lost.

    `%` first: encoding it after the others would escape their escapes.
    """
    assert encode("a\nb") == "a%0Ab"
    assert encode("100%") == "100%25"
    assert encode("a%\nb") == "a%25%0Ab"
    assert "\n" not in encode(report(RED))


def test_the_command_is_emitted_as_one_annotation(tmp_path):
    """One `::error::` line, because GitHub caps annotations per step at ten."""
    f = tmp_path / "out.txt"
    f.write_text(RED, encoding="utf-8")
    proc = subprocess.run([sys.executable, str(SCRIPT), str(f)],
                          capture_output=True, text=True, check=True)
    lines = [l for l in proc.stdout.split("\n") if l.strip()]
    assert len(lines) == 1, lines
    assert lines[0].startswith("::error title=Test failures::")


def test_a_missing_file_is_reported_rather_than_crashing(tmp_path):
    proc = subprocess.run([sys.executable, str(SCRIPT), str(tmp_path / "nope.txt")],
                          capture_output=True, text=True, check=True)
    assert "does not exist" in proc.stdout
    assert proc.returncode == 0


def test_the_reporter_never_fails_the_build(tmp_path):
    """It runs on an already-red build. A reporter that can fail adds a second
    failure mode to the thing it was meant to explain."""
    for content in (GREEN, RED, COLLECTION_ERROR, "", "\x00\xff garbage"):
        f = tmp_path / "out.txt"
        f.write_text(content, encoding="utf-8", errors="replace")
        proc = subprocess.run([sys.executable, str(SCRIPT), str(f)],
                              capture_output=True, text=True)
        assert proc.returncode == 0, proc.stderr


def test_a_real_pytest_tail_is_matched():
    """THE POSITIVE CONTROL: output from this repository's own pytest.

    The extractor matches another tool's human-readable output, so the way it
    breaks is pytest changing its wording — and a hand-written fixture cannot
    notice that. This runs a deliberately failing test and reads the real
    summary.
    """
    proc = subprocess.run(
        [sys.executable, "-m", "pytest", "-q", "-p", "no:randomly",
         "--no-header", "-x",
         f"--rootdir={REPO}", "-c", str(REPO / "pytest.ini"),
         str(Path(__file__).parent / "fixtures" / "_ci_annotate_probe.py")],
        capture_output=True, text=True, cwd=REPO)
    body = report(proc.stdout)
    assert "_ci_annotate_probe.py::test_this_fails" in body, (
        f"the extractor did not find the failure in real pytest output:\n"
        f"{proc.stdout[-2000:]}"
    )
    assert "1 failed" in body


def _test_job_steps():
    """The `test` job's steps, PARSED.

    Not a substring search of the file. The first version of the two tests
    below asked `"ci_annotate_failures.py" in wf` and `"if: failure()" in wf`,
    and both strings are in this workflow's COMMENTS — explaining the step —
    so both assertions passed with the step deleted. Two applied regressions
    caught it (`scripts/regressions/ci_annotate_failures.json`, mutations 2 and
    3) and neither fired on the first run.

    That is §0.6's substring-is-not-a-construct rule committed twice inside the
    test file for the script whose own version of that bug — "xfailed" matching
    "failed" — is pinned above. A comment is not a step; YAML says which is
    which, and `test_ci_table_matches_workflows.py` already parses these files
    for the same reason.
    """
    import yaml
    d = yaml.safe_load((REPO / ".github/workflows/backend-tests.yml")
                       .read_text(encoding="utf-8"))
    return d["jobs"]["test"]["steps"]


def _step_named(name):
    for i, step in enumerate(_test_job_steps()):
        if step.get("name") == name:
            return i, step
    raise AssertionError(f"backend-tests.yml has no step named {name!r}")


def test_the_test_step_captures_its_output_without_swallowing_the_exit_code():
    """`set -o pipefail` is the load-bearing half.

    Piping pytest into `tee` makes the step take TEE's exit code, which is 0
    whatever pytest did — so without pipefail a red suite reports green, which
    is a worse defect than the one this change fixes.
    """
    _, step = _step_named("Run tests")
    run = step["run"]
    assert "| tee pytest-output.txt" in run, (
        "the test step no longer writes its output to a file, so the reporter "
        "below has nothing to read"
    )
    assert "set -o pipefail" in run, (
        "the test step pipes pytest into `tee` WITHOUT pipefail, so the step "
        "takes tee's exit code and a red suite reports green"
    )


def test_the_workflow_runs_the_reporter_only_on_failure():
    """The step has to exist, run the script, be gated, and come after the
    tests — asserted on the parsed steps, so a comment cannot satisfy it."""
    steps = _test_job_steps()
    reporters = [(i, s) for i, s in enumerate(steps)
                 if "ci_annotate_failures.py" in (s.get("run") or "")]
    assert len(reporters) == 1, (
        f"expected exactly one step running the reporter, found "
        f"{[s.get('name') for _, s in reporters]} — a red run still says only "
        f"`exit code 1` if there are none"
    )
    index, step = reporters[0]
    assert step.get("if") == "failure()", (
        f"the reporter's `if` is {step.get('if')!r}. It must be `failure()`: "
        f"annotating a green run makes the annotation meaningless, which is "
        f"the same reason D-142's `pages_dropped` line is emitted only on a "
        f"drop."
    )
    test_index, _ = _step_named("Run tests")
    assert index > test_index, (
        "the reporter runs before the tests, so it reads the previous run's "
        "output or nothing at all"
    )

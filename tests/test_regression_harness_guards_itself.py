"""The harness that proves gates fire, proved to fire.

`scripts/apply_regressions.py` exists because three hand-run regressions
misreported in two days — stale bytecode, a backup that reverted its own edit,
and a `sed` no-op on a phrase spanning a line break. All three failed safe by
luck, and the last is D-087's own harness defect committed by its author.

A harness whose whole job is "do not trust a green you have not earned" cannot
itself be trusted on the strength of having been written carefully. So each
guard is asserted, and the two outcomes that must never be confused — a gate
that did not fire (exit 1) and a harness that could not prove its state
(exit 2) — are asserted by exit code.
"""
import importlib.util
import json
import signal
import subprocess
import sys
import time
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parent.parent
HARNESS = REPO / "scripts/apply_regressions.py"
SPECS = REPO / "scripts/regressions"


def _load():
    spec = importlib.util.spec_from_file_location("_apply_regressions", HARNESS)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@pytest.fixture(scope="module")
def harness():
    return _load()


# ─────────────────────────────────────────────────────────────────────────────
# The three misfires, each as a test
# ─────────────────────────────────────────────────────────────────────────────

def test_a_missing_anchor_is_an_error_and_not_a_pass(harness, tmp_path):
    """Misfire (3), the one that matters most.

    `sed` matched nothing, exited zero, and the gate passed on an unmodified
    file. Here the same mutation cannot run at all.
    """
    target = tmp_path / "doc.md"
    target.write_text("a phrase that\nspans a line break\n", encoding="utf-8")
    with pytest.raises(harness.MutationError) as exc:
        harness.apply_mutation(target, "a phrase that spans a line break", "x")
    assert "appears 0 times" in str(exc.value)
    assert target.read_text(encoding="utf-8").startswith("a phrase that")


def test_an_ambiguous_anchor_is_an_error(harness, tmp_path):
    """A mutation applied to one of three identical sites has no known shape."""
    target = tmp_path / "f.py"
    target.write_text("x = 1\nx = 1\nx = 1\n", encoding="utf-8")
    with pytest.raises(harness.MutationError) as exc:
        harness.apply_mutation(target, "x = 1", "x = 2")
    assert "appears 3 times" in str(exc.value)


def test_a_restore_that_does_not_land_is_an_error(harness, tmp_path):
    """Misfire (2). The restore is verified, not assumed.

    Simulated by handing `restore` a target whose write cannot take effect —
    a directory, which raises on write. The point under test is that the
    function does not return quietly when the file does not end up matching.
    """
    target = tmp_path / "adir"
    target.mkdir()
    with pytest.raises((harness.MutationError, IsADirectoryError, PermissionError)):
        harness.restore(target, "whatever")


def test_the_bytecode_clear_actually_removes_caches(harness, tmp_path):
    """Misfire (1). Same size, same second, stale `.pyc`.

    `clear_bytecode` walks the repo, so this asserts it finds and removes a
    `__pycache__` placed inside it rather than testing a tmp_path copy of the
    logic.
    """
    planted = REPO / "scripts" / "__pycache__"
    planted.mkdir(exist_ok=True)
    (planted / "sentinel.pyc").write_bytes(b"stale")
    assert (planted / "sentinel.pyc").exists()
    harness.clear_bytecode()
    assert not planted.exists() or not (planted / "sentinel.pyc").exists()


# ─────────────────────────────────────────────────────────────────────────────
# The two outcomes that must not be confused
# ─────────────────────────────────────────────────────────────────────────────

def test_a_mutation_that_does_not_fire_exits_1(harness, tmp_path, capsys):
    """A landed mutation that no gate notices is a finding, not a pass."""
    target = tmp_path / "unguarded.txt"
    target.write_text("ORIGINAL\n", encoding="utf-8")
    spec = tmp_path / "spec.json"
    spec.write_text(json.dumps([{
        "name": "lands, and nothing guards it",
        "file": str(target),
        "old": "ORIGINAL", "new": "MUTATED",
        # A gate chosen to be INERT with respect to the mutation, and to be
        # unconditionally green. The first version named
        # `test_the_spec_files_are_well_formed`, which is a real gate — and
        # when a recorded anchor moved, that gate started failing, the mutation
        # "fired", and THIS test failed for a reason that had nothing to do
        # with it. A self-test that borrows another test's status inherits its
        # failures. `--collect-only` on one node runs no assertions at all.
        "test": "--collect-only -q tests/test_regression_harness_guards_itself.py",
    }]), encoding="utf-8")
    # `file` is absolute here, so ROOT / abs == abs. Deliberate: the spec
    # format takes repo-relative paths, and an absolute one still resolves.
    assert harness.main([str(spec)]) == 1
    out = capsys.readouterr().out
    assert "DID NOT FIRE" in out
    assert target.read_text(encoding="utf-8") == "ORIGINAL\n", \
        "the restore must land even when the mutation did not fire"


def test_a_harness_error_is_not_a_gate_result(harness, tmp_path):
    """Exit 2, distinct from 1. It says nothing about the gate."""
    spec = tmp_path / "spec.json"
    spec.write_text(json.dumps([{
        "name": "anchor not present",
        "file": "scripts/apply_regressions.py",
        "old": "a string that is certainly not in that file",
        "new": "x",
        "test": "tests/test_regression_harness_guards_itself.py",
    }]), encoding="utf-8")
    with pytest.raises(harness.MutationError):
        harness.main([str(spec)])


def test_an_empty_spec_is_refused(harness, tmp_path):
    """A run of nothing reports 0/0 and would otherwise exit 0."""
    spec = tmp_path / "spec.json"
    spec.write_text("[]", encoding="utf-8")
    with pytest.raises(harness.MutationError):
        harness.main([str(spec)])


# ─────────────────────────────────────────────────────────────────────────────
# The recorded specs
# ─────────────────────────────────────────────────────────────────────────────

def test_the_spec_files_are_well_formed():
    """Every recorded mutation names a file that exists and a real anchor.

    §0.6: a recorded measurement whose subject moved describes nothing. A spec
    pointing at a renamed file is a regression nobody can re-run, and it would
    only surface as a harness error on the next person's run.
    """
    specs = sorted(SPECS.glob("*.json"))
    assert specs, f"no recorded regressions in {SPECS.relative_to(REPO)}"
    problems = []
    for path in specs:
        entries = json.loads(path.read_text(encoding="utf-8"))
        assert isinstance(entries, list) and entries, f"{path.name} is empty"
        for i, entry in enumerate(entries, 1):
            where = f"{path.name}[{i}] {entry.get('name', '?')[:50]}"
            missing = {"file", "old", "new", "test"} - set(entry)
            if missing:
                problems.append(f"{where}: missing keys {sorted(missing)}")
                continue
            target = REPO / entry["file"]
            if not target.is_file():
                problems.append(f"{where}: {entry['file']} does not exist")
                continue
            count = target.read_text(encoding="utf-8").count(entry["old"])
            if count != 1:
                problems.append(
                    f"{where}: anchor appears {count} times in "
                    f"{entry['file']} (needs exactly 1)")
            if entry["new"] == entry["old"]:
                problems.append(f"{where}: `new` equals `old`")
    assert not problems, (
        "recorded regressions that can no longer run:\n  "
        + "\n  ".join(problems)
        + "\n\nA mutation whose anchor has moved is a regression nobody can "
          "re-run, and it only surfaces on the next person's run."
    )


def test_the_predecessor_is_left_in_place():
    """`scripts/regress.py` is not replaced by this, and was nearly deleted.

    It was overwritten in the course of writing the generalised harness and
    restored from `origin/main`. It also restores `golden/themes.json`, which no
    spec expresses yet, so removing it would lose that. Consolidating the two is
    a decision for whoever is next in that file.
    """
    predecessor = REPO / "scripts/regress.py"
    assert predecessor.is_file()
    assert "themes.py" in predecessor.read_text(encoding="utf-8")


# ─────────────────────────────────────────────────────────────────────────────
# D-196 — the failure that corrupts everything measured after it
#
# The harness was piped to `head -40`. head exited, the next `print()` raised
# BrokenPipeError, and the process died AFTER writing the mutation and BEFORE
# the restore, with no exit code, because stdout was already gone. These run
# the harness as a real subprocess, because a signal and a dead pipe are
# properties of a process and cannot be asserted in-process.
#
# The kill window is found by POLLING FOR THE SENTINEL rather than by sleeping
# a guessed interval: the sentinel exists exactly between "about to mutate" and
# "restore verified", so waiting for it is the deterministic way to be inside
# the window this entry is about.
# ─────────────────────────────────────────────────────────────────────────────

SENTINEL = REPO / ".regress-mutation-in-progress.json"


def _slow_spec(tmp_path, n=12):
    """A spec whose gate is green and inert, long enough to be interrupted."""
    targets = []
    muts = []
    for i in range(n):
        t = tmp_path / f"f{i}.txt"
        t.write_text(f"ORIGINAL {i}\n", encoding="utf-8")
        targets.append(t)
        muts.append({
            "name": f"m{i}",
            "file": str(t),
            "old": f"ORIGINAL {i}",
            "new": f"MUTATED {i}",
            "test": ("--collect-only -q "
                     "tests/test_regression_harness_guards_itself.py"),
        })
    spec = tmp_path / "spec.json"
    spec.write_text(json.dumps(muts), encoding="utf-8")
    return spec, targets


def _launch(spec, stdout=subprocess.DEVNULL, shell_cmd=None):
    if shell_cmd:
        return subprocess.Popen(shell_cmd, cwd=REPO, shell=True)
    # stderr is KEPT, not discarded. `_wait_for_sentinel` has timed out twice
    # in a full-suite run and never once in isolation, and both times the
    # failure said only "never entered a mutation window" — which is a
    # symptom, not a diagnosis. Whatever the next one is, its reason will be
    # in the message.
    return subprocess.Popen(
        [sys.executable, str(HARNESS), str(spec)],
        cwd=REPO, stdout=stdout, stderr=subprocess.PIPE, text=True)


def _wait_for_sentinel(proc, timeout=30.0):
    """Wait until the harness is inside a mutation. Returns a reason on
    failure rather than a bare False, so a flake diagnoses itself."""
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        if SENTINEL.exists():
            return None
        if proc.poll() is not None:
            err = ""
            try:
                err = (proc.stderr.read() or "")[-600:] if proc.stderr else ""
            except Exception:
                pass
            return (f"the harness exited with {proc.returncode} before writing a "
                    f"sentinel. stderr:\n{err}")
        time.sleep(0.01)
    return f"no sentinel appeared within {timeout}s and the harness is still running"


def _enter_mutation_window(proc):
    reason = _wait_for_sentinel(proc)
    if reason:
        proc.kill()
        raise AssertionError(reason)


@pytest.fixture(autouse=True)
def _no_stale_sentinel():
    """Never let one of these tests leave the real repo's sentinel behind.

    If it survived, every later run of the harness would refuse to start —
    which is the correct behaviour and a terrible thing to inherit from a test.
    """
    yield
    SENTINEL.unlink(missing_ok=True)


def test_a_dead_consumer_does_not_abort_the_cycle(tmp_path):
    """The reported bug, reproduced through a real pipe to `head`.

    Before the fix this left the mutated file on disk. The assertion is about
    the TREE, not about the output: nothing this harness prints is worth a
    corrupted working copy.
    """
    spec, targets = _slow_spec(tmp_path, n=4)
    cmd = f"{sys.executable} {HARNESS} {spec} 2>&1 | head -2"
    proc = _launch(spec, shell_cmd=cmd)
    proc.wait(timeout=120)
    for i, t in enumerate(targets):
        assert t.read_text(encoding="utf-8") == f"ORIGINAL {i}\n", (
            f"{t.name} was left mutated after the consumer closed the pipe"
        )
    assert not SENTINEL.exists(), (
        "the run completed but left its sentinel, so the next run would refuse"
    )


def test_sigterm_mid_mutation_still_restores_and_exits_2(tmp_path):
    """`SIGTERM`'s default disposition kills the process outright, skipping
    every `finally`. It is turned into an exception for exactly this reason."""
    spec, targets = _slow_spec(tmp_path)
    proc = _launch(spec)
    _enter_mutation_window(proc)
    proc.send_signal(signal.SIGTERM)
    assert proc.wait(timeout=120) == 2, (
        "a harness killed mid-mutation has said nothing about any gate, which "
        "is exit 2 and not exit 1"
    )
    for i, t in enumerate(targets):
        assert t.read_text(encoding="utf-8") == f"ORIGINAL {i}\n"
    assert not SENTINEL.exists()


def test_sigkill_leaves_a_sentinel_and_the_next_run_refuses_to_start(tmp_path):
    """The one case code in this process cannot cover.

    No handler runs, no `finally` runs, and the mutation stays on disk. What
    must happen instead is that the NEXT run declines to measure anything
    against a tree it cannot vouch for — and that `--restore` recovers it only
    after proving the file is still the text this harness wrote.
    """
    spec, targets = _slow_spec(tmp_path)
    proc = _launch(spec)
    _enter_mutation_window(proc)
    proc.kill()
    proc.wait(timeout=30)

    assert SENTINEL.exists(), "a SIGKILL left nothing to recover from"
    record = json.loads(SENTINEL.read_text(encoding="utf-8"))
    victim = Path(record["file"])
    assert victim.read_text(encoding="utf-8") == record["mutated"]

    # A later run must do NOTHING while that is true.
    second = subprocess.run(
        [sys.executable, str(HARNESS), str(spec)],
        cwd=REPO, capture_output=True, text=True)
    assert second.returncode == 2, (
        f"a run started against a tree holding someone else's mutation: "
        f"{second.returncode}"
    )
    assert "left a mutation applied" in second.stderr
    assert victim.read_text(encoding="utf-8") == record["mutated"], (
        "the refusing run modified the file it refused to measure against"
    )

    # And --restore puts it back.
    third = subprocess.run(
        [sys.executable, str(HARNESS), "--restore"],
        cwd=REPO, capture_output=True, text=True)
    assert third.returncode == 0, third.stderr
    assert victim.read_text(encoding="utf-8") == record["original"]
    assert not SENTINEL.exists()
    for i, t in enumerate(targets):
        assert t.read_text(encoding="utf-8") == f"ORIGINAL {i}\n"


def test_restore_refuses_when_the_file_moved_on_after_the_mutation(tmp_path):
    """Misfire (2), one level up: a recovery source on disk can be older than a
    legitimate later edit. `--restore` holds the MUTATED text too, so it can
    prove the file is still the one it broke before writing to it."""
    target = tmp_path / "moved-on.txt"
    target.write_text("ORIGINAL\n", encoding="utf-8")
    SENTINEL.write_text(json.dumps({
        "file": str(target),
        "original": "SOMETHING OLDER\n",
        "mutated": "WHAT THE HARNESS WROTE\n",
        "pid": 1,
    }), encoding="utf-8")

    out = subprocess.run(
        [sys.executable, str(HARNESS), "--restore"],
        cwd=REPO, capture_output=True, text=True)
    assert out.returncode == 2
    assert "refused" in out.stderr
    assert target.read_text(encoding="utf-8") == "ORIGINAL\n", (
        "--restore discarded an edit made after the mutation"
    )

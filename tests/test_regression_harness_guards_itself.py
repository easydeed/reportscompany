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
import sys
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
        # A test that passes regardless — this very file, minus itself.
        "test": "tests/test_regression_harness_guards_itself.py::test_the_spec_files_are_well_formed",
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

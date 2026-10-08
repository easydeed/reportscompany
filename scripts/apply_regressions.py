#!/usr/bin/env python3
"""Apply a regression, prove it landed, run the gate, prove the restore landed.

WHY THIS EXISTS
---------------
Every claim in this remediation that a gate "was seen to fail" was produced by
hand: edit a file, run pytest, read the result, restore. Three of those runs
misreported in two days, and all three failed safe by luck:

1. **Stale bytecode.** Restoring `_DISPLAY_MIN = 3.0` over `2.0` writes the same
   number of bytes. `.pyc` validation is `(mtime, size)`, both edits landed in
   the same second, and Python kept running the `2.0` bytecode. The test
   reported a failure the source did not have.

2. **A backup that reverted its own edit.** `cp file backup` was taken, the file
   was then legitimately rewritten, and a later `cp backup file` silently undid
   the rewrite. The next run was green about a document that had been reverted.

3. **A `sed` no-op.** The phrase to mutate spanned a line break and `sed` is
   line-based, so it matched nothing, exited zero, and the gate passed — on an
   unmodified file. **A mutation that changes nothing and a working guard
   produce the same green.**

The third is D-087's own harness defect, filed in this project, committed by the
person who filed it. The remedy, named twice in reports and never built:
**assert the mutation is present in the file before reading green as evidence.**

So: not "the command exited zero". The changed text is read back off disk before
the gate runs, and the restore is proved byte for byte against content captured
in memory — never a file on disk, which is what (2) was.

`scripts/regress.py` already had two thirds of this for `themes.py` alone: an
anchor-count check and an "unchanged on disk" assert. What it lacked is the
bytecode clear, the restore verification, and an exit code — it prints
`*** NOTHING CAUGHT IT ***` and exits 0. This generalises it to any file and
makes the outcome machine-readable. The eleven `themes.py` mutations it records
are ported to `scripts/regressions/themes.json`; consolidating the two scripts
is a decision for whoever is next in that file, not something to do silently.

AND IN PRACTICE IT FINDS MISSING TESTS, NOT BAD MUTATIONS
---------------------------------------------------------
It was built for misfire (3) — a mutation that changes nothing reading as a
pass. Of the `DID NOT FIRE` results it has produced so far, ONE was a weak gate
(a substring match), one was a mutation on unreachable code, and THREE were
behaviour nobody had tested, including an entire wired report kind. See
`scripts/regressions/README.md` for the three readings of `DID NOT FIRE` and
which of them is a defect in the gate (only the first).

THE REPORTING IS INVERTED, WHICH IS THE POINT
---------------------------------------------
For a regression run, **a passing test is the failure.** This exits non-zero
when a mutation does not make its gate fail, and prints `DID NOT FIRE`. Exit 2
is reserved for the harness being unable to prove its own state, which is not a
result about the gate at all.

USAGE
-----
    python3 scripts/apply_regressions.py scripts/regressions/themes.json
    python3 scripts/apply_regressions.py spec.json --keep 3   # leave 3 applied

Spec format — a list of mutations:

    [
      {
        "name": "the alias rule narrowed back to direct-only",
        "file": "scripts/derive_sample_vs_builder.py",
        "old":  "elif isinstance(recv, ast.Name) and recv.id in aliases:",
        "new":  "elif False:",
        "test": "tests/test_sample_data_matches_the_builder.py"
      }
    ]

`old` must appear exactly once — an ambiguous anchor is a mutation whose shape
you cannot prove, and a missing one is misfire (3). `test` is split on
whitespace and passed to pytest, so a file, a node id or `-k expr` all work.
"""
from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


class MutationError(RuntimeError):
    """The harness could not prove its own state. Never a test result."""


def _rel(path: Path) -> str:
    """A readable name for a path that may be outside the repo.

    `relative_to` RAISES on a path outside its argument, and an exception while
    building an error message replaces the diagnosis with a traceback. Found by
    the harness's own tests, which mutate files under `tmp_path`.
    """
    try:
        return str(path.relative_to(ROOT))
    except ValueError:
        return str(path)


def clear_bytecode() -> None:
    """Remove every `__pycache__` under the repo.

    Misfire (1). Two edits of equal length in the same second are
    indistinguishable to `(mtime, size)` validation, so Python can keep running
    the previous bytecode across a restore. Cheap to make impossible.
    """
    for cache in ROOT.rglob("__pycache__"):
        if ".git" in cache.parts:
            continue
        shutil.rmtree(cache, ignore_errors=True)


def apply_mutation(path: Path, old: str, new: str) -> str:
    """Write the mutation and PROVE it is on disk. Returns the original text."""
    original = path.read_text(encoding="utf-8")
    count = original.count(old)
    if count != 1:
        raise MutationError(
            f"{_rel(path)}: anchor appears {count} times, needs "
            f"exactly 1.\n  anchor: {old[:90]!r}\n"
            f"Ambiguous means a mutation whose shape you cannot prove; zero "
            f"means misfire (3) — the no-op that reads as a pass."
        )
    if new == old:
        raise MutationError(f"{_rel(path)}: `new` equals `old`")

    path.write_text(original.replace(old, new, 1), encoding="utf-8")

    # THE GUARD. Read it back off disk — not the string just built, not the
    # return code of a command.
    after = path.read_text(encoding="utf-8")
    if new not in after:
        raise MutationError(
            f"{_rel(path)}: the mutation is NOT in the file after "
            f"writing it. The gate below would have been green about an "
            f"unmodified file."
        )
    if after == original:
        raise MutationError(
            f"{_rel(path)}: byte-identical after the write")
    return original


def restore(path: Path, original: str) -> None:
    """Put the captured text back and prove the file matches it exactly.

    Misfire (2): the restore source is the string captured immediately before
    the mutation and held in memory for the length of one mutation. A backup
    file on disk can be older than an edit made after it was taken.
    """
    path.write_text(original, encoding="utf-8")
    if path.read_text(encoding="utf-8") != original:
        raise MutationError(
            f"{_rel(path)}: restore did not land — the file "
            f"differs from the text captured before the mutation. The working "
            f"tree is now dirty in a way nothing else will report."
        )


def run_gate(test: str) -> tuple[bool, str]:
    """Run pytest. Returns `(passed, interesting lines)`."""
    cmd = [sys.executable, "-m", "pytest", "-q", "-p", "no:randomly",
           "-p", "no:cacheprovider", *test.split()]
    proc = subprocess.run(cmd, cwd=ROOT, capture_output=True, text=True)
    out = proc.stdout + proc.stderr
    tail = "\n".join(
        line for line in out.splitlines()
        if line.startswith(("FAILED", "ERROR"))
        or " passed" in line or " failed" in line or " error" in line
    )
    return proc.returncode == 0, tail.strip()


def one(mutation: dict, index: int, keep: bool) -> bool:
    """Run a single mutation. Returns True if it FIRED (the gate failed)."""
    name = mutation.get("name") or f"mutation {index}"
    path = ROOT / mutation["file"]
    print(f"\n-- [{index}] {name}\n   {mutation['file']}")

    original = apply_mutation(path, mutation["old"], mutation["new"])
    print("   mutation verified present on disk")
    try:
        clear_bytecode()
        passed, tail = run_gate(mutation["test"])
    finally:
        if keep:
            print("   --keep: mutation LEFT APPLIED, tree is dirty")
        else:
            restore(path, original)
            clear_bytecode()
            print("   restore verified byte-identical")

    for line in tail.splitlines():
        print(f"     {line}")
    if passed:
        print("   *** DID NOT FIRE *** the gate passed with the defect applied")
        return False
    print("   fired")
    return True


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("spec", help="JSON file: a list of mutations")
    ap.add_argument("--keep", type=int, metavar="N",
                    help="leave mutation N applied instead of restoring it")
    args = ap.parse_args(argv)

    mutations = json.loads(Path(args.spec).read_text(encoding="utf-8"))
    if not isinstance(mutations, list) or not mutations:
        raise MutationError(f"{args.spec}: expected a non-empty list")

    fired = [one(m, i, keep=(args.keep == i))
             for i, m in enumerate(mutations, 1)]

    n, total = sum(fired), len(fired)
    print(f"\n{'-' * 60}\n{n}/{total} mutations fired")
    if n != total:
        print("A MUTATION THAT DID NOT FIRE IS A GATE THAT DOES NOT GUARD.")
        print("Either the gate is wrong or the mutation did not express the "
              "defect. Both are findings; neither is a pass.")
        return 1
    print("every mutation made its gate fail, and every restore was verified")
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except MutationError as exc:
        # Exit 2, distinct from 1. A harness that cannot prove its own state
        # has said nothing about the gate, which is not the same outcome as a
        # gate that failed to fire.
        print(f"\nHARNESS ERROR (not a test result): {exc}", file=sys.stderr)
        sys.exit(2)

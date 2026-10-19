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

AND IT ONCE DIED HOLDING A MUTATION — D-196
-------------------------------------------
Piped to `head -40`: head exited, the next `print()` raised `BrokenPipeError`,
and the process died AFTER writing the mutation and BEFORE the restore, with no
exit code, because stdout was already gone. `apps/web/middleware.ts` was left
mutated — and the mutation was the one narrowing the middleware matcher, so
committing it would have exposed a deprecated admin tree (D-197). It was caught
on the next full-suite run by a test looking for something else entirely.

Four things close it, and only the third covers `SIGKILL`:

1. nothing stands between `apply_mutation` and the `try` whose `finally`
   restores — the `print` that used to sit there is now inside it;
2. `_say` survives a dead consumer instead of raising, and `SIGINT`/`SIGTERM`
   raise `Interrupted` so that `finally` still runs. `signal.SIGPIPE` is
   deliberately NOT set to `SIG_DFL`, which is the usual advice for a CLI tool
   and exactly wrong here: it makes the death immediate and silent;
3. `.regress-mutation-in-progress.json` is written before the mutation reaches
   disk and deleted after a verified restore. **A later run refuses to do
   anything while it exists**, and `--restore` puts the file back — but only
   after proving the file on disk is still the text this harness wrote, because
   restoring blind is misfire (2) one level up;
4. `tests/test_regression_harness_guards_itself.py` kills a real run between
   apply and restore and asserts the file came back.

**A harness that leaves a mutated tree corrupts every measurement taken after
it** — a worse failure than any it was built to catch.

USAGE
-----
    python3 scripts/apply_regressions.py scripts/regressions/themes.json
    python3 scripts/apply_regressions.py spec.json --keep 3   # leave 3 applied
    python3 scripts/apply_regressions.py --restore            # after a death

Redirect rather than pipe — `> out.txt 2>&1` — and `git status` after a run.

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
import os
import shutil
import signal
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

#: Written before a mutation reaches disk and deleted after a verified restore.
#: It is the only part of D-196's remedy that survives `SIGKILL` and a dead
#: container, because it does not depend on this process running any more code.
SENTINEL = ROOT / ".regress-mutation-in-progress.json"


class MutationError(RuntimeError):
    """The harness could not prove its own state. Never a test result."""


class Interrupted(MutationError):
    """A signal arrived. Raised so the `finally` that restores can run."""


# ─────────────────────────────────────────────────────────────────────────────
# D-196. Output that cannot kill the restore, and signals that do not skip it.
#
# The bug this closes: the output was piped to `head -40`, head exited, the
# next `print()` raised BrokenPipeError, and the process died AFTER writing the
# mutation and BEFORE the restore — with no exit code, because stdout was
# already gone. `middleware.ts` was left mutated in the working tree and the
# next full-suite run found it by accident.
#
# `signal.signal(signal.SIGPIPE, signal.SIG_DFL)` is the usual advice for a CLI
# tool and is exactly wrong here: it makes the death immediate and silent. What
# this file needs is the opposite — a write that fails must be survivable, so
# that the one thing that must happen (putting the file back) still happens.
# ─────────────────────────────────────────────────────────────────────────────

_stdout_is_gone = False


def _say(*args) -> None:
    """`print`, except a dead consumer silences this process instead of
    killing it. Nothing printed by this harness is worth a corrupted tree."""
    global _stdout_is_gone
    if _stdout_is_gone:
        return
    try:
        print(*args)
        sys.stdout.flush()
    except (BrokenPipeError, OSError, ValueError):
        _stdout_is_gone = True
        # Keep the interpreter from re-raising at shutdown over the same pipe.
        try:
            devnull = os.open(os.devnull, os.O_WRONLY)
            os.dup2(devnull, sys.stdout.fileno())
        except Exception:
            pass


def _install_signal_handlers() -> None:
    """Turn a terminating signal into an exception, so the `finally` runs.

    Covers `SIGTERM` and `SIGINT`. It cannot cover `SIGKILL` or a container
    that disappears — that is what the sentinel is for.
    """
    def handler(signum, _frame):
        raise Interrupted(
            f"signal {signal.Signals(signum).name} during a mutation")

    for sig in (signal.SIGINT, signal.SIGTERM):
        try:
            signal.signal(sig, handler)
        except (ValueError, OSError):
            pass  # not the main thread, or not supported here


def _write_sentinel(path: Path, original: str, mutated: str) -> None:
    """Record what is about to be changed, and to what.

    Both texts, because restoring blind is misfire (2) one level up: a restore
    source on disk can be older than a legitimate later edit. Holding the
    MUTATED text as well means the recovery can prove the file is still the one
    this harness broke before touching it.
    """
    SENTINEL.write_text(json.dumps({
        # `_rel`, not `relative_to`: that raises for a path outside the repo,
        # and the harness's own tests mutate files under `tmp_path`. An
        # absolute string still round-trips, because `ROOT / "/abs"` is "/abs".
        "file": _rel(path),
        "original": original,
        "mutated": mutated,
        "pid": os.getpid(),
    }), encoding="utf-8")


def _clear_sentinel() -> None:
    SENTINEL.unlink(missing_ok=True)


def _handle_stale_sentinel(do_restore: bool) -> None:
    """Refuse to run while a previous run's mutation may still be on disk.

    This does NOT restore on its own. A tool that silently writes files at
    startup is a worse problem than the one it is fixing, and `--keep` leaves a
    mutation applied on purpose. So: report, and recover only when asked.
    """
    if not SENTINEL.exists():
        return
    try:
        rec = json.loads(SENTINEL.read_text(encoding="utf-8"))
        target = ROOT / rec["file"]
        current = target.read_text(encoding="utf-8")
    except Exception as exc:
        raise MutationError(
            f"{SENTINEL.name} exists and cannot be read ({exc}). A previous "
            f"run died mid-mutation. Resolve it by hand before running "
            f"anything that reads this tree."
        )

    still_mutated = current == rec["mutated"]
    if not do_restore:
        raise MutationError(
            f"a previous run left a mutation applied to {rec['file']} "
            f"(pid {rec.get('pid')}).\n"
            f"  the file on disk {'IS' if still_mutated else 'is NOT'} the "
            f"mutated text this harness wrote.\n"
            f"  re-run with --restore to put it back, or delete "
            f"{SENTINEL.name} if you have resolved it yourself.\n"
            f"Nothing was run. Every measurement taken against this tree since "
            f"that run is suspect."
        )

    if not still_mutated:
        raise MutationError(
            f"--restore refused: {rec['file']} is neither the text this "
            f"harness mutated nor anything it can account for. Restoring would "
            f"discard an edit made after the mutation. Diff it yourself."
        )
    restore(target, rec["original"])
    _clear_sentinel()
    _say(f"restored {rec['file']} from {SENTINEL.name} and cleared it")


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
    _say(f"\n-- [{index}] {name}\n   {mutation['file']}")

    # D-196: the sentinel is written BEFORE the mutation reaches disk, and the
    # `print` that used to sit between the write and the `try` is now inside
    # it. There is no longer a statement between "the file is mutated" and "a
    # `finally` that restores it".
    original = path.read_text(encoding="utf-8")
    _write_sentinel(path, original, original.replace(
        mutation["old"], mutation["new"], 1))
    try:
        original = apply_mutation(path, mutation["old"], mutation["new"])
        _say("   mutation verified present on disk")
        clear_bytecode()
        passed, tail = run_gate(mutation["test"])
    finally:
        if keep:
            _say("   --keep: mutation LEFT APPLIED, tree is dirty")
            _say(f"   {SENTINEL.name} left in place; --restore undoes it")
        else:
            restore(path, original)
            clear_bytecode()
            _clear_sentinel()
            _say("   restore verified byte-identical")

    for line in tail.splitlines():
        _say(f"     {line}")
    if passed:
        _say("   *** DID NOT FIRE *** the gate passed with the defect applied")
        return False
    _say("   fired")
    return True


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("spec", nargs="?",
                    help="JSON file: a list of mutations")
    ap.add_argument("--keep", type=int, metavar="N",
                    help="leave mutation N applied instead of restoring it")
    ap.add_argument("--restore", action="store_true",
                    help="put back a mutation a previous run died holding "
                         "(D-196), then exit")
    args = ap.parse_args(argv)

    _handle_stale_sentinel(args.restore)
    if args.restore:
        return 0
    if not args.spec:
        ap.error("a spec is required unless --restore is given")

    mutations = json.loads(Path(args.spec).read_text(encoding="utf-8"))
    if not isinstance(mutations, list) or not mutations:
        raise MutationError(f"{args.spec}: expected a non-empty list")

    fired = [one(m, i, keep=(args.keep == i))
             for i, m in enumerate(mutations, 1)]

    n, total = sum(fired), len(fired)
    _say(f"\n{'-' * 60}\n{n}/{total} mutations fired")
    if n != total:
        _say("A MUTATION THAT DID NOT FIRE IS A GATE THAT DOES NOT GUARD.")
        _say("Either the gate is wrong or the mutation did not express the "
             "defect. Both are findings; neither is a pass.")
        return 1
    _say("every mutation made its gate fail, and every restore was verified")
    return 0


if __name__ == "__main__":
    # Installed here rather than in `main()`: this harness's own tests call
    # `main()` in-process, and replacing pytest's SIGINT handler for the rest
    # of the session is a side effect a test must not have.
    _install_signal_handlers()
    try:
        sys.exit(main())
    except MutationError as exc:
        # Exit 2, distinct from 1. A harness that cannot prove its own state
        # has said nothing about the gate, which is not the same outcome as a
        # gate that failed to fire.
        # `Interrupted` arrives here too, which is the point of raising it:
        # the restore in `one`'s `finally` has already run by now.
        try:
            print(f"\nHARNESS ERROR (not a test result): {exc}",
                  file=sys.stderr)
        except (BrokenPipeError, OSError, ValueError):
            pass  # D-196: a dead pipe must not change the exit code
        sys.exit(2)

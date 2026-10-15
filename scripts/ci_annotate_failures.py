#!/usr/bin/env python3
"""Turn a failed pytest run into ONE GitHub annotation that names the tests.

WHY THIS EXISTS
---------------
`Backend Tests` had been red on `main` for 25 consecutive runs and the only
thing any API client could learn about it was `Process completed with exit code
1`. The log body is served from a blob host that not every client will follow,
and a check run carries no `output.text` unless something writes one — so the
failure existed, was visible as a red tick, and carried no information. Two
weeks of merges happened on top of it (D-191).

**A signal that exists and says nothing is the shape half this board is made
of.** So the failing step writes its own summary where the checks API serves
it: `::error::` on stdout becomes an annotation, and
`GET /repos/{o}/{r}/check-runs/{id}/annotations` returns it.

ONE ANNOTATION, NOT ONE PER TEST. GitHub caps annotations per step (10 for
errors), and a cap that silently truncates is how a list of 40 failures becomes
a list of 10 that reads as complete. Newlines inside a workflow command have to
be encoded as `%0A`, which is what `encode` below is for.

THE FALLBACK IS THE POINT, NOT A COURTESY. A run that dies before pytest writes
a summary — a collection error, an import error, a killed process — is exactly
the case where "exit code 1" is least useful, so when there is no summary block
this prints the tail of the output instead and says that is what it did.

    python3 scripts/ci_annotate_failures.py pytest-output.txt [--max-lines N]

Exits 0 always: it is a reporter, and a reporter that can fail a build adds a
second failure mode to the thing it was meant to explain.
"""
import argparse
import re
import sys
from pathlib import Path

SUMMARY_MARKER = "short test summary info"

#: Prefixes pytest uses in its summary for outcomes that mean the build is red.
#: `XFAIL`/`XPASS`/`SKIPPED` lines also appear there under `-rA` and are not
#: failures — listing what we want rather than filtering what we do not is the
#: direction that does not quietly grow.
FAILURE_PREFIXES = ("FAILED", "ERROR")


def encode(message: str) -> str:
    """Workflow-command encoding for a multi-line annotation message.

    Order matters: `%` first, or the escapes introduced by the later
    substitutions get escaped themselves.
    """
    return (message.replace("%", "%25")
                   .replace("\r", "%0D")
                   .replace("\n", "%0A"))


def failure_lines(output: str):
    """The summary's FAILED/ERROR lines, in order, or [] if there is no summary."""
    marker = output.rfind(SUMMARY_MARKER)
    if marker == -1:
        return []
    tail = output[marker:].split("\n")[1:]
    return [l.rstrip() for l in tail if l.startswith(FAILURE_PREFIXES)]


#: `3 failed`, `2898 passed`, `20 xfailed` — a count and the word it counts.
#: Tokenised because `xfailed` ends in `failed` and `errors` starts with
#: `error`.
_COUNT = re.compile(r"(\d+)\s+([a-z]+)")

#: The words in pytest's counts line that mean the build is red. `xfailed` and
#: `xpassed` are deliberately absent: a strict xfail going green fails the run
#: and appears as `failed`, which is the signal that matters.
FAILURE_WORDS = ("failed", "error", "errors")


def outcome_counts(line: str) -> dict:
    """{"passed": 2898, "xfailed": 20, ...} from pytest's counts line."""
    return {word: int(n) for n, word in _COUNT.findall(line)}


def failure_count(line: str) -> int:
    counts = outcome_counts(line)
    return sum(counts.get(word, 0) for word in FAILURE_WORDS)


def counts_line(output: str) -> str:
    """pytest's last line — `3 failed, 2898 passed in 372.56s` — if present."""
    for line in reversed([l.strip() for l in output.split("\n") if l.strip()]):
        if " passed" in line or " failed" in line or " error" in line:
            return line.strip("= ").strip()
    return ""


def report(output: str, max_lines: int = 40) -> str:
    """The annotation body, or "" when there is nothing to report."""
    failures = failure_lines(output)
    counts = counts_line(output)

    if failures:
        shown = failures[:max_lines]
        body = "\n".join(shown)
        if len(failures) > max_lines:
            body += f"\n... and {len(failures) - max_lines} more"
        if counts:
            body += f"\n\n{counts}"
        return body

    # A run that finished and counted no failures has nothing to report, even
    # though this script is only invoked after a red step: the step can fail
    # for reasons outside pytest.
    #
    # COUNTED AS TOKENS, NOT SEARCHED AS SUBSTRINGS. The first version asked
    # `"failed" not in counts`, and this suite's green line reads
    # `2901 passed, 67 skipped, 20 xfailed` — **"xfailed" contains "failed"**,
    # so every green run reported itself as a failure. §0.6's
    # substring-is-not-a-construct rule, committed inside the script written to
    # stop a signal carrying no information, and caught by this file's own
    # green-run test rather than by reading it.
    if counts and not failure_count(counts):
        return ""

    # No summary block: say so, and show the tail rather than nothing. This is
    # the branch that covers a collection error, and it must not look like a
    # test failure list.
    tail = [l for l in output.split("\n") if l.strip()][-max_lines:]
    if not tail:
        return ""
    return ("pytest wrote no failure summary — this is the tail of its output, "
            "not a list of failed tests:\n" + "\n".join(tail))


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("output_file", help="the file the test step tee'd pytest into")
    ap.add_argument("--max-lines", type=int, default=40)
    args = ap.parse_args(argv)

    path = Path(args.output_file)
    if not path.exists():
        print(f"::error title=Test failures::{encode(f'{path} does not exist, so the test step produced no output to report')}")
        return 0

    body = report(path.read_text(encoding="utf-8", errors="replace"),
                  max_lines=args.max_lines)
    if not body:
        # A green run, or an empty file. Nothing to annotate, and no noise.
        return 0
    print(f"::error title=Test failures::{encode(body)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())

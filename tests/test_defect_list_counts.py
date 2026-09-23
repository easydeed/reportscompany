"""
The defect board's summary table must agree with its own entries.

WHY THIS EXISTS
---------------
`docs/DEFECT_LIST.md` carries a status table at the top, and the instruction
beside it has always been right: *"do not edit these counts by hand"* — parse the
entries and re-derive. Every branch did exactly that, and the derivations were
correct every time.

It went stale anyway. On 2026-09-23 the table read `open 33 · fixed 53 ·
Total 91` while the entries below said `30 / 60 / 94`, and its own severity line
summed to 34 against a stated 33.

**The derivation was never the failure. Writing the result back was.** Three
branches in a row updated the table with a `str.replace` against an expected
string; a merge changed that string, the replace matched nothing, and it
silently did nothing. That is the same no-op-mutation trap that made a
regression look green in D-087's harness — and it is invisible for the same
reason, because nothing distinguishes "replaced" from "matched nothing".

So the agreement becomes a property of the repository rather than of whoever
edits the file next. That is the move this project keeps arriving at: the guard
belongs in the structure, not in the diligence.

WHAT THIS DOES NOT CHECK
------------------------
Only that the summary matches the entries. It says nothing about whether a
`Status:` line is TRUE of the code — that is the stale sweep (§0.6, *a defect
list needs a read path*), and it needs a person.
"""
import collections
import re
from pathlib import Path

import pytest

DEFECT_LIST = Path(__file__).resolve().parents[1] / "docs/DEFECT_LIST.md"

ENTRY = re.compile(r"^### (D-\d{3}) — ", re.M)
STATUS = re.compile(r"^\*\*Status:\*\* `([a-z-]+)`", re.M)
SEVERITY = re.compile(r"^\*\*Severity:\*\* \*?\*?([A-Z]+)", re.M)


def parse():
    """
    {id: (status, severity)} for every entry, read the way the file's own
    instruction says to read it.

    Takes the FIRST Status line under each heading. Entries carry later
    quotations of other statuses inside their prose, and matching those is how a
    parser silently disagrees with a human reading the same file.
    """
    lines = DEFECT_LIST.read_text().split("\n")
    out, cur, sev = {}, None, None
    for line in lines:
        m = ENTRY.match(line)
        if m:
            cur, sev = m.group(1), None
            continue
        if cur is None:
            continue
        v = SEVERITY.match(line)
        if v:
            sev = v.group(1)
        s = STATUS.match(line)
        if s and cur not in out:
            out[cur] = (s.group(1), sev)
    return out


def stated(pattern, text):
    m = re.search(pattern, text)
    assert m, f"the summary table no longer contains {pattern!r} — if the table was "\
              f"restructured, update this test deliberately rather than deleting it"
    return int(m.group(1))


@pytest.fixture(scope="module")
def board():
    entries = parse()
    assert entries, "no defect entries parsed — the heading format changed"
    return entries


def test_the_summary_table_matches_the_entries(board):
    """THE REGRESSION. 33/53/91 in the table against 30/60/94 in the entries."""
    text = DEFECT_LIST.read_text()
    counts = collections.Counter(status for status, _ in board.values())

    for label, pattern in (
        ("open", r"\| `open` \| (\d+) \|"),
        ("fixed", r"\| `fixed` \| (\d+) \|"),
        ("closed-not-live", r"\| `closed-not-live` \| (\d+) \|"),
    ):
        assert stated(pattern, text) == counts[label], (
            f"the table says {label} = {stated(pattern, text)}; the entries say "
            f"{counts[label]}. Re-derive by parsing — and check the edit LANDED, "
            f"which is the part that failed last time."
        )

    assert stated(r"\| \*\*Total\*\* \| \*\*(\d+)\*\* \|", text) == len(board), (
        f"the table's total disagrees with the {len(board)} entries parsed"
    )


def test_the_severity_line_matches_the_open_entries(board):
    text = DEFECT_LIST.read_text()
    actual = collections.Counter(
        sev for status, sev in board.values() if status == "open"
    )
    m = re.search(
        r"\*\*Open by severity:\*\* BROKEN (\d+) · WRONG (\d+) · FRAGILE (\d+) · ROUGH (\d+)\. "
        r"\(Sums to (\d+),",
        text,
    )
    assert m, "the severity line is missing or reformatted"
    broken, wrong, fragile, rough, total = (int(g) for g in m.groups())

    assert (broken, wrong, fragile, rough) == (
        actual["BROKEN"], actual["WRONG"], actual["FRAGILE"], actual["ROUGH"]
    ), (
        f"severity line says BROKEN {broken} · WRONG {wrong} · FRAGILE {fragile} "
        f"· ROUGH {rough}; the open entries are {dict(actual)}"
    )
    assert total == sum(actual.values()), (
        f"the severity line claims to sum to {total} but its own numbers sum to "
        f"{sum(actual.values())} — it disagreed with ITSELF the last time this drifted"
    )


def test_the_ids_are_contiguous_with_no_duplicates(board):
    """
    The table asserts "D-001 … D-0NN, contiguous, no duplicates" in prose. A gap
    is legitimate while a defect is filed on an unmerged branch, but it must be
    explained in the table rather than merely true — so the prose and the parse
    have to agree.
    """
    nums = sorted(int(i[2:]) for i in board)
    missing = [n for n in range(1, max(nums) + 1) if n not in nums]
    text = DEFECT_LIST.read_text()
    claims_contiguous = "contiguous, no duplicates" in text

    if claims_contiguous:
        assert not missing, (
            f"the table claims the ids are contiguous, but D-{missing} are absent. "
            f"Either the entries were renumbered, or a branch reserving those "
            f"numbers has not merged — in which case say so in the table."
        )
    assert len(set(board)) == len(board), "duplicate defect ids"


def test_every_entry_has_a_severity(board):
    missing = sorted(d for d, (_, sev) in board.items() if sev is None)
    assert not missing, (
        f"{missing} have a Status but no Severity line, so they are invisible to "
        f"the severity tally while still counting toward the open total"
    )

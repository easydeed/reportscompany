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


def _summary_table() -> str:
    """The state table at the top, from its header row to its Total row."""
    text = DEFECT_LIST.read_text()
    head = text.index("| State | Count | Meaning |")
    tail = text.index("| **Total** |", head)
    return text[head:tail]


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


def test_the_table_has_a_row_for_every_status_and_they_sum_to_the_total(board):
    """A ROW THAT IS SIMPLY ABSENT IS INVISIBLE TO THE TEST ABOVE.

    The three checks above name the statuses they check. On 2026-10-01 a
    fifth status appeared — `duplicate`, for an entry that turned out to be
    a re-filing of D-131 — and every assertion above passed while the table's
    own rows summed to 159 against a stated total of 160. The table was
    internally inconsistent and nothing said so, which is the exact failure
    mode this file was written for, one level up from where it was looking.

    So the rows are derived from the entries rather than listed here: every
    status that occurs must have a row, and the rows must sum to the total.
    """
    counts = collections.Counter(status for status, _ in board.values())

    # THE SUMMARY TABLE ONLY. The first version matched `| `word` | 123 |`
    # across the whole document and summed to 850, because the file carries a
    # dozen other two-column tables with a code span in the first cell. The
    # accidental-selector trap, inside the test that exists to stop the
    # summary drifting — so the table is sliced out by its own header and
    # Total row before anything is matched.
    text = _summary_table()

    rows = {m.group(1): int(m.group(2))
            for m in re.finditer(r"^\| `([a-z-]+)` \| (\d+) \|", text, re.M)}

    missing = sorted(set(counts) - set(rows))
    assert not missing, (
        f"{missing} appear on entries and have no row in the summary table, so "
        f"those entries are counted in the Total and nowhere else"
    )
    wrong = {k: (rows[k], counts[k]) for k in counts if rows[k] != counts[k]}
    assert not wrong, f"table vs entries, (stated, actual): {wrong}"

    assert sum(rows.values()) == len(board), (
        f"the table's rows sum to {sum(rows.values())} and it claims "
        f"{len(board)} entries. A row is missing or a count is wrong."
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

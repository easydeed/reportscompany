"""
§0.6 — every xfail names its defect, and every defect names its xfails.

WHY THIS IS A TEST AND NOT A CONVENTION
---------------------------------------
`xfail(strict=True)` is what this project uses instead of leaving a check
permanently red, because unfixable red is the mechanism that hid D-038 and
D-041: nobody can act on it, so everybody stops reading the build, and the next
real failure lands inside the noise. The strict marker keeps the assertion
running and breaks the build the day the product catches up.

That argument only holds while the marker is traceable. An `xfail` whose reason
says nothing, or names a defect whose entry has never heard of it, is a `skip`
with better manners — it runs, it is quiet, and nothing will ever tell you to
remove it.

So the rule is a two-way link:

    reason  ->  defect ID          (the test says why it is allowed to fail)
    entry   ->  list of tests      (the defect says what to delete when fixed)

and the rule is checked here, because a documented invariant that nothing
verifies is a comment. This file is the same shape as the thing it guards: it
would be easy to write a version that reads the defect list, finds nothing, and
passes — so it asserts the expected defects are actually present before
comparing anything.
"""
import re
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[1]
DEFECT_LIST = REPO / "docs/DEFECT_LIST.md"

# Files that may contain gated xfails. A new one has to be added here, which is
# deliberate: the alternative is walking the tree and silently covering nothing
# when the walk is wrong.
SOURCES = [
    REPO / "tests/test_simplyrets_query_builder.py",
    REPO / "apps/api/tests/test_plans_limits.py",
]

MARKER_DEF = re.compile(r"^_D(\d{3})_GATED\s*=\s*pytest\.mark\.xfail", re.M)
MARKER_USE = re.compile(r"^\s*@_D(\d{3})_GATED\s*$")


def _defect_id(digits):
    """`_D087_GATED` -> `D-087`. Python identifiers cannot carry the hyphen the
    board uses, so the two spellings have to be reconciled somewhere; doing it
    here keeps every comparison below in the board's spelling."""
    return f"D-{digits}"
TEST_DEF = re.compile(r"^\s*def (test_\w+)")


def gated_tests():
    """{defect_id: {test names}} — read from the source, never hand-listed."""
    found = {}
    for path in SOURCES:
        lines = path.read_text().split("\n")
        pending = None
        for line in lines:
            m = MARKER_USE.match(line)
            if m:
                pending = _defect_id(m.group(1))
                continue
            if pending:
                d = TEST_DEF.match(line)
                if d:
                    found.setdefault(pending, set()).add(d.group(1))
                    pending = None
    return found


def defect_entry(defect_id):
    text = DEFECT_LIST.read_text()
    start = text.find(f"### {defect_id} —")
    if start == -1:
        return None
    nxt = text.find("\n### D-", start + 1)
    return text[start:nxt if nxt != -1 else len(text)]


def test_there_are_gated_xfails_to_check():
    """
    THE GUARD ON THIS FILE. Every assertion below is a loop over whatever
    `gated_tests()` found, so an empty result would make all of them vacuously
    true — the suite would report success for having looked at nothing. That is
    the failure mode §0.6 calls a diagnostic that drifts and reassures.
    """
    found = gated_tests()
    assert found, (
        "no @_Dxxx_GATED markers found. Either the convention changed and this "
        "file was not updated, or SOURCES is pointing at the wrong place — "
        "both of which make every other test here pass by doing nothing."
    )


def test_every_marker_names_a_defect_in_its_reason():
    for path in SOURCES:
        text = path.read_text()
        for digits in MARKER_DEF.findall(text):
            defect_id = _defect_id(digits)
            block = text[text.index(f"_D{digits}_GATED = pytest.mark.xfail"):][:800]
            assert 'strict=True' in block, (
                f"{defect_id}'s marker is not strict. A non-strict xfail that "
                f"starts passing stays silent, so nothing ever tells you to "
                f"remove it — which is the whole reason this is allowed."
            )
            reason = re.search(r'reason=\s*\(?\s*"([^"]+)', block)
            assert reason, f"{defect_id}'s marker has no reason= text"
            assert defect_id in reason.group(1), (
                f"{defect_id}'s marker reason does not name the defect: "
                f"{reason.group(1)!r}"
            )


@pytest.mark.parametrize("defect_id", sorted(gated_tests()))
def test_the_defect_entry_exists_and_lists_every_test_it_gates(defect_id):
    entry = defect_entry(defect_id)
    assert entry is not None, (
        f"{defect_id} gates xfails but has no entry in docs/DEFECT_LIST.md"
    )
    missing = sorted(t for t in gated_tests()[defect_id] if t not in entry)
    assert not missing, (
        f"{defect_id}'s entry does not list {len(missing)} test(s) it gates: "
        f"{missing}. Without the back-link, nobody fixing {defect_id} knows "
        f"which markers to delete."
    )


@pytest.mark.parametrize("defect_id", sorted(gated_tests()))
def test_a_fixed_defect_explains_why_its_xfails_outlive_it(defect_id):
    """
    THIS TEST STARTED LIFE ASSERTING THE WRONG THING, AND D-087 SAID SO ON THE
    FIRST RUN.

    The first version asserted that a defect gating xfails must still be `open`
    — the reasoning being that markers left behind on a fixed defect are stale.
    D-087 is `fixed` (the contaminated count is gone) and still gates two tests,
    because those tests want `_location` to send `cities`, which is a SEPARATE
    change gated on the production probe. The defect is closed; the follow-up is
    not. "Gated" and "unfixed" are different properties and the first version
    conflated them.

    Rewritten to check what actually matters: a `fixed` defect that still gates
    tests has to SAY so, so a reader who sees the green status and the live
    markers is not left to guess which one is wrong. The gating block carries
    that explanation, and `test_the_defect_entry_exists_and_lists_every_test_it_gates`
    already requires the block.
    """
    entry = defect_entry(defect_id)
    status = re.search(r"^\*\*Status:\*\* `([a-z-]+)`", entry, re.M)
    assert status, f"{defect_id}'s entry has no Status line"
    if status.group(1) != "fixed":
        return
    assert "XFAILS THIS DEFECT GATES" in entry, (
        f"{defect_id} is marked `fixed` but still gates "
        f"{sorted(gated_tests()[defect_id])}, and its entry does not explain "
        f"why the markers survive the fix. A green status beside live markers "
        f"is a contradiction a reader cannot resolve."
    )

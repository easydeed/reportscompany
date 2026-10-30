"""The figures in the market-surface status report, recomputed.

WHY THIS IS GATED
-----------------
`docs/MARKET_SURFACE_STATUS_2026-10-11.md` is the report this surface will be
read through, and every number in it is a measurement. A status document whose
figures have gone stale is worse than none, because the next decision gets
taken against them — the same reason `THEME_RENAME_SCOPE` and the capacity
document are gated.

The page-and-row measurement needs a browser and CI has none, so those are
pinned and asserted to still be what the document states. Everything derivable
from the repository — how many kinds are wired, the baseline row counts, the
capacity determinism, the defect statuses it cites — is recomputed.
"""
import re
import sys
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parent.parent
DOC = REPO / "docs/MARKET_SURFACE_STATUS_2026-10-11.md"
BASELINE = REPO / "apps/worker/tests/pdf_contrast_baseline.txt"
sys.path.insert(0, str(REPO / "apps/worker/src"))
sys.path.insert(0, str(REPO / "apps/worker/tests"))

from test_narrative_box import PAGE_1_CAPACITY  # noqa: E402
from worker.market_builder import ALL_REPORT_TYPES, V2_KINDS  # noqa: E402

#: Measured 2026-10-11 by running `measure_market_pagination.main()` twice on
#: one render path, with `V2_KINDS` emptied for the "before" column.
MEASURED = {"pages_before": 58, "pages_after": 48,
            "rows_before": 609, "rows_after": 601}


@pytest.fixture(scope="module")
def body():
    return DOC.read_text(encoding="utf-8")


def test_the_report_says_how_many_kinds_are_wired(body):
    """EIGHT since D-255, and the document must say so in its update.

    This was "SEVEN, and the document must not claim eight" — the assertion
    that mattered most, because a status report claiming the surface finished
    while one kind was unwired is the sentence somebody forwards. The kind
    landed; the document's 2026-10-11 body is kept as measured, and the dated
    update at its head is what makes the current claim.
    """
    assert len(V2_KINDS) == 8, (
        f"{len(V2_KINDS)} kinds are wired: {sorted(V2_KINDS)}; the document's "
        f"update says all eight."
    )
    assert sorted(set(ALL_REPORT_TYPES) - V2_KINDS) == []
    assert "ALL EIGHT KINDS NOW RENDER DESIGN'S `_v2` PAGE (D-255)" in body
    assert "wired 2026-10-26 (D-255)" in body


def test_the_page_and_row_figures_are_the_measured_ones(body):
    for name, value in MEASURED.items():
        assert str(value) in body, (
            f"the document no longer quotes the measured {name} of {value}. "
            f"Re-run the two-pass measurement and update MEASURED here too."
        )
    saved = MEASURED["pages_before"] - MEASURED["pages_after"]
    assert saved == 10, saved
    assert "**Ten pages saved.**" in body
    # The rows went DOWN by 8, all of it price_bands losing its listings table.
    # Asserted because "ten pages saved" invites reading it as more content in
    # fewer pages, and the row count is what stops that being overclaimed.
    assert MEASURED["rows_after"] < MEASURED["rows_before"]
    assert "every kind carries the identical rows" in body
    density_before = MEASURED["rows_before"] / MEASURED["pages_before"]
    density_after = MEASURED["rows_after"] / MEASURED["pages_after"]
    assert f"{density_before:.1f} → {density_after:.1f} rows per page" in body, (
        f"the density figures should read {density_before:.1f} → "
        f"{density_after:.1f}"
    )


def test_the_contrast_figures_recompute(body):
    rows = BASELINE.read_text(encoding="utf-8").splitlines()
    market = [r for r in rows if r.startswith("market__")]
    prop = [r for r in rows if r.startswith("property__")]
    assert market == [], f"{len(market)} market baseline rows are back"
    assert f"| property baseline | {len(prop)} " in body, (
        f"the property baseline is {len(prop)} rows; the document says "
        f"something else"
    )
    assert "**0**" in body and "5,058" in body


def test_the_determinism_claim_holds_for_every_wired_kind(body):
    """§3's claim, recomputed. One number per kind means page-1 capacity does
    not depend on how much prose a model produced."""
    swinging = {
        k: s for k, s in PAGE_1_CAPACITY.items()
        if k in V2_KINDS and s["no_narrative"] != s["with_narrative"]
    }
    assert swinging == {}, (
        f"these wired kinds' page-1 capacity depends on prose length again: "
        f"{swinging}. §3 of the document claims otherwise."
    )
    assert PAGE_1_CAPACITY["market_snapshot"] == {"no_narrative": 0, "with_narrative": 0}, (
        "the document says `market_snapshot` reads 0 / 0 since D-255"
    )
    assert "reads `0 / 0`" in body


def test_every_defect_it_cites_exists_and_carries_the_status_quoted(body):
    """A status report citing an entry that has moved describes nothing."""
    defects = REPO / "docs/DEFECT_LIST.md"
    text = defects.read_text(encoding="utf-8")
    for ref in sorted(set(re.findall(r"\bD-1[78]\d\b", body))):
        assert f"### {ref} " in text, (
            f"{ref} is cited in the status report and is not an entry"
        )
    # Each must still carry the status §5 quotes for it: D-187 `open`, and
    # D-184 `accepted` (Jerry, 2026-10-30: the grid spilling to page 2 stands).
    for ref, status in (("D-184", "accepted"), ("D-187", "open")):
        entry = text.split(f"### {ref} ", 1)[1].split("### D-", 1)[0]
        assert f"**Status:** `{status}`" in entry, (
            f"{ref} is no longer `{status}`; §5 of the status report says it is"
        )
    assert "**D-184** `accepted`" in body, "§5 no longer quotes D-184 as `accepted`"


def test_the_untracked_finding_is_still_true(body):
    """§7's claim: every function `test_new_metrics.py` tests is defined in it.

    Recomputed, because the whole point of the finding is that nobody noticed —
    and if one of the four lands in `apps/`, the entry's disposition changes.
    """
    suite = (REPO / "tests/test_new_metrics.py").read_text(encoding="utf-8")
    named = ["compute_price_cut_stats", "compute_dom_distribution",
             "comp_confidence", "parse_options_meta"]
    for fn in named:
        assert f"def {fn}(" in suite, f"{fn} is no longer defined in the suite"
        hits = list((REPO / "apps").rglob("*.py"))
        in_apps = [p for p in hits if f"def {fn}(" in p.read_text(encoding="utf-8")]
        assert not in_apps, (
            f"{fn} now exists in {[str(p) for p in in_apps]} — D-187's "
            f"disposition 1 has been taken for it. Update the entry and §7."
        )
    assert "every function it tests is defined inside the\ntest file" in body

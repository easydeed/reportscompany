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
    """SEVEN, and the document must not claim eight.

    This is the assertion that matters most in the file. A status report
    claiming the surface is finished when one kind is unwired is the one error
    here that would reach a customer, because it is the sentence somebody
    forwards.
    """
    assert len(V2_KINDS) == 7, (
        f"{len(V2_KINDS)} kinds are wired: {sorted(V2_KINDS)}. If "
        f"`market_snapshot` has landed, this document's title, §1 table, §5 "
        f"and §6 all change — update them together rather than one of them."
    )
    unwired = sorted(set(ALL_REPORT_TYPES) - V2_KINDS)
    assert unwired == ["market_snapshot"], unwired
    assert "Seven of the eight" in body
    assert "**`market_snapshot` is not wired**" in body
    for claim in ("All eight kinds wired", "all eight kinds render"):
        assert claim not in body, f"the document claims {claim!r}"


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
    assert PAGE_1_CAPACITY["market_snapshot"]["with_trend"] == 0, (
        "the document says `market_snapshot` still reads 3 / 3 / 0"
    )


def test_every_defect_it_cites_exists_and_carries_the_status_quoted(body):
    """A status report citing an entry that has moved describes nothing."""
    defects = REPO / "docs/DEFECT_LIST.md"
    text = defects.read_text(encoding="utf-8")
    for ref in sorted(set(re.findall(r"\bD-1[78]\d\b", body))):
        assert f"### {ref} " in text, (
            f"{ref} is cited in the status report and is not an entry"
        )
    # The two it calls `open` must still be open, and the one it calls the
    # remaining §7.3 item must still be unbuilt.
    for ref in ("D-184", "D-187"):
        entry = text.split(f"### {ref} ", 1)[1].split("### D-", 1)[0]
        assert "**Status:** `open`" in entry, (
            f"{ref} is no longer open; §5 of the status report says it is"
        )


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

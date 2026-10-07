"""The brand audit is a document we SEND, so its numbers are gated.

`docs/BRAND_AUDIT_FOR_DESIGN_2026-10-07.md` tells Design that their market
colour rule holds on a brand population it was never measured on. Three bounds
have now reached us derived from a sample and stated as a property of a surface
— `#8A8E95`, the display-size exception, and the brand set behind both. A table
of hexes typed into a markdown file is that same shape, and sending a stale one
would put us where we have twice asked them not to be.

So every figure in that document is re-derived by
`scripts/derive_brand_audit.py` and checked here.
"""
import importlib.util
import io
import json
import sys
from contextlib import redirect_stdout
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parent.parent
DOC = REPO / "docs/BRAND_AUDIT_FOR_DESIGN_2026-10-07.md"
DERIVE = REPO / "scripts/derive_brand_audit.py"


@pytest.fixture(scope="module")
def derived():
    spec = importlib.util.spec_from_file_location("_brand_audit", DERIVE)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    buf = io.StringIO()
    with redirect_stdout(buf):
        assert module.main() == 0
    return json.loads(buf.getvalue())


@pytest.fixture(scope="module")
def text():
    return DOC.read_text(encoding="utf-8")


def test_the_overlap_is_what_the_document_says(derived, text):
    """The finding itself: two shared, four each way."""
    assert len(derived["shared_hexes"]) == 2, derived["shared_hexes"]
    assert len(derived["ours_not_sampled"]) == 4
    assert len(derived["sampled_not_ours"]) == 4
    assert "Only two of the six brands are shared" in text, (
        f"the overlap is now shared={derived['shared_hexes']}, "
        f"ours-only={derived['ours_not_sampled']}, "
        f"theirs-only={derived['sampled_not_ours']} — the document's heading "
        f"says something else."
    )


def test_every_measured_ratio_in_the_document_is_current(derived, text):
    """Each brand's row, by its own numbers.

    A document that says 4.83 when the derivation says 4.91 is the thing this
    project keeps filing, and this one leaves the building.
    """
    stale = []
    for row in derived["ours"]:
        for field in ("white", "near_black", "best"):
            value = f"{row[field]:.2f}"
            if value not in text:
                stale.append(f"{row['name']}.{field} = {value}")
    for row in derived["ours"]:
        for field in ("ink_on_white", "ink_on_tint"):
            value = f"{row[field]:.2f}"
            if value not in text:
                stale.append(f"{row['name']}.{field} = {value}")
        if row["primary_ink"] not in text:
            stale.append(f"{row['name']}.primary_ink = {row['primary_ink']}")
    assert not stale, (
        "figures the derivation produces that are not in the document:\n  "
        + "\n  ".join(stale)
        + "\n\nRe-run scripts/derive_brand_audit.py and update the tables."
    )


def test_the_document_does_not_claim_a_failure_that_is_not_there(derived, text):
    """Both populations pass, and the document must not say otherwise.

    The direction that matters: a document claiming brands FAIL when they do
    not would be us making their mistake back at them.
    """
    assert derived["n_ours_band_below"] == 0
    assert derived["n_design_band_below"] == 0
    assert "Zero of twelve fall below 4.5" in text, (
        f"{derived['n_ours_band_below']} of ours and "
        f"{derived['n_design_band_below']} of Design's sample now fall below "
        f"{derived['thresholds']['small_text']}. The document says zero of "
        f"twelve. If that changed, the finding changed and the document is a "
        f"different document."
    )


def test_the_one_divergent_brand_is_named_correctly(derived, text):
    """`display_ink` != `on_primary` on exactly one brand per population."""
    assert derived["ours_display_ink_differs"] == ["Forest"], \
        derived["ours_display_ink_differs"]
    # Named by its corpus name, not its colloquial one: the colloquial name
    # for #0D9488 is also a retired theme's name, and a literal here takes
    # down `test_no_live_code_path_names_a_retired_theme`. Which is the gate
    # working — a brand is not a theme, and nothing can tell from the string.
    assert derived["design_display_ink_differs"] == ["luxury_estates"], \
        derived["design_display_ink_differs"]
    assert "`Forest` (`#059669`) is the only brand" in text


def test_the_worst_ink_on_tint_is_quoted(derived, text):
    assert derived["worst_ink_on_tint"] >= 4.5, (
        f"primary_ink's worst case on tint is now "
        f"{derived['worst_ink_on_tint']}, under 4.5 — D-170's guarantee no "
        f"longer holds and §4 of the document is wrong."
    )
    assert f"Worst case {derived['worst_ink_on_tint']:.2f}" in text


def test_the_presets_are_read_from_both_pages(derived):
    """`presets()` raises if the two copies disagree; asserted here so the
    audit cannot quietly describe one page's picker."""
    spec = importlib.util.spec_from_file_location("_brand_audit2", DERIVE)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    assert len(module.PRESET_FILES) == 2
    assert len(module.presets()) == 6, module.presets()

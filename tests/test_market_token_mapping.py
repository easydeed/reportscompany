"""Design's market colour roles against the tokens we already have.

Checked before wiring the first market kind, because this project's most
repeated defect is a second copy of something: five copies of the theme map
(D-163), two of the brand picker (D-175), two counts of the token set (D-171).
Adding `accent_ink` as a new token when `accent_on_light` already derives it
would be that mistake with a design handoff as the excuse.

The mapping lives in `docs/MARKET_TOKEN_MAPPING_2026-10-07.md`; this asserts the
one claim in it that is a guarantee rather than a name.
"""
import sys
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parent.parent
DOC = REPO / "docs/MARKET_TOKEN_MAPPING_2026-10-07.md"
sys.path.insert(0, str(REPO / "apps/worker/src"))

from worker.property_builder import compute_color_roles  # noqa: E402
from worker.themes import TOKENS, WHITE, contrast, derive_theme  # noqa: E402

#: Design's rule for `accent_ink`: "derived by darkening `accent` until >=4.5 on
#: white". Stated independently of our constants so this is not asserting a
#: value against itself.
ACCENT_INK_MIN = 4.5

#: Our six presets plus the three of Design's samples we do not ship.
BRANDS = {
    "Indigo": "#4F46E5", "Ocean": "#0EA5E9", "Crimson": "#DC2626",
    "Forest": "#059669", "Midnight": "#1E293B", "Royal": "#7C3AED",
    "amber": "#F59E0B", "lime": "#84CC16", "luxury_estates": "#0D9488",
}


@pytest.mark.parametrize("name,accent", sorted(BRANDS.items()))
def test_accent_ink_clears_aa_on_both_light_surfaces(name, accent):
    """D-177. On white AND on the brand's own tint, not just white.

    The first version of this test checked white alone, which is the same half
    a guarantee the function had: `accent_on_light` cleared white on all nine
    brands and failed the TINT on four — Crimson 4.41, Forest 4.39, lime 4.47,
    teal 4.38. Design's spec puts accent text on the tint panel, so the next
    thing built would have rendered it.

    Both surfaces, parametrised by name, so a failure says which brand and
    which surface rather than "a ratio moved".
    """
    ink = compute_color_roles(accent)["theme_color_on_light"]
    tint = derive_theme(accent)["tint"]
    for surface, label in ((WHITE, "white"), (tint, f"its tint {tint}")):
        ratio = contrast(ink, surface)
        assert ratio >= ACCENT_INK_MIN, (
            f"{name} ({accent}): accent_ink {ink} is {ratio:.2f} on {label}, "
            f"under Design's {ACCENT_INK_MIN}. A guarantee against one of the "
            f"surfaces a token is used on is half a guarantee (D-170, D-177)."
        )


def test_the_roles_design_names_are_all_accounted_for():
    """No new colour token. The claim the wiring rests on.

    `accent` and `primary` are inputs rather than derived tokens, so they are
    not in `TOKENS` — asserted separately to the ones that are, because a test
    that looked for all six in `TOKENS` would fail for the wrong reason.
    """
    derived = {"on_primary", "display_ink", "tint"}
    missing = sorted(derived - set(TOKENS))
    assert not missing, (
        f"{missing} are named in Design's market colour roles and are not in "
        f"`themes.TOKENS`. The mapping document claims no new token is needed."
    )
    roles = compute_color_roles("#4F46E5")
    assert "theme_color_on_light" in roles, (
        "`compute_color_roles` no longer returns `theme_color_on_light`, which "
        "is what the mapping identifies as Design's `accent_ink`."
    )


def test_the_document_does_not_claim_a_token_is_new_when_it_is_not():
    """The finding is that nothing needs building. If that changes, say so."""
    body = DOC.read_text(encoding="utf-8")
    assert "All six roles exist. None needs building." in body
    assert "no new colour token" in body
    worst = min(
        min(contrast(compute_color_roles(a)["theme_color_on_light"], s)
            for s in (WHITE, derive_theme(a)["tint"]))
        for a in BRANDS.values())
    assert f"**Worst case {worst:.2f} across both surfaces**" in body, (
        f"the worst accent_ink ratio across white and tint is now {worst:.2f}; "
        f"the document states something else."
    )


def test_the_tint_gap_is_recorded_as_found_and_fixed():
    """It was unmeasured; measuring it found D-177.

    The document must keep the pre-fix figures, because "it clears 4.5 now" is
    not the finding — the finding is that one of two implementations of the
    same derivation got D-170's fix and the other did not, and the four brands
    name the cost.
    """
    body = DOC.read_text(encoding="utf-8")
    assert "D-177" in body and "D-170" in body
    for figure in ("4.41", "4.39", "4.47", "4.38"):
        assert figure in body, (
            f"the pre-fix ratio {figure} is no longer recorded. Removing the "
            f"measurement leaves a fix with no evidence it was needed."
        )
    assert "two implementations" in body


def test_the_market_baseline_is_spent():
    """The heuristic's output, now that every row it described is closed.

    THE WHOLE PREDICTION, MADE BEFORE ANY TEMPLATE WAS WRITTEN. All six
    `market__*` baseline rows were badge selectors — three tier badges on
    `new_listings`, three status badges on `price_bands`, and none on `closed`.
    So the heuristic said: wiring `closed` closes 0, `new_listings` closes 3,
    `price_bands` closes 3. Measured on 2026-10-07/08: 0, 3, 3.

    It is the estimate that matters, not the zero. "Ask where a token paints
    before estimating what it closes" came out of D-171 (a token adoption that
    closed twenty rows) and D-177 (the same ticket shape closing none), and it
    is a grep of the baseline rather than a render — which is why it could be
    stated in advance and then checked.

    WHAT THIS GATE MEANS AT ZERO. It no longer constrains the heuristic's
    input; it holds the surface at zero, which is the thing that makes every
    later kind's baseline diff attributable. A market row reappearing means
    either a kind moved and brought a failure with it, or a `_v2` element took
    a token that does not clear at the size it paints — and the diff says which
    kind without anyone having to bisect.
    """
    baseline = (REPO / "apps/worker/tests/pdf_contrast_baseline.txt"
                ).read_text(encoding="utf-8")
    rows = [line.split("\t") for line in baseline.splitlines()
            if line.startswith("market__")]
    assert rows == [], (
        f"{len(rows)} market baseline rows are back: "
        f"{sorted({r[0] for r in rows})}. The market surface reached zero on "
        f"2026-10-08 and a new row is a failure this change introduced, not "
        f"one it inherited."
    )
    body = DOC.read_text(encoding="utf-8")
    assert "**`closed` closes zero contrast failures**" in body
    assert "0, 3, 3" in body, (
        "the document no longer records the three measured outcomes against "
        "the three predicted ones, which is the only evidence the heuristic "
        "was worth stating"
    )
    # And the prediction, now half-redeemed, must stay stated: the value of the
    # heuristic is that it was written down BEFORE the measurement agreed.
    assert "| `new_listings` | 3 (tier badges) | **3 pairings** |" in body

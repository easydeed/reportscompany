"""The masthead band, and the invariant that replaced five hardcoded whites.

WHY THE BAND AND NOT THE TEXT (D-112)
-------------------------------------
The market masthead is a gradient from the affiliate's brand to the platform
accent, and every label on it was `#ffffff` or `rgba(255,255,255,0.7)`. The
2026-09-29 audit measured 560 failing runs there — the largest single finding
in the corpus, and the subtitle failed for **every** brand at **every** stop.

The tempting fix is to choose a better text colour. Measured, it cannot work:
for three of the six audited brands no single colour clears 4.5:1 on both ends
— white fails on amber and lime, near-black fails on coastal and violet. The
band is what is wrong, so the band is what is guaranteed, and the text colour
becomes a consequence rather than a choice.

WHAT THESE ASSERT, AND WHAT test_pdf_contrast.py ASSERTS INSTEAD
-----------------------------------------------------------------
The browser gate measures the rendered document and would catch a regression
here. It is also 35 seconds, needs Chromium, and reports a ratio without
saying which decision produced it. These run in milliseconds on the
derivation, and they name the decision: the alpha the band is guaranteed for,
the fact that a dark brand is not dulled, and that the degraded path stays
unused. Two levels, deliberately — the same split as the layout map and the
render diff.
"""
import re
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "apps/worker/src"))

import worker.property_builder as property_builder  # noqa: E402
from worker.market_builder import (  # noqa: E402
    DEFAULT_ACCENT,
    DEFAULT_PRIMARY,
    MarketReportBuilder,
)
from worker.property_builder import flatten_over  # noqa: E402
from worker.themes import contrast  # noqa: E402

MARKET_CSS = ROOT / "apps/worker/src/worker/templates/market/_base/base.jinja2"

#: The same six the contrast audit and the email suite use, so a number here
#: can be compared with a number there.
BRANDS = ["#DC2626", "#0D9488", "#0E7490", "#F59E0B", "#84CC16", "#7C3AED"]

AA = 4.5


def band(primary, accent=DEFAULT_ACCENT):
    return MarketReportBuilder({"report_type": "closed", "listings": []})._masthead_band(
        primary, accent)


# ── the two halves of one decision ──────────────────────────────────────────

def test_the_guaranteed_alpha_is_the_alpha_the_stylesheet_uses():
    """
    The band is darkened until text at `MASTHEAD_SUBTITLE_ALPHA` is readable.
    If the stylesheet's opacity drops below that, the guarantee is being made
    for a lighter colour than the one on the page and means nothing — the
    §7.2 narrative-box contract, in a second place.
    """
    css = MARKET_CSS.read_text(encoding="utf-8")
    rule = re.search(r"\.masthead-subtitle\s*\{(.*?)\}", css, re.S)
    assert rule, ".masthead-subtitle rule not found"
    alpha = re.search(r"rgba\(\s*255\s*,\s*255\s*,\s*255\s*,\s*([\d.]+)\s*\)", rule.group(1))
    assert alpha, (
        "`.masthead-subtitle` no longer sets an rgba white. If it now uses an "
        "opaque colour, MASTHEAD_SUBTITLE_ALPHA should become 1.0 and this "
        "test should assert that instead — do not delete it."
    )
    assert float(alpha.group(1)) >= MarketReportBuilder.MASTHEAD_SUBTITLE_ALPHA, (
        f"the stylesheet renders the subtitle at {alpha.group(1)} but the band "
        f"is only guaranteed down to {MarketReportBuilder.MASTHEAD_SUBTITLE_ALPHA}"
    )


# ── the guarantee itself ────────────────────────────────────────────────────

@pytest.mark.parametrize("brand", BRANDS)
def test_both_band_stops_carry_the_title_and_the_muted_subtitle(brand):
    alpha = MarketReportBuilder.MASTHEAD_SUBTITLE_ALPHA
    for stop in band(brand):
        assert contrast("#ffffff", stop) >= AA, f"title on {stop}"
        seen = flatten_over("#ffffff", stop, alpha)
        assert contrast(seen, stop) >= AA, (
            f"the subtitle renders as {seen} on {stop} at "
            f"{contrast(seen, stop):.2f}:1"
        )


@pytest.mark.parametrize("brand", BRANDS)
def test_the_highlight_derives_against_the_band_not_the_raw_brand(brand):
    """
    `.masthead-highlight` reads `--accent-on-dark`. Derived against the raw
    colours it returned 3.74:1 for two brands and said so in a log; derived
    against the guaranteed band it clears AA for all six. This is the
    assertion that the derivation is fed the right surfaces.
    """
    stops = band(brand)
    role = property_builder.compute_color_roles(DEFAULT_ACCENT, stops)["theme_color_on_dark"]
    worst = min(contrast(role, s) for s in stops)
    assert worst >= AA, f"{role} on {stops} is {worst:.2f}:1"


def test_a_brand_already_dark_enough_is_not_dulled():
    """
    THE GUARD ON EVERY PROPERTY ABOVE. "Darken everything to #000000" passes
    each of them and destroys the brand. The band must stop at the first step
    that satisfies the invariant.

    `#18235c` is the platform navy and already carries the muted subtitle at
    7.77:1, so touching it at all is over-darkening. Note the invariant is the
    SUBTITLE, not opaque white: the first version of this test used coastal
    `#0E7490`, whose white clears AA at 5.36:1 while its 70% subtitle does
    not, and asserted it should be returned untouched. It was darkened,
    correctly, and the test was wrong about what the band promises.
    """
    already = "#18235c"
    alpha = MarketReportBuilder.MASTHEAD_SUBTITLE_ALPHA
    seen = flatten_over("#ffffff", already, alpha)
    assert contrast(seen, already) >= AA, "fixture no longer tests what it claims"
    assert band(already)[0].lower() == already.lower(), (
        "a colour that already carries its text was darkened anyway"
    )


@pytest.mark.parametrize("brand", BRANDS)
def test_the_derivation_is_idempotent(brand):
    """
    Feeding the band back in changes nothing — it stopped where it was
    satisfied rather than at a fixed number of steps. A constant function
    would also pass this, which is why the test above exists as well.
    """
    once = band(brand)
    twice = tuple(MarketReportBuilder({"report_type": "closed", "listings": []})
                  ._masthead_band(*once))
    assert twice == once, f"{once} -> {twice}"


def test_the_degraded_path_stays_unused_across_every_brand():
    """
    `_report_unreachable` prints "cannot reach 4.5:1 ... returning it anyway"
    and increments a counter. Before this change it fired on EVERY render, to
    a log nobody reads — the permanent unread warning this project keeps
    finding. The counter is the signal; this asserts it stays at zero.
    """
    before = property_builder.UNREACHABLE_CONTRAST_COUNT
    for brand in BRANDS + [DEFAULT_PRIMARY]:
        stops = band(brand)
        property_builder.compute_color_roles(DEFAULT_ACCENT, stops)
    assert property_builder.UNREACHABLE_CONTRAST_COUNT == before, (
        f"{property_builder.UNREACHABLE_CONTRAST_COUNT - before} contrast targets "
        f"could not be met. That used to be normal and is now a failure: the "
        f"band exists so this path is never taken."
    )


# ── the default is ours, not an affiliate's ─────────────────────────────────

def test_the_default_accent_is_the_platform_colour_not_an_affiliates_brand():
    """
    It was `#0d9488` — Luxury Estates' teal — so every account that had not
    picked an accent shipped someone else's identity, and a third of the
    masthead's audited failures were brand-independent because of it. D-098
    made the same call for the email: a default is not the affiliate's colour.
    """
    assert DEFAULT_ACCENT.lower() == "#4f46e5", (
        "the market default accent should be the platform default that "
        "templates.ts, social-templates.ts and the email all use"
    )
    assert DEFAULT_ACCENT.lower() not in {b.lower() for b in BRANDS}, (
        "the platform default is one of the affiliate brand colours again"
    )


def test_an_unbranded_report_still_produces_a_readable_band():
    """The defaults are a configuration like any other, and the one every
    account that has not chosen gets. It is measured, not assumed."""
    for stop in band(DEFAULT_PRIMARY, DEFAULT_ACCENT):
        assert contrast("#ffffff", stop) >= AA

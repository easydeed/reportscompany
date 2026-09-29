"""The price-band distribution chart (§7.3).

The stat cards above it already carry the exact counts, so this chart's job is
shape — which band is the market — and the assertions are about the things that
would quietly misrepresent that: a band dropped, a bar mis-scaled, the caption
disagreeing with the picture.
"""

import re
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from worker.market_builder import MarketReportBuilder  # noqa: E402
from worker.themes import derive_theme  # noqa: E402

BANDS = [
    {"label": "Under $700K", "count": 9},
    {"label": "$700K – $900K", "count": 18},
    {"label": "$900K – $1.1M", "count": 31},
    {"label": "$1.1M – $1.3M", "count": 21},
]


def render(bands, primary="#1B365D"):
    data = {
        "report_type": "price_bands", "city": "Irvine", "lookback_days": 30,
        "listings": [], "metrics": {}, "counts": {},
        "branding": {"agent_name": "A", "primary_color": primary},
        "price_bands": bands,
    }
    return MarketReportBuilder(data).render_html()


def chart(html):
    m = re.search(r'<div class="band-chart[^"]*">(.*?)</svg>', html, re.S)
    return m.group(1) if m else None


def bars(svg):
    """The data rects, excluding the 4px square baseline caps."""
    return [float(w) for w in re.findall(r'<rect x="\d+" y="\d+" width="([\d.]+)"', svg)
            if float(w) != 4]


def test_a_band_with_zero_listings_is_drawn_and_not_dropped():
    """The same distinction the trend chart draws one macro over.

    "Nothing is for sale above $1.6M" is a fact about the market and one of the
    more useful things on the page. A band that vanishes tells the reader
    nothing and looks like a shorter list. The first version of this chart used
    `selectattr('count')` and dropped them.
    """
    html = render(BANDS + [{"label": "$1.6M+", "count": 0}])
    svg = chart(html)
    assert "$1.6M+" in svg, "the empty band disappeared from the chart"
    assert ">none<" in svg, (
        "a zero band draws a zero-width bar, which reads as a missing row — it "
        "has to say so in words"
    )


def test_a_band_with_no_count_key_is_dropped():
    """No data is not the same as no listings, and only the second is drawn."""
    svg = chart(render(BANDS + [{"label": "Unknown"}]))
    assert "Unknown" not in svg


def test_bars_are_proportional_to_their_counts():
    """The one thing a bar chart must get right."""
    svg = chart(render(BANDS))
    widths = bars(svg)
    assert len(widths) == len(BANDS)
    counts = [b["count"] for b in BANDS]
    longest = max(range(len(counts)), key=lambda i: counts[i])
    assert widths[longest] == max(widths)
    # ratios hold, not just the ordering
    scale = widths[longest] / counts[longest]
    for w, c in zip(widths, counts):
        assert w == pytest.approx(c * scale, rel=0.01)


def test_only_the_largest_band_carries_a_number():
    """§7.3: never a number on every bar. The cards above carry the values;
    the chart carries the comparison, and labelling all four would duplicate
    the cards and clutter the shape they exist to show."""
    svg = chart(render(BANDS))
    values = re.findall(r'font-weight="600"[^>]*>([^<]+)<', svg)
    assert values == ["31"], values


def test_the_bars_wear_primary_ink_and_never_the_raw_brand_colour():
    primary = "#1B365D"
    ink = derive_theme(primary)["primary_ink"].lower()
    svg = chart(render(BANDS, primary=primary))
    fills = {f.lower() for f in re.findall(r'<rect[^>]*fill="([^"]+)"', svg)}
    assert fills == {ink}, fills


def test_band_labels_do_not_wear_the_series_colour():
    primary = "#0D9488"
    ink = derive_theme(primary)["primary_ink"].lower()
    svg = chart(render(BANDS, primary=primary))
    for fill in re.findall(r'<text[^>]*fill="([^"]+)"', svg):
        assert fill.lower() not in (ink, primary.lower()), fill


def test_one_band_is_not_a_distribution():
    assert chart(render(BANDS[:1])) is None
    assert chart(render([])) is None


def test_the_caption_counts_the_same_bands_the_chart_draws():
    """A caption that disagrees with the picture above it is worse than none.

    The first version counted only truthy counts and said "4 bands" under a
    chart showing five.
    """
    html = render(BANDS + [{"label": "$1.6M+", "count": 0}])
    assert "across 5 bands" in html
    assert "79 listings" in html


def test_the_cards_and_the_chart_show_the_same_bands():
    """D-107, inverted from the test that used to live here.

    That test asserted the caption's apology — "the cards above show the first
    4; the chart shows all 6" — which existed only to describe the defect. The
    cards render every band now, so the thing to protect is that they agree.
    A six-band market showing four cards above six bars is what this prevents.
    """
    six = BANDS + [{"label": "$1.3M – $1.6M", "count": 11}, {"label": "$1.6M+", "count": 5}]
    html = render(six)
    cards = re.findall(r'<div class="stat-card-label">([^<]*)</div>', html)
    bars = re.findall(r'text-anchor="end"[^>]*>([^<]+)</text>', chart(html))
    assert cards == [b["label"] for b in six], cards
    assert bars == [b["label"] for b in six], bars
    assert "the cards above show the first" not in html, (
        "the caption is still apologising for a layout that has been fixed"
    )


def test_the_chart_carries_no_script_and_no_external_reference():
    svg = chart(render(BANDS))
    assert "<script" not in svg and "http" not in svg

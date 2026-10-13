"""How a price-band distribution is drawn, on the page that now draws it.

WHAT MOVED, AND WHY THIS FILE DID NOT JUST GET DELETED
------------------------------------------------------
Until 2026-10-08 this file tested `band_distribution_chart` — an SVG of
horizontal bars rendered by `pricebands_layout`. `price_bands` joined
`V2_KINDS` on that date and renders Design's `_v2` page instead, whose body for
this kind is a five-column band table with an inline bar per row. **No report
type reaches the old chart any more**, so every assertion here was describing a
document that no longer renders — the same shape as a contrast baseline
outliving its template, which is a standing policy in this project.

Deleting the file was the other option and it is the wrong one. Six of the ten
assertions were about *the distribution*, not about the SVG: a band dropped, a
bar mis-scaled, no-data drawn as zero. Those concerns followed the data onto the
new page. So each is repointed, and the four that genuinely died with the old
chart are recorded below rather than silently lost — a concern that stops being
asserted and is not written down is how coverage disappears quietly.

    carried over                        | was
    ------------------------------------+----------------------------------------
    a zero band is drawn, not dropped   | same, and the word "none" became "0"
    no-count is not zero                | the old chart DROPPED it; this one
                                        | draws it as a dash (and the move
                                        | reintroduced `or 0` — see below)
    bars proportional to their counts    | share of the largest, not of the total
    no text wears the raw brand colour   | was asserted of the bar FILLS
    labels do not wear the series colour | same
    no script, no external reference     | asserted of the whole page now

    died with the old chart              | why
    -------------------------------------+---------------------------------------
    only the largest bar carries a number| Design puts the count beside EVERY
                                         | bar; it is a table row, and a row
                                         | with four values and no count is
                                         | missing a column
    the caption counts the bands drawn   | the `_v2` page has no caption. NOTE:
                                         | `_band_chart_note` still computes
                                         | one and nothing renders it —
                                         | `test_price_bands.py` still gates the
                                         | producer
    the cards and the chart agree (D-107)| the `_v2` page has no stat cards, so
                                         | there is no second place to disagree
                                         | with. The defect that test was
                                         | inverted from — four cards above six
                                         | bars — cannot be expressed here
    one band is not a distribution       | the old chart REFUSED at n=1. The
                                         | `_v2` body draws the one row, which
                                         | is correct for a table; the refusal
                                         | moved to the HEADLINE, gated in
                                         | test_market_v2_kinds.py

THE MOVE REINTRODUCED A DEFECT, AND THIS FILE IS WHAT CAUGHT IT
---------------------------------------------------------------
`_v2_bands_body` was written with `count = band.get("count") or 0`, which
renders a band carrying no `count` key as a hard zero — "nothing is for sale
above $1.6M", asserted of a band that was never counted. That is D-137's shape
(absent is not a default), and the old chart got it right by dropping such
bands. It was found by repointing `test_a_band_with_no_count_key_is_dropped`
rather than deleting it, which is the whole argument for repointing.
"""

import re
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from worker.market_builder import V2_KINDS, MarketReportBuilder  # noqa: E402
from worker.themes import derive_theme  # noqa: E402

BANDS = [
    {"label": "Under $700K", "count": 9},
    {"label": "$700K – $900K", "count": 18},
    {"label": "$900K – $1.1M", "count": 31},
    {"label": "$1.1M – $1.3M", "count": 21},
]


def test_this_file_is_pointed_at_the_page_that_actually_renders():
    """The premise of every assertion below, asserted first.

    If `price_bands` ever leaves `V2_KINDS`, these tests would render the old
    layout again and pass or fail for reasons that have nothing to do with what
    they say. Better to be told the premise moved.
    """
    assert "price_bands" in V2_KINDS


def render(bands, primary="#1B365D", **extra):
    data = {
        "report_type": "price_bands", "city": "Irvine", "lookback_days": 30,
        "listings": [], "metrics": {}, "counts": {},
        "branding": {"agent_name": "A", "primary_color": primary},
        "price_bands": bands,
        "ai_insights": None,
    }
    data.update(extra)
    return MarketReportBuilder(data).render_html()


def body(html):
    """The bands section, or None if the page did not render one."""
    m = re.search(r'<section class="bands">(.*?)</section>', html, re.S)
    return m.group(1) if m else None


def rows(section):
    """One string per data row, header excluded."""
    found = re.findall(r'<div class="brow">(.*?)\n  </div>', section, re.S)
    return found


def bar_widths(section):
    return [float(w) for w in re.findall(r'style="width: ([\d.]+)%"', section)]


def labels(section):
    return re.findall(r'<span class="blabel">([^<]*)</span>', section)


def counts(section):
    return re.findall(r'<span class="bcount">([^<]*)</span>', section)


# ─────────────────────────────────────────────────────────────────────────────
# Carried over from the old chart
# ─────────────────────────────────────────────────────────────────────────────

def test_a_band_with_zero_listings_is_drawn_and_not_dropped():
    """"Nothing is for sale above $1.6M" is a fact about the market.

    One of the more useful things on the page, and a band that vanishes tells
    the reader nothing while looking like a shorter list. The first version of
    the old chart used `selectattr('count')` and dropped them.

    The old chart also had to print the WORD "none", because a zero-width bar
    inside a chart reads as a missing row. Here the count sits beside the bar
    in a row that also carries a median, days and $/sq ft, so "0" is
    unambiguous — Design's placement, and the only one that survives a zero.
    """
    section = body(render(BANDS + [{"label": "$1.6M+", "count": 0}]))
    assert "$1.6M+" in labels(section), "the empty band disappeared"
    assert counts(section)[-1] == "0", counts(section)
    assert bar_widths(section)[-1] == 0


def test_a_band_with_no_count_key_is_not_drawn_as_zero():
    """No data is not no listings, and the row has to say which.

    The old chart dropped an uncounted band. This page draws it — its row still
    carries a label, a median, days and $/sq ft, so it is informative where an
    uncounted bar was not — but as a DASH with no bar, never as a `0`.

    `band.get("count") or 0` is what this forbids, and is what the first
    version of `_v2_bands_body` shipped with.
    """
    section = body(render(BANDS + [{"label": "Unknown"}]))
    assert "Unknown" in labels(section)
    assert counts(section)[-1] == "—", (
        f"an uncounted band rendered {counts(section)[-1]!r} — a claim about a "
        f"band nobody counted"
    )
    assert bar_widths(section)[-1] == 0


def test_an_uncounted_band_does_not_set_the_scale_for_the_others():
    """The bar scale is a max over the counts, and `None` is not a count.

    `max` over `[9, 18, None]` raises in Python 3, so this would have been a
    500 rather than a wrong picture — but only once an uncounted band reached
    production, which is the kind of discovery this suite exists to move
    earlier.
    """
    with_unknown = body(render(BANDS + [{"label": "Unknown"}]))
    without = body(render(BANDS))
    assert bar_widths(with_unknown)[:4] == bar_widths(without)


def test_bars_are_proportional_to_their_counts():
    """The one thing a bar chart must get right.

    A SHARE OF THE LARGEST COUNT, not of the total: Design's row is a
    comparison between bands, and a share of the total makes every bar short as
    soon as there are several bands. So the largest band is always 100%.
    """
    section = body(render(BANDS))
    widths = bar_widths(section)
    assert len(widths) == len(BANDS)
    band_counts = [b["count"] for b in BANDS]
    widest = max(band_counts)
    assert widths[band_counts.index(widest)] == 100
    for w, c in zip(widths, band_counts):
        assert w == pytest.approx(c / widest * 100, abs=0.5)


def test_no_text_in_the_bands_body_wears_the_raw_brand_colour():
    """The old chart asserted this of the bar FILLS; here it is the text.

    A bar is a filled rectangle with nothing on it, so `--primary` is the right
    token for it — the contrast rules govern text, and the count moved OUT of
    the bar precisely so it is never ink on brand. What must not happen is a
    13px label or value taking the raw brand colour, which is D-170's and
    D-177's whole subject and measured as low as 1.98:1 on a shipped palette.
    """
    primary = "#0D9488"
    html = render(BANDS, primary=primary)
    section = body(html)
    assert "background: var(--primary)" in html, (
        "the bar fill stopped using the brand colour, which is the one place "
        "on this row the raw brand belongs"
    )
    for cls in ("blabel", "bcount", "bcell"):
        rule = re.search(r"\." + cls + r" \{([^}]*)\}", html, re.S)
        assert rule, cls
        assert "var(--primary)" not in rule.group(1), (
            f".{cls} takes the raw brand colour; it is 13px text"
        )
    ink = derive_theme(primary)["primary_ink"].lower()
    assert primary.lower() not in section.lower()
    assert ink not in section.lower()


def test_band_labels_do_not_wear_the_series_colour():
    """A label coloured like its own bar reads as a highlight it is not."""
    html = render(BANDS, primary="#0D9488")
    rule = re.search(r"\.blabel \{([^}]*)\}", html, re.S).group(1)
    assert "var(--ink)" in rule, rule


#: The only hosts the `_v2` page is allowed to reference, and why.
#:
#: PDFShift fetches what the document references, so each one is a third party
#: in the render path. Geist is Design's typeface and the page is theirs; the
#: alternative is self-hosting two families as base64, which would put ~200KB
#: of font in every HTML payload. Recorded here so that a second host — an
#: analytics pixel, a CDN'd stylesheet, an image proxy — is a decision somebody
#: has to make twice.
ALLOWED_EXTERNAL_HOSTS = {"fonts.googleapis.com", "fonts.gstatic.com"}


def test_the_page_carries_no_script_and_no_unrecorded_external_reference():
    """Asserted of the whole page now, not of one SVG."""
    html = render(BANDS)
    assert "<script" not in html
    hosts = set(re.findall(r'https?://([^/\s"\'<>]+)', html)) - {"www.w3.org"}
    assert hosts <= ALLOWED_EXTERNAL_HOSTS, hosts - ALLOWED_EXTERNAL_HOSTS


# ─────────────────────────────────────────────────────────────────────────────
# What replaced the refusal at n=1
# ─────────────────────────────────────────────────────────────────────────────

def test_one_band_still_renders_a_row_and_still_makes_no_claim():
    """The old chart drew nothing at n=1. This page draws the row.

    Both are right for what they are: one bar is not a distribution, but one
    table row is a row. The refusal moved to the headline, where it belongs —
    a single band is 0 days ahead of an average that is itself, so
    `_v2_fastest_headline` returns the plain title. That boundary is gated in
    `test_market_v2_kinds.py`; what is asserted here is that the body
    does not quietly acquire a "Fastest" tag on a field of one.
    """
    section = body(render([{"label": "Under $700K", "count": 9, "avg_dom": 12}]))
    assert len(labels(section)) == 1
    assert "Fastest" not in section and "Slowest" not in section, (
        "a single band was tagged fastest or slowest against nothing"
    )


def test_no_bands_says_so_instead_of_heading_empty_space():
    """Five column headings above nothing reads as a broken page.

    `v2_bands` is a dict, so it is truthy for this kind whether or not there
    are bands — the template's outer test says "this kind has a bands body".
    The empty state is rendered, not the section suppressed: the standing
    instruction on an empty search is that the report renders and says the
    search returned nothing.
    """
    section = body(render([]))
    assert section is not None, "the bands section vanished entirely"
    assert "Price band" not in section, "a column header over no rows"
    assert "returned no listings" in section

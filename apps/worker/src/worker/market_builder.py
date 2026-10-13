"""
Market Report Builder
=====================

Renders brand-driven market reports (8 types) using a single Jinja2 template.
Colors come from the agent's branding (primary_color, accent_color).

Report types → layout mapping: see LAYOUT_MAP below, which is the only
declaration of it. This docstring used to repeat the mapping and had drifted —
it filed price_bands under "Analytics" when price_bands has had its own
`pricebands` layout and its own macro for some time. A second copy of a mapping
is a second thing to keep right, and this one was not kept right, so the copy
is gone rather than corrected. `test_the_layout_map_matches_the_macro_that_runs`
checks LAYOUT_MAP against an instrumented render.

Usage:
    builder = MarketReportBuilder(report_data)
    html = builder.render_html()
"""

import logging
from datetime import datetime
from typing import Any, Dict
from pathlib import Path
from jinja2 import Environment, FileSystemLoader, select_autoescape

from worker.property_builder import (
    compute_color_roles,
    darken_until_readable,
    ink_on,
    _darken,
    safe_url,
    sanitize_context_urls,
)
from worker.template_filters import (
    format_currency,
    format_currency_short,
    format_number,
    truncate,
)
from worker.ai_market_narrative import generate_market_pdf_narrative
from worker.compute.monthly_trend import (
    MIN_CLOSED_FOR_MEDIAN,
    count_series,
    median_series,
)
from worker.themes import derive_theme

logger = logging.getLogger(__name__)


def _first_present(source, *keys):
    """First key whose value is not None, or None. NOT `a or b`.

    D-108. `source.get("a") or source.get("b", 0)` treats a real 0 as absent
    and falls through — the same zero-is-falsy defect as Jinja's
    `{% if value %}`, in Python. It is the more damaging half of the pair,
    because it destroys the distinction before the template can render it:
    a studio (0 bedrooms) and a listing with no bed count both arrived as 0,
    and the template hid both, which is why it read as correct.
    """
    for key in keys:
        value = source.get(key)
        if value is not None:
            return value
    return None


def _pct(val) -> str | None:
    """Convert a ratio (0-1 or 90-110 range) to a percentage string for prompts."""
    if val is None:
        return None
    v = float(val)
    if v < 2:  # looks like 0.98 ratio
        return f"{v * 100:.1f}"
    return f"{v:.1f}"


# ─────────────────────────────────────────────────────────────────────────────
# Constants
# ─────────────────────────────────────────────────────────────────────────────

DEFAULT_PRIMARY = "#18235c"
#: #4F46E5, not #0d9488. The old default was Luxury Estates' teal — an
#: affiliate's brand shipping as the platform default, so every account that
#: had not picked an accent rendered someone else's identity. The 2026-09-29
#: contrast audit measured the consequence: a third of the masthead's failures
#: were brand-INDEPENDENT, because the band always ended in that teal.
#:
#: #4F46E5 is not a new colour. It is DEFAULT_PRIMARY_COLOR in
#: apps/web/lib/templates.ts and social-templates.ts, and the email moved to it
#: for the same reason in D-098: a default is not the affiliate's colour —
#: nobody chose it, and it is ours to set. The market PDF was the last surface
#: still defaulting to something else, so an unbranded account's PDF and its
#: email did not match. Now they do.
DEFAULT_ACCENT = "#4F46E5"

TEMPLATES_DIR = Path(__file__).parent / "templates" / "market"
TEMPLATE_PATH = "market.jinja2"

LAYOUT_MAP: Dict[str, str] = {
    "new_listings_gallery": "gallery",
    "featured_listings": "gallery",
    "open_houses": "gallery",
    "market_snapshot": "market_narrative",
    "closed": "closed_inventory",
    "inventory": "closed_inventory",
    "price_bands": "pricebands",
    "new_listings": "analytics",
}

ALL_REPORT_TYPES = list(LAYOUT_MAP.keys())


# ─────────────────────────────────────────────────────────────────────────────
# PDF-COMPREHENSIVE — per-report PDF caps + honest "what's shown" copy
# ─────────────────────────────────────────────────────────────────────────────
# Each report type has a clear narrative purpose. The cap matches the
# story we're telling, and the truncation/more-listings copy tells the
# reader exactly what they're seeing vs what exists in the market.
#
# Templates:
#   {city}      — report_data.city                (e.g. "Irvine")
#   {lookback}  — report_data.lookback_days       (e.g. 7)
#   {showing}   — number of listings rendered
#   {total}     — total available in the dataset
#   {remaining} — total - cap (only used by more_template)
#
# more_template = None  →  no "+ N more …" callout (full inventory shown).

# CAPS-SPLIT-SNAPSHOT-CATALOG — Market reports now split into two modes:
#
#   SNAPSHOT (curated sample):
#     market_snapshot, price_bands, featured_listings
#   CATALOG (ALL matching listings):
#     closed, inventory, new_listings, new_listings_gallery, open_houses
#
# THE SNAPSHOT MODES SAID "1-page" AND RENDER TWO. Corrected 2026-09-28 with
# measured numbers rather than aspirational ones (D-102): the caps are two to
# three times what page 1 holds, and page 1's capacity is now a known constant
# per type rather than a guess.
#
#   market_snapshot    cap 9   page 1 holds 3   -> 2 pages
#                              (and 0 by design when the trend chart is on
#                               page 1, with the listings starting on page 2)
#   price_bands        cap 8   page 1 holds 3   -> 2 pages
#   featured_listings  cap 12  page 1 holds 6   -> 2 pages
#
# The capacities are pinned in tests/test_narrative_box.py::PAGE_1_CAPACITY and
# emitted by `scripts/measure_market_pagination.py --emit-capacity`. Cutting a
# cap to its page-1 capacity would make that type genuinely one page with a
# smaller sample; that is a product decision and has not been taken.
#
# CATALOG types have `more_template = None` and a high cap (100-200) so the
# PDF renders every matching listing. The previous "+ N more — contact me for
# the complete list" callout was dishonest (agents had no way to produce
# that list) and is now removed across the board.
PDF_CONFIG: Dict[str, Dict[str, Any]] = {
    # ── SNAPSHOT mode ───────────────────────────────────────────────────────
    "market_snapshot": {
        "cap": 9,
        "section_label": "Recent Activity",
        "truncation_template": "Recent market activity — a curated sample of {showing} listings in {city}.",
        "more_template": None,
    },
    "price_bands": {
        "cap": 8,
        "section_label": "Example Listings by Price Band",
        "truncation_template": "Sample listings shown — see band totals above for complete counts.",
        "more_template": None,
    },
    "featured_listings": {
        "cap": 12,
        "section_label": "Hand-Picked Highlights",
        "truncation_template": "Showing {showing} hand-picked listings.",
        "more_template": None,
    },
    # ── CATALOG mode ────────────────────────────────────────────────────────
    "closed": {
        "cap": 200,
        "section_label": "Recent Closed Sales",
        "truncation_template": "All {total} closed sales in {city} in the last {lookback} days.",
        "more_template": None,
    },
    "inventory": {
        "cap": 200,
        "section_label": "Active Inventory",
        "truncation_template": "All {total} active listings in {city}.",
        "more_template": None,
    },
    "new_listings": {
        "cap": 200,
        "section_label": "New Listings",
        "truncation_template": "All {total} new listings in {city} in the last {lookback} days.",
        "more_template": None,
    },
    "new_listings_gallery": {
        "cap": 200,
        "section_label": "New Listings Gallery",
        "truncation_template": "Gallery of all {total} new listings in {city}.",
        "more_template": None,
    },
    "open_houses": {
        "cap": 100,
        "section_label": "Open Houses This Week",
        "truncation_template": "All {total} open houses scheduled this week in {city}.",
        "more_template": None,
    },
}


#: Design's dash for a value that exists and is empty, and its wording for a
#: value nothing produced. Two different facts, two different marks — collapsing
#: them is D-137's defect (absent is not a default) in presentation.
V2_DASH = "\u2014"
V2_NO_DATA = "no data"


def _ratio_as_percent(value):
    """A close-to-list ratio in PERCENT, whatever scale it arrived on.

    D-178. The same key carries two scales depending on which producer filled
    it: `compute/extract.py:79` computes `round((cp/lp)*100, 2)` and
    `compute/calc.py:54` rounds that average, so production is percent — while
    `measure_market_pagination.report_data`, the fixture under
    `test_market_layout_map` and several others, supplies `0.982`.

    The templates already knew. `macros.jinja2` carries
    `ratio * 100 if ratio < 2 else ratio` at TWO sites — the same guess,
    written twice, in a file where it cannot be unit-tested. The page renders
    correctly today because of it, which is why nobody had to fix the key.

    So the guess moves here, once, where it has a test. The threshold is
    unchanged on purpose: a close-to-list ratio of 2 would mean selling at
    200% of asking, and a FRACTION of 2 would mean 200x — both absurd, so the
    gap between the scales is enormous and 2 sits in the middle of it. What
    changes is that there is one copy and it is reachable from a test.

    Returns `None` for anything non-numeric or zero, because a ratio of zero is
    not a sale at asking and must not render as `0.0% of asking`.
    """
    if not isinstance(value, (int, float)) or isinstance(value, bool):
        return None
    if not value:
        return None
    return float(value) * 100 if value < 2 else float(value)


def _v2_money(value) -> str:
    """`$1.46M` / `$641K` — Design's casing, via the shared filter's `upper`.

    Not a second money formatter. `format_currency_short` takes a flag so the
    lowercase `k` every other surface ships stays untouched.
    """
    if not isinstance(value, (int, float)) or isinstance(value, bool) or not value:
        return V2_DASH
    return format_currency_short(value, upper=True)


def _v2_days(value) -> str:
    """`42 d`. ZERO IS A REAL ANSWER — a same-day sale reports 0 since D-105,
    so this tests the type rather than the truthiness (D-108)."""
    if not isinstance(value, (int, float)):
        return V2_DASH
    return f"{int(value)} d"


def _v2_count(value) -> str:
    if not isinstance(value, (int, float)):
        return V2_DASH
    return f"{int(value):,}"


def _v2_known_count(band: Dict[str, Any]):
    """A band's listing count as an int, or `None` when it is not reported.

    THE TWO ABSENCES ARE DIFFERENT and this is the function that keeps them so.
    `{"label": "$1.6M+", "count": 0}` means nothing is for sale up there, which
    is one of the more useful facts a bands report carries. `{"label": "$1.6M+"}`
    means the band was not counted. `band.get("count") or 0` renders the second
    as the first — a claim the data does not make, which is D-137's shape
    (absent is not a default) on a row that reads as fact.

    The legacy band chart drew the first and DROPPED the second
    (`test_a_band_with_no_count_key_is_dropped`). This page draws both, because
    its row carries a label, a median, days and $/sq ft beside the bar, so an
    uncounted band is informative where an uncounted bar was not — but it draws
    the uncounted one as a dash with no bar, never as a zero.

    Bools are excluded explicitly: `True` is an `int` in Python and `1` is a
    plausible-looking count.
    """
    value = band.get("count")
    if not isinstance(value, (int, float)) or isinstance(value, bool):
        return None
    return int(value)


def _v2_beds_baths(item) -> str:
    """`3/2`, and `3/-` when only one side is known.

    Not `f"{beds}/{baths}"` on raw values: a missing bath count would render
    `3/None`, and a 0 would render as missing under an `or` chain. Both are
    D-108/D-168's shape, and both have shipped in this repo before.
    """
    beds = item.get("beds")
    baths = item.get("baths")
    def one(v):
        if isinstance(v, (int, float)):
            return f"{v:g}"
        return V2_DASH
    if not isinstance(beds, (int, float)) and not isinstance(baths, (int, float)):
        return V2_DASH
    return f"{one(beds)}/{one(baths)}"


#: THE MIGRATION SEAM. Report types rendered by Design's `_v2` page rather than
#: by `market.jinja2` + `_base/base.jinja2`.
#:
#: The property surface's equivalent is `property_builder.V2_THEMES`, and it is
#: the same reasoning: eight kinds cannot land at once, the ones that have not
#: moved must keep rendering exactly as they do, and "which document is this"
#: has to be one readable fact rather than a condition spread through a
#: template. A kind not in here is untouched by the redesign.
#:
#: `closed` is first because it is the table kind WITH continuation pages, so it
#: exercises `header.start_at = 1`, `footer.start_at = 1` and the row capacity
#: together — the architectural risks, which if wrong invalidate the other
#: seven. It is NOT first for contrast: all six `market__*` baseline rows are
#: badge selectors on `new_listings` and `price_bands`, so wiring `closed`
#: closes zero of them, by construction. See
#: docs/MARKET_TOKEN_MAPPING_2026-10-07.md.
V2_KINDS = frozenset({"closed", "new_listings", "price_bands", "inventory",
                      "new_listings_gallery", "open_houses",
                      "featured_listings"})

#: Design's shared page. One template, dispatched on kind, per their README.
V2_TEMPLATE_PATH = "_v2/report.jinja2"

#: `#5E636B` — the muted neutral, 6.05:1 on white, from Design's neutral list.
#: The `vs. list` column takes it at weight 400 when the sale did not clear
#: asking; `accent_ink` at 600 when it did. Named because it is a threshold's
#: other side, not a decoration.
V2_MUTED = "#5E636B"

#: The label beside the big number sits in a FIXED 50px box (Design: "band
#: height is therefore fixed: nothing in it grows with data"), so the type size
#: steps down by character count rather than wrapping. Their ladder.
V2_LABEL_LADDER = ((26, 22), (34, 18), (44, 15))
V2_LABEL_MIN_PX = 13


#: THE TABLE'S COLUMNS, PER KIND. Design gives all three table kinds the same
#: grid — `1fr 64 72 108 72 44` — and changes two of the six headings. Data
#: rather than a branch in the template, because "which heading goes here" is a
#: per-kind fact and a template `{% if %}` chain over kinds is the dispatch the
#: `_v2` architecture exists to remove.
#:
#: `price` and `fifth` name what the fifth and fourth columns MEAN, so the row
#: builder fills one shape and the page reads one shape whichever kind rendered.
V2_TABLE_COLUMNS = {
    "closed": {"price": "Sold for", "fifth": "vs. list",
               "noun": "sales", "noun_one": "sale"},
    "new_listings": {"price": "List price", "fifth": "Listed",
                     "noun": "new listings", "noun_one": "new listing"},
    # Design: "same table; `vs. list` becomes `Status`: `New` in `accent_ink`
    # 600 when DOM <= 7, else `—` #5E636B 400". The noun is "homes for sale"
    # and not "listings" — an inventory report counts what is ON the market,
    # and "212 listings" reads as activity where "212 homes for sale" reads as
    # stock. Their band label says "homes for sale in {area}" for the same
    # reason, so the count line matches it.
    "inventory": {"price": "List price", "fifth": "Status",
                  "noun": "homes for sale", "noun_one": "home for sale"},
}

#: Design's page-1 photo grid per gallery kind, from their per-kind table.
#:
#: COLUMNS ONLY. The ROW count on a continuation page is not in their package —
#: their continuation section covers "closed, inventory, new_listings table"
#: and says nothing about a grid — so it is measured rather than quoted. The
#: page-1 row count IS theirs and is what the band leaves room for.
V2_GRID = {
    "new_listings_gallery": {"cols": 3, "rows_page_1": 2},
    "open_houses": {"cols": 3, "rows_page_1": 3},
    "featured_listings": {"cols": 2, "rows_page_1": 2},
}

#: `featured_listings` is the one gallery kind with its OWN card, not a
#: different grid of the same card. Design: price plate 18px (against 15),
#: address 15px/600 (against 13), and beds/baths/sq ft as three stacked
#: mini-stats to the right instead of one meta line underneath. Four cards on a
#: page can afford the size; nine cannot.
V2_FEATURED_CARD = "featured"
V2_LISTING_CARD = "listing"

#: Design's `Status` rule for `inventory`: "New" at or under this many days.
#:
#: SEVEN, NOT "a week" — and the boundary is INCLUSIVE, which is what their
#: `<= 7` says. A listing at exactly 7 days is new; at 8 it is not. Written
#: down because `< 7` and `<= 7` differ on one day in seven and neither reads
#: wrong in a diff.
V2_NEW_WITHIN_DAYS = 7


#: Design's slowest-band tag, from their neutral list, quoted with the ratio
#: they measured: "Slowest-band tag `#B42318` (5.9:1)". The FASTEST tag is
#: `accent_ink`, which is derived — only the slowest one is a fixed hex,
#: because "slow" is not a brand colour on any brand.
V2_SLOW_TAG = "#B42318"

#: Design's headline rule for the bands kind, stated in their README §per-kind:
#: "{band} is moving fastest" only when that band has >=10 listings and is >=3
#: days faster than the area average, else the plain title "{Area} · Price
#: Bands"; every headline hidden under 10 sales/listings.
#:
#: NAMED CONSTANTS BECAUSE THEY ARE A THRESHOLD SOMEONE CHOSE. Inline, the next
#: reader cannot tell 10 from an arbitrary 10, and the rule's whole character is
#: that it REFUSES to make the claim on thin data.
V2_FASTEST_MIN_LISTINGS = 10
V2_FASTEST_MIN_DAYS_AHEAD = 3

#: The big number's size per kind. Design: 88px, "snapshot: 96px; bands: 64px
#: headline" — a price range is wider than a count and does not fit at 88.
V2_BIG_PX = {"price_bands": 64, "market_snapshot": 96}
V2_BIG_PX_DEFAULT = 88


def _v2_listed_label(days) -> str:
    """Design's `Listed` column: "Today" at 0 days, else "n d ago".

    ZERO IS THE INTERESTING VALUE and it is why this is not a format string:
    a listing that went live today reports 0, which `or` would read as missing
    and render as a dash. The same defect as D-108's `or` chains, on the field
    whose zero is the whole point of a new-listings report.
    """
    if not isinstance(days, (int, float)) or isinstance(days, bool):
        return V2_DASH
    days = int(days)
    return "Today" if days == 0 else f"{days} d ago"


def _v2_card_specs(item) -> str:
    """`"3 bd / 2 ba / 1,480 sq ft"`, dropping whichever parts are absent.

    Built from the parts that exist rather than from a format string, because
    a format string renders `None bd / None ba` and an `or` chain renders a
    studio's 0 bedrooms as missing (D-108, D-168 — both have shipped here).
    """
    parts = []
    beds = item.get("beds")
    baths = item.get("baths")
    sqft = item.get("sqft")
    if isinstance(beds, (int, float)) and not isinstance(beds, bool):
        # "STUDIO", NOT "0 bd". The legacy card said Studio and
        # `test_zero_bedrooms_renders_as_a_studio` is a gate written because
        # zero bedrooms is a real property and an `or` chain eats it. "0 bd" is
        # not wrong so much as not what the thing is called, and a listing that
        # reads "0 bd" looks like missing data to the reader it is for.
        parts.append("Studio" if int(beds) == 0 else f"{int(beds)} bd")
    if isinstance(baths, (int, float)) and not isinstance(baths, bool):
        shown = int(baths) if float(baths).is_integer() else baths
        parts.append(f"{shown} ba")
    if isinstance(sqft, (int, float)) and not isinstance(sqft, bool) and sqft:
        parts.append(f"{int(sqft):,} sq ft")
    return " / ".join(parts)


def _v2_open_house_label(day) -> str:
    """`"Sat 11 Oct"` — Design's From/To cells.

    Day name first because that is what a reader scans for on an open-house
    report: "is there a Sunday one" is the question, not "is it the 12th".
    """
    return f"{day.strftime('%a')} {day.day} {day.strftime('%b')}"


def _v2_label_size(label: str) -> int:
    """Design's size ladder for the band label, by character count."""
    n = len(label or "")
    for limit, size in V2_LABEL_LADDER:
        if n <= limit:
            return size
    return V2_LABEL_MIN_PX


def _pdf_config_for(report_type: str) -> Dict[str, Any]:
    """Return the PDF_CONFIG entry for a report type (with safe fallback)."""
    return PDF_CONFIG.get(report_type, PDF_CONFIG["market_snapshot"])


class MarketReportBuilder:
    """
    Builds brand-driven HTML market reports using Jinja2 templates.

    Colors derive from branding.primary_color and branding.accent_color.
    Falls back to navy + teal when brand colors aren't provided.
    """

    def __init__(self, report_data: Dict[str, Any]):
        self.report_data = report_data

        self.report_type: str = report_data.get("report_type", "market_snapshot")
        if self.report_type not in LAYOUT_MAP:
            logger.warning(
                "Unknown report_type '%s', falling back to market_snapshot",
                self.report_type,
            )
            self.report_type = "market_snapshot"

        self.layout: str = LAYOUT_MAP[self.report_type]

        # Jinja2 environment rooted at templates/market/
        self.env = Environment(
            loader=FileSystemLoader(str(TEMPLATES_DIR)),
            autoescape=select_autoescape(["html", "xml", "jinja2"]),
            trim_blocks=True,
            lstrip_blocks=True,
        )
        self.env.filters["format_currency"] = format_currency
        self.env.filters["format_currency_short"] = format_currency_short
        self.env.filters["format_number"] = format_number
        self.env.filters["truncate"] = truncate

    # ── §7.1 masthead title fitting ────────────────────────────────────────

    #: Characters that fit on one line of `.masthead-left` (474px, 65% of the
    #: full-bleed row) at each step, MEASURED in this repo's fallback stack and
    #: then cut by ~12%.
    #:
    #: WHY THE CUT. The template asks Google Fonts for Outfit, and the container
    #: these were measured in has no network, so they are fallback-font widths.
    #: Outfit's advance widths are not these. The margin makes the ladder
    #: conservative rather than exact — and the HEIGHT does not depend on it
    #: either way, which is the property page-1 capacity actually needs. A size
    #: that turns out slightly too large in Outfit costs an ellipsis, not a
    #: wrapped line and not a shifted page.
    #:
    #: measured: 24px/31 chars · 21px/38 · 18px/43 · 16px/49 · 14px/56
    _TITLE_LADDER = ((27, 24), (33, 21), (38, 18), (43, 16))
    _TITLE_MIN_PX = 14

    def _masthead_title_px(self, text: str) -> int:
        """Largest step whose measured capacity holds `text` on one line.

        The masthead's title is "<report type> — <city>", and cities are
        unbounded, so at 24px a long one wrapped to a second line and moved page
        1 by 0.300in — which is how page-1 capacity came to depend on which city
        an affiliate reports (D-102). It sets smaller instead now, inside a box
        of fixed height, so the page below it does not move at all.
        """
        n = len(text or "")
        for limit, px in self._TITLE_LADDER:
            if n <= limit:
                return px
        return self._TITLE_MIN_PX

    # ── §7.3 price-band distribution ───────────────────────────────────────

    def _band_chart_note(self):
        """The sample line under the band chart, or None.

        Says what the bars are counting, and — when there are more bands than
        the stat cards show — that the cards are the partial view rather than
        the chart. Four cards beside six bars with nothing said about it reads
        as a rendering fault.
        """
        bands = self.report_data.get("price_bands") or []
        # Mirror the macro's filter exactly: a band with count 0 IS drawn — an
        # empty price band is a fact about the market — so it counts here too.
        # The first version used `if b.get("count")`, which said "4 bands"
        # under a chart showing five. A caption that disagrees with the picture
        # above it is worse than no caption.
        counted = [b for b in bands if b.get("count") is not None]
        if len(counted) < 2:
            return None
        total = sum(b["count"] for b in counted)
        # The clause that used to follow — "the cards above show the first 4;
        # the chart shows all 6" — existed only to describe D-107, and D-107 is
        # fixed: the cards render every band now, so the caption has nothing to
        # apologise for.
        note = f"Active listings by price band · {total:,} listings across {len(counted)} bands"
        # D-111: when the boundaries came from this period's results rather
        # than from twelve months of closings, the page says so. Bands that
        # may move between reports look identical to bands that will not, and
        # the whole point of the change is that a reader can compare two runs.
        caveat = self.report_data.get("price_bands_note")
        if caveat:
            note = f"{note} · {caveat}"
        return note

    # ── §7.3 median trend ──────────────────────────────────────────────────

    #: Which monthly series each report type carries, and nothing for the rest.
    #:
    #: `market_snapshot` answers "how is this market doing", so it gets the
    #: median price line. `inventory` answers "what is for sale and how fast is
    #: it moving", so it gets the SALES PACE — closings per month.
    #:
    #: §7.3 asked for a months-of-supply trend on the inventory report and that
    #: is not buildable; compute/monthly_trend.count_series explains why, and
    #: the short version is that MOI's numerator is total CURRENT active
    #: inventory and no past month's active count is recoverable from a feed
    #: fetched as Active/Pending/Closed. The pace is MOI's denominator and is
    #: knowable, so that is what ships, labelled as what it is.
    #: `inventory` WAS HERE AND IS NOT ANY MORE, AND THAT IS A REAL LOSS.
    #:
    #: Design's `_v2` page for `inventory` is the shared band over the listings
    #: table and specifies no chart, so from 2026-10-08 the sales-pace series
    #: has nowhere to render. It is removed from this map rather than left in
    #: it, because THIS MAP IS ALSO THE SHOPPING LIST: `TREND_REPORT_TYPES`
    #: below is derived from it and is what `tasks.py` reads to decide whether
    #: to pay for the twelve-month closings fetch (D-113). Leaving `inventory`
    #: here would buy a year of rows for a chart that cannot draw — "a fetch
    #: whose answer is never used", which is the exact failure the comment on
    #: `TREND_REPORT_TYPES` was written to prevent, arriving from the other
    #: direction.
    #:
    #: WHAT IS LOST, stated plainly because it is a product decision and not a
    #: cleanup: the inventory report no longer carries any trend. §7.3 asked
    #: for a months-of-supply trend, that is not buildable (no past month's
    #: active count is recoverable from a feed fetched as
    #: Active/Pending/Closed), and the pace — MOI's denominator, which IS
    #: knowable — is what shipped instead, labelled as what it is. That
    #: labelling is why it was honest. Design's spec replaces it with nothing.
    #:
    #: `count_series`, the pace note ("past inventory levels are not
    #: recoverable") and the whole of `compute/monthly_trend` are UNTOUCHED, so
    #: restoring it is adding this one line back plus a slot on the page. The
    #: producer surviving with no consumer is recorded in the defect list
    #: rather than deleted, which is D-181's lesson applied before the fact
    #: instead of after it.
    TREND_SERIES = {
        "market_snapshot": "median",
    }

    def _build_monthly_trend(self):
        """(series, note, fmt) for the trend chart, or (None, None, None).

        Both series come from `closed_history` — closed rows carrying
        `close_date` and `close_price`, which one `minclosedate = today - 365`
        fetch already returns. Neither is the 13-request count series decision
        01 priced; see compute/monthly_trend.py.

        Everything here fails to None. A market report with no trend is a
        complete report; a trend drawn from the wrong rows is not.
        """
        kind = self.TREND_SERIES.get(self.report_type)
        if not kind:
            return None, None, None

        history = self.report_data.get("closed_history")
        if not history:
            return None, None, None

        truncated = bool(self.report_data.get("closed_history_truncated"))
        try:
            if kind == "median":
                series = median_series(history, truncated=truncated)
            else:
                series = count_series(history, truncated=truncated)
        except Exception as e:  # pragma: no cover - defensive, as the narrative is
            logger.warning("monthly trend failed (non-fatal): %s", e)
            return None, None, None

        if not series:
            return None, None, None

        total = sum(p["n"] for p in series)
        if kind == "median":
            drawn = [p for p in series if p["value"] is not None]
            note = (
                f"Median closed price by month · {len(drawn)} of {len(series)} months "
                f"shown · {total:,} sales · months with fewer than "
                f"{MIN_CLOSED_FOR_MEDIAN} closings are left blank"
            )
            return series, note, "currency"

        note = (
            f"Homes sold per month · {total:,} sales over {len(series)} months · "
            f"sales pace, not months of supply — past inventory levels are not recoverable"
        )
        return series, note, "number"

    # ── colour resolution ──────────────────────────────────────────────────

    def _resolve_colors(self) -> tuple[str, str]:
        """Return (primary_color, accent_color) from branding, with defaults."""
        branding = self.report_data.get("branding") or {}
        primary = branding.get("primary_color") or DEFAULT_PRIMARY
        accent = (
            self.report_data.get("accent_color")
            or branding.get("accent_color")
            or DEFAULT_ACCENT
        )
        return primary, accent

    #: The subtitle's opacity in `.masthead-subtitle`. The band is guaranteed
    #: readable for text at THIS alpha, not for opaque white, because the
    #: translucent value is the one that was failing — 2.60:1 on the old
    #: default accent, for every brand. Guaranteeing the harder case makes the
    #: opaque title safe by construction and keeps the muted subtitle a design
    #: element rather than something the fix has to flatten away.
    #:
    #: It is pinned here and asserted against the stylesheet by
    #: test_masthead_contrast.py, so the two halves of one decision cannot
    #: drift — the same contract as §7.2's narrative box.
    MASTHEAD_SUBTITLE_ALPHA = 0.7

    def _masthead_band(self, primary: str, accent: str) -> tuple[str, str]:
        """The masthead gradient's two stops, each dark enough to carry its text.

        WHY THE BAND AND NOT THE TEXT (D-112). The gradient ran from the raw
        brand to the raw accent with every label hardcoded `#ffffff`. Measured
        across the audit's six brands, **no single text colour clears 4.5:1 on
        both ends for three of them** — white fails on amber and lime,
        near-black fails on coastal and violet. Choosing a better text colour
        cannot fix a band whose ends are that far apart in luminance; the band
        is the defect.

        So each stop is darkened until the text on it is readable, and stops
        at the first step that works — a brand already dark enough is returned
        untouched rather than dulled to a safe constant.

        Result across those six brands: title 7.41–7.57:1, subtitle 4.53:1,
        and `theme_color_on_dark` 4.53–4.63:1 where it previously reported
        3.74:1 and logged that it could not do better.
        """
        return (
            darken_until_readable(primary, "#ffffff", self.MASTHEAD_SUBTITLE_ALPHA),
            darken_until_readable(accent, "#ffffff", self.MASTHEAD_SUBTITLE_ALPHA),
        )

    # ── context builders ──────────────────────────────────────────────────

    def _build_header_context(self) -> Dict[str, Any]:
        data = self.report_data
        report_titles = {
            "new_listings_gallery": "New Listings",
            "featured_listings": "Featured Listings",
            "open_houses": "Open Houses",
            "market_snapshot": "Market Snapshot",
            "closed": "Closed Sales",
            "inventory": "Active Inventory",
            "price_bands": "Price Bands",
            "new_listings": "New Listings",
        }
        counts = data.get("counts") or {}
        total = sum(counts.values()) if counts else data.get("total_listings", 0)
        title = report_titles.get(self.report_type, "Market Report")
        city = data.get("city", "")
        return {
            "title": title,
            "subtitle": data.get("filters_label", ""),
            "city": city,
            "lookback_days": data.get("lookback_days", 30),
            "total_count": total,
            # §7.1 — the masthead renders "<title> — <city>" on ONE line in a
            # box of fixed height. This is the size that keeps it there.
            "title_px": self._masthead_title_px(f"{title} — {city}" if city else title),
        }

    def _build_listings_context(self) -> Dict[str, Any]:
        """Build the listings context plus the "what's shown vs what
        exists" copy that goes with it.

        PDF-COMPREHENSIVE — returns a dict so the template can read
        section_label / truncation_note / more_note alongside the
        listing items themselves. The cap comes from PDF_CONFIG and is
        applied here (was: per-template `[:6]` / `[:4]` slices).
        """
        raw = self.report_data.get("listings") or self.report_data.get("listings_sample") or []
        config = _pdf_config_for(self.report_type)
        cap = config["cap"]
        total = len(raw)
        showing = min(cap, total)

        items = []
        for item in raw[:cap]:
            items.append({
                "address": item.get("street_address") or item.get("address", ""),
                "city": item.get("city", ""),
                # `_first_present`, not `a or b or 0` (D-108). The `or` chain
                # is the same zero-is-falsy defect as `{% if value %}`, one
                # layer earlier and worse: it collapsed a real 0 AND a missing
                # value into the same 0, so the template could not tell a
                # studio from a listing with no bed count. It looked correct
                # only because the template then hid both. Fixing the template
                # without this would have printed "Studio" over missing data.
                "list_price": _first_present(item, "list_price", "price"),
                "close_price": item.get("close_price"),
                "beds": _first_present(item, "bedrooms", "beds"),
                "baths": _first_present(item, "bathrooms", "baths"),
                "sqft": _first_present(item, "sqft", "living_area"),
                "status": item.get("status", "Active"),
                "days_on_market": _first_present(item, "days_on_market", "dom"),
                # safe_url: vendor photo URLs land in src="…" in a template
                # Jinja autoescapes — which does nothing about the scheme, and
                # a PDF is rendered by a real browser. See safe_url's docstring.
                "photo_url": safe_url(
                    item.get("hero_photo_url") or item.get("photo_url") or item.get("image_url")
                ) or None,
                "lat": item.get("lat") or item.get("latitude"),
                "lng": item.get("lng") or item.get("longitude"),
                "next_open_house": item.get("next_open_house"),
            })

        fmt_kwargs = {
            "showing": showing,
            "total": total,
            "remaining": max(total - cap, 0),
            "city": self.report_data.get("city") or "this area",
            "lookback": self.report_data.get("lookback_days", 30),
        }

        try:
            truncation_note = config["truncation_template"].format(**fmt_kwargs) if total > 0 else ""
        except (KeyError, ValueError):
            truncation_note = ""

        more_note = None
        if config.get("more_template") and total > cap:
            try:
                more_note = config["more_template"].format(**fmt_kwargs)
            except (KeyError, ValueError):
                more_note = None

        return {
            "items": items,
            "section_label": config["section_label"],
            "truncation_note": truncation_note,
            "more_note": more_note,
            "total_available": total,
            "showing": showing,
        }

    def _build_stats_context(self) -> Dict[str, Any]:
        metrics = self.report_data.get("metrics") or {}
        counts = self.report_data.get("counts") or {}
        return {
            "median_list_price": metrics.get("median_list_price"),
            "median_close_price": _first_present(metrics, "median_close_price", "median_sold_price"),
            # `_first_present`, not `or` (D-108). An avg DOM of 0 is reachable
            # now that D-105 reads the feed's own value — a same-day sale
            # reports 0 — and `or` would have skipped past it to `median_dom`
            # and then to None, which the page renders as "no data".
            "avg_dom": _first_present(metrics, "avg_dom", "median_dom"),
            "months_of_inventory": metrics.get("months_of_inventory"),
            # The window months-of-supply is measured over is a choice, and a
            # reader cannot check a number whose basis is not stated (§0.6
            # rule 6). Sourced from compute/moi.py so every surface that shows
            # the figure quotes the same window.
            "months_of_inventory_pace": (
                (metrics.get("months_of_inventory_display") or {}).get("pace_label")
            ),
            "price_per_sqft": _first_present(metrics, "price_per_sqft", "avg_price_per_sqft"),
            "list_to_sale_ratio": _first_present(
                metrics, "list_to_sale_ratio", "close_to_list_ratio", "sale_to_list_ratio"
            ),
            # D-178. The same value in percent, normalised once here instead of
            # by a `< 2` guess written twice in `macros.jinja2`. The raw key
            # stays because other consumers read it and changing what it means
            # is a wider change than this.
            "list_to_sale_pct": _ratio_as_percent(_first_present(
                metrics, "list_to_sale_ratio", "close_to_list_ratio", "sale_to_list_ratio"
            )),
            "active_count": counts.get("Active", 0),
            "pending_count": counts.get("Pending", 0),
            "closed_count": counts.get("Closed", 0),
            "new_listings_count": metrics.get("new_listings_count", 0),
        }

    # ── Design's `_v2` page ────────────────────────────────────────────────
    # One band shape for every kind (fixed height, three rows) and one table
    # shape for the three table kinds. Only `closed` is wired; see V2_KINDS.

    def _v2_band(self) -> Dict[str, Any]:
        """Design's page-1 band, for the kinds in `V2_KINDS`.

        Three rows, fixed height: title + logo slot · big number + label + pill
        · three stats. The numbers are read from the SAME contexts the current
        page uses (`_build_stats_context`, `_build_header_context`) rather than
        recomputed — a second derivation of "median close price" would be this
        project's most-filed defect in a new template.
        """
        stats = self._build_stats_context()
        header = self._build_header_context()
        city = header["city"] or "this area"
        lookback = self.report_data.get("lookback_days", 30)

        if self.report_type == "closed":
            label = f"homes sold in {city}"
            ratio = stats["list_to_sale_pct"]
            big = stats["closed_count"]
            cells = [
                ("Median price", _v2_money(stats["median_close_price"])),
                ("Avg. days", _v2_days(stats["avg_dom"])),
                ("Sold over asking", self._v2_over_asking_count()),
            ]
            pill = f"{ratio:.1f}% of asking" if ratio is not None else None
            pill_sub = f"last {lookback} days"
        elif self.report_type in ("new_listings", "new_listings_gallery"):
            # Design: "same header, same pill, same stats" as the grid kind —
            # count / "new listings in {area}", price range / "this week",
            # Median list · Under $1M · Of inventory.
            label = f"new listings in {city}"
            big = stats["new_listings_count"] or len(
                self.report_data.get("listings")
                or self.report_data.get("listings_sample") or [])
            low, high = self._v2_price_range()
            cells = [
                ("Median list", _v2_money(stats["median_list_price"])),
                ("Under $1M", self._v2_under_a_million()),
                ("Of inventory", self._v2_share_of_inventory()),
            ]
            pill = f"{low} – {high}" if low and high else None
            pill_sub = "this week"

        elif self.report_type == "open_houses":
            # Design: count "9" / "homes to see this weekend", pill
            # "Open houses" / "Sat & Sun · {area}", stats From · To ·
            # Neighborhoods.
            #
            # THE PILL SUB IS DERIVED, NOT THE LITERAL "Sat & Sun". Design's
            # example says Sat & Sun because their sample week has both; a feed
            # with one Sunday slot would render a document promising Saturday
            # viewings that do not exist. The days actually present are read
            # off the listings and named.
            label = "homes to see this weekend"
            big = _v2_count(len(self._v2_listing_rows()))
            first, last, hoods = self._v2_open_house_span()
            cells = [
                ("From", first or V2_NO_DATA),
                ("To", last or V2_NO_DATA),
                ("Neighborhoods", _v2_count(hoods) if hoods else V2_NO_DATA),
            ]
            pill = "Open houses"
            pill_sub = self._v2_open_house_days(city)

        elif self.report_type == "featured_listings":
            # Design: count "4" / "featured homes in {area}", pill
            # "Hand-picked" / price range, stats Listings · Avg. price ·
            # Avg. sq ft.
            rows = self._v2_listing_rows()
            label = f"featured homes in {city}"
            big = _v2_count(len(rows))
            low, high = self._v2_price_range()
            cells = [
                ("Listings", _v2_count(len(rows))),
                ("Avg. price", _v2_money(self._v2_average("list_price", "price"))),
                ("Avg. sq ft", _v2_count(self._v2_average("sqft"))),
            ]
            pill = "Hand-picked"
            pill_sub = f"{low} – {high}" if low and high else None

        elif self.report_type == "inventory":
            # Design: count "212" / "homes for sale in {area}", pill
            # "1.9 months" / "of inventory · seller's market", stats
            # Median list · New this week · Avg. days listed.
            label = f"homes for sale in {city}"
            big = _v2_count(stats["active_count"])
            cells = [
                ("Median list", _v2_money(stats["median_list_price"])),
                ("New this week", self._v2_new_this_week()),
                ("Avg. days listed", _v2_days(stats["avg_dom"])),
            ]
            pill, pill_sub = self._v2_inventory_pill()

        elif self.report_type == "price_bands":
            headline = self._v2_fastest_headline()
            big = headline["band_label"]
            label = headline["label"]
            low, high = self._v2_price_range()
            cells = [
                ("Active listings", _v2_count(stats["active_count"])),
                ("Median list", _v2_money(stats["median_list_price"])),
                ("Price range", f"{low} – {high}" if low and high else V2_NO_DATA),
            ]
            pill = headline["pill"]
            pill_sub = headline["pill_sub"]

        else:
            raise NotImplementedError(
                f"{self.report_type} is in V2_KINDS with no band spec. Every "
                f"kind's band values are per-kind in Design's table; adding a "
                f"kind to V2_KINDS without them would render an empty band."
            )

        return {
            "title": header["title"],
            "big": big,
            "big_px": V2_BIG_PX.get(self.report_type, V2_BIG_PX_DEFAULT),
            "label": label,
            "label_px": _v2_label_size(label),
            "pill": pill,
            "pill_sub": pill_sub,
            "cells": [{"label": l, "value": v} for l, v in cells],
        }

    def _v2_over_asking_count(self) -> str:
        """How many closed sales cleared their asking price.

        Counted from the listings themselves, because no metric reports it.
        A sale with no list price is NOT counted as over asking — absent is not
        a default (D-137), and `close > None` would have been a TypeError
        rather than a quiet wrong answer, which is the one mercy here.
        """
        raw = (self.report_data.get("listings")
               or self.report_data.get("listings_sample") or [])
        over = 0
        comparable = 0
        for item in raw:
            close = _first_present(item, "close_price", "sold_price")
            lst = _first_present(item, "list_price", "price")
            if not isinstance(close, (int, float)) or not isinstance(lst, (int, float)):
                continue
            if not lst:
                continue
            comparable += 1
            if close > lst:
                over += 1
        if not comparable:
            return V2_NO_DATA
        return str(over)

    def _v2_fastest_headline(self) -> Dict[str, Any]:
        """Design's bands headline, and the rule that refuses to make it.

        *"{band} is moving fastest" only when that band has >=10 listings and
        is >=3 days faster than the area average, else the plain title
        "{Area} · Price Bands"; every headline hidden under 10 listings.*

        So this returns the plain title far more often than the claim, and that
        is the design: a fastest-band headline on four listings is a sentence
        the data cannot support. The comparison is against the area average
        across the ranked bands, not against the slowest band — "faster than
        the area" is what the sub-label says.

        `hottest_and_slowest` does the ranking, imported rather than rewritten:
        it already excludes bands with no sales rather than scoring them 999,
        which is the zero-is-falsy defect it was written to fix (D-108's
        family). A second ranking here would be the fifth copy problem in a
        new template.
        """
        from worker.compute.price_bands import hottest_and_slowest

        bands = self.report_data.get("price_bands") or []
        header = self._build_header_context()
        area = header["city"] or "this area"
        plain = {
            "band_label": f"{area} · Price Bands",
            "label": None, "pill": None, "pill_sub": None,
        }
        fastest, _slowest = hottest_and_slowest(bands)
        if not fastest.get("count") or fastest.get("avg_dom") is None:
            return plain
        if fastest["count"] < V2_FASTEST_MIN_LISTINGS:
            return plain

        ranked = [b["avg_dom"] for b in bands
                  if b.get("avg_dom") is not None and b.get("count")]
        area_avg = sum(ranked) / len(ranked)
        ahead = area_avg - fastest["avg_dom"]
        if ahead < V2_FASTEST_MIN_DAYS_AHEAD:
            return plain

        return {
            "band_label": fastest["label"],
            "label": "is moving fastest",
            "pill": _v2_days(fastest["avg_dom"]),
            "pill_sub": f"{ahead:.0f} days faster than the area",
        }

    def _v2_bands_body(self) -> Dict[str, Any]:
        """Design's band rows: label + tag, a bar, median, days, $/sq ft.

        THE BAR'S WIDTH IS A SHARE OF THE LARGEST COUNT, not of the total. A
        share of the total makes every bar short as soon as there are several
        bands, and Design's row is a comparison between bands rather than a
        composition of a whole.

        The count sits BESIDE the bar as ink text, not inside it — Design's
        spec, and it is also the only placement that survives a count of zero
        and a bar of zero width.
        """
        from worker.compute.price_bands import hottest_and_slowest

        bands = self.report_data.get("price_bands") or []
        fastest, slowest = hottest_and_slowest(bands)
        counts = [_v2_known_count(b) for b in bands]
        known = [c for c in counts if c is not None]
        widest = max(known) if known else 0
        # A COMPARATIVE TAG NEEDS TWO THINGS TO COMPARE. `hottest_and_slowest`
        # returns the single band as both when there is one, so an unguarded
        # `is_fastest` tagged one row "Fastest" against nothing — the body's
        # version of the refusal `_v2_fastest_headline` already makes for the
        # headline.
        #
        # RANKABLE MATCHES WHAT `hottest_and_slowest` RANKS: a known `avg_dom`
        # and a NON-ZERO count. Zero and absent are both excluded here and for
        # once that is right — an empty band has no speed to compare and an
        # uncounted one has no standing to compare it — which is the one place
        # in this method where `_v2_known_count`'s `None` and a `0` may be
        # treated alike.
        rankable = sum(1 for b in bands if b.get("avg_dom") is not None
                       and _v2_known_count(b))
        comparable = rankable >= 2
        rows = []
        for band, count in zip(bands, counts):
            is_fastest = (comparable
                          and band.get("label") == fastest.get("label")
                          and fastest.get("avg_dom") is not None)
            is_slowest = (comparable
                          and band.get("label") == slowest.get("label")
                          and slowest.get("avg_dom") is not None
                          and not is_fastest)
            rows.append({
                "label": band.get("label") or V2_DASH,
                "tag": "Fastest" if is_fastest else ("Slowest" if is_slowest else None),
                "is_fastest": is_fastest,
                "is_slowest": is_slowest,
                "count": _v2_count(count),
                "bar_pct": round(count / widest * 100) if (
                    widest and count is not None) else 0,
                "median": _v2_money(band.get("median_price")),
                "days": _v2_days(band.get("avg_dom")),
                "ppsf": (f"${int(band['avg_ppsf']):,}"
                         if isinstance(band.get("avg_ppsf"), (int, float))
                         else V2_DASH),
            })
        # THE D-111 DISCLOSURE, WHICH THIS MOVE NEARLY DROPPED.
        # `_band_chart_note` was fed to `band_distribution_chart`, and
        # `pricebands_layout` is the only caller of that macro — so when this
        # kind moved to the `_v2` page, the line saying "these boundaries came
        # from this period's results and may shift between reports" stopped
        # reaching any page while its producer, and the test on its producer,
        # stayed green. That caveat is the reason D-111's rebuild is honest:
        # bands that may move look identical to bands that will not, and the
        # whole point of round boundaries is that a reader can compare two
        # runs. A producer with no consumer is this project's read-with-no-
        # producer defect pointed the other way, and it is why
        # `test_price_bands.py` now renders the page instead of calling the
        # method.
        #
        # The note is REUSED, not rewritten — a second "N listings across M
        # bands" would be a second derivation of the figure the table above it
        # shows. It returns None under two counted bands, where there is no
        # distribution to caption; the caveat still has to land, so it is
        # carried on its own in that case.
        note = self._band_chart_note()
        caveat = self.report_data.get("price_bands_note")
        if not note and caveat:
            note = caveat
        return {"rows": rows, "slow_tag": V2_SLOW_TAG, "note": note}

    def _v2_new_this_week(self) -> str:
        """How many active listings came on within `V2_NEW_WITHIN_DAYS`.

        Counted from the listings rather than read from a metric, because
        `new_listings_count` is a DIFFERENT QUANTITY: it is produced by
        `build_new_listings_result` over that report's own lookback window,
        which is 30 days by default and settable per schedule. Design's cell
        says "New this week" and means seven days. Reading the 30-day figure
        under a label that says week would be a number that is right about
        something else, which is the hardest kind of wrong to see on a page.

        `V2_NO_DATA` when no listing reports a day count at all — not `0`.
        "No listing has a DOM" and "no listing is new" are different facts and
        only the second is a claim about the market (D-137).
        """
        raw = (self.report_data.get("listings")
               or self.report_data.get("listings_sample") or [])
        days = [item.get("days_on_market") for item in raw]
        known = [d for d in days
                 if isinstance(d, (int, float)) and not isinstance(d, bool)]
        if not known:
            return V2_NO_DATA
        return _v2_count(sum(1 for d in known if d <= V2_NEW_WITHIN_DAYS))

    def _v2_inventory_pill(self):
        """Design's `("1.9 months", "of inventory · seller's market")`.

        BOTH HALVES COME FROM `compute.moi` AND NEITHER IS COMPUTED HERE.
        `describe()` already owns the formatting ("one place decides how 'no
        number' looks, so the surfaces cannot disagree") and `condition()` now
        owns the classification, which was the one piece of MOI interpretation
        that module did not own — and which had therefore been reimplemented
        six times at two different thresholds (D-182). A seventh copy on a new
        page is how that defect would have reached a fourth surface.

        **NO NUMBER MEANS NO PILL.** `months_of_supply` returns `None` whenever
        MOI cannot honestly be estimated — fewer than three closings in the
        rate window, or an active count that hit a paging limit and is a floor
        rather than a count (D-056). The pill is dropped entirely in that case
        rather than filled with a dash: the band's pill is a claim about the
        market, and "— months of inventory · " is a claim with the evidence
        removed from the middle of it.
        """
        from worker.compute.moi import condition as moi_condition, describe

        metrics = self.report_data.get("metrics") or {}
        moi = metrics.get("months_of_inventory")
        if not isinstance(moi, (int, float)) or isinstance(moi, bool):
            return None, None
        label = moi_condition(moi)
        if label is None:
            return None, None
        return describe(moi)["formatted_current"], (
            f"of inventory · {label.lower()}")

    def _v2_listing_rows(self):
        """The raw listings a `_v2` body will render, capped as the page caps.

        One accessor, because four gallery/band branches were each reaching for
        `listings or listings_sample` and a fifth would have got it subtly
        different. The cap is `_build_listings_context`'s, so a band counting
        "9 homes to see" agrees with the nine cards below it rather than with
        the hundred the feed returned — a band that disagrees with its own body
        is worse than either number alone.
        """
        return self._build_listings_context()["items"]

    def _v2_average(self, *keys):
        """The mean of the first present numeric value across `keys`, or None.

        `None` and not `0` for an empty set: "no listing reports a sq ft" is
        not "the average sq ft is zero" (D-137), and `_v2_money`/`_v2_count`
        turn the None into a dash.
        """
        vals = []
        for item in self._v2_listing_rows():
            value = _first_present(item, *keys)
            if isinstance(value, (int, float)) and not isinstance(value, bool):
                vals.append(value)
        if not vals:
            return None
        return sum(vals) / len(vals)

    def _v2_open_house_span(self):
        """`("Sat 11 Oct", "Sun 12 Oct", 3)` — the first slot, last, and hoods.

        Design's three `open_houses` stats are From · To · Neighborhoods, and
        none of them is a metric: the open-house builder returns no `metrics`
        at all, so all three come from the listings. The dates are already
        sorted ascending by `build_open_houses_result`, but this does not rely
        on that — a body that trusts an upstream sort is a body that breaks
        when someone adds a filter.
        """
        dates = self._open_house_dates()
        hoods = {
            (item.get("city") or "").strip()
            for item in self._v2_listing_rows()
            if (item.get("city") or "").strip()
        }
        if not dates:
            return None, None, len(hoods)
        return (_v2_open_house_label(min(dates)),
                _v2_open_house_label(max(dates)),
                len(hoods))

    def _open_house_dates(self):
        """Every parseable `next_open_house` as a `date`, deduplicated."""
        out = set()
        for item in self._v2_listing_rows():
            raw = item.get("next_open_house")
            if not isinstance(raw, str) or not raw.strip():
                continue
            try:
                out.add(datetime.strptime(raw.strip()[:10], "%Y-%m-%d").date())
            except ValueError:
                # Feeds also send "Sat 1-4pm" and other free text here. An
                # unparseable slot is dropped from the SPAN and still renders
                # on its card, which is the right split: the card shows what
                # the feed said, the band only claims what it could read.
                continue
        return out

    def _v2_open_house_days(self, city: str) -> str:
        """`"Sat & Sun · Irvine"`, or whichever days are actually present.

        NOT THE LITERAL "Sat & Sun". Design's example reads that way because
        their sample week has both, and a report whose only slot is Sunday
        would otherwise promise Saturday viewings that do not exist — a claim
        the data contradicts, on a document an agent hands to a client.
        """
        dates = self._open_house_dates()
        if not dates:
            return city
        names = sorted({d.strftime("%a") for d in dates},
                       key=lambda n: min(d.weekday() for d in dates
                                         if d.strftime("%a") == n))
        if len(names) == 1:
            days = names[0]
        elif len(names) == 2:
            days = f"{names[0]} & {names[1]}"
        else:
            days = f"{names[0]}\u2013{names[-1]}"
        return f"{days} \u00b7 {city}"

    def _v2_price_range(self):
        """`($641K, $1.2M)` from the listings' own prices, or `(None, None)`.

        From the listings rather than from `metrics`, because no metric reports
        a range and inventing one from median +/- something would be a number
        with no source. A single listing gives a degenerate range, which is
        correct: one listing has one price.
        """
        raw = (self.report_data.get("listings")
               or self.report_data.get("listings_sample") or [])
        prices = [_first_present(i, "list_price", "price") for i in raw]
        prices = [p for p in prices
                  if isinstance(p, (int, float)) and not isinstance(p, bool) and p]
        if not prices:
            return None, None
        return _v2_money(min(prices)), _v2_money(max(prices))

    def _v2_under_a_million(self) -> str:
        """How many of the new listings are under $1M.

        A count, not a percentage: Design's cell is "Under $1M" beside a
        median, and a share would need a denominator the band does not show.
        """
        raw = (self.report_data.get("listings")
               or self.report_data.get("listings_sample") or [])
        prices = [_first_present(i, "list_price", "price") for i in raw]
        prices = [p for p in prices
                  if isinstance(p, (int, float)) and not isinstance(p, bool) and p]
        if not prices:
            return V2_NO_DATA
        return _v2_count(sum(1 for p in prices if p < 1_000_000))

    def _v2_share_of_inventory(self) -> str:
        """New listings as a share of active inventory.

        `V2_NO_DATA` when there is no active count, NOT 0% — a market with no
        recorded inventory has no share, and "0% of inventory" is a claim
        (D-137: absent is not a default).
        """
        active = (self.report_data.get("counts") or {}).get("Active")
        new = self._build_stats_context()["new_listings_count"]
        if not isinstance(active, (int, float)) or not active:
            return V2_NO_DATA
        if not isinstance(new, (int, float)):
            return V2_NO_DATA
        return f"{new / active * 100:.0f}%"

    def _v2_gallery(self) -> Dict[str, Any]:
        """Design's photo grid: the cards, the grid shape, and which card.

        TWO CARDS, NOT ONE GRID OF ONE CARD. `featured_listings` gets its own
        (price plate 18px, address 15px/600, beds/baths/sq ft as three stacked
        mini-stats to the right) because four cards on a page can afford the
        size and nine cannot. `new_listings_gallery` and `open_houses` share
        the listings card — Design's own words, "same card as listings".

        THE PHOTO RESERVES ITS BOX WITHOUT LOADING, and that is load-bearing
        for the page-fit measurement rather than a detail. It is an
        `aspect-ratio` on a `background-image` div, so the height is reserved
        from the column width whether or not a remote photo resolves — and
        remote photos never resolve in a headless render. The legacy card used
        a fixed `height: 180px` for the same reason; an `<img>` with no
        reserved box would make `measure_gallery_continuation_fit.py` measure a
        page that collapses to nothing.
        """
        rows = []
        for item in self._v2_listing_rows():
            price = _first_present(item, "list_price", "price")
            hood = (item.get("city") or "").strip()
            rows.append({
                "photo_url": item.get("photo_url") or None,
                "price": _v2_money(price),
                "address": item.get("address") or V2_NO_DATA,
                # `{hood} · {specs}` as ONE line, Design's spec. Joined here
                # rather than in the template so an absent hood does not render
                # a leading separator — the shape `· 3 bd / 2 ba` is the
                # thing a dot-joined template produces on missing data.
                "meta": " \u00b7 ".join(
                    part for part in (hood, _v2_card_specs(item)) if part),
                "hood": hood,
                "beds": _v2_count(item.get("beds")),
                "baths": _v2_count(item.get("baths")),
                "sqft": _v2_count(item.get("sqft")),
                # Free text as well as a date — feeds send both, and the card
                # shows whatever the feed said even when the band could not
                # parse it for the From/To span.
                "open_house": (item.get("next_open_house") or "").strip() or None,
                # THE CARD'S THIRD LINE, AND IT IS HOW "LISTED TODAY" SURVIVES
                # THE MOVE. Design's gallery card is price plate · address ·
                # "{hood} · {specs}" and names no date — but the legacy card
                # carried a "New" badge on a same-day listing, and
                # `test_zero_days_on_market_renders_as_new` is a gate written
                # because 0 days is the value an `or` chain eats (D-105,
                # D-108). Dropping it would lose the most interesting fact on
                # a new-listings report, silently, to a spec that did not ask
                # for it to go.
                #
                # It uses the SAME SLOT `open_houses` puts its viewing time in,
                # so this is Design's own card structure carrying a per-kind
                # line rather than a line invented beside it. Flagged for them:
                # one `{% if %}` removes it if they want the card bare.
                "listed": (_v2_listed_label(item.get("days_on_market"))
                           if self.report_type == "new_listings_gallery"
                           else None),
            })
        spec = V2_GRID[self.report_type]
        return {
            "rows": rows,
            # The search's own terms, for the empty state. Standing
            # instruction: an empty search renders and says it returned
            # nothing — and `_v2`'s grid is a `<section>` that collapses to a
            # bare empty element otherwise, which is the same defect the bands
            # body had (five column headings over nothing).
            # THE SEARCH'S OWN TERMS, not the report title. "No listings
            # matched this search" alone cannot tell an empty market from an
            # over-tight filter, which is the whole point of the gate on this:
            # the reader needs to know whether to widen the filter or believe
            # the market. `filters_label` is what the user chose.
            "empty_label": (self.report_data.get("filters_label") or "").strip(),
            "empty_city": self._build_header_context()["city"] or "",
            "cols": spec["cols"],
            "rows_page_1": spec["rows_page_1"],
            "card": (V2_FEATURED_CARD
                     if self.report_type == "featured_listings"
                     else V2_LISTING_CARD),
            "showing": len(rows),
            "total": self._build_listings_context()["total_available"],
        }

    def _v2_table(self) -> Dict[str, Any]:
        """Design's table for the three table kinds; `closed`'s columns here.

        `vs. list` carries a COLOUR RULE, not just a number: over asking takes
        `accent_ink` at 600, otherwise the muted neutral at 400. Design states
        it per kind ("`>100%` in `accent_ink` 600, else `#5E636B` 400"), and it
        is resolved here rather than in the template because the template
        cannot ask whether a ratio is above a threshold without reimplementing
        the threshold.
        """
        listings_ctx = self._build_listings_context()
        rows = []
        for item in listings_ctx["items"]:
            close = item.get("close_price")
            lst = item.get("list_price")
            ratio = None
            if isinstance(close, (int, float)) and isinstance(lst, (int, float)) and lst:
                ratio = close / lst * 100
            # PER KIND, AND AN UNKNOWN KIND RAISES.
            #
            # This was `if new_listings: ... else: ...`, and the `else` was
            # `closed`'s close-to-list ratio. That is right for two kinds and
            # silently wrong for every kind added afterwards: `inventory`'s
            # listings are Active, so they have no close price, so the ratio
            # comes out `None`, so the column would have rendered a full page
            # of dashes under a header reading "Status" — a page that looks
            # finished and says nothing. The same shape as the four gates that
            # encoded a table kind's property as the seam's property, in the
            # builder instead of in a test.
            if self.report_type == "new_listings":
                # Design's `Listed` column, and the LIST price — a new listing
                # has no sale price, so `close if close else lst` would be the
                # right value by accident rather than by intent.
                fifth = _v2_listed_label(item.get("days_on_market"))
                emphasis = fifth == "Today"
                price = _v2_money(lst)
            elif self.report_type == "inventory":
                # Design: `Status` — "New" when DOM <= 7, else a dash. The LIST
                # price for the same reason as `new_listings`: a home for sale
                # has not sold.
                dom = item.get("days_on_market")
                fresh = (isinstance(dom, (int, float))
                         and not isinstance(dom, bool)
                         and dom <= V2_NEW_WITHIN_DAYS)
                fifth = "New" if fresh else V2_DASH
                emphasis = fresh
                price = _v2_money(lst)
            elif self.report_type == "closed":
                fifth = f"{ratio:.1f}%" if ratio is not None else V2_DASH
                emphasis = bool(ratio is not None and ratio > 100)
                price = _v2_money(close if close else lst)
            else:
                raise NotImplementedError(
                    f"{self.report_type} has `_v2` table columns but no fifth-"
                    f"column rule. Design states that column per kind — a "
                    f"ratio on `closed`, a date on `new_listings`, a status on "
                    f"`inventory` — and there is no default that is right for "
                    f"a kind nobody has read the spec for."
                )
            rows.append({
                "address": item.get("address") or V2_NO_DATA,
                "hood": item.get("city") or "",
                "beds_baths": _v2_beds_baths(item),
                "sqft": _v2_count(item.get("sqft")),
                "price": price,
                # ONE SHAPE WHICHEVER KIND RENDERED. The fifth column means
                # "vs. list" on `closed` and "Listed" on `new_listings`;
                # `emphasis` is whichever of those the kind accents — over
                # asking, or listed today. The page reads two keys, not six.
                "fifth": fifth,
                "emphasis": emphasis,
                "days": _v2_days(item.get("days_on_market")),
            })
        return {
            "rows": rows,
            "showing": listings_ctx["showing"],
            "total": listings_ctx["total_available"],
            "columns": V2_TABLE_COLUMNS[self.report_type],
            # The count line's noun, per kind. "20 sales" on a new-listings
            # report would be wrong in a way nothing would catch — the number
            # is right and the word is not.
            "noun": V2_TABLE_COLUMNS[self.report_type]["noun"],
            "noun_one": V2_TABLE_COLUMNS[self.report_type]["noun_one"],
        }

    def _build_agent_context(self) -> Dict[str, Any]:
        branding = self.report_data.get("branding") or {}
        return {
            "name": branding.get("agent_name", ""),
            # Same construct as property_builder's agent title, hardened the
            # same way (D-067, §0.6: grep for the construct, not the symptom).
            # `.get(k, "")` returns None when the column exists holding NULL;
            # the market templates guard with `{% if agent.title %}` so that
            # never leaked the string "None", but a whitespace-only value is
            # truthy and rendered a blank styled line in the page footer.
            "title": (branding.get("agent_title") or "").strip(),
            "phone": branding.get("agent_phone", ""),
            "email": branding.get("agent_email", ""),
            "photo_url": safe_url(branding.get("agent_photo_url")) or None,
            "company_name": branding.get("company_name", ""),
            "logo_url": safe_url(branding.get("logo_url")) or None,
            # Fall back to header logo if no dedicated dark-on-light footer logo.
            "footer_logo_url": safe_url(
                branding.get("footer_logo_url") or branding.get("logo_url")
            ) or None,
        }

    # ── render ────────────────────────────────────────────────────────────

    def _build_narrative_data(self) -> Dict[str, Any]:
        """Build a flat dict of data points for the AI narrative prompt."""
        metrics = self.report_data.get("metrics") or {}
        counts = self.report_data.get("counts") or {}
        listings = self.report_data.get("listings") or self.report_data.get("listings_sample") or []
        prices = [l.get("list_price") or 0 for l in listings if l.get("list_price")]
        return {
            "lookback_days": self.report_data.get("lookback_days", 30),
            "listing_count": self.report_data.get("total_listings") or sum(counts.values()) or len(listings),
            "median_list_price": metrics.get("median_list_price"),
            "median_price": _first_present(metrics, "median_close_price", "median_list_price"),
            "avg_dom": _first_present(metrics, "avg_dom", "median_dom"),
            "months_of_inventory": metrics.get("months_of_inventory"),
            "list_to_sale_ratio": _pct(_first_present(metrics, "list_to_sale_ratio", "sale_to_list_ratio")),
            "close_to_list_ratio": _pct(_first_present(metrics, "close_to_list_ratio", "sale_to_list_ratio")),
            "closed_count": counts.get("Closed", 0),
            "active_count": counts.get("Active", 0),
            "min_price": min(prices) if prices else None,
            "max_price": max(prices) if prices else None,
            "price_bands": self.report_data.get("price_bands") or [],
        }

    def render_html(self) -> str:
        """Render the complete HTML report."""
        primary_color, accent_color = self._resolve_colors()
        # BOTH ends of the header band, not just the first. A label derived against
        # one stop alone measured 9.90:1 where it starts and 2.53:1 where the
        # other takes over (D-097).
        #
        # Derived against the GUARANTEED stops, not the raw brand colours. On
        # the raw pair this returned 3.74:1 for two of the six audited brands
        # and logged that it could not do better on every single render;
        # against the band it clears 4.5:1 for all six (D-112).
        band_start, band_end = self._masthead_band(primary_color, accent_color)
        color_roles = compute_color_roles(accent_color, (band_start, band_end))

        # Resolve AI narrative: use pre-supplied value, otherwise generate.
        #
        # EXCEPT ON THE `_v2` TABLE KINDS, where Design removes it: "this design
        # renders no AI narrative on table or gallery kinds, so there is no
        # narrative variant. Page-1 capacity is one state per kind."
        #
        # AND THIS SUPPRESSION IS NOT WHAT MAKES CAPACITY DETERMINISTIC — the
        # `_v2` page has no narrative block, so the prose could not affect
        # pagination even if it were generated. The first version of this
        # comment claimed otherwise, and a mutation that removed the
        # suppression came back DID NOT FIRE, which is how the claim got
        # checked: nothing about the rendered document changes.
        #
        # What it does do is avoid PAYING for prose nobody will read: an OpenAI
        # round trip, on every render of every v2 kind, whose output is
        # discarded by the template. That is the whole of it, and it is worth
        # doing — it is just a cost, not a correctness property.
        ai_insights = self.report_data.get("ai_insights") or ""
        if self.report_type in V2_KINDS:
            ai_insights = ""
        elif not ai_insights:
            try:
                city = self.report_data.get("city", "")
                narrative_data = self._build_narrative_data()
                ai_insights = generate_market_pdf_narrative(
                    self.report_type, city, narrative_data,
                ) or ""
            except Exception as e:
                logger.warning("AI narrative generation failed (non-fatal): %s", e)
                ai_insights = ""

        listings_ctx = self._build_listings_context()
        monthly_trend, monthly_trend_note, monthly_trend_fmt = self._build_monthly_trend()

        context: Dict[str, Any] = {
            "layout": self.layout,
            "report_type": self.report_type,
            # Brand colours
            "primary_color": primary_color,
            "accent_color": accent_color,
            # The masthead band's two stops, dark enough to carry their own
            # text. NOT the raw brand colours — see `_masthead_band`.
            "band_start": band_start,
            "band_end": band_end,
            "accent_on_dark": color_roles["theme_color_on_dark"],
            "accent_on_light": color_roles["theme_color_on_light"],
            "accent_light": color_roles["theme_color_light"],
            # On the accent TINT, not on white. `.stat-block-accent` and the
            # footer's initials circle paint accent-coloured text on a 35%
            # tint of that same accent — two shades of one colour — and
            # `theme_color_on_light` is computed against #ffffff, which is a
            # different and easier background. Measured at 1.62:1 (D-112).
            "accent_on_tint": ink_on(accent_color, color_roles["theme_color_light"]),
            # The muted label in the same block. `--gray-500` is chosen for a
            # white card and sat at 1.54:1 on the tint.
            "muted_on_tint": ink_on("#78716c", color_roles["theme_color_light"]),
            # Text color guaranteed readable when overlaid on the accent
            # (used by .listing-status pill via --accent-text).
            "theme_color_text": color_roles["theme_color_text"],
            # §7.3 — the chart's mark colour. primary_ink is the one brand value
            # themes.py guarantees as ink on white, which is this page's surface.
            "primary_ink": derive_theme(primary_color)["primary_ink"],
            # §7.3 — the band chart's sample note. The stat cards show only
            # price_bands[:4]; the chart shows every band, so when there are
            # more than four the note is the only place that says so.
            "band_chart_note": self._band_chart_note(),
            "monthly_trend": monthly_trend,
            "monthly_trend_note": monthly_trend_note,
            "monthly_trend_fmt": monthly_trend_fmt or "currency",
            # Section contexts
            "header": self._build_header_context(),
            # PDF-COMPREHENSIVE — listings is still a flat array so the
            # existing macro iteration keeps working; the section
            # label / truncation note / more-listings callout / counts
            # are exposed alongside it as separate context keys.
            "listings": listings_ctx["items"],
            "listings_section_label": listings_ctx["section_label"],
            "listings_truncation_note": listings_ctx["truncation_note"],
            "listings_more_note": listings_ctx["more_note"],
            "listings_total_available": listings_ctx["total_available"],
            "listings_showing": listings_ctx["showing"],
            "stats": self._build_stats_context(),
            "agent": self._build_agent_context(),
            # AI narrative (optional — exposed under both names for template compat)
            "ai_insights": ai_insights,
            "ai_narrative": ai_insights,
            # Price bands data (analytics layout)
            "price_bands": self.report_data.get("price_bands") or [],
        }

        if self.report_type in V2_KINDS:
            # Design's page takes the brand colour DIRECTLY as the band fill,
            # not the darkened two-stop band. That is safe here and was not
            # before: `on_primary` and `display_ink` are derived from whatever
            # fill they sit on, so the text adapts instead of the fill being
            # bent to fit text hardcoded to white (D-112's defect). It also
            # means the `_v2` band is solid — no gradient — which settles that
            # question for this kind without asking it.
            tokens = derive_theme(primary_color)
            context.update({
                "v2": True,
                "v2_band": self._v2_band(),
                # ONE BODY PER KIND, chosen here rather than by the template
                # asking what kind it is. `price_bands` is not a table and the
                # page must not pretend it is.
                "v2_table": (self._v2_table()
                             if self.report_type in V2_TABLE_COLUMNS else None),
                "v2_bands": (self._v2_bands_body()
                             if self.report_type == "price_bands" else None),
                "v2_gallery": (self._v2_gallery()
                               if self.report_type in V2_GRID else None),
                "on_primary": tokens["on_primary"],
                "display_ink": tokens["display_ink"],
                # The pill's text sits on WHITE, not on the brand fill, at
                # 13px/600 — which is not large text, so it needs 4.5 and the
                # raw brand colour does not have it (3.74 on teal, 2.15 on
                # amber, 1.98 on lime). `primary_ink` is the brand darkened
                # until it clears AA on white and on the tint (D-170, D-177).
                "primary_ink": tokens["primary_ink"],
                "tint": tokens["tint"],
                "v2_muted": V2_MUTED,
                # The rule colour follows which way `on_primary` resolved, per
                # Design's band-rules row. One expression, not two literals.
                "on_primary_rule": (
                    "rgba(255,255,255,0.3)"
                    if tokens["on_primary"].lower() == "#ffffff"
                    else "rgba(20,21,26,0.25)"
                ),
            })

        logger.info(
            "Rendering market report: type=%s, layout=%s, primary=%s, accent=%s",
            self.report_type,
            self.layout,
            primary_color,
            accent_color,
        )

        try:
            template = self.env.get_template(
            V2_TEMPLATE_PATH if self.report_type in V2_KINDS else TEMPLATE_PATH)
            # Every URL-shaped value is scheme-checked here, at the one place
            # a context can become HTML. See sanitize_context_urls.
            html = template.render(**sanitize_context_urls(context))
            logger.info("Rendered market report: html_len=%d", len(html))
            return html
        except Exception as e:
            logger.error(
                "Failed to render market report (type=%s): %s",
                self.report_type,
                e,
            )
            raise

    # ── PDFShift-native header/footer rendering ───────────────────────────
    # PDFSHIFT-NATIVE-HEADER-FOOTER — These two methods produce standalone
    # HTML documents that PDFShift's `header` / `footer` parameters consume.
    # PDFShift renders them in a separate document context (no shared CSS
    # custom properties with the main body), so the templates inline all
    # brand colors as literal hex values from the build context.

    def render_page_header_html(self) -> str:
        """Render the big gradient hero header as a standalone HTML doc,
        repeated on every page via PDFShift's `header` parameter."""
        primary_color, accent_color = self._resolve_colors()
        # The same guaranteed band as the body (D-112), so the running head
        # and footer cannot derive their text against a different surface
        # from the one they are painted on.
        color_roles = compute_color_roles(accent_color, self._masthead_band(primary_color, accent_color))
        header_ctx = self._build_header_context()
        subtitle_text = header_ctx.get("subtitle") or "All Properties"
        context = {
            "primary_color": primary_color,
            "accent_color": accent_color,
            "accent_on_dark": color_roles["theme_color_on_dark"],
            # Gradient dark stop, brand-derived rather than the hardcoded
            # "#18235c" navy of HERO-EVERY-PAGE.
            #
            # `_masthead_band`, not `_darken(primary_color, 0.35)`. A fixed
            # factor is a guess that happens to work for the colours someone
            # tried: measured across the audit's six brands, 0.35 leaves white
            # at 4.47:1 on lime — under the bar, by a hair, silently. The
            # derivation darkens until it is actually readable and stops
            # there, so a brand already dark enough is not dulled (D-112).
            "header_bg": self._masthead_band(primary_color, accent_color)[0],
            "report_title": header_ctx.get("title") or "Market Report",
            # The running head carries the BRAND; the page-1 masthead carries
            # the report title. They used to carry the same words 40px apart.
            "brand_name": (
                (self.report_data.get("branding") or {}).get("company_name")
                or (self.report_data.get("branding") or {}).get("agent_name")
                or ""
            ),
            "city": header_ctx.get("city") or "",
            "lookback_days": header_ctx.get("lookback_days") or 30,
            "subtitle_text": subtitle_text,
            "total_count": header_ctx.get("total_count"),
            "agent": self._build_agent_context(),
        }
        template = self.env.get_template("_base/page_header.jinja2")
        return template.render(**sanitize_context_urls(context))

    def render_page_footer_html(self) -> str:
        """Render the agent footer as a standalone HTML doc, repeated on every page."""
        primary_color, accent_color = self._resolve_colors()
        # The same guaranteed band as the body (D-112), so the running head
        # and footer cannot derive their text against a different surface
        # from the one they are painted on.
        color_roles = compute_color_roles(accent_color, self._masthead_band(primary_color, accent_color))

        context = {
            "primary_color": primary_color,
            "accent_color": accent_color,
            "accent_light": color_roles["theme_color_light"],
            # On the accent TINT, not on white. `.stat-block-accent` and the
            # footer's initials circle paint accent-coloured text on a 35%
            # tint of that same accent — two shades of one colour — and
            # `theme_color_on_light` is computed against #ffffff, which is a
            # different and easier background. Measured at 1.62:1 (D-112).
            "accent_on_tint": ink_on(accent_color, color_roles["theme_color_light"]),
            # The muted label in the same block. `--gray-500` is chosen for a
            # white card and sat at 1.54:1 on the tint.
            "muted_on_tint": ink_on("#78716c", color_roles["theme_color_light"]),
            "accent_on_light": color_roles["theme_color_on_light"],
            "agent": self._build_agent_context(),
        }
        template = self.env.get_template("_base/page_footer.jinja2")
        return template.render(**sanitize_context_urls(context))


#: Which report types draw a twelve-month trend, and therefore which ones the
#: fetch in tasks.py pays for (D-113).
#:
#: DERIVED from `TREND_SERIES`, not a second literal. The caller deciding
#: whether to buy the data and the builder deciding whether to draw it have to
#: read the same list, and two copies fail the quiet way in both directions:
#: a fetch whose answer is never used, or a chart whose data was never bought.
#: The first draft of this line WAS a second literal.
TREND_REPORT_TYPES = frozenset(MarketReportBuilder.TREND_SERIES)


#: Which report types need the twelve months FETCHED. A superset of
#: `TREND_REPORT_TYPES`, because `price_bands` wants the same rows for a
#: different reason: not to draw a line, but to size its band boundaries from
#: a year of closings rather than from this week's results (D-111).
#:
#: Deliberately a separate name. Folding price_bands into TREND_REPORT_TYPES
#: would make it fetch a trend it does not draw, and the next person to read
#: `TREND_SERIES` would find a type missing from it.
HISTORY_REPORT_TYPES = TREND_REPORT_TYPES | frozenset({"price_bands"})

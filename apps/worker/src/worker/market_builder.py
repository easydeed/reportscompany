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
V2_KINDS = frozenset({"closed"})

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
    TREND_SERIES = {
        "market_snapshot": "median",
        "inventory": "count",
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
        else:  # pragma: no cover - V2_KINDS holds one kind
            raise NotImplementedError(
                f"{self.report_type} is in V2_KINDS with no band spec. Every "
                f"kind's band values are per-kind in Design's table; adding a "
                f"kind to V2_KINDS without them would render an empty band."
            )

        return {
            "title": header["title"],
            "big": big,
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
            rows.append({
                "address": item.get("address") or V2_NO_DATA,
                "hood": item.get("city") or "",
                "beds_baths": _v2_beds_baths(item),
                "sqft": _v2_count(item.get("sqft")),
                "price": _v2_money(close if close else lst),
                "vs_list": f"{ratio:.1f}%" if ratio is not None else V2_DASH,
                "vs_over": bool(ratio is not None and ratio > 100),
                "days": _v2_days(item.get("days_on_market")),
            })
        return {
            "rows": rows,
            "showing": listings_ctx["showing"],
            "total": listings_ctx["total_available"],
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
                "v2_table": self._v2_table(),
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

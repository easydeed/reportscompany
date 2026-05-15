"""
Market Report Builder
=====================

Renders brand-driven market reports (8 types) using a single Jinja2 template.
Colors come from the agent's branding (primary_color, accent_color).

Report types → layout mapping:
  Gallery:         new_listings_gallery, featured_listings, open_houses
  Market Narrative: market_snapshot
  Closed/Inventory: closed, inventory
  Analytics:        price_bands, new_listings

Usage:
    builder = MarketReportBuilder(report_data)
    html = builder.render_html()
"""

import logging
from typing import Any, Dict
from pathlib import Path
from jinja2 import Environment, FileSystemLoader, select_autoescape

from worker.property_builder import compute_color_roles
from worker.template_filters import (
    format_currency,
    format_currency_short,
    format_number,
    truncate,
)
from worker.ai_market_narrative import generate_market_pdf_narrative

logger = logging.getLogger(__name__)


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
DEFAULT_ACCENT = "#0d9488"

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
#   SNAPSHOT (1-page, curated sample):
#     market_snapshot, price_bands, featured_listings
#   CATALOG (multi-page, ALL matching listings):
#     closed, inventory, new_listings, new_listings_gallery, open_houses
#
# CATALOG types have `more_template = None` and a high cap (100-200) so the
# PDF renders every matching listing. The previous "+ N more — contact me for
# the complete list" callout was dishonest (agents had no way to produce
# that list) and is now removed across the board.
PDF_CONFIG: Dict[str, Dict[str, Any]] = {
    # ── SNAPSHOT mode ───────────────────────────────────────────────────────
    "market_snapshot": {
        "cap": 8,
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
        return {
            "title": report_titles.get(self.report_type, "Market Report"),
            "subtitle": data.get("filters_label", ""),
            "city": data.get("city", ""),
            "lookback_days": data.get("lookback_days", 30),
            "total_count": total,
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
                "list_price": item.get("list_price") or item.get("price", 0),
                "close_price": item.get("close_price"),
                "beds": item.get("bedrooms") or item.get("beds", 0),
                "baths": item.get("bathrooms") or item.get("baths", 0),
                "sqft": item.get("sqft") or item.get("living_area", 0),
                "status": item.get("status", "Active"),
                "days_on_market": item.get("days_on_market") or item.get("dom", 0),
                "photo_url": item.get("hero_photo_url") or item.get("photo_url") or item.get("image_url"),
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
            "median_close_price": metrics.get("median_close_price") or metrics.get("median_sold_price"),
            "avg_dom": metrics.get("avg_dom") or metrics.get("median_dom"),
            "months_of_inventory": metrics.get("months_of_inventory"),
            "price_per_sqft": metrics.get("price_per_sqft") or metrics.get("avg_price_per_sqft"),
            "list_to_sale_ratio": metrics.get("list_to_sale_ratio") or metrics.get("close_to_list_ratio") or metrics.get("sale_to_list_ratio"),
            "active_count": counts.get("Active", 0),
            "pending_count": counts.get("Pending", 0),
            "closed_count": counts.get("Closed", 0),
            "new_listings_count": metrics.get("new_listings_count", 0),
        }

    def _build_agent_context(self) -> Dict[str, Any]:
        branding = self.report_data.get("branding") or {}
        return {
            "name": branding.get("agent_name", ""),
            "title": branding.get("agent_title", ""),
            "phone": branding.get("agent_phone", ""),
            "email": branding.get("agent_email", ""),
            "photo_url": branding.get("agent_photo_url"),
            "company_name": branding.get("company_name", ""),
            "logo_url": branding.get("logo_url"),
            # Fall back to header logo if no dedicated dark-on-light footer logo.
            "footer_logo_url": branding.get("footer_logo_url") or branding.get("logo_url"),
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
            "median_price": metrics.get("median_close_price") or metrics.get("median_list_price"),
            "avg_dom": metrics.get("avg_dom") or metrics.get("median_dom"),
            "months_of_inventory": metrics.get("months_of_inventory"),
            "list_to_sale_ratio": _pct(metrics.get("list_to_sale_ratio") or metrics.get("sale_to_list_ratio")),
            "close_to_list_ratio": _pct(metrics.get("close_to_list_ratio") or metrics.get("sale_to_list_ratio")),
            "closed_count": counts.get("Closed", 0),
            "active_count": counts.get("Active", 0),
            "min_price": min(prices) if prices else None,
            "max_price": max(prices) if prices else None,
            "price_bands": self.report_data.get("price_bands") or [],
        }

    def render_html(self) -> str:
        """Render the complete HTML report."""
        primary_color, accent_color = self._resolve_colors()
        color_roles = compute_color_roles(accent_color, primary_color)

        # Resolve AI narrative: use pre-supplied value, otherwise generate
        ai_insights = self.report_data.get("ai_insights") or ""
        if not ai_insights:
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

        context: Dict[str, Any] = {
            "layout": self.layout,
            "report_type": self.report_type,
            # Brand colours
            "primary_color": primary_color,
            "accent_color": accent_color,
            "accent_on_dark": color_roles["theme_color_on_dark"],
            "accent_on_light": color_roles["theme_color_on_light"],
            "accent_light": color_roles["theme_color_light"],
            # Text color guaranteed readable when overlaid on the accent
            # (used by .listing-status pill via --accent-text).
            "theme_color_text": color_roles["theme_color_text"],
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

        logger.info(
            "Rendering market report: type=%s, layout=%s, primary=%s, accent=%s",
            self.report_type,
            self.layout,
            primary_color,
            accent_color,
        )

        try:
            template = self.env.get_template(TEMPLATE_PATH)
            html = template.render(**context)
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
        color_roles = compute_color_roles(accent_color, primary_color)
        header_ctx = self._build_header_context()
        subtitle_text = header_ctx.get("subtitle") or "All Properties"
        context = {
            "primary_color": primary_color,
            "accent_color": accent_color,
            "accent_on_dark": color_roles["theme_color_on_dark"],
            "header_bg": "#18235c",  # Navy gradient stop. Hardcoded default;
                                     # can be made dynamic per brand later if needed.
            "report_title": header_ctx.get("title") or "Market Report",
            "city": header_ctx.get("city") or "",
            "lookback_days": header_ctx.get("lookback_days") or 30,
            "subtitle_text": subtitle_text,
            "total_count": header_ctx.get("total_count"),
            "agent": self._build_agent_context(),
        }
        template = self.env.get_template("_base/page_header.jinja2")
        return template.render(**context)

    def render_page_footer_html(self) -> str:
        """Render the agent footer as a standalone HTML doc, repeated on every page."""
        primary_color, accent_color = self._resolve_colors()
        color_roles = compute_color_roles(accent_color, primary_color)

        context = {
            "primary_color": primary_color,
            "accent_color": accent_color,
            "accent_light": color_roles["theme_color_light"],
            "accent_on_light": color_roles["theme_color_on_light"],
            "agent": self._build_agent_context(),
        }
        template = self.env.get_template("_base/page_footer.jinja2")
        return template.render(**context)

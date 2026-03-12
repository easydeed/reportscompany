"""
Market Report Builder
=====================

Renders themed market reports (8 types × 5 themes) using Jinja2 templates.
Mirrors PropertyReportBuilder patterns — same class shape, same color system.

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

logger = logging.getLogger(__name__)

# ─────────────────────────────────────────────────────────────────────────────
# Constants (duplicated from PropertyReportBuilder — static 5-line dicts,
# coupling to class internals is worse than the duplication)
# ─────────────────────────────────────────────────────────────────────────────

_THEME_DARK_BG: Dict[str, str] = {
    "teal": "#18235c",
    "modern": "#1A1F36",
    "classic": "#1B365D",
    "bold": "#15216E",
    "elegant": "#1a1a1a",
}

_THEME_DEFAULT_COLORS: Dict[str, str] = {
    "teal": "#34d1c3",
    "modern": "#FF6B5B",
    "classic": "#1B365D",
    "bold": "#15216E",
    "elegant": "#1a1a1a",
}

TEMPLATES_DIR = Path(__file__).parent / "templates" / "market"

THEME_TEMPLATES: Dict[str, str] = {
    "teal": "teal/market.jinja2",
    "bold": "bold/market.jinja2",
    "classic": "classic/market.jinja2",
    "modern": "modern/market.jinja2",
    "elegant": "elegant/market.jinja2",
}

LAYOUT_MAP: Dict[str, str] = {
    "new_listings_gallery": "gallery",
    "featured_listings": "gallery",
    "open_houses": "gallery",
    "market_snapshot": "market_narrative",
    "closed": "closed_inventory",
    "inventory": "closed_inventory",
    "price_bands": "analytics",
    "new_listings": "analytics",
}

ALL_REPORT_TYPES = list(LAYOUT_MAP.keys())
ALL_THEMES = list(THEME_TEMPLATES.keys())


class MarketReportBuilder:
    """
    Builds themed HTML market reports using Jinja2 templates.

    Accepts a single ``report_data`` dict (same shape as the worker task's
    result_json merged with branding).
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

        # Theme resolution: name string → template path
        theme_input = report_data.get("theme_id") or report_data.get("theme", "teal")
        if isinstance(theme_input, str) and theme_input in THEME_TEMPLATES:
            self.theme_name = theme_input
        else:
            self.theme_name = "teal"

        self.accent_color: str | None = report_data.get("accent_color")

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

    # ── colour helpers ────────────────────────────────────────────────────

    def _get_theme_color(self) -> str:
        """
        Accent priority: explicit accent_color → branding.accent_color →
        branding.primary_color → theme default.
        """
        branding = self.report_data.get("branding") or {}
        return (
            self.accent_color
            or branding.get("accent_color")
            or branding.get("primary_color")
            or _THEME_DEFAULT_COLORS.get(self.theme_name, "#34d1c3")
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
        return {
            "title": report_titles.get(self.report_type, "Market Report"),
            "subtitle": data.get("filters_label", ""),
            "city": data.get("city", ""),
            "lookback_days": data.get("lookback_days", 30),
            "total_count": total,
        }

    def _build_listings_context(self) -> list:
        raw = self.report_data.get("listings") or self.report_data.get("listings_sample") or []
        listings = []
        for item in raw:
            listings.append({
                "address": item.get("street_address") or item.get("address", ""),
                "city": item.get("city", ""),
                "list_price": item.get("list_price") or item.get("price", 0),
                "close_price": item.get("close_price"),
                "beds": item.get("bedrooms") or item.get("beds", 0),
                "baths": item.get("bathrooms") or item.get("baths", 0),
                "sqft": item.get("sqft") or item.get("living_area", 0),
                "status": item.get("status", "Active"),
                "days_on_market": item.get("days_on_market") or item.get("dom", 0),
                "photo_url": item.get("photo_url") or item.get("image_url"),
                "lat": item.get("lat") or item.get("latitude"),
                "lng": item.get("lng") or item.get("longitude"),
            })
        return listings

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
        }

    # ── render ────────────────────────────────────────────────────────────

    def render_html(self) -> str:
        """
        Render the complete HTML report.

        Returns:
            Complete HTML string ready for PDF generation via PDFShift.
        """
        theme_color = self._get_theme_color()
        dark_bg = _THEME_DARK_BG.get(self.theme_name, "#18235c")
        color_roles = compute_color_roles(theme_color, dark_bg)

        context: Dict[str, Any] = {
            # Theme + layout
            "theme_name": self.theme_name,
            "layout": self.layout,
            "report_type": self.report_type,
            # Colour roles
            **color_roles,
            # Section contexts
            "header": self._build_header_context(),
            "listings": self._build_listings_context(),
            "stats": self._build_stats_context(),
            "agent": self._build_agent_context(),
            # AI narrative (optional)
            "ai_insights": self.report_data.get("ai_insights", ""),
            # Price bands data (analytics layout)
            "price_bands": self.report_data.get("price_bands") or [],
        }

        template_path = THEME_TEMPLATES.get(self.theme_name, THEME_TEMPLATES["teal"])
        logger.info(
            "Rendering market report: type=%s, theme=%s, layout=%s",
            self.report_type,
            self.theme_name,
            self.layout,
        )

        try:
            template = self.env.get_template(template_path)
            html = template.render(**context)
            logger.info(
                "Rendered market report: theme=%s, html_len=%d",
                self.theme_name,
                len(html),
            )
            return html
        except Exception as e:
            logger.error(
                "Failed to render market report (theme=%s, type=%s): %s",
                self.theme_name,
                self.report_type,
                e,
            )
            raise

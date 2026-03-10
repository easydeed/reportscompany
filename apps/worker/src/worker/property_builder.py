"""
Property Report Builder
=======================

Renders property reports (seller/buyer) using self-contained Jinja2 templates.
All 5 themes use the same unified data contract.

Themes:
- classic (1): Navy + Sky Blue, Merriweather + Source Sans Pro
- modern (2): Coral + Midnight, Space Grotesk + DM Sans
- elegant (3): Burgundy + Gold, Playfair Display + Montserrat
- teal (4): Teal + Navy, Montserrat
- bold (5): Navy + Gold, Oswald + Montserrat

Usage:
    builder = PropertyReportBuilder(report_data)
    html = builder.render_html()
"""

import os
import logging
import colorsys
from typing import Dict, Any, List, Optional
from pathlib import Path
from jinja2 import Environment, FileSystemLoader, select_autoescape

logger = logging.getLogger(__name__)

_BUILDER_VERSION = "2026-03-05-v1"
logger.warning("[DIAGNOSTIC] PropertyReportBuilder version: %s", _BUILDER_VERSION)


# =============================================================================
# Color Utility Functions — compute derived roles from a single accent hex
# =============================================================================

def _hex_to_rgb(hex_color: str) -> tuple:
    """Convert '#RRGGBB' to (r, g, b) floats in 0-1."""
    h = hex_color.lstrip("#")
    if len(h) == 3:
        h = h[0]*2 + h[1]*2 + h[2]*2
    return tuple(int(h[i:i+2], 16) / 255.0 for i in (0, 2, 4))


def _rgb_to_hex(r: float, g: float, b: float) -> str:
    """Convert (r, g, b) floats in 0-1 to '#RRGGBB'."""
    return "#{:02x}{:02x}{:02x}".format(
        max(0, min(255, int(r * 255))),
        max(0, min(255, int(g * 255))),
        max(0, min(255, int(b * 255))),
    )


def _relative_luminance(r: float, g: float, b: float) -> float:
    """WCAG relative luminance (0 = black, 1 = white)."""
    def _lin(c):
        return c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4
    return 0.2126 * _lin(r) + 0.7152 * _lin(g) + 0.0722 * _lin(b)


def _lighten(hex_color: str, amount: float = 0.3) -> str:
    """Lighten a color by mixing with white."""
    r, g, b = _hex_to_rgb(hex_color)
    return _rgb_to_hex(
        r + (1.0 - r) * amount,
        g + (1.0 - g) * amount,
        b + (1.0 - b) * amount,
    )


def _darken(hex_color: str, amount: float = 0.25) -> str:
    """Darken a color by mixing toward black."""
    r, g, b = _hex_to_rgb(hex_color)
    return _rgb_to_hex(r * (1 - amount), g * (1 - amount), b * (1 - amount))


def _ensure_readable_on_dark(hex_color: str, dark_bg: str = "#18235c") -> str:
    """
    Return a version of hex_color that has enough contrast on a dark background.
    If the color is too dark, progressively lighten it until readable.
    Target: WCAG AA (contrast ratio ≥ 4.5) or at minimum 3.0 for large text.
    """
    r, g, b = _hex_to_rgb(hex_color)
    lum_color = _relative_luminance(r, g, b)
    br, bg_val, bb = _hex_to_rgb(dark_bg)
    lum_bg = _relative_luminance(br, bg_val, bb)

    # Contrast ratio: (lighter + 0.05) / (darker + 0.05)
    lighter = max(lum_color, lum_bg)
    darker = min(lum_color, lum_bg)
    ratio = (lighter + 0.05) / (darker + 0.05)

    if ratio >= 3.0:
        return hex_color  # Already readable

    # Lighten the color until we hit contrast ≥ 3.0
    h, s, v = colorsys.rgb_to_hsv(r, g, b)
    for _ in range(30):
        v = min(1.0, v + 0.04)
        s = max(0.0, s - 0.02)  # Slightly desaturate as we brighten
        nr, ng, nb = colorsys.hsv_to_rgb(h, s, v)
        lum_new = _relative_luminance(nr, ng, nb)
        new_ratio = (max(lum_new, lum_bg) + 0.05) / (min(lum_new, lum_bg) + 0.05)
        if new_ratio >= 3.0:
            return _rgb_to_hex(nr, ng, nb)

    return _rgb_to_hex(*colorsys.hsv_to_rgb(h, s, v))


def _ensure_readable_on_light(hex_color: str, light_bg: str = "#ffffff") -> str:
    """
    Return a version of hex_color that has enough contrast on a light background.
    If the color is too light/bright, darken it until readable.
    """
    r, g, b = _hex_to_rgb(hex_color)
    lum_color = _relative_luminance(r, g, b)
    lr, lg, lb = _hex_to_rgb(light_bg)
    lum_bg = _relative_luminance(lr, lg, lb)

    lighter = max(lum_color, lum_bg)
    darker = min(lum_color, lum_bg)
    ratio = (lighter + 0.05) / (darker + 0.05)

    if ratio >= 3.0:
        return hex_color

    # Darken the color until readable
    h, s, v = colorsys.rgb_to_hsv(r, g, b)
    for _ in range(30):
        v = max(0.0, v - 0.04)
        nr, ng, nb = colorsys.hsv_to_rgb(h, s, v)
        lum_new = _relative_luminance(nr, ng, nb)
        new_ratio = (max(lum_new, lum_bg) + 0.05) / (min(lum_new, lum_bg) + 0.05)
        if new_ratio >= 3.0:
            return _rgb_to_hex(nr, ng, nb)

    return _rgb_to_hex(*colorsys.hsv_to_rgb(h, s, v))


def _text_on_accent(hex_color: str) -> str:
    """Return '#ffffff' or '#1a1a1a' depending on accent brightness."""
    r, g, b = _hex_to_rgb(hex_color)
    lum = _relative_luminance(r, g, b)
    return "#ffffff" if lum < 0.35 else "#1a1a1a"


def compute_color_roles(hex_color: str, dark_bg: str = "#18235c") -> Dict[str, str]:
    """
    From a single accent hex, compute a complete set of color roles:

      theme_color          – the raw user pick
      theme_color_light    – lighter tint for subtle backgrounds
      theme_color_dark     – darker shade for borders / hover states
      theme_color_on_dark  – guaranteed readable on dark backgrounds
      theme_color_on_light – guaranteed readable on light backgrounds
      theme_color_text     – white or dark text to overlay on the accent
    """
    return {
        "theme_color":          hex_color,
        "theme_color_light":    _lighten(hex_color, 0.35),
        "theme_color_dark":     _darken(hex_color, 0.25),
        "theme_color_on_dark":  _ensure_readable_on_dark(hex_color, dark_bg),
        "theme_color_on_light": _ensure_readable_on_light(hex_color, "#ffffff"),
        "theme_color_text":     _text_on_accent(hex_color),
    }

# Template directory - points to property/ for Jinja2 inheritance to work
# This allows templates to use {% extends '_base/base.jinja2' %}
TEMPLATES_DIR = Path(__file__).parent / "templates" / "property"

# Theme template paths (relative to templates/property/)
# v3.0: Standalone self-contained templates (unique cover + CSS per theme)
THEME_TEMPLATES = {
    "teal": "teal/teal_report.jinja2",
    "bold": "bold/bold_report.jinja2",
    "classic": "classic/classic_report.jinja2",
    "modern": "modern/modern_report.jinja2",
    "elegant": "elegant/elegant_report.jinja2",
}

# Theme number to name mapping (for backward compatibility)
THEME_NUMBER_MAP = {
    1: "classic",
    2: "modern",
    3: "elegant",
    4: "teal",
    5: "bold",
}

# Configuration from environment
ASSETS_BASE_URL = os.getenv("ASSETS_BASE_URL", "https://assets.trendyreports.com")
GOOGLE_MAPS_API_KEY = os.getenv("GOOGLE_MAPS_API_KEY", "")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
logger.warning("[DIAGNOSTIC] property_builder loaded at startup")
logger.warning("[DIAGNOSTIC] GOOGLE_MAPS_API_KEY present: %s, length: %d", bool(GOOGLE_MAPS_API_KEY), len(GOOGLE_MAPS_API_KEY))
logger.warning("[DIAGNOSTIC] OPENAI_API_KEY present: %s, length: %d", bool(OPENAI_API_KEY), len(OPENAI_API_KEY))
logger.warning("[DIAGNOSTIC] TEMPLATES_DIR: %s, exists: %s", TEMPLATES_DIR, TEMPLATES_DIR.exists())


class PropertyReportBuilder:
    """
    Builds HTML property reports using the orchestrator template system.
    
    The orchestrator (seller_report.jinja2) handles:
    - Theme selection (1-5)
    - Page set configuration (full 21 pages / compact 9 pages / custom)
    - Including all section templates
    
    Expected report_data structure:
    {
        "id": "uuid",
        "account_id": "uuid",
        "report_type": "seller" | "buyer",
        "theme": 1-5,
        "accent_color": "#0d294b",
        "language": "en" | "es",
        "page_set": "full" | "compact" | ["cover", "property_details", ...],
        
        # Property fields
        "property_address": "123 Main St",
        "property_city": "Los Angeles",
        "property_state": "CA",
        "property_zip": "90210",
        "property_county": "Los Angeles",
        "apn": "1234-567-890",
        "owner_name": "John Doe",
        "legal_description": "LOT 1 BLK 2...",
        "property_type": "Single Family",
        
        # SiteX data (full property details from property search)
        "sitex_data": { ... },
        
        # Comparables
        "comparables": [ ... ],
        
        # Agent info (from user join)
        "agent": {
            "name": "Jane Agent",
            "email": "jane@example.com",
            "phone": "555-1234",
            "photo_url": "https://...",
            "title": "Real Estate Agent",
            "license_number": "01234567",
            "company_name": "Acme Realty",
            "logo_url": "https://..."
        },
        
        # Branding (from affiliate_branding join, if applicable)
        "branding": {
            "display_name": "Acme Real Estate",
            "logo_url": "https://...",
            "primary_color": "#0d294b",
            "accent_color": "#2563eb"
        }
    }
    """
    
    def __init__(self, report_data: Dict[str, Any]):
        self.report_data = report_data
        self.report_type = report_data.get("report_type", "seller")
        self.accent_color = report_data.get("accent_color")
        self.language = report_data.get("language", "en")
        
        # Resolve theme: accept either theme name (str) or theme number (int)
        theme_input = report_data.get("theme", 4)  # Default to teal
        if isinstance(theme_input, str) and theme_input in THEME_TEMPLATES:
            self.theme_name = theme_input
            self.theme_number = {v: k for k, v in THEME_NUMBER_MAP.items()}.get(theme_input, 4)
        elif isinstance(theme_input, int) and theme_input in THEME_NUMBER_MAP:
            self.theme_name = THEME_NUMBER_MAP[theme_input]
            self.theme_number = theme_input
        else:
            # Default to teal
            self.theme_name = "teal"
            self.theme_number = 4
        
        # Legacy compatibility: keep self.theme as the number
        self.theme = self.theme_number
        
        # Use selected_pages if provided, otherwise use default 7-page set
        # All unified templates use the same 7-page layout
        selected_pages = report_data.get("selected_pages")
        if selected_pages and isinstance(selected_pages, list) and len(selected_pages) > 0:
            self.page_set = selected_pages
        else:
            self.page_set = ["cover", "contents", "aerial", "property", "analysis", "comparables", "range"]
        
        # Initialize Jinja2 environment - single directory for all templates
        self.env = Environment(
            loader=FileSystemLoader(str(TEMPLATES_DIR)),
            autoescape=select_autoescape(['html', 'xml', 'jinja2']),
            trim_blocks=True,
            lstrip_blocks=True
        )
        
        # Add custom filters
        self.env.filters['format_currency'] = self._format_currency
        self.env.filters['format_currency_short'] = self._format_currency_short
        self.env.filters['format_number'] = self._format_number
        self.env.filters['truncate'] = self._truncate
        
    @staticmethod
    def _format_currency(value: Any) -> str:
        """Format number as currency."""
        if value is None:
            return "N/A"
        try:
            return f"${int(float(value)):,}"
        except (ValueError, TypeError):
            return str(value)
    
    @staticmethod
    def _format_number(value: Any) -> str:
        """Format number with commas."""
        if value is None:
            return "N/A"
        try:
            return f"{int(float(value)):,}"
        except (ValueError, TypeError):
            return str(value)
    
    @staticmethod
    def _format_currency_short(value: Any) -> str:
        """Format as short currency: 470000 -> $470k, 1200000 -> $1.2M"""
        if value is None:
            return "-"
        try:
            val = float(value)
            if val >= 1_000_000:
                return f"${val/1_000_000:.1f}M"
            elif val >= 1_000:
                return f"${val/1_000:.0f}k"
            else:
                return f"${val:.0f}"
        except (ValueError, TypeError):
            return str(value)
    
    @staticmethod
    def _truncate(value: Any, length: int = 40, suffix: str = "...") -> str:
        """Truncate string to specified length."""
        if value is None:
            return ""
        text = str(value)
        if len(text) <= length:
            return text
        return text[:length - len(suffix)] + suffix
    
    def _build_property_context(self) -> Dict[str, Any]:
        """
        Build property context matching template requirements.
        
        Maps report_data fields to the expected 'property' object structure.
        Supports both old-style (street) and new V0 template (street_address) naming.
        """
        sitex_data = self.report_data.get("sitex_data") or {}
        
        street = self.report_data.get("property_address", "")
        city = self.report_data.get("property_city", "")
        state = self.report_data.get("property_state", "")
        zip_code = self.report_data.get("property_zip", "")
        
        # Build full address string
        full_address = f"{street}, {city}, {state} {zip_code}".strip(", ")
        
        return {
            # Address (required) - both naming conventions for compatibility
            "street": street,
            "street_address": street,  # V0 template naming
            "city": city,
            "state": state,
            "zip_code": zip_code,
            "full_address": full_address,
            
            # Location for maps
            "latitude": sitex_data.get("latitude") or sitex_data.get("lat"),
            "longitude": sitex_data.get("longitude") or sitex_data.get("lng"),
            
            # Owner info
            "owner_name": self.report_data.get("owner_name", "") or sitex_data.get("owner_name", ""),
            "secondary_owner": sitex_data.get("secondary_owner") or "-",
            "county": self.report_data.get("property_county", "") or sitex_data.get("county", ""),
            "apn": self.report_data.get("apn", "") or sitex_data.get("apn", ""),
            
            # Property details (numeric fields default to 0 for safe template arithmetic)
            "bedrooms": sitex_data.get("bedrooms") or 0,
            "bathrooms": sitex_data.get("bathrooms") or 0,
            "sqft": sitex_data.get("sqft") or 0,
            "lot_size": sitex_data.get("lot_size") or 0,
            "year_built": sitex_data.get("year_built") or 0,
            "garage": sitex_data.get("garage") or "-",
            "fireplace": sitex_data.get("fireplace") or "-",
            "pool": sitex_data.get("pool") or "No",
            "total_rooms": sitex_data.get("total_rooms") or "-",
            "num_units": sitex_data.get("num_units") or "-",
            "units": sitex_data.get("num_units") or "-",  # V0 template naming
            "zoning": sitex_data.get("zoning") or "-",
            "property_type": self.report_data.get("property_type", "") or sitex_data.get("property_type", ""),
            "use_code": sitex_data.get("use_code") or "-",
            
            # Tax/Assessment
            "assessed_value": sitex_data.get("assessed_value") or 0,
            "tax_amount": sitex_data.get("tax_amount") or 0,
            "land_value": sitex_data.get("land_value") or 0,
            "improvement_value": sitex_data.get("improvement_value") or 0,
            "percent_improved": sitex_data.get("percent_improved") or 0,
            "improvement_pct": sitex_data.get("percent_improved") or 0,  # V0 template naming
            "tax_status": sitex_data.get("tax_status") or "Current",
            "tax_rate_area": sitex_data.get("tax_rate_area") or "-",
            "tax_year": sitex_data.get("tax_year") or "-",
            
            # Legal
            "legal_description": self.report_data.get("legal_description", "") or sitex_data.get("legal_description", ""),
            "mailing_address": sitex_data.get("mailing_address") or "",
            "census_tract": sitex_data.get("census_tract") or "-",
            "housing_tract": sitex_data.get("housing_tract") or "-",
            "lot_number": sitex_data.get("lot_number") or "-",
            "page_grid": sitex_data.get("page_grid") or "-",
            "partial_bath": sitex_data.get("partial_bath") or 0,
            "notes": sitex_data.get("notes") or "",
        }
    
    def _build_agent_context(self) -> Dict[str, Any]:
        """
        Build agent context matching template requirements.
        Supports both old-style and new V0 template naming conventions.
        """
        agent = self.report_data.get("agent") or {}
        branding = self.report_data.get("branding") or {}
        
        # Build full agent address
        agent_street = agent.get("company_address") or agent.get("street") or ""
        agent_city = agent.get("company_city") or agent.get("city") or ""
        agent_state = agent.get("company_state") or agent.get("state") or ""
        agent_zip = agent.get("company_zip") or agent.get("zip_code") or ""
        agent_address = f"{agent_street}, {agent_city}, {agent_state} {agent_zip}".strip(", ")
        
        # Format license number for display
        license_num = agent.get("license_number")
        license_display = f"CA BRE#{license_num}" if license_num else ""
        
        return {
            "name": agent.get("name", ""),
            "title": agent.get("title", "Realtor®"),
            "license_number": license_num,
            "license": license_display,  # V0 template naming (formatted)
            "phone": agent.get("phone", ""),
            "email": agent.get("email", ""),
            "company_name": agent.get("company_name") or branding.get("display_name", ""),
            "street": agent_street,
            "city": agent_city,
            "state": agent_state,
            "zip_code": agent_zip,
            "address": agent_address,  # V0 template expects full address string
            "photo_url": agent.get("photo_url"),
            "logo_url": agent.get("logo_url") or branding.get("logo_url"),
            # Standalone template fields (with safe defaults in templates)
            "company_short": agent.get("company_short") or (
                (agent.get("company_name") or "TR")[:2].upper()
            ),
            "company_tagline": agent.get("company_tagline", ""),
        }
    
    def _build_comparables_context(self) -> List[Dict[str, Any]]:
        """
        Build comparables list matching template requirements.
        
        Each comparable should have:
        - address, latitude, longitude
        - image_url, map_image_url (optional)
        - price/sale_price, days_on_market, distance/distance_miles
        - sqft, price_per_sqft
        - bedrooms, bathrooms, year_built
        - lot_size, pool, sold_date
        
        Handles field name variations from different sources:
        - Frontend sends: lat/lng, photo_url, distance_miles
        - SimplyRETS sends: latitude/longitude, photos, etc.
        """
        raw_comps = self.report_data.get("comparables") or []
        logger.info("_build_comparables_context: %d raw comps received", len(raw_comps))

        comparables = []
        for comp in raw_comps[:6]:  # Max 6 comparables (3 rows of 2)
            # Handle field name variations from different sources
            # Frontend: lat/lng, Backend: latitude/longitude
            latitude = comp.get("latitude") or comp.get("lat")
            longitude = comp.get("longitude") or comp.get("lng")
            
            # Frontend: photo_url, Backend: image_url or photos array
            image_url = (
                comp.get("image_url") or 
                comp.get("photo_url") or 
                (comp.get("photos", [None])[0] if comp.get("photos") else None)
            )
            logger.warning(
                "[DIAGNOSTIC] Comp %s: photo_url=%s, map_image_url=%s, resolved_image=%s",
                comp.get("address", "?")[:30],
                bool(comp.get("photo_url")),
                bool(comp.get("map_image_url")),
                bool(image_url),
            )

            # Frontend: distance_miles, Backend: distance
            distance_raw = comp.get("distance") or comp.get("distance_miles", "")
            distance_formatted = distance_raw
            if distance_raw and isinstance(distance_raw, (int, float)):
                distance_formatted = f"{distance_raw:.1f} mi"
            
            # Get raw price for stats calculations
            raw_price = comp.get("price") or comp.get("close_price") or comp.get("sale_price") or comp.get("list_price")
            
            # Generate map URL if we have coordinates
            map_image_url = comp.get("map_image_url")
            if not map_image_url and latitude and longitude and GOOGLE_MAPS_API_KEY:
                map_image_url = (
                    f"https://maps.googleapis.com/maps/api/staticmap"
                    f"?center={latitude},{longitude}"
                    f"&zoom=16&size=400x200&maptype=roadmap"
                    f"&markers={latitude},{longitude}"
                    f"&key={GOOGLE_MAPS_API_KEY}"
                )
            
            # Ensure raw_price is numeric
            try:
                raw_price_num = float(raw_price) if raw_price else 0
            except (ValueError, TypeError):
                raw_price_num = 0

            comp_sqft = comp.get("sqft") or comp.get("area") or 0
            try:
                comp_sqft = float(comp_sqft)
            except (ValueError, TypeError):
                comp_sqft = 0

            # ── Status & dates ──────────────────────────────────────────────
            status = comp.get("status") or "Active"
            list_date_raw = comp.get("list_date") or ""
            sold_date_raw = comp.get("sold_date") or comp.get("close_date") or ""

            # Display date: active/pending → list_date; closed → sold/close_date
            is_active = status.lower() in ("active", "pending")
            display_date = self._fmt_date(list_date_raw if is_active else sold_date_raw)
            display_date_label = "Listed" if is_active else "Sold"

            resolved_addr = comp.get("address") or comp.get("full_address", "")

            comparables.append({
                "address": resolved_addr,
                "latitude": latitude,
                "longitude": longitude,
                "image_url": image_url,
                "photo_url": image_url,  # V0 template field (prefer property photo)
                "map_image_url": map_image_url,  # Fallback satellite thumbnail
                "price": self._format_price(raw_price),  # Formatted string
                "sale_price": raw_price_num,  # V0 template (raw number for filter/arithmetic)
                "list_price": float(comp.get("list_price") or 0),
                # Dates
                "sold_date": display_date,           # Formatted display date (may be list_date for active)
                "sold_date_label": display_date_label,  # "Listed" or "Sold"
                "list_date": self._fmt_date(list_date_raw),
                "status": status,
                "days_on_market": comp.get("days_on_market") or comp.get("dom") or 0,
                "distance": distance_formatted,
                "distance_miles": float(distance_raw) if isinstance(distance_raw, (int, float)) else 0,
                "sqft": comp_sqft,
                "price_per_sqft": self._calc_price_per_sqft(raw_price, comp_sqft) or 0,
                "bedrooms": comp.get("bedrooms") or 0,
                "bathrooms": comp.get("bathrooms") or 0,
                "year_built": comp.get("year_built") or 0,
                "lot_size": comp.get("lot_size") or 0,
                "lot_display": comp.get("lot_display") or "",
                "hoa_fee": comp.get("hoa_fee"),
                "hoa_frequency": comp.get("hoa_frequency") or "",
                "pool": comp.get("pool") if isinstance(comp.get("pool"), bool) else (comp.get("pool", "No") == "Yes"),
            })
        
        logger.info("_build_comparables_context: returning %d processed comps", len(comparables))
        return comparables
    
    def _format_price(self, price: Any) -> str:
        """Format price for display."""
        if price is None:
            return "N/A"
        try:
            return f"${int(float(price)):,}"
        except (ValueError, TypeError):
            return str(price)
    
    def _calc_price_per_sqft(self, price: Any, sqft: Any) -> Optional[int]:
        """Calculate price per square foot."""
        try:
            if price and sqft:
                return int(float(price) / float(sqft))
        except (ValueError, TypeError, ZeroDivisionError):
            pass
        return None

    def _fmt_date(self, date_str: Any) -> str:
        """
        Format an ISO date string for display on comparable cards.

        Examples:
          '2024-03-15T00:00:00Z'  →  'Mar 2024'
          '2024-03-15'            →  'Mar 2024'
          None / ''               →  ''
        """
        if not date_str:
            return ""
        try:
            from datetime import datetime as _dt
            raw = str(date_str).split("T")[0]   # strip time component
            return _dt.strptime(raw, "%Y-%m-%d").strftime("%b %Y")
        except (ValueError, AttributeError):
            # Graceful fallback: return first 10 chars (keeps YYYY-MM-DD readable)
            return str(date_str)[:10]

    def _build_neighborhood_context(self) -> Dict[str, Any]:
        """
        Build neighborhood statistics context.
        Uses data from sitex_data if available, otherwise defaults.
        """
        sitex_data = self.report_data.get("sitex_data") or {}
        neighborhood = sitex_data.get("neighborhood") or {}
        
        return {
            "female_ratio": neighborhood.get("female_ratio", "51.5"),
            "male_ratio": neighborhood.get("male_ratio", "48.5"),
            "avg_sale_price": neighborhood.get("avg_sale_price", ""),
            "avg_sqft": neighborhood.get("avg_sqft", ""),
            "avg_beds": neighborhood.get("avg_beds", "3"),
            "avg_baths": neighborhood.get("avg_baths", "2"),
        }
    
    def _build_area_analysis_context(self) -> Dict[str, Any]:
        """
        Build area analysis context for charts and statistics.
        """
        sitex_data = self.report_data.get("sitex_data") or {}
        area = sitex_data.get("area_analysis") or {}
        
        return {
            "chart_url": area.get("chart_url"),
            "area_min_radius": area.get("area_min_radius", "0.1 mi"),
            "area_median_radius": area.get("area_median_radius", "0.5 mi"),
            "area_max_radius": area.get("area_max_radius", "1.2 mi"),
            "living_area": sitex_data.get("sqft"),
            "living_area_low": area.get("living_area_low"),
            "living_area_median": area.get("living_area_median"),
            "living_area_high": area.get("living_area_high"),
            "price_per_sqft": area.get("price_per_sqft"),
            "price_per_sqft_low": area.get("price_per_sqft_low"),
            "price_per_sqft_median": area.get("price_per_sqft_median"),
            "price_per_sqft_high": area.get("price_per_sqft_high"),
            "year_built": sitex_data.get("year_built"),
            "year_low": area.get("year_low"),
            "year_median": area.get("year_median"),
            "year_high": area.get("year_high"),
            "lot_size": sitex_data.get("lot_size"),
            "lot_size_low": area.get("lot_size_low"),
            "lot_size_median": area.get("lot_size_median"),
            "lot_size_high": area.get("lot_size_high"),
            "bedrooms": sitex_data.get("bedrooms"),
            "bedrooms_low": area.get("bedrooms_low"),
            "bedrooms_median": area.get("bedrooms_median"),
            "bedrooms_high": area.get("bedrooms_high"),
            "bathrooms": sitex_data.get("bathrooms"),
            "bathrooms_low": area.get("bathrooms_low"),
            "bathrooms_median": area.get("bathrooms_median"),
            "bathrooms_high": area.get("bathrooms_high"),
            "stories": area.get("stories"),
            "pool": sitex_data.get("pool"),
            "pool_low": area.get("pool_low"),
            "pool_median": area.get("pool_median"),
            "pool_high": area.get("pool_high"),
            "sale_price": area.get("sale_price"),
            "sale_price_low": area.get("sale_price_low"),
            "sale_price_median": area.get("sale_price_median"),
            "sale_price_high": area.get("sale_price_high"),
        }
    
    @staticmethod
    def _extract_price(comp: Dict) -> Optional[float]:
        """Extract a numeric price from a comp dict, checking all known field names."""
        for key in ("price", "close_price", "sale_price", "list_price", "sold_price"):
            val = comp.get(key)
            if val is not None and val != "" and val != "-":
                try:
                    fval = float(val)
                    if fval > 0:
                        return fval
                except (ValueError, TypeError):
                    continue
        return None

    def _build_range_of_sales_context(self) -> Dict[str, Any]:
        """
        Build range of sales context from comparables.
        """
        comparables = self.report_data.get("comparables") or []
        
        if not comparables:
            return {}
        
        prices = []
        sqfts = []
        beds = []
        baths = []
        
        for comp in comparables:
            price_val = self._extract_price(comp)
            if price_val is not None:
                prices.append(price_val)
            if comp.get("sqft"):
                try:
                    sqfts.append(float(comp.get("sqft")))
                except (ValueError, TypeError):
                    pass
            if comp.get("bedrooms"):
                try:
                    beds.append(int(comp.get("bedrooms")))
                except (ValueError, TypeError):
                    pass
            if comp.get("bathrooms"):
                try:
                    baths.append(float(comp.get("bathrooms")))
                except (ValueError, TypeError):
                    pass
        
        return {
            "total_comps": len(comparables),
            "avg_sqft": f"{int(sum(sqfts)/len(sqfts)):,}" if sqfts else "",
            "avg_beds": round(sum(beds)/len(beds)) if beds else "",
            "avg_baths": round(sum(baths)/len(baths)) if baths else "",
            "price_min": str(int(min(prices)/1000)) if prices else "",
            "price_max": str(int(max(prices)/1000)) if prices else "",
        }
    
    def _build_stats_context(self) -> Dict[str, Any]:
        """
        Build stats context for V0 Teal template.
        
        Creates the stats object with piq (property in question), low, medium, high
        sub-objects for the Area Sales Analysis table.
        """
        comparables = self.report_data.get("comparables") or []
        sitex_data = self.report_data.get("sitex_data") or {}
        
        # Calculate statistics from comparables
        prices = []
        sqfts = []
        beds = []
        baths = []
        years = []
        lots = []
        distances = []
        
        days_on_market = []
        
        for comp in comparables:
            price_val = self._extract_price(comp)
            if price_val is not None:
                prices.append(price_val)
            sqft_val = comp.get("sqft") or comp.get("living_area") or comp.get("area")
            if sqft_val:
                try:
                    sqfts.append(float(sqft_val))
                except (ValueError, TypeError):
                    pass
            if comp.get("bedrooms"):
                try:
                    beds.append(int(comp.get("bedrooms")))
                except (ValueError, TypeError):
                    pass
            if comp.get("bathrooms"):
                try:
                    baths.append(float(comp.get("bathrooms")))
                except (ValueError, TypeError):
                    pass
            if comp.get("year_built"):
                try:
                    years.append(int(comp.get("year_built")))
                except (ValueError, TypeError):
                    pass
            if comp.get("lot_size"):
                try:
                    lots.append(float(comp.get("lot_size")))
                except (ValueError, TypeError):
                    pass
            dist = comp.get("distance_miles") or comp.get("distance")
            if dist and isinstance(dist, (int, float)):
                distances.append(float(dist))
            dom = comp.get("days_on_market")
            if dom is not None:
                try:
                    days_on_market.append(int(dom))
                except (ValueError, TypeError):
                    pass

        logger.info("_build_stats_context: %d prices, %d sqfts from %d comps", len(prices), len(sqfts), len(comparables))
        
        # Sort comparables by price to get low/medium/high
        sorted_by_price = sorted(
            [c for c in comparables if self._extract_price(c) is not None],
            key=lambda x: self._extract_price(x) or 0
        )
        
        # Get low, medium, high comps
        low_comp = sorted_by_price[0] if sorted_by_price else {}
        high_comp = sorted_by_price[-1] if sorted_by_price else {}
        med_idx = len(sorted_by_price) // 2
        med_comp = sorted_by_price[med_idx] if sorted_by_price else {}
        
        def _safe_num(val, default=0):
            """Convert value to a number, returning default for None/'-'/non-numeric."""
            if val is None or val == "-" or val == "":
                return default
            try:
                return float(val)
            except (ValueError, TypeError):
                return default

        def extract_comp_stats(comp):
            raw_price = self._extract_price(comp) or 0
            sqft = comp.get("sqft") or comp.get("living_area") or comp.get("area")
            return {
                "distance": _safe_num(comp.get("distance_miles") or comp.get("distance"), 0),
                "sqft": _safe_num(sqft, 0),
                "price_per_sqft": _safe_num(self._calc_price_per_sqft(raw_price, sqft), 0),
                "year_built": _safe_num(comp.get("year_built"), 0),
                "lot_size": _safe_num(comp.get("lot_size"), 0),
                "bedrooms": _safe_num(comp.get("bedrooms"), 0),
                "bathrooms": _safe_num(comp.get("bathrooms"), 0),
                "stories": _safe_num(comp.get("stories"), 0),
                "pools": 1 if comp.get("pool") else 0,
                "price": _safe_num(raw_price, 0),
            }
        
        # Property in question stats (from sitex_data)
        # Use assessed_value as fallback for estimated_value since SiteX may not provide it
        est_value = sitex_data.get("estimated_value") or sitex_data.get("assessed_value") or 0
        piq = {
            "distance": 0,
            "sqft": _safe_num(sitex_data.get("sqft"), 0),
            "price_per_sqft": _safe_num(self._calc_price_per_sqft(est_value, sitex_data.get("sqft")), 0),
            "year_built": _safe_num(sitex_data.get("year_built"), 0),
            "lot_size": _safe_num(sitex_data.get("lot_size"), 0),
            "bedrooms": _safe_num(sitex_data.get("bedrooms"), 0),
            "bathrooms": _safe_num(sitex_data.get("bathrooms"), 0),
            "stories": _safe_num(sitex_data.get("stories"), 0),
            "pools": 1 if sitex_data.get("pool") else 0,
            "price": _safe_num(est_value, 0),
        }
        
        # Calculate avg price per sqft across all comps
        avg_price_per_sqft = 0
        if prices and sqfts and len(prices) == len(sqfts):
            ppsf_values = [p / s for p, s in zip(prices, sqfts) if s > 0]
            avg_price_per_sqft = int(sum(ppsf_values) / len(ppsf_values)) if ppsf_values else 0
        elif prices and sqfts:
            avg_price_per_sqft = int((sum(prices) / len(prices)) / (sum(sqfts) / len(sqfts))) if sqfts else 0
        
        return {
            "total_comps": len(comparables),
            "avg_sqft": int(sum(sqfts)/len(sqfts)) if sqfts else 0,
            "avg_beds": round(sum(beds)/len(beds)) if beds else 0,
            "avg_baths": round(sum(baths)/len(baths)) if baths else 0,
            "avg_price_per_sqft": avg_price_per_sqft,
            "avg_days_on_market": int(sum(days_on_market)/len(days_on_market)) if days_on_market else None,
            "active_listings": None,  # Populated if available from MLS data
            "max_distance": round(max(distances), 1) if distances else None,
            "price_low": min(prices) if prices else 0,
            "price_high": max(prices) if prices else 0,
            "piq": piq,
            "low": extract_comp_stats(low_comp),
            "medium": extract_comp_stats(med_comp),
            "high": extract_comp_stats(high_comp),
        }
    
    @staticmethod
    def _geocode_address(address: str) -> tuple:
        """
        Geocode an address via Google Maps Geocoding API.
        Returns (lat, lng) or (None, None) on failure.
        """
        if not address or not GOOGLE_MAPS_API_KEY:
            return None, None
        try:
            import httpx
            resp = httpx.get(
                "https://maps.googleapis.com/maps/api/geocode/json",
                params={"address": address, "key": GOOGLE_MAPS_API_KEY},
                timeout=10.0,
            )
            data = resp.json()
            if data.get("status") == "OK" and data.get("results"):
                loc = data["results"][0]["geometry"]["location"]
                logger.warning("[DIAGNOSTIC] Geocoded '%s' → %s, %s", address[:50], loc["lat"], loc["lng"])
                return loc["lat"], loc["lng"]
            logger.warning("[DIAGNOSTIC] Geocode failed for '%s': %s", address[:50], data.get("status"))
        except Exception as e:
            logger.warning("[DIAGNOSTIC] Geocode error: %s", e)
        return None, None

    def _build_images_context(self) -> Dict[str, Any]:
        """
        Build images context for V0 Teal template.

        Hero image priority:
          1. Explicitly stored cover_image_url (user-uploaded or pre-set)
          2. Google Street View static image based on lat/lng (auto fallback)
          3. None → template shows placeholder gradient

        Aerial map: Google Static Maps roadmap with property pin.
        """
        sitex_data = self.report_data.get("sitex_data") or {}
        lat = sitex_data.get("latitude") or sitex_data.get("lat") or None
        lng = sitex_data.get("longitude") or sitex_data.get("lng") or None

        # SiteX often returns 0/0 when it has no coordinates — treat as missing
        if lat is not None and lng is not None and float(lat) == 0 and float(lng) == 0:
            lat, lng = None, None

        # Fallback: geocode the address if we have no coordinates
        if (lat is None or lng is None) and GOOGLE_MAPS_API_KEY:
            prop = self._build_property_context()
            full_addr = prop.get("full_address") or ""
            if full_addr:
                lat, lng = self._geocode_address(full_addr)

        logger.warning("[DIAGNOSTIC] _build_images_context: lat=%s, lng=%s", lat, lng)
        logger.warning("[DIAGNOSTIC] GOOGLE_MAPS_API_KEY truthy: %s", bool(GOOGLE_MAPS_API_KEY))

        # --- Hero / Cover image -------------------------------------------
        hero = self.report_data.get("cover_image_url")
        if not hero and lat and lng and GOOGLE_MAPS_API_KEY:
            hero = (
                f"https://maps.googleapis.com/maps/api/streetview"
                f"?size=1200x800"
                f"&location={lat},{lng}"
                f"&fov=90&pitch=0"
                f"&key={GOOGLE_MAPS_API_KEY}"
            )

        # --- Aerial / neighbourhood map -----------------------------------
        aerial_map = None
        if lat and lng and GOOGLE_MAPS_API_KEY:
            aerial_map = (
                f"https://maps.googleapis.com/maps/api/staticmap"
                f"?center={lat},{lng}"
                f"&zoom=15&size=800x600&maptype=roadmap"
                f"&markers={lat},{lng}"
                f"&key={GOOGLE_MAPS_API_KEY}"
            )
            logger.warning("[DIAGNOSTIC] aerial_map URL generated: %s", aerial_map[:80])
        else:
            logger.warning(
                "[DIAGNOSTIC] aerial_map SKIPPED — lat:%s lng:%s key:%s",
                bool(lat), bool(lng), bool(GOOGLE_MAPS_API_KEY),
            )

        logger.warning("[DIAGNOSTIC] hero image: %s", "SET" if hero else "NONE")
        return {
            "hero": hero,
            "aerial_map": aerial_map,
        }
    
    # Per-theme default accent colours (must match the CSS defaults inside
    # each standalone *_report.jinja2 template).
    _THEME_DEFAULT_COLORS = {
        "teal":    "#34d1c3",
        "modern":  "#FF6B5B",
        "classic": "#1B365D",
        "bold":    "#15216E",
        "elegant": "#1a1a1a",
    }

    # Per-theme dark background colour — used by compute_color_roles() to
    # guarantee the "on_dark" variant has enough contrast.
    _THEME_DARK_BG = {
        "teal":    "#18235c",  # --navy
        "modern":  "#1A1F36",  # --midnight
        "classic": "#1B365D",  # --navy
        "bold":    "#15216E",  # --navy
        "elegant": "#1a1a1a",  # --charcoal
    }

    def _get_theme_color(self) -> str:
        """
        Get the theme color, preferring wizard accent over branding primary.
        Falls back to the theme's built-in default so CSS variables are
        never rendered as the literal string ``None``.
        """
        branding = self.report_data.get("branding") or {}
        accent = self.accent_color
        branding_primary = branding.get("primary_color")
        theme_default = self._THEME_DEFAULT_COLORS.get(self.theme_name, "#34d1c3")

        logger.warning(
            "[DIAGNOSTIC] _get_theme_color: accent_color=%s, branding_primary=%s, theme_default=%s",
            accent, branding_primary, theme_default,
        )

        result = accent or branding_primary or theme_default
        logger.warning("[DIAGNOSTIC] _get_theme_color result: %s", result)
        return result
    
    def _build_default_content_sections(self) -> Dict[str, Any]:
        """
        Build default content sections for text-heavy pages.
        Templates have built-in defaults, but we can override here if needed.
        """
        return {
            # Use template defaults for these sections
            "introduction": {},
            "roadmap": {
                "points": [{"title": None, "sub_title": None}] * 7  # 7 points required
            },
            "promise": {
                "points": [{"title": None, "content": None}] * 6  # 6 points required
            },
            "how_buyers_find": {},
            "pricing": {},
            "avg_days": {},
            "marketing_online": {},
            "marketing_print": {},
            "marketing_social": {},
            "analyze_optimize": {},
            "negotiating": {},
            "transaction": {},
        }
    
    def render_html(self) -> str:
        """
        Render the complete HTML report using the unified template system.
        
        All 5 themes use self-contained templates with the same data contract.
        
        Returns:
            Complete HTML string ready for PDF generation
        """
        # Determine theme color
        theme_color = self._get_theme_color()

        # ── Market Trends (optional page) ─────────────────────────────────
        # Only fetch if the page is actually selected — saves 3 API calls for
        # reports that don't include the Market Trends page.
        page_set = list(self.page_set)  # local copy so we can drop the page if data fails

        # Allow callers (e.g. test scripts) to pre-inject data and skip the API call.
        market_trends_data = self.report_data.get("market_trends_data") or None

        if market_trends_data is None and "market_trends" in page_set:
            city     = self.report_data.get("property_city", "")
            zip_code = self.report_data.get("property_zip", "")
            state    = self.report_data.get("property_state", "")
            logger.info("market_trends: auto-fetching for city=%s, zip=%s, state=%s", city, zip_code, state)
            try:
                from worker.compute.market_trends import fetch_and_compute_market_trends
                market_trends_data = fetch_and_compute_market_trends(city, zip_code, state)
                logger.info("market_trends: fetch returned %s", "data" if market_trends_data else "None")
            except Exception as _mt_exc:
                logger.warning("market_trends: fetch FAILED — %s", _mt_exc)

        if market_trends_data is None and "market_trends" in page_set:
            page_set = [p for p in page_set if p != "market_trends"]
            logger.info("market_trends: page REMOVED from page_set (no data returned)")

        # ── Compute Color Roles ───────────────────────────────────────────
        dark_bg = self._THEME_DARK_BG.get(self.theme_name, "#18235c")
        color_roles = compute_color_roles(theme_color, dark_bg)

        # Build the unified context (same structure for all themes)
        context = {
            # Theme configuration
            "theme_number": self.theme_number,
            "theme_name": self.theme_name,
            "assets_base_url": ASSETS_BASE_URL,
            "google_maps_api_key": GOOGLE_MAPS_API_KEY,

            # Color roles (all templates can use any of these)
            **color_roles,
            
            # Page set (may have market_trends removed if data unavailable)
            "page_set": page_set,

            # Market trends data (None when page was dropped)
            "market_trends": market_trends_data,
            
            # Property data
            "property": self._build_property_context(),
            
            # Agent data
            "agent": self._build_agent_context(),
            
            # Comparables
            "comparables": self._build_comparables_context(),
            
            # Statistics (unified format for all themes)
            "stats": self._build_stats_context(),
            
            # Images
            "images": self._build_images_context(),
            
            # Legacy context (for any remaining old templates)
            "neighborhood": self._build_neighborhood_context(),
            "area_analysis": self._build_area_analysis_context(),
            "range_of_sales": self._build_range_of_sales_context(),
            
            # Content sections (use template defaults)
            **self._build_default_content_sections(),
            
            # Optional assets
            "cover_image_url": self.report_data.get("cover_image_url"),
        }

        # ── AI Executive Summary (optional page) ──────────────────────────
        overview_text = self.report_data.get("overview_text")  # allow pre-injection
        if overview_text is None and "overview" in page_set:
            try:
                from worker.ai_overview import generate_overview
                overview_text = generate_overview(
                    property_ctx=context["property"],
                    agent_ctx=context["agent"],
                    stats_ctx=context["stats"],
                    comparables=context["comparables"],
                    market_trends=market_trends_data,
                )
            except Exception as _ov_exc:
                logger.warning("ai_overview: generation failed — %s", _ov_exc)

        if overview_text is None and "overview" in page_set:
            page_set = [p for p in page_set if p != "overview"]
            context["page_set"] = page_set
            logger.info("ai_overview: page removed from page_set (no API key or generation failed)")

        context["overview_text"] = overview_text or ""

        logger.info("Final page_set: %s", page_set)
        logger.info("Context comparables: %d, price_low: %s, price_high: %s",
            len(context.get("comparables", [])),
            context.get("stats", {}).get("price_low"),
            context.get("stats", {}).get("price_high"),
        )

        try:
            template_path = THEME_TEMPLATES.get(self.theme_name, THEME_TEMPLATES["teal"])
            full_template_path = TEMPLATES_DIR / template_path
            logger.warning("[DIAGNOSTIC] Using template: %s, exists: %s", full_template_path, full_template_path.exists())

            # Verify the Jinja2 template contains the photo_url fix
            try:
                tmpl_content = full_template_path.read_text(encoding="utf-8")
                has_photo_fix = "comp.photo_url" in tmpl_content
                has_default_fallback = "default(comp.map_image_url)" in tmpl_content
                logger.warning(
                    "[DIAGNOSTIC] Template has photo_url ref: %s, has default(map) fallback: %s",
                    has_photo_fix, has_default_fallback,
                )
            except Exception as _tmpl_read_exc:
                logger.warning("[DIAGNOSTIC] Could not read template for inspection: %s", _tmpl_read_exc)

            # Log image context summary
            images_ctx = context.get("images", {})
            for key, val in images_ctx.items():
                logger.warning("[DIAGNOSTIC] Image %s: %s", key, str(val)[:100] if val else "NONE/EMPTY")

            template = self.env.get_template(template_path)
            html = template.render(**context)
            
            logger.warning(
                "[DIAGNOSTIC] Rendered %s report: theme=%s (%s), pages=%s, html_len=%d",
                self.report_type, self.theme_name, self.theme_number, page_set, len(html),
            )
            return html
            
        except Exception as e:
            logger.error("Failed to render report with theme %s: %s", self.theme_name, e)
            raise
    
    def render_preview(self, pages: List[str] = None) -> str:
        """
        Render a preview with limited pages.
        
        Args:
            pages: List of page names to include (e.g., ["cover", "property_details"])
                   Defaults to first 3 pages.
        
        Returns:
            HTML string for preview
        """
        if pages is None:
            pages = ["cover", "property", "comparables"]
        
        # Temporarily override page_set
        original_page_set = self.page_set
        self.page_set = pages
        
        try:
            return self.render_html()
        finally:
            self.page_set = original_page_set
    
    def fetch_comparables(self) -> Optional[List[Dict[str, Any]]]:
        """
        Fetch comparables for the property if not already set.
        
        This method checks if comparables are already in report_data.
        If not, it could potentially fetch them from SimplyRETS based on
        the property address (but this is typically done at report creation time).
        
        Returns:
            List of comparable properties or None
        """
        # Check if comparables already exist in report data
        existing = self.report_data.get("comparables")
        if existing and isinstance(existing, list) and len(existing) > 0:
            logger.info(f"Using {len(existing)} existing comparables from report data")
            return existing
        
        # Comparables should be selected in the wizard and stored in the DB
        # If none exist, we can't fetch them here without the subject property coords
        logger.info("No comparables in report data - should be selected during report creation")
        return None

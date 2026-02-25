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
from typing import Dict, Any, List, Optional
from pathlib import Path
from jinja2 import Environment, FileSystemLoader, select_autoescape

logger = logging.getLogger(__name__)

# Template directory - points to property/ for Jinja2 inheritance to work
# This allows templates to use {% extends '_base/base.jinja2' %}
TEMPLATES_DIR = Path(__file__).parent / "templates" / "property"

# Theme template paths (relative to templates/property/)
# v2.0: Templates now use inheritance from _base/base.jinja2
THEME_TEMPLATES = {
    "teal": "teal/teal.jinja2",
    "bold": "bold/bold.jinja2",
    "classic": "classic/classic.jinja2",
    "modern": "modern/modern.jinja2",
    "elegant": "elegant/elegant.jinja2",
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
            "secondary_owner": sitex_data.get("secondary_owner"),
            "county": self.report_data.get("property_county", "") or sitex_data.get("county", ""),
            "apn": self.report_data.get("apn", "") or sitex_data.get("apn", ""),
            
            # Property details (numeric fields default to 0 for safe template arithmetic)
            "bedrooms": sitex_data.get("bedrooms") or 0,
            "bathrooms": sitex_data.get("bathrooms") or 0,
            "sqft": sitex_data.get("sqft") or 0,
            "lot_size": sitex_data.get("lot_size") or 0,
            "year_built": sitex_data.get("year_built") or 0,
            "garage": sitex_data.get("garage"),
            "fireplace": sitex_data.get("fireplace"),
            "pool": sitex_data.get("pool"),
            "total_rooms": sitex_data.get("total_rooms"),
            "num_units": sitex_data.get("num_units"),
            "units": sitex_data.get("num_units"),  # V0 template naming
            "zoning": sitex_data.get("zoning"),
            "property_type": self.report_data.get("property_type", "") or sitex_data.get("property_type", ""),
            "use_code": sitex_data.get("use_code"),
            
            # Tax/Assessment
            "assessed_value": sitex_data.get("assessed_value"),
            "tax_amount": sitex_data.get("tax_amount"),
            "land_value": sitex_data.get("land_value"),
            "improvement_value": sitex_data.get("improvement_value"),
            "percent_improved": sitex_data.get("percent_improved"),
            "improvement_pct": sitex_data.get("percent_improved"),  # V0 template naming
            "tax_status": sitex_data.get("tax_status"),
            "tax_rate_area": sitex_data.get("tax_rate_area"),
            "tax_year": sitex_data.get("tax_year"),
            
            # Legal
            "legal_description": self.report_data.get("legal_description", "") or sitex_data.get("legal_description", ""),
            "mailing_address": sitex_data.get("mailing_address"),
            "census_tract": sitex_data.get("census_tract"),
            "housing_tract": sitex_data.get("housing_tract"),
            "lot_number": sitex_data.get("lot_number"),
            "page_grid": sitex_data.get("page_grid"),
            "partial_bath": sitex_data.get("partial_bath"),
            "notes": sitex_data.get("notes"),
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
                    f"&markers=color:0x1e3a5f%7C{latitude},{longitude}"
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

            comparables.append({
                "address": comp.get("address") or comp.get("full_address", ""),
                "latitude": latitude,
                "longitude": longitude,
                "image_url": image_url,
                "photo_url": image_url,  # V0 template field (prefer property photo)
                "map_image_url": map_image_url,  # Fallback satellite thumbnail
                "price": self._format_price(raw_price),  # Formatted string
                "sale_price": raw_price_num,  # V0 template (raw number for filter/arithmetic)
                "list_price": float(comp.get("list_price") or 0),
                "sold_date": comp.get("sold_date") or comp.get("close_date", ""),  # V0 template
                "days_on_market": comp.get("days_on_market") or 0,
                "distance": distance_formatted,
                "distance_miles": float(distance_raw) if isinstance(distance_raw, (int, float)) else 0,
                "sqft": comp_sqft,
                "price_per_sqft": self._calc_price_per_sqft(raw_price, comp_sqft) or 0,
                "bedrooms": comp.get("bedrooms") or 0,
                "bathrooms": comp.get("bathrooms") or 0,
                "year_built": comp.get("year_built") or 0,
                "lot_size": comp.get("lot_size") or 0,
                "pool": comp.get("pool") if isinstance(comp.get("pool"), bool) else (comp.get("pool", "No") == "Yes"),
            })
        
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
    
    def _build_range_of_sales_context(self) -> Dict[str, Any]:
        """
        Build range of sales context from comparables.
        """
        comparables = self.report_data.get("comparables") or []
        
        if not comparables:
            return {}
        
        # Calculate statistics from comparables
        prices = []
        sqfts = []
        beds = []
        baths = []
        
        for comp in comparables:
            if comp.get("price") or comp.get("close_price"):
                try:
                    prices.append(float(comp.get("price") or comp.get("close_price")))
                except (ValueError, TypeError):
                    pass
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
            raw_price = comp.get("price") or comp.get("close_price") or comp.get("sale_price") or comp.get("list_price")
            if raw_price:
                try:
                    prices.append(float(raw_price))
                except (ValueError, TypeError):
                    pass
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
        
        # Sort comparables by price to get low/medium/high
        sorted_by_price = sorted(
            [c for c in comparables if c.get("price") or c.get("close_price") or c.get("sale_price") or c.get("list_price")],
            key=lambda x: float(x.get("price") or x.get("close_price") or x.get("sale_price") or x.get("list_price") or 0)
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
            raw_price = comp.get("price") or comp.get("close_price") or comp.get("sale_price") or comp.get("list_price")
            sqft = comp.get("sqft") or comp.get("area")
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
    
    def _build_images_context(self) -> Dict[str, Any]:
        """
        Build images context for V0 Teal template.
        
        Includes hero image and aerial map URLs.
        """
        sitex_data = self.report_data.get("sitex_data") or {}
        lat = sitex_data.get("latitude") or sitex_data.get("lat")
        lng = sitex_data.get("longitude") or sitex_data.get("lng")
        
        # Generate aerial map URL if we have coordinates
        aerial_map = None
        if lat and lng and GOOGLE_MAPS_API_KEY:
            aerial_map = (
                f"https://maps.googleapis.com/maps/api/staticmap"
                f"?center={lat},{lng}"
                f"&zoom=15&size=800x600&maptype=roadmap"
                f"&markers=color:0x1e3a5f%7C{lat},{lng}"
                f"&key={GOOGLE_MAPS_API_KEY}"
            )
        
        return {
            "hero": self.report_data.get("cover_image_url"),
            "aerial_map": aerial_map,
        }
    
    def _get_theme_color(self) -> str:
        """
        Get the theme color, preferring branding over report accent_color.
        """
        branding = self.report_data.get("branding") or {}
        return (
            branding.get("primary_color") or 
            self.accent_color or 
            None  # Let template use theme default
        )
    
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
        
        # Build the unified context (same structure for all themes)
        context = {
            # Theme configuration
            "theme_number": self.theme_number,
            "theme_name": self.theme_name,
            "theme_color": theme_color,
            "assets_base_url": ASSETS_BASE_URL,
            "google_maps_api_key": GOOGLE_MAPS_API_KEY,
            
            # Page set
            "page_set": self.page_set,
            
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
        
        try:
            # Simple theme lookup - all templates are self-contained
            template_path = THEME_TEMPLATES.get(self.theme_name, THEME_TEMPLATES["teal"])
            template = self.env.get_template(template_path)
            
            html = template.render(**context)
            
            logger.info(f"Rendered {self.report_type} report: theme={self.theme_name} ({self.theme_number}), template={template_path}")
            return html
            
        except Exception as e:
            logger.error(f"Failed to render report with theme {self.theme_name}: {e}")
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

"""
Property Report Builder
=======================

Renders property reports (seller/buyer) using Jinja2 templates.
Uses the orchestrator template (seller_report.jinja2) which handles:
- Theme selection (1-5)
- Page set configuration (full/compact/custom)
- All page includes

Usage:
    builder = PropertyReportBuilder(report_data)
    html = builder.render_html()

Based on SELLER_REPORT_INTEGRATION.md guide.
"""

import os
import logging
from typing import Dict, Any, List, Optional
from pathlib import Path
from jinja2 import Environment, FileSystemLoader, select_autoescape

logger = logging.getLogger(__name__)

# Template directories
# Old templates: templates/reports/seller (themes 1-3, 5)
# V0 Teal templates: templates/property/teal (theme 4)
TEMPLATES_BASE_DIR = Path(__file__).parent / "templates" / "reports"
TEMPLATES_V0_DIR = Path(__file__).parent / "templates"  # Parent for property/teal includes

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
        self.theme = report_data.get("theme", 1)
        self.accent_color = report_data.get("accent_color")
        self.language = report_data.get("language", "en")
        
        # Use selected_pages if provided, otherwise fall back to page_set or default
        # selected_pages can be:
        #   - A list of page IDs like ["cover", "property_details", "comparables", ...]
        #   - None (use default based on theme: compact for themes 4-5, full for 1-3)
        selected_pages = report_data.get("selected_pages")
        if selected_pages and isinstance(selected_pages, list) and len(selected_pages) > 0:
            self.page_set = selected_pages
        else:
            # Default based on theme: themes 4-5 use compact, themes 1-3 use full
            default_page_set = "compact" if self.theme >= 4 else "full"
            self.page_set = report_data.get("page_set", default_page_set)
        
        # Check if using V0 Teal theme (theme 4)
        self.use_v0_teal = (self.theme == 4)
        
        # Template directory based on theme and report type
        if self.use_v0_teal:
            # V0 Teal templates use the parent templates directory
            # to allow includes like 'property/teal/teal_cover.jinja2'
            template_dir = TEMPLATES_V0_DIR
        else:
            # Original templates in templates/reports/seller
            template_dir = TEMPLATES_BASE_DIR / self.report_type
        
        # Initialize Jinja2 environment
        self.env = Environment(
            loader=FileSystemLoader(str(template_dir)),
            autoescape=select_autoescape(['html', 'xml', 'jinja2']),
            trim_blocks=True,
            lstrip_blocks=True
        )
        
        # Add custom filters
        self.env.filters['format_currency'] = self._format_currency
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
        """
        sitex_data = self.report_data.get("sitex_data") or {}
        
        return {
            # Address (required)
            "street": self.report_data.get("property_address", ""),
            "city": self.report_data.get("property_city", ""),
            "state": self.report_data.get("property_state", ""),
            "zip_code": self.report_data.get("property_zip", ""),
            
            # Location for maps
            "latitude": sitex_data.get("latitude"),
            "longitude": sitex_data.get("longitude"),
            
            # Owner info
            "owner_name": self.report_data.get("owner_name", "") or sitex_data.get("owner_name", ""),
            "secondary_owner": sitex_data.get("secondary_owner"),
            "county": self.report_data.get("property_county", "") or sitex_data.get("county", ""),
            "apn": self.report_data.get("apn", "") or sitex_data.get("apn", ""),
            
            # Property details
            "bedrooms": sitex_data.get("bedrooms"),
            "bathrooms": sitex_data.get("bathrooms"),
            "sqft": sitex_data.get("sqft"),
            "lot_size": sitex_data.get("lot_size"),
            "year_built": sitex_data.get("year_built"),
            "garage": sitex_data.get("garage"),
            "fireplace": sitex_data.get("fireplace"),
            "pool": sitex_data.get("pool"),
            "total_rooms": sitex_data.get("total_rooms"),
            "num_units": sitex_data.get("num_units"),
            "zoning": sitex_data.get("zoning"),
            "property_type": self.report_data.get("property_type", "") or sitex_data.get("property_type", ""),
            "use_code": sitex_data.get("use_code"),
            
            # Tax/Assessment
            "assessed_value": sitex_data.get("assessed_value"),
            "tax_amount": sitex_data.get("tax_amount"),
            "land_value": sitex_data.get("land_value"),
            "improvement_value": sitex_data.get("improvement_value"),
            "percent_improved": sitex_data.get("percent_improved"),
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
        }
    
    def _build_agent_context(self) -> Dict[str, Any]:
        """
        Build agent context matching template requirements.
        """
        agent = self.report_data.get("agent") or {}
        branding = self.report_data.get("branding") or {}
        
        return {
            "name": agent.get("name", ""),
            "title": agent.get("title", "Realtor®"),
            "license_number": agent.get("license_number"),
            "phone": agent.get("phone", ""),
            "email": agent.get("email", ""),
            "company_name": agent.get("company_name") or branding.get("display_name", ""),
            "street": agent.get("company_address") or agent.get("street"),
            "city": agent.get("company_city") or agent.get("city"),
            "state": agent.get("company_state") or agent.get("state"),
            "zip_code": agent.get("company_zip") or agent.get("zip_code"),
            "photo_url": agent.get("photo_url"),
            "logo_url": agent.get("logo_url") or branding.get("logo_url"),
        }
    
    def _build_comparables_context(self) -> List[Dict[str, Any]]:
        """
        Build comparables list matching template requirements.
        
        Each comparable should have:
        - address, latitude, longitude
        - image_url (optional)
        - price, days_on_market, distance
        - sqft, price_per_sqft
        - bedrooms, bathrooms, year_built
        - lot_size, pool
        
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
            distance = comp.get("distance") or comp.get("distance_miles", "")
            if distance and isinstance(distance, (int, float)):
                distance = f"{distance:.1f} mi"
            
            comparables.append({
                "address": comp.get("address") or comp.get("full_address", ""),
                "latitude": latitude,
                "longitude": longitude,
                "image_url": image_url,
                "price": self._format_price(comp.get("price") or comp.get("close_price")),
                "days_on_market": comp.get("days_on_market"),
                "distance": distance,
                "sqft": comp.get("sqft") or comp.get("area"),
                "price_per_sqft": self._calc_price_per_sqft(
                    comp.get("price") or comp.get("close_price"),
                    comp.get("sqft") or comp.get("area")
                ),
                "bedrooms": comp.get("bedrooms"),
                "bathrooms": comp.get("bathrooms"),
                "year_built": comp.get("year_built"),
                "lot_size": comp.get("lot_size"),
                "pool": comp.get("pool", "No"),
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
        Render the complete HTML report using the orchestrator template.
        
        For theme 4 (Teal), uses the V0-generated pixel-perfect templates.
        For other themes, uses the original seller_report.jinja2 orchestrator.
        
        Returns:
            Complete HTML string ready for PDF generation
        """
        # Determine theme color
        theme_color = self._get_theme_color()
        
        # Build the complete context as specified in SELLER_REPORT_INTEGRATION.md
        context = {
            # Theme configuration
            "theme_number": self.theme,
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
            
            # Statistics
            "neighborhood": self._build_neighborhood_context(),
            "area_analysis": self._build_area_analysis_context(),
            "range_of_sales": self._build_range_of_sales_context(),
            
            # Content sections (use template defaults)
            **self._build_default_content_sections(),
            
            # Optional assets
            "cover_image_url": self.report_data.get("cover_image_url"),
        }
        
        try:
            # Select template based on theme
            if self.use_v0_teal:
                # V0 Teal theme uses the new pixel-perfect templates
                template = self.env.get_template("property/teal/teal_report.jinja2")
                logger.info(f"Using V0 Teal template for theme {self.theme}")
            else:
                # Original templates
                template = self.env.get_template(f"{self.report_type}_report.jinja2")
            
            html = template.render(**context)
            
            logger.info(f"Rendered {self.report_type} report: theme={self.theme}, pages={self.page_set}, v0_teal={self.use_v0_teal}")
            return html
            
        except Exception as e:
            logger.error(f"Failed to render report: {e}")
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
            pages = ["cover", "property_details", "comparables"]
        
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

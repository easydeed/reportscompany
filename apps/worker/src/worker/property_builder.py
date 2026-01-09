"""
Property Report Builder
=======================

Renders property reports (seller/buyer) using Jinja2 templates.
Combines cover page + property details + comparables into a full HTML document.

Usage:
    builder = PropertyReportBuilder(report_data)
    html = builder.render_html()
"""

import os
import logging
from typing import Dict, Any, List, Optional
from pathlib import Path
from jinja2 import Environment, FileSystemLoader, select_autoescape

from .vendors.simplyrets import fetch_properties

logger = logging.getLogger(__name__)

# Template directory
TEMPLATES_DIR = Path(__file__).parent / "templates" / "property"


class PropertyReportBuilder:
    """
    Builds HTML property reports from database report data.
    
    The report_data should come from the database with joins for:
    - user (for agent info)
    - account (for branding)
    - affiliate_branding (if applicable)
    
    Expected report_data structure:
    {
        "id": "uuid",
        "account_id": "uuid",
        "report_type": "seller" | "buyer",
        "theme": 1-5,
        "accent_color": "#2563eb",
        "language": "en" | "es",
        
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
        
        # SiteX data (full property details)
        "sitex_data": { ... },
        
        # Comparables (pre-fetched or will be fetched)
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
            "company_address": "456 Broker St",
            "company_city": "Los Angeles",
            "company_state": "CA",
            "company_zip": "90210",
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
        self.accent_color = report_data.get("accent_color", "#0d294b")
        self.language = report_data.get("language", "en")
        
        # Initialize Jinja2 environment
        self.env = Environment(
            loader=FileSystemLoader(str(TEMPLATES_DIR)),
            autoescape=select_autoescape(['html', 'xml', 'jinja2']),
            trim_blocks=True,
            lstrip_blocks=True
        )
        
        # Add custom filters
        self.env.filters['format_currency'] = self._format_currency
        self.env.filters['format_number'] = self._format_number
        
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
    
    def fetch_comparables(self) -> List[Dict[str, Any]]:
        """
        Fetch comparable properties from SimplyRETS if not already set.
        
        Searches for similar properties based on:
        - Location (city/zip)
        - Property type
        - Price range (+/- 20%)
        - Bed/bath count (+/- 1)
        
        Returns:
            List of comparable property dictionaries
        """
        # Return existing comparables if already fetched
        existing = self.report_data.get("comparables")
        if existing:
            logger.info(f"Using {len(existing)} pre-fetched comparables")
            return existing
        
        # Extract search parameters from SiteX data or report data
        sitex_data = self.report_data.get("sitex_data") or {}
        
        city = self.report_data.get("property_city", "")
        state = self.report_data.get("property_state", "CA")
        zip_code = self.report_data.get("property_zip", "")
        
        # Get property characteristics for matching
        bedrooms = sitex_data.get("bedrooms") or 3
        bathrooms = sitex_data.get("bathrooms") or 2
        sqft = sitex_data.get("sqft") or 1500
        assessed_value = sitex_data.get("assessed_value")
        
        # Build SimplyRETS query for comparables
        # Focus on recent closed sales for accurate comps
        from datetime import datetime, timedelta
        end_date = datetime.utcnow().date()
        start_date = end_date - timedelta(days=180)  # 6 months of sales
        
        params = {
            "q": city or zip_code,
            "status": "Closed",
            "mindate": start_date.isoformat(),
            "maxdate": end_date.isoformat(),
            "sort": "-closeDate",
        }
        
        # Add bedroom filter (+/- 1)
        if bedrooms:
            params["minbeds"] = max(1, bedrooms - 1)
            params["maxbeds"] = bedrooms + 1
        
        # Add bathroom filter (+/- 1)
        if bathrooms:
            params["minbaths"] = max(1, int(bathrooms) - 1)
            params["maxbaths"] = int(bathrooms) + 2
        
        # Add sqft filter (+/- 30%)
        if sqft:
            params["minarea"] = int(sqft * 0.7)
            params["maxarea"] = int(sqft * 1.3)
        
        # Add price filter if we have assessed value (+/- 25%)
        if assessed_value:
            # Use assessed value as rough estimate for price range
            params["minprice"] = int(assessed_value * 0.75)
            params["maxprice"] = int(assessed_value * 1.5)
        
        try:
            logger.info(f"Fetching comparables: {params}")
            raw_comps = fetch_properties(params, limit=20)
            
            # Extract relevant fields for comparables
            comparables = []
            for prop in raw_comps[:10]:  # Limit to 10 comps
                address = prop.get("address", {})
                mls = prop.get("mls", {})
                property_info = prop.get("property", {})
                
                comp = {
                    "address": address.get("full", ""),
                    "city": address.get("city", ""),
                    "state": address.get("state", ""),
                    "zip": address.get("postalCode", ""),
                    "price": prop.get("listPrice") or prop.get("closePrice"),
                    "close_price": prop.get("closePrice"),
                    "close_date": prop.get("closeDate"),
                    "bedrooms": property_info.get("bedrooms"),
                    "bathrooms": property_info.get("bathrooms"),
                    "sqft": property_info.get("area"),
                    "lot_size": property_info.get("lotSize"),
                    "year_built": property_info.get("yearBuilt"),
                    "days_on_market": mls.get("daysOnMarket"),
                    "mls_id": mls.get("listingId"),
                    "photos": prop.get("photos", [])[:3],  # First 3 photos
                }
                comparables.append(comp)
            
            logger.info(f"Found {len(comparables)} comparable properties")
            return comparables
            
        except Exception as e:
            logger.error(f"Failed to fetch comparables: {e}")
            return []
    
    def _build_property_context(self) -> Dict[str, Any]:
        """
        Build property context for templates from report data and SiteX data.
        """
        sitex_data = self.report_data.get("sitex_data") or {}
        
        return {
            # Address
            "street": self.report_data.get("property_address", ""),
            "address": self.report_data.get("property_address", ""),
            "city": self.report_data.get("property_city", ""),
            "state": self.report_data.get("property_state", ""),
            "zip": self.report_data.get("property_zip", ""),
            "county": self.report_data.get("property_county", "") or sitex_data.get("county", ""),
            
            # Property identifiers
            "apn": self.report_data.get("apn", "") or sitex_data.get("apn", ""),
            "owner_name": self.report_data.get("owner_name", "") or sitex_data.get("owner_name", ""),
            "secondary_owner": sitex_data.get("secondary_owner"),
            "legal_description": self.report_data.get("legal_description", "") or sitex_data.get("legal_description", ""),
            
            # Property characteristics
            "bedrooms": sitex_data.get("bedrooms"),
            "bathrooms": sitex_data.get("bathrooms"),
            "sqft": sitex_data.get("sqft"),
            "lot_size": sitex_data.get("lot_size"),
            "year_built": sitex_data.get("year_built"),
            "property_type": self.report_data.get("property_type", "") or sitex_data.get("property_type", ""),
            
            # Tax/Assessment
            "assessed_value": sitex_data.get("assessed_value"),
            "tax_amount": sitex_data.get("tax_amount"),
            "land_value": sitex_data.get("land_value"),
            "improvement_value": sitex_data.get("improvement_value"),
            "tax_year": sitex_data.get("tax_year"),
            
            # Additional fields from SiteX
            "garage": sitex_data.get("garage"),
            "fireplace": sitex_data.get("fireplace"),
            "pool": sitex_data.get("pool"),
            "total_rooms": sitex_data.get("total_rooms"),
            "num_units": sitex_data.get("num_units"),
            "zoning": sitex_data.get("zoning"),
            "use_code": sitex_data.get("use_code"),
            "census_tract": sitex_data.get("census_tract"),
            "housing_tract": sitex_data.get("housing_tract"),
            "lot_number": sitex_data.get("lot_number"),
            "page_grid": sitex_data.get("page_grid"),
            "mailing_address": sitex_data.get("mailing_address"),
            "latitude": sitex_data.get("latitude"),
            "longitude": sitex_data.get("longitude"),
        }
    
    def _build_agent_context(self) -> Dict[str, Any]:
        """
        Build agent context from report data.
        """
        agent = self.report_data.get("agent") or {}
        branding = self.report_data.get("branding") or {}
        
        return {
            "name": agent.get("name", ""),
            "email": agent.get("email", ""),
            "phone": agent.get("phone", ""),
            "photo_url": agent.get("photo_url"),
            "title": agent.get("title", "Real Estate Professional"),
            "license_number": agent.get("license_number"),
            "company_name": agent.get("company_name") or branding.get("display_name", ""),
            "company_address": agent.get("company_address"),
            "company_city": agent.get("company_city"),
            "company_state": agent.get("company_state"),
            "company_zip": agent.get("company_zip"),
            "logo_url": agent.get("logo_url") or branding.get("logo_url"),
        }
    
    def _get_theme_color(self) -> str:
        """
        Get the theme color, preferring branding over report accent_color.
        """
        branding = self.report_data.get("branding") or {}
        return (
            branding.get("primary_color") or 
            self.accent_color or 
            "#0d294b"
        )
    
    def render_html(self) -> str:
        """
        Render the complete HTML report.
        
        Combines:
        - Cover page
        - Property details page
        - Comparables pages (if available)
        
        Returns:
            Complete HTML string ready for PDF generation
        """
        # Build template contexts
        property_ctx = self._build_property_context()
        agent_ctx = self._build_agent_context()
        theme_color = self._get_theme_color()
        
        # Fetch comparables if not already set
        comparables = self.fetch_comparables()
        
        # Base template selection
        base_template = f"{self.report_type}_base.jinja2"
        
        # Build template context
        context = {
            "property": property_ctx,
            "agent": agent_ctx,
            "theme_color": theme_color,
            "comparables": comparables,
            "report_type": self.report_type,
            "language": self.language,
            "cover_image_url": self.report_data.get("cover_image_url"),
        }
        
        # Render each page
        pages_html = []
        
        # 1. Cover page
        try:
            cover_template = self.env.get_template(f"{self.report_type}_cover.jinja2")
            cover_html = cover_template.render(**context)
            pages_html.append(cover_html)
            logger.debug("Rendered cover page")
        except Exception as e:
            logger.error(f"Failed to render cover page: {e}")
        
        # 2. Property details page
        try:
            details_template = self.env.get_template(f"{self.report_type}_property_details.jinja2")
            details_html = details_template.render(**context)
            pages_html.append(details_html)
            logger.debug("Rendered property details page")
        except Exception as e:
            logger.error(f"Failed to render property details page: {e}")
        
        # 3. Comparables page (if we have comps and template exists)
        if comparables:
            try:
                comps_template = self.env.get_template(f"{self.report_type}_comparables.jinja2")
                comps_html = comps_template.render(**context)
                pages_html.append(comps_html)
                logger.debug(f"Rendered comparables page with {len(comparables)} comps")
            except Exception as e:
                # Template might not exist yet
                logger.warning(f"Comparables template not available: {e}")
        
        # Combine all pages
        # Each template extends the base and renders as a complete HTML doc
        # For PDF generation, we need them as separate pages
        
        if len(pages_html) == 1:
            return pages_html[0]
        
        # If multiple pages, we need to combine them properly
        # Extract body content from each and wrap in a single document
        return self._combine_pages(pages_html, context)
    
    def _combine_pages(self, pages_html: List[str], context: Dict[str, Any]) -> str:
        """
        Combine multiple page HTMLs into a single document.
        
        For PDF generation, we need page breaks between sections.
        This extracts the body content from each rendered template
        and combines them with proper page break styling.
        """
        # For now, simply concatenate the pages
        # The templates use <page> elements with page-break-after: always
        # PDFShift handles this correctly
        
        # Render base template with all pages as content
        try:
            base_template = self.env.get_template(f"{self.report_type}_base.jinja2")
            
            # Extract body content from each page (between <body> and </body>)
            body_contents = []
            for html in pages_html:
                import re
                match = re.search(r'<body[^>]*>(.*?)</body>', html, re.DOTALL)
                if match:
                    body_contents.append(match.group(1))
                else:
                    body_contents.append(html)
            
            # Create combined content block
            combined_content = "\n<!-- PAGE BREAK -->\n".join(body_contents)
            
            # Render the base template with combined content
            # Override the content block
            context['combined_content'] = combined_content
            
            # For now, just return the first page's full HTML with all content
            # This is because each template extends base and is complete
            # A better solution would be a master template that includes all pages
            
            return pages_html[0].replace(
                '</body>',
                f'\n{chr(10).join(body_contents[1:])}\n</body>'
            )
            
        except Exception as e:
            logger.error(f"Failed to combine pages: {e}")
            return pages_html[0] if pages_html else ""
    
    def render_page(self, page_name: str) -> str:
        """
        Render a single page by name.
        
        Args:
            page_name: Template name without extension (e.g., "seller_cover")
            
        Returns:
            Rendered HTML string
        """
        context = {
            "property": self._build_property_context(),
            "agent": self._build_agent_context(),
            "theme_color": self._get_theme_color(),
            "comparables": self.report_data.get("comparables") or [],
            "report_type": self.report_type,
            "language": self.language,
            "cover_image_url": self.report_data.get("cover_image_url"),
        }
        
        template = self.env.get_template(f"{page_name}.jinja2")
        return template.render(**context)


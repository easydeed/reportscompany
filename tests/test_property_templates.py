# tests/test_property_templates.py
"""
Unit tests for property report templates.
Ensures all 5 themes render correctly with various data scenarios.
"""

import pytest
from pathlib import Path
from jinja2 import Environment, FileSystemLoader, UndefinedError

# Adjust this path to match your project structure
TEMPLATES_DIR = Path(__file__).parent.parent / "apps/worker/src/worker/templates"

THEME_TEMPLATES = {
    "teal": "property/teal/teal_report.jinja2",
    "bold": "property/bold/bold_report.jinja2",
    "classic": "property/classic/classic_report.jinja2",
    "modern": "property/modern/modern_report.jinja2",
    "elegant": "property/elegant/elegant_report.jinja2",
}


# ============================================================================
# Custom Filters (must match production)
# ============================================================================

def format_currency(value):
    """Format as $XXX,XXX"""
    if value is None:
        return "-"
    try:
        return f"${int(value):,}"
    except (ValueError, TypeError):
        return "-"


def format_currency_short(value):
    """Format as $XXXk or $X.Xm"""
    if value is None:
        return "-"
    try:
        val = float(value)
        if val >= 1_000_000:
            return f"${val/1_000_000:.1f}m"
        elif val >= 1_000:
            return f"${int(val/1_000)}k"
        return f"${int(val)}"
    except (ValueError, TypeError):
        return "-"


def format_number(value):
    """Format with commas: 1,234"""
    if value is None:
        return "-"
    try:
        return f"{int(value):,}"
    except (ValueError, TypeError):
        return "-"


# ============================================================================
# Test Fixtures
# ============================================================================

@pytest.fixture
def jinja_env():
    """Create Jinja2 environment with custom filters."""
    env = Environment(
        loader=FileSystemLoader(str(TEMPLATES_DIR)),
        autoescape=True
    )
    env.filters['format_currency'] = format_currency
    env.filters['format_currency_short'] = format_currency_short
    env.filters['format_number'] = format_number
    return env


@pytest.fixture
def minimal_context():
    """Minimal context - tests default filter handling."""
    return {
        "property": {
            "street_address": "123 Test St",
            "city": "Test City",
            "state": "CA",
            "zip_code": "90210",
            "full_address": "123 Test St, Test City, CA 90210",
        },
        "agent": {
            "name": "Test Agent",
        },
        "images": {},
        "comparables": [],
        "stats": {
            "total_comps": 0,
            "avg_sqft": 0,
            "avg_beds": 0,
            "avg_baths": 0,
            "price_low": 0,
            "price_high": 0,
            "piq": {},
            "low": {},
            "medium": {},
            "high": {},
        },
    }


@pytest.fixture
def full_context():
    """Complete context with all fields populated."""
    return {
        "property": {
            "street_address": "1358 5th Street",
            "city": "La Verne",
            "state": "CA",
            "zip_code": "91750",
            "full_address": "1358 5th St, La Verne, CA 91750",
            "owner_name": "HERNANDEZ GERARDO J",
            "secondary_owner": "MENDOZA YESSICA S",
            "mailing_address": "1358 5th St, La Verne, CA 91750",
            "apn": "8381-021-001",
            "county": "LOS ANGELES",
            "census_tract": "4089.00",
            "legal_description": "LOT 44 TR#6654",
            "bedrooms": 2,
            "bathrooms": 1.0,
            "sqft": 786,
            "lot_size": 6155,
            "year_built": 1949,
            "property_type": "Single Family Residential",
            "zoning": "LVPR4.5D*",
            "pool": "None",
            "garage": "1",
            "fireplace": "No",
            "assessed_value": 428248,
            "land_value": 337378,
            "improvement_value": 90870,
            "tax_amount": 5198,
            "tax_year": 2024,
        },
        "agent": {
            "name": "Zoe Noelle",
            "title": "Real Estate Specialist",
            "license": "DRE #01234567",
            "phone": "(213) 309-7286",
            "email": "zoe@realty.com",
            "address": "123 Main St, Los Angeles, CA",
            "photo_url": None,
            "company_name": "TrendyReports",
            "company_short": "TR",
            "company_tagline": "Your Property Partner",
        },
        "images": {
            "hero": None,
            "aerial_map": None,
        },
        "comparables": [
            {
                "address": "1889 Bonita Ave, La Verne",
                "sale_price": 631500,
                "sold_date": "5/10/23",
                "sqft": 940,
                "bedrooms": 2,
                "bathrooms": 1,
                "year_built": 1953,
                "lot_size": 7446,
                "price_per_sqft": 671,
                "distance_miles": 0.58,
                "pool": False,
                "map_image_url": None,
            },
            {
                "address": "1507 2nd St, La Verne",
                "sale_price": 635000,
                "sold_date": "3/15/23",
                "sqft": 912,
                "bedrooms": 3,
                "bathrooms": 1,
                "year_built": 1952,
                "lot_size": 6261,
                "price_per_sqft": 696,
                "distance_miles": 0.54,
                "pool": False,
                "map_image_url": None,
            },
            {
                "address": "1845 Walnut St, La Verne",
                "sale_price": 470000,
                "sold_date": "4/25/22",
                "sqft": 770,
                "bedrooms": 3,
                "bathrooms": 1,
                "year_built": 1910,
                "lot_size": 4917,
                "price_per_sqft": 610,
                "distance_miles": 0.24,
                "pool": False,
                "map_image_url": None,
            },
            {
                "address": "1848 1st St, La Verne",
                "sale_price": 590000,
                "sold_date": "4/8/22",
                "sqft": 698,
                "bedrooms": 1,
                "bathrooms": 1,
                "year_built": 1950,
                "lot_size": 5500,
                "price_per_sqft": 845,
                "distance_miles": 0.30,
                "pool": True,
                "map_image_url": None,
            },
        ],
        "stats": {
            "total_comps": 4,
            "avg_sqft": 830,
            "avg_beds": 2.25,
            "avg_baths": 1.0,
            "price_low": 470000,
            "price_high": 635000,
            "piq": {
                "distance": "0",
                "sqft": 786,
                "price_per_sqft": 469,
                "year_built": 1949,
                "lot_size": 6155,
                "bedrooms": 2,
                "bathrooms": 1,
                "price": 369000,
                "stories": 1,
                "pools": 0,
            },
            "low": {
                "distance": "0.24",
                "sqft": 698,
                "price_per_sqft": 610,
                "year_built": 1910,
                "lot_size": 4917,
                "bedrooms": 1,
                "bathrooms": 1,
                "price": 470000,
                "stories": 1,
                "pools": 0,
            },
            "medium": {
                "distance": "0.54",
                "sqft": 912,
                "price_per_sqft": 696,
                "year_built": 1952,
                "lot_size": 6261,
                "bedrooms": 3,
                "bathrooms": 1,
                "price": 610750,
                "stories": 1,
                "pools": 0,
            },
            "high": {
                "distance": "0.58",
                "sqft": 940,
                "price_per_sqft": 845,
                "year_built": 1953,
                "lot_size": 7446,
                "bedrooms": 3,
                "bathrooms": 1,
                "price": 635000,
                "stories": 1,
                "pools": 1,
            },
        },
    }


# ============================================================================
# Template Existence Tests
# ============================================================================

class TestTemplateExistence:
    """Verify all theme templates exist."""

    @pytest.mark.parametrize("theme,path", THEME_TEMPLATES.items())
    def test_template_file_exists(self, theme, path):
        """Each theme template file should exist."""
        full_path = TEMPLATES_DIR / path
        assert full_path.exists(), f"Missing template for {theme}: {full_path}"

    def test_all_themes_defined(self):
        """Ensure we have all 5 themes."""
        expected_themes = {"teal", "bold", "classic", "modern", "elegant"}
        assert set(THEME_TEMPLATES.keys()) == expected_themes


# ============================================================================
# Template Rendering Tests
# ============================================================================

class TestTemplateRendering:
    """Test that templates render without errors."""

    @pytest.mark.parametrize("theme", THEME_TEMPLATES.keys())
    def test_renders_with_minimal_context(self, jinja_env, minimal_context, theme):
        """Templates should render with minimal data (tests default filters)."""
        template = jinja_env.get_template(THEME_TEMPLATES[theme])
        html = template.render(**minimal_context)
        
        assert html is not None
        assert len(html) > 1000, f"{theme} template output suspiciously short"

    @pytest.mark.parametrize("theme", THEME_TEMPLATES.keys())
    def test_renders_with_full_context(self, jinja_env, full_context, theme):
        """Templates should render with complete data."""
        template = jinja_env.get_template(THEME_TEMPLATES[theme])
        html = template.render(**full_context)
        
        assert html is not None
        assert len(html) > 5000, f"{theme} template output suspiciously short"


# ============================================================================
# HTML Structure Tests
# ============================================================================

class TestHTMLStructure:
    """Verify generated HTML has correct structure."""

    @pytest.mark.parametrize("theme", THEME_TEMPLATES.keys())
    def test_valid_html_structure(self, jinja_env, full_context, theme):
        """Generated HTML should have proper structure."""
        template = jinja_env.get_template(THEME_TEMPLATES[theme])
        html = template.render(**full_context)
        
        assert '<html' in html, f"{theme}: Missing <html> tag"
        assert '</html>' in html, f"{theme}: Missing </html> tag"
        assert '<head>' in html, f"{theme}: Missing <head> tag"
        assert '<body>' in html, f"{theme}: Missing <body> tag"

    @pytest.mark.parametrize("theme", THEME_TEMPLATES.keys())
    def test_no_unrendered_jinja(self, jinja_env, full_context, theme):
        """No Jinja2 syntax should remain in output."""
        template = jinja_env.get_template(THEME_TEMPLATES[theme])
        html = template.render(**full_context)
        
        assert '{{' not in html, f"{theme}: Unrendered Jinja2 variable"
        assert '{%' not in html, f"{theme}: Unrendered Jinja2 block"

    @pytest.mark.parametrize("theme", THEME_TEMPLATES.keys())
    def test_no_undefined_values(self, jinja_env, full_context, theme):
        """No 'undefined' or 'None' text should appear in output."""
        template = jinja_env.get_template(THEME_TEMPLATES[theme])
        html = template.render(**full_context)
        
        # These patterns indicate missing default filters
        assert 'undefined' not in html.lower(), f"{theme}: 'undefined' in output"
        # Note: 'None' might legitimately appear in addresses, so we check specific patterns
        assert '>None<' not in html, f"{theme}: Bare 'None' value in output"

    @pytest.mark.parametrize("theme", THEME_TEMPLATES.keys())
    def test_has_seven_pages(self, jinja_env, full_context, theme):
        """Each template should generate 7 pages."""
        template = jinja_env.get_template(THEME_TEMPLATES[theme])
        html = template.render(**full_context)
        
        # Count page sections (all templates use class="page")
        page_count = html.count('class="page ')
        if page_count == 0:
            page_count = html.count("class='page ")
        if page_count == 0:
            page_count = html.count('class="page"')
        
        assert page_count >= 7, f"{theme}: Expected 7 pages, found {page_count}"


# ============================================================================
# Content Tests
# ============================================================================

class TestContentRendering:
    """Verify specific content renders correctly."""

    @pytest.mark.parametrize("theme", THEME_TEMPLATES.keys())
    def test_property_address_rendered(self, jinja_env, full_context, theme):
        """Property address should appear in output."""
        template = jinja_env.get_template(THEME_TEMPLATES[theme])
        html = template.render(**full_context)
        
        assert "1358 5th Street" in html or "1358 5th St" in html, \
            f"{theme}: Property address not rendered"

    @pytest.mark.parametrize("theme", THEME_TEMPLATES.keys())
    def test_agent_name_rendered(self, jinja_env, full_context, theme):
        """Agent name should appear in output."""
        template = jinja_env.get_template(THEME_TEMPLATES[theme])
        html = template.render(**full_context)
        
        assert "Zoe Noelle" in html, f"{theme}: Agent name not rendered"

    @pytest.mark.parametrize("theme", THEME_TEMPLATES.keys())
    def test_comparables_rendered(self, jinja_env, full_context, theme):
        """Comparable properties should appear in output."""
        template = jinja_env.get_template(THEME_TEMPLATES[theme])
        html = template.render(**full_context)
        
        # Check at least one comparable address appears
        assert "Bonita Ave" in html or "1889" in html, \
            f"{theme}: Comparables not rendered"

    @pytest.mark.parametrize("theme", THEME_TEMPLATES.keys())
    def test_currency_formatting(self, jinja_env, full_context, theme):
        """Currency values should be formatted correctly."""
        template = jinja_env.get_template(THEME_TEMPLATES[theme])
        html = template.render(**full_context)
        
        # Check for formatted currency (should have $ and comma)
        assert "$631,500" in html or "$631500" in html or "$632k" in html, \
            f"{theme}: Currency not formatted"


# ============================================================================
# Print CSS Tests
# ============================================================================

class TestPrintCSS:
    """Verify print-related CSS is present."""

    @pytest.mark.parametrize("theme", THEME_TEMPLATES.keys())
    def test_has_page_size_rule(self, jinja_env, full_context, theme):
        """Template should define page size for printing."""
        template = jinja_env.get_template(THEME_TEMPLATES[theme])
        html = template.render(**full_context)
        
        assert '@page' in html, f"{theme}: Missing @page CSS rule"

    @pytest.mark.parametrize("theme", THEME_TEMPLATES.keys())
    def test_has_print_media_query(self, jinja_env, full_context, theme):
        """Template should have print media query."""
        template = jinja_env.get_template(THEME_TEMPLATES[theme])
        html = template.render(**full_context)
        
        assert '@media print' in html, f"{theme}: Missing @media print rule"

    @pytest.mark.parametrize("theme", THEME_TEMPLATES.keys())
    def test_has_page_break_rules(self, jinja_env, full_context, theme):
        """Template should control page breaks."""
        template = jinja_env.get_template(THEME_TEMPLATES[theme])
        html = template.render(**full_context)
        
        has_break_after = 'page-break-after' in html
        has_break_inside = 'page-break-inside' in html
        has_break_before = 'page-break-before' in html
        
        assert has_break_after or has_break_inside or has_break_before, \
            f"{theme}: Missing page-break CSS rules"


# ============================================================================
# Edge Case Tests
# ============================================================================

class TestEdgeCases:
    """Test edge cases and error handling."""

    @pytest.mark.parametrize("theme", THEME_TEMPLATES.keys())
    def test_empty_comparables(self, jinja_env, minimal_context, theme):
        """Templates should handle empty comparables list."""
        template = jinja_env.get_template(THEME_TEMPLATES[theme])
        html = template.render(**minimal_context)
        
        # Should not crash, should produce valid HTML
        assert '<html' in html
        assert '</html>' in html

    @pytest.mark.parametrize("theme", THEME_TEMPLATES.keys())
    def test_missing_optional_fields(self, jinja_env, theme):
        """Templates should handle missing optional fields gracefully."""
        context = {
            "property": {
                "street_address": "Test St",
                "city": "City",
                "state": "ST",
                "zip_code": "00000",
                "full_address": "Test St, City, ST 00000",
                # All other fields missing
            },
            "agent": {"name": "Agent"},
            "images": {},
            "comparables": [],
            "stats": {
                "total_comps": 0,
                "avg_sqft": 0,
                "avg_beds": 0,
                "avg_baths": 0,
                "price_low": 0,
                "price_high": 0,
                "piq": {},
                "low": {},
                "medium": {},
                "high": {},
            },
        }
        
        template = jinja_env.get_template(THEME_TEMPLATES[theme])
        # Should not raise UndefinedError
        html = template.render(**context)
        assert '<html' in html

    @pytest.mark.parametrize("theme", THEME_TEMPLATES.keys())
    def test_none_values_handled(self, jinja_env, theme):
        """Templates should handle None values without crashing."""
        context = {
            "property": {
                "street_address": "Test St",
                "city": "City",
                "state": "ST",
                "zip_code": "00000",
                "full_address": "Test St, City, ST 00000",
                "owner_name": None,
                "bedrooms": None,
                "sqft": None,
                "assessed_value": None,
            },
            "agent": {
                "name": "Agent",
                "phone": None,
                "email": None,
            },
            "images": {
                "hero": None,
                "aerial_map": None,
            },
            "comparables": [],
            "stats": {
                "total_comps": 0,
                "avg_sqft": None,
                "avg_beds": None,
                "avg_baths": None,
                "price_low": None,
                "price_high": None,
                "piq": {},
                "low": {},
                "medium": {},
                "high": {},
            },
        }
        
        template = jinja_env.get_template(THEME_TEMPLATES[theme])
        html = template.render(**context)
        
        # Should render with "-" placeholders, not "None"
        assert '>None<' not in html


# ============================================================================
# Run Tests
# ============================================================================

if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])

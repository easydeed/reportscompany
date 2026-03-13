# tests/test_market_templates.py
"""
Unit tests for market report templates.
Ensures all 8 report types render correctly with brand colors.
"""

import sys
from pathlib import Path

import pytest

# Ensure worker package is importable
WORKER_SRC = Path(__file__).parent.parent / "apps" / "worker" / "src"
sys.path.insert(0, str(WORKER_SRC))

from worker.market_builder import (
    MarketReportBuilder,
    ALL_REPORT_TYPES,
    TEMPLATES_DIR,
)

# ============================================================================
# Test Fixtures
# ============================================================================

@pytest.fixture
def minimal_data():
    """Minimal report data — tests graceful handling of missing fields."""
    return {
        "report_type": "market_snapshot",
        "city": "Test City",
        "lookback_days": 30,
        "listings": [],
        "metrics": {},
        "counts": {},
        "branding": {"agent_name": "Test Agent"},
    }


@pytest.fixture
def full_data():
    """Complete report data with all fields populated."""
    return {
        "report_type": "new_listings_gallery",
        "city": "Irvine",
        "lookback_days": 30,
        "filters_label": "2+ beds, SFR, under $1.5M",
        "listings": [
            {
                "street_address": "123 Main St",
                "city": "Irvine",
                "list_price": 950000,
                "close_price": 935000,
                "bedrooms": 4,
                "bathrooms": 3,
                "sqft": 2200,
                "status": "Active",
                "days_on_market": 8,
                "photo_url": "https://example.com/photo1.jpg",
            },
            {
                "street_address": "456 Oak Ave",
                "city": "Irvine",
                "list_price": 1125000,
                "close_price": 1100000,
                "bedrooms": 3,
                "bathrooms": 2.5,
                "sqft": 1850,
                "status": "Active",
                "days_on_market": 14,
                "photo_url": "https://example.com/photo2.jpg",
            },
            {
                "street_address": "789 Elm Dr",
                "city": "Irvine",
                "list_price": 780000,
                "close_price": 775000,
                "bedrooms": 3,
                "bathrooms": 2,
                "sqft": 1600,
                "status": "Pending",
                "days_on_market": 5,
                "photo_url": None,
            },
            {
                "street_address": "101 Birch Ln",
                "city": "Irvine",
                "list_price": 1350000,
                "close_price": 1320000,
                "bedrooms": 5,
                "bathrooms": 4,
                "sqft": 3100,
                "status": "Closed",
                "days_on_market": 22,
                "photo_url": "https://example.com/photo4.jpg",
            },
        ],
        "metrics": {
            "median_list_price": 922500,
            "median_close_price": 907500,
            "avg_dom": 12,
            "months_of_inventory": 2.1,
            "price_per_sqft": 520,
            "list_to_sale_ratio": 0.982,
            "new_listings_count": 42,
        },
        "counts": {"Active": 67, "Pending": 12, "Closed": 38},
        "total_listings": 117,
        "branding": {
            "agent_name": "Jennifer Martinez",
            "agent_title": "Luxury Home Specialist",
            "agent_phone": "(949) 555-4567",
            "agent_email": "jennifer@luxuryestates.com",
            "agent_photo_url": "https://example.com/agent.jpg",
            "company_name": "Luxury Estates Realty",
            "logo_url": "https://example.com/logo.png",
            "primary_color": "#1B365D",
            "accent_color": None,
        },
        "ai_insights": "The Irvine market showed balanced activity this period.",
        "price_bands": [],
    }


# ============================================================================
# Template Existence Tests
# ============================================================================

class TestTemplateExistence:
    """Verify template files exist."""

    def test_template_file_exists(self):
        assert (TEMPLATES_DIR / "market.jinja2").exists()

    def test_base_template_exists(self):
        assert (TEMPLATES_DIR / "_base" / "base.jinja2").exists()

    def test_macros_file_exists(self):
        assert (TEMPLATES_DIR / "_base" / "macros.jinja2").exists()


# ============================================================================
# Template Rendering Tests — 8 report types
# ============================================================================

class TestTemplateRendering:
    """Test that every report_type renders without error."""

    @pytest.mark.parametrize("report_type", ALL_REPORT_TYPES)
    def test_renders_with_full_data(self, full_data, report_type):
        full_data["report_type"] = report_type
        builder = MarketReportBuilder(full_data)
        html = builder.render_html()

        assert html is not None
        assert len(html) > 500, f"{report_type}: output suspiciously short ({len(html)} chars)"

    @pytest.mark.parametrize("report_type", ALL_REPORT_TYPES)
    def test_renders_with_minimal_data(self, minimal_data, report_type):
        minimal_data["report_type"] = report_type
        builder = MarketReportBuilder(minimal_data)
        html = builder.render_html()

        assert html is not None
        assert len(html) > 500


# ============================================================================
# HTML Structure Tests
# ============================================================================

class TestHTMLStructure:
    """Verify generated HTML has correct structure."""

    def test_valid_html_structure(self, full_data):
        builder = MarketReportBuilder(full_data)
        html = builder.render_html()

        assert "<html" in html, "Missing <html> tag"
        assert "</html>" in html, "Missing </html> tag"
        assert "<head>" in html, "Missing <head> tag"
        assert "<body>" in html, "Missing <body> tag"

    @pytest.mark.parametrize("report_type", ALL_REPORT_TYPES)
    def test_no_unrendered_jinja(self, full_data, report_type):
        full_data["report_type"] = report_type
        builder = MarketReportBuilder(full_data)
        html = builder.render_html()

        assert "{{" not in html, f"{report_type}: Unrendered Jinja2 variable"
        assert "{%" not in html, f"{report_type}: Unrendered Jinja2 block"

    @pytest.mark.parametrize("report_type", ALL_REPORT_TYPES)
    def test_no_undefined_values(self, full_data, report_type):
        full_data["report_type"] = report_type
        builder = MarketReportBuilder(full_data)
        html = builder.render_html()

        assert "undefined" not in html.lower(), f"{report_type}: 'undefined' in output"
        assert ">None<" not in html, f"{report_type}: Bare 'None' value in output"


# ============================================================================
# Content Rendering Tests
# ============================================================================

class TestContentRendering:
    """Verify specific content renders correctly."""

    def test_city_name_rendered(self, full_data):
        builder = MarketReportBuilder(full_data)
        html = builder.render_html()
        assert "Irvine" in html, "City name not rendered"

    def test_agent_name_rendered(self, full_data):
        builder = MarketReportBuilder(full_data)
        html = builder.render_html()
        assert "Jennifer Martinez" in html, "Agent name not rendered"

    def test_listing_prices_rendered(self, full_data):
        builder = MarketReportBuilder(full_data)
        html = builder.render_html()
        assert "$950,000" in html or "$950k" in html, "Listing price not rendered"

    def test_brand_primary_color_in_css(self, full_data):
        builder = MarketReportBuilder(full_data)
        html = builder.render_html()
        assert "#1B365D" in html or "#1b365d" in html, "Primary color not in CSS"

    def test_custom_accent_color(self, full_data):
        full_data["branding"]["accent_color"] = "#FF6B54"
        builder = MarketReportBuilder(full_data)
        html = builder.render_html()
        assert "#FF6B54" in html or "#ff6b54" in html, "Custom accent color not in CSS"


# ============================================================================
# Print CSS Tests
# ============================================================================

class TestPrintCSS:
    """Verify print-related CSS is present."""

    def test_has_page_size_rule(self, full_data):
        builder = MarketReportBuilder(full_data)
        html = builder.render_html()
        assert "@page" in html, "Missing @page CSS rule"

    def test_has_print_media_query(self, full_data):
        builder = MarketReportBuilder(full_data)
        html = builder.render_html()
        assert "@media print" in html, "Missing @media print rule"

    def test_has_page_break_rules(self, full_data):
        builder = MarketReportBuilder(full_data)
        html = builder.render_html()
        assert "page-break-after" in html or "page-break-inside" in html, \
            "Missing page-break CSS rules"


# ============================================================================
# Edge Case Tests
# ============================================================================

class TestEdgeCases:
    """Test edge cases and error handling."""

    @pytest.mark.parametrize("report_type", ALL_REPORT_TYPES)
    def test_zero_listings(self, minimal_data, report_type):
        """Templates should handle 0 listings gracefully."""
        minimal_data["report_type"] = report_type
        builder = MarketReportBuilder(minimal_data)
        html = builder.render_html()
        assert "<html" in html
        assert "</html>" in html

    def test_missing_optional_metrics(self):
        """Templates should handle missing metrics gracefully."""
        data = {
            "report_type": "market_snapshot",
            "city": "City",
            "listings": [],
            "metrics": {},
            "counts": {},
            "branding": {"agent_name": "Agent"},
        }
        builder = MarketReportBuilder(data)
        html = builder.render_html()
        assert "<html" in html

    def test_none_values_handled(self):
        """Templates should handle None values without crashing."""
        data = {
            "report_type": "closed",
            "city": "City",
            "listings": [
                {
                    "street_address": "Test St",
                    "list_price": None,
                    "close_price": None,
                    "bedrooms": None,
                    "bathrooms": None,
                    "sqft": None,
                    "status": None,
                    "days_on_market": None,
                    "photo_url": None,
                }
            ],
            "metrics": {
                "median_list_price": None,
                "median_close_price": None,
                "avg_dom": None,
            },
            "counts": {},
            "branding": {
                "agent_name": "Agent",
                "agent_phone": None,
                "agent_email": None,
                "agent_photo_url": None,
            },
        }
        builder = MarketReportBuilder(data)
        html = builder.render_html()
        assert ">None<" not in html

    def test_no_brand_colors_uses_defaults(self):
        """Reports render with default navy+teal when no brand colors given."""
        data = {
            "report_type": "new_listings_gallery",
            "city": "Anywhere",
            "listings": [],
            "metrics": {},
            "counts": {},
            "branding": {"agent_name": "Agent"},
        }
        builder = MarketReportBuilder(data)
        html = builder.render_html()
        assert "#18235c" in html, "Default primary color not found"
        assert "<html" in html

    def test_unknown_report_type_falls_back(self, full_data):
        full_data["report_type"] = "nonexistent_type"
        builder = MarketReportBuilder(full_data)
        assert builder.report_type == "market_snapshot"

    def test_theme_id_ignored_gracefully(self, full_data):
        """Old theme_id field doesn't break anything."""
        full_data["theme_id"] = "bold"
        builder = MarketReportBuilder(full_data)
        html = builder.render_html()
        assert "<html" in html


# ============================================================================
# Run Tests
# ============================================================================

if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])

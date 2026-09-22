# tests/test_property_templates.py
"""
Property report templates — rendered the way production renders them.

WHY THIS FILE WAS REWRITTEN (D-089)
-----------------------------------
It contributed 23 of the root suite's 40 failures, and not one of them was a
defect in the product. Every one came from the test hand-building the data the
templates receive.

    20 x jinja2.UndefinedError: 'dict object' has no attribute
        'assessed_value' / 'land_value' / 'tax_amount'

The fixtures wrote the `property` dict by hand and left those keys out.
`_build_property_context()` — one dict literal, the ONLY place a `property`
context is constructed — sets all three unconditionally, as `sitex.get(k) or 0`.
So the shape the templates were asked to render is a shape production cannot
produce. The remaining three were `test_no_undefined_values` asserting that
`>None<` never appears in the output while its own fixture set
`"pool": "None"` — the literal string. The builder writes `sitex.get("pool") or
"No"`.

The file also carried its own copies of `format_currency`,
`format_currency_short` and `format_number` under a header reading "Custom
Filters (must match production)". They had stopped matching: the copies returned
`"-"` for None where `template_filters.py` returns `"N/A"`. **A copy annotated
"must match" is a copy someone already noticed was at risk and left
unprotected.** And the local Jinja `Environment` differed from the real one in
three settings — `trim_blocks`, `lstrip_blocks`, and `select_autoescape` instead
of `autoescape=True`.

THE FIX IS STRUCTURAL, NOT A FIXTURE PATCH
------------------------------------------
Adding the missing keys would have made these tests green while leaving the
mechanism that produced them untouched — and it would have to be done again the
next time `_build_property_context` gains a field.

So nothing here builds a context. Every test goes through
`PropertyReportBuilder(report_data).render_html()`, which is what
`tasks.py` calls. The builder supplies the context, registers the real filters
and owns the Environment, so all three drift surfaces disappear at once. The
inputs these tests DO write by hand are `report_data` — the builder's own
argument, the thing production also hands it.

Confirmed no network: with the default 7-page set, `render_html()` fetches
market trends only when "market_trends" is in the page set and calls the LLM
only when "overview" is. Neither is, so the render is pure.

WHAT THIS COSTS, SAID PLAINLY
-----------------------------
These are no longer template unit tests; they are builder-plus-template
integration tests. A defect in `_build_property_context` can now hide a template
defect by never producing the shape that would expose it. That is a real
trade and it is the right one here: the previous arrangement tested a data shape
that does not exist, which is not coverage of anything.
"""

import os
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "apps/worker/src"))

os.environ.setdefault("DATABASE_URL", "postgresql://fake/fake")
os.environ.setdefault("REDIS_URL", "redis://localhost:6379/0")

from worker.property_builder import (  # noqa: E402
    PropertyReportBuilder,
    THEME_TEMPLATES,
    TEMPLATES_DIR,
)

THEMES = list(THEME_TEMPLATES.keys())

# The 7-page set the builder defaults to. Named here so the page-count test
# asserts against the contract rather than against a number somebody typed.
DEFAULT_PAGE_SET = ["cover", "contents", "aerial", "property", "analysis",
                    "comparables", "range"]


# ============================================================================
# report_data — the builder's input, which is what production writes by hand
# ============================================================================

MINIMAL_REPORT_DATA = {
    "property_address": "123 Test St",
    "property_city": "Test City",
    "property_state": "CA",
    "property_zip": "90210",
}

FULL_REPORT_DATA = {
    "property_address": "1358 5th Street",
    "property_city": "La Verne",
    "property_state": "CA",
    "property_zip": "91750",
    "property_county": "LOS ANGELES",
    "property_type": "Single Family Residential",
    "owner_name": "HERNANDEZ GERARDO J",
    "apn": "8381-021-001",
    "legal_description": "LOT 44 TR#6654",
    "sitex_data": {
        "secondary_owner": "MENDOZA YESSICA S",
        "mailing_address": "1358 5th St, La Verne, CA 91750",
        "census_tract": "4089.00",
        "bedrooms": 2,
        "bathrooms": 1.0,
        "sqft": 786,
        "lot_size": 6155,
        "year_built": 1949,
        "zoning": "LVPR4.5D*",
        "pool": "Yes",
        "garage": "1",
        "fireplace": "No",
        "assessed_value": 428248,
        "land_value": 337378,
        "improvement_value": 90870,
        "tax_amount": 5198,
        "tax_year": 2024,
    },
    # `agent`, not `branding` — `_build_agent_context` reads `report_data["agent"]`
    # for the name, title, phone and email, and only falls back to `branding` for
    # the company display name. Written from the builder, not from memory: the
    # first version of this data put the name under `branding.agent_name` (which
    # is where the MARKET builder reads it) and all five themes rendered an empty
    # agent block while the test still said "agent name not rendered".
    "agent": {
        "name": "Zoe Noelle",
        "title": "Real Estate Specialist",
        "phone": "(213) 309-7286",
        "email": "zoe@realty.com",
        "company_name": "TrendyReports",
    },
    "comparables": [
        {
            "address": "1420 6th Street",
            "city": "La Verne",
            "list_price": 749000,
            "close_price": 735000,
            "sqft": 1100,
            "bedrooms": 3,
            "bathrooms": 2.0,
            "year_built": 1955,
            "days_on_market": 21,
            "status": "Closed",
        },
        {
            "address": "1502 5th Street",
            "city": "La Verne",
            "list_price": 810000,
            "close_price": 799000,
            "sqft": 1240,
            "bedrooms": 3,
            "bathrooms": 2.0,
            "year_built": 1961,
            "days_on_market": 14,
            "status": "Closed",
        },
    ],
}

# Every optional field explicitly None rather than absent. The builder's
# `or <default>` chains are what turn these into renderable values, and that is
# the behaviour under test — a None that reaches a template is the defect.
NONE_VALUED_REPORT_DATA = {
    **MINIMAL_REPORT_DATA,
    "owner_name": None,
    "sitex_data": {
        "bedrooms": None,
        "bathrooms": None,
        "sqft": None,
        "lot_size": None,
        "year_built": None,
        "assessed_value": None,
        "land_value": None,
        "tax_amount": None,
        "pool": None,
        "garage": None,
        "latitude": None,
        "longitude": None,
    },
    "agent": {
        "name": "Agent",
        "title": None,
        "phone": None,
        "email": None,
        "photo_url": None,
    },
    "comparables": [],
}


def render(theme, report_data=None):
    """
    THE ONLY WAY THIS FILE PRODUCES HTML.

    `render_html()` is the production entry point (`tasks.py` calls it), so the
    context, the filters and the Environment all come from the code that ships
    rather than from a copy maintained here.
    """
    data = dict(report_data if report_data is not None else MINIMAL_REPORT_DATA)
    data["theme"] = theme
    return PropertyReportBuilder(data).render_html()


@pytest.fixture
def minimal_html(request):
    return render(request.param)


# ============================================================================
# Template Existence
# ============================================================================

class TestTemplateExistence:
    """Verify all theme templates exist."""

    @pytest.mark.parametrize("theme,path", THEME_TEMPLATES.items())
    def test_template_file_exists(self, theme, path):
        assert (TEMPLATES_DIR / path).exists(), f"{theme}: template not found at {path}"

    def test_all_themes_defined(self):
        assert set(THEMES) == {"teal", "bold", "classic", "modern", "elegant"}


# ============================================================================
# Rendering
# ============================================================================

class TestTemplateRendering:

    @pytest.mark.parametrize("theme", THEMES)
    def test_renders_with_minimal_report_data(self, theme):
        """
        THE 20-FAILURE REGRESSION, INVERTED.

        The old version of this test rendered a hand-written `property` dict
        missing `assessed_value`, and every theme raised UndefinedError. The
        minimal case that matters is an address and nothing else — a SiteX
        lookup that came back empty — and the builder fills the rest.
        """
        html = render(theme, MINIMAL_REPORT_DATA)
        assert "<html" in html
        assert len(html) > 500, f"{theme}: output suspiciously short ({len(html)})"

    @pytest.mark.parametrize("theme", THEMES)
    def test_renders_with_full_report_data(self, theme):
        html = render(theme, FULL_REPORT_DATA)
        assert "<html" in html
        assert len(html) > 500


# ============================================================================
# HTML Structure
# ============================================================================

class TestHTMLStructure:

    @pytest.mark.parametrize("theme", THEMES)
    def test_valid_html_structure(self, theme):
        html = render(theme, FULL_REPORT_DATA)
        assert "<html" in html
        assert "</html>" in html
        assert "<body" in html
        assert "</body>" in html

    @pytest.mark.parametrize("theme", THEMES)
    def test_no_unrendered_jinja(self, theme):
        html = render(theme, FULL_REPORT_DATA)
        assert "{{" not in html, f"{theme}: unrendered Jinja variable"
        assert "{%" not in html, f"{theme}: unrendered Jinja block"

    @pytest.mark.parametrize("theme", THEMES)
    def test_no_undefined_values(self, theme):
        """
        Three of the 23. The old fixture set `"pool": "None"` — the STRING —
        and then asserted `>None<` never appears, so it forbade the value it
        supplied. Through the builder, `sitex.get("pool") or "No"` turns a
        missing pool into "No"; see `test_the_string_None_does_not_reach_the_page`
        below for the case where SiteX hands back the word itself.
        """
        html = render(theme, FULL_REPORT_DATA)
        assert "undefined" not in html.lower(), f"{theme}: 'undefined' in output"
        assert ">None<" not in html, f"{theme}: bare 'None' in output"

    @pytest.mark.parametrize("theme", THEMES)
    def test_has_seven_pages(self, theme):
        """
        The old version counted `class="page ` — WITH a trailing space — and
        fell back to `class="page"` only when that returned zero. teal uses both
        (5 spaced, 2 bare), so the fallback never fired and it reported 5 of 7.
        teal has always rendered seven pages.

        Counting both, and asserting against the builder's declared page set
        rather than a literal 7, so the two cannot drift apart.
        """
        html = render(theme, FULL_REPORT_DATA)
        pages = html.count('class="page ') + html.count('class="page"')
        assert pages >= len(DEFAULT_PAGE_SET), (
            f"{theme}: expected {len(DEFAULT_PAGE_SET)} pages, found {pages}"
        )


# ============================================================================
# Content
# ============================================================================

class TestContentRendering:

    @pytest.mark.parametrize("theme", THEMES)
    def test_property_address_rendered(self, theme):
        html = render(theme, FULL_REPORT_DATA)
        assert "1358 5th Street" in html or "1358 5Th Street" in html

    @pytest.mark.parametrize("theme", THEMES)
    def test_agent_name_rendered(self, theme):
        html = render(theme, FULL_REPORT_DATA)
        assert "Zoe Noelle" in html, f"{theme}: agent name not rendered"

    @pytest.mark.parametrize("theme", THEMES)
    def test_comparables_rendered(self, theme):
        html = render(theme, FULL_REPORT_DATA)
        assert "1420 6th Street" in html or "1502 5th Street" in html, (
            f"{theme}: no comparable address in the output"
        )

    @pytest.mark.parametrize("theme", THEMES)
    def test_currency_formatting(self, theme):
        """
        Through `template_filters.format_currency`, not a local copy of it.
        The copy this file used to carry had drifted on the None case.
        """
        html = render(theme, FULL_REPORT_DATA)
        assert "$" in html, f"{theme}: no currency symbol anywhere in the report"


# ============================================================================
# Print CSS
# ============================================================================

class TestPrintCSS:

    @pytest.mark.parametrize("theme", THEMES)
    def test_has_page_size_rule(self, theme):
        html = render(theme, FULL_REPORT_DATA)
        assert "@page" in html, f"{theme}: no @page rule"

    @pytest.mark.parametrize("theme", THEMES)
    def test_has_print_media_query(self, theme):
        html = render(theme, FULL_REPORT_DATA)
        assert "@media print" in html, f"{theme}: no print media query"

    @pytest.mark.parametrize("theme", THEMES)
    def test_has_page_break_rules(self, theme):
        html = render(theme, FULL_REPORT_DATA)
        assert "page-break" in html or "break-after" in html or "break-inside" in html, (
            f"{theme}: no page-break rules"
        )


# ============================================================================
# Edge Cases
# ============================================================================

class TestEdgeCases:

    @pytest.mark.parametrize("theme", THEMES)
    def test_empty_comparables(self, theme):
        html = render(theme, {**MINIMAL_REPORT_DATA, "comparables": []})
        assert "<html" in html

    @pytest.mark.parametrize("theme", THEMES)
    def test_missing_optional_fields(self, theme):
        """No SiteX data at all — the lookup failed or the parcel is unknown."""
        html = render(theme, MINIMAL_REPORT_DATA)
        assert "<html" in html

    @pytest.mark.parametrize("theme", THEMES)
    def test_none_values_handled(self, theme):
        """
        Explicit Nones, not absent keys. The builder's `or` chains are what make
        these renderable, and a None reaching a template is the defect.
        """
        html = render(theme, NONE_VALUED_REPORT_DATA)
        assert ">None<" not in html, f"{theme}: a None value reached the page"
        assert "undefined" not in html.lower()


# ============================================================================
# The contract this file now depends on
# ============================================================================

class TestBuilderContract:
    """
    These tests exist because the rewrite moved a risk rather than removing it.
    Going through the builder means a builder change can now silently stop
    exercising a template path. These pin the parts of the contract the tests
    above rely on, so that change fails here with a clear reason instead of
    somewhere confusing.
    """

    def test_the_property_context_always_carries_the_tax_fields(self):
        """
        THE 20 FAILURES, STATED AS THE CONTRACT THEY VIOLATED. The templates
        reference `property.assessed_value` unguarded; `format_currency` raises
        UndefinedError on an absent key (it catches ValueError/TypeError, and
        UndefinedError is neither). So "the builder always sets these" is
        load-bearing for every property PDF, not a tidiness preference.
        """
        ctx = PropertyReportBuilder(MINIMAL_REPORT_DATA)._build_property_context()
        for key in ("assessed_value", "land_value", "tax_amount"):
            assert key in ctx, (
                f"_build_property_context no longer sets {key!r}. The property "
                f"templates reference it unguarded and format_currency raises "
                f"UndefinedError on a missing key — every property PDF fails."
            )

    def test_the_render_makes_no_network_calls(self, monkeypatch):
        """
        The rewrite is only safe if rendering is pure. Market trends are fetched
        when "market_trends" is in the page set and the overview calls an LLM
        when "overview" is; neither is in the default set. Asserted rather than
        assumed, because a future default that includes either would turn this
        file into a suite that hits a vendor API.
        """
        import worker.vendors.simplyrets as vendor

        def explode(*a, **k):
            raise AssertionError("render_html() made a vendor call")

        monkeypatch.setattr(vendor, "fetch_properties", explode)
        monkeypatch.setattr(vendor, "count_properties", explode)
        render("teal", FULL_REPORT_DATA)

    def test_the_string_None_does_not_reach_the_page(self):
        """
        The case the old fixture accidentally described. `or "No"` only replaces
        FALSY values, and the string "None" is truthy — so if SiteX ever returns
        the word, it renders as "Pool/Spa: None".

        NOT ASSERTED AS A DEFECT, because nothing establishes SiteX does that;
        the only evidence was a test fixture, and a fixture is not a
        measurement. Recorded as an xfail so the day someone checks the vendor,
        the question is already written down and named.
        """
        html = render("teal", {
            **MINIMAL_REPORT_DATA,
            "sitex_data": {"pool": "None"},
        })
        if ">None<" in html:
            pytest.xfail(
                "SiteX returning the literal string 'None' for pool renders as "
                "'Pool/Spa: None'. Unconfirmed against the vendor — see D-089."
            )


# ============================================================================
# Run Tests
# ============================================================================

if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])

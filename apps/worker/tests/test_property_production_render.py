"""
Workstream E, measured before it was started — the durable half.

WHY THIS FILE EXISTS
--------------------
The 22 E tickets were written from six PDFs produced by
`scripts/generate_all_property_pdfs.py`, which does not call
`PropertyReportBuilder`: it owns a copy of the Jinja filters and a 200-line
`SAMPLE_CONTEXT` literal. Seven of the 22 turned out to describe that literal
rather than the product (§0.6, *a document rendered by something other than the
production path is evidence about that something*).

Re-measuring found five defects that are properties of the BUILDER or the
TEMPLATES and will therefore reproduce on every render, forever, until each is
fixed. A document recording them rots. A strict xfail cannot: it fails the suite
the day someone fixes one without saying so, and it fails the suite the day
someone changes the shape of one without fixing it.

Each xfail below was confirmed to fail for the reason named — not for an
incidental one — by reading the value it asserts on out of a real render.

WHAT PASSES HERE
----------------
`test_all_five_themes_render_through_the_production_path` is the floor the rest
stand on. If the production path stops rendering, every xfail below becomes an
error rather than a finding, and the distinction matters.
"""
import os
import re
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

os.environ.setdefault("DATABASE_URL", "postgresql://fake/fake")
os.environ.setdefault("REDIS_URL", "redis://localhost:6379/0")

from worker.property_builder import PropertyReportBuilder, THEME_TEMPLATES  # noqa: E402

THEMES = sorted(THEME_TEMPLATES)

# `sitex_data` as SiteX returns it, including the two details that matter:
# `pool` is the STRING "None" for a house without one, and there is no
# `estimated_value` key at all — no writer in the repository sets one.
SITEX = {
    "latitude": 34.1008, "longitude": -117.7678,
    "bedrooms": 2, "bathrooms": 1.0, "sqft": 786, "lot_size": 6155,
    "year_built": 1949, "property_type": "Single Family Residential",
    "pool": "None", "garage": "1", "assessed_value": 428248,
    "land_value": 337378, "improvement_value": 90870,
    "tax_amount": 5198, "tax_year": 2024, "census_tract": "4089.00",
    # Carried so test_no_owner_identity_in_property_report can prove they do
    # NOT render. A fixture that omits the field cannot test its absence.
    "secondary_owner": "MENDOZA YESSICA S",
    "mailing_address": "742 Evergreen Terrace, Springfield, CA 90210",
}

# Four comps, which is what the API's ladder returns in a thin market. Four is
# also the smallest count at which "one of them is missing from the analysis"
# is unambiguous rather than an artefact of a degenerate case.
COMPS = [
    {"address": "1889 Bonita Ave", "price": 631500, "close_date": "2026-05-10",
     "sqft": 940, "bedrooms": 2, "bathrooms": 1, "year_built": 1953,
     "lot_size": 7446, "distance": 0.58, "status": "Closed", "days_on_market": 12},
    {"address": "1507 2nd St", "price": 635000, "close_date": "2026-03-15",
     "sqft": 912, "bedrooms": 3, "bathrooms": 1, "year_built": 1952,
     "lot_size": 6261, "distance": 0.54, "status": "Closed", "days_on_market": 21},
    {"address": "1845 Walnut St", "price": 470000, "close_date": "2026-04-25",
     "sqft": 770, "bedrooms": 3, "bathrooms": 1, "year_built": 1910,
     "lot_size": 4917, "distance": 0.24, "status": "Closed", "days_on_market": 34},
    {"address": "1848 1st St", "price": 590000, "close_date": "2026-04-08",
     "sqft": 698, "bedrooms": 1, "bathrooms": 1, "year_built": 1950,
     "lot_size": 5500, "distance": 0.30, "status": "Closed", "days_on_market": 8},
]


def report_data(theme):
    """Shaped as property_tasks/property_report.fetch_report_with_joins returns it."""
    return {
        "id": "00000000-0000-0000-0000-000000000001",
        "account_id": "00000000-0000-0000-0000-0000000000a1",
        "report_type": "seller", "theme": theme, "accent_color": None, "language": "en",
        "property_address": "1358 5th Street", "property_city": "La Verne",
        "property_state": "CA", "property_zip": "91750",
        "property_county": "LOS ANGELES", "apn": "8381-021-001",
        "owner_name": "HERNANDEZ GERARDO J", "legal_description": "LOT 44 TR#6654",
        "property_type": "Single Family Residential",
        "sitex_data": SITEX, "comparables": COMPS, "selected_pages": None,
        "agent": {"name": "Zoe Noelle", "email": "zoe@example.com",
                  "phone": "(213) 555-0100", "photo_url": None,
                  "title": "Real Estate Professional", "license_number": "01234567",
                  "company_name": "TrendyReports", "logo_url": None},
        "branding": None,
    }


@pytest.fixture(scope="module")
def renders():
    return {t: PropertyReportBuilder(report_data(t)).render_html() for t in THEMES}


@pytest.fixture(scope="module")
def builders():
    return {t: PropertyReportBuilder(report_data(t)) for t in THEMES}


# ── the floor ───────────────────────────────────────────────────────────────

def test_all_five_themes_render_through_the_production_path(renders):
    """Every theme produces a document. Nothing below means anything without this."""
    for theme in THEMES:
        assert len(renders[theme]) > 10_000, f"{theme} rendered {len(renders[theme])} chars"


def test_the_default_page_set_is_the_seven_pages_the_rest_of_this_file_assumes(builders):
    """`overview` and `market_trends` are NOT in it — the premise of D-121."""
    for theme in THEMES:
        assert builders[theme].page_set == [
            "cover", "contents", "aerial", "property",
            "analysis", "comparables", "range",
        ]


# ── D-121 · the contents page is a literal block with no page_set guard ─────

CONTENTS_ENTRIES = {
    # Every theme's contents page names these, whatever the page set says.
    "Executive Summary": "overview",
    "Market Trends": "market_trends",
}


@pytest.mark.xfail(strict=True, reason="D-121 — contents is hardcoded, not derived from page_set")
@pytest.mark.parametrize("theme", THEMES)
def test_the_contents_page_lists_only_pages_the_report_contains(theme, renders, builders):
    html, pages = renders[theme], builders[theme].page_set
    listed = [label for label, page in CONTENTS_ENTRIES.items()
              if label in html and page not in pages]
    assert not listed, (
        f"{theme}'s contents advertises {listed}, which the {len(pages)}-page "
        f"default set does not contain"
    )


# ── D-118 · the subject's "Sale Price" is its tax assessment ────────────────

@pytest.mark.xfail(strict=True, reason="D-118 — est_value falls through to assessed_value")
@pytest.mark.parametrize("theme", THEMES)
def test_the_subject_price_is_not_the_county_assessment(theme, builders):
    piq = builders[theme]._build_stats_context()["piq"]
    assert piq["price"] != SITEX["assessed_value"], (
        "the subject's price in the Sale Price row is the Prop 13 assessed "
        f"value ({SITEX['assessed_value']}), printed beside real closed sales"
    )


# ── D-119 · the analysis table drops every comp but three ───────────────────

@pytest.mark.xfail(strict=True, reason="D-119 — low/medium/high is three slots for n comps")
@pytest.mark.parametrize("theme", THEMES)
def test_every_comparable_reaches_the_area_sales_analysis(theme, builders):
    stats = builders[theme]._build_stats_context()
    shown = {stats[k]["price"] for k in ("low", "medium", "high")}
    missing = {float(c["price"]) for c in COMPS} - shown
    assert not missing, (
        f"{len(missing)} of {len(COMPS)} comps appear in the chart and the "
        f"comparables page but in no column of the analysis table: {sorted(missing)}"
    )


# ── D-120 · `pools` is computed from a truthy string ────────────────────────

@pytest.mark.xfail(strict=True, reason='D-120 — `1 if sitex["pool"] else 0`, and "None" is truthy')
@pytest.mark.parametrize("theme", THEMES)
def test_the_analysis_table_agrees_with_the_property_page_about_the_pool(theme, builders):
    b = builders[theme]
    says_no_pool = b._build_property_context()["pool"] in ("None", "No", "-", "")
    has_pool = bool(b._build_stats_context()["piq"]["pools"])
    assert says_no_pool != has_pool, (
        "the property page prints Pool/Spa: "
        f"{b._build_property_context()['pool']!r} and the analysis table one "
        f"page later prints Pools: {b._build_stats_context()['piq']['pools']}"
    )


# ── D-124 · the field set changes with the theme ────────────────────────────

# Row labels as each template spells them, matched case-insensitively INSIDE
# the analysis table only. Scoping matters: "Lot Size" and "Bathrooms" also
# appear on the property page, so a document-wide grep reports modern as
# carrying rows it does not have — §0.6, *a selector that is unique by accident*.
ROW_LABELS = {
    "distance":     ("Distance",),
    "living area":  ("Living Area",),
    "price/sqft":   ("Price/Sq.Ft.", "Price Per Sqft"),
    "year built":   ("Year Built",),
    "lot size":     ("Lot Size",),
    "bedrooms":     ("Bedrooms",),
    "bathrooms":    ("Bathrooms", "Baths"),
    "stories":      ("Stories",),
    "pools":        ("Pools",),
    "sale price":   ("Sale Price", "Sales Price"),
}


def analysis_table(html: str) -> str:
    """The one table carrying both `Year Built` and `Distance`.

    Asserted unique rather than taken with `[0]`: teal has eight tables and
    elegant seven, and picking the first that matches is the accidental-selector
    trap. If a template ever grows a second comparison table this fails loudly
    instead of silently measuring the wrong one.
    """
    tables = re.findall(r"<table\b.*?</table>", html, re.S)
    hits = [t for t in tables if "Year Built" in t and "Distance" in t]
    assert len(hits) == 1, f"expected one analysis table, found {len(hits)} of {len(tables)}"
    return hits[0]


@pytest.mark.xfail(strict=True, reason="D-124 — each template hand-picks its own rows")
def test_the_analysis_table_shows_the_same_fields_in_every_theme(renders):
    def rows_in(html):
        lower = analysis_table(html).lower()
        return {datum for datum, spellings in ROW_LABELS.items()
                if any(s.lower() in lower for s in spellings)}

    sets = {theme: rows_in(renders[theme]) for theme in THEMES}
    reference = sets[THEMES[0]]
    differing = {t: sorted(s ^ reference) for t, s in sets.items() if s != reference}
    assert not differing, (
        f"the analysis table's fields differ by theme (vs {THEMES[0]}): {differing}. "
        "An agent switching themes changes what analysis their client receives."
    )

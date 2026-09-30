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
from datetime import date, timedelta
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
    # D-118: SiteX's SaleLoanInfo, exact keys and values confirmed by the
    # probe against production. $369,000 on 2015-12-23.
    "last_sale_price": 369000, "last_sale_date": "2015-12-23",
    "last_sale_price_per_sqft": 469.0,
    "secondary_owner": "MENDOZA YESSICA S",
    "mailing_address": "742 Evergreen Terrace, Springfield, CA 90210",
}

# Four comps, which is what the API's ladder returns in a thin market. Four is
# also the smallest count at which "one of them is missing from the analysis"
# is unambiguous rather than an artefact of a degenerate case.
# Close dates are RELATIVE, and that is not a style preference. Written with
# absolute dates ("2026-05-10" …), this fixture silently aged past the
# six-month window as the calendar moved, and the D-132 tests began reporting
# a twelve-month window for comps meant to be recent. A fixture with a
# hardcoded date encodes the day it was written; D-117 is the same mistake in
# the product.
def _days_ago(n: int) -> str:
    return (date.today() - timedelta(days=n)).isoformat()


COMPS = [
    {"address": "1889 Bonita Ave", "price": 631500, "close_date": _days_ago(40),
     "sqft": 940, "bedrooms": 2, "bathrooms": 1, "year_built": 1953,
     "lot_size": 7446, "distance": 0.58, "status": "Closed", "days_on_market": 12},
    {"address": "1507 2nd St", "price": 635000, "close_date": _days_ago(150),
     "sqft": 912, "bedrooms": 3, "bathrooms": 1, "year_built": 1952,
     "lot_size": 6261, "distance": 0.54, "status": "Closed", "days_on_market": 21},
    {"address": "1845 Walnut St", "price": 470000, "close_date": _days_ago(95),
     "sqft": 770, "bedrooms": 3, "bathrooms": 1, "year_built": 1910,
     "lot_size": 4917, "distance": 0.24, "status": "Closed", "days_on_market": 34},
    {"address": "1848 1st St", "price": 590000, "close_date": _days_ago(112),
     "sqft": 698, "bedrooms": 1, "bathrooms": 1, "year_built": 1950,
     "lot_size": 5500, "distance": 0.30, "status": "Closed", "days_on_market": 8},
]


def test_the_fixture_comps_stay_inside_the_six_month_window():
    """The guard for the bug above: if someone reinstates absolute dates, or
    the window shrinks, this says so instead of the D-132 tests failing for a
    reason that has nothing to do with D-132."""
    oldest = max((date.today() - date.fromisoformat(c["close_date"])).days
                 for c in COMPS)
    assert oldest <= PropertyReportBuilder.COMP_CLOSE_WINDOW_DAYS, (
        f"the oldest fixture comp is {oldest} days old, outside the "
        f"{PropertyReportBuilder.COMP_CLOSE_WINDOW_DAYS}-day window it is "
        f"meant to sit inside"
    )


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

@pytest.mark.parametrize("theme", THEMES)
def test_the_subject_price_is_not_the_county_assessment(theme, builders):
    """FIXED 2026-09-30. Was a strict xfail; the assessment is gone.

    `estimated_value` is written by nothing, so `or assessed_value` was not a
    fallback — it was the only path, and the subject's price was a Prop 13
    figure beside real sales 50% higher.
    """
    piq = builders[theme]._build_stats_context()["piq"]
    assert piq["price"] != SITEX["assessed_value"], (
        "the subject's price in the Sale Price row is the Prop 13 assessed "
        f"value ({SITEX['assessed_value']}), printed beside real closed sales"
    )
    assert piq["price"] == SITEX["last_sale_price"], (
        "the row shows the last RECORDED SALE, which SiteX carries in "
        "SaleLoanInfo and the parser now reads"
    )
    assert piq["price_per_sqft"] == SITEX["last_sale_price_per_sqft"]


def test_sitex_s_own_ratio_is_used_where_it_differs_from_a_derived_one():
    """The fixture's 369000/786 rounds to 469, which is also SiteX's figure —
    so asserting equality against the fixture proves nothing about WHICH was
    used. Measured: replacing the vendor value with a derived one left the
    suite green. This case separates them.

    They diverge in practice because SiteX computes against the sqft recorded
    with the SALE, which differs from PropertyCharacteristics after an
    addition. A row that disagrees with itself is worse than one slightly
    stale.
    """
    data = report_data("teal")
    data["sitex_data"] = {**SITEX, "last_sale_price_per_sqft": 527.1}
    piq = PropertyReportBuilder(data)._build_stats_context()["piq"]
    assert piq["price_per_sqft"] == 527.1, (
        "the derived 369000/786 = 469 was used instead of SiteX's 527.1"
    )


@pytest.mark.parametrize("theme", THEMES)
def test_with_no_recorded_sale_the_cell_is_empty_not_zero(theme):
    """A property that has never transferred, or one whose report predates
    the parser reading the block."""
    data = report_data(theme)
    data["sitex_data"] = {k: v for k, v in SITEX.items()
                          if not k.startswith("last_sale")}
    piq = PropertyReportBuilder(data)._build_stats_context()["piq"]
    assert piq["price"] is None, (
        "zero is a price — `format_currency(0)` renders '$0'"
    )
    assert piq["price_per_sqft"] is None
    assert piq["price_display"] == "N/A"


@pytest.mark.parametrize("theme", THEMES)
def test_the_sale_is_shown_with_its_date(theme, renders):
    """A 2015 sale presented bare reads as a current valuation sitting 25%
    below four recent comps — the same anchoring harm the assessment did, with
    a true number. D-118."""
    html = renders[theme]
    assert "$369,000" in html
    assert "Dec 2015" in html, f"{theme} prints the figure without its date"
    row = [l for l in analysis_table(html).split("</tr>") if "369,000" in l]
    assert row and "Dec 2015" in row[0], (
        f"{theme} has the date somewhere, but not in the price row"
    )


@pytest.mark.parametrize("theme", THEMES)
def test_the_comps_cells_carry_no_date(theme, renders):
    """Their dates are already a column on the Sales Comparables page, and
    four more in this row would crowd out the price spread it exists to show."""
    row = [l for l in analysis_table(renders[theme]).split("</tr>")
           if "369,000" in l][0]
    assert row.count("\u00b7") <= 1 and row.count("&middot;") == 0


@pytest.mark.parametrize("theme", THEMES)
def test_the_assessment_appears_only_under_its_own_label(theme, renders):
    """Jerry kept the Tax & Assessment block. What went is the assessment
    standing in for a sale price."""
    html = renders[theme]
    assert "428,248" in html, f"{theme} lost the Tax & Assessment block entirely"
    assert "428,248" not in analysis_table(html), (
        f"{theme}'s analysis table still carries the assessed value"
    )


@pytest.mark.parametrize("theme", THEMES)
def test_a_computed_estimate_outranks_a_ten_year_old_sale(theme):
    """`estimated_value` is written by nothing today and D-134 will decide
    what computes it. When it does, a current estimate should beat a 2015
    sale — and its ratio must be DERIVED, because SiteX's PricePerSQFT
    belongs to SiteX's price, not to ours."""
    data = report_data(theme)
    data["sitex_data"] = {**SITEX, "estimated_value": 700000}
    piq = PropertyReportBuilder(data)._build_stats_context()["piq"]
    assert piq["price"] == 700000
    assert piq["price_per_sqft"] == 890            # 700000 / 786, not 469
    assert "Dec 2015" not in piq["price_display"], (
        "an estimate we computed must not be dated with SiteX's sale"
    )


@pytest.mark.parametrize("theme", THEMES)
def test_the_price_row_says_which_kind_of_price_it_shows(theme):
    """Over active listings `_extract_price` returns list_price, so a row
    headed "Sale Price" shows what sellers are asking. Same defect as the
    subtitle, one row lower."""
    assert "Sale Price" in _with_status(theme, "Closed")
    active = _with_status(theme, "Active")
    assert "List Price" in active
    assert "Sale Price" not in analysis_table(active), (
        f"{theme}'s analysis table calls asking prices sale prices"
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

@pytest.mark.parametrize("theme", THEMES)
def test_the_analysis_table_agrees_with_the_property_page_about_the_pool(theme, builders):
    """FIXED 2026-09-30 by D-137. Was a strict xfail.

    The contradiction was `1 if sitex_data.get("pool") else 0` against
    `pool or "No"` — SiteX spells "no pool" as the STRING "None", which is
    truthy, so the table said 1 while the page said None. Both now route
    through `_tri_state_bool`, which distinguishes absent from a real
    negative instead of collapsing them.
    """
    b = builders[theme]
    page = b._build_property_context()["pool"]
    table = b._build_stats_context()["piq"]["pools"]
    says_no_pool = page in ("None", "No", "-", "")
    has_pool = table == 1
    assert not (says_no_pool and has_pool), (
        f"the property page prints Pool/Spa: {page!r} and the analysis table "
        f"one page later prints Pools: {table!r}"
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


# ── D-117 · what the page may say about the comps it is carrying ───────────

# The months figure is derived from the constant, never typed, so the copy
# cannot drift from the query the way it did for twelve months.
WINDOW_MONTHS = PropertyReportBuilder.COMP_CLOSE_WINDOW_DAYS // 30


def _with_status(theme, status):
    data = report_data(theme)
    data["comparables"] = [{**c, "status": status} for c in data["comparables"]]
    return PropertyReportBuilder(data).render_html()


@pytest.mark.parametrize("theme", THEMES)
def test_closed_comps_are_described_as_sales_in_the_window(theme):
    html = _with_status(theme, "Closed")
    assert f"last {WINDOW_MONTHS} months" in html or \
           f"PAST {WINDOW_MONTHS} MONTHS" in html, f"{theme} states no window"
    assert "12 months" not in html and "12-month" not in html


@pytest.mark.parametrize("theme", THEMES)
def test_active_comps_are_not_described_as_sales(theme):
    """The wizard DEFAULTS to Active (property-wizard.tsx:53). Correcting
    twelve months to six on a list of homes that have not sold would state a
    wrong thing more precisely, which is worse than vaguely."""
    html = _with_status(theme, "Active")
    lower = html.lower()
    for claim in (f"sold within the last {WINDOW_MONTHS} months",
                  f"sales in the past {WINDOW_MONTHS} months"):
        assert claim not in lower, f"{theme} calls active listings {claim!r}"
    assert "currently" in lower or "asking" in lower, \
        f"{theme} says nothing about these being listings rather than sales"


def test_the_empty_case_claims_nothing():
    data = report_data("teal")
    data["comparables"] = []
    window = PropertyReportBuilder(data)._comps_window()
    assert "No comparable properties" in window["label"]
    for text in window.values():
        assert f"{WINDOW_MONTHS} months" not in text, (
            "an empty table must not be headed with a window it did not search"
        )


# The construct, not the symptom: any month count typed into window copy can
# drift from COMP_CLOSE_WINDOW_DAYS, which is exactly what D-117 was.
WINDOW_COPY = re.compile(
    r"(?:last|past|within)\s+(?:the\s+)?(\d+)[\s-]*months?", re.I)

@pytest.mark.parametrize("theme", THEMES)
def test_no_live_template_hardcodes_a_comp_window(theme):
    from worker.property_builder import TEMPLATES_DIR
    path = TEMPLATES_DIR / THEME_TEMPLATES[theme]
    text = path.read_text(encoding="utf-8")
    found = WINDOW_COPY.findall(text)
    assert not found, (
        f"{path.name} hardcodes a {found} month window in its copy. The number "
        "belongs to COMP_CLOSE_WINDOW_DAYS and reaches the page through "
        "`comps_window` — a typed one is how D-117 happened."
    )


# ── D-132 · the page states the window that actually covers its comps ──────

def _aged(theme, *days_ago):
    data = report_data(theme)
    base = data["comparables"]
    data["comparables"] = [
        {**base[i % len(base)], "status": "Closed", "close_date": _days_ago(d)}
        for i, d in enumerate(days_ago)
    ]
    return PropertyReportBuilder(data)


@pytest.mark.parametrize("theme", THEMES)
def test_comps_inside_six_months_are_stated_as_six(theme):
    assert _aged(theme, 20, 90, 170)._comps_window()["subtitle"] == \
        "SALES IN THE PAST 6 MONTHS"


@pytest.mark.parametrize("theme", THEMES)
def test_a_comp_from_the_widened_window_is_stated_as_twelve(theme):
    """D-132's L6 searches twelve months when six returns under three. If the
    page still said six it would be D-117 again, one level up — a stated
    window the query did not use."""
    window = _aged(theme, 20, 270)._comps_window()
    assert window["subtitle"] == "SALES IN THE PAST 12 MONTHS"
    assert "last 12 months" in window["note"]


def test_a_comp_older_than_any_ladder_window_is_reported_not_rounded_down():
    """Legacy rows and hand-edited comps exist. Understating their age is the
    D-117 failure with a smaller number."""
    assert _aged("teal", 20, 1100)._comps_window()["subtitle"] == \
        "SALES IN THE PAST 36 MONTHS"


def test_the_window_comes_from_the_comps_and_not_from_the_constant():
    """The derivation is the point: plumbing the window from the API through
    the wizard, the payload and the DB row is four hops that can each drop it,
    for a number the data already implies."""
    import inspect
    src = inspect.getsource(PropertyReportBuilder._window_months)
    assert "close_date" in src and "COMP_WINDOW_BUCKETS_MONTHS" in src
    assert PropertyReportBuilder.COMP_WINDOW_BUCKETS_MONTHS[0] == \
        PropertyReportBuilder.COMP_CLOSE_WINDOW_DAYS // 30

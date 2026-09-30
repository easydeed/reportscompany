"""
D-139 — the consumer CMA and the agent CMA must render the same property page.

WHY A RENDER DIFF AND NOT A FIELD DIFF
--------------------------------------
`apps/api/tests/test_property_lookup_contract.py` compares model fields, which
is cheap and catches a field added to `PropertyData` and forgotten. It cannot
catch the third place this path drops things: `tasks.py`'s consumer branch
builds its own `report_data` and its own `sitex_data` literal, so a field can
be stored on the row, accepted by every model, and still never reach the
builder. That is what happened to `apn`, `county`, `legal_description` and
`property_type` — present in `consumer_reports.property_data`, absent from the
report, for as long as the path has existed.

This test builds both `report_data` dicts the way the two producers build
them, runs the real builder on each, and requires the property contexts to
match. It measures what a reader sees, so it survives a rename, a new block,
or a fourth place that drops things.

THE CONSUMER PATH IS THE ONE THAT CARRIES DEFECTS, THREE TIMES NOW
------------------------------------------------------------------
D-116 (owner identity), D-138 (the last-sale fields), D-139 (nine more). Each
time the agent path worked and the consumer path did not, and each time that
is why it survived review. Its construction is the reason: the agent path
hands `PropertyData` almost straight through, while the consumer path retypes
the shape three times — a projection, a request payload, and a literal in the
worker. Every retyping is a place to forget a field, and none of them errors
when it does.

It is also the path with no agent in the loop to notice the report is thinner
than it should be.
"""
import os
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
sys.path.insert(0, str(Path(__file__).resolve().parents[3] / "apps/api/src"))

os.environ.setdefault("DATABASE_URL", "postgresql://fake/fake")
os.environ.setdefault("REDIS_URL", "redis://localhost:6379/0")

from api.services.sitex import PropertyData  # noqa: E402
from worker.property_builder import PropertyReportBuilder  # noqa: E402

#: One SiteX lookup, every field populated, so a dropped one shows as a gap
#: rather than as two matching blanks — the coincidence class, §0.6.
LOOKUP = PropertyData(
    street="1358 5th Street", city="La Verne", state="CA", zip_code="91750",
    county="LOS ANGELES", apn="8381-021-001", legal_description="LOT 44 TR#6654",
    bedrooms=2, bathrooms=1.0, sqft=786, lot_size=6155, year_built=1949,
    assessed_value=428248, tax_amount=5198.0, land_value=337378,
    improvement_value=90870, tax_year=2024,
    latitude=34.1008, longitude=-117.7678,
    property_type="Single Family Residential",
    last_sale_price=369000, last_sale_date="2015-12-23",
    last_sale_price_per_sqft=469.0,
).model_dump()


#: Four comps, relative dates so the fixture cannot age past the six-month
#: window (D-132). BOTH fixtures get these: without them the analysis table's
#: comp columns are `$0` on both sides, and
#: `test_both_paths_render_the_same_analysis_table` would pass by comparing
#: two rows of zeros — the coincidence class, caught here for the third time
#: while writing a test to catch it.
def _days_ago(n: int) -> str:
    from datetime import date, timedelta
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


def agent_report_data():
    """The wizard's payload, as `routes/property.create_report` stores it and
    `fetch_report_with_joins` returns it.

    The four address fields are top-level columns on `property_reports`, NOT
    part of `sitex_data` — `_build_property_context` reads them from
    `report_data`. They were missing from this fixture until D-140, and the
    mirrored consumer fixture was missing them too, so the parity test
    compared two blanks and passed. Exactly the coincidence
    `test_every_field_that_should_travel_is_populated` was written to
    prevent, one level up from where that test was looking.
    """
    return {
        "property_address": LOOKUP["street"],
        "property_city": LOOKUP["city"],
        "property_state": LOOKUP["state"],
        "property_zip": LOOKUP["zip_code"],
        "sitex_data": LOOKUP,
        "apn": LOOKUP["apn"],
        "property_county": LOOKUP["county"],
        "legal_description": LOOKUP["legal_description"],
        "property_type": LOOKUP["property_type"],
        "comparables": COMPS,
    }


def consumer_property_data():
    """`consumer_reports.property_data`, as `lead_pages.request_report` stores it."""
    keys = ("apn", "county", "legal_description", "property_type",
            "bedrooms", "bathrooms", "sqft", "lot_size", "year_built",
            "latitude", "longitude", "assessed_value", "land_value",
            "improvement_value", "tax_amount", "tax_year",
            "last_sale_price", "last_sale_date", "last_sale_price_per_sqft")
    return {k: LOOKUP[k] for k in keys}


def consumer_report_data():
    """`report_data`, as `tasks.py`'s consumer branch builds it.

    IMPORTED, NOT MIRRORED — D-140, and the whole point of the extraction.

    This function used to restate `tasks.py`'s dict literal, because the
    literal lived ~350 lines inside a Celery task and there was nothing to
    import. That made the gate silent on the one failure it exists to catch:
    editing the task without editing the test left it green, guarding
    nothing. The R2 regression for D-139 only failed because both copies were
    changed by hand, which is not a property a gate can rely on.

    `build_consumer_report_data` is now the single definition. A field
    dropped from it fails here by construction.
    """
    from worker.consumer_report_data import build_consumer_report_data

    pd = consumer_property_data()
    return build_consumer_report_data(
        property_data=pd,
        prop_address=LOOKUP["street"],
        prop_city=LOOKUP["city"],
        prop_state=LOOKUP["state"],
        prop_zip=LOOKUP["zip_code"],
        comparables=COMPS,
        agent_name="Zoe Noelle",
    )


def test_the_two_paths_render_the_same_property_page():
    agent = PropertyReportBuilder(agent_report_data())._build_property_context()
    consumer = PropertyReportBuilder(consumer_report_data())._build_property_context()
    differing = {f: (agent[f], consumer[f]) for f in agent if agent[f] != consumer[f]}
    assert not differing, (
        "the consumer CMA renders a different property page from the agent's. "
        "Nobody sees an error when this happens — the stranger just gets a "
        "thinner report:\n" + "\n".join(
            f"    {f}: agent={a!r} consumer={c!r}"
            for f, (a, c) in sorted(differing.items()))
    )


def test_the_two_paths_agree_on_the_subject_price_row():
    """The row D-118 fixed, checked on the path D-138 broke."""
    agent = PropertyReportBuilder(agent_report_data())._build_stats_context()["piq"]
    consumer = PropertyReportBuilder(consumer_report_data())._build_stats_context()["piq"]
    assert agent["price"] == consumer["price"] == 369000
    assert agent["price_display"] == consumer["price_display"]
    assert "Dec 2015" in consumer["price_display"]


#: Must NOT travel to the consumer path, so they are blank in LOOKUP on
#: purpose. `apps/api/tests/test_property_lookup_contract.py` owns the full
#: reasoning and asserts the list against the model; repeated here only
#: because this test's fixture has to know which blanks are deliberate.
MUST_NOT_TRAVEL = {"owner_name", "secondary_owner",   # D-116, identity
                   "fips",                            # re-query key, never rendered
                   "full_address",                    # derived by the builder
                   "unit_number", "unit_type",        # not reachable from the
                                                      # consumer address search
                   "raw_response", "source", "confidence"}


def test_every_field_that_should_travel_is_populated_in_the_fixture():
    """Two paths agreeing on a blank is not agreement.

    §0.6: a fixture that leaves a field empty cannot tell "both carry it"
    from "neither does" — the same coincidence that let a derived ratio pass
    for SiteX's own. Caught by this test on its first run, which is the only
    reason it is worth having.
    """
    blank = sorted(k for k, v in LOOKUP.items()
                   if v in (None, "", 0) and k not in MUST_NOT_TRAVEL)
    assert not blank, (
        f"these would compare equal by being absent on both sides: {blank}"
    )


def test_neither_path_s_property_page_is_blank_where_they_agree():
    """The guard the fixture guard was missing.

    `test_every_field_that_should_travel_is_populated` checks LOOKUP, the
    SOURCE. It cannot see a field that both `report_data` dicts fail to
    supply — which is what happened to the four address columns: they live on
    `property_reports`, not in `sitex_data`, so LOOKUP being complete said
    nothing about them. Both sides rendered blank, the parity test compared
    two absences, and it passed.

    So: assert agreement AND non-emptiness, on every field the report shows.
    """
    agent = PropertyReportBuilder(agent_report_data())._build_property_context()
    rendered_blank = sorted(
        f for f, v in agent.items()
        if v in (None, "", 0, "-") and f not in MUST_NOT_TRAVEL
        # Genuinely absent from SiteX for this subject — D-135's nineteen.
        # Listed so the ones that are supposed to be there stay checked.
        and f not in {"pool", "zoning", "garage", "fireplace", "census_tract",
                      "housing_tract", "lot_number", "page_grid",
                      "partial_bath", "percent_improved", "tax_status",
                      "tax_rate_area", "total_rooms", "num_units", "units",
                      "use_code", "notes", "mailing_address", "improvement_pct",
                      "latitude", "longitude"}
    )
    assert not rendered_blank, (
        f"these render blank on BOTH paths, so the parity test above cannot "
        f"tell 'both carry it' from 'neither does': {rendered_blank}"
    )


def test_the_deliberate_blanks_are_still_blank():
    """The other half: if `owner_name` ever gets a value in this fixture, the
    parity test above would start demanding the consumer path carry it."""
    for field in ("owner_name", "secondary_owner"):
        assert not LOOKUP[field], f"{field} must stay empty here (D-116)"


def test_the_consumer_path_still_carries_no_identity():
    """Widening this path is exactly when an owner name gets added back by
    reflex. D-116, asserted where the shape is retyped."""
    consumer = PropertyReportBuilder(consumer_report_data())._build_property_context()
    assert not consumer["owner_name"]
    assert consumer["secondary_owner"] in ("-", "", None)


# ══════════════════════════════════════════════════════════════════════════
# D-141 · the consumer report must place the subject against its comps
# ══════════════════════════════════════════════════════════════════════════

import re  # noqa: E402

from worker.consumer_report_data import CONSUMER_PAGES  # noqa: E402


def _render(report_data):
    return PropertyReportBuilder(report_data).render_html()


def _analysis_table(html):
    """The one table carrying both `Year Built` and `Distance`, or None."""
    hits = [t for t in re.findall(r"<table\b.*?</table>", html, re.S)
            if "Year Built" in t and "Distance" in t]
    assert len(hits) <= 1, f"expected at most one analysis table, found {len(hits)}"
    return hits[0] if hits else None


def test_the_consumer_report_carries_the_area_sales_analysis():
    """The page that places the subject against its comps.

    Without it the reader gets four cards showing OTHER houses' prices and a
    range, and nothing that says "and here is yours" — in a document they
    requested by typing their address into a form asking what it is worth.
    """
    assert "analysis" in CONSUMER_PAGES
    assert _analysis_table(_render(consumer_report_data())) is not None


def test_the_subject_s_last_sale_reaches_the_consumer_report():
    """D-118's figure was wired through the projection, the payload, the row
    and the builder across three PRs — and landed on a page this path did not
    print. "The page renders" is not "the figure is on it", so this asserts
    the value, in the row, in the table.
    """
    table = _analysis_table(_render(consumer_report_data()))
    price_row = [r for r in table.split("</tr>") if "369,000" in r]
    assert price_row, "the last-sale figure is not in the analysis table"
    cells = [re.sub("<[^>]+>", "", c).strip()
             for c in re.findall(r"<t[dh][^>]*>(.*?)</t[dh]>", price_row[0], re.S)]
    assert "Dec 2015" in cells[1], cells
    assert cells[2:5] == ["$470,000", "$631,500", "$635,000"], cells


def test_both_paths_render_the_same_analysis_table():
    """Not just present — the same. A consumer table built from a thinner
    context would pass the test above and still differ."""
    agent = _analysis_table(_render(agent_report_data()))
    consumer = _analysis_table(_render(consumer_report_data()))
    def rows(t):
        return [[re.sub("<[^>]+>", "", c).strip()
                 for c in re.findall(r"<t[dh][^>]*>(.*?)</t[dh]>", r, re.S)]
                for r in t.split("</tr>") if "<td" in r or "<th" in r]
    assert rows(agent) == rows(consumer)


def test_contents_is_back_and_describes_a_consumer_report():
    """D-121 landed 2026-10-01; this asserted its absence until then.

    The consumer set is where a hardcoded contents page shows worst — it
    differs from the default on four pages, so every literal row would have
    been wrong. Now that the rows come from the page set, the check is that
    the contents of a consumer report describes THIS report: no `property`
    row in a set that has one, no `Area Sales Analysis` row pointing at the
    comparables page.
    """
    assert "contents" in CONSUMER_PAGES
    html = _render(consumer_report_data())
    labels = re.findall(r'class="(?:contents-text|name)">\s*([^<]*?)\s*<', html)
    assert labels, "the contents page rendered no rows"
    # Every label must be a heading that exists in this document.
    headings = {h.strip().upper() for h in re.findall(
        r'class="(?:page-header-title|property-title|section-title|aerial-title|h)"'
        r'[^>]*>\s*([^<]*?)\s*<', html)}
    missing = [l for l in labels if l.upper() not in headings]
    assert not missing, (
        f"the consumer contents advertises {missing}; this document is headed "
        f"{sorted(headings)}"
    )


#: SEVEN / EIGHT / NINE since D-121 restored `contents` to the consumer set
#: (2026-10-01). It was six / seven / eight while the contents page was held
#: out because its rows were hardcoded.
@pytest.mark.parametrize("supply_trends,supply_overview,expected_sections", [
    (False, False, 7),
    (True,  False, 8),
    (True,  True,  9),
])
def test_the_page_set_is_a_maximum_not_a_guarantee(
        supply_trends, supply_overview, expected_sections):
    """D-142. `market_trends` needs a live SimplyRETS fetch and `overview` an
    OpenAI key; `render_html` drops either without a word. So the consumer
    report is seven pages when neither answers and nine when both do — and
    `analysis` renders unconditionally, which is half of why it belongs in
    the set.

    Counted from the RENDER, not from `builder.page_set`: `render_html`
    prunes a local copy and writes it to the context, leaving `self.page_set`
    at its original value. An assertion on the attribute would have reported
    eight pages for a six-page document — measuring the intent instead of the
    output, which is the whole error this defect is made of.
    """
    from worker.compute.market_trends import SAMPLE_MARKET_TRENDS
    data = consumer_report_data()
    if supply_trends:
        data["market_trends_data"] = SAMPLE_MARKET_TRENDS
    if supply_overview:
        data["overview_text"] = "A short executive summary."
    html = PropertyReportBuilder(data).render_html()
    assert len(re.findall(r'<section class="', html)) == expected_sections

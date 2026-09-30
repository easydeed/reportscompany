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
        comparables=[],
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

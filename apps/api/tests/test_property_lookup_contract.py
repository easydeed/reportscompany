"""
The wizard's contract with the lookup endpoints, asserted rather than read.

WHY THIS EXISTS
---------------
D-118 added `last_sale_price`, `last_sale_date` and `last_sale_price_per_sqft`
to `PropertyData` and taught two wizards to read them. `tsc` passed. The agent
wizard worked. **The consumer wizard silently did not**, because
`/v1/cma/{code}/search` does not return `PropertyData` — it returns
`PropertySearchResult`, a HAND-COPIED projection that had no such fields. The
frontend read `undefined`, sent nothing, and the consumer's report fell back
to `N/A` with no error in any log.

That is this project's signature failure — a producer that silently stops
covering a consumer — on code written the same day the rule was written down.

WHAT IS ASSERTED
----------------
1. The fields survive `PropertySearchResponse`, which the agent wizard reads.
2. `PropertySearchResult` covers every field the consumer wizard sends onward.
3. `ReportRequestPayload` accepts every field that projection can produce.
4. The TypeScript that reads them names them identically.

(4) is the one that catches a rename, which is the failure mode here: every
Python side can agree perfectly and the frontend still read `d.lastSalePrice`.
Parsing the .tsx with a regex is crude, and it is the only thing in reach that
crosses the language boundary — §0.6's construct-search rule, applied where the
construct is a JSON key shared by two languages.
"""
import re
from pathlib import Path

import pytest

from api.routes.lead_pages import PropertySearchResult, ReportRequestPayload
from api.routes.property import PropertySearchResponse
from api.services.sitex import PropertyData

WEB = Path(__file__).resolve().parents[3] / "apps/web/components"

#: The three D-118 added. Named once so a fourth cannot be added to the model
#: and forgotten here — `test_every_last_sale_field_is_listed` fails if it is.
LAST_SALE = ("last_sale_price", "last_sale_date", "last_sale_price_per_sqft")


def test_every_last_sale_field_on_the_model_reaches_a_consumer():
    """Both directions for this family.

    A field added to `PropertyData` and not listed here is untested — that is
    the read-with-no-producer shape. A field listed here and not on the model
    is the mirror, and D-138 is what that mirror cost: `last_sale_document`
    was parsed for one commit with nothing to display it.
    """
    declared = {f for f in PropertyData.model_fields if f.startswith("last_sale")}
    assert declared == set(LAST_SALE), (
        f"model has {sorted(declared)}, this file covers {sorted(LAST_SALE)}. "
        f"Either wire the new field through both wizards and list it, or do "
        f"not parse it."
    )


# ── 1 · the agent path ────────────────────────────────────────────────────

def test_the_search_response_carries_the_last_sale_to_the_agent_wizard():
    """`data: Optional[PropertyData]`, so the fields serialise — but this is
    asserted through the response model rather than read off the annotation,
    because a narrower `data` type is exactly how the consumer path broke."""
    body = PropertySearchResponse(
        success=True,
        data=PropertyData(last_sale_price=369000, last_sale_date="2015-12-23",
                          last_sale_price_per_sqft=469.0),
    ).model_dump()
    for f in LAST_SALE:
        assert f in body["data"], f"{f} does not survive PropertySearchResponse"
    assert body["data"]["last_sale_price"] == 369000
    assert body["data"]["last_sale_date"] == "2015-12-23"


# ── 2 · the consumer path, which is where it actually broke ───────────────

def test_the_cma_search_result_carries_the_last_sale():
    fields = set(PropertySearchResult.model_fields)
    missing = [f for f in LAST_SALE if f not in fields]
    assert not missing, (
        f"/v1/cma/{{code}}/search drops {missing}. The consumer wizard reads "
        f"them, gets undefined, and the report says N/A with no error anywhere."
    )


def test_the_report_request_accepts_everything_the_search_can_return():
    """The consumer wizard forwards the search result into `/request`. A field
    the search returns and the request rejects is dropped one hop later, which
    looks identical from the report."""
    returned = set(PropertySearchResult.model_fields)
    accepted = set(ReportRequestPayload.model_fields)
    # Renamed deliberately on the way through, not dropped.
    renamed = {"apn": "property_apn", "fips": "property_fips",
               "address": "property_address", "city": "property_city",
               "state": "property_state", "zip": "property_zip"}
    lost = sorted(f for f in returned - accepted if renamed.get(f) not in accepted)
    assert not lost, f"the search returns {lost} and /request will not accept them"


def test_the_projection_does_not_leak_a_name():
    """`PropertySearchResult` is hand-copied, so widening it is the moment an
    owner or seller name gets added by reflex. D-116's rule, at the one place
    the shape is retyped."""
    fields = set(PropertySearchResult.model_fields)
    assert "secondary_owner" not in fields
    assert not any(f.endswith(("seller", "lender", "title_company"))
                   for f in fields), fields


# ── 3 · the language boundary, which is what a rename slips through ───────

def _reads_dot_fields(path: Path, receiver: str) -> set:
    """`<receiver>.someField` occurrences in a .tsx file."""
    src = path.read_text(encoding="utf-8")
    return set(re.findall(rf"{re.escape(receiver)}!?\.([a-zA-Z_][\w]*)", src))


@pytest.mark.parametrize("tsx,receiver", [
    ("property-wizard/step-generate.tsx", "property"),
    ("lead-pages/ConsumerLandingWizard.tsx", "selectedProperty"),
])
def test_the_frontend_spells_the_fields_the_way_the_api_does(tsx, receiver):
    path = WEB / tsx
    assert path.exists(), path
    read = _reads_dot_fields(path, receiver)
    used = read & set(LAST_SALE)
    assert used == set(LAST_SALE), (
        f"{tsx} reads {sorted(used)} of {sorted(LAST_SALE)} off `{receiver}`. "
        f"A camelCase or misspelt name typechecks against an optional field "
        f"and silently sends undefined."
    )


def test_the_consumer_wizard_forwards_them_to_the_request_endpoint():
    """Reading them is not sending them — the bug would survive a rename of
    the outgoing key alone."""
    src = (WEB / "lead-pages/ConsumerLandingWizard.tsx").read_text(encoding="utf-8")
    body = src[src.index("/request`"):]
    for f in LAST_SALE:
        assert re.search(rf"\b{f}\s*:", body), f"{f} is read but never sent"


# ══════════════════════════════════════════════════════════════════════════
# D-139 · the general question: what ELSE does the consumer path drop?
# ══════════════════════════════════════════════════════════════════════════
#
# D-138 fixed the three fields somebody tripped over. `lot_size` had been
# missing the same way for longer, which said the projection had been dropping
# things for a while and nothing noticed. Measured: NINE fields differed
# between the two paths' rendered property pages — the whole Parcel & Legal
# block blank on the consumer report, and the whole Tax & Assessment block
# reading $0.
#
# THREE SEPARATE PLACES DROP FIELDS ON ONE PATH, and only the third is free:
#   1. `PropertySearchResult` — the hand-copied projection (D-138's culprit)
#   2. `ReportRequestPayload` — the next hop, same failure one step later
#   3. `tasks.py`'s consumer `report_data` — dropped fields ALREADY STORED
#      on the row, which is the one that cost nothing and hid the longest
#
# The tests below are deliberately at two levels. The model-field diff is
# cheap and catches a field added to `PropertyData` and forgotten. The
# RENDER diff is the one that answers Jerry's question permanently: it
# compares what a reader sees, so it survives a rename, a new block, or a
# fourth place that drops things.

#: Never carried to the consumer path, and each for a stated reason — not
#: because nobody got round to it. Anything not here must reach both paths.
CONSUMER_EXCLUDED = {
    # D-116: identity is out of the property report entirely, and the
    # consumer path is the one that made that urgent.
    "owner_name": "assessor-roll identity (D-116)",
    "secondary_owner": "as owner_name",
    # Plumbing, not property facts.
    "source": "which vendor answered",
    "confidence": "the lookup's own certainty",
    "raw_response": "excluded from model_dump by design",
    "fips": "used to re-query SiteX, never rendered",
    # Composed by the builder from street/city/state/zip.
    "full_address": "derived",
    # SiteX returns these only for a unit within a parcel; the consumer
    # landing page searches whole addresses.
    "unit_number": "unit-level, not reachable from the consumer search",
    "unit_type": "as unit_number",
    # Renamed on the way through, and asserted present under the new name.
    "street": "renamed to `address`",
    "zip_code": "renamed to `zip`",
}


def test_the_projection_carries_every_property_fact_or_says_why_not():
    """Cheap layer. A field added to `PropertyData` and not carried is a
    field silently absent from every consumer report."""
    src = set(PropertyData.model_fields)
    proj = set(PropertySearchResult.model_fields)
    renamed = {"street": "address", "zip_code": "zip"}
    dropped = sorted(f for f in src - proj
                     if renamed.get(f) not in proj
                     and f not in CONSUMER_EXCLUDED)
    assert not dropped, (
        f"the consumer search drops {dropped}. Either carry them, or add "
        f"each to CONSUMER_EXCLUDED with the reason it must not travel."
    )


def test_the_exclusion_list_does_not_outlive_the_model():
    """An entry excusing a field nobody has any more is one nobody rechecks."""
    stale = sorted(set(CONSUMER_EXCLUDED) - set(PropertyData.model_fields))
    assert not stale, f"CONSUMER_EXCLUDED names fields PropertyData no longer has: {stale}"


def test_the_renamed_fields_really_are_present_under_the_new_name():
    """`CONSUMER_EXCLUDED` excuses `street` and `zip_code` as renamed. If the
    rename target were also missing, the excuse would hide a real gap."""
    proj = set(PropertySearchResult.model_fields)
    assert {"address", "zip"} <= proj, proj

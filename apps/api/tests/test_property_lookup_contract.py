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

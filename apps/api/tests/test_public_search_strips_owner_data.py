"""D-309: the public address search returns no owner, tax, assessment or sale data.

`POST /v1/cma/{code}/search` needs no login: it is the address box on an
agent's public lead page, and anyone can type any address into it. It returned
the assessor's owner name, the assessed, land and improvement values, the tax
bill and year, and the last sale price, date and price per sqft. The page shows
none of that, but the response put all of it in the visitor's browser, which
made the page a free public-records lookup. Same class as #233 (D-304): data
that left through the lookup instead of the report.

Owner decision: the agent's signed-in search (`POST /v1/property/search`) keeps
them. Both are asserted on the real routes, with SiteX replaced by one record
that has every field filled.
"""
import asyncio
from contextlib import contextmanager

import pytest

from api.routes import lead_pages, property as property_routes
from api.services.sitex import PropertyData

#: The fields the ticket names, plus their siblings from the same records.
STRIPPED = (
    "owner_name",
    "assessed_value", "land_value", "improvement_value", "tax_amount", "tax_year",
    "last_sale_price", "last_sale_date", "last_sale_price_per_sqft",
)
OWNER = "Margaret Q. Ownerton"

RECORD = PropertyData(
    apn="1234-567-890", fips="06059", street="14 Cartwheel", city="Irvine",
    state="CA", zip_code="92618", county="Orange", owner_name=OWNER,
    secondary_owner="Second Q. Ownerton",
    bedrooms=4, bathrooms=2.5, sqft=2100, year_built=1998, lot_size=6000,
    property_type="Single Family", latitude=33.68, longitude=-117.82,
    assessed_value=812345, land_value=500111, improvement_value=312234,
    tax_amount=9876.54, tax_year=2025,
    last_sale_price=765432, last_sale_date="2019-06-14", last_sale_price_per_sqft=364.49,
)
#: Values that would only be in the body if a stripped field were.
TELLTALES = (OWNER, "Ownerton", "812345", "500111", "312234", "9876.54", "765432", "2019-06-14", "364.49")


@pytest.fixture
def public_search(monkeypatch):
    @contextmanager
    def no_db():
        yield (None, None)

    async def lookup(address, city_state_zip=""):
        return RECORD

    monkeypatch.setattr(lead_pages, "db_conn", no_db)
    monkeypatch.setattr(lead_pages, "get_agent_by_code",
                        lambda cur, code: {"id": "a1", "landing_page_enabled": True})
    monkeypatch.setattr(lead_pages, "lookup_property", lookup)

    from fastapi.testclient import TestClient
    from api.main import app
    with TestClient(app) as client:
        yield lambda: client.post("/v1/cma/ABC123/search", json={"address": "14 Cartwheel"})


def test_the_public_search_returns_none_of_the_owner_data(public_search):
    r = public_search()
    assert r.status_code == 200, r.text
    results = r.json()
    assert len(results) == 1, "the stub's record did not come back; the test proves nothing"
    leaked = sorted(set(results[0]) & set(STRIPPED))
    assert not leaked, f"the public search returns {leaked} (D-309)"
    for value in TELLTALES:
        assert value not in r.text, f"{value!r} from the owner record is in the public response"


def test_the_public_search_still_returns_the_house(public_search):
    """POSITIVE CONTROL: the page pre-fills these, and they come from the same
    record. If they vanish, the strip took the property facts with it."""
    got = public_search().json()[0]
    assert (got["address"], got["city"], got["zip"]) == ("14 Cartwheel", "Irvine", "92618")
    assert (got["bedrooms"], got["bathrooms"], got["sqft"], got["year_built"]) == (4, 2.5, 2100, 1998)
    assert got["apn"] == "1234-567-890" and got["lot_size"] == 6000


def test_the_agent_search_keeps_them(monkeypatch):
    """The signed-in path is unchanged by owner decision. Called directly, past
    its auth check, so this asserts the route's own output."""
    async def lookup(address, city_state_zip=""):
        return RECORD

    monkeypatch.setattr(property_routes, "lookup_property", lookup)
    monkeypatch.setattr(property_routes, "require_account_id", lambda request: "acct-1")
    resp = asyncio.run(property_routes.search_property(
        property_routes.AddressSearchRequest(address="14 Cartwheel", city_state_zip="Irvine, CA"),
        request=None,
    ))
    data = resp.model_dump()["data"]
    for f in STRIPPED:
        assert data[f] not in (None, ""), f"the agent search lost {f}"
    assert data["owner_name"] == OWNER

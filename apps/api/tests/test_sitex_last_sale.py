"""
D-118 — SiteX carries the last sale in `SaleLoanInfo`, and the parser read
none of it.

THE PROBE'S ANSWER, AND WHAT IT CLOSED
--------------------------------------
`scripts/probe_sitex_sale_history.py` came back with exact keys from
production: `TransferDate 20151223`, `SalesPrice 369000`, `PricePerSQFT 469.0`,
`DocumentNumber 15-1611995`. The subject sold for $369,000 in December 2015,
and that figure has been sitting in `raw_response` on every property report
ever generated, unread, while the page printed the Prop 13 assessment instead.

It also closes an old loose end. The $369,000 in Group A of the six reviewed
PDFs was the one number nobody could account for. It was the real last sale
price all along, reaching the page by a path the current parser stopped
taking — the QA script's literal was correct data, wrongly assumed invented.

WHAT IS DELIBERATELY NOT PARSED
-------------------------------
`SellerName`, `LenderName` and `TitleCompany` sit in the same block. They are
person and counterparty names, out for the same reason the owner block came
out (D-116), and a test below asserts they cannot reach `PropertyData` even if
someone adds them to the model without thinking.
"""
import pytest

from api.services.sitex import PropertyData, SiteXClient, SiteXConfig


@pytest.fixture(scope="module")
def client():
    return SiteXClient(SiteXConfig())


#: Exactly as production returned it, names included, so the redaction test
#: has something real to exclude.
SALE_LOAN_INFO = {
    "TransferDate": 20151223,
    "SalesPrice": 369000,
    "PricePerSQFT": 469.0,
    "DocumentNumber": "15-1611995",
    "SellerName": "A PREVIOUS OWNER",
    "LenderName": "SOME BANK NA",
    "TitleCompany": "A TITLE CO",
}


def _response(sale_info):
    return {"Feed": {"PropertyProfile": {
        "SiteAddress": "1358 5th Street", "SiteCity": "La Verne",
        "SiteState": "CA", "SiteZip": "91750",
        "PropertyCharacteristics": {"BuildingArea": 786},
        "SaleLoanInfo": sale_info,
    }}}


# ── the date, which is where the traps are ────────────────────────────────

@pytest.mark.parametrize("raw,expected", [
    (20151223,   "2015-12-23"),
    ("20151223", "2015-12-23"),
    (20000101,   "2000-01-01"),
    # 0 is the field PRESENT AND EMPTY. Through any epoch-based parser this
    # becomes 1970-01-01 and the report states the home last sold in 1970.
    (0,          None),
    ("0",        None),
    (None,       None),
    ("",         None),
    # A real month, an impossible day. Guessing prints a date nobody recorded.
    (20151332,   None),
    (20150230,   None),   # 30 February
    # Truncated. NOT padded: "in 2015" and "on 1 December 2015" are different
    # claims, and the product may only make the one the feed supports.
    (201512,     None),
    (2015,       None),
    ("abc",      None),
    (-20151223,  None),
    (99999999,   None),   # passes the digit test, fails as a date
])
def test_transfer_date_is_yyyymmdd_and_zero_is_absent(raw, expected):
    assert SiteXClient._sitex_date(raw) == expected


# ── the parse ─────────────────────────────────────────────────────────────

def test_the_last_sale_is_read_from_sale_loan_info(client):
    data = client._parse_response(_response(SALE_LOAN_INFO))
    assert data.last_sale_price == 369000
    assert data.last_sale_date == "2015-12-23"
    assert data.last_sale_price_per_sqft == 469.0
    assert data.last_sale_document == "15-1611995"


def test_no_name_from_the_sale_block_reaches_property_data(client):
    """Same rule as D-116, one layer earlier. Asserted against the whole
    serialised model rather than the three field names, so adding a field
    that happens to carry a name fails here too."""
    dumped = client._parse_response(_response(SALE_LOAN_INFO)).model_dump()
    blob = repr(dumped)
    for name in ("A PREVIOUS OWNER", "SOME BANK NA", "A TITLE CO"):
        assert name not in blob, f"{name!r} reached PropertyData"
    assert not any(k for k in dumped
                   if k.endswith(("seller", "lender", "title_company"))), dumped.keys()


def test_a_property_with_no_recorded_sale_parses_to_none(client):
    data = client._parse_response(_response({}))
    assert data.last_sale_price is None
    assert data.last_sale_date is None
    assert data.last_sale_price_per_sqft is None


def test_a_zero_transfer_date_does_not_become_1970(client):
    """The specific trap: `SalesPrice` present, `TransferDate` 0."""
    data = client._parse_response(_response({"SalesPrice": 369000, "TransferDate": 0}))
    assert data.last_sale_price == 369000
    assert data.last_sale_date is None


def test_price_per_sqft_is_dropped_when_the_price_is_absent(client):
    """A ratio with no numerator is not a datum. It would render `$469` in a
    column whose price cell reads `N/A`."""
    data = client._parse_response(_response({"PricePerSQFT": 469.0}))
    assert data.last_sale_price is None
    assert data.last_sale_price_per_sqft is None


def test_the_fields_survive_model_dump(client):
    """`sitex_data` is `model_dump()`, so a field excluded there never
    reaches the worker however well it parses — which is how `raw_response`
    is deliberately kept out."""
    dumped = client._parse_response(_response(SALE_LOAN_INFO)).model_dump()
    assert dumped["last_sale_price"] == 369000
    assert dumped["last_sale_date"] == "2015-12-23"


def test_the_model_declares_the_fields_the_builder_reads():
    """The D-135 contract, at its source: `sitex_data`'s key set IS this
    model's fields, so a field the builder reads must be declared here."""
    fields = set(PropertyData.model_fields)
    assert {"last_sale_price", "last_sale_date",
            "last_sale_price_per_sqft"} <= fields

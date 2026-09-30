"""
D-145 — `closePrice` and `closeDate` live under `sales`, and five production
sites read them at the top level.

HOW THIS WAS FOUND, AND WHY THAT MATTERS
-----------------------------------------
D-144 was filed on the probe's verdict that `closePrice` was present on 0 of
20 closed listings, and the ticket that followed asked for a count-based
check against a real market before any label changed: if no closed listing
carries a sale price, the comps table can never show one, and that is a
product fact rather than a bug.

The count came back the other way. `tmp/market_snapshot_downey.json` is a
real capture of a real market — 134 listings, 31 of them Closed — and it
reports `median_close_price` of $810,000 over those 31, with escrow days
computed for 31 of 31, which requires `closeDate` and `contractDate` on every
one. The field is not missing. The probe read `r["closePrice"]`, the feed
writes `r["sales"]["closePrice"]`, and 0/20 measured our own reach.

This is the third instance of the shape: `daysOnMarket` at the top level
where the feed puts it under `mls` (D-105), `bathrooms` read as
`property.bathrooms` where the feed carries `bathsFull` (D-106), and now
this. `extract.py` has read `sales.closePrice` correctly since it was
written — so the repo contains both the right path and the wrong one, and
the wrong one is in the four files that build what a reader sees.

WHAT EACH TEST WOULD HAVE CAUGHT
---------------------------------
Every assertion below is driven from `tests/fixtures/listing_closed_minimal.json`,
a captured response, NOT a dict written here. A fixture written to match the
code would have passed against the wrong path — that is how the top-level
read survived: `apps/api/tests/test_comp_close_window.py` builds its rows as
`{"mls": {"closeDate": ...}}` and `{"closeDate": ...}` and asserts one
against the other. Two wrong paths agreeing is the coincidence class from
§0.6, and I wrote it nine days ago.

The window filter is the serious one. `_closed_within_window` keeps a listing
with no close date on purpose — an Active listing has not closed. Reading the
date from a path the feed never uses makes every closed listing look
date-less, so every one is kept, so the filter is a no-op. Its own docstring
says "THE CLIENT-SIDE PASS IS NOT BELT AND BRACES, IT IS THE ACTUAL
GUARANTEE". The guarantee was void, and D-117's derived subtitle has been
asserting a six-month window that nothing in our code enforced.
"""
import ast
import json
from pathlib import Path

import pytest

from api.routes.property import COMP_CLOSE_WINDOW_DAYS, _closed_within_window
from api.schemas.property import normalize_comparable
from api.services.simplyrets import normalize_listing

REPO = Path(__file__).resolve().parents[3]
CLOSED = json.loads(
    (REPO / "tests/fixtures/listing_closed_minimal.json").read_text(encoding="utf-8")
)


def test_the_captured_response_puts_close_fields_under_sales():
    """The premise every other test here rests on, asserted rather than assumed.

    If a future capture moves these to the top level, this fails first and the
    rest of the file's failures are explained by it.
    """
    assert "closePrice" not in CLOSED, "top level should NOT carry closePrice"
    assert "closeDate" not in CLOSED, "top level should NOT carry closeDate"
    assert CLOSED["sales"]["closePrice"] == 1175000
    assert CLOSED["sales"]["closeDate"].startswith("2026-02-18")
    # And it differs from the list price, which is the whole point: showing
    # the list price for a closed comp is not a labelling problem, it is a
    # different number.
    assert CLOSED["listPrice"] != CLOSED["sales"]["closePrice"]


def test_normalize_listing_surfaces_the_close_price():
    out = normalize_listing(CLOSED)
    assert out["close_price"] == 1175000
    assert out["close_date"].startswith("2026-02-18")
    # `price` is what the comps table prints. For a closed listing it is the
    # sale price, not the asking price.
    assert out["price"] == 1175000


def test_normalize_comparable_prefers_the_sale_price():
    out = normalize_comparable(CLOSED)
    assert out["sale_price"] == 1175000
    assert str(out["sold_date"]).startswith("2026-02-18")


def test_window_filter_drops_a_sale_older_than_the_window():
    """The regression that matters: a four-year-old closing must not survive.

    Against the top-level read this listing looks date-less, and a date-less
    listing is kept by design, so it came through.
    """
    old = dict(CLOSED, sales=dict(CLOSED["sales"], closeDate="2021-01-04T08:00:00Z"))
    assert _closed_within_window([old], COMP_CLOSE_WINDOW_DAYS) == []


def test_window_filter_keeps_a_recent_sale_and_a_listing_with_no_close_date():
    """Both directions, so the filter cannot pass by dropping everything."""
    from datetime import datetime, timedelta

    recent_date = (datetime.utcnow().date() - timedelta(days=10)).isoformat()
    recent = dict(CLOSED, sales=dict(CLOSED["sales"], closeDate=recent_date))
    active = {k: v for k, v in CLOSED.items() if k != "sales"}

    assert _closed_within_window([recent], COMP_CLOSE_WINDOW_DAYS) == [recent]
    assert _closed_within_window([active], COMP_CLOSE_WINDOW_DAYS) == [active]


#: Files that build what a reader sees from a raw SimplyRETS row. `tools/` and
#: `scripts/` are excluded deliberately — they are instruments, they already
#: read `sales.*`, and one of them (`dump_market_snapshot.py`) is the capture
#: that proved this defect.
PRODUCTION_SITES = [
    "apps/api/src/api/routes/property.py",
    "apps/api/src/api/services/simplyrets.py",
    "apps/api/src/api/schemas/property.py",
    "apps/worker/src/worker/tasks.py",
]

#: Keys the feed nests under `sales`. A read of one of these off anything that
#: is not a `sales` object is the defect this file exists for.
SALES_NESTED_KEYS = {"closePrice", "closeDate", "contractDate"}


def _sales_key_reads(path: Path):
    """Every `X.get("closePrice")` in a file, with the receiver rendered.

    Source-level rather than behavioural because two of the four sites build
    their dict inline inside a 350-line route — there is nothing importable to
    call, which is the same wall D-140 hit. A guard that reads the source
    catches the fifth site on the day it is written, which is the point: this
    key has now been read from the wrong place five times.
    """
    tree = ast.parse(path.read_text(encoding="utf-8"))
    for node in ast.walk(tree):
        if not (
            isinstance(node, ast.Call)
            and isinstance(node.func, ast.Attribute)
            and node.func.attr == "get"
            and node.args
            and isinstance(node.args[0], ast.Constant)
            and node.args[0].value in SALES_NESTED_KEYS
        ):
            continue
        recv = node.func.value
        # `(sales or {}).get(...)` is the guarded form used throughout.
        if isinstance(recv, ast.BoolOp) and isinstance(recv.op, ast.Or):
            recv = recv.values[0]
        yield node.lineno, ast.unparse(recv), node.args[0].value


#: Receiver names that ARE the sales object. Anything else reaching for a
#: nested key is reading past it. The inline guarded form
#: `(row.get("sales") or {}).get("closeDate")` is accepted too — it unparses
#: to `row.get('sales')` rather than to a bare name, and rejecting it would
#: force a local variable on call sites that do not want one.
SALES_RECEIVERS = {"sales", "sales_obj", "_sales"}


def _is_sales_object(recv: str) -> bool:
    return recv in SALES_RECEIVERS or recv.endswith(".get('sales')")


@pytest.mark.parametrize("rel", PRODUCTION_SITES)
def test_close_fields_are_never_read_off_the_row(rel):
    offenders = [
        (line, recv, key)
        for line, recv, key in _sales_key_reads(REPO / rel)
        if not _is_sales_object(recv)
    ]
    assert not offenders, (
        f"{rel} reads a sales-nested key off something else — the feed puts it "
        f"at row['sales'][key]:\n"
        + "\n".join(f"  line {ln}: {recv}.get({k!r})" for ln, recv, k in offenders)
    )

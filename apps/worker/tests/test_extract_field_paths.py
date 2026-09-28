"""Fields read off a raw SimplyRETS row must be read where the feed puts them.

D-105. `extract.py` read `daysOnMarket` at the top level; the feed carries it at
`mls.daysOnMarket`. The lookup returned None for every listing, always, so every
DOM in the product came from the fallback — and for a closed sale the fallback
computed `close - list`, which is the marketing period PLUS escrow. On this
repo's own captured fixture that is 42 days against the feed's 16.

This is the third read of its kind after `closeDate` at `sales.closeDate` and
postal-code case sensitivity, which is why the assertions below are about PATHS
rather than about DOM: the shape recurs, and a test that only pinned the DOM
number would not catch the next one.

WHAT MAKES THESE TESTS DIFFERENT FROM THE ONES THAT MISSED IT. The repo already
contained the right answer — `tests/test_new_metrics.py:334` reads
`closed_listing["mls"]["daysOnMarket"]` and asserts on it. Two files, one
reading the correct path and one the wrong one, and nothing compared them.
These run the extractor over the same fixtures those tests use, so the two
cannot disagree in silence again.
"""

import json
import sys
from datetime import datetime
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from worker.compute.extract import PropertyDataExtractor  # noqa: E402

FIXTURES = ROOT / "tests/fixtures"


def fixture(name):
    return json.loads((FIXTURES / f"{name}.json").read_text())


def extracted(row):
    return PropertyDataExtractor([row]).run()[0]


def test_days_on_market_comes_from_the_feed_not_from_close_minus_list():
    """The regression, at the exact discrepancy that hid the defect."""
    row = fixture("listing_closed_minimal")
    feed = row["mls"]["daysOnMarket"]
    parse = lambda s: datetime.fromisoformat(s.replace("Z", ""))
    close_minus_list = (parse(row["sales"]["closeDate"]) - parse(row["listDate"])).days

    assert feed != close_minus_list, (
        "this fixture no longer distinguishes the two quantities, so it cannot "
        "catch the defect it was chosen for — pick one where they differ"
    )
    assert extracted(row)["days_on_market"] == feed, (
        f"DOM is {extracted(row)['days_on_market']}, the feed says {feed}. "
        f"close - list is {close_minus_list} — marketing plus escrow, which is "
        f"not days on market (D-105)."
    )


def test_the_feed_value_is_read_rather_than_re_derived():
    """THE PATH, not the number — and the test above cannot check it.

    Reverting the fix to the old top-level-only read was applied as a
    regression and the test above PASSED: with the feed value unread, the code
    falls through to the contract-derived branch, which on this fixture
    computes the same 16. Two independent routes agreeing on one input, so the
    assertion could not tell "read it" from "worked it out".

    Feeds report DOM excluding off-market days, so the two legitimately differ.
    Setting the feed's value to something neither derivation can produce makes
    the read the only way to get it.
    """
    row = fixture("listing_closed_minimal")
    parse = lambda s: datetime.fromisoformat(s.replace("Z", ""))
    contract_minus_list = (parse(row["sales"]["contractDate"]) - parse(row["listDate"])).days
    close_minus_list = (parse(row["sales"]["closeDate"]) - parse(row["listDate"])).days

    sentinel = 7
    assert sentinel not in (contract_minus_list, close_minus_list)
    row["mls"]["daysOnMarket"] = sentinel

    assert extracted(row)["days_on_market"] == sentinel, (
        f"the extractor produced {extracted(row)['days_on_market']} where the "
        f"feed says {sentinel}. It is deriving the value instead of reading it "
        f"— which is D-105, and it agrees with the feed only by coincidence on "
        f"listings where nothing went off-market."
    )


def test_a_closed_sale_with_no_feed_value_reports_list_to_contract():
    """Derive the SAME quantity rather than a different one."""
    row = fixture("listing_closed_minimal")
    row["mls"] = {k: v for k, v in row["mls"].items() if k != "daysOnMarket"}
    parse = lambda s: datetime.fromisoformat(s.replace("Z", ""))
    expected = (parse(row["sales"]["contractDate"]) - parse(row["listDate"])).days
    assert extracted(row)["days_on_market"] == expected


def test_a_closed_sale_with_neither_reports_nothing_rather_than_a_different_quantity():
    """D-056's rule. `close - list` is available and is not days on market, so
    it is not substituted; the table renders None as '-'."""
    row = fixture("listing_closed_minimal")
    row["mls"] = {k: v for k, v in row["mls"].items() if k != "daysOnMarket"}
    row["sales"] = {k: v for k, v in row["sales"].items() if k != "contractDate"}
    assert extracted(row)["days_on_market"] is None


def test_an_active_listing_still_counts_days_so_far():
    """The fallback that is correct: a listing that has not sold has been on the
    market since it was listed. Only closed rows changed."""
    row = fixture("listing_active_minimal")
    row["mls"] = {k: v for k, v in row["mls"].items() if k != "daysOnMarket"}
    parse = lambda s: datetime.fromisoformat(s.replace("Z", ""))
    expected = (datetime.now() - parse(row["listDate"])).days
    assert extracted(row)["days_on_market"] == pytest.approx(expected, abs=1)


@pytest.mark.parametrize("name", ["listing_closed_minimal", "listing_active_minimal"])
def test_every_extracted_field_that_the_feed_carries_is_actually_populated(name):
    """The sweep, as a standing gate rather than a one-off script.

    A field the feed provides and the extractor emits as None is the D-105
    shape: a read at a path the feed does not use. It fails silently because
    every template guards with `{% if %}`, so the value simply disappears.

    `bathrooms` is expected to fail here — D-106, the feed carries `bathsFull`
    and `bathsHalf` and nothing named `bathrooms` — and is listed so the gate
    passes while naming what is still broken. Removing a name from this set
    without fixing the read is the thing this is here to stop.
    """
    known_broken = {"bathrooms"}
    row = fixture(name)
    out = extracted(row)
    # Fields whose source the feed demonstrably carries for this fixture.
    expected_present = {
        "mls_id": row.get("mlsId"),
        "list_date": row.get("listDate"),
        "status": (row.get("mls") or {}).get("status"),
        "list_price": row.get("listPrice"),
        "sqft": (row.get("property") or {}).get("area"),
        "bedrooms": (row.get("property") or {}).get("bedrooms"),
        "bathrooms": (row.get("property") or {}).get("bathsFull"),
        "days_on_market": (row.get("mls") or {}).get("daysOnMarket"),
        "city": (row.get("address") or {}).get("city"),
        "zip_code": (row.get("address") or {}).get("postalCode"),
    }
    missing = sorted(
        field for field, feed_value in expected_present.items()
        if feed_value is not None and out.get(field) is None
    )
    assert missing == sorted(known_broken & set(missing)), (
        f"{name}: the feed carries these and the extractor dropped them: "
        f"{[m for m in missing if m not in known_broken]}"
    )

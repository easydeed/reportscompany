"""
D-074 — closed sales are narrowed by CLOSE date, and an unknown one is not a sale.

WHAT WAS WRONG
--------------
`market_trends.py` believed SimplyRETS has no close-date filter and worked
around it with `minlistdate`, 210 days. A cutoff on the wrong column: a home
listed 300 days ago and sold last week is a closed sale inside every window
that matters, and the API excluded it.

**The loss is not random.** Long days-on-market listings are exactly the ones
that take more than seven months to sell, so the rows dropped were
systematically the slow ones — the sales rate came out too LOW and months of
supply too HIGH, never the other way. High supply flips the market-condition
badge to buyer's-market and produces copy about homes taking longer to sell. A
seller reading that page prices lower than the market warrants. That has been
shipping on the property report.

`minclosedate` exists and filters, confirmed against the production feed.

THE DEFENSIVE POSTURE, AND WHY IT STAYS
---------------------------------------
The API filter is now sent AND the client-side split by `close_date` remains.
That is not belt-and-braces for its own sake: the corroborating half of D-074 is
still open — the probe has shown `minclosedate` filters, not yet that it filters
correctly at an in-range date. Under either answer the published numbers are
right. If the parameter is honoured the client-side pass is a no-op; if it is
not, the client-side pass is what makes the window true.

THE UNKNOWN CLOSE DATE
----------------------
The production probe found a Closed record with **no `closeDate` at all**
(mlsId=206984498) that leaked through the API's own future-date filter. Such a
row is not a sale that happened in this window — it is a sale whose date is
unknown, and counting it would inflate the sales rate and deflate months of
supply: the D-074 error with the sign flipped. It must be excluded, and it must
not crash the comparison.
"""
import os
import sys
from datetime import datetime, timedelta
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

os.environ.setdefault("DATABASE_URL", "postgresql://fake/fake")
os.environ.setdefault("REDIS_URL", "redis://localhost:6379/0")

from worker.compute import market_trends  # noqa: E402

NOW = datetime.now()


def listing(days_ago_listed, days_ago_closed, price=500_000, sqft=1800, **over):
    """
    One extracted closed listing. `days_ago_closed=None` means the feed gave us
    a Closed record with no close date — the production case above.
    """
    row = {
        "status": "Closed",
        "city": "Glendora",
        "close_price": price,
        "list_price": price,
        "sqft": sqft,
        "days_on_market": days_ago_listed - (days_ago_closed or 0),
        "close_date": None if days_ago_closed is None
        else NOW - timedelta(days=days_ago_closed),
        "list_date": NOW - timedelta(days=days_ago_listed),
    }
    row.update(over)
    return row


@pytest.fixture
def feed(monkeypatch):
    """
    Replaces the vendor call and records what it was asked for.

    The fake returns whatever it is given REGARDLESS of the date params — which
    is the point. A fake that honoured `minclosedate` would make the
    client-side pass untestable, and the client-side pass is the half that has
    to hold when the API's behaviour is still in question.
    """
    calls = []

    def install(closed, active=(), pending=()):
        def fake_fetch(params, limit=500):
            calls.append(dict(params))
            status = params.get("status")
            if status == "Closed":
                return list(closed)
            if status == "Active":
                return list(active)
            return list(pending)

        # PATCH THE SOURCE MODULE, NOT THIS ONE. `market_trends` imports
        # `fetch_properties` INSIDE the function (line 77, to avoid a circular
        # import), so the name never exists as a module attribute here and
        # patching `market_trends.fetch_properties` fails outright. The
        # function-local import resolves through `worker.vendors.simplyrets`
        # every call, so that is where the stand-in has to go.
        import worker.vendors.simplyrets as vendor
        monkeypatch.setattr(vendor, "fetch_properties", fake_fetch)

        # extract.py is exercised elsewhere; the rows above are already in its
        # OUTPUT shape, so the extractor is the identity here. It is
        # `PropertyDataExtractor(rows).run()`, imported function-locally like
        # the fetch, so the stand-in goes on its source module too.
        import worker.compute.extract as extract

        class _Identity:
            def __init__(self, rows):
                self._rows = list(rows)

            def run(self):
                return self._rows

        monkeypatch.setattr(extract, "PropertyDataExtractor", _Identity)

        # `_filter_by_city` drops rows whose city does not match; every row the
        # helper above builds says Glendora, so it is a no-op — but it is the
        # real function, not stubbed, so a change there would show up here.
        return calls

    return install


def closed_query(calls):
    return next(c for c in calls if c.get("status") == "Closed")


# ── the query ───────────────────────────────────────────────────────────────

def test_the_closed_query_filters_on_close_date_not_list_date(feed):
    """
    THE REGRESSION. `minlistdate` is a cutoff on the wrong column, and the rows
    it drops are systematically the slow-selling ones.
    """
    calls = feed(closed=[listing(30, 10) for _ in range(5)],
                 active=[{"status": "Active", "city": "Glendora", "list_price": 500_000}])
    market_trends.fetch_and_compute_market_trends("Glendora")

    q = closed_query(calls)
    assert "minlistdate" not in q, (
        "the closed query still narrows by list date; a home listed 300 days "
        "ago and sold last week is excluded, and months of supply comes out high"
    )
    assert "minclosedate" in q, "the closed query has no close-date filter at all"


def test_the_window_is_the_one_the_split_actually_reads(feed):
    """
    180 days, because the split below uses 0-90 as the current period and
    90-180 as the prior one. A wider window fetches rows nothing reads; a
    narrower one silently empties the prior period and kills the comparisons.
    """
    calls = feed(closed=[listing(30, 10) for _ in range(5)],
                 active=[{"status": "Active", "city": "Glendora", "list_price": 500_000}])
    market_trends.fetch_and_compute_market_trends("Glendora")

    cutoff = datetime.strptime(closed_query(calls)["minclosedate"], "%Y-%m-%d")
    days = (NOW - cutoff).days
    assert 178 <= days <= 182, f"minclosedate is {days} days back, not ~180"


# ── the sale that used to be dropped ────────────────────────────────────────

def test_a_long_dom_recent_sale_is_counted(feed):
    """
    THE EXACT ROW D-074 IS ABOUT: listed 300 days ago, sold 10 days ago. Under
    `minlistdate=210d` the API never returned it. It belongs in the current
    period.
    """
    rows = [listing(300, 10), listing(280, 20), listing(30, 15)]
    calls = feed(closed=rows,
                 active=[{"status": "Active", "city": "Glendora", "list_price": 500_000}])
    result = market_trends.fetch_and_compute_market_trends("Glendora")

    assert result is not None, (
        "the page was dropped; all three sales are inside the 90-day window"
    )
    assert "minlistdate" not in closed_query(calls)


# ── the unknown close date ──────────────────────────────────────────────────

def test_a_closed_record_with_no_close_date_is_excluded(feed):
    """
    Not counted, and not a crash. The production probe found one of these
    leaking through the API's own filter (mlsId=206984498). Counting it would
    inflate the sales rate and deflate months of supply.

    Asserted through the guard that drops the page below MIN_CLOSED_TO_RENDER:
    with three real sales the page renders; replace one with an undated row and
    it must not.
    """
    active = [{"status": "Active", "city": "Glendora", "list_price": 500_000}]

    feed(closed=[listing(40, 10), listing(50, 20), listing(60, 30)], active=active)
    assert market_trends.fetch_and_compute_market_trends("Glendora") is not None, (
        "precondition: three dated sales are enough to render"
    )

    feed(closed=[listing(40, 10), listing(50, 20), listing(60, None)], active=active)
    assert market_trends.fetch_and_compute_market_trends("Glendora") is None, (
        "a Closed record with no closeDate was counted toward the sales rate"
    )


def test_an_undated_record_does_not_raise(feed):
    """
    The other half. Excluding it by crashing is not excluding it — the whole
    report would fail rather than the one row being ignored.
    """
    feed(closed=[listing(40, None) for _ in range(6)],
         active=[{"status": "Active", "city": "Glendora", "list_price": 500_000}])
    assert market_trends.fetch_and_compute_market_trends("Glendora") is None


def test_a_string_close_date_is_still_parsed(feed):
    """
    `extract.py` returns datetimes, and the split guards against strings in case
    that changes. A guard nobody exercises is a guard nobody knows is broken.
    """
    rows = [listing(40, 10), listing(50, 20), listing(60, 30)]
    for r in rows:
        r["close_date"] = r["close_date"].isoformat() + "Z"
    feed(closed=rows, active=[{"status": "Active", "city": "Glendora", "list_price": 500_000}])
    assert market_trends.fetch_and_compute_market_trends("Glendora") is not None, (
        "ISO-string close dates were dropped, so every sale fell out of the window"
    )


# ── the defensive posture ───────────────────────────────────────────────────

def test_the_client_side_split_still_applies_when_the_api_does_not_filter(feed):
    """
    THE HALF THAT IS NOT SETTLED. The probe has shown `minclosedate` filters;
    it has not yet shown it filters correctly at an in-range date. The fake
    here ignores the parameter entirely — which is the pessimistic answer — and
    the window must still come out right.

    Three sales inside 90 days and three well outside 180. If the client-side
    pass were removed on the strength of the API filter, the out-of-window rows
    would be counted and the sales rate would be double what it should be.
    """
    inside = [listing(40, 10), listing(50, 20), listing(60, 30)]
    ancient = [listing(900, 800), listing(950, 850), listing(1000, 900)]
    feed(closed=inside + ancient,
         active=[{"status": "Active", "city": "Glendora", "list_price": 500_000}])

    result = market_trends.fetch_and_compute_market_trends("Glendora")
    assert result is not None

    # `sample_size` is the 90-day closed count — named, not guessed at. The
    # first version of this assertion scanned the result for any int under a key
    # containing "closed" and accepted 3 anywhere in it, which would have passed
    # on a coincidence and failed on a rename with a useless message.
    assert result["sample_size"] == 3, (
        f"the 90-day window came out as {result['sample_size']} sales, not 3. "
        f"Six were returned by the feed and three of them closed over two years "
        f"ago — if the client-side split were removed on the strength of the API "
        f"filter, the sales rate would be double what it should be and months of "
        f"supply half."
    )

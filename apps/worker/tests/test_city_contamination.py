"""
D-087 — a count of a fuzzy query is a count of the wrong city.

WHAT IS AND IS NOT WRONG
------------------------
`_location` sends `q=<city>`, SimplyRETS' free-text search over MLS number,
address, city and ZIP. Measured against the demo feed:

    cities=Houston  ->  X-Total-Count 12, every row in Houston
    q=Houston       ->  X-Total-Count 13, twelve Houston + one TOMBALL
    Cities=Houston  ->  X-Total-Count 65, the whole feed (D-084)

The ROWS were never the problem. Every builder runs `_filter_by_city` before
computing anything, so the listings table, the medians, the DOM and
`counts["Active"]` have always excluded the Tomball row. That defence predates
this ticket and the first test below pins it, because it is what makes the rest
of the posture safe.

What cannot be defended that way is `count=true`. The answer is a header — one
number covering whatever the API matched — and there is nothing to filter. So on
a city report the count and the rows describe DIFFERENT POPULATIONS, and the
count is the months-of-supply numerator. That is D-056's mistake arriving by a
new route: a numerator over one set, a listings table over another, and no way
for a reader to see it.

WHY NOT JUST SEND `cities`
--------------------------
Because D-084 measured what SimplyRETS does with a parameter NAME it does not
recognise: accepts it, ignores it, returns the whole feed with a 200. The code's
own comment says `cities` "may not be supported by all accounts". On an
unsupporting account, swapping `q` for `cities` turns one stray Tomball listing
into every listing in the MLS — a report on 70,000 homes, silently. The swap
waits for the production probe, which already canaries `cities`.

So: keep `q`, keep cleaning the rows, and stop counting.
"""
import os
import sys
from datetime import datetime, timedelta
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

os.environ.setdefault("DATABASE_URL", "postgresql://fake/fake")
os.environ.setdefault("REDIS_URL", "redis://localhost:6379/0")

from worker.report_builders import build_inventory_result, _filter_by_city  # noqa: E402
from worker.query_builders import (  # noqa: E402
    build_inventory_active,
    location_is_exact,
)
from worker.vendors import simplyrets  # noqa: E402

NOW = datetime.now()


@pytest.fixture
def city_search_enabled(monkeypatch):
    """
    Re-import `query_builders` with credentials that enable city search, and put
    it back afterwards.

    THIS FIXTURE EXISTS BECAUSE THE FIRST VERSION OF THIS FILE DID THE LAZY
    THING AND IT PASSED. `ALLOW_CITY_SEARCH` is a module-level constant read
    from `SIMPLYRETS_USERNAME` at import time, and `_location` emits no location
    filter at all when it is False. Setting the variable at the top of this
    module is enough when the file runs alone — and useless in the full suite,
    where some earlier test has already imported `query_builders` in demo mode.
    Isolated: green. Whole suite: red. The environment decided, and nothing in
    the test said so.

    So the test declares the mode it needs instead of inheriting one, which is
    the same correction the root suite needs (D-054) stated as code. The reload
    on the way out matters as much as the one on the way in: leaving the module
    flipped would hand the next test file a different `query_builders` than it
    imported, and that is this bug with the blame moved.
    """
    import importlib
    import worker.query_builders as qb

    monkeypatch.setenv("SIMPLYRETS_USERNAME", "notthedemoaccount")
    importlib.reload(qb)
    assert qb.ALLOW_CITY_SEARCH, "precondition: city search must be on"
    yield qb
    monkeypatch.undo()
    importlib.reload(qb)


def listing(city, price=500_000, days_ago=5, status="Active", dom=10):
    return {
        "status": status,
        "city": city,
        "list_price": price,
        "days_on_market": dom,
        "list_date": NOW - timedelta(days=days_ago),
    }


def build(listings, city="Houston", **ctx):
    context = {"city": city, "lookback_days": 30}
    context.update(ctx)
    return build_inventory_result(listings, context)


# ── the rows: the defence that already existed ──────────────────────────────

def test_the_tomball_listing_does_not_enter_a_houston_report():
    """
    THE MEASURED CASE. `q=Houston` returns twelve Houston listings and one from
    Tomball whose text mentions Houston. The Tomball row must not reach the
    table, the count or any median.
    """
    rows = [listing("Houston", 400_000, dom=10) for _ in range(12)]
    rows.append(listing("Tomball", 9_000_000, dom=900))

    result = build(rows, city="Houston")

    assert result["counts"]["Active"] == 12, (
        "the Tomball listing was counted as Houston inventory"
    )
    # `median_dom` rather than the asking median, because it exists on this
    # branch's base. The point is the same: a metric computed over the rows
    # must not move when a foreign row is in the fetch.
    assert result["metrics"]["median_dom"] == 10, (
        "a listing from another city moved a published metric"
    )
    assert all(l.get("city") == "Houston" for l in result["listings_sample"]), (
        "a listing from another city is in the table"
    )


def test_the_filter_is_case_insensitive_but_not_fuzzy_itself():
    """
    Replacing one fuzzy match with another would not be a fix. `HOUSTON` is the
    same city; `Houston Heights` and `South Houston` are not, and a substring
    or prefix test would readmit exactly the rows `q` wrongly matched.
    """
    kept = _filter_by_city([listing("HOUSTON"), listing("houston")], "Houston")
    assert len(kept) == 2

    dropped = _filter_by_city(
        [listing("Houston Heights"), listing("South Houston"), listing("Tomball")],
        "Houston",
    )
    assert dropped == [], (
        "the city filter matched a different city by substring, which is the "
        "same error as `q` and would undo the whole defence"
    )


def test_a_zip_report_is_not_city_filtered():
    """
    When the request is by ZIP, `city` carries the ZIP itself and the API has
    already filtered exactly. Filtering again on a city field that will never
    equal "77018" would empty every ZIP report.
    """
    rows = [listing("Houston"), listing("Tomball")]
    assert _filter_by_city(rows, "77018") == rows


# ── the count: what the row filter cannot reach ─────────────────────────────

def test_a_city_query_is_not_an_exact_location(city_search_enabled):
    """The real query, from the real builder — not a hand-written dict."""
    q = city_search_enabled.build_inventory_active({"city": "Houston"})
    assert q.get("q") == "Houston", f"expected a fuzzy city filter, got {q}"
    assert not city_search_enabled.location_is_exact(q), (
        "a free-text city query was treated as countable; its X-Total-Count "
        "includes listings from other cities"
    )


def test_a_zip_query_is_an_exact_location():
    """
    D-081 MUST SURVIVE THIS FIX. `postalCodes` was measured exact
    (`postalCodes=77018` -> 5 rows, all in that ZIP), so ZIP reports keep the
    exact count and keep the removed 1000-row ceiling.
    """
    q = build_inventory_active({"zips": ["77018", "77019"]})
    assert q.get("postalCodes") == "77018,77019"
    assert location_is_exact(q)


def test_no_location_filter_at_all_is_not_exact():
    """
    Demo mode sends no location filter. "The whole feed" is not "the requested
    city" — it is the same error as the Tomball row, only larger.
    """
    assert not location_is_exact({"status": "Active", "limit": 1000})


def test_the_count_request_is_not_sent_for_a_fuzzy_query(monkeypatch, city_search_enabled):
    """
    Not merely discarded — not sent. A request whose answer must be thrown away
    is a call spent on nothing.
    """
    calls = []
    monkeypatch.setattr(
        simplyrets, "count_properties", lambda p: calls.append(p) or 99999
    )

    fuzzy = city_search_enabled.build_inventory_active({"city": "Houston"})
    assert simplyrets.count_properties_if_exact(fuzzy) is None, (
        "a fuzzy query's X-Total-Count was published as this city's inventory"
    )
    assert calls == [], f"a count request was sent anyway: {calls}"


def test_the_count_request_is_still_sent_for_an_exact_query(monkeypatch):
    """The other half. A guard that refuses everything is not a guard."""
    calls = []
    monkeypatch.setattr(
        simplyrets, "count_properties", lambda p: calls.append(p) or 4321
    )

    exact = build_inventory_active({"zips": ["77018"]})
    assert simplyrets.count_properties_if_exact(exact) == 4321
    assert len(calls) == 1


# ── what the report says before and after ───────────────────────────────────

def test_the_numerator_falls_back_to_the_city_filtered_rows():
    """
    None is not zero and not an error — it is the path that already handled "the
    feed did not return the header", and it lands on the CITY-FILTERED row
    count. The fallback has to be the cleaned population, or the fix would
    reintroduce the contamination it removes.
    """
    rows = [listing("Houston") for _ in range(12)] + [listing("Tomball")]
    result = build(rows, city="Houston", active_total=None)

    assert result["metrics"]["total_active"] == 12, (
        "the fallback counted rows before the city filter, so Tomball is back"
    )


def test_before_and_after_on_one_report():
    """
    THE WHOLE TICKET IN ONE ASSERTION, using the measured demo numbers.

    Twelve Houston actives, one Tomball, three closed sales. The hero KPI and
    the months-of-supply numerator used to come from the header (13); they now
    come from the cleaned rows (12). Both are stated so a reader can see the
    size of the error rather than take "contaminated" on trust.
    """
    rows = [listing("Houston") for _ in range(12)] + [listing("Tomball")]

    contaminated = build(rows, city="Houston", active_total=13)
    corrected = build(rows, city="Houston", active_total=None)

    assert contaminated["metrics"]["total_active"] == 13
    assert corrected["metrics"]["total_active"] == 12

    # And the count beside it was always 12 — which is the tell. A report whose
    # hero KPI says 13 over a table of 12 was already visibly inconsistent; the
    # months-of-supply numerator carried the same 13 invisibly.
    assert contaminated["counts"]["Active"] == corrected["counts"]["Active"] == 12


def test_a_truncated_fetch_still_refuses_to_publish_supply():
    """
    Losing the exact count costs the removed ceiling back on city reports, and
    that has to fail LOUDLY rather than publish a floor as a total. D-078's
    flag already does this; the fix must not route around it.
    """
    rows = [listing("Houston") for _ in range(1000)]
    result = build(
        rows, city="Houston", active_total=None, active_was_truncated=True
    )
    assert result["metrics"]["months_of_inventory"] is None, (
        "months of supply was published from a floor presented as a total"
    )

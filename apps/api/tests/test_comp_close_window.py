"""
D-117 — the comparables query sent no date filter while every theme printed
"sold within the last 12 months".

WHY THE TEST DRIVES THE ENDPOINT RATHER THAN A HELPER
------------------------------------------------------
The params are assembled by `_build_params`, which is a closure defined inside
`get_comparables`. There is nothing importable to call. Testing an
extracted copy would prove the copy — §0.6, *a test that supplies its own input
proves the consumer and says nothing about the producer*, which is how D-113
went unseen for three weeks.

So the real route runs, with `simplyrets_fetch_properties` replaced by a spy
that records every params dict the six-level fallback ladder sends. What is
asserted is what the vendor would have received.

THE WINDOW IS NOT SENT ON EVERY QUERY, AND THAT IS THE POINT
-------------------------------------------------------------
The wizard defaults to ACTIVE listings (property-wizard.tsx:53). An active
listing has no close date, so `minclosedate` on that query either empties the
result or is ignored, and neither is a filter. `Active,Closed` is worse:
SimplyRETS applies the parameter to the whole response, so it would silently
drop the active half of a deliberately mixed search.
"""
import pytest
from unittest.mock import patch
from fastapi.testclient import TestClient

from api.main import app
from api.routes.property import (
    COMP_CLOSE_WINDOW_DAYS,
    _closed_since,
    _closed_within_window,
)

client = TestClient(app)


@pytest.fixture
def mock_auth():
    client.headers.update({"X-Demo-Account": "test-account-id"})
    yield
    client.headers.pop("X-Demo-Account", None)


@pytest.fixture(autouse=True)
def _no_database():
    """`AuthContextMiddleware` opens a pooled connection on every request
    (authn.py:103, 147, 181, 283). With no database reachable, `db.py`'s
    `timeout=10` means each of these tests waits ten seconds for a connection
    it will never get — measured at 10.01s per test before this fixture, a
    sixty-second tax on CI for a module that tests query parameters.

    The cursor answers every lookup with nothing, which is all the comparables
    route needs: it reads `request.state.account_id`, set from the
    `X-Demo-Account` header before any of these queries run.
    """
    from contextlib import contextmanager
    from unittest.mock import MagicMock
    from api.middleware import authn as _authn

    @contextmanager
    def _fake_conn(*a, **k):
        cur = MagicMock()
        cur.fetchone.return_value = None
        cur.fetchall.return_value = []
        yield cur

    real = _authn.db_conn_autocommit
    _authn.db_conn_autocommit = _fake_conn
    try:
        yield
    finally:
        _authn.db_conn_autocommit = real


@pytest.fixture(autouse=True)
def _rate_limiter_without_redis():
    """D-094: the limiter calls Redis unguarded, so every request 500s without one."""
    from api.middleware import authn

    store = {}

    class _FakeRedis:
        def get(self, k):
            return store.get(k)

        def setex(self, k, _ttl, v):
            store[k] = v

        def incr(self, k):
            store[k] = str(int(store.get(k, 0)) + 1)
            return int(store[k])

        def expire(self, k, _ttl):
            return True

    real = authn.redis.from_url
    authn.redis.from_url = lambda *a, **k: _FakeRedis()
    app.middleware_stack = app.build_middleware_stack()
    try:
        yield
    finally:
        authn.redis.from_url = real
        app.middleware_stack = app.build_middleware_stack()


BODY = {
    "address": "1358 5th Street",
    "city_state_zip": "La Verne, CA 91750",
    "latitude": 34.1008,
    "longitude": -117.7678,
    "beds": 2,
    "baths": 1.0,
    "sqft": 786,
    "property_type": "Single Family Residential",
}


def _call(status, listings=()):
    """Run the real endpoint and return every params dict the ladder sent.

    `listings` may be a list (returned for every level) or a callable taking
    the params dict — which is how a real feed behaves, and the only way to
    test that a wider window surfaces sales a narrower one did not. A fixed
    list makes every level identical, so the ladder can never be seen to gain
    anything, and a test written against it would assert the wrong thing
    confidently.
    """
    sent = []

    async def _spy(params, limit=None):
        sent.append(dict(params))
        return list(listings(params) if callable(listings) else listings)

    with patch("api.routes.property.simplyrets_fetch_properties", _spy):
        res = client.post("/v1/property/comparables", json={**BODY, "status": status})
    assert res.status_code == 200, res.text
    assert sent, "the ladder sent no query at all"
    return sent, res.json()


# ── the parameter ───────────────────────────────────────────────────────────

def test_a_closed_search_sends_minclosedate_at_the_six_month_mark(mock_auth):
    sent, _ = _call("Closed")
    # The first six levels. The seventh deliberately widens (D-132) and has
    # its own tests below; asserting six months on every level would have
    # made this pass only while L6 did not exist.
    for params in sent[:6]:
        assert params["minclosedate"] == _closed_since(COMP_CLOSE_WINDOW_DAYS)


def test_every_ladder_level_carries_the_window(mock_auth):
    """A later level widens the search. It must not widen the window with it."""
    sent, _ = _call("Closed")
    assert len(sent) > 1, "the ladder stopped at one level; widen the test, not the window"
    assert all("minclosedate" in p for p in sent)


def test_it_is_minclosedate_and_never_mindate(mock_auth):
    """D-075 measured `mindate` being accepted and doing nothing, silently."""
    sent, _ = _call("Closed")
    for params in sent:
        assert "mindate" not in params


@pytest.mark.parametrize("status", ["Active", "All"])
def test_a_search_that_includes_active_listings_sends_no_close_window(status, mock_auth):
    sent, _ = _call(status)
    for params in sent:
        assert "minclosedate" not in params, (
            f"status={status!r} resolves to {params['status']!r}; a close-date "
            "filter on a query that asks for active listings drops them or is "
            "ignored, and neither is a filter"
        )


# ── the client-side pass, which is the actual guarantee ────────────────────

def _closed_listing(date):
    # `sales.closeDate`. Every fixture in this file used to say
    # `mls.closeDate`, and the code under test used to read `mls.closeDate`
    # first — so the filter and its tests agreed with each other and both
    # disagreed with the feed, which nests the field under `sales` (D-145).
    # Two wrong paths agreeing is not a test. Checked against
    # `tests/fixtures/listing_closed_minimal.json`, which is captured.
    return {"mlsId": date, "sales": {"closeDate": date}}


def test_a_sale_outside_the_window_is_dropped_even_if_the_vendor_returns_it():
    inside = _closed_listing(_closed_since(10))
    outside = _closed_listing(_closed_since(COMP_CLOSE_WINDOW_DAYS + 30))
    kept = _closed_within_window([inside, outside], COMP_CLOSE_WINDOW_DAYS)
    assert kept == [inside]


def test_a_listing_with_no_close_date_is_kept():
    """An active listing has not closed. Dropping it here would empty an
    Active comps search through a filter that does not apply to it."""
    active = {"mlsId": "A1", "listPrice": 500000}
    assert _closed_within_window([active], COMP_CLOSE_WINDOW_DAYS) == [active]


def test_the_close_date_is_read_from_the_one_place_the_feed_writes_it():
    """The replacement for a test that asserted the opposite and was wrong.

    It used to require that `mls.closeDate` and a top-level `closeDate` were
    BOTH honoured, reasoning from D-105 that the feed might use either. It
    uses neither: `tests/fixtures/listing_closed_minimal.json` and a 134-row
    capture of the Downey market both carry `sales.closeDate` and nothing
    else. Honouring the two invented paths is what let the real one go
    unread, so the assertion is inverted — a date at either of them is a
    listing whose close date we did not find, and a listing with no close
    date is kept.
    """
    old = _closed_since(COMP_CLOSE_WINDOW_DAYS + 30)
    assert _closed_within_window([{"sales": {"closeDate": old}}], COMP_CLOSE_WINDOW_DAYS) == []
    for invented in ({"mls": {"closeDate": old}}, {"closeDate": old}):
        assert _closed_within_window([invented], COMP_CLOSE_WINDOW_DAYS) == [invented], (
            "a path the feed does not use was treated as a close date"
        )


def test_the_endpoint_drops_an_out_of_window_sale_the_vendor_returned(mock_auth):
    """The two halves together, through the real route."""
    fresh = {"mlsId": "NEW", "sales": {"closeDate": _closed_since(10)},
             "property": {"type": "RES"}, "address": {"full": "1 Fresh St"},
             "geo": {"lat": 34.1008, "lng": -117.7678}}
    stale = {"mlsId": "OLD", "sales": {"closeDate": _closed_since(4 * 365)},
             "property": {"type": "RES"}, "address": {"full": "2 Stale St"},
             "geo": {"lat": 34.1008, "lng": -117.7678}}
    _, body = _call("Closed", [fresh, stale])
    addresses = [c["address"] for c in body["comparables"]]
    assert "1 Fresh St" in addresses
    assert "2 Stale St" not in addresses, (
        "a sale from four years ago reached a report headed 'sold in the last "
        "6 months' — this is D-117"
    )


# ── the two deployments must agree ─────────────────────────────────────────

def test_the_api_and_the_worker_agree_on_the_window():
    """API and worker are separate deployments, so the constant cannot be
    shared. A query window and a printed window that drift apart IS D-117, so
    the agreement is asserted rather than hoped for."""
    import sys
    from pathlib import Path
    sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "worker/src"))
    from worker.property_builder import PropertyReportBuilder

    assert PropertyReportBuilder.COMP_CLOSE_WINDOW_DAYS == COMP_CLOSE_WINDOW_DAYS


# ── what the window costs, measured rather than asserted ───────────────────

def test_the_ladder_widens_in_response_to_the_window(mock_auth):
    """The window filter runs BEFORE the `>= FALLBACK_MIN` check, so a thin
    result caused by the window escalates the ladder exactly as a thin result
    caused by the sqft filter does.

    This is the whole of the ladder's compensation, and it is worth being
    precise about its limit: the six levels widen sqft tolerance, bed range,
    subtype and radius. **Not one of them widens time.** So the window is a
    hard floor the ladder cannot climb past — see D-132.
    """
    stale = {"mlsId": "OLD", "sales": {"closeDate": _closed_since(4 * 365)},
             "property": {"type": "RES"}, "address": {"full": "2 Stale St"},
             "geo": {"lat": 34.1008, "lng": -117.7678}}
    sent, body = _call("Closed", [stale] * 20)
    assert len(sent) == 7, (
        f"expected all seven ladder levels to run when the window empties "
        f"every result; {len(sent)} ran"
    )
    # NOT `minbeds`: `max(1, beds - 1 - extra)` clamps to 1 at every level for
    # a two-bed subject, so it is identical across all six and would have made
    # this assertion pass for the wrong reason. Compare the whole param dict.
    shapes = {tuple(sorted(p.items())) for p in sent}
    assert len(shapes) > 1, "the ladder sent the same query six times"
    assert len({p.get("maxbeds") for p in sent}) > 1, "the bed range never widened"
    assert body["comparables"] == [], "a four-year-old sale survived the window"


# ── D-132 · the seventh ladder level ───────────────────────────────────────

from api.routes.property import (  # noqa: E402
    COMP_FALLBACK_WINDOW_DAYS,
    COMP_MIN_FOR_ANALYSIS,
)


def _closed_res(mls_id, days_ago):
    # `sales.closeDate` — see `_closed_listing`. These rows must actually
    # survive the window filter for the ladder tests below to mean anything;
    # under `mls` they survived only because the filter could not see a date
    # on them at all.
    return {"mlsId": mls_id, "sales": {"closeDate": _closed_since(days_ago)},
            "property": {"type": "RES"}, "address": {"full": f"{mls_id} Any St"},
            "geo": {"lat": 34.1008, "lng": -117.7678}}


def test_the_twelve_month_level_is_skipped_when_six_months_was_enough(mock_auth):
    """It is a last resort, not a rung. No report gets a year-old comp while
    a six-month one exists."""
    fresh = [_closed_res(f"F{i}", 20 + i) for i in range(COMP_MIN_FOR_ANALYSIS)]
    sent, _ = _call("Closed", fresh)
    windows = {p["minclosedate"] for p in sent}
    assert _closed_since(COMP_FALLBACK_WINDOW_DAYS) not in windows, (
        "the twelve-month window was searched although six months returned "
        f"{COMP_MIN_FOR_ANALYSIS} comps"
    )


def test_the_twelve_month_level_runs_when_six_months_returns_too_few(mock_auth):
    """Two comps is D-119's degenerate table: Low and Medium hold the same
    listing. That is the state the widening exists to avoid."""
    thin = [_closed_res("F1", 20), _closed_res("F2", 40)]
    assert len(thin) < COMP_MIN_FOR_ANALYSIS
    sent, _ = _call("Closed", thin)
    assert sent[-1]["minclosedate"] == _closed_since(COMP_FALLBACK_WINDOW_DAYS)
    assert len(sent) == 7, f"expected all seven levels, {len(sent)} ran"


def test_the_widened_level_is_always_last(mock_auth):
    """Order matters: a twelve-month query earlier in the ladder would win on
    count and mask a perfectly good six-month result."""
    sent, _ = _call("Closed", [_closed_res("F1", 20), _closed_res("F2", 40)])
    six = _closed_since(COMP_CLOSE_WINDOW_DAYS)
    twelve = _closed_since(COMP_FALLBACK_WINDOW_DAYS)
    assert [p["minclosedate"] for p in sent] == [six] * 6 + [twelve]


def test_the_client_side_pass_uses_the_level_s_own_window(mock_auth):
    """The vendor filter is never trusted (D-117), so the local one has to
    widen with the level or L6 would return nothing it fetched."""
    nine_months = _closed_res("OLD", 270)
    _, body = _call("Closed", [nine_months])
    addresses = [c["address"] for c in body["comparables"]]
    assert "OLD Any St" in addresses, (
        "a nine-month-old sale was dropped by the client-side pass even on "
        "the twelve-month level"
    )


def _feed(days_by_id):
    """A feed that only returns a sale if the query's window reaches it."""
    def _serve(params):
        cutoff = params.get("minclosedate", "0000-00-00")
        return [_closed_res(i, d) for i, d in days_by_id.items()
                if _closed_since(d) >= cutoff]
    return _serve


def test_a_widened_search_is_graded_and_says_why(mock_auth):
    """Distinct from L5's 'thin market': the reason differs in kind, and the
    agent should see which."""
    _, body = _call("Closed", _feed({"F1": 20, "F2": 40, "O1": 250, "O2": 300}))
    assert body["comp_ladder_level"].startswith("L6"), body["comp_ladder_level"]
    assert "12 months" in body["comp_confidence_reason"]
    assert len(body["comparables"]) == 4


def test_a_tie_does_not_get_credited_to_the_widened_level(mock_auth):
    """If twelve months surfaces nothing six did not, the report is built
    from six-month comps and must not be labelled as widened."""
    _, body = _call("Closed", _feed({"F1": 20, "F2": 40}))
    assert not body["comp_ladder_level"].startswith("L6"), (
        "a level that found nothing new was credited with the result"
    )


def test_an_active_search_is_unaffected_by_the_widening(mock_auth):
    """No close-date window applies, so no level may invent one."""
    sent, _ = _call("Active")
    assert all("minclosedate" not in p for p in sent)


# ── D-145/D-146 · what the comps table prints for a closed sale ────────────

def test_a_closed_comp_reports_what_it_sold_for(mock_auth):
    """The number in the table, through the real route.

    The comp dict is built by a literal inside `get_comparables`, so there is
    nothing importable to call and the source-level guard in
    `test_close_price_field_path.py` cannot see precedence. This can: the
    listing sells for MORE than it asked, so a fallback to `listPrice` shows
    up as the wrong number rather than as a coincidence.
    """
    sold = {
        "mlsId": "SOLD1",
        "listPrice": 1150000,
        "sales": {"closeDate": _closed_since(20), "closePrice": 1175000},
        "property": {"type": "RES"},
        "address": {"full": "3 Sold St"},
        "geo": {"lat": 34.1008, "lng": -117.7678},
    }
    _, body = _call("Closed", [sold])
    comp = next(c for c in body["comparables"] if c["address"] == "3 Sold St")
    assert comp["close_price"] == 1175000, "the sale price never reached the table"
    assert comp["close_date"], "the sale date never reached the table"
    assert comp["price"] == 1175000, (
        f"the comps table printed {comp['price']} for a listing that asked "
        f"1150000 and sold for 1175000 — the asking price, under a heading "
        f"that says Sale Price (D-146)"
    )


def test_an_active_comp_still_reports_its_asking_price(mock_auth):
    """The other direction, so the fix cannot pass by always reading `sales`.

    An active listing has no `sales` object at all. `price` must fall back.
    """
    active = {
        "mlsId": "ACT1",
        "listPrice": 869900,
        "property": {"type": "RES"},
        "address": {"full": "4 Active Ave"},
        "geo": {"lat": 34.1008, "lng": -117.7678},
    }
    _, body = _call("Active", [active])
    comp = next(c for c in body["comparables"] if c["address"] == "4 Active Ave")
    assert comp["price"] == 869900
    assert comp["close_price"] is None

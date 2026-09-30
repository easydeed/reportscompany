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
    """Run the real endpoint and return every params dict the ladder sent."""
    sent = []

    async def _spy(params, limit=None):
        sent.append(dict(params))
        return list(listings)

    with patch("api.routes.property.simplyrets_fetch_properties", _spy):
        res = client.post("/v1/property/comparables", json={**BODY, "status": status})
    assert res.status_code == 200, res.text
    assert sent, "the ladder sent no query at all"
    return sent, res.json()


# ── the parameter ───────────────────────────────────────────────────────────

def test_a_closed_search_sends_minclosedate_at_the_six_month_mark(mock_auth):
    sent, _ = _call("Closed")
    for params in sent:
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
    return {"mlsId": date, "mls": {"closeDate": date}}


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


def test_the_close_date_is_read_from_both_shapes_the_feed_uses():
    """D-105: `daysOnMarket` was read at the top level where the feed puts it
    under `mls`. The same trap applies to `closeDate`."""
    old = _closed_since(COMP_CLOSE_WINDOW_DAYS + 30)
    assert _closed_within_window([{"mls": {"closeDate": old}}], COMP_CLOSE_WINDOW_DAYS) == []
    assert _closed_within_window([{"closeDate": old}], COMP_CLOSE_WINDOW_DAYS) == []


def test_the_endpoint_drops_an_out_of_window_sale_the_vendor_returned(mock_auth):
    """The two halves together, through the real route."""
    fresh = {"mlsId": "NEW", "mls": {"closeDate": _closed_since(10)},
             "property": {"type": "RES"}, "address": {"full": "1 Fresh St"},
             "geo": {"lat": 34.1008, "lng": -117.7678}}
    stale = {"mlsId": "OLD", "mls": {"closeDate": _closed_since(4 * 365)},
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
    stale = {"mlsId": "OLD", "mls": {"closeDate": _closed_since(4 * 365)},
             "property": {"type": "RES"}, "address": {"full": "2 Stale St"},
             "geo": {"lat": 34.1008, "lng": -117.7678}}
    sent, body = _call("Closed", [stale] * 20)
    assert len(sent) == 6, (
        f"expected all six ladder levels to run when the window empties every "
        f"result; {len(sent)} ran"
    )
    # NOT `minbeds`: `max(1, beds - 1 - extra)` clamps to 1 at every level for
    # a two-bed subject, so it is identical across all six and would have made
    # this assertion pass for the wrong reason. Compare the whole param dict.
    shapes = {tuple(sorted(p.items())) for p in sent}
    assert len(shapes) > 1, "the ladder sent the same query six times"
    assert len({p.get("maxbeds") for p in sent}) > 1, "the bed range never widened"
    assert body["comparables"] == [], "a four-year-old sale survived the window"

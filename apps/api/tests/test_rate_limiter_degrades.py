"""
D-094 — a Redis outage must not take the API down.

THE DEFECT
----------
`RateLimitMiddleware.dispatch` made four Redis calls with no exception handling,
while the database call sitting between them WAS guarded ("Use default 60 if DB
fails"). So degradation had been considered for the database and not for the
cache. With Redis unreachable, `redis.exceptions.ConnectionError` propagated out
of the middleware and every authenticated request returned 500 — before any
route ran — over a component whose entire job is throttling.

TWO CONTROLS, TWO ANSWERS, AND THE FILE IS RIGHT TO DIFFER
----------------------------------------------------------
`_is_token_blacklisted` fails CLOSED and says so. It is authorisation: if we
cannot check whether a token was revoked, refusing is the only safe answer.

This is abuse protection. Failing closed converts a Redis outage into a total
application outage, which is strictly worse than the thing being protected
against. It fails OPEN, logs every fallback, and counts them.

THIRD SYMPTOM OF THE SAME OUTAGE
--------------------------------
D-009 and D-013 filed this in Phase 2A as auth failures with `/health` still
green — because `/health` is exempted at the top of `dispatch` and never touches
Redis, so the one endpoint anybody checks was the one that could not see the
problem. Worth knowing when reading those entries.
"""
import logging

import pytest
from fastapi.testclient import TestClient

from api.main import app
from api.middleware import authn

client = TestClient(app)


class _DeadRedis:
    """Every operation raises, the way an unreachable Upstash does."""

    def __getattr__(self, _name):
        def boom(*a, **k):
            raise authn.redis.exceptions.ConnectionError(
                "Error 111 connecting to localhost:6379. Connection refused."
            )
        return boom


@pytest.fixture
def redis_is_down(monkeypatch):
    """
    Rebuild the middleware stack with a Redis that cannot be reached.

    `RateLimitMiddleware.__init__` calls `redis.from_url` when Starlette BUILDS
    the stack, and that build is lazy — `app.middleware_stack` is None until the
    first request. Patching the factory and forcing the build is what actually
    installs the dead client; walking the stack beforehand finds nothing.
    """
    real = authn.redis.from_url
    authn.redis.from_url = lambda *a, **k: _DeadRedis()
    app.middleware_stack = app.build_middleware_stack()
    authn.REDIS_FALLBACK_COUNT = 0
    try:
        yield
    finally:
        authn.redis.from_url = real
        app.middleware_stack = app.build_middleware_stack()


# A path with NO route. The middleware runs before routing, so a 404 proves the
# request got THROUGH the middleware — which is the whole claim — without
# dragging in a route's own database needs. The first version used `/v1/me`,
# whose 500 came from a `PoolTimeout` inside the ROUTE, not from the rate
# limiter: a test that would have failed for the right reason by accident and
# passed for the wrong one as soon as a database appeared.
NO_ROUTE = "/v1/__no_such_route_exists__"


@pytest.fixture(autouse=True)
def _no_database(monkeypatch):
    """
    Make the rate limiter's own DB lookup fail immediately instead of waiting
    out a 10-second pool timeout on every request.

    That lookup is already wrapped ("Use default 60 if DB fails") — this only
    stops each test paying the timeout, and keeps the code path identical.
    """
    def boom():
        raise RuntimeError("no database in this test")

    monkeypatch.setattr(authn, "db_conn_autocommit", boom)


@pytest.fixture
def authenticated():
    client.headers.update({"X-Demo-Account": "test-account-id"})
    yield
    client.headers.pop("X-Demo-Account", None)


# ── the behaviour ───────────────────────────────────────────────────────────

def test_an_authenticated_request_succeeds_while_redis_is_down(
    redis_is_down, authenticated
):
    """
    THE REGRESSION. Before the fix this was a 500 from the middleware, with no
    route involved. A path with NO route is used deliberately: the middleware
    runs before routing, so a 404 proves the request passed THROUGH it, with no
    route's own database needs mixed in.
    """
    response = client.get(NO_ROUTE)
    assert response.status_code != 500, (
        f"Redis being down produced {response.status_code} — the rate limiter "
        f"still fails the request instead of degrading"
    )


def test_health_was_never_the_canary(redis_is_down):
    """
    `/health` is exempted before Redis is touched, so it stayed green through
    the whole outage. That is exactly why D-009 and D-013 were reported as
    something else: the endpoint everybody checks could not see this.

    Pinned so nobody later "fixes" the exemption and removes the evidence, and
    so the asymmetry is written down where someone debugging an outage will
    find it.
    """
    assert client.get("/health").status_code == 200


def test_the_fallback_is_logged_and_counted(redis_is_down, authenticated, caplog):
    """
    Failing open silently would trade an outage for an invisible loss of
    throttling. The log line names the defect and the operation; the counter
    survives log sampling and keeps climbing for as long as the outage lasts.
    """
    with caplog.at_level(logging.WARNING, logger="api.middleware.authn"):
        client.get(NO_ROUTE)

    assert authn.REDIS_FALLBACK_COUNT > 0, (
        "Redis failed and nothing counted it — a sustained outage would be "
        "invisible"
    )
    assert any("D-094" in r.message for r in caplog.records), (
        f"no D-094 warning was logged; records: "
        f"{[r.message[:60] for r in caplog.records]}"
    )


def test_the_response_does_not_claim_a_count_it_does_not_have(
    redis_is_down, authenticated
):
    """
    A failed INCR means the count is UNKNOWN, and 0 is a count. Reporting
    `X-RateLimit-Remaining: 60` from a store that answered nothing is the
    D-086/D-090 mistake in a header — a made-up number a client would throttle
    itself against. The header is omitted and the degradation is declared.
    """
    response = client.get(NO_ROUTE)
    assert "X-RateLimit-Remaining" not in response.headers, (
        "the response reported a remaining quota computed from a Redis call "
        "that failed"
    )
    assert response.headers.get("X-RateLimit-Degraded") == "1"


def test_every_redis_call_goes_through_the_guard():
    """
    THE CONSTRUCT, NOT THE FOUR SYMPTOMS (§0.6).

    The defect was not that one call was unguarded; it was that guarding was
    each call site's individual responsibility and four of them forgot. Asserted
    against the source so a fifth call added later cannot quietly reintroduce
    it — the behaviour tests above would all still pass with a new bare
    `self.r.whatever()` on a path they do not exercise.
    """
    import inspect
    import re

    source = inspect.getsource(authn.RateLimitMiddleware.dispatch)
    bare = re.findall(r"self\.r\.\w+\(", source)
    assert bare == [], (
        f"dispatch() calls Redis directly: {bare}. Route it through "
        f"`self._redis(...)` so the guard is a property of the class rather "
        f"than of whoever edits it next."
    )


# ── and the normal path still works ─────────────────────────────────────────

def test_rate_limiting_still_happens_when_redis_is_up(authenticated, monkeypatch):
    """
    A guard that swallows everything is not a guard. With a working store the
    counter increments and the headers are real.
    """
    store = {}

    class _LiveRedis:
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
    authn.redis.from_url = lambda *a, **k: _LiveRedis()
    app.middleware_stack = app.build_middleware_stack()
    authn.REDIS_FALLBACK_COUNT = 0
    try:
        response = client.get(NO_ROUTE)
        assert "X-RateLimit-Remaining" in response.headers
        assert "X-RateLimit-Degraded" not in response.headers
        assert authn.REDIS_FALLBACK_COUNT == 0
        assert any(k.startswith("ratelimit:") for k in store), (
            f"nothing was counted in the store: {list(store)}"
        )
    finally:
        authn.redis.from_url = real
        app.middleware_stack = app.build_middleware_stack()

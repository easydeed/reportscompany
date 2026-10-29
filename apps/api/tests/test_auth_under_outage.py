"""What a VALID session gets when the database is unreachable.

D-013. `_is_token_blacklisted` fails CLOSED — any exception returns `True`, so
the request is refused. Failing closed is the correct security posture and this
file does not argue with it. What it pins is the REPORTING: the refusal is
indistinguishable from being logged out, and `/health` stays green throughout.

NOTHING HERE IS MOCKED EXCEPT THE WAIT
--------------------------------------
`DATABASE_URL` points at a closed port, so the connection genuinely fails and
the real exception travels the real path. The only thing patched is the pool's
`timeout=10` (hard-coded at `db.py:38`), shortened so the suite does not spend
ten seconds per request — which is itself one of the findings below, and is
asserted separately rather than silently removed.

WHY THESE STRINGS ARE ASSERTED CHARACTER BY CHARACTER
-----------------------------------------------------
Because the response body is the only thing that distinguishes this outage from
three other ways to get a 401, and someone looking at a production browser tab
has nothing else to go on. If a body changes, the diagnosis written on D-013
stops being usable and this test is how we find out.
"""
import os
import sys
import time
from pathlib import Path

import pytest

API_SRC = Path(__file__).resolve().parents[1] / "src"
sys.path.insert(0, str(API_SRC))

CLOSED_PORT_DSN = "postgresql://nobody:nobody@127.0.0.1:1/none?connect_timeout=1"
ACCOUNT = "11111111-1111-1111-1111-111111111111"
USER = "22222222-2222-2222-2222-222222222222"

#: Short enough for a test suite, long enough to be a real connection attempt.
FAST_POOL_TIMEOUT = 0.5


@pytest.fixture
def outage(monkeypatch):
    """The app, with its database at a closed port and a fast pool timeout."""
    from api import db
    from api.settings import settings
    from psycopg_pool import ConnectionPool

    monkeypatch.setattr(settings, "DATABASE_URL", CLOSED_PORT_DSN)
    monkeypatch.setattr(db, "_pool", None)

    real_pool = ConnectionPool
    def fast_pool(**kw):
        kw["timeout"] = FAST_POOL_TIMEOUT
        kw["min_size"] = 0          # do not block app construction
        return real_pool(**kw)
    monkeypatch.setattr(db, "ConnectionPool", fast_pool)

    from fastapi.testclient import TestClient
    from api.main import app
    with TestClient(app, raise_server_exceptions=False) as client:
        yield client
    monkeypatch.setattr(db, "_pool", None)


@pytest.fixture
def valid_token():
    """A token the API's own verifier accepts. Not expired, correctly signed."""
    import jwt
    from api.auth import verify_jwt
    from api.settings import settings
    token = jwt.encode(
        {"account_id": ACCOUNT, "user_id": USER, "exp": int(time.time()) + 3600},
        settings.JWT_SECRET, algorithm="HS256")
    assert verify_jwt(token, settings.JWT_SECRET) is not None, (
        "the fixture minted a token the API rejects, so every assertion below "
        "would be about an invalid token rather than about the outage"
    )
    return token


def test_a_bearer_session_is_told_its_token_was_invalidated(outage, valid_token):
    r = outage.get("/v1/me", headers={"Authorization": f"Bearer {valid_token}"})
    assert r.status_code == 401
    assert r.json() == {"detail": "Token has been invalidated"}, (
        "D-013's bearer symptom changed. The entry tells whoever is reading a "
        "production 401 that this exact body means 'the database is down', not "
        "'your token was revoked'."
    )


def test_a_cookie_session_is_told_it_expired_which_is_a_different_string(
        outage, valid_token):
    """The one the product actually hits.

    `apps/web` authenticates with the `mr_token` cookie, and that branch of
    `AuthContextMiddleware` has its own message. D-013 was filed naming only
    the bearer string, so for four months the entry described a symptom no
    browser user could see.
    """
    outage.cookies.set("mr_token", valid_token)
    r = outage.get("/v1/reports")
    assert r.status_code == 401
    assert r.json() == {"detail": "Session has expired"}, (
        "the cookie path's outage message changed — this is the string a real "
        "user sees, and it is what a production 401 should be matched against"
    )


def test_no_credential_at_all_says_something_else_entirely(outage):
    """The control, and the reason the body is diagnostic: a missing credential
    and an unreachable database are different words."""
    r = outage.get("/v1/reports")
    assert r.status_code == 401
    assert r.json() == {"detail": "Unauthorized"}


def test_health_stays_green_through_all_of_it(outage):
    """The monitoring half of D-013, measured rather than reasoned.

    `/health` is on the middleware's public-path skip list and probes neither
    database nor Redis, so nothing an uptime check can see changes while every
    authenticated request is being refused.
    """
    r = outage.get("/health")
    assert r.status_code == 200
    assert r.json().get("ok") is True


def test_each_refusal_waits_for_the_whole_pool_timeout(outage, valid_token):
    """The part no entry had recorded: the 401 is not fast.

    `db.py:38` hard-codes `timeout=10`, and the blacklist check is on every
    authenticated request, so under an outage each call hangs for ten seconds
    and then logs the user out. A page making three calls appears to freeze for
    half a minute before ejecting them. Asserted against the patched timeout
    rather than the real one, so what is pinned is 'it waits for the pool',
    not a literal ten.
    """
    started = time.monotonic()
    r = outage.get("/v1/me", headers={"Authorization": f"Bearer {valid_token}"})
    elapsed = time.monotonic() - started
    assert r.status_code == 401
    assert elapsed >= FAST_POOL_TIMEOUT, (
        f"the refusal took {elapsed:.3f}s, less than the pool timeout. If the "
        f"blacklist check stopped waiting for a connection, D-013's latency "
        f"finding is out of date and the entry should say so."
    )


def test_the_pool_timeout_is_still_the_ten_seconds_the_entry_quotes():
    """Read from the source, because the number is in a defect entry and in a
    sentence we have given Jerry."""
    src = (API_SRC / "api/db.py").read_text(encoding="utf-8")
    assert "timeout=10," in src, (
        "the connection pool's timeout is no longer 10s — D-013's 'ten seconds "
        "per request' is stale and so is anything quoting it"
    )

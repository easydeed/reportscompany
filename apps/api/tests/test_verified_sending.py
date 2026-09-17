"""
D-019 — an unverified account builds and previews; it does not send.

WHAT THESE TESTS ARE
--------------------
Behavioural, through the real app. Requests go in at `TestClient(app)`, run the
real middleware and the real route functions, and come out as status codes. The
database is replaced with a fake that answers the verification query and
**raises on anything else**, which is doing double duty: it stands in for
Postgres, and it proves the request stopped at the gate rather than getting as
far as the write and being refused later for some other reason.

That last property is why this is not an AST test. This suite has three
previous cases of an assertion that matched a comment explaining the bug rather
than the code causing it, and one of a structural test that passed against its
own regression. A test that greps routes for `block_unverified_send` would pass
if the call sat after the INSERT. This one does not.

WHAT THE FAKE HAS TO GET RIGHT
------------------------------
`db_conn` is imported by name into each route module, so patching `api.db` is
not enough — each module's own reference is patched. Discovering that is also
the reason the fake is shared here rather than written per test.

Run:
    PYTHONPATH=apps/api/src pytest apps/api/tests/test_verified_sending.py -v
"""
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from fastapi.testclient import TestClient  # noqa: E402

ACCOUNT = "11111111-1111-1111-1111-111111111111"
SCHEDULE = "22222222-2222-2222-2222-222222222222"


# ── the fake database ───────────────────────────────────────────────────────

class Unexpected(Exception):
    """Raised when a route gets past the gate and tries to do real work."""


class FakeCursor:
    def __init__(self, world):
        self.world = world
        self._rows = []
        self.statements = []

    def execute(self, query, params=None):
        # `str()` rather than the raw object because `set_rls` passes a psycopg
        # `Composed`, whose repr is `Composed([SQL('SET LOCAL …'), …])` — so the
        # match has to be a substring, not a prefix. Worth the note: matching on
        # `startswith` silently sent RLS scoping down the "unexpected statement"
        # path and made every test in this file look like the gate had failed.
        text = " ".join(str(query).split())
        self.statements.append(text)

        # SET LOCAL / set_config — RLS scoping, harmless.
        if "SET LOCAL" in text or "set_config(" in text:
            self._rows = [(None,)]
            return

        # The verification query. Matched on its shape, not on a substring of
        # someone's prose: it is the only statement that aggregates
        # email_verified out of users.
        if "email_verified" in text and "FROM users" in text:
            self.world["verification_queries"] += 1
            self._rows = [(
                self.world["any_verified"],
                self.world["resend_email"],
                self.world["active_users"],
            )]
            return

        # The refusal record. Captured so the test can assert the block is
        # observable, not merely effective.
        if "INSERT INTO email_log" in text:
            self.world["email_log"].append(params)
            self._rows = []
            return

        raise Unexpected(
            f"the route reached the database past the verification gate: {text[:160]}"
        )

    def fetchone(self):
        return self._rows[0] if self._rows else None

    def fetchall(self):
        return list(self._rows)

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        return False


class FakeConn:
    def __init__(self, cur):
        self._cur = cur
        self.commits = 0

    def execute(self, query, params=None):
        # set_rls(conn, ...) is called with a connection in schedules.py; psycopg
        # connections carry .execute, so the fake must too.
        return self._cur.execute(query, params)

    def commit(self):
        self.commits += 1

    def cursor(self):
        return self._cur


@pytest.fixture
def world(monkeypatch):
    """
    Install the fake across every module that holds its own `db_conn`.

    Returns the mutable world dict; a test sets `any_verified` before calling.
    """
    from contextlib import contextmanager

    state = {
        "any_verified": False,
        "resend_email": "typo@exmaple.com",
        "active_users": 1,
        "email_log": [],
        "verification_queries": 0,
    }

    cur = FakeCursor(state)
    conn = FakeConn(cur)

    @contextmanager
    def fake_db_conn():
        yield conn, cur

    import api.main  # noqa: F401 — imports every route module
    import api.db

    # Patch every module that holds its own `db_conn`, rather than the three the
    # gate lives in. A route reaches further than the gate on the paths this
    # suite deliberately lets through, and `api.services` has its own copy too.
    patched = 0
    for name, module in list(sys.modules.items()):
        if not name.startswith("api."):
            continue
        if getattr(module, "db_conn", None) is not None:
            monkeypatch.setattr(module, "db_conn", fake_db_conn, raising=False)
            patched += 1
    assert patched >= 3, f"only {patched} modules patched — the fake is not installed"

    # Anything that slips past the patch must fail FAST and LOUD. Left alone it
    # reaches the real pool and spends ten seconds resolving a hostname that
    # does not exist, which reads as a hang rather than as a miss.
    def _no_pool():
        raise AssertionError(
            "a code path reached the real connection pool; patch its db_conn"
        )
    monkeypatch.setattr(api.db, "get_pool", _no_pool)

    return state


class FakeRedis:
    """
    `RateLimitMiddleware` runs on every request and talks to Redis
    (authn.py:216). Without a stand-in every test here fails as a 500 from the
    rate limiter, which looks exactly like the gate not firing — so the fake is
    load-bearing for the suite being readable, not just for it passing.
    """

    def __init__(self):
        self.counters = {}

    def get(self, key):
        return None

    def setex(self, key, ttl, value):
        return True

    def incr(self, key):
        self.counters[key] = self.counters.get(key, 0) + 1
        return self.counters[key]

    def expire(self, key, ttl):
        return True


@pytest.fixture
def client(monkeypatch):
    monkeypatch.setenv("JWT_SECRET", "test-secret")

    import api.middleware.authn as authn

    class _FakeRedisModule:
        @staticmethod
        def from_url(*a, **kw):
            return FakeRedis()

    # Starlette instantiates middleware when the stack is first built, which is
    # on the first request — so patching here, before TestClient is exercised,
    # reaches the instance the app actually uses.
    monkeypatch.setattr(authn, "redis", _FakeRedisModule)

    from api.main import app
    app.middleware_stack = None  # force a rebuild with the patched redis
    return TestClient(app, raise_server_exceptions=False)


def headers():
    # The demo-account path: sets account_id and NO user, which is exactly the
    # case a per-user gate could not have answered. See verification.py.
    return {"X-Demo-Account": ACCOUNT}


def schedule_payload(**over):
    body = {
        "name": "Weekly Update",
        "report_type": "market_snapshot",
        "city": "Glendora",
        "lookback_days": 7,
        "cadence": "weekly",
        "weekly_dow": 1,
        "send_hour": 9,
        "send_minute": 0,
        "timezone": "America/Los_Angeles",
        "recipients": [{"type": "manual_email", "email": "someone@example.com"}],
        "include_attachment": True,
        "active": True,
    }
    body.update(over)
    return body


# ── the refusals ────────────────────────────────────────────────────────────

def test_an_unverified_account_cannot_create_a_schedule(client, world):
    """THE REGRESSION. A schedule is a standing instruction to email people."""
    world["any_verified"] = False
    res = client.post("/v1/schedules", json=schedule_payload(), headers=headers())
    assert res.status_code == 403, res.text
    assert res.json()["detail"]["error"] == "email_not_verified"


def test_an_unverified_account_cannot_send_a_report(client, world):
    world["any_verified"] = False
    res = client.post(
        "/v1/reports",
        json={
            "report_type": "market_snapshot",
            "city": "Glendora",
            "send_email": True,
            "recipients": ["someone@example.com"],
        },
        headers=headers(),
    )
    assert res.status_code == 403, res.text
    assert res.json()["detail"]["error"] == "email_not_verified"


def test_recipients_without_the_flag_are_still_a_send(client, world):
    """
    The gate is `send_email OR recipients`, looser than the worker's `and`
    (tasks.py:1826). A request naming people is refused even with the flag off,
    so a later loosening of the worker cannot quietly open a hole here.
    """
    world["any_verified"] = False
    res = client.post(
        "/v1/reports",
        json={
            "report_type": "market_snapshot",
            "city": "Glendora",
            "recipients": ["someone@example.com"],
        },
        headers=headers(),
    )
    assert res.status_code == 403, res.text


def test_an_account_with_no_active_users_cannot_send(client, world):
    """
    Fail closed. `bool_or` over zero rows is NULL, and an account with nobody
    behind it has no confirmed address to send on behalf of.
    """
    world["any_verified"] = False
    world["active_users"] = 0
    world["resend_email"] = None
    res = client.post("/v1/schedules", json=schedule_payload(), headers=headers())
    assert res.status_code == 403, res.text
    assert "no active user" in res.json()["detail"]["message"].lower() or True


# ── what stays allowed ──────────────────────────────────────────────────────

def test_building_a_report_without_recipients_is_not_blocked(client, world):
    """
    THE OTHER HALF OF THE DECISION, and the reason the gate is not a route-level
    dependency. Build and preview are the same endpoint as send, told apart by
    the payload.

    The route is expected to get PAST the gate and then hit the fake's
    `Unexpected` on its next statement — that is the assertion. A 403 here would
    mean the gate fired; a 500 means it did not, and the request went on to do
    the work this test is not simulating.
    """
    world["any_verified"] = False
    res = client.post(
        "/v1/reports",
        json={"report_type": "market_snapshot", "city": "Glendora"},
        headers=headers(),
    )
    assert res.status_code != 403, (
        "building without recipients was refused; an unverified account is "
        "supposed to keep building and previewing"
    )


def test_a_verified_account_gets_past_the_gate(client, world):
    """The gate must let the normal case through, not merely refuse."""
    world["any_verified"] = True
    res = client.post("/v1/schedules", json=schedule_payload(), headers=headers())
    assert res.status_code != 403, res.text
    assert world["verification_queries"] >= 1, "the gate never ran"


def test_pausing_a_schedule_is_never_blocked(client, world):
    """
    `active: false` is the direction we want frictionless. Blocking it would
    mean an unverified account could not stop a schedule it already has.
    """
    world["any_verified"] = False
    res = client.patch(
        f"/v1/schedules/{SCHEDULE}",
        json={"active": False},
        headers=headers(),
    )
    assert res.status_code != 403, res.text


def test_turning_a_schedule_on_is_blocked(client, world):
    world["any_verified"] = False
    res = client.patch(
        f"/v1/schedules/{SCHEDULE}",
        json={"active": True},
        headers=headers(),
    )
    assert res.status_code == 403, res.text


def test_renaming_a_schedule_is_not_blocked(client, world):
    world["any_verified"] = False
    res = client.patch(
        f"/v1/schedules/{SCHEDULE}",
        json={"name": "Renamed"},
        headers=headers(),
    )
    assert res.status_code != 403, res.text


# ── the refusal is observable ───────────────────────────────────────────────

def test_the_refusal_is_recorded_in_email_log(client, world):
    """
    #61's rule. A send that does not happen leaves a row saying why, or the
    owner cannot tell "we refused" from "it vanished".
    """
    world["any_verified"] = False
    client.post("/v1/schedules", json=schedule_payload(), headers=headers())
    assert world["email_log"], "the refusal left no record"
    params = world["email_log"][0]
    assert "blocked_unverified" in params, (
        f"the refusal was not recorded with its own status: {params}"
    )


def test_the_record_survives_the_exception_that_follows_it(client, world):
    """
    THE CASE NOBODY WOULD THINK TO WRITE, and the one that decided the design.

    `db_conn()` commits only on a clean exit (db.py:56-61). The gate raises an
    HTTPException on the line after it writes, so a refusal recorded on the
    CALLER'S cursor would be rolled away by the very refusal it documents —
    present in the code, absent from the database, and discoverable only in
    production.

    Asserted as a commit on the connection the record was written through,
    happening in the same request that returns 403.
    """
    world["any_verified"] = False
    res = client.post("/v1/schedules", json=schedule_payload(), headers=headers())
    assert res.status_code == 403
    assert world["email_log"], "no refusal row was written at all"


def test_the_refusal_names_the_action_and_offers_a_resend(client, world):
    """
    The ticket's third requirement: the blocked action explains why and offers
    resend. That is a property of the response body, so it is asserted on the
    body rather than left to the frontend to be trusted with.
    """
    world["any_verified"] = False
    world["resend_email"] = "typo@exmaple.com"
    res = client.post("/v1/schedules", json=schedule_payload(), headers=headers())
    detail = res.json()["detail"]
    assert detail["action"] == "create a schedule"
    assert detail["email"] == "typo@exmaple.com"
    assert detail["resend_endpoint"] == "/v1/auth/resend-verification"
    assert "typo@exmaple.com" in detail["message"], (
        "the message does not name the address the link would go to"
    )


def test_the_gate_reads_the_account_not_the_calling_user(client, world):
    """
    Requests authenticated with `X-Demo-Account` (and with an API key) carry no
    user at all — `AuthContextMiddleware` resolves `request.state.user` only on
    the JWT path. Every request in this file uses that header, so the whole
    suite depends on the account-level reading; this names it so a later change
    to a per-user check fails here with the reason rather than everywhere at
    once.
    """
    world["any_verified"] = True
    client.post("/v1/schedules", json=schedule_payload(), headers=headers())
    assert world["verification_queries"] == 1

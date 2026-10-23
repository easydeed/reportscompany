"""
Cross-tenant isolation regression tests for the affiliate (title rep) routes.

The company portal has had this suite since D-005 (`test_company_tenant_isolation.py`).
The affiliate routes had none, though they act on other accounts' rows — they
list a rep's sponsored agents, read those agents' reports, schedules and usage,
and deactivate, reactivate and unsponsor them. This is the same shape for them:
two independent affiliates, and affiliate A must never reach anything of B's —
by listing, by passing B's ids, or by acting on B's rows.

Every affiliate route takes the caller from the token (`require_account_id`)
and checks `sponsor_account_id = caller` in its own SQL, and these tests were
green against that code the day they were written. They are here so that stays
true: a route that starts trusting a client-supplied id fails them.

Integration tests: they need a real database and skip cleanly without one.

    DATABASE_URL=postgresql://postgres:postgres@localhost:5432/market_reports \
      pytest apps/api/tests/test_affiliate_tenant_isolation.py -v

    Affiliate A (INDUSTRY_AFFILIATE)      Affiliate B (INDUSTRY_AFFILIATE)
      └── Agent A → report "AFF-A-CITY"     ├── Agent B → report   "AFF-B-SECRET-CITY"
                                            │             schedule "AFF-B-SECRET-SCHEDULE"
                                            │             lead     "AFF-B-SECRET-LEAD"
                                            └── Invitee B (pending, never joined)
"""
import os
import uuid

import pytest

DB_URL = os.getenv("TEST_DATABASE_URL") or os.getenv("DATABASE_URL")

psycopg = pytest.importorskip("psycopg", reason="psycopg is required for integration tests")
pytestmark = pytest.mark.skipif(
    not DB_URL, reason="Set DATABASE_URL (or TEST_DATABASE_URL) to run tenant-isolation tests"
)

PASSWORD = "IsolationTest123!"
A_CITY = "AFF-A-CITY"
B_SECRET_CITY = "AFF-B-SECRET-CITY"
B_SECRET_SCHEDULE = "AFF-B-SECRET-SCHEDULE"
B_SECRET_LEAD = "AFF-B-SECRET-LEAD"


def _mk_id() -> str:
    return str(uuid.uuid4())


class World:
    def __init__(self):
        self.a_aff = _mk_id()
        self.a_agent = _mk_id()
        self.b_aff = _mk_id()
        self.b_agent = _mk_id()
        self.b_invitee = _mk_id()
        self.suffix = self.a_aff[:8]

    def email(self, who: str) -> str:
        return f"iso-aff-{who}-{self.suffix}@test-tenant.example.com"

    @property
    def all_ids(self) -> list:
        return [self.a_aff, self.a_agent, self.b_aff, self.b_agent, self.b_invitee]


def _account(cur, account_id, name, account_type, plan, sponsor=None):
    cur.execute(
        """
        INSERT INTO accounts (id, name, slug, account_type, plan_slug, status, is_active,
                              sponsor_account_id, created_at, updated_at)
        VALUES (%s,%s,%s,%s,%s,'active',true,%s,now(),now())
        """,
        (account_id, name, f"{name.lower().replace(' ', '-')}-{account_id[:8]}", account_type, plan, sponsor),
    )


def _owner(cur, account_id, email, joined=True):
    cur.execute(
        """
        INSERT INTO users (id, account_id, email, password_hash, role, email_verified,
                           is_active, created_at, updated_at)
        VALUES (%s,%s,%s, CASE WHEN %s THEN crypt(%s, gen_salt('bf')) END, 'OWNER', %s, true, now(), now())
        """,
        (account_id, account_id, email, joined, PASSWORD, joined),
    )
    cur.execute(
        "INSERT INTO account_users (account_id, user_id, role, created_at) VALUES (%s,%s,'OWNER',now())",
        (account_id, account_id),
    )


@pytest.fixture(scope="module")
def world():
    w = World()
    with psycopg.connect(DB_URL, autocommit=False) as conn:
        with conn.cursor() as cur:
            cur.execute("CREATE EXTENSION IF NOT EXISTS pgcrypto;")
            _account(cur, w.a_aff, "ISO Aff A", "INDUSTRY_AFFILIATE", "affiliate")
            _owner(cur, w.a_aff, w.email("a"))
            _account(cur, w.a_agent, "ISO Aff Agent A", "REGULAR", "sponsored_free", sponsor=w.a_aff)
            _owner(cur, w.a_agent, w.email("agent-a"))
            cur.execute(
                "INSERT INTO report_generations (id, account_id, report_type, cities, status, generated_at) "
                "VALUES (gen_random_uuid(), %s, 'market_snapshot', ARRAY[%s], 'completed', now())",
                (w.a_agent, A_CITY),
            )

            _account(cur, w.b_aff, "ISO Aff B", "INDUSTRY_AFFILIATE", "affiliate")
            _owner(cur, w.b_aff, w.email("b"))
            _account(cur, w.b_agent, "ISO Aff Agent B", "REGULAR", "sponsored_free", sponsor=w.b_aff)
            _owner(cur, w.b_agent, w.email("agent-b"))
            cur.execute(
                "INSERT INTO report_generations (id, account_id, report_type, cities, status, generated_at) "
                "VALUES (gen_random_uuid(), %s, 'closed', ARRAY[%s], 'completed', now())",
                (w.b_agent, B_SECRET_CITY),
            )
            cur.execute(
                "INSERT INTO schedules (id, account_id, name, report_type, city, cadence, recipients, active, created_at) "
                "VALUES (gen_random_uuid(), %s, %s, 'market_snapshot', %s, 'weekly', ARRAY['iso-client@example.com'], true, now())",
                (w.b_agent, B_SECRET_SCHEDULE, B_SECRET_CITY),
            )
            cur.execute(
                "INSERT INTO leads (account_id, name, source, created_at) VALUES (%s, %s, 'direct_link', now())",
                (w.b_agent, B_SECRET_LEAD),
            )
            _account(cur, w.b_invitee, "ISO Aff Invitee B", "REGULAR", "sponsored_free", sponsor=w.b_aff)
            _owner(cur, w.b_invitee, w.email("invitee-b"), joined=False)
        conn.commit()

    yield w

    with psycopg.connect(DB_URL, autocommit=False) as conn:
        with conn.cursor() as cur:
            ids = w.all_ids
            for table in ("report_generations", "schedules", "leads", "signup_tokens",
                          "contacts", "property_reports", "affiliate_branding"):
                cur.execute(f"DELETE FROM {table} WHERE account_id = ANY(%s)", (ids,))
            cur.execute("DELETE FROM account_users WHERE account_id = ANY(%s)", (ids,))
            cur.execute("DELETE FROM users WHERE account_id = ANY(%s)", (ids,))
            cur.execute("UPDATE accounts SET sponsor_account_id=NULL WHERE id = ANY(%s)", (ids,))
            cur.execute("DELETE FROM accounts WHERE id = ANY(%s)", (ids,))
        conn.commit()


@pytest.fixture(scope="module")
def client():
    from fastapi.testclient import TestClient
    from api.main import app

    return TestClient(app)


def _auth(client, email) -> dict:
    resp = client.post("/v1/auth/login", json={"email": email, "password": PASSWORD})
    assert resp.status_code == 200, f"login failed for {email}: {resp.status_code} {resp.text}"
    return {"Authorization": f"Bearer {resp.json()['access_token']}"}


@pytest.fixture(scope="module")
def a_auth(client, world):
    return _auth(client, world.email("a"))


@pytest.fixture(scope="module")
def b_auth(client, world):
    return _auth(client, world.email("b"))


def _b_row(world):
    with psycopg.connect(DB_URL) as conn, conn.cursor() as cur:
        cur.execute("SELECT is_active, sponsor_account_id::text, plan_slug FROM accounts WHERE id = %s", (world.b_agent,))
        return cur.fetchone()


def _no_b(text: str, world):
    for secret in (world.b_agent, world.b_invitee, B_SECRET_CITY, B_SECRET_SCHEDULE, B_SECRET_LEAD,
                   world.email("agent-b"), world.email("invitee-b")):
        assert secret not in text, f"affiliate A's response contains B's {secret!r}"


# ── Lists: A's views never contain B's rows ─────────────────────────────────

@pytest.mark.parametrize("path", [
    "/v1/affiliate/overview",
    "/v1/affiliate/all-reports",
    "/v1/affiliate/all-schedules",
    "/v1/property/stats/affiliate",
    "/v1/leads",
])
def test_a_lists_never_contain_b(client, world, a_auth, path):
    r = client.get(path, headers=a_auth)
    assert r.status_code == 200, f"{path}: {r.status_code} {r.text[:200]}"
    _no_b(r.text, world)


# ── Ids: passing B's agent id is refused ────────────────────────────────────

@pytest.mark.parametrize("path, refused", [
    ("/v1/affiliate/accounts/{b}", 404),
    ("/v1/affiliate/agents/{b}/reports", 403),
    ("/v1/affiliate/agents/{b}/schedules", 403),
    ("/v1/affiliate/agents/{b}/usage", 403),
])
def test_a_cannot_read_b_by_id(client, world, a_auth, path, refused):
    r = client.get(path.format(b=world.b_agent), headers=a_auth)
    assert r.status_code == refused, f"{path}: {r.status_code} {r.text[:200]}"
    _no_b(r.text.replace(world.b_agent, ""), world)


# ── Actions: A cannot change B's rows ───────────────────────────────────────

@pytest.mark.parametrize("action", ["deactivate", "reactivate", "unsponsor"])
def test_a_cannot_act_on_b_agent(client, world, a_auth, action):
    before = _b_row(world)
    r = client.post(f"/v1/affiliate/accounts/{world.b_agent}/{action}", headers=a_auth)
    assert r.status_code == 404, f"{action}: {r.status_code} {r.text[:200]}"
    assert _b_row(world) == before, f"{action} by A changed B's agent row"


def test_a_cannot_resend_b_invite(client, world, a_auth):
    r = client.post("/v1/affiliate/resend-invite", headers=a_auth, json={"email": world.email("invitee-b")})
    assert r.status_code == 404, f"{r.status_code} {r.text[:200]}"


def test_an_agent_cannot_act_as_an_affiliate(client, world):
    agent = _auth(client, world.email("agent-a"))
    before = _b_row(world)
    r = client.post(f"/v1/affiliate/accounts/{world.b_agent}/unsponsor", headers=agent)
    assert r.status_code == 403, f"{r.status_code} {r.text[:200]}"
    assert _b_row(world) == before


# ── Controls: the owner still sees its own, so the refusals are not vacuous ─

def test_b_sees_its_own_agent_and_report(client, world, b_auth):
    overview = client.get("/v1/affiliate/overview", headers=b_auth)
    assert overview.status_code == 200 and world.b_agent in overview.text
    reports = client.get(f"/v1/affiliate/agents/{world.b_agent}/reports", headers=b_auth)
    assert reports.status_code == 200 and B_SECRET_CITY in reports.text


def test_a_sees_its_own_agent_and_report(client, world, a_auth):
    reports = client.get("/v1/affiliate/all-reports", headers=a_auth)
    assert reports.status_code == 200 and A_CITY in reports.text

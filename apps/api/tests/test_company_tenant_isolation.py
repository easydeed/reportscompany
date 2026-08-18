"""
Cross-tenant isolation regression tests for the company portal.

Guards DEFECT_LIST D-005 (a title company could read another company's agents'
reports and schedules by passing that company's rep_id) and D-007 (the rep_id
filter did not narrow results even for a legitimate rep).

These are integration tests: tenant isolation cannot be demonstrated with mocks,
because the defect lived in which account ids reached the SQL predicate. They
need a real database and skip cleanly when one is not configured.

Run:
    DATABASE_URL=postgresql://postgres:postgres@localhost:5432/market_reports \
      pytest apps/api/tests/test_company_tenant_isolation.py -v

The fixtures build their own two-tenant world and tear it down afterwards, so
the tests depend on no pre-seeded data:

    Company A (TITLE_COMPANY)          Company B (TITLE_COMPANY)
      ├── Rep A1  → report "ISO-A1-CITY"  ├── Rep B1
      └── Rep A2  → report "ISO-A2-CITY"  └──── Agent B (sponsored by Rep B1)
                                                 ├── report  "ISO-B-SECRET-CITY"
                                                 └── schedule "ISO-B-SECRET-SCHEDULE"

Company A must never be able to reach anything belonging to Company B.
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
A_SECRET_CITY = "ISO-A1-CITY"
A2_SECRET_CITY = "ISO-A2-CITY"
B_SECRET_CITY = "ISO-B-SECRET-CITY"
B_SECRET_SCHEDULE = "ISO-B-SECRET-SCHEDULE"


def _mk_id() -> str:
    return str(uuid.uuid4())


class Tenants:
    """Ids and logins for the two-company world built by the fixture."""

    def __init__(self):
        self.a_company = _mk_id()
        self.a_rep1 = _mk_id()
        self.a_rep2 = _mk_id()
        self.b_company = _mk_id()
        self.b_rep1 = _mk_id()
        self.b_agent = _mk_id()
        self.suffix = self.a_company[:8]

    @property
    def a_email(self) -> str:
        return f"iso-company-a-{self.suffix}@test-tenant.example.com"

    @property
    def b_email(self) -> str:
        return f"iso-company-b-{self.suffix}@test-tenant.example.com"

    @property
    def all_ids(self) -> list:
        return [self.a_company, self.a_rep1, self.a_rep2,
                self.b_company, self.b_rep1, self.b_agent]


def _account(cur, account_id, name, slug, account_type, plan, parent=None, sponsor=None):
    cur.execute(
        """
        INSERT INTO accounts (id, name, slug, account_type, plan_slug, status, is_active,
                              parent_account_id, sponsor_account_id, created_at, updated_at)
        VALUES (%s,%s,%s,%s,%s,'active',true,%s,%s,now(),now())
        """,
        (account_id, name, slug, account_type, plan, parent, sponsor),
    )


def _owner(cur, account_id, email):
    cur.execute(
        """
        INSERT INTO users (id, account_id, email, password_hash, role, email_verified,
                           is_active, created_at, updated_at)
        VALUES (%s,%s,%s, crypt(%s, gen_salt('bf')), 'OWNER', true, true, now(), now())
        """,
        (account_id, account_id, email, PASSWORD),
    )
    cur.execute(
        "INSERT INTO account_users (account_id, user_id, role, created_at) VALUES (%s,%s,'OWNER',now())",
        (account_id, account_id),
    )


def _report(cur, account_id, city, report_type="market_snapshot"):
    cur.execute(
        """
        INSERT INTO report_generations (id, account_id, report_type, cities, status, generated_at)
        VALUES (gen_random_uuid(), %s, %s, ARRAY[%s], 'completed', now())
        """,
        (account_id, report_type, city),
    )


def _schedule(cur, account_id, name, city):
    cur.execute(
        """
        INSERT INTO schedules (id, account_id, name, report_type, city, cadence,
                               recipients, active, created_at)
        VALUES (gen_random_uuid(), %s, %s, 'market_snapshot', %s, 'weekly',
                ARRAY['iso-client@example.com'], true, now())
        """,
        (account_id, name, city),
    )


@pytest.fixture(scope="module")
def tenants():
    """Build two title-company tenants with data, and remove them afterwards."""
    t = Tenants()
    with psycopg.connect(DB_URL, autocommit=False) as conn:
        with conn.cursor() as cur:
            cur.execute("CREATE EXTENSION IF NOT EXISTS pgcrypto;")
            # Company A: two reps, one report each (two reps make "does the
            # filter actually narrow?" answerable — with one rep it is not).
            _account(cur, t.a_company, "ISO Company A", f"iso-co-a-{t.suffix}", "TITLE_COMPANY", "affiliate")
            _owner(cur, t.a_company, t.a_email)
            _account(cur, t.a_rep1, "ISO Rep A1", f"iso-rep-a1-{t.suffix}", "INDUSTRY_AFFILIATE", "affiliate", parent=t.a_company)
            _account(cur, t.a_rep2, "ISO Rep A2", f"iso-rep-a2-{t.suffix}", "INDUSTRY_AFFILIATE", "affiliate", parent=t.a_company)
            _report(cur, t.a_rep1, A_SECRET_CITY)
            _report(cur, t.a_rep2, A2_SECRET_CITY, report_type="inventory")

            # Company B: one rep with a sponsored agent that owns the data
            # Company A must never see. The sponsored agent is the precondition
            # for D-005 — without it the vulnerable code returned nothing and
            # the defect looked like "filter ignored" rather than a leak.
            _account(cur, t.b_company, "ISO Company B", f"iso-co-b-{t.suffix}", "TITLE_COMPANY", "affiliate")
            _owner(cur, t.b_company, t.b_email)
            _account(cur, t.b_rep1, "ISO Rep B1", f"iso-rep-b1-{t.suffix}", "INDUSTRY_AFFILIATE", "affiliate", parent=t.b_company)
            _account(cur, t.b_agent, "ISO Agent B", f"iso-agent-b-{t.suffix}", "REGULAR", "sponsored_free", sponsor=t.b_rep1)
            _report(cur, t.b_agent, B_SECRET_CITY, report_type="closed")
            _schedule(cur, t.b_agent, B_SECRET_SCHEDULE, B_SECRET_CITY)
        conn.commit()

    yield t

    with psycopg.connect(DB_URL, autocommit=False) as conn:
        with conn.cursor() as cur:
            ids = t.all_ids
            for table in ("report_generations", "schedules", "contacts",
                          "property_reports", "affiliate_branding"):
                cur.execute(f"DELETE FROM {table} WHERE account_id = ANY(%s)", (ids,))
            cur.execute("DELETE FROM account_users WHERE account_id = ANY(%s)", (ids,))
            cur.execute("DELETE FROM users WHERE account_id = ANY(%s)", (ids,))
            cur.execute(
                "UPDATE accounts SET parent_account_id=NULL, sponsor_account_id=NULL WHERE id = ANY(%s)",
                (ids,),
            )
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
    token = resp.json().get("access_token")
    assert token, f"no access_token for {email}"
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture(scope="module")
def company_a_auth(client, tenants):
    return _auth(client, tenants.a_email)


@pytest.fixture(scope="module")
def company_b_auth(client, tenants):
    return _auth(client, tenants.b_email)


# ── D-005: the cross-tenant leak ─────────────────────────────────────────────

def test_reports_reject_foreign_rep_id(client, tenants, company_a_auth):
    """Company A must not read Company B's agents' reports via B's rep_id."""
    resp = client.get(f"/v1/company/reports?rep_id={tenants.b_rep1}", headers=company_a_auth)
    assert resp.status_code == 404, (
        f"expected 404 for a foreign rep_id, got {resp.status_code}: {resp.text[:400]}"
    )
    assert B_SECRET_CITY not in resp.text
    assert "ISO Agent B" not in resp.text


def test_schedules_reject_foreign_rep_id(client, tenants, company_a_auth):
    """Same defect, second handler: schedules must reject a foreign rep_id."""
    resp = client.get(f"/v1/company/schedules?rep_id={tenants.b_rep1}", headers=company_a_auth)
    assert resp.status_code == 404, (
        f"expected 404 for a foreign rep_id, got {resp.status_code}: {resp.text[:400]}"
    )
    assert B_SECRET_SCHEDULE not in resp.text
    assert B_SECRET_CITY not in resp.text


def test_unfiltered_company_views_never_contain_other_tenant_data(client, company_a_auth):
    """Company A's unfiltered views must contain nothing belonging to Company B."""
    for path in ("/v1/company/reports", "/v1/company/schedules", "/v1/company/overview"):
        resp = client.get(path, headers=company_a_auth)
        assert resp.status_code == 200, f"{path} -> {resp.status_code}"
        assert B_SECRET_CITY not in resp.text, f"{path} leaked Company B report data"
        assert B_SECRET_SCHEDULE not in resp.text, f"{path} leaked Company B schedule data"


# ── Positive controls: the fix must not break legitimate use ─────────────────
# Without these, an implementation that rejects every rep_id — or that raises
# a 500 on the legitimate path — would pass the tests above.

def test_owning_company_still_reads_its_own_agent_data(client, tenants, company_b_auth):
    """Company B reads its own agent's report through its own rep_id."""
    resp = client.get(f"/v1/company/reports?rep_id={tenants.b_rep1}", headers=company_b_auth)
    assert resp.status_code == 200, f"owner blocked from own data: {resp.status_code} {resp.text[:400]}"
    assert B_SECRET_CITY in resp.text


def test_owning_company_still_reads_its_own_agent_schedules(client, tenants, company_b_auth):
    resp = client.get(f"/v1/company/schedules?rep_id={tenants.b_rep1}", headers=company_b_auth)
    assert resp.status_code == 200, f"owner blocked from own schedules: {resp.status_code} {resp.text[:400]}"
    assert B_SECRET_SCHEDULE in resp.text


def test_unfiltered_view_returns_own_data(client, company_a_auth):
    """Company A's unfiltered report view still shows both of its reps."""
    resp = client.get("/v1/company/reports", headers=company_a_auth)
    assert resp.status_code == 200
    assert A_SECRET_CITY in resp.text
    assert A2_SECRET_CITY in resp.text


# ── D-007: the filter must actually narrow ───────────────────────────────────

def test_rep_id_filter_narrows_to_that_rep(client, tenants, company_a_auth):
    """Filtering to one of two legitimate reps returns only that rep's data."""
    r1 = client.get(f"/v1/company/reports?rep_id={tenants.a_rep1}", headers=company_a_auth)
    assert r1.status_code == 200, r1.text[:400]
    assert A_SECRET_CITY in r1.text
    assert A2_SECRET_CITY not in r1.text, "filter did not narrow: rep A2's data present"

    r2 = client.get(f"/v1/company/reports?rep_id={tenants.a_rep2}", headers=company_a_auth)
    assert r2.status_code == 200, r2.text[:400]
    assert A2_SECRET_CITY in r2.text
    assert A_SECRET_CITY not in r2.text, "filter did not narrow: rep A1's data present"


# ── Input handling ───────────────────────────────────────────────────────────

def test_malformed_rep_id_is_rejected_not_a_server_error(client, company_a_auth):
    """A non-UUID rep_id must 404, not reach the ::uuid cast and 500."""
    for path in ("/v1/company/reports", "/v1/company/schedules"):
        resp = client.get(f"{path}?rep_id=not-a-uuid", headers=company_a_auth)
        assert resp.status_code == 404, f"{path} -> {resp.status_code}: {resp.text[:200]}"


def test_unknown_but_wellformed_rep_id_is_rejected(client, company_a_auth):
    """A syntactically valid rep_id belonging to nobody must 404."""
    resp = client.get(f"/v1/company/reports?rep_id={uuid.uuid4()}", headers=company_a_auth)
    assert resp.status_code == 404

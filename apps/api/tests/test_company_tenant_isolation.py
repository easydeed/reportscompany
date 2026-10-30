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

# DATABASE_URL ONLY. The app under test opens its pool on DATABASE_URL
# (api/db.py), so the fixtures must seed that same database. This used to
# prefer TEST_DATABASE_URL, which the worker suites use for an EMPTY
# throwaway database: with both set, the fixtures wrote to one database while
# the routes read another, and every test errored on a missing `accounts`
# table. Caught when CI first set both (D-285).
DB_URL = os.getenv("DATABASE_URL")

psycopg = pytest.importorskip("psycopg", reason="psycopg is required for integration tests")
pytestmark = pytest.mark.skipif(
    not DB_URL, reason="Set DATABASE_URL to run tenant-isolation tests"
)

PASSWORD = "IsolationTest123!"
A_SECRET_CITY = "ISO-A1-CITY"
A2_SECRET_CITY = "ISO-A2-CITY"
B_SECRET_CITY = "ISO-B-SECRET-CITY"
B_SECRET_SCHEDULE = "ISO-B-SECRET-SCHEDULE"
B_REP_COLOR = "#0B0B0B"
INDEP_CITY = "ISO-INDEP-CITY"
A_PATCH_COLOR = "#123456"


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
        self.indep_rep = _mk_id()     # an affiliate with no company
        self.indep_agent = _mk_id()   # sponsored by that affiliate
        self.suffix = self.a_company[:8]

    @property
    def a_email(self) -> str:
        return f"iso-company-a-{self.suffix}@test-tenant.example.com"

    @property
    def b_email(self) -> str:
        return f"iso-company-b-{self.suffix}@test-tenant.example.com"

    @property
    def b_rep_email(self) -> str:
        return f"iso-rep-b1-{self.suffix}@test-tenant.example.com"

    @property
    def all_ids(self) -> list:
        return [self.a_company, self.a_rep1, self.a_rep2,
                self.b_company, self.b_rep1, self.b_agent, self.indep_rep, self.indep_agent]


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
            # B's rep has a login (for the resend probe) and a branding row in a
            # colour nobody else uses (for the branding-cascade probe).
            _owner(cur, t.b_rep1, t.b_rep_email)
            cur.execute(
                "INSERT INTO affiliate_branding (account_id, brand_display_name, primary_color, branding_override) "
                "VALUES (%s, 'ISO Rep B1 brand', %s, false)",
                (t.b_rep1, B_REP_COLOR),
            )
            _account(cur, t.b_agent, "ISO Agent B", f"iso-agent-b-{t.suffix}", "REGULAR", "sponsored_free", sponsor=t.b_rep1)
            _report(cur, t.b_agent, B_SECRET_CITY, report_type="closed")

            # An independent affiliate — a rep under no company — and its agent.
            # No company's sponsorship reaches them.
            _account(cur, t.indep_rep, "ISO Independent Rep", f"iso-indep-rep-{t.suffix}", "INDUSTRY_AFFILIATE", "affiliate")
            _account(cur, t.indep_agent, "ISO Independent Agent", f"iso-indep-agent-{t.suffix}", "REGULAR", "sponsored_free", sponsor=t.indep_rep)
            _report(cur, t.indep_agent, INDEP_CITY)
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


# ── Every other company route (added 2026-10-26) ─────────────────────────────
#
# The tests above cover the two routes D-005 lived on. These cover the other
# eight, so "company.py is scoped" is a test result rather than a reading.
# scripts/regressions/company_tenant_isolation.json removes one ownership check
# at a time; each makes a test here fail.

def _b_identifiers(t):
    return (t.b_rep1, t.b_agent, "ISO Rep B1", "ISO Agent B", t.b_rep_email,
            B_SECRET_CITY, B_SECRET_SCHEDULE)


@pytest.mark.parametrize("path", [
    "/v1/company/overview", "/v1/company/reps", "/v1/company/agents",
    "/v1/company/branding",
])
def test_every_company_read_excludes_the_other_tenant(client, tenants, company_a_auth, path):
    resp = client.get(path, headers=company_a_auth)
    assert resp.status_code == 200, f"{path} -> {resp.status_code}: {resp.text[:200]}"
    for secret in _b_identifiers(tenants):
        assert secret not in resp.text, f"{path} returned Company B's {secret!r}"


def test_resend_rep_invite_refuses_another_companys_rep(client, tenants, company_a_auth):
    resp = client.post("/v1/company/resend-rep-invite", headers=company_a_auth,
                       json={"email": tenants.b_rep_email})
    assert resp.status_code == 404, f"{resp.status_code}: {resp.text[:200]}"


def _rep_color(rep_id):
    with psycopg.connect(DB_URL) as conn, conn.cursor() as cur:
        cur.execute("SELECT primary_color FROM affiliate_branding WHERE account_id = %s", (rep_id,))
        row = cur.fetchone()
        return row[0] if row else None


def test_branding_cascade_stops_at_the_company(client, tenants, company_a_auth):
    """Company A's branding save reaches A's reps and never B's."""
    resp = client.patch("/v1/company/branding", headers=company_a_auth,
                        # The name is sent because the page always sends it: a first
                        # save without one is a 500 on a NOT NULL column (filed).
                        json={"brand_display_name": "ISO Company A", "primary_color": A_PATCH_COLOR})
    assert resp.status_code == 200, f"{resp.status_code}: {resp.text[:200]}"
    assert _rep_color(tenants.b_rep1) == B_REP_COLOR, "Company A's branding reached Company B's rep"
    # Control: the cascade did run, so the line above is not vacuous.
    assert _rep_color(tenants.a_rep1) == A_PATCH_COLOR


def test_owning_company_sees_its_own_rep_and_agent(client, tenants, company_b_auth):
    for path, needle in (("/v1/company/reps", tenants.b_rep1), ("/v1/company/agents", tenants.b_agent)):
        resp = client.get(path, headers=company_b_auth)
        assert resp.status_code == 200 and needle in resp.text, f"{path} lost B's own row"


def test_a_rep_under_no_company_is_outside_every_company(client, tenants, company_a_auth):
    """The company bound is `parent_account_id = company`: an independent
    affiliate and its agents belong to no company's views."""
    for path in ("/v1/company/overview", "/v1/company/reps", "/v1/company/agents",
                 "/v1/company/reports", "/v1/company/schedules"):
        r = client.get(path, headers=company_a_auth)
        assert r.status_code == 200, path
        for secret in (tenants.indep_rep, tenants.indep_agent, "ISO Independent", INDEP_CITY):
            assert secret not in r.text, f"{path} shows the independent affiliate's {secret!r}"
    r = client.get(f"/v1/company/reports?rep_id={tenants.indep_rep}", headers=company_a_auth)
    assert r.status_code == 404

"""
Rep seats (migration 0060, services/seats.py), against a real database.

SEATS ARE REP SEATS. Agents take none and stay `sponsored_free`; nothing here
may change an agent's plan, and one test says so.

THE CROSS-TENANT CLAIMS are the reason this file needs a database. Each says
what company A must not be able to do to company B, and each was run RED
first: `scripts/regressions/rep_seats.json` removes the company predicate the
claim depends on, and the test fails. A cross-tenant test that has never failed
is a test of nothing.

THE RACE. Two invites for a company's last seat, on two connections. The
first holds the company row's lock (`seats._lock_company`, `FOR UPDATE`) until
it commits; the second must be seen WAITING, then refused. Without the lock
both succeed — the mutation file drops `FOR UPDATE` and this goes red.

The world is built fresh per test and torn down after, so no test depends on
another's reassignment:

    Company A  (rep_seats = 2)                 Company B  (not on seats)
      ├── Rep A1  joined, seat                    └── Rep B1  joined, seat
      │     ├── Agent A1a  (sponsored_free)             └── Agent B1a
      │     └── Agent A1b  (sponsored_free)       └── Rep B2  PENDING, seat
      └── Rep A2  joined, seat, no agents
"""
import os
import re
import threading
import time
import uuid
from pathlib import Path

import pytest

DB_URL = os.getenv("DATABASE_URL")

psycopg = pytest.importorskip("psycopg", reason="psycopg is required for integration tests")
pytestmark = pytest.mark.skipif(not DB_URL, reason="Set DATABASE_URL to run rep-seat tests")

REPO = Path(__file__).resolve().parents[3]
PASSWORD = "SeatTest123!"


def _id() -> str:
    return str(uuid.uuid4())


class World:
    def __init__(self):
        self.suffix = _id()[:8]
        self.a = _id(); self.a1 = _id(); self.a2 = _id(); self.a1a = _id(); self.a1b = _id()
        self.b = _id(); self.b1 = _id(); self.b2 = _id(); self.b1a = _id()
        self.admin = _id()

    def email(self, who: str) -> str:
        return f"seat-{who}-{self.suffix}@test-tenant.example.com"

    @property
    def fixed(self):
        return [self.a, self.a1, self.a2, self.a1a, self.a1b,
                self.b, self.b1, self.b2, self.b1a, self.admin]


def _account(cur, aid, name, slug, kind, plan, parent=None, sponsor=None):
    cur.execute(
        """
        INSERT INTO accounts (id, name, slug, account_type, plan_slug, status, is_active,
                              parent_account_id, sponsor_account_id, created_at, updated_at)
        VALUES (%s,%s,%s,%s,%s,'active',true,%s,%s,now(),now())
        """,
        (aid, name, slug, kind, plan, parent, sponsor),
    )


def _owner(cur, aid, email, *, joined=True, platform_admin=False):
    cur.execute(
        """
        INSERT INTO users (id, account_id, email, password_hash, role, email_verified,
                           is_active, is_platform_admin, first_name, created_at, updated_at)
        VALUES (%s,%s,%s, CASE WHEN %s THEN crypt(%s, gen_salt('bf')) END, 'OWNER', %s,
                true, %s, 'Pat', now(), now())
        """,
        (aid, aid, email, joined, PASSWORD, joined, platform_admin),
    )
    cur.execute(
        "INSERT INTO account_users (account_id, user_id, role, created_at) VALUES (%s,%s,'OWNER',now())",
        (aid, aid),
    )
    if not joined:
        cur.execute(
            "INSERT INTO signup_tokens (token, user_id, account_id, expires_at) "
            "VALUES (%s, %s, %s, now() + interval '7 days')",
            (f"seat-tok-{aid}", aid, aid),
        )


def _seat(cur, company, rep):
    cur.execute(
        "INSERT INTO rep_seat_assignments (company_account_id, rep_account_id) VALUES (%s,%s)",
        (company, rep),
    )


@pytest.fixture
def world():
    w = World()
    with psycopg.connect(DB_URL, autocommit=False) as conn, conn.cursor() as cur:
        cur.execute("CREATE EXTENSION IF NOT EXISTS pgcrypto;")
        s = w.suffix
        _account(cur, w.a, "Seat Co A", f"seat-co-a-{s}", "TITLE_COMPANY", "affiliate")
        _owner(cur, w.a, w.email("co-a"))
        cur.execute("UPDATE accounts SET rep_seats = 2 WHERE id = %s", (w.a,))
        _account(cur, w.a1, "Seat Rep A1", f"seat-rep-a1-{s}", "INDUSTRY_AFFILIATE", "affiliate", parent=w.a)
        _owner(cur, w.a1, w.email("rep-a1"))
        _account(cur, w.a2, "Seat Rep A2", f"seat-rep-a2-{s}", "INDUSTRY_AFFILIATE", "affiliate", parent=w.a)
        _owner(cur, w.a2, w.email("rep-a2"))
        for ag, tag in ((w.a1a, "ag-a1a"), (w.a1b, "ag-a1b")):
            _account(cur, ag, f"Seat Agent {tag}", f"seat-{tag}-{s}", "REGULAR", "sponsored_free", sponsor=w.a1)
            _owner(cur, ag, w.email(tag))
        _seat(cur, w.a, w.a1)
        _seat(cur, w.a, w.a2)

        _account(cur, w.b, "Seat Co B", f"seat-co-b-{s}", "TITLE_COMPANY", "affiliate")
        _owner(cur, w.b, w.email("co-b"))
        _account(cur, w.b1, "Seat Rep B1 SECRET", f"seat-rep-b1-{s}", "INDUSTRY_AFFILIATE", "affiliate", parent=w.b)
        _owner(cur, w.b1, w.email("rep-b1"))
        _account(cur, w.b2, "Seat Rep B2 PENDING", f"seat-rep-b2-{s}", "INDUSTRY_AFFILIATE", "affiliate", parent=w.b)
        _owner(cur, w.b2, w.email("rep-b2"), joined=False)
        _account(cur, w.b1a, "Seat Agent B1a", f"seat-ag-b1a-{s}", "REGULAR", "sponsored_free", sponsor=w.b1)
        _owner(cur, w.b1a, w.email("ag-b1a"))
        _seat(cur, w.b, w.b1)
        _seat(cur, w.b, w.b2)

        # Both companies have a branding row, as Pacific Coast Title does. A
        # company without one is test_a_new_company_can_invite_reps.py's case.
        for co, name in ((w.a, "Seat Co A"), (w.b, "Seat Co B")):
            cur.execute("INSERT INTO affiliate_branding (account_id, brand_display_name) VALUES (%s, %s)",
                        (co, name))
        _account(cur, w.admin, "Seat Platform", f"seat-admin-{s}", "REGULAR", "free")
        _owner(cur, w.admin, w.email("admin"), platform_admin=True)
        conn.commit()

    yield w

    with psycopg.connect(DB_URL, autocommit=False) as conn, conn.cursor() as cur:
        cur.execute(
            "SELECT id::text FROM accounts WHERE id = ANY(%s::uuid[]) "
            "OR parent_account_id = ANY(%s::uuid[]) OR slug LIKE %s",
            (w.fixed, [w.a, w.b], f"%{w.suffix}%"),
        )
        ids = list({r[0] for r in cur.fetchall()} | set(w.fixed))
        cur.execute("SELECT id::text FROM accounts WHERE sponsor_account_id = ANY(%s::uuid[])", (ids,))
        ids = list(set(ids) | {r[0] for r in cur.fetchall()})
        cur.execute("DELETE FROM signup_tokens WHERE account_id = ANY(%s::uuid[])", (ids,))
        cur.execute("DELETE FROM usage_tracking WHERE account_id = ANY(%s::uuid[])", (ids,))
        cur.execute("DELETE FROM email_log WHERE account_id = ANY(%s::uuid[])", (ids,))
        # Before the accounts: a trigger on property_reports rewrites the stats
        # row on delete, and would do it for an account being deleted.
        cur.execute("DELETE FROM property_reports WHERE account_id = ANY(%s::uuid[])", (ids,))
        cur.execute("DELETE FROM property_report_stats WHERE account_id = ANY(%s::uuid[])", (ids,))
        cur.execute("DELETE FROM rep_seat_assignments WHERE company_account_id = ANY(%s::uuid[])", (ids,))
        cur.execute(
            "UPDATE accounts SET parent_account_id = NULL, sponsor_account_id = NULL WHERE id = ANY(%s::uuid[])",
            (ids,),
        )
        cur.execute("DELETE FROM accounts WHERE id = ANY(%s::uuid[])", (ids,))
        conn.commit()


@pytest.fixture(scope="module")
def client():
    from fastapi.testclient import TestClient
    from api.main import app
    return TestClient(app)


@pytest.fixture
def sent(monkeypatch):
    """Every email the seat routes queue, recorded instead of sent."""
    import api.routes.company as company_routes
    out = {"invites": [], "notices": []}
    monkeypatch.setattr(company_routes, "send_role_invite_email",
                        lambda *a, **k: out["invites"].append((a, k)))
    monkeypatch.setattr(company_routes, "send_rep_change_notice_email",
                        lambda *a, **k: out["notices"].append((a, k)))
    return out


def _auth(client, email):
    r = client.post("/v1/auth/login", json={"email": email, "password": PASSWORD})
    assert r.status_code == 200, f"login {email}: {r.status_code} {r.text}"
    return {"Authorization": f"Bearer {r.json()['access_token']}"}


def _q(sql, *params):
    with psycopg.connect(DB_URL) as conn:
        return conn.execute(sql, params).fetchall()


def _open_seat_reps(company):
    return {r[0] for r in _q(
        "SELECT rep_account_id::text FROM rep_seat_assignments "
        "WHERE company_account_id = %s AND ended_at IS NULL", company)}


def _reassign_body(w, who="new", **over):
    body = {"name": f"Seat New Rep {who}", "email": w.email(who), "first_name": "Nia"}
    body.update(over)
    return body


# ── cross-tenant: company A against company B ───────────────────────────────

def test_seat_history_is_only_the_callers(client, world):
    w = world
    resp = client.get("/v1/company/seats", headers=_auth(client, w.email("co-a")))
    assert resp.status_code == 200, resp.text
    reps = {h["rep_id"] for h in resp.json()["history"]}
    assert reps == {w.a1, w.a2}
    assert "SECRET" not in resp.text and "PENDING" not in resp.text
    assert resp.json()["seats"] == {"total": 2, "held": 2, "open": 0, "pending": 0, "idle": 2}


def test_a_company_cannot_reassign_another_companys_rep(client, world, sent):
    w = world
    resp = client.post(f"/v1/company/reps/{w.b1}/reassign",
                       json=_reassign_body(w, "intruder"), headers=_auth(client, w.email("co-a")))
    assert resp.status_code == 404, resp.text
    # Nothing moved, nobody was switched off, nobody was created or written to.
    assert _q("SELECT sponsor_account_id::text FROM accounts WHERE id = %s", w.b1a) == [(w.b1,)]
    assert _q("SELECT is_active FROM users WHERE account_id = %s", w.b1) == [(True,)]
    assert _open_seat_reps(w.b) == {w.b1, w.b2}
    assert _q("SELECT 1 FROM users WHERE email = %s", w.email("intruder")) == []
    assert sent == {"invites": [], "notices": []}


def test_a_company_cannot_send_its_agents_to_another_companys_rep(client, world, sent):
    w = world
    resp = client.post(f"/v1/company/reps/{w.a1}/reassign",
                       json=_reassign_body(w, agents_to_rep_id=w.b1),
                       headers=_auth(client, w.email("co-a")))
    assert resp.status_code == 404, resp.text
    assert {r[0] for r in _q("SELECT sponsor_account_id::text FROM accounts WHERE id = ANY(%s::uuid[])",
                             [w.a1a, w.a1b])} == {w.a1}
    assert _open_seat_reps(w.a) == {w.a1, w.a2}
    assert sent["notices"] == []


def test_a_company_cannot_cancel_another_companys_invite(client, world):
    w = world
    resp = client.post(f"/v1/company/reps/{w.b2}/cancel-invite", headers=_auth(client, w.email("co-a")))
    assert resp.status_code == 404, resp.text
    assert _open_seat_reps(w.b) == {w.b1, w.b2}
    assert _q("SELECT is_active FROM users WHERE account_id = %s", w.b2) == [(True,)]


def test_the_overview_seat_block_is_the_callers(client, world):
    w = world
    a = client.get("/v1/company/overview", headers=_auth(client, w.email("co-a"))).json()
    b = client.get("/v1/company/overview", headers=_auth(client, w.email("co-b"))).json()
    assert a["seats"]["total"] == 2 and a["seats"]["held"] == 2
    assert b["seats"] is None, "company B is not on seats"
    assert "total_agent_seats" not in a["metrics"], "it was the agent count under a seat name"
    assert {r["id"] for r in a["reps"]} == {w.a1, w.a2}


# ── the cap, and the race for the last seat ─────────────────────────────────

def test_an_invite_is_refused_when_every_seat_is_held(client, world, sent):
    w = world
    resp = client.post("/v1/company/invite-rep", headers=_auth(client, w.email("co-a")),
                       json={"name": "Seat Rep A3", "email": w.email("rep-a3"),
                             "first_name": "Al", "last_name": "Three"})
    assert resp.status_code == 409, resp.text
    assert resp.json()["detail"]["error"] == "seats_full"
    assert _q("SELECT 1 FROM users WHERE email = %s", w.email("rep-a3")) == [], "nothing is created"
    assert sent["invites"] == []


def test_a_pending_invite_holds_a_seat_from_the_moment_it_is_sent(client, world, sent):
    w = world
    with psycopg.connect(DB_URL) as conn:
        conn.execute("UPDATE accounts SET rep_seats = 3 WHERE id = %s", (w.a,))
    resp = client.post("/v1/company/invite-rep", headers=_auth(client, w.email("co-a")),
                       json={"name": "Seat Rep A3", "email": w.email("rep-a3"),
                             "first_name": "Al", "last_name": "Three"})
    assert resp.status_code == 200, resp.text
    new = resp.json()["rep_account_id"]
    assert new in _open_seat_reps(w.a)
    seats = client.get("/v1/company/seats", headers=_auth(client, w.email("co-a"))).json()["seats"]
    assert seats["held"] == 3 and seats["open"] == 0 and seats["pending"] == 1


def test_two_invites_for_the_last_seat_cannot_both_take_it(world):
    """The second waits on the company row's lock, then is refused."""
    from api.services import seats
    w = world
    with psycopg.connect(DB_URL, autocommit=False) as conn, conn.cursor() as cur:
        cur.execute("UPDATE accounts SET rep_seats = 3 WHERE id = %s", (w.a,))
        for rid, tag in ((_id(), "x"), (_id(), "y")):
            _account(cur, rid, f"Seat Racer {tag}", f"seat-racer-{tag}-{w.suffix}",
                     "INDUSTRY_AFFILIATE", "affiliate", parent=w.a)
        conn.commit()
    x, y = (r[0] for r in _q(
        "SELECT id::text FROM accounts WHERE slug = ANY(%s) ORDER BY slug",
        [f"seat-racer-x-{w.suffix}", f"seat-racer-y-{w.suffix}"]))

    first = psycopg.connect(DB_URL, autocommit=False)
    outcome = {}

    def second():
        with psycopg.connect(DB_URL, autocommit=False) as conn, conn.cursor() as cur:
            try:
                seats.reserve_seat(cur, w.a)
                seats.open_seat(cur, w.a, y)
                conn.commit()
                outcome["second"] = "took the seat"
            except seats.SeatsFull:
                conn.rollback()
                outcome["second"] = "refused"

    try:
        cur = first.cursor()
        seats.reserve_seat(cur, w.a)
        seats.open_seat(cur, w.a, x)
        t = threading.Thread(target=second)
        t.start()
        time.sleep(0.6)
        waited = t.is_alive()
        first.commit()
        t.join(10)
    finally:
        first.close()
    assert waited, "the second invite did not wait for the first: no lock is held"
    assert outcome.get("second") == "refused", outcome
    assert _open_seat_reps(w.a) == {w.a1, w.a2, x}


def test_the_database_refuses_two_open_seats_for_one_rep(world):
    w = world
    with pytest.raises(psycopg.errors.UniqueViolation):
        with psycopg.connect(DB_URL) as conn:
            _seat(conn.cursor(), w.a, w.a1)


# ── reassignment ────────────────────────────────────────────────────────────

def test_agents_move_with_the_seat_and_are_told_who_their_rep_is(client, world, sent):
    w = world
    resp = client.post(f"/v1/company/reps/{w.a1}/reassign", json=_reassign_body(w),
                       headers=_auth(client, w.email("co-a")))
    assert resp.status_code == 200, resp.text
    new = resp.json()["new_rep_account_id"]
    assert resp.json()["agents_to_rep_id"] == new
    # The agents follow the seat, and only their sponsor changes.
    rows = _q("SELECT sponsor_account_id::text, plan_slug FROM accounts WHERE id = ANY(%s::uuid[])",
              [w.a1a, w.a1b])
    assert rows == [(new, "sponsored_free")] * 2
    # The leaving rep is switched off; the seat count is unchanged.
    assert _q("SELECT is_active FROM users WHERE account_id = %s", w.a1) == [(False,)]
    assert _open_seat_reps(w.a) == {new, w.a2}
    hist = _q("SELECT ended_reason, successor_rep_account_id::text, agents_moved, ended_by_user_id::text "
              "FROM rep_seat_assignments WHERE rep_account_id = %s", w.a1)
    assert hist == [("reassigned", new, 2, w.a)]
    # One invite to the new rep, one notice per agent naming them.
    assert [a[0] for a, _ in sent["invites"]] == [w.email("new")]
    told = {(a[0], k["new_rep_name"], k["new_rep_email"]) for a, k in sent["notices"]}
    assert told == {(w.email("ag-a1a"), "Seat New Rep new", w.email("new")),
                    (w.email("ag-a1b"), "Seat New Rep new", w.email("new"))}


def test_the_company_can_send_the_agents_to_another_of_its_reps(client, world, sent):
    w = world
    resp = client.post(f"/v1/company/reps/{w.a1}/reassign",
                       json=_reassign_body(w, agents_to_rep_id=w.a2),
                       headers=_auth(client, w.email("co-a")))
    assert resp.status_code == 200, resp.text
    assert {r[0] for r in _q("SELECT sponsor_account_id::text FROM accounts WHERE id = ANY(%s::uuid[])",
                             [w.a1a, w.a1b])} == {w.a2}
    assert {k["new_rep_name"] for _, k in sent["notices"]} == {"Seat Rep A2"}
    assert {k["new_rep_email"] for _, k in sent["notices"]} == {w.email("rep-a2")}


def test_the_history_records_the_move(client, world, sent):
    w = world
    auth = _auth(client, w.email("co-a"))
    client.post(f"/v1/company/reps/{w.a1}/reassign", json=_reassign_body(w), headers=auth)
    history = client.get("/v1/company/seats", headers=auth).json()["history"]
    moved = [h for h in history if h["rep_id"] == w.a1]
    assert len(moved) == 1 and moved[0]["ended_reason"] == "reassigned"
    assert moved[0]["successor_name"] == "Seat New Rep new" and moved[0]["agents_moved"] == 2


def test_agents_cannot_be_sent_to_the_rep_who_is_leaving(client, world, sent):
    w = world
    resp = client.post(f"/v1/company/reps/{w.a1}/reassign",
                       json=_reassign_body(w, agents_to_rep_id=w.a1),
                       headers=_auth(client, w.email("co-a")))
    assert resp.status_code == 409, resp.text
    assert _open_seat_reps(w.a) == {w.a1, w.a2}


# ── cancelling a pending invite ─────────────────────────────────────────────

def test_cancelling_a_pending_invite_frees_its_seat(client, world):
    w = world
    resp = client.post(f"/v1/company/reps/{w.b2}/cancel-invite", headers=_auth(client, w.email("co-b")))
    assert resp.status_code == 200, resp.text
    assert _open_seat_reps(w.b) == {w.b1}
    assert _q("SELECT ended_reason FROM rep_seat_assignments WHERE rep_account_id = %s", w.b2) == [("invite_cancelled",)]
    assert _q("SELECT used FROM signup_tokens WHERE account_id = %s", w.b2) == [(True,)], "the link must stop working"


def test_a_joined_reps_seat_is_not_cancelled_it_is_reassigned(client, world):
    """Rep A2 has joined and has NO agents, so this is the joined rule on its
    own: a rep with agents is refused by the agents check as well, and testing
    on one would not show which rule held."""
    w = world
    resp = client.post(f"/v1/company/reps/{w.a2}/cancel-invite", headers=_auth(client, w.email("co-a")))
    assert resp.status_code == 409, resp.text
    assert _open_seat_reps(w.a) == {w.a1, w.a2}
    assert _q("SELECT is_active FROM users WHERE account_id = %s", w.a2) == [(True,)]


# ── idle ────────────────────────────────────────────────────────────────────

def _idle(cur_company):
    from api.services import seats
    with psycopg.connect(DB_URL) as conn, conn.cursor() as cur:
        return seats.idle_rep_ids(cur, cur_company)


def test_a_rep_is_idle_until_an_agent_finishes_a_report_in_30_days(world):
    w = world
    assert _idle(w.a) == {w.a1, w.a2}, "no reports anywhere: both idle (A2 has no agents)"
    with psycopg.connect(DB_URL) as conn:
        conn.execute(
            "INSERT INTO report_generations (id, account_id, report_type, cities, status, generated_at) "
            "VALUES (gen_random_uuid(), %s, 'closed', ARRAY['X'], 'completed', now() - interval '40 days')",
            (w.a1a,))
    assert w.a1 in _idle(w.a), "a report 40 days old does not count"
    with psycopg.connect(DB_URL) as conn:
        conn.execute(
            "INSERT INTO report_generations (id, account_id, report_type, cities, status, generated_at) "
            "VALUES (gen_random_uuid(), %s, 'closed', ARRAY['X'], 'failed', now())", (w.a1a,))
    assert w.a1 in _idle(w.a), "a failed report is not a report"


def test_a_property_report_alone_makes_a_rep_not_idle(world):
    """`property_reports.status` is 'complete', not 'completed'."""
    w = world
    with psycopg.connect(DB_URL) as conn:
        conn.execute(
            "INSERT INTO property_reports (id, account_id, report_type, property_address, property_city, property_state, property_zip, status, created_at) "
            "VALUES (gen_random_uuid(), %s, 'seller', '1 Seat St', 'Irvine', 'CA', '92618', 'complete', now())", (w.a1b,))
    assert _idle(w.a) == {w.a2}


def test_a_pending_invite_is_pending_not_idle(world):
    w = world
    assert w.b2 not in _idle(w.b)


# ── the platform admin's seat count ─────────────────────────────────────────

def test_only_the_platform_admin_sets_the_seat_count(client, world):
    w = world
    as_company = client.put(f"/v1/admin/companies/{w.b}/rep-seats", json={"rep_seats": 9},
                            headers=_auth(client, w.email("co-b")))
    assert as_company.status_code == 403
    admin = _auth(client, w.email("admin"))
    assert client.put(f"/v1/admin/companies/{w.b}/rep-seats", json={"rep_seats": 5},
                      headers=admin).status_code == 200
    assert _q("SELECT rep_seats FROM accounts WHERE id = %s", w.b) == [(5,)]
    below = client.put(f"/v1/admin/companies/{w.b}/rep-seats", json={"rep_seats": 1}, headers=admin)
    assert below.status_code == 409, "two seats are held, the pending invite included"
    assert client.put(f"/v1/admin/companies/{w.b}/rep-seats", json={"rep_seats": None},
                      headers=admin).status_code == 200
    assert _q("SELECT rep_seats FROM accounts WHERE id = %s", w.b) == [(None,)]


def test_the_database_refuses_a_seat_count_on_a_non_company(world):
    w = world
    with pytest.raises(psycopg.errors.CheckViolation):
        with psycopg.connect(DB_URL) as conn:
            conn.execute("UPDATE accounts SET rep_seats = 1 WHERE id = %s", (w.a1,))


# ── the backfill ────────────────────────────────────────────────────────────

def _backfill_sql():
    src = (REPO / "db/migrations/0060_rep_seats.sql").read_text(encoding="utf-8")
    m = re.search(r"^INSERT INTO rep_seat_assignments.*?;$", src, re.S | re.M)
    assert m, "the backfill INSERT is not in 0060"
    return m.group(0)


def test_the_backfill_seats_every_current_rep_once_and_changes_no_account(world):
    w = world
    with psycopg.connect(DB_URL, autocommit=False) as conn, conn.cursor() as cur:
        cur.execute("DELETE FROM rep_seat_assignments WHERE company_account_id = ANY(%s::uuid[])", ([w.a, w.b],))
        # A deactivated rep is not using a seat and gets none.
        cur.execute("UPDATE users SET is_active = FALSE WHERE account_id = %s", (w.a2,))
        cur.execute("SELECT id, sponsor_account_id, parent_account_id, plan_slug, is_active, updated_at "
                    "FROM accounts WHERE id = ANY(%s::uuid[]) ORDER BY id", (w.fixed,))
        before = cur.fetchall()
        cur.execute(_backfill_sql())
        cur.execute(_backfill_sql())          # idempotent
        cur.execute("SELECT id, sponsor_account_id, parent_account_id, plan_slug, is_active, updated_at "
                    "FROM accounts WHERE id = ANY(%s::uuid[]) ORDER BY id", (w.fixed,))
        after = cur.fetchall()
        cur.execute("SELECT rep_account_id::text, started_at = (SELECT created_at FROM accounts WHERE id = rep_account_id) "
                    "FROM rep_seat_assignments WHERE company_account_id = ANY(%s::uuid[]) AND ended_at IS NULL",
                    ([w.a, w.b],))
        rows = cur.fetchall()
        conn.commit()
    assert before == after, "the backfill wrote to an account"
    assert sorted(r[0] for r in rows) == sorted([w.a1, w.b1, w.b2]), rows
    assert all(r[1] for r in rows), "each seat is dated from its rep's account creation"


# ── the leaving rep's scheduled sends go where the agents go ────────────────
#
# Asserted through the WORKER's own recipient resolution, against the account
# the schedule now belongs to: "handed over" means the next run still reaches
# the same people, not that a column changed.

def _worker_resolve(account_id, recipients):
    import sys
    sys.path.insert(0, str(REPO / "apps/worker/src"))
    from worker.tasks import resolve_recipients_to_emails
    with psycopg.connect(DB_URL) as conn, conn.cursor() as cur:
        return sorted(resolve_recipients_to_emails(cur, account_id, recipients))


def _book(cur, w):
    """Rep A1's book: a contact, a group holding that contact and agent A1a,
    a schedule sending to the contact, the group, agent A1b and a typed-in
    address, and one recipient who unsubscribed from A1."""
    import json
    contact, group, sched = _id(), _id(), _id()
    cur.execute("INSERT INTO contacts (id, account_id, name, email, type) VALUES (%s,%s,'Cli',%s,'client')",
                (contact, w.a1, w.email("client")))
    cur.execute("INSERT INTO contact_groups (id, account_id, name) VALUES (%s,%s,'Book')", (group, w.a1))
    for kind, member in (("contact", contact), ("sponsored_agent", w.a1a)):
        cur.execute("INSERT INTO contact_group_members (group_id, account_id, member_type, member_id) "
                    "VALUES (%s,%s,%s,%s)", (group, w.a1, kind, member))
    recipients = [json.dumps({"type": "contact", "id": contact}),
                  json.dumps({"type": "group", "id": group}),
                  json.dumps({"type": "sponsored_agent", "id": w.a1b}),
                  json.dumps({"type": "manual_email", "email": w.email("typed")})]
    cur.execute("INSERT INTO schedules (id, account_id, name, report_type, city, cadence, recipients, active) "
                "VALUES (%s,%s,'A1 weekly','market_snapshot','Irvine','weekly',%s,true)", (sched, w.a1, recipients))
    cur.execute("INSERT INTO email_suppressions (account_id, email, reason) VALUES (%s,%s,'user_request')",
                (w.a1, w.email("opted-out")))
    return sched, recipients


@pytest.fixture
def book(world):
    with psycopg.connect(DB_URL) as conn, conn.cursor() as cur:
        return _book(cur, world)


def test_the_schedules_follow_the_agents_and_still_reach_everyone(client, world, book, sent):
    w, (sched, recipients) = world, book
    before = _worker_resolve(w.a1, recipients)
    assert before == sorted([w.email("client"), w.email("ag-a1a"), w.email("ag-a1b"), w.email("typed")])
    resp = client.post(f"/v1/company/reps/{w.a1}/reassign", json=_reassign_body(w),
                       headers=_auth(client, w.email("co-a")))
    assert resp.status_code == 200, resp.text
    new = resp.json()["new_rep_account_id"]
    assert resp.json()["schedules_moved"] == 1
    assert _q("SELECT account_id::text, active FROM schedules WHERE id = %s", sched) == [(new, True)]
    assert _worker_resolve(new, recipients) == before, "the handed-over schedule reaches different people"
    assert _q("SELECT book_to_account_id::text, schedules_moved FROM rep_seat_assignments "
              "WHERE rep_account_id = %s", w.a1) == [(new, 1)]


def test_an_unsubscribe_follows_the_schedules(client, world, book, sent):
    w = world
    client.post(f"/v1/company/reps/{w.a1}/reassign", json=_reassign_body(w), headers=_auth(client, w.email("co-a")))
    new = _q("SELECT successor_rep_account_id::text FROM rep_seat_assignments WHERE rep_account_id = %s", w.a1)[0][0]
    rows = _q("SELECT account_id::text FROM email_suppressions WHERE email = %s", w.email("opted-out"))
    assert sorted(r[0] for r in rows) == sorted([w.a1, new]), "they opted out; the new name must not mail them"


def test_the_schedules_go_to_the_rep_the_agents_go_to(client, world, book, sent):
    w, (sched, recipients) = world, book
    before = _worker_resolve(w.a1, recipients)
    resp = client.post(f"/v1/company/reps/{w.a1}/reassign", json=_reassign_body(w, agents_to_rep_id=w.a2),
                       headers=_auth(client, w.email("co-a")))
    assert resp.status_code == 200, resp.text
    assert _q("SELECT account_id::text FROM schedules WHERE id = %s", sched) == [(w.a2,)]
    assert _worker_resolve(w.a2, recipients) == before


def test_a_link_sent_before_the_move_stops_the_sends_after_it(client, world, book, sent):
    """The token was signed for A1. The schedule is the new rep's now."""
    w = world
    with psycopg.connect(DB_URL) as conn:
        conn.execute("INSERT INTO email_log (account_id, provider, to_emails, subject, status) "
                     "VALUES (%s, 'sendgrid', ARRAY[%s], 's', 'sent')", (w.a1, w.email("typed")))
    client.post(f"/v1/company/reps/{w.a1}/reassign", json=_reassign_body(w), headers=_auth(client, w.email("co-a")))
    new = _q("SELECT successor_rep_account_id::text FROM rep_seat_assignments WHERE rep_account_id = %s", w.a1)[0][0]
    from api.routes.unsubscribe import generate_unsubscribe_token
    r = client.post("/v1/email/unsubscribe",
                    json={"email": w.email("typed"), "token": generate_unsubscribe_token(w.a1, w.email("typed"))})
    assert r.status_code == 200, r.text
    rows = _q("SELECT email FROM email_suppressions WHERE account_id = %s AND email = ANY(%s)",
              new, [w.email("typed")])
    assert rows == [(w.email("typed"),)], "the new rep's next run would still mail them"

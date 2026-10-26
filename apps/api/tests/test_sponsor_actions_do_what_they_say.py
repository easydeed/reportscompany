"""
The rep's agent actions do what their labels say (D-273), and bulk invite is bounded.

"Deactivate" and "Cancel Invitation" both call `/accounts/{id}/deactivate`.
Until this change it set `accounts.is_active`, which nothing reads: the agent
kept signing in, kept sending, kept showing "active", and a cancelled invite
link still worked. Each test here is one of those effects, measured where it
lives — the login route, the session check, the accept-invite route, the
schedule sender's own predicate, the rep's list.

Bulk invite had no ceiling on rows or bytes and no dedupe within a file.

Integration tests: they need a real database and skip cleanly without one.
"""
import io
import os
import sys
import uuid
from pathlib import Path

import pytest

DB_URL = os.getenv("TEST_DATABASE_URL") or os.getenv("DATABASE_URL")

psycopg = pytest.importorskip("psycopg", reason="psycopg is required for integration tests")
pytestmark = pytest.mark.skipif(
    not DB_URL, reason="Set DATABASE_URL (or TEST_DATABASE_URL) to run these tests"
)

PASSWORD = "ActionsTest123!"
WORKER_SRC = Path(__file__).resolve().parents[2] / "worker" / "src"


class World:
    def __init__(self):
        self.aff = str(uuid.uuid4())
        self.agent = str(uuid.uuid4())
        self.invitee = str(uuid.uuid4())
        self.token = f"act-{uuid.uuid4().hex}"
        self.suffix = self.aff[:8]

    def email(self, who):
        return f"act-{who}-{self.suffix}@test-tenant.example.com"

    @property
    def ids(self):
        return [self.aff, self.agent, self.invitee]


def _account(cur, aid, name, typ, plan, sponsor=None):
    cur.execute(
        "INSERT INTO accounts (id, name, slug, account_type, plan_slug, status, is_active, sponsor_account_id, created_at, updated_at) "
        "VALUES (%s,%s,%s,%s,%s,'active',true,%s,now(),now())",
        (aid, name, f"{name.lower().replace(' ', '-')}-{aid[:8]}", typ, plan, sponsor),
    )


def _owner(cur, aid, email, joined=True):
    cur.execute(
        "INSERT INTO users (id, account_id, email, password_hash, role, email_verified, is_active, created_at, updated_at) "
        "VALUES (%s,%s,%s, CASE WHEN %s THEN crypt(%s, gen_salt('bf')) END, 'OWNER', %s, true, now(), now())",
        (aid, aid, email, joined, PASSWORD, joined),
    )
    cur.execute("INSERT INTO account_users (account_id, user_id, role, created_at) VALUES (%s,%s,'OWNER',now())", (aid, aid))


@pytest.fixture(scope="module")
def world():
    w = World()
    with psycopg.connect(DB_URL) as conn, conn.cursor() as cur:
        cur.execute("CREATE EXTENSION IF NOT EXISTS pgcrypto;")
        _account(cur, w.aff, "ACT Affiliate", "INDUSTRY_AFFILIATE", "affiliate")
        _owner(cur, w.aff, w.email("aff"))
        _account(cur, w.agent, "ACT Agent", "REGULAR", "sponsored_free", sponsor=w.aff)
        _owner(cur, w.agent, w.email("agent"))
        _account(cur, w.invitee, "ACT Invitee", "REGULAR", "sponsored_free", sponsor=w.aff)
        _owner(cur, w.invitee, w.email("invitee"), joined=False)
        cur.execute(
            "INSERT INTO signup_tokens (token, user_id, account_id, expires_at) VALUES (%s,%s,%s, now() + interval '7 days')",
            (w.token, w.invitee, w.invitee),
        )
        conn.commit()
    yield w
    with psycopg.connect(DB_URL) as conn, conn.cursor() as cur:
        cur.execute("SELECT id::text FROM accounts WHERE sponsor_account_id = %s", (w.aff,))
        ids = w.ids + [r[0] for r in cur.fetchall()]
        for table in ("signup_tokens", "account_users", "users"):
            cur.execute(f"DELETE FROM {table} WHERE account_id = ANY(%s::uuid[])", (ids,))
        cur.execute("UPDATE accounts SET sponsor_account_id = NULL WHERE id = ANY(%s::uuid[])", (ids,))
        cur.execute("DELETE FROM accounts WHERE id = ANY(%s::uuid[])", (ids,))
        conn.commit()


@pytest.fixture(scope="module")
def client():
    from fastapi.testclient import TestClient
    from api.main import app

    return TestClient(app)


def _login(client, email):
    return client.post("/v1/auth/login", json={"email": email, "password": PASSWORD})


def _auth(client, email):
    r = _login(client, email)
    assert r.status_code == 200, r.text
    return {"Authorization": f"Bearer {r.json()['access_token']}"}


def _status(client, aff_auth, account_id):
    r = client.get("/v1/affiliate/overview", headers=aff_auth)
    return next(a["status"] for a in r.json()["sponsored_accounts"] if a["account_id"] == account_id)


def _can_send(account_id):
    if str(WORKER_SRC) not in sys.path:
        sys.path.insert(0, str(WORKER_SRC))
    from worker.schedules_tick import account_can_send

    with psycopg.connect(DB_URL) as conn, conn.cursor() as cur:
        return account_can_send(cur, account_id)


# ── Deactivate / Reactivate ─────────────────────────────────────────────────

def test_deactivate_does_what_the_label_says_and_reactivate_undoes_it(client, world):
    aff = _auth(client, world.email("aff"))
    agent_session = _auth(client, world.email("agent"))
    assert client.get("/v1/account", headers=agent_session).status_code == 200
    assert _can_send(world.agent) is True

    assert client.post(f"/v1/affiliate/accounts/{world.agent}/deactivate", headers=aff).status_code == 200

    assert _login(client, world.email("agent")).status_code != 200, "a deactivated agent can still sign in"
    assert client.get("/v1/account", headers=agent_session).status_code == 401, "their existing session still works"
    assert _can_send(world.agent) is False, "their schedules would still send"
    assert _status(client, aff, world.agent) == "deactivated", "the rep's list does not show it"

    assert client.post(f"/v1/affiliate/accounts/{world.agent}/reactivate", headers=aff).status_code == 200
    assert _login(client, world.email("agent")).status_code == 200
    assert _can_send(world.agent) is True
    assert _status(client, aff, world.agent) == "active"


# ── Cancel Invitation ───────────────────────────────────────────────────────

def test_cancel_invitation_stops_the_invite_link(client, world):
    aff = _auth(client, world.email("aff"))
    assert _status(client, aff, world.invitee) == "pending"

    assert client.post(f"/v1/affiliate/accounts/{world.invitee}/deactivate", headers=aff).status_code == 200

    r = client.post("/v1/auth/accept-invite", json={"token": world.token, "password": "Whatever123!"})
    assert r.status_code == 400, f"a cancelled invite still works: {r.status_code} {r.text[:200]}"
    assert _status(client, aff, world.invitee) == "deactivated", "a cancelled invite still reads 'pending'"


    # Reactivating the invitee must not revive the link that was cancelled;
    # Resend is what issues a working one.
    assert client.post(f"/v1/affiliate/accounts/{world.invitee}/reactivate", headers=aff).status_code == 200
    r = client.post("/v1/auth/accept-invite", json={"token": world.token, "password": "Whatever123!"})
    assert r.status_code == 400, f"reactivation revived the cancelled link: {r.status_code} {r.text[:200]}"
    assert client.post("/v1/affiliate/resend-invite", headers=aff, json={"email": world.email("invitee")}).status_code == 200
    with psycopg.connect(DB_URL) as conn, conn.cursor() as cur:
        cur.execute("SELECT token FROM signup_tokens WHERE account_id = %s AND used = FALSE", (world.invitee,))
        fresh = cur.fetchone()
    assert fresh, "Resend issued no new token"
    r = client.post("/v1/auth/accept-invite", json={"token": fresh[0], "password": "Whatever123!"})
    assert r.status_code == 200, f"the resent link does not work: {r.status_code} {r.text[:200]}"


# ── Bulk invite ─────────────────────────────────────────────────────────────

def _csv(rows):
    return ("name,email\n" + "\n".join(f"{n},{e}" for n, e in rows) + "\n").encode()


def _bulk(client, aff, payload):
    return client.post("/v1/affiliate/bulk-invite", headers=aff,
                       files={"file": ("agents.csv", io.BytesIO(payload), "text/csv")})


def test_bulk_invite_over_the_row_limit_invites_nobody(client, world):
    from api.routes.affiliates import BULK_INVITE_MAX_ROWS

    aff = _auth(client, world.email("aff"))
    rows = [(f"Over {i}", f"act-over-{i}-{world.suffix}@test-tenant.example.com") for i in range(BULK_INVITE_MAX_ROWS + 1)]
    r = _bulk(client, aff, _csv(rows))
    assert r.status_code == 400, f"{r.status_code} {r.text[:200]}"
    with psycopg.connect(DB_URL) as conn, conn.cursor() as cur:
        cur.execute("SELECT count(*) FROM users WHERE email LIKE %s", (f"act-over-%-{world.suffix}@%",))
        assert cur.fetchone()[0] == 0, "rows were created before the limit refused the file"


def test_bulk_invite_over_the_size_limit_is_refused(client, world):
    from api.routes.affiliates import BULK_INVITE_MAX_BYTES

    aff = _auth(client, world.email("aff"))
    r = _bulk(client, aff, b"name,email\n" + b"x" * (BULK_INVITE_MAX_BYTES + 1))
    assert r.status_code == 413, f"{r.status_code} {r.text[:200]}"


def test_bulk_invite_dedupes_within_the_file(client, world):
    aff = _auth(client, world.email("aff"))
    dup = f"act-dup-{world.suffix}@test-tenant.example.com"
    r = _bulk(client, aff, _csv([("Dup One", dup), ("Dup Two", dup.upper())]))
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["invited"] == 1 and body["skipped"] == 1
    assert body["errors"][0]["reason"] == "duplicate of row 2"

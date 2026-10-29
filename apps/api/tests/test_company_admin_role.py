"""D-280: only the company's admin can use the company's admin actions.

`get_company_admin` checked only that the ACCOUNT was a title company, so any
user on the account could reassign a rep's seat (which signs that rep out for
good), cancel invites, invite reps and change the brand. Now the user's own
role on the account (`account_users.role`) must be OWNER; any other user on the
account reads everything and changes nothing.

Against a real database, on `test_rep_seats.World`, with one more person:
"Morgan", a MEMBER of company A. Every refusal also checks that nothing moved —
a 403 that ran half the write first would pass a status-code test.
"""
import uuid

import pytest

from test_rep_seats import (  # noqa: F401 — pytest fixtures, used by name
    PASSWORD, _auth, _q, _reassign_body, client, sent, world,
)

psycopg = pytest.importorskip("psycopg")
import os  # noqa: E402

DB_URL = os.getenv("DATABASE_URL")


@pytest.fixture
def member(world):
    """A second user on company A, role MEMBER."""
    uid = str(uuid.uuid4())
    email = world.email("member-a")
    with psycopg.connect(DB_URL, autocommit=False) as conn, conn.cursor() as cur:
        cur.execute(
            """INSERT INTO users (id, account_id, email, password_hash, role, email_verified,
                                  is_active, first_name, created_at, updated_at)
               VALUES (%s, %s, %s, crypt(%s, gen_salt('bf')), 'member', true, true, 'Morgan', now(), now())""",
            (uid, world.a, email, PASSWORD))
        cur.execute("INSERT INTO account_users (account_id, user_id, role, created_at) VALUES (%s, %s, 'MEMBER', now())",
                    (world.a, uid))
        conn.commit()
    yield {"id": uid, "email": email}
    with psycopg.connect(DB_URL, autocommit=False) as conn, conn.cursor() as cur:
        cur.execute("DELETE FROM account_users WHERE user_id = %s", (uid,))
        cur.execute("DELETE FROM users WHERE id = %s", (uid,))
        conn.commit()


READS = ["/v1/company/overview", "/v1/company/reps", "/v1/company/agents", "/v1/company/seats",
         "/v1/company/branding", "/v1/company/reports", "/v1/company/schedules", "/v1/company/metrics"]


@pytest.mark.parametrize("path", READS)
def test_a_member_can_read_every_company_view(client, world, member, path):
    resp = client.get(path, headers=_auth(client, member["email"]))
    assert resp.status_code == 200, f"{path}: {resp.status_code} {resp.text[:200]}"


def test_the_views_say_who_can_act(client, world, member):
    as_member = _auth(client, member["email"])
    as_owner = _auth(client, world.email("co-a"))
    for path in ("/v1/company/overview", "/v1/company/reps", "/v1/company/branding"):
        assert client.get(path, headers=as_member).json()["can_manage"] is False, path
        assert client.get(path, headers=as_owner).json()["can_manage"] is True, path


def _state(w):
    """Everything an admin action could change, for company A."""
    return {
        "seats": sorted(_q("SELECT rep_account_id::text, ended_at IS NULL FROM rep_seat_assignments "
                           "WHERE company_account_id = %s", w.a)),
        "users": sorted(_q("SELECT email, is_active FROM users WHERE account_id IN "
                           "(SELECT id FROM accounts WHERE parent_account_id = %s)", w.a)),
        "sponsors": sorted(_q("SELECT id::text, sponsor_account_id::text FROM accounts "
                              "WHERE sponsor_account_id IN (SELECT id FROM accounts WHERE parent_account_id = %s)", w.a)),
        "brand": _q("SELECT brand_display_name, primary_color FROM affiliate_branding WHERE account_id = %s", w.a),
        "tokens": _q("SELECT count(*) FROM signup_tokens WHERE account_id IN "
                     "(SELECT id FROM accounts WHERE parent_account_id = %s)", w.a),
    }


def _admin_actions(w):
    return [
        ("POST", f"/v1/company/reps/{w.a1}/reassign", _reassign_body(w, "by-member")),
        ("POST", f"/v1/company/reps/{w.a2}/cancel-invite", None),
        ("POST", "/v1/company/invite-rep",
         {"name": "Member Invite", "email": w.email("member-invite"), "first_name": "Member", "last_name": "Invite"}),
        ("POST", "/v1/company/resend-rep-invite", {"email": w.email("rep-a1")}),
        ("PATCH", "/v1/company/branding", {"brand_display_name": "Changed by a member", "primary_color": "#123456"}),
    ]


@pytest.mark.parametrize("i", range(5), ids=["reassign", "cancel-invite", "invite-rep", "resend-invite", "branding"])
def test_a_member_cannot_use_an_admin_action_and_nothing_changes(client, world, member, sent, i):
    method, path, body = _admin_actions(world)[i]
    before = _state(world)
    resp = client.request(method, path, json=body, headers=_auth(client, member["email"]))
    assert resp.status_code == 403, f"{method} {path}: {resp.status_code} {resp.text[:200]}"
    assert "admin" in resp.json()["detail"]
    assert _state(world) == before, "a refused action changed something"
    assert sent == {"invites": [], "notices": []}, "a refused action sent email"


def test_the_owner_still_can(client, world, sent):
    """POSITIVE CONTROL: the same reassignment, by the company's OWNER."""
    resp = client.post(f"/v1/company/reps/{world.a1}/reassign", json=_reassign_body(world, "by-owner"),
                       headers=_auth(client, world.email("co-a")))
    assert resp.status_code == 200, resp.text


def test_a_user_with_no_role_on_the_account_reads_nothing(client, world, member):
    """A user whose home is the company but who has no account_users row is
    nobody on it: refused, not treated as its admin."""
    with psycopg.connect(DB_URL) as conn:
        conn.execute("DELETE FROM account_users WHERE user_id = %s", (member["id"],))
    resp = client.get("/v1/company/reps", headers=_auth(client, member["email"]))
    assert resp.status_code in (401, 403), resp.text


def test_another_companys_owner_is_refused_on_this_company(client, world, sent):
    """Cross-tenant still holds with the role check in front of it: B's admin
    is an admin, of B, and A's rep is not B's."""
    before = _state(world)
    resp = client.post(f"/v1/company/reps/{world.a1}/reassign", json=_reassign_body(world, "by-b"),
                       headers=_auth(client, world.email("co-b")))
    assert resp.status_code == 404, resp.text
    assert _state(world) == before

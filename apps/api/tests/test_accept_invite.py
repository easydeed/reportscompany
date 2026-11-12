"""
Accepting an invitation is single-use and atomic (LR-017, D-376).

`/v1/auth/accept-invite` read the token's `used` flag without a lock, then set
the password and the flag unconditionally. Two concurrent accepts both
succeeded in four of four review runs and the last password won; a seat
cancelled during acceptance was accepted anyway. Validation, consumption and
the password now happen in one transaction: the user row is locked first (the
order seat cancellation takes), then the token is claimed by a conditional
UPDATE that the loser of any race cannot match.

These run against real PostgreSQL. They replace mock-cursor tests that replayed
query results in order and so could never see a race.
"""
import os
import threading
import uuid

import pytest

DB_URL = os.getenv("DATABASE_URL")
psycopg = pytest.importorskip("psycopg")
pytestmark = pytest.mark.skipif(not DB_URL, reason="Set DATABASE_URL to run these tests")

OLD_HASH = "$2b$12$abcdefghijklmnopqrstuuJ8uL0V9Qq5xY0y6h6Q1y5vYq2r3s4t."   # never a valid login


def _q(sql, *p):
    with psycopg.connect(DB_URL, autocommit=True) as conn:
        cur = conn.execute(sql, p)
        return cur.fetchall() if cur.description else None


class Invitee:
    """One sponsor, one invited agent with no password yet, one token."""

    def __init__(self, *, expires="now() + interval '7 days'", active=True):
        self.sponsor, self.account = str(uuid.uuid4()), str(uuid.uuid4())
        self.user = self.account
        self.token = f"lr017-{uuid.uuid4().hex}"
        tag = self.account[:8]
        for aid, name, typ, plan, sponsor in (
            (self.sponsor, "LR017 Sponsor", "INDUSTRY_AFFILIATE", "affiliate", None),
            (self.account, "LR017 Invitee", "REGULAR", "sponsored_free", self.sponsor),
        ):
            _q("INSERT INTO accounts (id, name, slug, account_type, plan_slug, status, is_active, "
               "sponsor_account_id, created_at, updated_at) VALUES (%s,%s,%s,%s,%s,'active',true,%s,now(),now())",
               aid, name, f"lr017-{aid[:8]}", typ, plan, sponsor)
        _q("INSERT INTO users (id, account_id, email, password_hash, role, email_verified, is_active, "
           "created_at, updated_at) VALUES (%s,%s,%s,%s,'OWNER',false,%s,now(),now())",
           self.user, self.account, f"lr017-{tag}@test-tenant.example.com", OLD_HASH, active)
        _q("INSERT INTO account_users (account_id, user_id, role, created_at) VALUES (%s,%s,'OWNER',now())",
           self.account, self.user)
        _q(f"INSERT INTO signup_tokens (token, user_id, account_id, expires_at) VALUES (%s,%s,%s,{expires})",
           self.token, self.user, self.account)

    def password_hash(self):
        return _q("SELECT password_hash FROM users WHERE id = %s", self.user)[0][0]

    def token_used(self):
        return _q("SELECT used FROM signup_tokens WHERE token = %s", self.token)[0][0]

    def drop(self):
        ids = [self.account, self.sponsor]
        _q("DELETE FROM signup_tokens WHERE user_id = %s OR token = %s", self.user, self.token)
        for table in ("signup_tokens", "contact_groups", "account_users", "users"):
            _q(f"DELETE FROM {table} WHERE account_id = ANY(%s::uuid[])", ids)
        _q("UPDATE accounts SET sponsor_account_id = NULL WHERE id = ANY(%s::uuid[])", ids)
        _q("DELETE FROM accounts WHERE id = ANY(%s::uuid[])", ids)


@pytest.fixture
def invitee():
    made = []

    def make(**kw):
        made.append(Invitee(**kw))
        return made[-1]
    yield make
    for i in made:
        i.drop()


@pytest.fixture(scope="module")
def client():
    from fastapi.testclient import TestClient
    from api.main import app
    return TestClient(app)


def _accept(client, token, password="SecurePass123!"):
    return client.post("/v1/auth/accept-invite", json={"token": token, "password": password})


def _verify(hash_, password):
    from api.auth import check_password
    return check_password(password, hash_)


# ── the ordinary cases, on the real schema ──────────────────────────────────

def test_a_valid_invitation_sets_the_password_spends_the_token_and_signs_in(client, invitee):
    i = invitee()
    r = _accept(client, i.token)
    assert r.status_code == 200, r.text
    assert i.token_used() is True
    assert _verify(i.password_hash(), "SecurePass123!")
    assert _q("SELECT email_verified FROM users WHERE id = %s", i.user)[0][0] is True
    assert "mr_token" in r.headers.get("set-cookie", "")


def test_whitespace_around_the_token_is_ignored(client, invitee):
    i = invitee()
    assert _accept(client, f"  {i.token}\n").status_code == 200


@pytest.mark.parametrize("password,code", [("short7!", 400), ("Exactly8", 200)])
def test_the_password_minimum_is_eight(client, invitee, password, code):
    i = invitee()
    r = _accept(client, i.token, password)
    assert r.status_code == code, r.text
    if code == 400:
        assert i.token_used() is False and i.password_hash() == OLD_HASH


def test_an_unknown_token_is_refused(client):
    r = _accept(client, f"lr017-missing-{uuid.uuid4().hex}")
    assert r.status_code == 400 and r.json()["detail"]["error"] == "invalid_token"


def test_an_expired_token_is_refused_and_changes_nothing(client, invitee):
    i = invitee(expires="now() - interval '1 minute'")
    r = _accept(client, i.token)
    assert r.status_code == 400 and r.json()["detail"]["error"] == "invalid_token"
    assert i.password_hash() == OLD_HASH and i.token_used() is False


def test_a_token_is_accepted_once_and_never_again(client, invitee):
    i = invitee()
    assert _accept(client, i.token, "FirstPass123!").status_code == 200
    r = _accept(client, i.token, "SecondPass123!")
    assert r.status_code == 400 and r.json()["detail"]["error"] == "invalid_token"
    assert _verify(i.password_hash(), "FirstPass123!"), "a repeated accept replaced the password"


def test_a_deactivated_user_is_refused_and_the_token_is_left_unused(client, invitee):
    i = invitee(active=False)
    r = _accept(client, i.token)
    assert r.status_code == 400 and r.json()["detail"]["error"] == "account_inactive"
    assert i.token_used() is False and i.password_hash() == OLD_HASH


def test_a_token_naming_another_account_signs_nobody_in(client, invitee):
    i, other = invitee(), invitee()
    _q("UPDATE signup_tokens SET account_id = %s WHERE token = %s", other.account, i.token)
    r = _accept(client, i.token)
    assert r.status_code == 400 and r.json()["detail"]["error"] == "invalid_token"
    assert i.password_hash() == OLD_HASH and i.token_used() is False


def test_a_failure_after_the_claim_rolls_the_claim_back(client, invitee, monkeypatch):
    from api.routes import auth as auth_route
    i = invitee()

    def broken(_):
        raise RuntimeError("hashing unavailable")
    monkeypatch.setattr(auth_route, "hash_password", broken)
    from fastapi.testclient import TestClient
    from api.main import app
    r = TestClient(app, raise_server_exceptions=False).post(
        "/v1/auth/accept-invite", json={"token": i.token, "password": "SecurePass123!"})
    assert r.status_code == 500
    assert i.token_used() is False and i.password_hash() == OLD_HASH
    monkeypatch.undo()
    assert _accept(client, i.token).status_code == 200, "the link no longer works after a failed attempt"


# ── races ───────────────────────────────────────────────────────────────────

def _together(*fns):
    barrier = threading.Barrier(len(fns), timeout=30)
    out = [None] * len(fns)

    def run(k, fn):
        barrier.wait()
        try:
            out[k] = fn()
        except BaseException as e:   # noqa: BLE001 - reported to the test
            out[k] = e
    threads = [threading.Thread(target=run, args=(k, fn)) for k, fn in enumerate(fns)]
    [t.start() for t in threads]
    [t.join(60) for t in threads]
    return out


@pytest.mark.parametrize("attempt", range(5))
def test_two_concurrent_accepts_give_one_session_and_the_loser_cannot_set_the_password(client, invitee, attempt):
    i = invitee()
    a, b = _together(lambda: _accept(client, i.token, "AlphaPass123!"),
                     lambda: _accept(client, i.token, "BravoPass123!"))
    codes = sorted([a.status_code, b.status_code])
    assert codes == [200, 400], (a.status_code, a.text, b.status_code, b.text)
    winner = "AlphaPass123!" if a.status_code == 200 else "BravoPass123!"
    loser = "BravoPass123!" if winner == "AlphaPass123!" else "AlphaPass123!"
    refused = a if a.status_code == 400 else b
    assert refused.json()["detail"]["error"] == "invalid_token"
    assert "mr_token" not in refused.headers.get("set-cookie", ""), "the loser got a session"
    assert _verify(i.password_hash(), winner) and not _verify(i.password_hash(), loser)


def test_a_seat_cancelled_while_acceptance_waits_is_refused(client, invitee):
    """Cancellation holds the user row (services/seats.py `_switch_off` order);
    acceptance waits for it, then finds the token spent."""
    from api.services.seats import _switch_off
    i = invitee()
    holder = psycopg.connect(DB_URL)
    cur = holder.cursor()
    _switch_off(cur, i.account)                      # uncommitted: holds users, tokens, accounts
    done = {}
    t = threading.Thread(target=lambda: done.setdefault("r", _accept(client, i.token)))
    t.start()
    t.join(2)
    assert t.is_alive(), "acceptance did not wait for the cancellation in flight"
    holder.commit()
    holder.close()
    t.join(30)
    r = done["r"]
    assert r.status_code == 400, r.text
    # The cancelled link reads as invalid, like any spent link; it does not
    # reveal that the account behind it was switched off.
    assert r.json()["detail"]["error"] == "invalid_token", r.text
    assert i.password_hash() == OLD_HASH


@pytest.mark.parametrize("attempt", range(5))
def test_acceptance_racing_either_cancellation_never_deadlocks_or_half_applies(client, invitee, attempt):
    """Both cancellation paths, in their own lock orders, against acceptance."""
    from api.services.seats import _switch_off
    i = invitee()

    def seat_cancel():
        with psycopg.connect(DB_URL) as conn, conn.cursor() as cur:
            _switch_off(cur, i.account)

    def sponsor_deactivate():   # routes/affiliates.py order: accounts, users, tokens
        with psycopg.connect(DB_URL) as conn, conn.cursor() as cur:
            cur.execute("UPDATE accounts SET is_active = FALSE WHERE id = %s::uuid", (i.account,))
            cur.execute("UPDATE users SET is_active = FALSE WHERE account_id = %s::uuid", (i.account,))
            cur.execute("UPDATE signup_tokens SET used = TRUE WHERE account_id = %s::uuid AND used = FALSE",
                        (i.account,))

    cancel = seat_cancel if attempt % 2 == 0 else sponsor_deactivate
    r, c = _together(lambda: _accept(client, i.token), cancel)
    assert not isinstance(c, BaseException), f"cancellation failed: {c!r}"
    assert not isinstance(r, BaseException) and r.status_code in (200, 400), r
    assert i.token_used() is True
    assert _q("SELECT is_active FROM users WHERE id = %s", i.user)[0][0] is False
    if r.status_code == 200:
        assert _verify(i.password_hash(), "SecurePass123!")    # accepted, then switched off
    else:
        assert i.password_hash() == OLD_HASH                    # refused: nothing written

"""
An unsubscribe link, clicked, stops the next send. Against a real database.

THE DEFECT. Both endpoints — the link and RFC 8058 one-click — returned 500 to
every request: `_suppress` did `with db_conn() as conn: conn.cursor()`, and
`db_conn()` yields a `(conn, cur)` tuple. Underneath that, the account lookup
could not have worked either: it matched the address against
`schedules.recipients`, which the API stores as JSON, so no schedule created
through the API ever matched and the endpoint would have answered
"unsubscribed" while recording nothing. Recipients could not opt out.

`apps/worker/tests/test_unsubscribe_token_roundtrip.py` covers the token —
signing, encoding, one message per recipient. Nothing called the route, which
is where both of these lived.

THE CLAIMS
  1. A valid link records a suppression for the account that sent it, and the
     worker's send filter then drops the address (its own query, below).
  2. The same through one-click.
  3. A recipient added as JSON (`manual_email`) is found, through `email_log`.
  4. A token signed for another account suppresses nothing and is a 400.
  5. Of two accounts that mailed the address, only the one the token was
     signed for is suppressed.
  6. An address nobody mailed gets the success answer and no row.

`scripts/regressions/unsubscribe.json` breaks each and each goes red.
"""
import json
import os
import uuid

import pytest

DB_URL = os.getenv("DATABASE_URL")
psycopg = pytest.importorskip("psycopg", reason="psycopg is required for integration tests")
pytestmark = pytest.mark.skipif(not DB_URL, reason="Set DATABASE_URL to run unsubscribe tests")

#: The worker's filter, verbatim from worker/email/send.py: what decides
#: whether the next scheduled email goes to this address.
WORKER_FILTER = """
    SELECT email
    FROM email_suppressions
    WHERE account_id = %s
      AND email = ANY(%s)
"""


@pytest.fixture
def world():
    tag = uuid.uuid4().hex[:8]
    a, b = str(uuid.uuid4()), str(uuid.uuid4())
    w = {"a": a, "b": b, "email": f"unsub-{tag}@example.com", "other": f"unsub-other-{tag}@example.com"}
    with psycopg.connect(DB_URL) as conn:
        for aid, name in ((a, "Unsub A"), (b, "Unsub B")):
            conn.execute(
                "INSERT INTO accounts (id, name, slug, account_type, plan_slug) "
                "VALUES (%s, %s, %s, 'REGULAR', 'free')", (aid, name, f"unsub-{name[-1].lower()}-{tag}"))
        # A's schedule, created the way the API creates one: JSON recipients.
        conn.execute(
            "INSERT INTO schedules (id, account_id, name, report_type, city, cadence, recipients, active) "
            "VALUES (gen_random_uuid(), %s, 'u', 'market_snapshot', 'Irvine', 'weekly', ARRAY[%s], true)",
            (a, json.dumps({"type": "manual_email", "email": w["email"]})))
        # And the send the worker logged for it, with the resolved address.
        conn.execute(
            "INSERT INTO email_log (account_id, provider, to_emails, subject, status) "
            "VALUES (%s, 'sendgrid', ARRAY[%s], 'Your Market Snapshot Report', 'sent')", (a, w["email"]))
    yield w
    with psycopg.connect(DB_URL) as conn:
        for t in ("email_suppressions", "email_log", "schedules"):
            conn.execute(f"DELETE FROM {t} WHERE account_id = ANY(%s::uuid[])", ([a, b],))
        conn.execute("DELETE FROM accounts WHERE id = ANY(%s::uuid[])", ([a, b],))


@pytest.fixture(scope="module")
def client():
    from fastapi.testclient import TestClient
    from api.main import app
    return TestClient(app, raise_server_exceptions=False)


def _token(account_id, email):
    from api.routes.unsubscribe import generate_unsubscribe_token
    return generate_unsubscribe_token(account_id, email)


def _suppressed(account_id, email):
    with psycopg.connect(DB_URL) as conn:
        return [r[0] for r in conn.execute(WORKER_FILTER, (account_id, [email])).fetchall()]


def test_a_clicked_link_stops_the_next_send(client, world):
    w = world
    r = client.post("/v1/email/unsubscribe",
                    json={"email": w["email"], "token": _token(w["a"], w["email"])})
    assert r.status_code == 200, r.text
    assert _suppressed(w["a"], w["email"]) == [w["email"]], "the worker would still send to them"


def test_one_click_stops_the_next_send(client, world):
    w = world
    r = client.post("/v1/email/unsubscribe/one-click",
                    params={"email": w["email"], "token": _token(w["a"], w["email"])})
    assert r.status_code == 200, r.text
    assert _suppressed(w["a"], w["email"]) == [w["email"]]


def test_a_token_for_another_account_suppresses_nothing(client, world):
    w = world
    r = client.post("/v1/email/unsubscribe",
                    json={"email": w["email"], "token": _token(w["b"], w["email"])})
    assert r.status_code == 400, r.text
    assert _suppressed(w["a"], w["email"]) == [] and _suppressed(w["b"], w["email"]) == []


def test_only_the_account_the_token_was_signed_for_is_suppressed(client, world):
    w = world
    with psycopg.connect(DB_URL) as conn:
        conn.execute(
            "INSERT INTO email_log (account_id, provider, to_emails, subject, status) "
            "VALUES (%s, 'sendgrid', ARRAY[%s], 's', 'sent')", (w["b"], w["email"]))
    r = client.post("/v1/email/unsubscribe",
                    json={"email": w["email"], "token": _token(w["b"], w["email"])})
    assert r.status_code == 200, r.text
    assert _suppressed(w["b"], w["email"]) == [w["email"]]
    assert _suppressed(w["a"], w["email"]) == [], "A's token was not the one clicked"


def test_an_address_nobody_mailed_gets_the_same_answer_and_no_row(client, world):
    w = world
    r = client.post("/v1/email/unsubscribe",
                    json={"email": w["other"], "token": _token(w["a"], w["other"])})
    assert r.status_code == 200, r.text
    assert _suppressed(w["a"], w["other"]) == []

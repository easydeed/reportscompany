"""
A scheduled email's unsubscribe works, end to end, on every CI run.

WHY THIS IS A GATE AND NOT A TEST OF A FUNCTION. Unsubscribe was "fixed and
verified" on 2026-08-18 (U1–U5) and did not work then, or before, or after,
until #225. It never regressed: `routes/unsubscribe.py` was written on
2025-11-11 (f1510014) using `db_conn()`'s `(conn, cur)` tuple as a connection,
so the route raised on every request from its first day; and on 2025-11-20
(b82d0124) recipients became JSON, so its lookup could not have matched a
schedule anyway. U1–U5 verified everything up to the route — per-recipient
tokens, signing, URL encoding, the landing page, the RFC 8058 headers — and
`test_unsubscribe_token_roundtrip.py` stubs the database. Nothing ever clicked
a link and then sent again. A legal requirement was verified in every part
except the one that does it.

So this does exactly that, through the real code at every step:

  1. A schedule with JSON recipients (as the API stores them) is sent by the
     worker's own scheduled-send path: `resolve_recipients_to_emails` then
     `_send_and_log_report_email`, which writes `email_log` and calls
     `send_schedule_email`. Only the provider's HTTP call is captured.
  2. The FOOTER LINK is taken out of the first recipient's rendered email and
     followed as the web route does (GET /api/v1/email/unsubscribe forwards
     to POST /v1/email/unsubscribe); the route file must exist.
  3. The LIST-UNSUBSCRIBE header is taken from the second recipient's message
     and POSTed as Gmail does, through the one-click route.
  4. Both must succeed, and the NEXT scheduled send must mail only the third
     recipient, who did nothing.

`scripts/regressions/unsubscribe.json` breaks the route, and this goes red.
"""
import html as htmllib
import json
import os
import re
import uuid
from pathlib import Path
from urllib.parse import parse_qs, urlparse

import pytest

DB_URL = os.getenv("DATABASE_URL")
psycopg = pytest.importorskip("psycopg", reason="psycopg is required for integration tests")
needs_db = pytest.mark.skipif(not DB_URL, reason="Set DATABASE_URL to run the unsubscribe gate")

REPO = Path(__file__).resolve().parents[3]
SECRET = "unsubscribe-e2e-secret"
FOOTER_LINK = re.compile(r'href="([^"]*/api/v1/email/unsubscribe\?[^"]*)"')


@pytest.fixture
def world():
    tag = uuid.uuid4().hex[:8]
    acct, sched = str(uuid.uuid4()), str(uuid.uuid4())
    people = [f"e2e-{n}-{tag}@example.com" for n in ("link", "oneclick", "stays")]
    with psycopg.connect(DB_URL) as conn:
        conn.execute("INSERT INTO accounts (id, name, slug, account_type, plan_slug) "
                     "VALUES (%s, 'E2E Agent', %s, 'REGULAR', 'free')", (acct, f"e2e-unsub-{tag}"))
        conn.execute(
            "INSERT INTO schedules (id, account_id, name, report_type, city, cadence, recipients, active) "
            "VALUES (%s, %s, 'weekly', 'market_snapshot', 'Irvine', 'weekly', %s, true)",
            (sched, acct, [json.dumps({"type": "manual_email", "email": p}) for p in people]))
    yield {"acct": acct, "sched": sched, "people": people}
    with psycopg.connect(DB_URL) as conn:
        for t in ("email_suppressions", "email_log", "report_generations", "schedules"):
            conn.execute(f"DELETE FROM {t} WHERE account_id = %s", (acct,))
        conn.execute("DELETE FROM accounts WHERE id = %s", (acct,))


@pytest.fixture
def worker(monkeypatch):
    """The worker's modules with one shared secret and a captured provider."""
    import sys
    sys.path.insert(0, str(REPO / "apps/worker/src"))
    import worker.email.send as send
    import worker.tasks as tasks
    import api.routes.unsubscribe as unsub
    monkeypatch.setattr(send, "EMAIL_UNSUB_SECRET", SECRET)
    monkeypatch.setattr(unsub, "EMAIL_UNSUB_SECRET", SECRET)
    sent = []

    def provider(to_emails, subject, html_content, headers=None, **_):
        sent.append({"to": to_emails, "html": html_content, "headers": headers or {}})
        return 202, "accepted"

    monkeypatch.setattr(send, "send_email", provider)
    return tasks, sent


def _scheduled_send(tasks, w):
    """One scheduled run of `w`'s schedule, the way the worker does it."""
    run = str(uuid.uuid4())
    with psycopg.connect(DB_URL) as conn, conn.cursor() as cur:
        cur.execute("INSERT INTO report_generations (id, account_id, report_type, cities, status, generated_at) "
                    "VALUES (%s, %s, 'market_snapshot', ARRAY['Irvine'], 'completed', now())", (run, w["acct"]))
        cur.execute("SELECT recipients FROM schedules WHERE id = %s", (w["sched"],))
        emails = tasks.resolve_recipients_to_emails(cur, w["acct"], cur.fetchone()[0])
        conn.commit()
        result = {"metrics": {"median_close_price": 1_250_000, "total_closed": 40}, "counts": {"Closed": 40},
                  "listings_sample": []}
        return tasks._send_and_log_report_email(
            conn, cur, w["acct"], run, emails, "market_snapshot", "Irvine", [], 30,
            result, "https://example.com/report.pdf", schedule_id=w["sched"])


@pytest.fixture
def client():
    from fastapi.testclient import TestClient
    from api.main import app
    return TestClient(app, raise_server_exceptions=False)


def _web_route_exists(path):
    return (REPO / "apps/web/app" / path.lstrip("/") / "route.ts").exists()


def test_ci_runs_this_gate_rather_than_skipping_it():
    """A skip is green. Locally without a database the gate below skips, as
    every database suite does; on GitHub Actions it must run, so a workflow
    that stopped provisioning Postgres turns this red instead of quietly
    passing a legal requirement nobody checked (D-285's shape)."""
    if os.getenv("GITHUB_ACTIONS") == "true":
        assert DB_URL, "CI has no DATABASE_URL, so the unsubscribe gate would skip"


@needs_db
def test_an_unsubscribed_recipient_is_not_mailed_again(client, world, worker):
    tasks, sent = worker
    link_person, oneclick_person, stays = world["people"]

    status, text = _scheduled_send(tasks, world)
    assert status == 202, text
    by_recipient = {m["to"][0]: m for m in sent}
    assert set(by_recipient) == set(world["people"]), sent

    # 2. The footer link a person clicks.
    m = FOOTER_LINK.search(by_recipient[link_person]["html"])
    assert m, "the email has no unsubscribe link"
    footer = urlparse(htmllib.unescape(m.group(1)))
    assert _web_route_exists(footer.path), f"the link points at {footer.path}, which no web route serves"
    q = {k: v[0] for k, v in parse_qs(footer.query).items()}
    assert q["email"] == link_person, "the link names someone else"
    r = client.post("/v1/email/unsubscribe", json={"email": q["email"], "token": q["token"], "reason": "user_request"})
    assert r.status_code == 200, f"clicking the link failed: {r.status_code} {r.text}"

    # 3. The header Gmail and Yahoo act on.
    header = by_recipient[oneclick_person]["headers"].get("List-Unsubscribe", "")
    assert header.startswith("<") and header.endswith(">"), header
    one = urlparse(header[1:-1])
    assert _web_route_exists(one.path), f"List-Unsubscribe points at {one.path}, which no web route serves"
    q = {k: v[0] for k, v in parse_qs(one.query).items()}
    r = client.post("/v1/email/unsubscribe/one-click", params={"email": q["email"], "token": q["token"]})
    assert r.status_code == 200, f"one-click failed: {r.status_code} {r.text}"

    # 4. The next run.
    sent.clear()
    status, text = _scheduled_send(tasks, world)
    assert status == 202, text
    assert [m["to"] for m in sent] == [[stays]], (
        f"after two opt-outs the next send went to {[m['to'] for m in sent]}")

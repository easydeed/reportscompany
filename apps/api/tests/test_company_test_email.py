"""The company's "Email me a sample report" (Jerry, 2026-10-29).

A real report email in the company's brand, to the signed-in admin and nobody
else, under the same rules as a real send: the brand the reps' emails resolve,
the footer's real postal address, and an unsubscribe link and one-click header
that actually work — the link this endpoint replaced in the agent version is
`"#"`.

Against a real database on `test_rep_seats.World`; SendGrid is replaced by a
recorder, everything up to it runs.
"""
import os
import re
from html import unescape
from urllib.parse import parse_qs, urlparse

import pytest

from test_rep_seats import _auth, client, world  # noqa: F401 — pytest fixtures, used by name
from test_company_admin_role import member  # noqa: F401

psycopg = pytest.importorskip("psycopg")
DB_URL = os.getenv("DATABASE_URL")


@pytest.fixture
def outbox(monkeypatch):
    import api.routes.branding_tools as bt
    sent = []

    async def fake_send(**kw):
        sent.append(kw)
        return 202

    monkeypatch.setattr(bt, "SENDGRID_API_KEY", "test-key")
    monkeypatch.setattr(bt, "sendgrid_send", fake_send)
    return sent


def _send(client, who, **body):
    return client.post("/v1/company/branding/test-email", json=body or {"report_type": "market_snapshot"},
                       headers=_auth(client, who))


def _unsub_link(html):
    links = [unescape(h) for h in re.findall(r'href="([^"]*unsubscribe[^"]*)"', html)]
    assert links, "the email has no unsubscribe link"
    return links[0]


def test_it_goes_to_the_signed_in_admin_and_nobody_else(client, world, outbox):
    resp = _send(client, world.email("co-a"), report_type="market_snapshot", email="someone-else@example.com")
    assert resp.status_code == 200, resp.text
    assert resp.json()["sent_to"] == world.email("co-a")
    assert [m["to"] for m in outbox] == [world.email("co-a")], "a recipient in the request was used"


def test_a_member_cannot_send_one(client, world, member, outbox):
    resp = _send(client, member["email"])
    assert resp.status_code == 403
    assert outbox == []


def test_its_unsubscribe_link_and_header_actually_unsubscribe(client, world, outbox):
    to = world.email("co-a")
    assert _send(client, to).status_code == 200
    link = _unsub_link(outbox[0]["html"])
    assert link != "#"
    q = parse_qs(urlparse(link).query)
    assert q["email"] == [to]
    header = outbox[0]["headers"]["List-Unsubscribe"]
    assert "one-click" in header and outbox[0]["headers"]["List-Unsubscribe-Post"] == "List-Unsubscribe=One-Click"
    resp = client.post("/v1/email/unsubscribe", json={"email": to, "token": q["token"][0]})
    assert resp.status_code == 200, resp.text
    with psycopg.connect(DB_URL) as conn:
        rows = conn.execute("SELECT account_id::text FROM email_suppressions WHERE email = %s", (to,)).fetchall()
        conn.execute("DELETE FROM email_suppressions WHERE email = %s", (to,))
    assert (world.a,) in rows, "the link did not suppress this company's sends to the address"


def test_it_is_logged_for_the_company(client, world, outbox):
    assert _send(client, world.email("co-a")).status_code == 200
    with psycopg.connect(DB_URL) as conn:
        rows = conn.execute("SELECT to_emails, status FROM email_log WHERE account_id = %s", (world.a,)).fetchall()
    assert rows == [([world.email("co-a")], "sent")]


def test_the_footer_carries_a_real_postal_address(client, world, outbox):
    from worker.email.template import PLATFORM_POSTAL_ADDRESS
    assert _send(client, world.email("co-a")).status_code == 200
    assert PLATFORM_POSTAL_ADDRESS in unescape(outbox[0]["html"]), "unset, the platform's address is the footer's"
    assert "18575 Jamboree" not in outbox[0]["html"]
    with psycopg.connect(DB_URL) as conn:
        conn.execute("UPDATE affiliate_branding SET postal_address = '1 Company Way, Irvine, CA 92618' "
                     "WHERE account_id = %s", (world.a,))
    assert _send(client, world.email("co-a")).status_code == 200
    assert "1 Company Way, Irvine, CA 92618" in unescape(outbox[1]["html"])


def test_an_unset_colour_is_the_real_emails_default_not_an_invented_one(client, world, outbox):
    with psycopg.connect(DB_URL) as conn:
        conn.execute("UPDATE affiliate_branding SET primary_color = NULL WHERE account_id = %s", (world.a,))
    assert _send(client, world.email("co-a")).status_code == 200
    html = outbox[0]["html"].lower()
    assert "#7c3aed" not in html, "the test email painted a colour no real email uses"
    assert "#4f46e5" in html


def test_it_says_it_is_a_test_on_sample_figures(client, world, outbox):
    """The banner's old insertion points do not exist in Design's template, so
    it was never added. It must be at the top, before anything else."""
    from api.routes.branding_tools import TEST_EMAIL_NOTICE, TEST_EMAIL_NOTICE_SUB
    assert _send(client, world.email("co-a")).status_code == 200
    html = outbox[0]["html"]
    body = html[html.index("<body"):]
    assert TEST_EMAIL_NOTICE in body[:2000], "the test banner is missing or not at the top"
    assert "sample data" in TEST_EMAIL_NOTICE_SUB
    assert outbox[0]["subject"].startswith("[Test]")
    text = unescape(html)
    assert "Data from the MLS" not in text, "a test on canned figures says they are the MLS's"
    assert "contacts." not in text.split("Unsubscribe")[0][-200:], "a test says the reader is in someone's contacts"
    assert "Sample figures for a test email" in text and "you asked for a test email" in text

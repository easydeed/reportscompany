"""
D-304 — the consumer report viewer names the record owner to whoever has the link.

D-116 took the assessor-roll owner block off the property report, because the
person who requests a home-value report is often not the owner: a neighbour, a
buyer, another agent. D-155 took the owner's name out of the email that
delivers it. The page the email and the SMS link to — `/r/{id}`, rendered from
the public, unauthenticated `GET /v1/r/{id}/data` — still carried it, twice:
"Owner: <name>" under the address, and an "Owner" row in Property Details.

`owner_name` stays in `consumer_reports.property_data`: the agent path shows
the owner of record deliberately (`test_lead_records_who_asked.py`). What goes
is the public response, and the viewer's two lines.

Red on main: the response body carries the name.
"""
import json
import os
import re
import uuid
from pathlib import Path

import pytest

DB_URL = os.getenv("DATABASE_URL")
psycopg = pytest.importorskip("psycopg", reason="psycopg is required for integration tests")

OWNER = "Gerardo Recordowner"
VIEWER = (Path(__file__).resolve().parents[3]
          / "apps/web/components/mobile-report/MobileReportViewer.tsx")


@pytest.fixture
def report():
    if not DB_URL:
        if os.getenv("GITHUB_ACTIONS"):
            pytest.fail("DATABASE_URL is not set in CI; this test must not skip there")
        pytest.skip("Set DATABASE_URL to run the consumer report test")
    tag = uuid.uuid4().hex[:8]
    account, agent, rid = str(uuid.uuid4()), str(uuid.uuid4()), str(uuid.uuid4())
    with psycopg.connect(DB_URL) as conn:
        conn.execute(
            "INSERT INTO accounts (id, name, slug, account_type, plan_slug) "
            "VALUES (%s, 'Owner Test', %s, 'REGULAR', 'free')", (account, f"owner-{tag}"))
        conn.execute(
            "INSERT INTO users (id, account_id, email, first_name, last_name) "
            "VALUES (%s, %s, %s, 'Dana', 'Ortiz')", (agent, account, f"agent-{tag}@example.com"))
        conn.execute(
            "INSERT INTO consumer_reports (id, agent_id, agent_code, property_address, "
            "property_city, property_state, property_zip, property_data, value_estimate, "
            "status) VALUES (%s, %s, 'T1', '14 Sandpiper Ln', 'Irvine', 'CA', '92602', "
            "%s, %s, 'ready')",
            (rid, agent,
             json.dumps({"address": "14 Sandpiper Ln", "city": "Irvine", "state": "CA",
                         "zip": "92602", "owner_name": OWNER, "bedrooms": 3}),
             json.dumps({"low": 1, "mid": 2, "high": 3, "confidence": "medium"})))
    yield rid
    with psycopg.connect(DB_URL) as conn:
        conn.execute("DELETE FROM report_analytics WHERE report_id = %s", (rid,))
        conn.execute("DELETE FROM consumer_reports WHERE id = %s", (rid,))
        conn.execute("DELETE FROM users WHERE id = %s", (agent,))
        conn.execute("DELETE FROM accounts WHERE id = %s", (account,))


@pytest.fixture(scope="module")
def client():
    from fastapi.testclient import TestClient
    from api.main import app
    return TestClient(app, raise_server_exceptions=False)


def test_the_public_report_data_does_not_carry_the_owner(client, report):
    r = client.get(f"/v1/r/{report}/data")
    assert r.status_code == 200, r.text
    assert OWNER not in r.text, (
        "GET /v1/r/{id}/data — public, no login — returns the record owner's name "
        "to whoever holds the link")
    assert "owner_name" not in r.json()["property"]


def test_the_rest_of_the_property_still_arrives(client, report):
    """The control: the fix removes one field, not the property block."""
    prop = client.get(f"/v1/r/{report}/data").json()["property"]
    assert prop["address"] == "14 Sandpiper Ln" and prop["bedrooms"] == 3


def test_the_viewer_prints_no_owner_line():
    src = VIEWER.read_text(encoding="utf-8")
    assert "owner_name" not in src, "the viewer still reads owner_name"
    assert not re.search(r"['\"]Owner['\"]|>\s*Owner:", src), "the viewer still labels an owner"

"""A consumer report held for review stays viewable (LR-019).

When the worker cannot tell whether a text or email reached the person (a
timeout after the provider may have accepted it), it marks the report
`needs_review` and never sends it again. The person may already have the link
in hand, so the page must still open.

Red before this change: `GET /v1/r/{id}/data` answered 404 for a held report;
its status was not in the viewer's allowed list.
"""
import os
import uuid

import pytest

DB_URL = os.getenv("DATABASE_URL")
psycopg = pytest.importorskip("psycopg", reason="psycopg is required for integration tests")


@pytest.fixture
def reports():
    if not DB_URL:
        if os.getenv("GITHUB_ACTIONS"):
            pytest.fail("DATABASE_URL is not set in CI; this test must not skip there")
        pytest.skip("Set DATABASE_URL to run the held-report test")
    tag = uuid.uuid4().hex[:8]
    account, agent = str(uuid.uuid4()), str(uuid.uuid4())
    held, failed, ready = (str(uuid.uuid4()) for _ in range(3))
    with psycopg.connect(DB_URL) as conn:
        conn.execute("INSERT INTO accounts (id, name, slug, account_type, plan_slug) "
                     "VALUES (%s, 'Held Test', %s, 'REGULAR', 'free')", (account, f"held-{tag}"))
        conn.execute("INSERT INTO users (id, account_id, email, first_name, last_name) "
                     "VALUES (%s, %s, %s, 'Dana', 'Ortiz')", (agent, account, f"agent-{tag}@example.com"))
        for rid, status in ((held, "needs_review"), (failed, "failed"), (ready, "sent")):
            conn.execute(
                "INSERT INTO consumer_reports (id, agent_id, agent_code, property_address, "
                "property_city, property_state, property_zip, status) VALUES "
                "(%s, %s, 'H1', '1358 5th Street', 'La Verne', 'CA', '91750', %s)",
                (rid, agent, status))
    yield {"held": held, "failed": failed, "sent": ready}
    with psycopg.connect(DB_URL) as conn:
        for rid in (held, failed, ready):
            conn.execute("DELETE FROM report_analytics WHERE report_id = %s", (rid,))
            conn.execute("DELETE FROM consumer_reports WHERE id = %s", (rid,))
        conn.execute("DELETE FROM users WHERE id = %s", (agent,))
        conn.execute("DELETE FROM accounts WHERE id = %s", (account,))


@pytest.fixture(scope="module")
def client():
    from fastapi.testclient import TestClient
    from api.main import app
    return TestClient(app, raise_server_exceptions=False)


def test_a_held_report_still_opens(client, reports):
    r = client.get(f"/v1/r/{reports['held']}/data")
    assert r.status_code == 200, r.text


def test_a_failed_report_is_still_not_served(client, reports):
    """Unchanged: nothing was sent, so there is no link in anyone's hands."""
    assert client.get(f"/v1/r/{reports['failed']}/data").status_code == 404

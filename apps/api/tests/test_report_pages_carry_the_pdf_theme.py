"""The public report endpoints carry the PDF's theme and tokens (Design's digital-report handoff).

`GET /v1/property/public/{code}` (/p) and `GET /v1/r/{id}/data` (/r) gave the
pages a raw `accent_color` / `primary_color` and no theme for /r, so the pages
coloured themselves from whichever field they picked: /p led with the accent
under white text, /r with a primary-to-accent gradient. They now return
`theme_tokens` — the PDF's `derive_theme()` of the colour that document's PDF
uses — and /r returns the theme it renders in.

Red on main: neither response has `theme_tokens`, and /r has no `theme`.
"""
import os
import sys
import uuid
from pathlib import Path

import pytest

DB_URL = os.getenv("DATABASE_URL")
psycopg = pytest.importorskip("psycopg", reason="psycopg is required for integration tests")
sys.path.insert(0, str(Path(__file__).resolve().parents[3] / "apps/worker/src"))

NAVY, AMBER, RED = "#1B365D", "#F59E0B", "#DC2626"


def _derive(color):
    from worker.themes import TOKENS, derive_theme
    d = derive_theme(color)
    return {k: d[k] for k in TOKENS}


@pytest.fixture
def account():
    if not DB_URL:
        if os.getenv("GITHUB_ACTIONS"):
            pytest.fail("DATABASE_URL is not set in CI; this test must not skip there")
        pytest.skip("Set DATABASE_URL to run the report theme test")
    tag = uuid.uuid4().hex[:8]
    ids = {k: str(uuid.uuid4()) for k in ("account", "user", "cr", "pr", "pr_null")}
    ids.update(code=f"t{tag}"[:8], code_null=f"n{tag}"[:8])
    from api.theme_registry import THEME_NUMBER_MAP, DEFAULT_THEME_ID
    ids["theme"] = next(i for i in sorted(THEME_NUMBER_MAP) if i != DEFAULT_THEME_ID)
    with psycopg.connect(DB_URL) as conn:
        conn.execute("INSERT INTO accounts (id, name, slug, account_type, plan_slug, primary_color, "
                     "secondary_color, default_theme_id) VALUES (%s, 'Theme Test', %s, 'REGULAR', 'free', "
                     "%s, %s, %s)", (ids["account"], f"theme-{tag}", NAVY, AMBER, ids["theme"]))
        conn.execute("INSERT INTO users (id, account_id, email, first_name, last_name) "
                     "VALUES (%s, %s, %s, 'Dana', 'Ortiz')", (ids["user"], ids["account"], f"a-{tag}@example.com"))
        conn.execute("INSERT INTO consumer_reports (id, agent_id, agent_code, property_address, property_city, "
                     "property_state, property_zip, property_data, status) VALUES (%s, %s, 'T1', '1 A St', "
                     "'La Verne', 'CA', '91750', '{}', 'ready')", (ids["cr"], ids["user"]))
        for pr, code, accent in ((ids["pr"], ids["code"], RED), (ids["pr_null"], ids["code_null"], None)):
            conn.execute("INSERT INTO property_reports (id, account_id, user_id, report_type, theme, accent_color, "
                         "property_address, property_city, property_state, property_zip, status, short_code, is_active) "
                         "VALUES (%s, %s, %s, 'seller', %s, %s, '1 A St', 'La Verne', 'CA', '91750', 'complete', %s, TRUE)",
                         (pr, ids["account"], ids["user"], ids["theme"], accent, code))
    yield ids
    with psycopg.connect(DB_URL) as conn:
        conn.execute("DELETE FROM report_analytics WHERE report_id = %s", (ids["cr"],))
        conn.execute("DELETE FROM consumer_reports WHERE id = %s", (ids["cr"],))
        conn.execute("DELETE FROM property_reports WHERE account_id = %s", (ids["account"],))
        conn.execute("DELETE FROM users WHERE id = %s", (ids["user"],))
        conn.execute("DELETE FROM accounts WHERE id = %s", (ids["account"],))


@pytest.fixture(scope="module")
def client():
    from fastapi.testclient import TestClient
    from api.main import app
    return TestClient(app, raise_server_exceptions=False)


def test_the_consumer_page_gets_the_consumer_pdfs_theme_and_colour(client, account):
    body = client.get(f"/v1/r/{account['cr']}/data").json()
    assert body["theme"] == account["theme"]
    # The account's primary, as on /p and the consumer PDF (decided 2026-11-04);
    # the account's amber secondary plays no part.
    assert body["theme_tokens"] == _derive(NAVY), "/r takes the account's primary"


def test_the_property_page_gets_the_reports_accent(client, account):
    body = client.get(f"/v1/property/public/{account['code']}").json()
    assert body["theme_tokens"] == _derive(RED)


def test_a_report_with_no_accent_takes_the_brand(client, account):
    """It used to 500: `accent_color: str` refused the row's NULL."""
    r = client.get(f"/v1/property/public/{account['code_null']}")
    assert r.status_code == 200, r.text
    assert r.json()["theme_tokens"] == _derive(NAVY)

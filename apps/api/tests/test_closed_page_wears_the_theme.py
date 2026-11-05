"""A closed /p page still wears its report's theme (Design's round 2, B3).

`GET /v1/property/public/{code}` answers 410 for an inactive, expired or full
page. The status page Design drew reads `theme` and `theme_tokens` from that
body; the body carried only `detail`, so a closed page could not be themed.
It now carries both, the same tokens the live page would get, beside the same
`detail` message the web app already parses.

Red on main: the 410 body has no `theme` and no `theme_tokens`.
"""
import os
import sys
import uuid
from pathlib import Path

import pytest

DB_URL = os.getenv("DATABASE_URL")
psycopg = pytest.importorskip("psycopg", reason="psycopg is required for integration tests")
sys.path.insert(0, str(Path(__file__).resolve().parents[3] / "apps/worker/src"))

RED, NAVY = "#DC2626", "#1B365D"


def _derive(color):
    from worker.themes import TOKENS, derive_theme
    d = derive_theme(color)
    return {k: d[k] for k in TOKENS}


@pytest.fixture
def pages():
    if not DB_URL:
        if os.getenv("GITHUB_ACTIONS"):
            pytest.fail("DATABASE_URL is not set in CI; this test must not skip there")
        pytest.skip("Set DATABASE_URL to run the closed-page theme test")
    from api.theme_registry import DEFAULT_THEME_ID, THEME_NUMBER_MAP
    theme = next(i for i in sorted(THEME_NUMBER_MAP) if i != DEFAULT_THEME_ID)
    tag = uuid.uuid4().hex[:7]
    acc, usr = str(uuid.uuid4()), str(uuid.uuid4())
    rows = {  # kind: (id, code, accent, is_active, expires_sql)
        "inactive": (str(uuid.uuid4()), f"i{tag}", RED, False, "NULL"),
        "expired": (str(uuid.uuid4()), f"e{tag}", RED, True, "NOW() - INTERVAL '1 day'"),
        "inactive_no_accent": (str(uuid.uuid4()), f"n{tag}", None, False, "NULL"),
        "live": (str(uuid.uuid4()), f"l{tag}", RED, True, "NULL"),
    }
    with psycopg.connect(DB_URL) as conn:
        conn.execute("INSERT INTO accounts (id, name, slug, account_type, plan_slug, primary_color) "
                     "VALUES (%s, 'Closed Page Test', %s, 'REGULAR', 'free', %s)", (acc, f"closed-{tag}", NAVY))
        conn.execute("INSERT INTO users (id, account_id, email, first_name, last_name) "
                     "VALUES (%s, %s, %s, 'Dana', 'Ortiz')", (usr, acc, f"c-{tag}@example.com"))
        for rid, code, accent, active, expires in rows.values():
            conn.execute("INSERT INTO property_reports (id, account_id, user_id, report_type, theme, accent_color, "
                         "property_address, property_city, property_state, property_zip, status, short_code, "
                         f"is_active, expires_at) VALUES (%s, %s, %s, 'seller', %s, %s, '1 A St', 'La Verne', "
                         f"'CA', '91750', 'complete', %s, %s, {expires})",
                         (rid, acc, usr, theme, accent, code, active))
    yield {"theme": theme, **{k: v[1] for k, v in rows.items()}}
    with psycopg.connect(DB_URL) as conn:
        conn.execute("DELETE FROM property_reports WHERE account_id = %s", (acc,))
        conn.execute("DELETE FROM users WHERE id = %s", (usr,))
        conn.execute("DELETE FROM accounts WHERE id = %s", (acc,))


@pytest.fixture(scope="module")
def client():
    from fastapi.testclient import TestClient
    from api.main import app
    return TestClient(app, raise_server_exceptions=False)


@pytest.mark.parametrize("kind,detail", [("inactive", "This page is no longer available"),
                                         ("expired", "This page has expired")])
def test_a_closed_page_carries_its_theme(client, pages, kind, detail):
    r = client.get(f"/v1/property/public/{pages[kind]}")
    assert r.status_code == 410
    body = r.json()
    assert body["detail"] == detail, "the web app reads `detail` to tell expired from inactive"
    assert body["theme"] == pages["theme"]
    assert body["theme_tokens"] == _derive(RED)


def test_the_closed_page_matches_the_live_page(client, pages):
    live = client.get(f"/v1/property/public/{pages['live']}").json()
    closed = client.get(f"/v1/property/public/{pages['inactive']}").json()
    assert closed["theme_tokens"] == live["theme_tokens"]
    assert closed["theme"] == live["theme"]


def test_a_closed_page_with_no_accent_takes_the_brand(client, pages):
    body = client.get(f"/v1/property/public/{pages['inactive_no_accent']}").json()
    assert body["theme_tokens"] == _derive(NAVY)


def test_a_closed_page_discloses_nothing_else(client, pages):
    body = client.get(f"/v1/property/public/{pages['inactive']}").json()
    assert set(body) == {"detail", "theme", "theme_tokens"}

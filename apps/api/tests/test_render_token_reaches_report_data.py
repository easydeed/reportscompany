"""The render token reaches /v1/reports/{id}/data, and nothing else gets in.

The report Share page (apps/web/app/api/social/[runId]/route.ts) and the legacy
print page read report data server-side with X-Internal-Render-Token and no
account. The route checks that token. AuthContextMiddleware refused every
request without an account first, so the check was unreachable: in production
every Share link answered "Report Not Found" (404). Probe, November 18:
GET /v1/reports/not-a-uuid/data answered 401, where the route answers 400.

Real app, real middleware, real route, migrated database. Only the token value
is set for the test (settings.INTERNAL_RENDER_TOKEN, as the API reads it).
"""
import json
import os
import uuid

import pytest

DB = os.getenv("DATABASE_URL")
psycopg = pytest.importorskip("psycopg")
pytestmark = pytest.mark.skipif(not DB or "fake" in (DB or ""), reason="Set DATABASE_URL to run this test")
TOKEN = "render-token-for-tests"
PASSWORD = "RenderToken123!"
RESULT = {"report_type": "market_snapshot", "city": "Irvine", "counts": {"Active": 3}}


@pytest.fixture(scope="module")
def client():
    from fastapi.testclient import TestClient
    from api.main import app
    return TestClient(app, raise_server_exceptions=False)


@pytest.fixture(autouse=True)
def render_token(monkeypatch):
    from api.settings import settings
    monkeypatch.setattr(settings, "INTERNAL_RENDER_TOKEN", TOKEN)


@pytest.fixture
def world(client):
    """Two accounts, each with one completed report; account A can sign in."""
    made, reports = [], {}
    with psycopg.connect(DB, autocommit=True) as conn:
        for name in ("a", "b"):
            aid = str(uuid.uuid4())
            conn.execute("INSERT INTO accounts (id, name, slug, account_type, plan_slug, status, is_active) "
                         "VALUES (%s, %s, %s, 'REGULAR', 'free', 'active', true)",
                         (aid, f"Render {name}", f"render-{name}-{aid[:8]}"))
            conn.execute("INSERT INTO users (id, account_id, email, password_hash, role, email_verified, is_active) "
                         "VALUES (%s, %s, %s, crypt(%s, gen_salt('bf')), 'OWNER', true, true)",
                         (aid, aid, f"render-{name}-{aid[:8]}@example.com", PASSWORD))
            conn.execute("INSERT INTO account_users (account_id, user_id, role) VALUES (%s, %s, 'OWNER')", (aid, aid))
            rid = str(uuid.uuid4())
            conn.execute("INSERT INTO report_generations (id, account_id, user_id, report_type, status, generated_at, "
                         "result_json) VALUES (%s, %s, %s, 'market_snapshot', 'completed', now(), %s)",
                         (rid, aid, aid, json.dumps(RESULT)))
            made.append(aid)
            reports[name] = (aid, rid, f"render-{name}-{aid[:8]}@example.com")
    yield reports
    with psycopg.connect(DB, autocommit=True) as conn:
        for aid in made:
            for table in ("report_generations", "account_users", "users"):
                conn.execute(f"DELETE FROM {table} WHERE account_id = %s", (aid,))
            conn.execute("DELETE FROM accounts WHERE id = %s", (aid,))


def _data(client, rid, token=None, headers=None):
    h = dict(headers or {})
    if token is not None:
        h["X-Internal-Render-Token"] = token
    return client.get(f"/v1/reports/{rid}/data", headers=h)


# ── the render token now works ──────────────────────────────────────────────

def test_the_render_token_reads_the_report(client, world):
    _, rid, _ = world["a"]
    r = _data(client, rid, token=TOKEN)
    assert r.status_code == 200, (r.status_code, r.text)
    assert r.json()["city"] == "Irvine" and "brand" in r.json()


def test_the_route_is_reached_so_a_malformed_id_is_a_400_not_a_401(client):
    """The production probe: the route answers a malformed id with 400 before
    reading credentials. A 401 here means the middleware refused first."""
    r = _data(client, "not-a-uuid", token=TOKEN)
    assert r.status_code == 400, (r.status_code, r.text)


def test_an_unknown_report_is_a_404(client):
    assert _data(client, str(uuid.uuid4()), token=TOKEN).status_code == 404


# ── everything that was refused is still refused ────────────────────────────

@pytest.mark.parametrize("token", ["wrong-token", TOKEN + "x", " "])
def test_a_wrong_token_is_refused_by_the_route(client, world, token):
    _, rid, _ = world["a"]
    r = _data(client, rid, token=token)
    assert r.status_code == 401, (token, r.status_code, r.text)
    assert "Irvine" not in r.text


def test_no_token_and_no_session_is_refused(client, world):
    _, rid, _ = world["a"]
    assert _data(client, rid).status_code == 401
    assert _data(client, rid, token="").status_code == 401


def test_no_token_configured_means_the_token_path_is_closed(client, world, monkeypatch):
    from api.settings import settings
    monkeypatch.setattr(settings, "INTERNAL_RENDER_TOKEN", "")
    _, rid, _ = world["a"]
    assert _data(client, rid, token=TOKEN).status_code == 401


@pytest.mark.parametrize("path", [
    "/v1/reports",
    "/v1/account/plan-usage",
    "/v1/reports/{rid}",
    "/v1/reports/{rid}/data/extra",
    "/v1/reports/{rid}/datax",
    "/v1/reports/a/b/data",
    "/v1/admin/accounts",
])
def test_the_token_opens_no_other_route(client, world, path):
    _, rid, _ = world["a"]
    r = client.get(path.format(rid=rid), headers={"X-Internal-Render-Token": TOKEN})
    assert r.status_code in (401, 404, 405), (path, r.status_code, r.text[:200])
    assert r.status_code != 200


# ── signed-in users are unchanged ───────────────────────────────────────────

def _signed_in(client, email):
    r = client.post("/v1/auth/login", json={"email": email, "password": PASSWORD})
    assert r.status_code == 200, r.text
    return {"Authorization": f"Bearer {r.json()['access_token']}"}


def test_a_signed_in_owner_still_reads_their_report(client, world):
    _, rid, email = world["a"]
    r = _data(client, rid, headers=_signed_in(client, email))
    assert r.status_code == 200 and r.json()["city"] == "Irvine"


def test_a_signed_in_user_cannot_read_another_accounts_report(client, world):
    _, _, email = world["a"]
    _, other, _ = world["b"]
    assert _data(client, other, headers=_signed_in(client, email)).status_code == 404


def test_a_session_with_a_token_header_is_still_scoped_to_its_account(client, world):
    """A signed-in caller resolves to their account in the middleware, so the
    route takes the session path and the header changes nothing."""
    _, _, email = world["a"]
    _, other, _ = world["b"]
    r = _data(client, other, token="anything", headers=_signed_in(client, email))
    assert r.status_code == 404


# ── the middleware's own boundary ───────────────────────────────────────────
# Every other route also checks sign-in itself, so a looser middleware would
# still end in 401 there and the route tests above could not see it. These pin
# the middleware's pass-through to exactly one request shape.

@pytest.mark.parametrize("path,header,passes", [
    ("/v1/reports/{rid}/data", True, True),
    ("/v1/reports/not-a-uuid/data", True, True),       # the route then 400s it
    ("/v1/reports/{rid}/data", False, False),
    ("/v1/reports/{rid}", True, False),
    ("/v1/reports", True, False),
    ("/v1/reports/{rid}/data/extra", True, False),
    ("/v1/reports/{rid}/datax", True, False),
    ("/v1/reports/a/b/data", True, False),
    ("/v1/account/plan-usage", True, False),
    ("/x/v1/reports/{rid}/data", True, False),
])
def test_only_the_data_path_with_a_token_header_is_passed_through(path, header, passes):
    from starlette.requests import Request
    from api.middleware.authn import _render_token_request
    headers = [(b"x-internal-render-token", b"anything")] if header else []
    scope = {"type": "http", "method": "GET", "path": path.format(rid=uuid.uuid4()),
             "headers": headers, "query_string": b""}
    assert _render_token_request(Request(scope)) is passes


def test_without_the_header_the_middleware_still_refuses_first(client):
    """No header: refused by the middleware (401), not passed to the route,
    which would have answered this malformed id with 400."""
    r = client.get("/v1/reports/not-a-uuid/data")
    assert r.status_code == 401, (r.status_code, r.text)

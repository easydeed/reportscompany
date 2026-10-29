"""
D-293 — the admin plan picker labelled plans from the legacy column.

"Free (5 reports/month)" and "Trial (10 reports/month)" were typed into the
admin account page; the gate enforces `market_reports_limit`, 3 for both. The
page now labels from `GET /v1/admin/plans`, which must therefore carry the
enforced column, equal to the table.
"""
import os

import pytest

DB_URL = os.getenv("DATABASE_URL")
psycopg = pytest.importorskip("psycopg")


@pytest.fixture
def plans_response():
    """The route function itself, against the real table. Authentication is
    the admin dependency's job and is tested with it; this is about the rows."""
    if not DB_URL:
        if os.getenv("GITHUB_ACTIONS"):
            pytest.fail("DATABASE_URL is not set in CI; this test must not skip there")
        pytest.skip("Set DATABASE_URL")
    from api.routes.admin import list_plans
    return list_plans(_admin={"account_id": "", "user_id": "admin"})


def test_every_plan_carries_the_limit_the_gate_enforces(plans_response):
    served = {p["plan_slug"]: p["market_reports_limit"] for p in plans_response["plans"]}
    with psycopg.connect(DB_URL) as conn:
        table = dict(conn.execute("SELECT plan_slug, market_reports_limit FROM plans").fetchall())
    assert served == table
    assert served, "no plans served; the check read nothing"

"""Plan & Seats reads its numbers; it types none (D-315).

GET /v1/company/seats returns `agent_plan`: what each agent a rep invites
gets, read from the `plans` row the invite puts them on. Changing that row
changes the answer — a number typed into the page or the route would not move.
"""
import os

import pytest

from test_rep_seats import _auth, client, world  # noqa: F401 — pytest fixtures, used by name

psycopg = pytest.importorskip("psycopg")
DB_URL = os.getenv("DATABASE_URL")


@pytest.fixture
def agent_plan_row():
    """The sponsored_free row, restored after the test."""
    with psycopg.connect(DB_URL) as conn:
        before = conn.execute(
            "SELECT market_reports_limit, schedules_limit, property_reports_per_month "
            "FROM plans WHERE plan_slug = 'sponsored_free'").fetchone()
    assert before, "no sponsored_free plan row in this database"
    yield before
    with psycopg.connect(DB_URL) as conn:
        conn.execute(
            "UPDATE plans SET market_reports_limit = %s, schedules_limit = %s, property_reports_per_month = %s "
            "WHERE plan_slug = 'sponsored_free'", before)


def _seats(client, w):
    resp = client.get("/v1/company/seats", headers=_auth(client, w.email("co-a")))
    assert resp.status_code == 200, resp.text
    return resp.json()


def test_the_agents_plan_is_the_plans_table(client, world, agent_plan_row):
    plan = _seats(client, world)["agent_plan"]
    assert (plan["market_reports"], plan["schedules"], plan["property_reports"]) == tuple(agent_plan_row)
    with psycopg.connect(DB_URL) as conn:
        conn.execute("UPDATE plans SET market_reports_limit = 7, schedules_limit = 2, "
                     "property_reports_per_month = 4 WHERE plan_slug = 'sponsored_free'")
    plan = _seats(client, world)["agent_plan"]
    assert (plan["market_reports"], plan["schedules"], plan["property_reports"]) == (7, 2, 4)
    assert plan["plan_name"]


def test_a_limit_the_table_does_not_give_is_dropped_not_invented(client, world, agent_plan_row):
    with psycopg.connect(DB_URL) as conn:
        conn.execute("UPDATE plans SET schedules_limit = NULL WHERE plan_slug = 'sponsored_free'")
    assert _seats(client, world)["agent_plan"]["schedules"] is None


def test_the_seats_read_says_who_can_act(client, world):
    assert _seats(client, world)["can_manage"] is True

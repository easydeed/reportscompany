"""The rep's book: one agent, the leads feed, and the report and schedule
lists the rep pages read (D-324, D-319, the leads feed).

Against a real database on `test_rep_seats.World`: rep A1's agents are a1a
and a1b; rep B1 (another company) has b1a. Each agent's leads are written the
way their own pages write them. The rep sees counts and where a lead came
from — never who the homeowner is — and only for agents in their own book.
"""
import os
import uuid

import pytest

from test_rep_seats import _auth, client, world  # noqa: F401 — pytest fixtures, used by name

psycopg = pytest.importorskip("psycopg")
DB_URL = os.getenv("DATABASE_URL")
SECRET_HOMEOWNER = "secret.homeowner@example.com"


@pytest.fixture
def book(world):
    w = world
    made = {"leads": [], "reports": [], "schedules": []}
    with psycopg.connect(DB_URL) as conn:
        for acct, source, days in ((w.a1a, "qr_scan", 1), (w.a1a, "direct_link", 2), (w.a1a, "cma_page", 3),
                                   (w.a1b, "manual", 40), (w.b1a, "qr_scan", 1)):
            lid = str(uuid.uuid4())
            conn.execute(
                """INSERT INTO leads (id, account_id, name, email, phone, message, source, status, created_at)
                   VALUES (%s, %s, 'Secret Homeowner', %s, '555-0100', 'call me', %s, 'new',
                           date_trunc('month', NOW()) + interval '1 hour' - (%s || ' days')::interval * (CASE WHEN %s > 30 THEN 1 ELSE 0 END))""",
                (lid, acct, SECRET_HOMEOWNER, source, days, days))
            made["leads"].append(lid)
        rid, sid = str(uuid.uuid4()), str(uuid.uuid4())
        conn.execute("""INSERT INTO report_generations (id, account_id, report_type, cities, status, generated_at, lookback_days, billable)
                        VALUES (%s, %s, 'market_snapshot', %s, 'completed', '2026-10-29 03:30:00', 30, false)""",
                     (rid, w.a1a, ["BOOK-CITY"]))
        conn.execute("""INSERT INTO schedules (id, account_id, name, report_type, city, cadence, monthly_dom, send_hour,
                                               send_minute, recipients, active, timezone)
                        VALUES (%s, %s, 'book sched', 'new_listings', 'BOOK-CITY', 'monthly', 15, 9, 0, %s, true, 'America/Los_Angeles')""",
                     (sid, w.a1a, ["x@example.com"]))
        made["reports"].append(rid)
        made["schedules"].append(sid)
    yield made
    with psycopg.connect(DB_URL) as conn:
        conn.execute("DELETE FROM leads WHERE id = ANY(%s::uuid[])", (made["leads"],))
        conn.execute("DELETE FROM report_generations WHERE id = ANY(%s::uuid[])", (made["reports"],))
        conn.execute("DELETE FROM schedules WHERE id = ANY(%s::uuid[])", (made["schedules"],))


def _get(client, who, path, status=200):
    resp = client.get(path, headers=_auth(client, who))
    assert resp.status_code == status, f"{path}: {resp.status_code} {resp.text[:200]}"
    return resp.json()


def test_the_leads_feed_says_whose_and_from_where_never_who(client, world, book):
    d = _get(client, world.email("rep-a1"), "/v1/affiliate/leads")
    assert all(set(l) == {"id", "agent_account_id", "agent_name", "came_from", "created_at"} for l in d["leads"]), d["leads"]
    text = str(d)
    for secret in (SECRET_HOMEOWNER, "Secret Homeowner", "555-0100", "call me"):
        assert secret not in text, f"the rep can read the homeowner's {secret!r}"
    came = sorted(l["came_from"] for l in d["leads"] if l["agent_account_id"] == world.a1a)
    assert came == ["home_value_page", "property_page", "property_page"], "qr_scan and direct_link are both the property page"
    assert [l["came_from"] for l in d["leads"] if l["agent_account_id"] == world.a1b] == ["other"]


def test_the_counts_are_per_agent_and_add_up(client, world, book):
    d = _get(client, world.email("rep-a1"), "/v1/affiliate/leads")
    by = {a["agent_account_id"]: a for a in d["agents"]}
    assert by[world.a1a]["this_month"] == 3 and by[world.a1a]["total"] == 3
    assert by[world.a1b]["this_month"] == 0 and by[world.a1b]["total"] == 1
    assert d["this_month"] == sum(a["this_month"] for a in d["agents"])


def test_another_companys_agent_and_leads_never_show(client, world, book):
    d = _get(client, world.email("rep-a1"), "/v1/affiliate/leads")
    assert world.b1a not in str(d)
    _get(client, world.email("rep-a1"), f"/v1/affiliate/leads?agent={world.b1a}", status=403)
    _get(client, world.email("rep-a1"), f"/v1/affiliate/agents/{world.b1a}", status=403)
    other = _get(client, world.email("rep-b1"), "/v1/affiliate/leads")
    assert world.a1a not in str(other) and len(other["leads"]) == 1


def test_a_rep_with_no_agents_sees_none(client, world, book):
    d = _get(client, world.email("rep-a2"), "/v1/affiliate/leads")
    assert d["leads"] == [] and d["agents"] == [] and d["this_month"] == 0


def test_only_a_rep_reads_a_book(client, world, book):
    _get(client, world.email("co-a"), "/v1/affiliate/leads", status=403)
    _get(client, world.email("ag-a1a"), f"/v1/affiliate/agents/{world.a1a}", status=403)


def test_one_agent_says_who_they_are_and_where_they_stand(client, world, book):
    d = _get(client, world.email("rep-a1"), f"/v1/affiliate/agents/{world.a1a}")
    a = d["agent"]
    assert a["email"] == world.email("ag-a1a") and a["status"] == "active" and a["name"]
    assert a["plan_name"] and isinstance(a["market_reports_used"], int)
    assert a["last_report_at"].endswith("+00:00")
    assert d["leads"] == {"this_month": 3, "last_month": 0, "total": 3}
    assert SECRET_HOMEOWNER not in str(d)


def test_rep_report_times_are_marked_utc(client, world, book):
    """D-319, the rep's half."""
    rows = _get(client, world.email("rep-a1"), "/v1/affiliate/all-reports")["reports"]
    row = next(r for r in rows if r["city"] == "BOOK-CITY")
    assert row["generated_at"] == "2026-10-29T03:30:00+00:00"
    rows = _get(client, world.email("rep-a1"), f"/v1/affiliate/agents/{world.a1a}/reports")["reports"]
    assert next(r for r in rows if r["city"] == "BOOK-CITY")["generated_at"] == "2026-10-29T03:30:00+00:00"


def test_schedules_carry_their_day(client, world, book):
    rows = _get(client, world.email("rep-a1"), "/v1/affiliate/all-schedules")["schedules"]
    s = next(r for r in rows if r["area"] == "BOOK-CITY")
    assert (s["weekly_dow"], s["monthly_dom"]) == (None, 15)
    rows = _get(client, world.email("rep-a1"), f"/v1/affiliate/agents/{world.a1a}/schedules")["schedules"]
    assert next(r for r in rows if r["area"] == "BOOK-CITY")["monthly_dom"] == 15

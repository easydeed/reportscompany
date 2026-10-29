"""Company Activity reads who made what, and when, correctly (D-317).

GET /v1/company/reports and /v1/company/schedules now carry each row's rep
(an agent's is their sponsor, a rep is their own) so the page can say "Ben's
agent" and filter by rep, and report times are marked UTC — the column is
`timestamp without time zone`, and a bare value reads seven or eight hours late in a
browser in California.

Against a real database on `test_rep_seats.World`: company A's agent and rep
each make a report and own a schedule; so does company B's agent, whose rows
must never appear in A's feed, under any filter.
"""
import os
import uuid

import pytest

from test_rep_seats import _auth, client, world  # noqa: F401 — pytest fixtures, used by name

psycopg = pytest.importorskip("psycopg")
DB_URL = os.getenv("DATABASE_URL")


@pytest.fixture
def made(world):
    w = world
    rows = {"reports": [], "schedules": []}
    with psycopg.connect(DB_URL) as conn:
        for acct, city in ((w.a1a, "AGENT-A-CITY"), (w.a1, "REP-A-CITY"), (w.b1a, "COMPANY-B-SECRET-CITY")):
            rid, sid = str(uuid.uuid4()), str(uuid.uuid4())
            conn.execute(
                """INSERT INTO report_generations (id, account_id, report_type, cities, status, generated_at,
                                                    lookback_days, billable)
                   VALUES (%s, %s, 'market_snapshot', %s, 'completed', '2026-10-29 03:30:00', 30, false)""",
                (rid, acct, [city]))
            conn.execute(
                """INSERT INTO schedules (id, account_id, name, report_type, city, cadence, weekly_dow,
                                          send_hour, send_minute, recipients, active, timezone)
                   VALUES (%s, %s, %s, 'new_listings', %s, 'weekly', 1, 8, 0, %s, true, 'America/Los_Angeles')""",
                (sid, acct, f"sched {city}", city, ["someone@example.com"]))
            rows["reports"].append(rid)
            rows["schedules"].append(sid)
    yield rows
    with psycopg.connect(DB_URL) as conn:
        conn.execute("DELETE FROM report_generations WHERE id = ANY(%s::uuid[])", (rows["reports"],))
        conn.execute("DELETE FROM schedules WHERE id = ANY(%s::uuid[])", (rows["schedules"],))


def _get(client, w, path):
    resp = client.get(path, headers=_auth(client, w.email("co-a")))
    assert resp.status_code == 200, resp.text
    return resp.json()


def test_each_report_says_whose_rep_it_is(client, world, made):
    w = world
    rows = {r["city"]: r for r in _get(client, w, "/v1/company/reports")["reports"]}
    assert rows["AGENT-A-CITY"]["rep_id"] == w.a1 and rows["AGENT-A-CITY"]["rep_name"] == "Seat Rep A1"
    assert rows["AGENT-A-CITY"]["account_id"] == w.a1a
    assert rows["REP-A-CITY"]["rep_id"] == w.a1, "a rep's own report is their own"


def test_each_schedule_says_whose_rep_it_is_and_its_day(client, world, made):
    w = world
    rows = {s["area"]: s for s in _get(client, w, "/v1/company/schedules")["schedules"]}
    s = rows["AGENT-A-CITY"]
    assert (s["rep_id"], s["rep_name"], s["weekly_dow"], s["monthly_dom"]) == (w.a1, "Seat Rep A1", 1, None)


def test_report_times_are_marked_utc(client, world, made):
    row = next(r for r in _get(client, world, "/v1/company/reports")["reports"] if r["city"] == "AGENT-A-CITY")
    assert row["generated_at"] == "2026-10-29T03:30:00+00:00"
    overview = _get(client, world, "/v1/company/overview")
    assert all(a["timestamp"] is None or a["timestamp"].endswith("+00:00") for a in overview["activity"])


def test_another_companys_activity_never_shows(client, world, made):
    w = world
    for path in ("/v1/company/reports", "/v1/company/schedules",
                 f"/v1/company/reports?rep_id={w.a1}", f"/v1/company/schedules?rep_id={w.a1}"):
        assert "COMPANY-B-SECRET-CITY" not in str(_get(client, w, path)), path
    for path in (f"/v1/company/reports?rep_id={w.b1}", f"/v1/company/schedules?rep_id={w.b1}"):
        resp = client.get(path, headers=_auth(client, w.email("co-a")))
        assert resp.status_code == 404, f"{path}: {resp.status_code}"


def test_the_rep_filter_narrows_to_that_rep(client, world, made):
    w = world
    cities = {r["city"] for r in _get(client, w, f"/v1/company/reports?rep_id={w.a2}")["reports"]}
    assert "AGENT-A-CITY" not in cities and "REP-A-CITY" not in cities

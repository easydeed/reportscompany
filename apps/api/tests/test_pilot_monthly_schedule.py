from contextlib import nullcontext
from datetime import datetime, timezone
from unittest.mock import Mock

import pytest

from test_rep_seats import client, world  # noqa: F401 - pytest fixtures

from api.routes import schedules
from api.services import schedule_utils


@pytest.mark.parametrize(("now", "expected"), [
    ((2026, 1, 30), (2026, 2, 5)), ((2026, 1, 31), (2026, 2, 5)),
    ((2028, 2, 29), (2028, 3, 5)), ((2026, 10, 31), (2026, 11, 5)),
    ((2026, 12, 31), (2027, 1, 5)),
])
def test_first_monthly_occurrence_at_month_end(monkeypatch, now, expected):
    class Clock(datetime):
        @classmethod
        def now(cls, tz):
            return datetime(*now, 12, tzinfo=timezone.utc).astimezone(tz)

    monkeypatch.setattr(schedule_utils, "datetime", Clock)
    result = schedule_utils.compute_next_run("monthly", None, 5, 9, 0, "UTC")
    assert result == datetime(*expected, 9, tzinfo=timezone.utc)


@pytest.mark.parametrize(("active", "fields", "retime"), [
    (True, {"name": "Edited"}, False),
    (True, {"weekly_dow": 3, "monthly_dom": 5, "cadence": "monthly"}, False),
    (True, {"active": False}, False),
    (True, {"send_hour": 9, "monthly_dom": 5, "active": True}, False),
    (True, {"send_hour": 10}, True),
    (False, {"active": True}, True),
])
def test_schedule_edit_preserves_due_occurrence(monkeypatch, active, fields, retime):
    cur = Mock()
    cur.fetchone.side_effect = [("monthly", None, 5, 9, 0, "UTC", active), ("id",)]
    monkeypatch.setattr(schedules, "db_conn", lambda: nullcontext((Mock(), cur)))
    monkeypatch.setattr(schedules, "set_rls", Mock())
    monkeypatch.setattr(schedules, "block_unverified_send", Mock())
    schedules.update_schedule("id", schedules.ScheduleUpdate(**fields), Mock(), "account")
    assert ("next_run_at =" in cur.execute.call_args.args[0]) is retime


@pytest.mark.parametrize(("cadence", "extra_day"), [
    ("weekly", {"monthly_dom": 13}), ("monthly", {"weekly_dow": 4}),
])
def test_full_form_keeps_existing_due_alert(client, world, cadence, extra_day):
    import os
    import psycopg
    from test_rep_seats import _auth

    with psycopg.connect(os.environ["DATABASE_URL"]) as conn:
        sid, due = conn.execute("""
            INSERT INTO schedules (account_id, name, report_type, city, cadence,
                weekly_dow, monthly_dom, send_hour, send_minute, recipients, active, timezone, next_run_at)
            VALUES (%s, 'Due', 'new_listings', 'Downey', %s, 1, 5, 9, 0,
                ARRAY['pilot@example.com'], true, 'UTC', NOW() - INTERVAL '25 seconds')
            RETURNING id, next_run_at
        """, (world.a1a, cadence)).fetchone()
    try:
        fields = {"name": "Renamed", "cadence": cadence, "send_hour": 9, "send_minute": 0,
                  "timezone": "UTC", "active": True, **extra_day}
        response = client.patch(f"/v1/schedules/{sid}", json=fields,
                                headers=_auth(client, world.email("ag-a1a")))
        assert response.status_code == 200, response.text
        with psycopg.connect(os.environ["DATABASE_URL"]) as conn:
            assert conn.execute("""
                SELECT id, next_run_at FROM schedules WHERE account_id = %s
                  AND name = 'Renamed' AND active AND next_run_at <= NOW()
            """, (world.a1a,)).fetchall() == [(sid, due)]
    finally:
        with psycopg.connect(os.environ["DATABASE_URL"]) as conn:
            conn.execute("DELETE FROM schedules WHERE id = %s", (sid,))

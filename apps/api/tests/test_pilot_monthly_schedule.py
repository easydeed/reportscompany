from contextlib import nullcontext
from datetime import datetime, timezone
from unittest.mock import Mock

import pytest

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

"""
D-308 — the welcome email promised the Free plan 5 reports a month; the gate
allows 3.

The 5 was typed into the copy, and it was the legacy `plans.monthly_report_limit`.
The market-report gate reads `market_reports_limit`. Owner decision
(2026-10-29): plan numbers in email copy are read from the plans table the gate
reads, so they cannot drift again. Against a real database: change the plan,
and the next email says the new number.
"""
import os
import re
from unittest.mock import patch

import pytest

from api.services import email as em

DB_URL = os.getenv("DATABASE_URL")
psycopg = pytest.importorskip("psycopg")


def _welcome_html():
    sent = {}
    with patch.object(em.email_service, "send_email_sync", lambda **p: sent.update(p) or {"ok": True}):
        em.send_regular_agent_welcome_email(to_email="a@x.test", first_name="Dana")
    return sent["html"]


@pytest.fixture
def free_plan():
    if not DB_URL:
        if os.getenv("GITHUB_ACTIONS"):
            pytest.fail("DATABASE_URL is not set in CI; this test must not skip there")
        pytest.skip("Set DATABASE_URL")
    with psycopg.connect(DB_URL) as conn:
        before = conn.execute(
            "SELECT market_reports_limit FROM plans WHERE plan_slug = 'free'").fetchone()[0]
    yield before
    with psycopg.connect(DB_URL) as conn:
        conn.execute("UPDATE plans SET market_reports_limit = %s WHERE plan_slug = 'free'", (before,))


def test_the_welcome_states_the_limit_the_gate_enforces(free_plan):
    html = _welcome_html()
    assert f"includes {free_plan} market reports a month" in html
    assert "includes 5 market reports a month" not in html or free_plan == 5


def test_a_change_to_the_plan_reaches_the_next_email(free_plan):
    """The number is read at send time, not frozen into the copy."""
    with psycopg.connect(DB_URL) as conn:
        conn.execute("UPDATE plans SET market_reports_limit = 7 WHERE plan_slug = 'free'")
    assert "includes 7 market reports a month" in _welcome_html()


def test_no_number_rather_than_a_guess_when_the_plan_cannot_be_read():
    with patch.object(em, "_plan_market_limit", lambda slug: None):
        html = _welcome_html()
    assert not re.search(r"includes \d+ (market )?reports", html)
    assert "See plans" in html


def test_no_plan_number_is_typed_into_email_copy():
    """The general form of the decision: in the email module, a number next to
    'reports per month' or 'reports a month' is an interpolation, never a literal."""
    src = em.__file__
    text = open(src, encoding="utf-8").read()
    literals = re.findall(r"\b\d+\s+(?:market\s+)?reports?\s+(?:per|a)\s+month", text)
    assert not literals, f"plan numbers typed into email copy: {literals}"

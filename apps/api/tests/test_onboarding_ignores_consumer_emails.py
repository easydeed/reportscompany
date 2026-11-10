"""The home-value email to a lead is not the agent's first report (LR-020, Q2).

LR-020 journals every consumer delivery email in `email_log`, with
`report_id` = the consumer report (design §3.5; Jerry, 2026-11-10: it shows in
the account's recent emails). Onboarding's "first report" step counted any
sent `email_log` row with a report id, so a lead requesting a home value
report would have ticked the agent's own first-report step.

Real SQL against the migrated database; red on main once a consumer email row
exists.
"""
import os
import uuid

import pytest

psycopg = pytest.importorskip("psycopg")
DB = os.getenv("DATABASE_URL")


@pytest.fixture
def account():
    if not DB or "fake" in DB:
        if os.getenv("GITHUB_ACTIONS"):
            pytest.fail("DATABASE_URL is not set in CI; this test must not skip there")
        pytest.skip("Set DATABASE_URL to run this test")
    acc, user, rid = str(uuid.uuid4()), str(uuid.uuid4()), str(uuid.uuid4())
    tag = uuid.uuid4().hex[:8]
    with psycopg.connect(DB, autocommit=True) as conn:
        conn.execute("INSERT INTO accounts (id, name, slug, account_type, plan_slug) "
                     "VALUES (%s, 'LR-020 Onboarding', %s, 'REGULAR', 'free')", (acc, f"lr020-{tag}"))
        conn.execute("INSERT INTO users (id, account_id, email, first_name, last_name) "
                     "VALUES (%s, %s, %s, 'Ana', 'Reyes')", (user, acc, f"a-{tag}@example.com"))
        conn.execute("INSERT INTO consumer_reports (id, agent_id, agent_code, consumer_email, consent_given, "
                     "property_address, property_city, property_state, property_zip, status, delivery_method) "
                     "VALUES (%s, %s, 'LR020', 'lead@example.com', TRUE, '1 Main St', 'La Verne', 'CA', "
                     "'91750', 'sent', 'email')", (rid, user))
    yield acc, user, rid
    with psycopg.connect(DB, autocommit=True) as conn:
        conn.execute("DELETE FROM consumer_reports WHERE id = %s", (rid,))
        conn.execute("DELETE FROM users WHERE id = %s", (user,))
        conn.execute("DELETE FROM accounts WHERE id = %s", (acc,))   # email_log cascades


def _email(acc, report_id):
    with psycopg.connect(DB, autocommit=True) as conn:
        conn.execute("INSERT INTO email_log (account_id, report_id, provider, to_emails, subject, status) "
                     "VALUES (%s, %s, 'resend', ARRAY['someone@example.com'], 's', 'sent')", (acc, report_id))


def _steps(acc, user):
    from api.routes.onboarding import check_auto_completions
    with psycopg.connect(DB) as conn:
        with conn.cursor() as cur:
            return check_auto_completions(cur, user, acc, "REGULAR")


def test_a_lead_email_does_not_complete_the_first_report_step(account):
    acc, user, consumer_report = account
    _email(acc, consumer_report)
    assert "first_report" not in _steps(acc, user)


def test_the_agents_own_report_email_still_does(account):
    acc, user, consumer_report = account
    _email(acc, consumer_report)
    _email(acc, str(uuid.uuid4()))          # a report run the agent emailed
    assert "first_report" in _steps(acc, user)

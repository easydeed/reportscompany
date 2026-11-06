"""Consumer delivery failures are recorded on the real schema (LR-019).

Every failure write in `process_consumer_report` used `consumer_reports.error`,
a column the table has never had (0039_lead_pages.sql:36 defines
`error_message`). Each one raised inside its own error handling, the outer
handler's write raised too and was swallowed, and the row stayed at
`processing` for good, so the viewer and the agent waited on a report that had
already failed. Text-matching tests passed throughout because they asserted the
wrong column name as text.

These run the real task against the migrated database, with the outside world
faked at its edges: the MLS fetch, the PDF renderer, Twilio's client and the
Resend HTTP call. Each failure must leave an honest state, `failed`, with a
bounded reason that names no phone number, email address or key. Failures that
another attempt could fix are retried and the row says so; failures that cannot
be fixed by retrying are not; exhaustion is visible; success clears an earlier
attempt's reason.

Red on main: every case leaves the row at `processing` (or raises on the
missing column) instead of `failed` with a reason.
"""
import os
import sys
import uuid
from pathlib import Path

import pytest

psycopg = pytest.importorskip("psycopg", reason="psycopg is required for integration tests")
DB_URL = os.getenv("DATABASE_URL")
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

PHONE = "6265550199"
EMAIL = "lead.lr019@example.com"


@pytest.fixture
def db():
    if not DB_URL or "fake" in DB_URL:
        if os.getenv("GITHUB_ACTIONS"):
            pytest.fail("DATABASE_URL is not set in CI; this test must not skip there")
        pytest.skip("Set DATABASE_URL to run the consumer failure test")
    return DB_URL


@pytest.fixture
def tasks(db, monkeypatch):
    from worker import tasks as t
    from worker.vendors import simplyrets
    monkeypatch.setattr(t, "DATABASE_URL", db)
    # The outside world, faked at its edges.
    monkeypatch.setattr(simplyrets, "fetch_properties", lambda *a, **k: [])
    monkeypatch.setattr(t, "fetch_properties", lambda *a, **k: [], raising=False)

    def no_pdf(*a, **k):
        raise RuntimeError("PDF renderer not available in this test")
    monkeypatch.setattr(t, "render_pdf", no_pdf)
    return t


@pytest.fixture
def report(db):
    """One account, its agent, and one consumer report waiting to be delivered."""
    tag = uuid.uuid4().hex[:8]
    acc, user, rid = str(uuid.uuid4()), str(uuid.uuid4()), str(uuid.uuid4())
    with psycopg.connect(db) as conn:
        conn.execute("INSERT INTO accounts (id, name, slug, account_type, plan_slug, sms_credits) "
                     "VALUES (%s, 'LR-019 Test', %s, 'REGULAR', 'free', 10)", (acc, f"lr019-{tag}"))
        conn.execute("INSERT INTO users (id, account_id, email, first_name, last_name, phone) "
                     "VALUES (%s, %s, %s, 'Zoe', 'Noelle', '2135550100')", (user, acc, f"agent-{tag}@example.com"))

    def make(delivery_method="sms", phone=PHONE, email=EMAIL):
        with psycopg.connect(db) as conn:
            conn.execute(
                "INSERT INTO consumer_reports (id, agent_id, agent_code, consumer_phone, consumer_email, "
                "consent_given, property_address, property_city, property_state, property_zip, property_data, "
                "status, delivery_method) VALUES (%s, %s, 'LR019', %s, %s, TRUE, '1358 5th Street', "
                "'La Verne', 'CA', '91750', %s, 'pending', %s)",
                (rid, user, phone, email,
                 '{"address": "1358 5th Street", "city": "La Verne", "state": "CA", "zip": "91750", '
                 '"requester_name": "Dana Rivera"}', delivery_method))
        return rid

    yield make
    with psycopg.connect(db) as conn:
        conn.execute("DELETE FROM sms_logs WHERE consumer_report_id = %s", (rid,))
        conn.execute("DELETE FROM consumer_reports WHERE id = %s", (rid,))
        conn.execute("DELETE FROM users WHERE id = %s", (user,))
        conn.execute("DELETE FROM accounts WHERE id = %s", (acc,))


def _row(db, rid):
    with psycopg.connect(db) as conn:
        return conn.execute("SELECT status, error_message, consumer_sms_sent_at, consumer_email_sent_at "
                            "FROM consumer_reports WHERE id = %s", (rid,)).fetchone()


class FakeTwilio:
    """Stands in for twilio.rest.Client; `behaviour` decides each create()."""

    def __init__(self, behaviour):
        self.calls = []
        self.behaviour = behaviour
        self.messages = self

    def create(self, body, from_, to):
        self.calls.append(to)
        return self.behaviour(len(self.calls), to)


def _twilio(monkeypatch, behaviour):
    from worker.sms import send as sms_send
    fake = FakeTwilio(behaviour)
    monkeypatch.setattr(sms_send, "get_twilio_client", lambda: fake)
    monkeypatch.setattr(sms_send, "TWILIO_PHONE_NUMBER", "+15555550000")
    return fake


def _sent(n, to):
    class Msg:
        sid = f"SM{n:032d}"
        status = "queued"
    return Msg()


def _assert_clean(text):
    assert PHONE not in text and "626-555" not in text and EMAIL not in text, text
    assert len(text) <= 500


# ── SMS ─────────────────────────────────────────────────────────────────────

def test_sms_refused_for_good_is_failed_once_with_the_reason(tasks, report, db, monkeypatch):
    from twilio.base.exceptions import TwilioRestException

    def refuse(n, to):
        raise TwilioRestException(400, "uri", msg=f"The 'To' number {to} has opted out (STOP)", code=21610)
    fake = _twilio(monkeypatch, refuse)
    rid = report("sms")
    result = tasks.process_consumer_report.apply(args=[rid]).get(propagate=False)
    status, error, sms_at, _ = _row(db, rid)
    assert status == "failed"
    assert "SMS provider did not accept" in error and "opted out" in error
    assert "retrying" not in error and "gave up" not in error, "a STOP is not worth retrying"
    _assert_clean(error)
    assert sms_at is None
    assert len(fake.calls) == 1, "a permanent refusal must not be retried"
    assert result["ok"] is False


def test_sms_not_configured_is_failed_without_retrying(tasks, report, db, monkeypatch):
    from worker.sms import send as sms_send
    monkeypatch.setattr(sms_send, "get_twilio_client", lambda: None)
    rid = report("sms")
    tasks.process_consumer_report.apply(args=[rid]).get(propagate=False)
    status, error, *_ = _row(db, rid)
    assert status == "failed" and "Twilio not configured" in error
    assert "retrying" not in error and "gave up" not in error


def test_sms_timeout_is_retried_visibly_and_exhaustion_is_recorded(tasks, report, db, monkeypatch):
    seen = []

    def timeout(n, to):
        seen.append(_row(db, rid)[1])   # what the row said while this attempt ran
        raise TimeoutError(f"timed out talking to Twilio about {to}")
    fake = _twilio(monkeypatch, timeout)
    rid = report("sms")
    tasks.process_consumer_report.apply(args=[rid]).get(propagate=False)
    status, error, *_ = _row(db, rid)
    attempts = tasks.process_consumer_report.max_retries + 1
    assert len(fake.calls) == attempts, "a timeout is worth another attempt"
    assert seen[1] and "attempt 1 of 4; retrying" in seen[1], seen
    assert status == "failed"
    assert error.endswith(f"(gave up after {attempts} attempts)"), error
    assert error.count("gave up") == 1 and "retrying" not in error
    _assert_clean(error)


def test_a_success_after_a_failed_attempt_clears_the_reason(tasks, report, db, monkeypatch):
    def flaky(n, to):
        if n == 1:
            raise TimeoutError("timed out")
        return _sent(n, to)
    _twilio(monkeypatch, flaky)
    rid = report("sms")
    result = tasks.process_consumer_report.apply(args=[rid]).get(propagate=False)
    status, error, sms_at, _ = _row(db, rid)
    assert result["ok"] is True
    assert status == "sent" and sms_at is not None
    assert error is None, "a delivered report must not keep the earlier attempt's failure"


def test_no_phone_is_failed_without_retrying(tasks, report, db, monkeypatch):
    fake = _twilio(monkeypatch, _sent)
    rid = report("sms", phone=None)
    tasks.process_consumer_report.apply(args=[rid]).get(propagate=False)
    status, error, *_ = _row(db, rid)
    assert status == "failed" and "no usable delivery method" in error and "phone=missing" in error
    assert "retrying" not in error and "gave up" not in error
    assert fake.calls == []


def test_an_invalid_number_is_recorded_without_the_number(tasks, report, db, monkeypatch):
    _twilio(monkeypatch, _sent)
    rid = report("sms", phone="626-555-01")      # nine digits: send_sms refuses it
    tasks.process_consumer_report.apply(args=[rid]).get(propagate=False)
    status, error, *_ = _row(db, rid)
    assert status == "failed" and "Invalid phone number" in error
    assert "626-555-01" not in error and "[phone]" in error
    assert "retrying" not in error


# ── email ───────────────────────────────────────────────────────────────────

class FakeResponse:
    def __init__(self, code):
        self.status_code = code


def test_email_not_configured_is_failed_without_retrying(tasks, report, db, monkeypatch):
    monkeypatch.delenv("RESEND_API_KEY", raising=False)
    calls = []
    monkeypatch.setattr(tasks.httpx, "post", lambda *a, **k: calls.append(1) or FakeResponse(200))
    rid = report("email")
    tasks.process_consumer_report.apply(args=[rid]).get(propagate=False)
    status, error, _, email_at = _row(db, rid)
    assert status == "failed" and "RESEND_API_KEY is not configured" in error
    assert "retrying" not in error and calls == [] and email_at is None


def test_email_refused_with_a_4xx_is_failed_once(tasks, report, db, monkeypatch):
    monkeypatch.setenv("RESEND_API_KEY", "re_test_not_a_real_key_123456")
    calls = []
    monkeypatch.setattr(tasks.httpx, "post", lambda *a, **k: calls.append(1) or FakeResponse(422))
    rid = report("email")
    tasks.process_consumer_report.apply(args=[rid]).get(propagate=False)
    status, error, *_ = _row(db, rid)
    assert status == "failed" and "(status 422)" in error
    assert len(calls) == 1 and "retrying" not in error and "gave up" not in error


def test_email_timeout_is_retried_and_named_without_crashing(tasks, report, db, monkeypatch):
    """The failure branch read `resp`, unbound when the call raised: NameError."""
    monkeypatch.setenv("RESEND_API_KEY", "re_test_not_a_real_key_123456")
    calls = []

    def timeout(*a, **k):
        calls.append(1)
        raise tasks.httpx.ReadTimeout(f"timed out sending to {EMAIL}")
    monkeypatch.setattr(tasks.httpx, "post", timeout)
    rid = report("email")
    tasks.process_consumer_report.apply(args=[rid]).get(propagate=False)
    status, error, *_ = _row(db, rid)
    assert status == "failed"
    assert "no response: ReadTimeout" in error, error
    assert error.endswith("(gave up after 4 attempts)")
    assert len(calls) == 4
    _assert_clean(error)


def test_no_email_address_is_failed_without_retrying(tasks, report, db, monkeypatch):
    monkeypatch.setenv("RESEND_API_KEY", "re_test_not_a_real_key_123456")
    rid = report("email", email=None)
    tasks.process_consumer_report.apply(args=[rid]).get(propagate=False)
    status, error, *_ = _row(db, rid)
    assert status == "failed" and "email=missing" in error and "retrying" not in error


# ── anything else ─────────────────────────────────────────────────────────────

def test_an_unexpected_exception_is_recorded_not_left_processing(tasks, report, db, monkeypatch):
    monkeypatch.setenv("RESEND_API_KEY", "re_test_not_a_real_key_123456")

    def boom(*a, **k):
        raise RuntimeError(f"branding lookup broke for {EMAIL} / 626-555-0199 using sk_live_abcdef123456")
    monkeypatch.setattr(tasks, "_fetch_affiliate_branding", boom)
    rid = report("email")
    result = tasks.process_consumer_report.apply(args=[rid])
    assert result.failed(), "an unexpected exception still fails the task"
    status, error, *_ = _row(db, rid)
    assert status == "failed", "the row must not be left at processing"
    assert "unexpected error while processing the report (RuntimeError)" in error
    assert "[email]" in error and "[phone]" in error and "sk_live_[redacted]" in error
    _assert_clean(error)
    assert "abcdef123456" not in error


def test_the_failure_text_is_bounded_and_scrubbed():
    from worker.tasks import consumer_failure_text
    text = consumer_failure_text("x" * 900 + f" {EMAIL} +1 (626) 555-0199 Bearer abcdefghijkl")
    assert len(text) == 500
    assert consumer_failure_text(f"to {EMAIL} at +1 (626) 555-0199, Bearer abcdefghijkl") == \
        "to [email] at [phone], Bearer [redacted]"
    assert consumer_failure_text("status 422, Twilio code 21610") == "status 422, Twilio code 21610"
    assert consumer_failure_text("") == "Delivery failed"

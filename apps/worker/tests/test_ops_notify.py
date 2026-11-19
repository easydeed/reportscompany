"""LR-027 slice 3: operator alert delivery (design #317 rev 3, sections 5-7).

Real PostgreSQL, committed rows (claims commit before the provider call, so a
rolled-back fixture would hide exactly what is under test), fake providers
that count calls. Never a real SendGrid or Twilio request.
"""
import logging
import os
import sys
import threading
import time
import uuid
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
DB = os.getenv("DATABASE_URL")
psycopg = pytest.importorskip("psycopg")

from worker import ops_monitor, ops_notify, ops_signals  # noqa: E402
from worker.email.providers import sendgrid  # noqa: E402
from worker.ops_signals import Reading  # noqa: E402

EMAIL = "operator-secret@example.com"
PHONE = "+15555550123"


def u():
    return str(uuid.uuid4())


@pytest.fixture
def conn():
    if not DB:
        pytest.skip("DATABASE_URL (a disposable local database) is needed")
    c = psycopg.connect(DB)
    c.execute("DELETE FROM ops_alerts")          # cascades to members and notifications
    c.commit()
    yield c
    c.rollback()
    c.execute("DELETE FROM ops_alerts")
    c.commit()
    c.close()


@pytest.fixture
def on(monkeypatch):
    monkeypatch.setenv("OPS_ALERTS_ENABLED", "1")
    monkeypatch.setenv("OPS_ALERT_EMAIL", EMAIL)
    monkeypatch.setenv("OPS_ALERT_SMS_TO", PHONE)
    monkeypatch.setenv("OPS_PUBLIC_BASE", "https://example.test")


class Providers:
    """Fake SendGrid (send_email) and fake Twilio (client.messages.create)."""

    def __init__(self, monkeypatch):
        self.emails, self.texts = [], []
        self.email_outcome = sendgrid.Attempt(sendgrid.ACCEPTED, 202, "accepted")
        self.sms_result = "SM-test"         # a SID, or an exception to raise
        self.delay = 0.0
        self.lock = threading.Lock()
        monkeypatch.setattr(sendgrid, "send_email", self._email)
        monkeypatch.setattr(ops_notify, "_twilio_client", lambda: (self, "+15555550999"))

    @property
    def messages(self):
        return self

    def _email(self, to, subject, html, **kwargs):
        assert kwargs.get("single_attempt") is True and kwargs.get("timeout") == ops_notify.CALL_TIMEOUT_S
        time.sleep(self.delay)
        with self.lock:
            self.emails.append({"to": to, "subject": subject, "html": html})
        return self.email_outcome

    def create(self, body, from_, to):
        time.sleep(self.delay)
        with self.lock:
            self.texts.append({"to": to, "body": body})
        if isinstance(self.sms_result, Exception):
            raise self.sms_result

        class Msg:
            sid = self.sms_result
        return Msg()


@pytest.fixture
def providers(monkeypatch):
    return Providers(monkeypatch)


def trip(conn, key="schedule_overdue", identities=("schedule:a",)):
    with conn.cursor() as cur:
        event = ops_monitor.record(cur, key, Reading(True, list(identities), len(identities), {}))
    conn.commit()
    return event


def clear(conn, key="schedule_overdue"):
    with conn.cursor() as cur:
        ops_monitor.record(cur, key, Reading(False, [], 0, {}))
    conn.commit()


def rows(conn):
    with conn.cursor() as cur:
        cur.execute("""SELECT a.key, n.event, n.channel, n.state, n.attempts, n.provider_message_id,
                              n.last_error_class, n.claimed_at IS NOT NULL
                       FROM ops_alert_notifications n JOIN ops_alerts a ON a.id = n.alert_id
                       ORDER BY n.id""")
        out = cur.fetchall()
    conn.commit()
    return out


def events(conn):
    return {(k, e, ch) for k, e, ch, *_ in rows(conn)}


def dispatch(conn):
    return ops_notify.dispatch(conn, time.monotonic, time.monotonic() + 60)


# ── off by default: slice 2's guarantee holds until Jerry flips the switch ──

def test_switched_off_nothing_is_queued_or_sent(conn, providers, monkeypatch):
    monkeypatch.delenv("OPS_ALERTS_ENABLED", raising=False)
    monkeypatch.setenv("OPS_ALERT_EMAIL", EMAIL)
    monkeypatch.setenv("OPS_ALERT_SMS_TO", PHONE)
    trip(conn)
    clear(conn)
    dispatch(conn)
    assert rows(conn) == [] and providers.emails == [] and providers.texts == []
    monkeypatch.setenv("OPS_ALERTS_ENABLED", "0")
    trip(conn)
    dispatch(conn)
    assert rows(conn) == [] and providers.emails == [] and providers.texts == []


def test_switched_on_without_destinations_nothing_is_queued(conn, providers, monkeypatch):
    monkeypatch.setenv("OPS_ALERTS_ENABLED", "1")
    monkeypatch.delenv("OPS_ALERT_EMAIL", raising=False)
    monkeypatch.delenv("OPS_ALERT_SMS_TO", raising=False)
    trip(conn)
    dispatch(conn)
    assert rows(conn) == [] and providers.emails == [] and providers.texts == []
    assert "no destination set" in ops_monitor.enabled_mode()


# ── which events go to which channel ──

def test_an_open_incident_queues_email_and_sms_for_an_sms_key(conn, on):
    trip(conn, "schedule_overdue")
    trip(conn, "schedule_blocked", ("schedule:b",))           # its SMS column says email only
    assert events(conn) == {("schedule_overdue", "open", "email"), ("schedule_overdue", "open", "sms"),
                            ("schedule_blocked", "open", "email")}


def test_new_members_are_email_only_and_each_update_is_its_own_row(conn, on):
    trip(conn, identities=("schedule:a",))
    trip(conn, identities=("schedule:a", "schedule:b"))
    trip(conn, identities=("schedule:a", "schedule:b"))       # nothing new: nothing queued
    trip(conn, identities=("schedule:a", "schedule:b", "schedule:c"))
    updates = sorted((e, ch) for _, e, ch, *_ in rows(conn) if e.startswith("update:"))
    assert updates == [("update:1", "email"), ("update:2", "email")]


def test_recovery_queues_one_resolved_event_and_a_flap_reopens_by_email_only(conn, on):
    trip(conn)
    clear(conn)
    clear(conn)                                               # already resolved: nothing more
    trip(conn)                                                # within 30 min: flapping
    got = [(e, ch) for _, e, ch, *_ in rows(conn)]
    assert got.count(("resolved", "email")) == 1 and got.count(("resolved", "sms")) == 1
    assert got.count(("open", "email")) == 2 and got.count(("open", "sms")) == 1


def test_a_still_open_incident_is_renotified_every_six_hours_once(conn, on):
    trip(conn)
    with conn.cursor() as cur:
        cur.execute("UPDATE ops_alerts SET opened_at = now() - interval '13 hours'")
    conn.commit()
    for _ in range(3):
        with conn.cursor() as cur:
            ops_notify.enqueue_renotifications(cur)
        conn.commit()
    renotify = sorted((e, ch) for _, e, ch, *_ in rows(conn) if e.startswith("renotify:"))
    assert renotify == [("renotify:2", "email"), ("renotify:2", "sms")]


def test_sms_are_capped_at_ten_an_hour_with_one_cap_notice(conn, on):
    keys = [s.key for s in ops_signals.SIGNALS if s.sms][:6]
    assert len(keys) == 6
    for key in keys:                      # six opens and six recoveries: twelve texts wanted
        trip(conn, key, ("x:1",))
    for key in keys:
        clear(conn, key)
    sms = [e for _, e, ch, *_ in rows(conn) if ch == "sms"]
    assert len([e for e in sms if not e.startswith("sms_cap:")]) == ops_notify.SMS_CAP_PER_HOUR
    assert len([e for e in sms if e.startswith("sms_cap:")]) == 1                 # one notice, not two
    emails = [e for _, e, ch, *_ in rows(conn) if ch == "email"]
    assert len(emails) == 12                                                      # email is never capped


# ── delivery: claim before the call, never resend an uncertain outcome ──

def test_an_accepted_alert_is_sent_once_on_each_channel(conn, on, providers):
    trip(conn)
    dispatch(conn)
    dispatch(conn)
    assert len(providers.emails) == 1 and len(providers.texts) == 1
    states = {(ch, st, pid) for _, _, ch, st, _, pid, _, _ in rows(conn)}
    assert states == {("email", "accepted", None), ("sms", "accepted", "SM-test")}
    assert providers.emails[0]["to"] == [EMAIL] and providers.texts[0]["to"] == PHONE


def test_a_refused_text_is_retried_and_the_accepted_email_is_never_resent(conn, on, providers):
    from twilio.base.exceptions import TwilioRestException
    providers.sms_result = TwilioRestException(400, "uri", msg="invalid", code=21211)
    trip(conn)
    dispatch(conn)
    sms = [r for r in rows(conn) if r[2] == "sms"][0]
    assert sms[3:5] == ("not_sent", 1) and sms[6] == "refused_400" and sms[7] is False   # claim released
    dispatch(conn)
    assert len(providers.emails) == 1                                    # no second email
    assert len(providers.texts) == 2
    for _ in range(5):
        dispatch(conn)
    assert len(providers.texts) == ops_notify.MAX_ATTEMPTS               # bounded


def test_an_uncertain_email_is_never_retried_and_the_text_still_goes(conn, on, providers):
    providers.email_outcome = sendgrid.Attempt(sendgrid.UNKNOWN, None, "ReadTimeout")
    trip(conn)
    dispatch(conn)
    dispatch(conn)
    assert len(providers.emails) == 1 and len(providers.texts) == 1
    email = [r for r in rows(conn) if r[2] == "email"][0]
    assert email[3] == "unknown"


@pytest.mark.parametrize("outcome,state", [
    (sendgrid.Attempt(sendgrid.REJECTED, 400, "bad"), "not_sent"),
    (sendgrid.Attempt(sendgrid.NOT_SENT, None, "no connection"), "not_sent"),
    (sendgrid.Attempt(sendgrid.UNKNOWN, 502, "bad gateway"), "unknown"),
])
def test_email_outcomes_are_classified_from_the_single_attempt(conn, on, providers, monkeypatch, outcome, state):
    monkeypatch.delenv("OPS_ALERT_SMS_TO")
    providers.email_outcome = outcome
    trip(conn)
    dispatch(conn)
    assert [r[3] for r in rows(conn)] == [state]


@pytest.mark.parametrize("raised,state", [
    ("twilio_500", "unknown"),
    ("timeout_after_send", "unknown"),
    ("connect_timeout", "not_sent"),
])
def test_text_outcomes_are_classified_like_sms_outcome(conn, on, providers, monkeypatch, raised, state):
    import requests
    from twilio.base.exceptions import TwilioRestException
    monkeypatch.delenv("OPS_ALERT_EMAIL")
    providers.sms_result = {
        "twilio_500": TwilioRestException(500, "uri", msg="server"),
        "timeout_after_send": requests.exceptions.ReadTimeout("read"),
        "connect_timeout": requests.exceptions.ConnectTimeout("connect"),
    }[raised]
    trip(conn)
    dispatch(conn)
    assert [r[3] for r in rows(conn)] == [state]


def test_a_claim_with_no_outcome_becomes_unknown_after_the_lease_and_is_never_sent(conn, on, providers):
    trip(conn)
    with conn.cursor() as cur:            # a run that claimed, then died before recording anything
        cur.execute("""UPDATE ops_alert_notifications SET state = 'claimed', claimed_at = now() - interval '6 minutes',
                       claim_token = gen_random_uuid(), attempts = 1""")
    conn.commit()
    dispatch(conn)
    assert {r[3] for r in rows(conn)} == {"unknown"} and {r[6] for r in rows(conn)} == {"abandoned"}
    assert providers.emails == [] and providers.texts == []
    dispatch(conn)
    assert providers.emails == [] and providers.texts == []


def test_a_fresh_claim_is_left_alone(conn, on, providers):
    trip(conn)
    with conn.cursor() as cur:
        cur.execute("""UPDATE ops_alert_notifications SET state = 'claimed', claimed_at = now() - interval '1 minute',
                       claim_token = gen_random_uuid(), attempts = 1""")
    conn.commit()
    dispatch(conn)
    assert {r[3] for r in rows(conn)} == {"claimed"} and providers.emails == []


def test_two_runs_racing_for_one_row_send_once(conn, on, providers, monkeypatch):
    monkeypatch.delenv("OPS_ALERT_SMS_TO")
    providers.delay = 0.3
    trip(conn)
    with conn.cursor() as cur:
        cur.execute("SELECT id FROM ops_alert_notifications")
        row_id = cur.fetchone()[0]
    conn.commit()
    barrier, outcomes = threading.Barrier(2), []

    def run():
        c = psycopg.connect(DB)
        barrier.wait()
        outcomes.append(ops_notify.deliver(c, row_id))
        c.close()

    threads = [threading.Thread(target=run) for _ in range(2)]
    for t in threads:
        t.start()
    for t in threads:
        t.join(5)
    assert len(providers.emails) == 1 and sorted(outcomes, key=str) == sorted(["accepted", None], key=str)


def test_an_exception_after_the_claim_is_unknown_not_retried(conn, on, providers, monkeypatch):
    monkeypatch.delenv("OPS_ALERT_SMS_TO")

    def boom(*_a, **_k):
        raise RuntimeError("provider library blew up mid-call")

    monkeypatch.setattr(sendgrid, "send_email", boom)
    trip(conn)
    dispatch(conn)
    dispatch(conn)
    assert [r[3] for r in rows(conn)] == ["unknown"]


def test_an_invalid_destination_is_not_sent_without_a_call(conn, on, providers, monkeypatch):
    monkeypatch.delenv("OPS_ALERT_EMAIL")
    monkeypatch.setenv("OPS_ALERT_SMS_TO", "555-0123")
    trip(conn)
    dispatch(conn)
    assert [r[3] for r in rows(conn)] == ["not_sent"] and providers.texts == []
    assert rows(conn)[0][6] == "invalid_destination"


def test_the_email_lists_alerts_whose_delivery_is_uncertain(conn, on, providers, monkeypatch):
    monkeypatch.delenv("OPS_ALERT_SMS_TO")
    providers.email_outcome = sendgrid.Attempt(sendgrid.UNKNOWN, None, "ReadTimeout")
    trip(conn, "schedule_overdue")
    dispatch(conn)
    providers.email_outcome = sendgrid.Attempt(sendgrid.ACCEPTED, 202, "accepted")
    trip(conn, "dispatch_stranded", ("run:x",))
    dispatch(conn)
    assert "1 earlier alert(s) may not have been delivered" in providers.emails[-1]["html"]


def test_resolved_incidents_are_purged_after_ninety_days(conn, on):
    trip(conn)
    clear(conn)
    with conn.cursor() as cur:
        cur.execute("UPDATE ops_alerts SET resolved_at = now() - interval '91 days', opened_at = now() - interval '92 days'")
    conn.commit()
    dispatch(conn)
    with conn.cursor() as cur:
        cur.execute("SELECT count(*) FROM ops_alerts")
        assert cur.fetchone()[0] == 0
    conn.commit()


# ── the monitor drives it, inside its own run ──

def test_a_monitor_run_queues_and_delivers_in_the_same_run(conn, on, providers, monkeypatch):
    sig = ops_signals.Signal("schedule_overdue", True, "Scheduled sends have stopped.",
                             lambda cur: Reading(True, ["schedule:z"], 1, {}))
    monkeypatch.setattr(ops_signals, "SIGNALS", [sig])
    monkeypatch.setattr(ops_monitor, "heartbeat_readings", lambda client: {})
    results = ops_monitor.run_once(DB, object())
    assert results == {"schedule_overdue": "open"}
    assert len(providers.emails) == 1 and len(providers.texts) == 1
    assert ops_monitor.enabled_mode() == "send (email, sms)"


# ── privacy: bodies and logs carry no customer data and no destination ──

PII = ("Jane Homeowner", "jane.homeowner@example.com", "+13105551234", "1 Secret Street", "Agent Smith")


@pytest.fixture
def pii_rows():
    rid = u()
    c = psycopg.connect(DB, autocommit=True)
    c.execute("SET session_replication_role = replica")
    c.execute("""INSERT INTO consumer_reports (id, agent_id, agent_code, property_address, consumer_email,
                 consumer_phone, status, created_at, updated_at, error_message)
                 VALUES (%s, %s, 'code', %s, %s, %s, 'needs_review', now() - interval '1 hour', now(), %s)""",
              (rid, u(), PII[3], PII[1], PII[2], f"held for {PII[0]} / {PII[4]}"))
    yield rid
    c.execute("DELETE FROM consumer_reports WHERE id = %s", (rid,))
    c.close()


def test_bodies_and_logs_carry_no_customer_data_and_no_destination(conn, on, providers, monkeypatch,
                                                                   pii_rows, caplog):
    caplog.set_level(logging.DEBUG)
    sig = next(s for s in ops_signals.SIGNALS if s.key == "consumer_delivery_stuck")
    monkeypatch.setattr(ops_signals, "SIGNALS", [sig])
    monkeypatch.setattr(ops_monitor, "heartbeat_readings", lambda client: {})
    ops_monitor.run_once(DB, object())
    assert providers.emails and providers.texts
    assert f"consumer:{pii_rows}" in providers.emails[0]["html"]                # identities, by design
    captured = " ".join([e["subject"] + e["html"] for e in providers.emails] +
                        [t["body"] for t in providers.texts]) + caplog.text
    for value in PII:
        assert value not in captured, value
    assert EMAIL not in caplog.text and PHONE not in caplog.text and PHONE[2:] not in caplog.text


def test_the_operator_text_path_logs_no_destination_unlike_the_customer_path(conn, on, providers,
                                                                             monkeypatch, caplog):
    """Design section 5: the customer sender logs the number; the operator path
    must not. The control proves this check sees a number when one is logged."""
    from worker.sms import send as sms_send
    monkeypatch.delenv("OPS_ALERT_EMAIL")
    caplog.set_level(logging.DEBUG)
    trip(conn)
    dispatch(conn)
    assert providers.texts and PHONE not in caplog.text and PHONE[2:] not in caplog.text
    caplog.clear()
    monkeypatch.setattr(sms_send, "get_twilio_client", lambda: providers)
    sms_send.send_sms(PHONE[2:], "control")                       # the customer path
    assert PHONE in caplog.text


def test_the_operator_twilio_client_is_bounded_and_quiet(monkeypatch, caplog):
    from worker.sms import send as sms_send
    monkeypatch.setattr(sms_send, "TWILIO_ACCOUNT_SID", "AC" + "0" * 32)
    monkeypatch.setattr(sms_send, "TWILIO_AUTH_TOKEN", "token")
    monkeypatch.setattr(sms_send, "TWILIO_PHONE_NUMBER", "+15555550999")
    caplog.set_level(logging.DEBUG)
    client, _ = ops_notify._twilio_client()
    assert client.http_client.timeout == ops_notify.CALL_TIMEOUT_S
    with pytest.raises(Exception):
        client.http_client.request("POST", "http://127.0.0.1:1/Messages.json", data={"To": PHONE})
    assert "Twilio API Request" not in caplog.text and PHONE not in caplog.text

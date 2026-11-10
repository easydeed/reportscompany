"""Consumer delivery has one owner, one record and one debit (LR-020, D-069).

Design: docs/plans/launch-readiness-2026-11-06/LR-020-021_DELIVERY_STATE.md,
revision 3, Codex PASS on #280. Every test runs the real task against a
database built from every migration, with the outside world faked at its edges
(MLS, PDF renderer, R2, Twilio's client, Resend's HTTP call).

On main:
  * two runs of one report could both generate, and the later one replaced the
    comps and the PDF behind a link already sent (R1b);
  * a replay of a delivered report set it back to `processing` and regenerated
    it (R1);
  * a second run held a LIVE send for review, a false alert (R2);
  * the debit was a separate write (R3), the attempt had no identity (R4);
  * an unknown email was held with no replay (Jerry approved one, same key).
"""
import json
import os
import threading
import uuid
from datetime import timedelta
from pathlib import Path

import pytest

from test_consumer_failures_are_recorded import (  # noqa: F401  (fixtures)
    EMAIL, PHONE, WorkerDied, _age_claim, _credits, _row, _run, _sent, _twilio,
    db, report, tasks,
)

psycopg = pytest.importorskip("psycopg")
AGENT_PHONE_DIGITS = "2135550100"


class Resp:
    def __init__(self, code, email_id=None):
        self.status_code = code
        self._id = email_id

    def json(self):
        return {"id": self._id} if self._id else {}


def _q(db, sql, *params):
    with psycopg.connect(db) as conn:
        return conn.execute(sql, params).fetchall()


def _report_row(db, rid):
    return _q(db, "SELECT status, generation_id, delivery_attempt_id, delivery_claimed_at, "
                  "comparables, property_data, pdf_url, consumer_sms_sent_at, consumer_email_sent_at, "
                  "error_message FROM consumer_reports WHERE id = %s", rid)[0]


def _lead_calls(fake):
    return [c for c in fake.calls if c.endswith(PHONE)]


@pytest.fixture
def r2(tasks, monkeypatch, tmp_path):
    """A fake renderer and object store. Each run's PDF bytes name its generation."""
    store = {}

    def render(run_id, account_id, html_content, print_base=None, **k):
        path = tmp_path / f"{uuid.uuid4().hex}.pdf"
        path.write_bytes(f"PDF by {threading.current_thread().name}".encode())
        return str(path), None

    def upload(local_path, key, *a, **k):
        store[key] = Path(local_path).read_bytes()
        return f"https://r2.test/{key}"
    monkeypatch.setattr(tasks, "render_pdf", render)
    monkeypatch.setattr(tasks, "upload_to_r2", upload)
    return store


def _in_thread(name, fn):
    out = {}

    def run():
        try:
            out["result"] = fn()
        except BaseException as e:   # noqa: BLE001 - reported to the test
            out["error"] = e
    t = threading.Thread(target=run, name=name)
    t.start()
    return t, out


# ── one owner, one call, one debit ──────────────────────────────────────────

def test_two_runs_synchronised_at_the_text_make_one_call_and_one_debit(tasks, report, db, monkeypatch):
    fake = _twilio(monkeypatch, _sent)
    rid = report("sms")
    real_claim = tasks.consumer_delivery.claim_sms
    barrier = threading.Barrier(2, timeout=30)

    def claim_together(*a, **k):
        barrier.wait()
        return real_claim(*a, **k)
    monkeypatch.setattr(tasks.consumer_delivery, "claim_sms", claim_together)
    a, ra = _in_thread("run-a", lambda: _run(tasks, rid))
    b, rb = _in_thread("run-b", lambda: _run(tasks, rid))
    a.join(60)
    b.join(60)
    assert "error" not in ra and "error" not in rb, (ra, rb)
    assert len(_lead_calls(fake)) == 1, fake.calls
    status, *_rest = _report_row(db, rid)
    assert status == "sent"
    assert _credits(db, rid) == 9, "exactly one credit for one text"
    journal = _q(db, "SELECT status FROM sms_logs WHERE consumer_report_id = %s AND recipient_type = 'consumer'", rid)
    assert journal == [("sent",)], journal


def test_two_runs_synchronised_at_the_email_make_one_call(tasks, report, db, monkeypatch):
    monkeypatch.setenv("RESEND_API_KEY", "re_test_not_a_real_key_123456")
    _twilio(monkeypatch, _sent)
    calls = []
    monkeypatch.setattr(tasks.httpx, "post",
                        lambda *a, **k: calls.append(k["headers"]["Idempotency-Key"]) or Resp(200, "em_1"))
    rid = report("email")
    real_claim = tasks.consumer_delivery.claim_email
    barrier = threading.Barrier(2, timeout=30)

    def claim_together(*a, **k):
        barrier.wait()
        return real_claim(*a, **k)
    monkeypatch.setattr(tasks.consumer_delivery, "claim_email", claim_together)
    a, _ = _in_thread("run-a", lambda: _run(tasks, rid))
    b, _ = _in_thread("run-b", lambda: _run(tasks, rid))
    a.join(60)
    b.join(60)
    assert len(calls) == 1, calls
    assert _report_row(db, rid)[0] == "sent"
    assert _credits(db, rid) == 10, "email never spends an SMS credit"
    rows = _q(db, "SELECT status, idempotency_key, provider_message_id FROM email_log WHERE report_id = %s", rid)
    assert rows == [("sent", calls[0], "em_1")], rows


def test_the_journal_holds_the_exact_text_before_the_call(tasks, report, db, monkeypatch):
    seen = {}

    def check_journal_first(n, to):
        if to.endswith(PHONE):
            seen["journal"] = _q(db, "SELECT status, message, message_body, from_phone, to_phone "
                                     "FROM sms_logs WHERE consumer_report_id = %s AND recipient_type = 'consumer'", rid)
        return _sent(n, to)
    fake = _twilio(monkeypatch, check_journal_first)
    sent_bodies = []
    real_send = tasks.send_report_sms

    def spy(**k):
        result = real_send(**k)
        sent_bodies.append(result["message_body"])
        return result
    monkeypatch.setattr(tasks, "send_report_sms", spy)
    rid = report("sms")
    _run(tasks, rid)
    [(status, message, message_body, from_phone, to_phone)] = seen["journal"]
    assert status == "pending", "the attempt is journalled, unsettled, before the provider call"
    assert message == message_body == sent_bodies[0], "the journal must hold the body that was sent"
    assert from_phone == "+15555550000" and to_phone.endswith(PHONE)
    assert len(_lead_calls(fake)) == 1


# ── R1: a delivered report is finished ──────────────────────────────────────

def test_a_replay_of_a_delivered_report_changes_nothing_and_sends_nothing(tasks, report, db, monkeypatch, r2):
    fake = _twilio(monkeypatch, _sent)
    rid = report("sms")
    _run(tasks, rid)
    before = _report_row(db, rid)
    objects_before = dict(r2)
    renders = []
    monkeypatch.setattr(tasks, "render_pdf", lambda *a, **k: renders.append(1) or (_ for _ in ()).throw(AssertionError))
    result = _run(tasks, rid)
    assert result["ok"] is True and "already delivered" in result["note"]
    assert _report_row(db, rid) == before, "a replay rewrote a delivered report"
    assert dict(r2) == objects_before and renders == [], "a replay regenerated the PDF"
    assert len(_lead_calls(fake)) == 1


# ── R1b / §3.2: generation is owned and frozen at the claim ─────────────────

def test_a_generation_that_finishes_after_the_send_cannot_replace_it(tasks, report, db, monkeypatch, r2):
    """B starts generating, A generates, claims and sends, THEN B finishes."""
    _twilio(monkeypatch, _sent)
    rid = report("sms")
    b_generating, a_sent = threading.Event(), threading.Event()
    real_publish = tasks.consumer_delivery.publish_generation
    real_record = tasks.consumer_delivery.record_sms_sent

    def publish(*a, **k):
        if threading.current_thread().name == "run-b":
            b_generating.set()
            assert a_sent.wait(30)
        return real_publish(*a, **k)

    def record(*a, **k):
        out = real_record(*a, **k)
        a_sent.set()
        return out
    monkeypatch.setattr(tasks.consumer_delivery, "publish_generation", publish)
    monkeypatch.setattr(tasks.consumer_delivery, "record_sms_sent", record)

    b, rb = _in_thread("run-b", lambda: _run(tasks, rid))
    assert b_generating.wait(30)
    ra = {}
    a, ra = _in_thread("run-a", lambda: _run(tasks, rid))
    a.join(60)
    b.join(60)
    assert ra["result"]["ok"] is True, ra
    assert "nothing sent" in rb["result"]["note"], rb

    status, generation, _a, _c, comps, prop, pdf_url, sms_at, *_ = _report_row(db, rid)
    assert status == "sent" and sms_at is not None
    key = pdf_url.split("https://r2.test/", 1)[1]
    assert key.endswith(f"/{generation}.pdf"), (key, generation)
    assert r2[key] == b"PDF by run-a", "the PDF behind the delivered link is not the delivered one"
    others = [k for k in r2 if k != key]
    assert len(others) == 1 and r2[others[0]] == b"PDF by run-b", "B's PDF must sit at its own key"


def test_a_generation_published_before_the_claim_is_the_one_sent(tasks, report, db, monkeypatch, r2):
    """A publishes and waits; B publishes over it and sends; A's claim then fails."""
    fake = _twilio(monkeypatch, _sent)
    rid = report("sms")
    a_published, b_sent = threading.Event(), threading.Event()
    real_claim = tasks.consumer_delivery.claim_sms
    real_record = tasks.consumer_delivery.record_sms_sent

    def claim(*a, **k):
        if threading.current_thread().name == "run-a":
            a_published.set()
            assert b_sent.wait(30)
        return real_claim(*a, **k)

    def record(*a, **k):
        out = real_record(*a, **k)
        b_sent.set()
        return out
    monkeypatch.setattr(tasks.consumer_delivery, "claim_sms", claim)
    monkeypatch.setattr(tasks.consumer_delivery, "record_sms_sent", record)
    a, ra = _in_thread("run-a", lambda: _run(tasks, rid))
    assert a_published.wait(30)
    b, rb = _in_thread("run-b", lambda: _run(tasks, rid))
    b.join(60)
    a.join(60)
    assert len(_lead_calls(fake)) == 1
    assert "not sent" in ra["result"]["note"], ra
    *_x, pdf_url, _sms, _em, _err = _report_row(db, rid)
    assert r2[pdf_url.split("https://r2.test/", 1)[1]] == b"PDF by run-b"


def test_only_the_current_generations_publisher_can_claim(tasks, report, db, monkeypatch, r2):
    """A publishes, B publishes over it, then A tries to claim FIRST: refused.

    The claim requires `generation_id = <mine>`, so the run that sends is the
    run whose comps, values and PDF the report shows."""
    senders = []

    def record_sender(n, to):
        if to.endswith(PHONE):
            senders.append(threading.current_thread().name)
        return _sent(n, to)
    _twilio(monkeypatch, record_sender)
    rid = report("sms")
    a_pub, b_pub, a_tried = threading.Event(), threading.Event(), threading.Event()
    real_publish = tasks.consumer_delivery.publish_generation
    real_claim = tasks.consumer_delivery.claim_sms

    def publish(*a, **k):
        if threading.current_thread().name == "run-b":
            assert a_pub.wait(30)
        out = real_publish(*a, **k)
        (a_pub if threading.current_thread().name == "run-a" else b_pub).set()
        return out

    def claim(*a, **k):
        if threading.current_thread().name == "run-a":
            assert b_pub.wait(30)
            try:
                return real_claim(*a, **k)
            finally:
                a_tried.set()
        assert a_tried.wait(30)
        return real_claim(*a, **k)
    monkeypatch.setattr(tasks.consumer_delivery, "publish_generation", publish)
    monkeypatch.setattr(tasks.consumer_delivery, "claim_sms", claim)
    a, ra = _in_thread("run-a", lambda: _run(tasks, rid))
    b, rb = _in_thread("run-b", lambda: _run(tasks, rid))
    a.join(60)
    b.join(60)
    assert senders == ["run-b"], f"the text was sent by {senders}, not by the current generation's publisher"
    *_x, pdf_url, _sms, _em, _err = _report_row(db, rid)
    assert r2[pdf_url.split("https://r2.test/", 1)[1]] == b"PDF by run-b"


# ── R2: a live claim is not a dead one ──────────────────────────────────────

def test_a_worker_that_dies_before_the_call_is_never_sent_and_held_only_when_stale(tasks, report, db, monkeypatch, caplog):
    fake = _twilio(monkeypatch, _sent)

    def died(**k):
        raise WorkerDied()
    monkeypatch.setattr(tasks, "send_report_sms", died)
    rid = report("sms")
    _run(tasks, rid)
    assert _report_row(db, rid)[0] == "sending"
    caplog.clear()
    note = _run(tasks, rid)["note"]
    assert "another run is sending" in note and _report_row(db, rid)[0] == "sending"
    assert not [r for r in caplog.records if r.levelname == "CRITICAL"], "a live claim raised an alert"
    _age_claim(db, rid)
    _run(tasks, rid)
    assert _report_row(db, rid)[0] == "needs_review"
    assert fake.calls == [] and _credits(db, rid) == 10


# ── refusals release the claim; a retry is a new attempt ────────────────────

def test_a_refused_text_releases_its_claim_and_the_retry_is_a_new_attempt(tasks, report, db, monkeypatch):
    from twilio.base.exceptions import TwilioRestException

    def flaky(n, to):
        if n == 1:
            raise TwilioRestException(429, "uri", msg="Too Many Requests", code=20429)
        return _sent(n, to)
    _twilio(monkeypatch, flaky)
    rid = report("sms")
    _run(tasks, rid)
    rows = _q(db, "SELECT id, status FROM sms_logs WHERE consumer_report_id = %s "
                  "AND recipient_type = 'consumer' ORDER BY created_at", rid)
    assert [s for _, s in rows] == ["failed", "sent"], rows
    assert rows[0][0] != rows[1][0]
    status, _g, attempt, *_ = _report_row(db, rid)
    assert status == "sent" and str(attempt) == str(rows[1][0])
    assert _credits(db, rid) == 9


def test_an_email_refused_on_the_first_call_retries_with_a_new_key(tasks, report, db, monkeypatch):
    monkeypatch.setenv("RESEND_API_KEY", "re_test_not_a_real_key_123456")
    _twilio(monkeypatch, _sent)
    keys = []

    def post(*a, **k):
        keys.append(k["headers"]["Idempotency-Key"])
        return Resp(429) if len(keys) == 1 else Resp(200, "em_2")
    monkeypatch.setattr(tasks.httpx, "post", post)
    rid = report("email")
    _run(tasks, rid)
    assert len(keys) == 2 and keys[0] != keys[1], keys
    assert _report_row(db, rid)[0] == "sent"


# ── the one approved email replay (§3.4) ────────────────────────────────────

def _email(tasks, monkeypatch, *responses):
    """Resend answers in order: a Resp, or an exception to raise."""
    monkeypatch.setenv("RESEND_API_KEY", "re_test_not_a_real_key_123456")
    calls = []

    def post(*a, **k):
        calls.append({"key": k["headers"]["Idempotency-Key"], "body": json.dumps(k["json"], sort_keys=True)})
        answer = responses[len(calls) - 1]
        if isinstance(answer, BaseException) or (isinstance(answer, type) and issubclass(answer, BaseException)):
            raise answer
        return answer
    monkeypatch.setattr(tasks.httpx, "post", post)
    return calls


def test_an_unknown_email_is_replayed_once_with_the_same_request_and_settles(tasks, report, db, monkeypatch):
    _twilio(monkeypatch, _sent)
    calls = _email(tasks, monkeypatch, tasks.httpx.ReadTimeout("lost"), Resp(200, "em_orig"))
    rid = report("email")
    _run(tasks, rid)
    assert len(calls) == 2
    assert calls[0] == calls[1], "the replay must send the same key and a byte-identical body"
    status, *_x, email_at, _err = _report_row(db, rid)
    assert status == "sent" and email_at is not None
    assert _q(db, "SELECT provider_message_id FROM email_log WHERE report_id = %s", rid) == [("em_orig",)]


@pytest.mark.parametrize("replay", [
    Resp(409),                                  # concurrent_idempotent_requests / invalid_idempotent_request
    Resp(429),                                  # the replay created nothing; the first call is still unknown
    Resp(503),
])
def test_anything_but_a_200_on_the_replay_is_held_never_failed(tasks, report, db, monkeypatch, replay):
    _twilio(monkeypatch, _sent)
    calls = _email(tasks, monkeypatch, tasks.httpx.ReadTimeout("lost"), replay, Resp(200))
    rid = report("email")
    result = _run(tasks, rid)
    status, *_x, err = _report_row(db, rid)
    assert status == "needs_review", (status, err)
    assert len(calls) == 2, "at most two calls per attempt, and no Celery retry of an unknown email"
    assert "one replay with the same key" in err
    assert result.get("needs_review") is True


def test_a_crash_during_the_replay_is_held_with_no_third_call(tasks, report, db, monkeypatch):
    _twilio(monkeypatch, _sent)
    calls = _email(tasks, monkeypatch, tasks.httpx.ReadTimeout("lost"), WorkerDied(), Resp(200))
    rid = report("email")
    _run(tasks, rid)
    _age_claim(db, rid)
    _run(tasks, rid)
    assert len(calls) == 2 and _report_row(db, rid)[0] == "needs_review"


def test_no_replay_once_the_attempt_is_no_longer_owned(tasks, report, db, monkeypatch):
    _twilio(monkeypatch, _sent)
    monkeypatch.setenv("RESEND_API_KEY", "re_test_not_a_real_key_123456")
    calls = []

    def post(*a, **k):
        calls.append(1)
        # An operator held the attempt while the first call was out.
        with psycopg.connect(db, autocommit=True) as conn:
            conn.execute("UPDATE consumer_reports SET status = 'needs_review' WHERE id = %s", (rid,))
        raise tasks.httpx.ReadTimeout("lost")
    monkeypatch.setattr(tasks.httpx, "post", post)
    rid = report("email")
    _run(tasks, rid)
    assert len(calls) == 1, "a run that no longer owns the attempt must not replay it"
    assert _report_row(db, rid)[0] == "needs_review"


def test_no_replay_past_the_deadline(tasks, report, db, monkeypatch):
    """A clock injected through the key's lifetime: elapsed is past lifetime - margin."""
    _twilio(monkeypatch, _sent)
    monkeypatch.setattr(tasks.consumer_delivery, "EMAIL_KEY_LIFETIME", timedelta(0))
    calls = _email(tasks, monkeypatch, tasks.httpx.ReadTimeout("lost"), Resp(200))
    rid = report("email")
    _run(tasks, rid)
    assert len(calls) == 1 and _report_row(db, rid)[0] == "needs_review"


def test_the_replay_deadline_boundary():
    from worker import consumer_delivery as cd
    cutoff = cd.EMAIL_KEY_LIFETIME - cd.EMAIL_REPLAY_MARGIN
    assert cd.replay_deadline_ok(cutoff - timedelta(seconds=1))
    assert not cd.replay_deadline_ok(cutoff)
    assert not cd.replay_deadline_ok(cd.EMAIL_KEY_LIFETIME)
    assert cd.EMAIL_REPLAY_MARGIN >= timedelta(seconds=15), "the margin must cover the 15 s request timeout"


# ── held sends: the operator's workflow (§6) ────────────────────────────────

def _held_text(tasks, monkeypatch, report, db):
    """A consumer text whose answer was lost: held, attempt journalled."""
    fake = _twilio(monkeypatch, lambda n, to: (_ for _ in ()).throw(TimeoutError("lost")))
    rid = report("sms")
    _run(tasks, rid)
    status, _g, attempt, *_ = _report_row(db, rid)
    assert status == "needs_review"
    return rid, str(attempt), fake


def test_resolving_a_held_text_as_sent_records_it_and_debits_once(tasks, report, db, monkeypatch):
    from worker import consumer_delivery as cd
    rid, attempt, fake = _held_text(tasks, monkeypatch, report, db)
    with psycopg.connect(db, autocommit=True) as conn:
        cd.resolve_sent(conn, rid, stage="consumer", attempt_id=attempt, provider_id="SMfound",
                        evidence="Twilio log: delivered 12:01", operator="jerry")
        with pytest.raises(cd.ResolutionRefused):
            cd.resolve_sent(conn, rid, stage="consumer", attempt_id=attempt, provider_id="SMfound",
                            evidence="again", operator="jerry")
        # A late provider answer for the same attempt changes nothing.
        assert cd.record_sms_sent(conn, rid, attempt, account_id=_account(db, rid), sid="SMlate") is False
    status, *_x, sms_at, _e, _err = _report_row(db, rid)
    assert status == "sent" and sms_at is not None
    assert _credits(db, rid) == 9, "one debit, however many times it is recorded"
    assert _q(db, "SELECT status, resolution, resolved_by, resolution_evidence FROM sms_logs "
                  "WHERE id = %s", attempt) == [("sent", "sent", "jerry", "Twilio log: delivered 12:01")]
    assert len(fake.calls) == 1, "the tool never sends"


def test_resolving_not_sent_releases_without_sending_and_a_late_answer_still_wins(tasks, report, db, monkeypatch, caplog):
    from worker import consumer_delivery as cd
    rid, attempt, fake = _held_text(tasks, monkeypatch, report, db)
    with psycopg.connect(db, autocommit=True) as conn:
        cd.resolve_not_sent(conn, rid, stage="consumer", attempt_id=attempt,
                            evidence="Twilio search 11:50-12:20 for the number: no message", operator="jerry")
    status, _g, claimed_attempt, *_ = _report_row(db, rid)
    assert status == "failed" and claimed_attempt is None
    assert len(fake.calls) == 1, "resolving not-sent must not send"
    assert _q(db, "SELECT status, resolution FROM sms_logs WHERE id = %s", attempt) == [("failed", "not_sent")]
    # Twilio's answer turns up after all: the evidence is recorded, one debit,
    # and the contradiction is raised.
    with psycopg.connect(db, autocommit=True) as conn:
        assert cd.record_sms_sent(conn, rid, attempt, account_id=_account(db, rid), sid="SMlate") is True
    assert _report_row(db, rid)[0] == "sent" and _credits(db, rid) == 9
    assert any("CONTRADICTION" in r.getMessage() and r.levelname == "CRITICAL" for r in caplog.records)


def test_resolutions_refuse_the_wrong_attempt_stage_or_missing_evidence(tasks, report, db, monkeypatch):
    from worker import consumer_delivery as cd
    rid, attempt, _fake = _held_text(tasks, monkeypatch, report, db)
    # A real attempt of the same report, but not the held one.
    older = str(uuid.uuid4())
    with psycopg.connect(db, autocommit=True) as conn:
        conn.execute("INSERT INTO sms_logs (id, account_id, consumer_report_id, to_phone, from_phone, message, "
                     "recipient_type, status) VALUES (%s, %s, %s, '+16265550199', '+15555550000', 'old', "
                     "'consumer', 'failed')", (older, _account(db, rid), rid))
    with psycopg.connect(db, autocommit=True) as conn:
        for kwargs in (
            dict(stage="consumer", attempt_id=str(uuid.uuid4()), provider_id="SM1", evidence="e", operator="j"),
            dict(stage="consumer", attempt_id=older, provider_id="SM1", evidence="e", operator="j"),
            dict(stage="agent", attempt_id=attempt, provider_id="SM1", evidence="e", operator="j"),
            dict(stage="consumer", attempt_id=attempt, provider_id="", evidence="e", operator="j"),
            dict(stage="consumer", attempt_id=attempt, provider_id="SM1", evidence=" ", operator="j"),
        ):
            with pytest.raises(cd.ResolutionRefused):
                cd.resolve_sent(conn, rid, **kwargs)
        with pytest.raises(cd.ResolutionRefused):
            cd.resolve_not_sent(conn, rid, stage="consumer", attempt_id=attempt, evidence="", operator="j")
        with pytest.raises(cd.ResolutionRefused):
            cd.resolve_not_sent(conn, rid, stage="consumer", attempt_id=older, evidence="e", operator="j")
    assert _report_row(db, rid)[0] == "needs_review" and _credits(db, rid) == 10


def test_an_agent_resolution_never_touches_the_consumer_or_credits(tasks, report, db, monkeypatch):
    from worker import consumer_delivery as cd
    fake = _twilio(monkeypatch, _sent)
    rid = report("sms")
    _run(tasks, rid)
    agent_attempt = str(uuid.uuid4())
    with psycopg.connect(db, autocommit=True) as conn:
        conn.execute("INSERT INTO sms_logs (id, account_id, consumer_report_id, to_phone, from_phone, message, "
                     "recipient_type, status) VALUES (%s, %s, %s, '+12135550100', '+15555550000', 'lead', "
                     "'agent', 'pending')", (agent_attempt, _account(db, rid), rid))
        conn.execute("UPDATE consumer_reports SET agent_sms_sent_at = NULL, agent_notify_status = 'needs_review', "
                     "agent_notify_attempt_id = %s, agent_notify_claimed_at = NOW() - interval '1 hour' "
                     "WHERE id = %s", (agent_attempt, rid))
        before = _report_row(db, rid)
        credits = _credits(db, rid)
        cd.resolve_sent(conn, rid, stage="agent", attempt_id=agent_attempt, provider_id="SMagent",
                        evidence="Twilio log", operator="jerry")
    assert _report_row(db, rid) == before and _credits(db, rid) == credits
    assert _q(db, "SELECT agent_notify_status, agent_sms_sid FROM consumer_reports WHERE id = %s", rid) == \
        [("sent", "SMagent")]
    assert len(_lead_calls(fake)) == 1


def test_list_shows_held_and_stale_attempts_with_masked_destinations(tasks, report, db, monkeypatch):
    from worker import consumer_delivery as cd
    rid, attempt, _fake = _held_text(tasks, monkeypatch, report, db)
    with psycopg.connect(db, autocommit=True) as conn:
        rows = [r for r in cd.list_held(conn.cursor(), stage="consumer") if r["report_id"] == rid]
    assert len(rows) == 1 and rows[0]["attempt_id"] == attempt and rows[0]["channel"] == "sms"
    assert PHONE not in json.dumps(rows) and rows[0]["destination"].endswith(PHONE[-4:])


def test_hold_moves_only_a_stale_claim(tasks, report, db, monkeypatch):
    from worker import consumer_delivery as cd
    monkeypatch.setattr(tasks, "send_report_sms", lambda **k: (_ for _ in ()).throw(WorkerDied()))
    _twilio(monkeypatch, _sent)
    rid = report("sms")
    _run(tasks, rid)
    attempt = str(_report_row(db, rid)[2])
    with psycopg.connect(db, autocommit=True) as conn:
        with pytest.raises(cd.ResolutionRefused):
            cd.hold_stale(conn, rid, stage="consumer", attempt_id=attempt, operator="jerry")
        _age_claim(db, rid)
        cd.hold_stale(conn, rid, stage="consumer", attempt_id=attempt, operator="jerry")
    assert _report_row(db, rid)[0] == "needs_review"


def test_the_command_line_refuses_without_changing_anything(tasks, report, db, monkeypatch, capsys):
    import importlib.util
    spec = importlib.util.spec_from_file_location(
        "held_sends", Path(__file__).resolve().parents[3] / "scripts" / "ops" / "held_sends.py")
    cli = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(cli)
    rid, attempt, _fake = _held_text(tasks, monkeypatch, report, db)
    monkeypatch.setenv("DATABASE_URL", db)
    assert cli.main(["list", "--stage", "consumer"]) == 0
    assert PHONE not in capsys.readouterr().out
    assert cli.main(["resolve", rid, "--stage", "consumer", "--attempt", attempt, "--sent",
                     "--evidence", "x", "--operator", "jerry"]) == 1
    assert _report_row(db, rid)[0] == "needs_review"


def test_no_code_clears_delivery_evidence():
    src = (Path(__file__).resolve().parents[1] / "src" / "worker" / "consumer_delivery.py").read_text()
    tasks_src = (Path(__file__).resolve().parents[1] / "src" / "worker" / "tasks.py").read_text()
    for column in ("consumer_sms_sent_at", "consumer_email_sent_at", "agent_sms_sent_at"):
        for text in (src, tasks_src):
            assert f"{column} = NULL" not in " ".join(text.split()), f"something clears {column}"


def _account(db, rid):
    return str(_q(db, "SELECT u.account_id FROM consumer_reports cr JOIN users u ON u.id = cr.agent_id "
                      "WHERE cr.id = %s", rid)[0][0])

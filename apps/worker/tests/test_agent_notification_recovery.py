"""The agent's new-lead text is its own stage, recovered on its own (LR-021, D-379).

Design: docs/plans/launch-readiness-2026-11-06/LR-020-021_DELIVERY_STATE.md §3.6
(revision 3, Codex PASS on #280). Real task, migrated Postgres, Twilio faked at
its client.

On main (after LR-020): the agent text was sent inline after the homeowner's,
with no record of its own. A refusal was logged and forgotten; a worker that
died between the two stages lost it for good; and a later run of a delivered
report returned before reaching it.
"""
import threading
import uuid

import pytest

from test_consumer_failures_are_recorded import (  # noqa: F401  (fixtures)
    PHONE, WorkerDied, _credits, _run, _sent, _twilio, db, report, tasks,
)

psycopg = pytest.importorskip("psycopg")
AGENT = "2135550100"


def _q(db, sql, *params):
    with psycopg.connect(db) as conn:
        return conn.execute(sql, params).fetchall()


def _agent(db, rid):
    return _q(db, "SELECT agent_notify_status, agent_sms_sent_at, agent_sms_sid, agent_notify_attempt_id, "
                  "agent_notify_error, status FROM consumer_reports WHERE id = %s", rid)[0]


def _to(fake, digits):
    return [c for c in fake.calls if c.endswith(digits)]


def _bodies(db, rid):
    return [r[0] for r in _q(db, "SELECT message FROM sms_logs WHERE consumer_report_id = %s "
                                 "AND recipient_type = 'agent' ORDER BY created_at", rid)]


def _script(**by_recipient):
    """Twilio answers per recipient, in order; the last answer repeats."""
    seen = {}

    def behave(n, to):
        key = "agent" if to.endswith(AGENT) else "lead"
        answers = by_recipient.get(key) or [_sent]
        i = seen.get(key, 0)
        seen[key] = i + 1
        return answers[min(i, len(answers) - 1)](n, to)
    return behave


def _refuse(code=21211, status=400):
    def answer(n, to):
        from twilio.base.exceptions import TwilioRestException
        raise TwilioRestException(status, "uri", msg="refused", code=code)
    return answer


def _timeout(n, to):
    raise TimeoutError("lost")


@pytest.fixture
def retries(tasks, monkeypatch):
    """Capture the agent stage's own retry instead of queueing it."""
    queued = []
    monkeypatch.setattr(tasks, "_schedule_agent_retry", lambda rid, attempt=0: queued.append(str(rid)), raising=False)
    return queued


# ── the stage runs once, and resumes only itself ───────────────────────────

def test_a_delivered_lead_tells_the_agent_once_and_spends_no_credit(tasks, report, db, monkeypatch, retries):
    fake = _twilio(monkeypatch, _script())
    rid = report("sms")
    result = _run(tasks, rid)
    assert result["agent"] == "sent"
    status, sent_at, sid, attempt, _err, consumer_status = _agent(db, rid)
    assert status == "sent" and sent_at is not None and sid and consumer_status == "sent"
    assert len(_to(fake, AGENT)) == 1 and len(_to(fake, PHONE)) == 1
    assert _credits(db, rid) == 9, "only the homeowner's text spends a credit"
    # Both done: a later run sends neither.
    _run(tasks, rid)
    assert len(fake.calls) == 2


def test_a_refused_agent_text_is_resumed_alone_on_the_next_run(tasks, report, db, monkeypatch, retries):
    fake = _twilio(monkeypatch, _script(agent=[_refuse(), _sent]))
    rid = report("sms")
    _run(tasks, rid)
    assert _agent(db, rid)[0] == "failed" and retries == [], "a permanent refusal is not auto-retried"
    _run(tasks, rid)
    assert _agent(db, rid)[0] == "sent"
    assert len(_to(fake, PHONE)) == 1, "the homeowner's report was sent again to recover the agent text"
    assert len(_to(fake, AGENT)) == 2
    assert _credits(db, rid) == 9


def test_a_worker_that_dies_between_the_stages_sends_only_the_agent_text_after(tasks, report, db, monkeypatch, retries):
    fake = _twilio(monkeypatch, _script())
    real = tasks._notify_agent
    monkeypatch.setattr(tasks, "_notify_agent", lambda rid: (_ for _ in ()).throw(WorkerDied()))
    rid = report("sms")
    _run(tasks, rid)
    assert _agent(db, rid)[0] is None and len(fake.calls) == 1
    monkeypatch.setattr(tasks, "_notify_agent", real)
    result = _run(tasks, rid)                 # acks_late hands the task back
    assert result["agent"] == "sent"
    assert len(_to(fake, PHONE)) == 1 and len(_to(fake, AGENT)) == 1


def test_concurrent_recoveries_send_one_agent_text(tasks, report, db, monkeypatch, retries):
    fake = _twilio(monkeypatch, _script(agent=[_refuse(), _sent]))
    rid = report("sms")
    _run(tasks, rid)                          # delivered; agent text refused
    real_claim = tasks.consumer_delivery.claim_agent_notification
    barrier = threading.Barrier(2, timeout=30)

    def together(*a, **k):
        barrier.wait()
        return real_claim(*a, **k)
    monkeypatch.setattr(tasks.consumer_delivery, "claim_agent_notification", together)
    out = []
    threads = [threading.Thread(target=lambda: out.append(tasks._notify_agent(rid))) for _ in range(2)]
    [t.start() for t in threads]
    [t.join(60) for t in threads]
    assert sorted(r["agent"] for r in out) == ["not claimed", "sent"], out
    assert len(_to(fake, AGENT)) == 2, "one refused, then exactly one more"


# ── refusal, timeout, no phone ─────────────────────────────────────────────

def test_a_rate_limited_agent_text_is_retried_by_its_own_task(tasks, report, db, monkeypatch, retries):
    fake = _twilio(monkeypatch, _script(agent=[_refuse(code=20429, status=429), _sent]))
    rid = report("sms")
    _run(tasks, rid)
    assert _agent(db, rid)[0] == "failed" and retries == [rid], "a 429 must queue the agent's own retry"
    result = tasks.notify_consumer_report_agent.apply(args=[rid]).get()
    assert result["agent"] == "sent" and len(_to(fake, PHONE)) == 1


def test_the_agent_retry_task_has_its_own_budget(tasks, report, db, monkeypatch, retries):
    fake = _twilio(monkeypatch, _script(agent=[_refuse(code=20429, status=429)]))
    rid = report("sms")
    _run(tasks, rid)
    calls_before = len(_to(fake, AGENT))
    tasks.notify_consumer_report_agent.apply(args=[rid]).get(propagate=False)
    assert len(_to(fake, AGENT)) - calls_before == tasks.notify_consumer_report_agent.max_retries + 1
    assert _agent(db, rid)[0] == "failed" and len(_to(fake, PHONE)) == 1


def test_an_agent_text_with_an_unknown_outcome_is_held_and_never_resent(tasks, report, db, monkeypatch, retries, caplog):
    fake = _twilio(monkeypatch, _script(agent=[_timeout, _sent]))
    rid = report("sms")
    _run(tasks, rid)
    status, sent_at, _sid, attempt, err, consumer_status = _agent(db, rid)
    assert status == "needs_review" and sent_at is None and attempt is not None
    assert consumer_status == "sent", "the agent stage changed the homeowner's status"
    assert any("AGENT_NOTIFY_NEEDS_REVIEW" in r.getMessage() and r.levelname == "CRITICAL" for r in caplog.records)
    _run(tasks, rid)
    assert len(_to(fake, AGENT)) == 1 and retries == []


def test_no_agent_phone_is_skipped_once(tasks, report, db, monkeypatch, retries):
    fake = _twilio(monkeypatch, _script())
    rid = report("sms")
    with psycopg.connect(db, autocommit=True) as conn:
        conn.execute("UPDATE users SET phone = NULL WHERE id = (SELECT agent_id FROM consumer_reports WHERE id = %s)",
                     (rid,))
    _run(tasks, rid)
    _run(tasks, rid)
    status, *_x, err, _c = _agent(db, rid)
    assert status == "skipped" and "no phone" in err
    assert _to(fake, AGENT) == [] and retries == []


# ── the destination ────────────────────────────────────────────────────────

def _set_agent_phone(db, rid, phone):
    with psycopg.connect(db, autocommit=True) as conn:
        conn.execute("UPDATE users SET phone = %s WHERE id = (SELECT agent_id FROM consumer_reports WHERE id = %s)",
                     (phone, rid))


def test_a_new_attempt_goes_to_the_agents_current_phone(tasks, report, db, monkeypatch, retries):
    fake = _twilio(monkeypatch, _script(agent=[_refuse(), _sent]))
    rid = report("sms")
    _run(tasks, rid)
    _set_agent_phone(db, rid, "3105550111")
    _run(tasks, rid)
    assert _to(fake, "3105550111") and _agent(db, rid)[0] == "sent"
    tos = [r[0] for r in _q(db, "SELECT to_phone FROM sms_logs WHERE consumer_report_id = %s "
                                "AND recipient_type = 'agent' ORDER BY created_at", rid)]
    assert tos == ["2135550100", "3105550111"], "each attempt journals the destination it used"


def test_an_unknown_attempt_is_not_retargeted_when_the_phone_changes(tasks, report, db, monkeypatch, retries):
    fake = _twilio(monkeypatch, _script(agent=[_timeout, _sent]))
    rid = report("sms")
    _run(tasks, rid)
    _set_agent_phone(db, rid, "3105550111")
    _run(tasks, rid)
    assert _to(fake, "3105550111") == [] and len(_to(fake, AGENT)) == 1


# ── the name ───────────────────────────────────────────────────────────────

def test_the_agent_text_names_the_requester_never_the_owner(tasks, report, db, monkeypatch, retries):
    _twilio(monkeypatch, _script())
    rid = report("sms")
    with psycopg.connect(db, autocommit=True) as conn:
        conn.execute("UPDATE consumer_reports SET property_data = property_data || "
                     "'{\"owner_name\": \"Gerardo Owner\"}'::jsonb WHERE id = %s", (rid,))
    _run(tasks, rid)
    [body] = _bodies(db, rid)
    assert "Dana Rivera is interested in" in body and "Gerardo" not in body


def test_an_unnamed_requester_gets_the_generic_text_not_the_owner(tasks, report, db, monkeypatch, retries):
    _twilio(monkeypatch, _script())
    rid = report("sms")
    with psycopg.connect(db, autocommit=True) as conn:
        conn.execute("UPDATE consumer_reports SET property_data = (property_data - 'requester_name') || "
                     "'{\"owner_name\": \"Gerardo Owner\"}'::jsonb WHERE id = %s", (rid,))
    _run(tasks, rid)
    [body] = _bodies(db, rid)
    assert "Someone is interested in" in body and "Gerardo" not in body


def test_the_journal_holds_the_exact_agent_text_before_the_call(tasks, report, db, monkeypatch, retries):
    seen = {}

    def check(n, to):
        if to.endswith(AGENT):
            seen["rows"] = _q(db, "SELECT status, message, message_body FROM sms_logs "
                                  "WHERE consumer_report_id = %s AND recipient_type = 'agent'", rid)
        return _sent(n, to)
    _twilio(monkeypatch, check)
    sent_bodies = []
    from worker.sms import send as sms_send
    real = sms_send.send_sms

    def spy(to, body):
        if to.endswith(AGENT) or "".join(filter(str.isdigit, to)).endswith(AGENT):
            sent_bodies.append(body)
        return real(to, body)
    monkeypatch.setattr(sms_send, "send_sms", spy)
    rid = report("sms")
    _run(tasks, rid)
    [(status, message, message_body)] = seen["rows"]
    assert status == "pending" and message == message_body == sent_bodies[0]


# ── stale claims and the recovery window ───────────────────────────────────

def test_a_live_agent_claim_is_left_alone_and_a_stale_one_is_held(tasks, report, db, monkeypatch, retries):
    fake = _twilio(monkeypatch, _script())
    rid = report("sms")
    with psycopg.connect(db, autocommit=True) as conn:
        conn.execute("UPDATE consumer_reports SET consumer_sms_sent_at = NOW(), status = 'sent', "
                     "agent_notify_status = 'sending', agent_notify_attempt_id = %s, "
                     "agent_notify_claimed_at = NOW() WHERE id = %s", (str(uuid.uuid4()), rid))
    assert tasks._notify_agent(rid)["agent"] == "another run is notifying the agent"
    with psycopg.connect(db, autocommit=True) as conn:
        conn.execute("UPDATE consumer_reports SET agent_notify_claimed_at = NOW() - interval '1 hour' "
                     "WHERE id = %s", (rid,))
    assert tasks._notify_agent(rid)["agent"] == "needs_review"
    assert _agent(db, rid)[0] == "needs_review" and fake.calls == []


def test_an_old_lead_is_not_recovered_automatically(tasks, report, db, monkeypatch, retries):
    """Historical replay needs a reviewed list (ticket rollout), not a re-run."""
    fake = _twilio(monkeypatch, _script())
    rid = report("sms")
    with psycopg.connect(db, autocommit=True) as conn:
        conn.execute("UPDATE consumer_reports SET status = 'sent', "
                     "consumer_sms_sent_at = NOW() - make_interval(hours => %s) WHERE id = %s",
                     (tasks.consumer_delivery.AGENT_RECOVERY_HOURS + 1, rid))
    _run(tasks, rid)
    assert fake.calls == [] and _agent(db, rid)[0] is None


def test_an_operator_resolution_of_the_agent_stage_stops_any_resend(tasks, report, db, monkeypatch, retries):
    from worker import consumer_delivery as cd
    fake = _twilio(monkeypatch, _script(agent=[_timeout, _sent]))
    rid = report("sms")
    _run(tasks, rid)
    attempt = str(_agent(db, rid)[3])
    with psycopg.connect(db, autocommit=True) as conn:
        cd.resolve_sent(conn, rid, stage="agent", attempt_id=attempt, provider_id="SMagent",
                        evidence="Twilio log", operator="jerry")
    _run(tasks, rid)
    assert len(_to(fake, AGENT)) == 1 and _agent(db, rid)[0] == "sent"


def test_a_report_whose_agent_was_texted_before_lr021_is_not_texted_again(tasks, report, db, monkeypatch, retries):
    """Rows from before this change carry `agent_sms_sent_at` and no stage status."""
    fake = _twilio(monkeypatch, _script())
    rid = report("sms")
    with psycopg.connect(db, autocommit=True) as conn:
        conn.execute("UPDATE consumer_reports SET status = 'sent', consumer_sms_sent_at = NOW(), "
                     "agent_sms_sent_at = NOW(), agent_sms_sid = 'SMold' WHERE id = %s", (rid,))
    _run(tasks, rid)
    assert fake.calls == [] and _agent(db, rid)[0] is None

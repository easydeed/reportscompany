"""Who owns a consumer delivery, what it records, and how it settles (LR-020).

Design: docs/plans/launch-readiness-2026-11-06/LR-020-021_DELIVERY_STATE.md,
revision 3 (Codex PASS on #280). Section numbers below refer to it.

Every statement here is conditional, and each condition is one of four rules:

* EVIDENCE IS TERMINAL (Rule 1). `consumer_sms_sent_at` / `consumer_email_sent_at`
  record an irreversible act. Nothing clears them, and every automated status
  write requires them to be NULL. Writing evidence is the one write that does
  NOT check ownership: a send that happened must be recorded, whoever holds the
  claim, and the SMS credit is debited in the same transaction only when the
  evidence goes from NULL to set, which can happen once.

* GENERATION IS OWNED (§3.2). A run publishes its comps, values and PDF under
  its own `generation_id`, and only while nothing is claimed or delivered. Only
  the publisher of the current generation can claim its delivery, so the data
  behind the link is the data the message pointed to.

* ONE CLAIM (§3.1). One conditional UPDATE ... RETURNING takes the delivery
  and, in the same transaction, writes the journal row whose id is the attempt
  id. It is committed before any provider call.

* SETTLE ONLY YOUR OWN ATTEMPT. Refusals and holds are conditional on
  `delivery_attempt_id = <mine>`; the operator's resolutions on the exact
  attempt and its held state.

No function here calls a provider.
"""
from __future__ import annotations

import logging
import os
import uuid
from datetime import timedelta

logger = logging.getLogger(__name__)

SENDING = "sending"
NEEDS_REVIEW = "needs_review"

# Same window as the scheduled-email path (tasks.DUPLICATE_SEND_WINDOW_MINUTES):
# longer than task_time_limit (300 s), so a live attempt is never taken as
# stale; shorter than the broker's visibility_timeout (900 s), so the acks_late
# redelivery of a dead run finds the claim stale and holds it.
CLAIM_WINDOW_MINUTES = int(os.getenv("DUPLICATE_SEND_WINDOW_MINUTES", "10"))

# Resend keeps an Idempotency-Key for 24 hours. The one replay is made only
# well inside that, measured from just before the first call (§3.4).
EMAIL_KEY_LIFETIME = timedelta(hours=24)
EMAIL_REPLAY_MARGIN = timedelta(minutes=10)

_NO_EVIDENCE = "consumer_sms_sent_at IS NULL AND consumer_email_sent_at IS NULL"


def email_idempotency_key(report_id, attempt_id) -> str:
    return f"consumer-report:{report_id}:{attempt_id}"


def replay_deadline_ok(elapsed: timedelta) -> bool:
    """May the one email replay still be made, this long after the first call began?"""
    return elapsed < EMAIL_KEY_LIFETIME - EMAIL_REPLAY_MARGIN


# ── Task start ────────────────────────────────────────────────────────────────

def start_processing(cur, report_id) -> bool:
    """Mark a report as generating. Never over a claim, a hold or a delivery (R1)."""
    cur.execute(f"""
        UPDATE consumer_reports SET status = 'processing'
        WHERE id = %s::uuid
          AND status IN ('pending', 'processing', 'failed')
          AND delivery_attempt_id IS NULL
          AND {_NO_EVIDENCE}
        RETURNING id
    """, (str(report_id),))
    return cur.fetchone() is not None


def claim_is_stale(cur, report_id) -> bool:
    """Is the report's `sending` claim older than the window (or undated)?"""
    cur.execute("""
        SELECT delivery_claimed_at IS NULL
            OR delivery_claimed_at < NOW() - make_interval(mins => %s)
        FROM consumer_reports WHERE id = %s::uuid
    """, (CLAIM_WINDOW_MINUTES, str(report_id)))
    row = cur.fetchone()
    return bool(row and row[0])


def hold_stale_claim(cur, report_id, text: str):
    """Hold a `sending` claim nobody settled. Never a send. Returns the attempt id held, or None.

    Only a stale claim: one inside the window belongs to a run that is still
    sending, and holding it was R2's false alert.
    """
    cur.execute(f"""
        UPDATE consumer_reports SET status = %s, error_message = %s
        WHERE id = %s::uuid
          AND status = %s
          AND (delivery_claimed_at IS NULL
               OR delivery_claimed_at < NOW() - make_interval(mins => %s))
          AND {_NO_EVIDENCE}
        RETURNING delivery_attempt_id
    """, (NEEDS_REVIEW, text, str(report_id), SENDING, CLAIM_WINDOW_MINUTES))
    row = cur.fetchone()
    if row is None:
        return None
    logger.critical("CONSUMER_DELIVERY_NEEDS_REVIEW report=%s attempt=%s: %s",
                    report_id, row[0], text)
    return row[0] or "(no attempt id)"


# ── Generation (§3.2) ─────────────────────────────────────────────────────────

def pdf_render_id(report_id, generation_id) -> str:
    """The renderer's run id, which names its local output file: one per generation."""
    return f"consumer-{report_id}-{generation_id}"


def pdf_object_key(account_id, report_id, generation_id) -> str:
    """One object per generation, so no upload can replace a delivered PDF."""
    return f"consumer-reports/{account_id}/{report_id}/{generation_id}.pdf"


def publish_generation(cur, report_id, generation_id, *, property_data_json, comparables_json,
                       value_estimate_json, market_stats_json, pdf_url, pdf_key=None) -> bool:
    """Make this run's generation the one the report shows, if nothing is claimed or sent."""
    cur.execute(f"""
        UPDATE consumer_reports
        SET property_data = %s::jsonb,
            comparables = %s::jsonb,
            value_estimate = %s::jsonb,
            market_stats = %s::jsonb,
            pdf_url = %s,
            pdf_generated_at = CASE WHEN %s::text IS NULL THEN NULL ELSE NOW() END,
            pdf_object_key = %s,
            pdf_status = CASE WHEN %s::text IS NULL THEN NULL ELSE 'ready' END,
            pdf_error = NULL,
            generation_id = %s::uuid
        WHERE id = %s::uuid
          AND status = 'processing'
          AND delivery_attempt_id IS NULL
          AND {_NO_EVIDENCE}
        RETURNING id
    """, (property_data_json, comparables_json, value_estimate_json, market_stats_json,
          pdf_url, pdf_url, pdf_key if pdf_url else None, pdf_url, str(generation_id), str(report_id)))
    return cur.fetchone() is not None


# ── The claim (§3.1, §3.5) ────────────────────────────────────────────────────

_CLAIM = f"""
    UPDATE consumer_reports
    SET status = %s, delivery_claimed_at = NOW(), delivery_attempt_id = %s::uuid
    WHERE id = %s::uuid
      AND status = 'processing'
      AND generation_id = %s::uuid
      AND delivery_attempt_id IS NULL
      AND {_NO_EVIDENCE}
    RETURNING id
"""


def claim_sms(conn, report_id, generation_id, *, account_id, to_phone, from_phone, body):
    """Claim the delivery as a text, journalling the exact message first. Returns the attempt id."""
    attempt_id = uuid.uuid4()
    with conn.transaction():
        cur = conn.cursor()
        cur.execute(_CLAIM, (SENDING, str(attempt_id), str(report_id), str(generation_id)))
        if cur.fetchone() is None:
            return None
        # 0035: to_phone, from_phone and message are NOT NULL; 0039 added
        # message_body beside `message`. Both hold the body that is sent.
        cur.execute("""
            INSERT INTO sms_logs (id, account_id, consumer_report_id, to_phone, from_phone,
                                  message, message_body, recipient_type, status, direction)
            VALUES (%s::uuid, %s::uuid, %s::uuid, %s, %s, %s, %s, 'consumer', 'pending', 'outbound')
        """, (str(attempt_id), str(account_id), str(report_id), to_phone, from_phone, body, body))
    return attempt_id


def claim_email(conn, report_id, generation_id, *, account_id, to_email, subject):
    """Claim the delivery as an email. Returns (attempt id, idempotency key) or None."""
    attempt_id = uuid.uuid4()
    key = email_idempotency_key(report_id, attempt_id)
    with conn.transaction():
        cur = conn.cursor()
        cur.execute(_CLAIM, (SENDING, str(attempt_id), str(report_id), str(generation_id)))
        if cur.fetchone() is None:
            return None
        # email_log has row-level security on the account (0006/0025).
        cur.execute("SELECT set_config('app.current_account_id', %s, true)", (str(account_id),))
        cur.execute("""
            INSERT INTO email_log (id, account_id, report_id, provider, to_emails, subject,
                                   status, idempotency_key)
            VALUES (%s::uuid, %s::uuid, %s::uuid, 'resend', ARRAY[%s], %s, 'sending', %s)
        """, (str(attempt_id), str(account_id), str(report_id), to_email, subject, key))
    return attempt_id, key


def refresh_ownership(cur, report_id, attempt_id) -> bool:
    """Do I still own this attempt? If so, refresh the claim so nobody takes it as stale."""
    cur.execute(f"""
        UPDATE consumer_reports SET delivery_claimed_at = NOW()
        WHERE id = %s::uuid AND status = %s AND delivery_attempt_id = %s::uuid
          AND {_NO_EVIDENCE}
        RETURNING id
    """, (str(report_id), SENDING, str(attempt_id)))
    return cur.fetchone() is not None


# ── Outcomes ──────────────────────────────────────────────────────────────────
#
# The decisive write (evidence + debit, the release, or the hold) is committed
# on its own. The journal update follows it and is best-effort: a log row that
# cannot be updated must not undo the record of a text that went out (LR-019's
# rule, kept). The journal INSERT at the claim is different: it is part of the
# claim, so a journal that cannot be written stops the send before it starts.

def _journal(conn, sql, params, *, account_id=None):
    try:
        with conn.transaction():
            cur = conn.cursor()
            if account_id is not None:
                cur.execute("SELECT set_config('app.current_account_id', %s, true)", (str(account_id),))
            cur.execute(sql, params)
    except Exception as e:
        logger.error("CONSUMER DELIVERY: journal update failed (the delivery record stands): %s",
                     type(e).__name__)


def _warn_if_resolved_not_sent(cur, table, attempt_id, report_id):
    cur.execute(f"SELECT resolution FROM {table} WHERE id = %s::uuid", (str(attempt_id),))
    row = cur.fetchone()
    if row and row[0] == "not_sent":
        logger.critical(
            "CONSUMER_DELIVERY_CONTRADICTION report=%s attempt=%s: the provider accepted a "
            "message an operator resolved as not sent; the delivery is recorded as sent",
            report_id, attempt_id)


def record_sms_sent(conn, report_id, attempt_id, *, account_id, sid) -> bool:
    """The provider accepted the text. Evidence, debit and journal in one transaction.

    Returns True when this call recorded the evidence (and so debited one credit).
    """
    with conn.transaction():
        cur = conn.cursor()
        cur.execute("""
            UPDATE consumer_reports
            SET status = 'sent', consumer_sms_sent_at = NOW(), consumer_sms_sid = %s,
                error_message = NULL
            WHERE id = %s::uuid AND consumer_sms_sent_at IS NULL
            RETURNING id
        """, (sid, str(report_id)))
        recorded = cur.fetchone() is not None
        if recorded:
            # Consumer SMS is the only delivery that spends a credit.
            cur.execute("""
                UPDATE accounts SET sms_credits = GREATEST(sms_credits - 1, 0)
                WHERE id = %s::uuid
            """, (str(account_id),))
    _journal(conn, """
        UPDATE sms_logs SET status = 'sent', twilio_sid = %s, error_message = NULL
        WHERE id = %s::uuid
    """, (sid, str(attempt_id)))
    try:
        _warn_if_resolved_not_sent(conn.cursor(), "sms_logs", attempt_id, report_id)
    except Exception:
        pass
    return recorded


def record_email_sent(conn, report_id, attempt_id, *, account_id, response_code, provider_message_id) -> bool:
    """The provider accepted the email. Evidence and journal in one transaction. No credit."""
    with conn.transaction():
        cur = conn.cursor()
        cur.execute("""
            UPDATE consumer_reports
            SET status = 'sent', consumer_email_sent_at = NOW(), error_message = NULL
            WHERE id = %s::uuid AND consumer_email_sent_at IS NULL
            RETURNING id
        """, (str(report_id),))
        recorded = cur.fetchone() is not None
    _journal(conn, """
        UPDATE email_log SET status = 'sent', response_code = %s, provider_message_id = %s,
                             error = NULL
        WHERE id = %s::uuid
    """, (response_code, provider_message_id, str(attempt_id)), account_id=account_id)
    try:
        cur = conn.cursor()
        cur.execute("SELECT set_config('app.current_account_id', %s, false)", (str(account_id),))
        _warn_if_resolved_not_sent(cur, "email_log", attempt_id, report_id)
    except Exception:
        pass
    return recorded


def release_refused(conn, report_id, attempt_id, *, channel, text, account_id=None,
                    response_code=None) -> bool:
    """The provider refused, and so sent nothing: `failed`, and the claim is released.

    Releasing it lets a retry publish and claim a NEW attempt (new journal row,
    new key). The refused attempt stays in the journal.
    """
    with conn.transaction():
        cur = conn.cursor()
        cur.execute(f"""
            UPDATE consumer_reports
            SET status = 'failed', error_message = %s,
                delivery_attempt_id = NULL, delivery_claimed_at = NULL
            WHERE id = %s::uuid AND status = %s AND delivery_attempt_id = %s::uuid
              AND {_NO_EVIDENCE}
            RETURNING id
        """, (text, str(report_id), SENDING, str(attempt_id)))
        owned = cur.fetchone() is not None
    if channel == "sms":
        _journal(conn, "UPDATE sms_logs SET status = 'failed', error_message = %s WHERE id = %s::uuid",
                 (text, str(attempt_id)))
    else:
        _journal(conn, "UPDATE email_log SET status = 'failed', response_code = %s, error = %s "
                       "WHERE id = %s::uuid",
                 (response_code, text, str(attempt_id)), account_id=account_id)
    return owned


def hold_attempt(conn, report_id, attempt_id, *, channel, text, account_id=None) -> bool:
    """The outcome is unknown: hold it for an operator. The claim stays, frozen.

    The journal row is left unsettled (`pending` / `sending`) with the note.
    """
    with conn.transaction():
        cur = conn.cursor()
        cur.execute(f"""
            UPDATE consumer_reports SET status = %s, error_message = %s
            WHERE id = %s::uuid AND status = %s AND delivery_attempt_id = %s::uuid
              AND {_NO_EVIDENCE}
            RETURNING id
        """, (NEEDS_REVIEW, text, str(report_id), SENDING, str(attempt_id)))
        owned = cur.fetchone() is not None
    if channel == "sms":
        _journal(conn, "UPDATE sms_logs SET error_message = %s WHERE id = %s::uuid",
                 (text, str(attempt_id)))
    else:
        _journal(conn, "UPDATE email_log SET error = %s WHERE id = %s::uuid",
                 (text, str(attempt_id)), account_id=account_id)
    if owned:
        logger.critical("CONSUMER_DELIVERY_NEEDS_REVIEW report=%s attempt=%s channel=%s: %s",
                        report_id, attempt_id, channel, text)
    return owned


def hold_on_exception(cur, report_id, attempt_id, text) -> bool:
    """The outer handler, for a run that owns a claim: hold it, never fail it."""
    cur.execute(f"""
        UPDATE consumer_reports SET status = %s, error_message = %s
        WHERE id = %s::uuid AND status = %s AND delivery_attempt_id = %s::uuid
          AND {_NO_EVIDENCE}
        RETURNING id
    """, (NEEDS_REVIEW, text, str(report_id), SENDING, str(attempt_id)))
    return cur.fetchone() is not None


def fail_on_exception(cur, report_id, generation_id, text) -> bool:
    """The outer handler, for a run that claimed nothing: `failed`, but never over
    another run's claim, a hold, a delivery, or a generation it did not publish."""
    cur.execute(f"""
        UPDATE consumer_reports SET status = 'failed', error_message = %s
        WHERE id = %s::uuid
          AND status IN ('pending', 'processing')
          AND delivery_attempt_id IS NULL
          AND (generation_id IS NULL OR generation_id = %s::uuid)
          AND {_NO_EVIDENCE}
        RETURNING id
    """, (text, str(report_id), str(generation_id) if generation_id else None))
    return cur.fetchone() is not None


# ── Held sends: the operator's workflow, both stages (§6) ─────────────────────
#
# scripts/ops/held_sends.py is the command line over these. Nothing here calls a
# provider or enqueues a send. Every move is conditional on the exact stage,
# attempt and state; evidence is only ever set where it is NULL.

class ResolutionRefused(ValueError):
    """The resolution did not apply: wrong attempt, wrong state, or missing evidence."""


STAGES = ("consumer", "agent")

_STAGE = {
    "consumer": {"status": "status", "attempt": "delivery_attempt_id",
                 "claimed": "delivery_claimed_at", "error": "error_message"},
    "agent": {"status": "agent_notify_status", "attempt": "agent_notify_attempt_id",
              "claimed": "agent_notify_claimed_at", "error": "agent_notify_error"},
}


def _mask(value):
    value = str(value or "")
    return ("…" + value[-4:]) if len(value) > 4 else "…"


def list_held(cur, *, stage=None, state="all", older_than_minutes=0):
    """Held and stale attempts, newest first. Destinations masked to four characters."""
    rows = []
    for st in ([stage] if stage else STAGES):
        c = _STAGE[st]
        conds = []
        if state in ("held", "all"):
            conds.append(f"cr.{c['status']} = '{NEEDS_REVIEW}'")
        if state in ("stale", "all"):
            conds.append(f"(cr.{c['status']} = '{SENDING}' AND (cr.{c['claimed']} IS NULL "
                         f"OR cr.{c['claimed']} < NOW() - make_interval(mins => {CLAIM_WINDOW_MINUTES})))")
        cur.execute(f"""
            SELECT cr.id, cr.{c['status']}, cr.{c['attempt']}, cr.{c['claimed']},
                   EXTRACT(EPOCH FROM NOW() - cr.{c['claimed']})::int,
                   cr.{c['error']},
                   s.to_phone, s.twilio_sid, e.to_emails, e.provider_message_id, e.idempotency_key
            FROM consumer_reports cr
            LEFT JOIN sms_logs s ON s.id = cr.{c['attempt']}
            LEFT JOIN email_log e ON e.id = cr.{c['attempt']}
            WHERE ({' OR '.join(conds)})
              AND (cr.{c['claimed']} IS NULL
                   OR cr.{c['claimed']} < NOW() - make_interval(mins => %s))
            ORDER BY cr.{c['claimed']} DESC NULLS LAST
        """, (int(older_than_minutes),))
        for (rid, status, attempt, claimed, age_s, error, phone, sid, emails, email_id, key) in cur.fetchall():
            channel = "sms" if phone is not None else ("email" if emails is not None else "unknown")
            rows.append({
                "report_id": str(rid), "stage": st, "channel": channel, "state": status,
                "attempt_id": str(attempt) if attempt else None,
                "claimed_at": claimed.isoformat() if claimed else None,
                "age_minutes": None if age_s is None else age_s // 60,
                "outcome": error,
                "destination": _mask(phone if phone is not None else (emails or [""])[0]),
                "provider_id": sid or email_id,
                "idempotency_key": key,
                "replayed": bool(error and "one replay with the same key" in error),
            })
    return rows


def hold_stale(conn, report_id, *, stage, attempt_id, operator):
    """Move a stale `sending` attempt to `needs_review`. Exact attempt, stale claim only."""
    c = _STAGE[stage]
    text = f"held by {operator}: the attempt's outcome was never recorded"
    with conn.transaction():
        cur = conn.cursor()
        cur.execute(f"""
            UPDATE consumer_reports SET {c['status']} = %s, {c['error']} = %s
            WHERE id = %s::uuid AND {c['status']} = %s AND {c['attempt']} = %s::uuid
              AND ({c['claimed']} IS NULL
                   OR {c['claimed']} < NOW() - make_interval(mins => %s))
            RETURNING id
        """, (NEEDS_REVIEW, text, str(report_id), SENDING, str(attempt_id), CLAIM_WINDOW_MINUTES))
        if cur.fetchone() is None:
            raise ResolutionRefused(
                f"{stage} attempt {attempt_id} on report {report_id} is not a stale 'sending' claim")
    logger.critical("%s report=%s attempt=%s: %s",
                    "CONSUMER_DELIVERY_NEEDS_REVIEW" if stage == "consumer" else "AGENT_NOTIFY_NEEDS_REVIEW",
                    report_id, attempt_id, text)


def _journal_attempt(cur, report_id, stage, attempt_id):
    """The attempt's own journal row: (channel, account_id), validated.

    The account comes from the row written at the claim, never from the
    agent's CURRENT account (Codex review of c57e505b): an agent moved to
    another account between the claim and the resolution must not move the
    debit or the email audit with them. The row must belong to this report and
    this stage, or nothing is resolved.
    """
    cur.execute("""
        SELECT 'sms', account_id, consumer_report_id, recipient_type
        FROM sms_logs WHERE id = %s::uuid
    """, (str(attempt_id),))
    row = cur.fetchone()
    if row is None and stage == "consumer":
        # email_log has row-level security on the account. Look under the
        # report's account; a row filed under another account is not found,
        # which refuses the resolution rather than guessing.
        cur.execute("""
            SELECT set_config('app.current_account_id', u.account_id::text, true)
            FROM consumer_reports cr JOIN users u ON u.id = cr.agent_id
            WHERE cr.id = %s::uuid
        """, (str(report_id),))
        cur.execute("""
            SELECT 'email', account_id, report_id, 'consumer'
            FROM email_log WHERE id = %s::uuid
        """, (str(attempt_id),))
        row = cur.fetchone()
    if row is None:
        raise ResolutionRefused(f"no journal row for attempt {attempt_id} on report {report_id}")
    channel, account_id, journal_report, recipient = row
    if str(journal_report) != str(report_id) or recipient != stage or account_id is None:
        raise ResolutionRefused(
            f"attempt {attempt_id} is not a {stage} attempt of report {report_id}")
    return channel, account_id


def _require(value, what):
    if not str(value or "").strip():
        raise ResolutionRefused(f"{what} is required")
    return str(value).strip()


def resolve_sent(conn, report_id, *, stage, attempt_id, provider_id, evidence, operator, sent_at=None):
    """The operator found the provider's record of this attempt: record it as sent.

    Requires the provider's own id (Twilio SID or Resend email id). Evidence is
    set only where it is NULL; a consumer text debits one credit, once, in the
    same transaction. The agent stage never touches consumer state or credits.
    """
    provider_id = _require(provider_id, "--provider-id (the Twilio SID or Resend email id)")
    evidence = _require(evidence, "--evidence")
    operator = _require(operator, "--operator")
    c = _STAGE[stage]
    with conn.transaction():
        cur = conn.cursor()
        channel, account_id = _journal_attempt(cur, report_id, stage, attempt_id)
        if stage == "consumer":
            column = "consumer_sms_sent_at" if channel == "sms" else "consumer_email_sent_at"
            sid_set = ", consumer_sms_sid = %s" if channel == "sms" else ""
            params = [sent_at] + ([provider_id] if channel == "sms" else [])
            cur.execute(f"""
                UPDATE consumer_reports
                SET status = 'sent', {column} = COALESCE(%s::timestamptz, NOW()){sid_set},
                    error_message = NULL
                WHERE id = %s::uuid AND status = %s AND delivery_attempt_id = %s::uuid
                  AND {column} IS NULL
                RETURNING id
            """, params + [str(report_id), NEEDS_REVIEW, str(attempt_id)])
            if cur.fetchone() is None:
                raise ResolutionRefused(
                    f"consumer attempt {attempt_id} on report {report_id} is not held, or is already recorded")
            if channel == "sms":
                cur.execute("UPDATE accounts SET sms_credits = GREATEST(sms_credits - 1, 0) "
                            "WHERE id = %s::uuid", (str(account_id),))
        else:
            cur.execute(f"""
                UPDATE consumer_reports
                SET {c['status']} = 'sent', agent_sms_sent_at = COALESCE(%s::timestamptz, NOW()),
                    agent_sms_sid = %s, {c['error']} = NULL
                WHERE id = %s::uuid AND {c['status']} = %s AND {c['attempt']} = %s::uuid
                  AND agent_sms_sent_at IS NULL
                RETURNING id
            """, (sent_at, provider_id, str(report_id), NEEDS_REVIEW, str(attempt_id)))
            if cur.fetchone() is None:
                raise ResolutionRefused(
                    f"agent attempt {attempt_id} on report {report_id} is not held, or is already recorded")
        _resolve_journal(cur, channel, attempt_id, account_id, "sent", provider_id, evidence, operator)


def resolve_not_sent(conn, report_id, *, stage, attempt_id, evidence, operator):
    """The operator has positive evidence the provider did not accept this attempt.

    The stage becomes `failed` and its claim is released. Nothing is sent or
    enqueued: a new send is a separate, explicit decision, and claims a NEW
    attempt. When the evidence is uncertain, do not call this; leave it held.
    """
    evidence = _require(evidence, "--evidence (positive proof the provider did not accept it)")
    operator = _require(operator, "--operator")
    c = _STAGE[stage]
    note = consumer_failure_note(f"resolved not sent by {operator}: {evidence}")
    with conn.transaction():
        cur = conn.cursor()
        channel, account_id = _journal_attempt(cur, report_id, stage, attempt_id)
        guard = _NO_EVIDENCE if stage == "consumer" else "agent_sms_sent_at IS NULL"
        cur.execute(f"""
            UPDATE consumer_reports
            SET {c['status']} = 'failed', {c['error']} = %s,
                {c['attempt']} = NULL, {c['claimed']} = NULL
            WHERE id = %s::uuid AND {c['status']} = %s AND {c['attempt']} = %s::uuid
              AND {guard}
            RETURNING id
        """, (note, str(report_id), NEEDS_REVIEW, str(attempt_id)))
        if cur.fetchone() is None:
            raise ResolutionRefused(
                f"{stage} attempt {attempt_id} on report {report_id} is not held, or is already recorded")
        _resolve_journal(cur, channel, attempt_id, account_id, "not_sent", None, evidence, operator)


def consumer_failure_note(text, limit=500):
    return str(text).strip()[:limit]


def _resolve_journal(cur, channel, attempt_id, account_id, resolution, provider_id, evidence, operator):
    if channel == "sms":
        cur.execute("""
            UPDATE sms_logs
            SET status = %s, twilio_sid = COALESCE(%s, twilio_sid),
                resolution = %s, resolved_at = NOW(), resolved_by = %s, resolution_evidence = %s
            WHERE id = %s::uuid
        """, ("sent" if resolution == "sent" else "failed", provider_id,
              resolution, operator, evidence, str(attempt_id)))
    else:
        cur.execute("SELECT set_config('app.current_account_id', %s, true)", (str(account_id),))
        cur.execute("""
            UPDATE email_log
            SET status = %s, provider_message_id = COALESCE(%s, provider_message_id),
                resolution = %s, resolved_at = NOW(), resolved_by = %s, resolution_evidence = %s
            WHERE id = %s::uuid
        """, ("sent" if resolution == "sent" else "failed", provider_id,
              resolution, operator, evidence, str(attempt_id)))


# ── A delivered report's missing PDF (LR-022) ────────────────────────────────
#
# The API queues (pdf_status 'queued'); this claims ('generating'), and only
# the claim's owner records 'ready' or 'failed'. A PDF that exists is never
# replaced: every statement requires pdf_url and pdf_object_key to be NULL.

PDF_CLAIM_WINDOW_MINUTES = CLAIM_WINDOW_MINUTES

def claim_pdf_generation(cur, report_id):
    """Claim the generation of a delivered report's missing PDF. Returns the row, or None."""
    claim_id = uuid.uuid4()
    cur.execute("""
        UPDATE consumer_reports cr
        SET pdf_status = 'generating', pdf_claimed_at = NOW(), pdf_claim_id = %(claim)s::uuid,
            pdf_error = NULL
        FROM users u
        WHERE cr.id = %(rid)s::uuid AND u.id = cr.agent_id
          AND cr.pdf_url IS NULL AND cr.pdf_object_key IS NULL
          AND (cr.consumer_sms_sent_at IS NOT NULL OR cr.consumer_email_sent_at IS NOT NULL
               OR cr.status = 'sent')
          AND (cr.pdf_status IS NULL OR cr.pdf_status IN ('queued', 'failed')
               OR (cr.pdf_status = 'generating'
                   AND cr.pdf_claimed_at < NOW() - make_interval(mins => %(window)s)))
        RETURNING cr.id, u.account_id, cr.agent_id, cr.property_data, cr.comparables,
                  cr.property_address, cr.property_city, cr.property_state, cr.property_zip,
                  u.first_name, u.last_name, u.phone, cr.pdf_claim_id
    """, {"claim": str(claim_id), "rid": str(report_id), "window": PDF_CLAIM_WINDOW_MINUTES})
    return cur.fetchone()


def finish_pdf_generation(cur, report_id, claim_id, *, pdf_url, pdf_key) -> bool:
    """Record the generated PDF, only for the claim's owner and only if none exists."""
    cur.execute("""
        UPDATE consumer_reports
        SET pdf_url = %s, pdf_object_key = %s, pdf_generated_at = NOW(),
            pdf_status = 'ready', pdf_error = NULL
        WHERE id = %s::uuid AND pdf_claim_id = %s::uuid AND pdf_status = 'generating'
          AND pdf_url IS NULL AND pdf_object_key IS NULL
        RETURNING id
    """, (pdf_url, pdf_key, str(report_id), str(claim_id)))
    return cur.fetchone() is not None


def fail_pdf_generation(cur, report_id, claim_id, text) -> bool:
    """Record why the generation failed, only for the claim's owner."""
    cur.execute("""
        UPDATE consumer_reports SET pdf_status = 'failed', pdf_error = %s
        WHERE id = %s::uuid AND pdf_claim_id = %s::uuid AND pdf_status = 'generating'
        RETURNING id
    """, (text, str(report_id), str(claim_id)))
    return cur.fetchone() is not None

"""
A committed scheduled send survives a broker failure (LR-023, D-381).

Design: docs/plans/launch-readiness-2026-11-06/LR-023_DURABLE_DISPATCH.md, rev 3
(Codex design PASS on #286). Section numbers below refer to it.

One `schedule_runs` row is one occurrence. Only rows the new ticker inserts are
`recovery_tracked`; every other row keeps today's path exactly (§2). For a
tracked row:

  publish   the ticker, or the sweep, counts the attempt and commits, then
            publishes; the broker's acknowledgement is recorded after (§3);
  lease     the worker's FIRST step, before any report_generations write: one
            conditional UPDATE takes an owner token, so exactly one worker
            owns the run; every later write is conditioned on that token (§4);
  claim     committed after the render and immediately before the first POST,
            re-checking the 6-hour horizon and eligibility. Never cleared. A
            claim with no recorded outcome is needs_review, never resent (§5);
  sweep     terminal checks first, then republish within the bounds: 6
            publishes in all, 2/4/8/16-minute backoff, 6 hours (§6).

Every time is the database's clock, and the horizon is measured from the
occurrence's created_at, never from a retry.
"""
from __future__ import annotations

import json
import logging
import os
import uuid
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Callable, Iterable, Optional

import psycopg

logger = logging.getLogger(__name__)

# ── Bounds (Jerry approved the 6-hour horizon, 2026-11-11) ───────────────────
HORIZON = timedelta(hours=6)
#: A lease not refreshed for this long belongs to a dead owner. Clears Celery's
#: task_time_limit (300 s), so a live run is never mistaken for a dead one.
STALE_LEASE = timedelta(minutes=int(os.getenv("STALE_STARTED_MINUTES", "6")))
#: A first publish whose acknowledgement was never recorded.
UNACKED = timedelta(minutes=2)
#: An acknowledged message that never started: the broker lost it. Wide enough
#: to let a burst drain (see STALE_QUEUED_MINUTES in schedules_tick.py).
LOST = timedelta(minutes=int(os.getenv("STALE_QUEUED_MINUTES", "30")))
#: Publishes in all, the first included: the 6th is allowed, the 7th refused.
MAX_PUBLISHES = 6
#: Minutes to wait after publish n before publish n+1, capped at 16.
BACKOFF_MINUTES = (2, 4, 8, 16)

OPEN = ("queued", "processing")

# Terminal statuses this module writes (free text since 0006; 0068's COMMENT).
COMPLETED = "completed"
FAILED = "failed"
CANCELLED = "cancelled"
EXPIRED = "expired"
BLOCKED = "blocked_unverified"
NEEDS_REVIEW = "needs_review"

# What the worker gets back when it does not take the lease.
DUPLICATE_MESSAGE = "duplicate_message"

# The send claim's three answers.
CLAIMED = "claimed"
REFUSED = "refused"
CLAIM_ERROR = "error"

MSG_EXPIRED = "not sent: it could not start within 6 hours of its scheduled time"
MSG_PAUSED = "not sent: the schedule was paused before it ran"
MSG_DEACTIVATED = "not sent: the account was deactivated before it ran"
MSG_UNVERIFIED = ("not sent: no user on this account has confirmed their email address "
                  "(users.email_verified is false for all of them)")
MSG_CLAIMED_NO_OUTCOME = ("outcome unknown: the run stopped after its send was claimed, "
                          "so the email may have gone out; not resent")

# Same meaning as schedules_tick.account_can_send and the API's
# sender_verification: an active user with a confirmed email.
_CAN_SEND = ("EXISTS (SELECT 1 FROM users u WHERE u.account_id = a.id "
             "AND COALESCE(u.is_active, TRUE) AND COALESCE(u.email_verified, FALSE))")


class Superseded(Exception):
    """This worker no longer owns the run: a token-conditioned write matched nothing."""


@dataclass(frozen=True)
class RunState:
    id: str
    run_id: str
    status: str
    created_at: datetime
    lease_at: Optional[datetime]
    owner_token: Optional[str]
    send_claimed_at: Optional[datetime]
    dispatched_at: Optional[datetime]
    dispatch_attempts: int
    last_dispatch_at: Optional[datetime]
    schedule_id: str
    schedule_active: bool
    account_id: str
    account_active: bool
    can_send: bool
    recipients: Optional[list]
    report_type: Optional[str]
    params: Optional[dict]
    now: datetime


_STATE_SELECT = f"""
    SELECT sr.id::text, sr.report_run_id::text, sr.status, sr.created_at, sr.lease_at,
           sr.owner_token::text, sr.send_claimed_at, sr.dispatched_at, sr.dispatch_attempts,
           sr.last_dispatch_at, s.id::text, COALESCE(s.active, FALSE), a.id::text,
           COALESCE(a.is_active, TRUE), {_CAN_SEND}, s.recipients,
           rg.report_type, rg.input_params, now()
    FROM schedule_runs sr
    JOIN schedules s ON s.id = sr.schedule_id
    JOIN accounts a ON a.id = s.account_id
    LEFT JOIN report_generations rg ON rg.id = sr.report_run_id
"""


def _state(row) -> RunState:
    params = row[17]
    if isinstance(params, str):
        params = json.loads(params)
    return RunState(*row[:17], params, row[18])


# ── Judging an open row (§4 table; shared by the worker and the sweep) ──────

def lease_is_live(st: RunState) -> bool:
    return (st.status == "processing" and st.lease_at is not None
            and st.lease_at >= st.now - STALE_LEASE)


def ineligible(st: RunState) -> Optional[tuple[str, str]]:
    """Why this occurrence may no longer start or send, judged now."""
    if st.created_at <= st.now - HORIZON:
        return EXPIRED, MSG_EXPIRED
    if not st.schedule_active:
        return CANCELLED, MSG_PAUSED
    if not st.account_active:
        return CANCELLED, MSG_DEACTIVATED
    if not st.can_send:
        return BLOCKED, MSG_UNVERIFIED
    return None


def terminal_outcome(st: RunState) -> Optional[tuple[str, str]]:
    """
    The one truthful terminal outcome due for an open row, or None.

    None for a terminal row, a row under a live lease, and a row that may still
    run. A stale row with a send claim is needs_review before anything else:
    the claim is the authority, whatever else has changed since.
    """
    if st.status not in OPEN or lease_is_live(st):
        return None
    if st.send_claimed_at is not None:
        return NEEDS_REVIEW, MSG_CLAIMED_NO_OUTCOME
    return ineligible(st)


def _set_account(cur, account_id: str) -> None:
    cur.execute("SELECT set_config('app.current_account_id', %s, true)", (str(account_id),))


def write_terminal(cur, st: RunState, status: str, error: str) -> bool:
    """
    Settle an open row, under the caller's row lock. Never touches a row that
    is already terminal. A run that never produced its report also closes its
    report_generations row, so nothing is left at 'queued' forever.
    """
    cur.execute("""
        UPDATE schedule_runs
        SET status = %s, error = %s, finished_at = now()
        WHERE id = %s::uuid AND status IN ('queued', 'processing')
        RETURNING 1
    """, (status, error, st.id))
    if not cur.fetchone():
        return False
    _set_account(cur, st.account_id)
    if status != NEEDS_REVIEW:
        cur.execute("""
            UPDATE report_generations SET status = 'failed', error = %s
            WHERE id = %s::uuid AND status IN ('queued', 'processing')
        """, (error, st.run_id))
    if status == BLOCKED:
        from .schedules_tick import record_unverified_skip
        record_unverified_skip(cur, st.account_id, st.schedule_id, st.recipients)
    logger.error("SCHEDULED RUN %s (schedule %s, account %s): %s — %s",
                 st.run_id, st.schedule_id, st.account_id, status, error)
    return True


# ── §3 publishing: count the attempt, commit, publish, record the ack ───────

def record_dispatch(db_url: str, run_id: str, ok: bool, error: Optional[str] = None) -> None:
    """Best effort. If it fails, the row stays recoverable (case a or b)."""
    try:
        with psycopg.connect(db_url, autocommit=True) as conn:
            if ok:
                conn.execute("""
                    UPDATE schedule_runs SET dispatched_at = now(), last_dispatch_error = NULL
                    WHERE report_run_id = %s::uuid AND recovery_tracked AND dispatched_at IS NULL
                """, (run_id,))
            else:
                conn.execute("""
                    UPDATE schedule_runs SET last_dispatch_error = %s
                    WHERE report_run_id = %s::uuid AND recovery_tracked
                """, ((error or "publish failed")[:2000], run_id))
    except Exception as e:   # noqa: BLE001
        logger.warning("Could not record the dispatch of run %s (it stays recoverable): %s", run_id, e)


# ── §4 the lease: the worker's first step ───────────────────────────────────

def is_tracked(db_url: str, run_id: str) -> bool:
    with psycopg.connect(db_url, autocommit=True) as conn:
        row = conn.execute(
            "SELECT recovery_tracked FROM schedule_runs WHERE report_run_id = %s::uuid",
            (run_id,),
        ).fetchone()
    return bool(row and row[0])


def take_lease(db_url: str, run_id: str) -> tuple[Optional[str], str]:
    """
    (token, "leased") when this worker now owns the run; otherwise
    (None, outcome): the terminal status written, or DUPLICATE_MESSAGE.
    Makes no report_generations write unless it settles the run.
    """
    token = str(uuid.uuid4())
    with psycopg.connect(db_url) as conn:
        with conn.cursor() as cur:
            cur.execute(f"""
                UPDATE schedule_runs sr
                SET status = 'processing', started_at = COALESCE(sr.started_at, now()),
                    owner_token = %s::uuid, lease_at = now()
                FROM schedules s JOIN accounts a ON a.id = s.account_id
                WHERE sr.report_run_id = %s::uuid AND sr.recovery_tracked
                  AND sr.send_claimed_at IS NULL
                  AND (sr.status = 'queued'
                       OR (sr.status = 'processing' AND (sr.lease_at IS NULL
                                                         OR sr.lease_at < now() - %s::interval)))
                  AND sr.created_at > now() - %s::interval
                  AND s.id = sr.schedule_id AND s.active AND COALESCE(a.is_active, TRUE)
                  AND {_CAN_SEND}
                RETURNING sr.owner_token::text
            """, (token, run_id, STALE_LEASE, HORIZON))
            if cur.fetchone():
                conn.commit()
                return token, "leased"
            cur.execute(_STATE_SELECT + """
                WHERE sr.report_run_id = %s::uuid AND sr.recovery_tracked
                FOR UPDATE OF sr
            """, (run_id,))
            row = cur.fetchone()
            if not row:
                return None, DUPLICATE_MESSAGE
            st = _state(row)
            outcome = terminal_outcome(st)
            if outcome and write_terminal(cur, st, *outcome):
                conn.commit()
                return None, outcome[0]
    return None, DUPLICATE_MESSAGE


def refresh_lease(db_url: str, run_id: str, token: str) -> None:
    """Between render stages. Raises Superseded when the run is no longer ours."""
    with psycopg.connect(db_url, autocommit=True) as conn:
        row = conn.execute("""
            UPDATE schedule_runs SET lease_at = now()
            WHERE report_run_id = %s::uuid AND owner_token = %s::uuid AND status = 'processing'
            RETURNING 1
        """, (run_id, token)).fetchone()
    if not row:
        raise Superseded(run_id)


# Appended to a report_generations UPDATE's WHERE: the write lands only while
# this token owns the run. With token None (legacy and manual runs) it is
# always true, so one statement serves both paths.
OWNED = (" AND (%s::uuid IS NULL OR EXISTS (SELECT 1 FROM schedule_runs o "
         "WHERE o.report_run_id = %s::uuid AND o.owner_token = %s::uuid AND o.status = 'processing'))")


def owned(run_id: str, token: Optional[str]) -> tuple:
    return (token, run_id, token)


# Appended to a schedule_runs UPDATE's WHERE (keyed on report_run_id).
RUN_OWNED = " AND (%s::uuid IS NULL OR (owner_token = %s::uuid AND status = 'processing'))"


def run_owned(token: Optional[str]) -> tuple:
    return (token, token)


# ── §5 the pre-send claim ───────────────────────────────────────────────────

def claim_send(db_url: str, run_id: str, token: str, recipients: Iterable[str]) -> str:
    """
    CLAIMED: committed; the caller may POST, once per recipient.
    REFUSED: no POST. An ineligible run was settled under the row lock (past
             the horizon, paused, deactivated, unverified); a superseded owner
             writes nothing.
    CLAIM_ERROR: no POST, and NOTHING is written or cleared. If the COMMIT's
             answer was lost the claim may have persisted; then the stale
             lease routes the run to needs_review, because send_claimed_at is
             the authority, not the exception (Codex, design PASS).
    """
    try:
        with psycopg.connect(db_url) as conn:
            with conn.cursor() as cur:
                cur.execute(f"""
                    UPDATE schedule_runs sr
                    SET send_claimed_at = now(), send_token = %s::uuid, lease_at = now(),
                        send_recipients = %s
                    FROM schedules s JOIN accounts a ON a.id = s.account_id
                    WHERE sr.report_run_id = %s::uuid AND sr.recovery_tracked
                      AND sr.owner_token = %s::uuid AND sr.status = 'processing'
                      AND sr.send_claimed_at IS NULL
                      AND sr.created_at > now() - %s::interval
                      AND s.id = sr.schedule_id AND s.active AND COALESCE(a.is_active, TRUE)
                      AND {_CAN_SEND}
                    RETURNING 1
                """, (str(uuid.uuid4()), list(recipients), run_id, token, HORIZON))
                if cur.fetchone():
                    conn.commit()
                    return CLAIMED
                cur.execute(_STATE_SELECT + """
                    WHERE sr.report_run_id = %s::uuid AND sr.recovery_tracked
                    FOR UPDATE OF sr
                """, (run_id,))
                row = cur.fetchone()
                if row:
                    st = _state(row)
                    if (st.owner_token == token and st.status == "processing"
                            and st.send_claimed_at is None):
                        outcome = ineligible(st)
                        if outcome:
                            write_terminal(cur, st, *outcome)
                conn.commit()
                return REFUSED
    except Exception as e:   # noqa: BLE001 - fail closed
        logger.error("SCHEDULED RUN %s: the send claim failed (%s); nothing is sent, "
                     "nothing is cleared", run_id, e)
        return CLAIM_ERROR


def append_outcome(db_url: str, run_id: str, token: str, email: str, attempt) -> None:
    """One entry per recipient POSTed; refreshes the lease. Best effort."""
    entry = {"email": email, "outcome": attempt.outcome, "status_code": attempt.status_code,
             "detail": (attempt.detail or "")[:300]}
    with psycopg.connect(db_url, autocommit=True) as conn:
        conn.execute("""
            UPDATE schedule_runs
            SET send_outcomes = send_outcomes || jsonb_build_array(
                    %s::jsonb || jsonb_build_object('at', now())),
                lease_at = now()
            WHERE report_run_id = %s::uuid AND owner_token = %s::uuid AND status = 'processing'
        """, (json.dumps(entry), run_id, token))


def aggregate(attempts) -> tuple[str, Optional[str], str]:
    """
    (schedule_runs status, error, email_log status) for one claimed occurrence.
    Any unknown outcome wins over a definite rejection for another recipient.
    """
    from .email.providers.sendgrid import ACCEPTED, UNKNOWN
    total = len(attempts)
    unknown = [(e, a) for e, a in attempts if a.outcome == UNKNOWN]
    if unknown:
        e, a = unknown[0]
        return (NEEDS_REVIEW,
                f"outcome unknown for {len(unknown)} of {total} recipient(s): the provider may "
                f"have accepted these; not resent (first: {e} -> {a.status_code} {a.detail})"[:2000],
                "needs_review")
    failed = [(e, a) for e, a in attempts if a.outcome != ACCEPTED]
    if failed:
        e, a = failed[0]
        return (FAILED,
                f"failed_email: {len(failed)} of {total} recipient(s) not accepted "
                f"(first: {e} -> {a.outcome} {a.status_code} {a.detail})"[:2000],
                "failed")
    return COMPLETED, None, "sent"


def finish(db_url: str, run_id: str, token: str, status: str, error: Optional[str]) -> bool:
    """The owner's terminal write. False when superseded or already settled."""
    with psycopg.connect(db_url, autocommit=True) as conn:
        row = conn.execute("""
            UPDATE schedule_runs SET status = %s, error = %s, finished_at = now()
            WHERE report_run_id = %s::uuid AND owner_token = %s::uuid AND status = 'processing'
            RETURNING 1
        """, (status, error, run_id, token)).fetchone()
    return bool(row)


def finish_after_error(cur, run_id: str, token: str, unclaimed_status: str, error: str) -> Optional[str]:
    """
    An exception escaped the owner. If the send was claimed, the email may have
    gone out: needs_review, never failed (the claim is the authority).
    Returns the status written, or None when superseded or already settled.
    """
    cur.execute("""
        UPDATE schedule_runs
        SET status = CASE WHEN send_claimed_at IS NOT NULL THEN 'needs_review' ELSE %s END,
            error = CASE WHEN send_claimed_at IS NOT NULL THEN %s ELSE %s END,
            finished_at = now()
        WHERE report_run_id = %s::uuid AND owner_token = %s::uuid AND status = 'processing'
        RETURNING status
    """, (unclaimed_status, f"{MSG_CLAIMED_NO_OUTCOME} ({error})"[:2000], error[:2000], run_id, token))
    row = cur.fetchone()
    return row[0] if row else None


# ── §6 the sweep, for tracked rows ──────────────────────────────────────────

def backoff_elapsed(st: RunState) -> bool:
    if st.last_dispatch_at is None:
        return True
    n = max(st.dispatch_attempts, 1)
    wait = BACKOFF_MINUTES[min(n, len(BACKOFF_MINUTES)) - 1]
    return st.last_dispatch_at <= st.now - timedelta(minutes=wait)


def recovery_case(st: RunState) -> Optional[str]:
    """(a) never acknowledged, (b) acknowledged and lost, (c) a dead owner."""
    if st.send_claimed_at is not None:
        return None
    if st.status == "queued":
        if st.dispatched_at is None and st.created_at < st.now - UNACKED:
            return "a"
        if st.dispatched_at is not None and st.dispatched_at < st.now - LOST:
            return "b"
        return None
    if st.status == "processing" and not lease_is_live(st):
        return "c"
    return None


GIVE_UP = {
    "a": "not sent: the queue was unavailable for 6 attempts",
    "b": "not sent: the queue lost the task 6 times",
    "c": "not sent: the worker stopped before finishing, 6 times",
}


def sweep_decision(st: RunState) -> Optional[tuple[str, Optional[str]]]:
    """
    ("terminal", status, error) | ("republish", case) | None, as a tuple:
    (kind, detail...). Pure: the sweep and its tests share it.
    """
    out = terminal_outcome(st)
    if out:
        return ("terminal",) + out
    case = recovery_case(st)
    if case is None or not backoff_elapsed(st):
        return None
    if st.dispatch_attempts >= MAX_PUBLISHES:
        return ("terminal", FAILED, GIVE_UP[case])
    if not st.report_type:
        return ("terminal", FAILED, "not sent: the report row is missing")
    return ("republish", case)


def sweep_tracked(db_url: str, publish: Callable[[str, str, str, dict, str], tuple]) -> dict:
    """
    One pass. Rows are locked FOR UPDATE SKIP LOCKED, so concurrent tickers
    never take the same row. Attempts are counted and committed BEFORE any
    publish (§3); the publishes happen after the commit.
    """
    summary = {"terminal": {}, "republished": 0}
    to_publish = []
    with psycopg.connect(db_url) as conn:
        with conn.cursor() as cur:
            cur.execute(_STATE_SELECT + """
                WHERE sr.recovery_tracked AND sr.status IN ('queued', 'processing')
                ORDER BY sr.created_at
                LIMIT 200
                FOR UPDATE OF sr SKIP LOCKED
            """)
            for row in cur.fetchall():
                st = _state(row)
                decision = sweep_decision(st)
                if decision is None:
                    continue
                if decision[0] == "terminal":
                    if write_terminal(cur, st, decision[1], decision[2]):
                        summary["terminal"][decision[1]] = summary["terminal"].get(decision[1], 0) + 1
                    continue
                cur.execute("""
                    UPDATE schedule_runs
                    SET dispatch_attempts = dispatch_attempts + 1, last_dispatch_at = now(),
                        dispatched_at = NULL
                    WHERE id = %s::uuid
                """, (st.id,))
                to_publish.append(st)
        conn.commit()

    for st in to_publish:
        task_id, error = publish(st.run_id, st.account_id, st.report_type, st.params or {}, st.schedule_id)
        record_dispatch(db_url, st.run_id, task_id is not None, error)
        summary["republished"] += 1
        logger.warning("SCHEDULED RUN %s: republished (attempt %d) %s",
                       st.run_id, st.dispatch_attempts + 1,
                       "acknowledged" if task_id else f"FAILED: {error}")
    return summary

"""LR-027 customer-outcome signals (design #317 rev 3, section 4).

Each signal is one bounded read. It returns the outstanding ATTEMPT
IDENTITIES, never names, addresses, phone numbers or message text:

  run:<report_run_id>       a scheduled attempt (schedule_runs and its email_log
                            rows share it, so one attempt is one member)
  email:<email_log.id>      an unscheduled email attempt
  schedule:<schedule_id>    a schedule-level condition
  report:<report_generations.id>
  consumer:<consumer_reports.id>
  webhook:<webhook_id>
  heartbeat:<ticker|worker>

THRESHOLDS ARE PROPOSALS. Each carries the date it was proposed; Jerry approves
the final values after observe mode (design section 8). Changing one is a
reviewed diff, never an environment edit.

Timestamps: columns WITHOUT a time zone (report_generations.generated_at,
webhook_deliveries.created_at) are written with the session's NOW(); they are
compared with LOCALTIMESTAMP, the same clock, so the server's TimeZone setting
cannot skew them. Columns WITH a time zone use now().
"""
from dataclasses import dataclass, field
from typing import Callable, Optional

MEMBER_LIMIT = 5000   # identities stored per signal per run (design section 5)


@dataclass(frozen=True)
class Threshold:
    value: float
    proposed: str = "2026-11-18"
    approved: Optional[str] = None   # set when Jerry approves (design section 9)


# ── Proposed thresholds ──────────────────────────────────────────────────────
SCHEDULE_OVERDUE_MIN = Threshold(15)
SCHEDULE_BLOCKED_LOOKBACK_H = Threshold(24)
DISPATCH_STRANDED_ATTEMPTS = Threshold(6)          # LR-023 MAX_PUBLISHES
DISPATCH_STRANDED_HORIZON_H = Threshold(6)         # LR-023 HORIZON
# report_generations has no processing-start column, only its creation time
# (generated_at). 45 min = the 30-minute queued horizon (STALE_QUEUED_MINUTES)
# + the 5-minute task limit + margin, so a report delayed behind a burst and
# then processed normally does not trip it. Design rev 3 said 30 min of
# processing; this is the honest equivalent with the columns that exist.
REPORT_STUCK_MIN = Threshold(45)
REPORT_FAILURES_MIN_COUNT = Threshold(5)
REPORT_FAILURES_MIN_SHARE = Threshold(0.20)
CONSUMER_STUCK_MIN = Threshold(15)
CONSUMER_LOOKBACK_D = Threshold(7)
WEBHOOK_FAILURES_PER_HOUR = Threshold(3)
PROVIDER_REFUSALS_MIN_COUNT = Threshold(10)
PROVIDER_REFUSALS_MIN_SHARE = Threshold(0.10)
SEND_NOT_ATTEMPTED_MIN_COUNT = Threshold(3)


@dataclass
class Reading:
    tripped: bool
    identities: list = field(default_factory=list)
    count: int = 0                    # outstanding members (may exceed the stored list)
    value: dict = field(default_factory=dict)   # counts only, for the incident and the log


@dataclass(frozen=True)
class Signal:
    key: str
    sms: bool
    consequence: str
    read: Callable


def _identities(cur, sql: str, params: dict) -> Reading:
    """Rows of one identity column; any row trips; count beyond the bound is exact."""
    cur.execute(f"SELECT ident FROM ({sql}) s LIMIT %(limit)s", {**params, "limit": MEMBER_LIMIT})
    ids = [r[0] for r in cur.fetchall()]
    count = len(ids)
    if count >= MEMBER_LIMIT:
        cur.execute(f"SELECT count(*) FROM ({sql}) s", params)
        count = cur.fetchone()[0]
    return Reading(tripped=count > 0, identities=ids, count=count, value={"count": count})


# ── Signals ──────────────────────────────────────────────────────────────────

def schedule_overdue(cur) -> Reading:
    # The ticker's exception path clears the lock and records NOTHING, and
    # next_run_at never advances: an overdue active schedule is the only trace.
    # Inactive schedules (the 43 kept inactive) are excluded by `active`.
    return _identities(cur, """
        SELECT 'schedule:' || id::text AS ident
        FROM schedules
        WHERE active
          AND COALESCE(next_run_at, created_at) < now() - make_interval(mins => %(m)s)
        ORDER BY COALESCE(next_run_at, created_at)
    """, {"m": int(SCHEDULE_OVERDUE_MIN.value)})


def schedule_blocked(cur) -> Reading:
    # An unverified account's due schedule is skipped with an email_log row and
    # NO schedule_runs row (schedules_tick.record_unverified_skip).
    return _identities(cur, """
        SELECT DISTINCT 'schedule:' || schedule_id::text AS ident
        FROM email_log
        WHERE status = 'blocked_unverified' AND schedule_id IS NOT NULL
          AND created_at > now() - make_interval(hours => %(h)s)
    """, {"h": int(SCHEDULE_BLOCKED_LOOKBACK_H.value)})


def dispatch_stranded(cur) -> Reading:
    return _identities(cur, """
        SELECT 'run:' || report_run_id::text AS ident
        FROM schedule_runs
        WHERE recovery_tracked
          AND status IN ('queued', 'processing')
          AND (dispatch_attempts >= %(n)s
               OR created_at < now() - make_interval(hours => %(h)s))
        ORDER BY created_at
    """, {"n": int(DISPATCH_STRANDED_ATTEMPTS.value), "h": int(DISPATCH_STRANDED_HORIZON_H.value)})


def send_needs_review(cur) -> Reading:
    # One member per ATTEMPT: a scheduled attempt can be held in schedule_runs
    # and in email_log (report_id = report_run_id); both map to run:<id>.
    return _identities(cur, """
        SELECT DISTINCT ident FROM (
            SELECT 'run:' || report_run_id::text AS ident
            FROM schedule_runs
            WHERE status = 'needs_review' AND report_run_id IS NOT NULL
            UNION ALL
            SELECT CASE WHEN schedule_id IS NOT NULL AND report_id IS NOT NULL
                        THEN 'run:' || report_id::text
                        ELSE 'email:' || id::text END
            FROM email_log
            WHERE status = 'needs_review' AND resolution IS NULL
        ) held
    """, {})


def report_stuck(cur) -> Reading:
    return _identities(cur, """
        SELECT 'report:' || id::text AS ident
        FROM report_generations
        WHERE status = 'processing'
          AND generated_at < LOCALTIMESTAMP - make_interval(mins => %(m)s)
        ORDER BY generated_at
    """, {"m": int(REPORT_STUCK_MIN.value)})


def report_failures(cur) -> Reading:
    cur.execute("""
        SELECT count(*) FILTER (WHERE status = 'failed'), count(*)
        FROM report_generations
        WHERE generated_at > LOCALTIMESTAMP - interval '1 hour'
    """)
    failed, total = cur.fetchone()
    tripped = (failed >= REPORT_FAILURES_MIN_COUNT.value
               and total > 0 and failed / total >= REPORT_FAILURES_MIN_SHARE.value)
    reading = _identities(cur, """
        SELECT 'report:' || id::text AS ident
        FROM report_generations
        WHERE status = 'failed' AND generated_at > LOCALTIMESTAMP - interval '1 hour'
        ORDER BY generated_at DESC
    """, {})
    return Reading(tripped=tripped, identities=reading.identities if tripped else [],
                   count=reading.count if tripped else 0, value={"failed": failed, "total": total})


def consumer_delivery_stuck(cur) -> Reading:
    # LR-020/021/022 states. A terminal failure stays in the row, so the
    # lookback keeps an old, already-handled one from holding an incident open
    # forever; observe mode measures whether 7 days is right.
    return _identities(cur, """
        SELECT 'consumer:' || id::text AS ident
        FROM consumer_reports
        WHERE created_at > now() - make_interval(days => %(d)s)
          AND (
            (delivery_claimed_at < now() - make_interval(mins => %(m)s)
             AND consumer_email_sent_at IS NULL AND consumer_sms_sent_at IS NULL)
            OR agent_notify_status IN ('failed', 'needs_review')
            OR pdf_status = 'failed'
            OR (pdf_status IN ('queued', 'generating')
                AND pdf_claimed_at < now() - make_interval(mins => %(m)s))
          )
        ORDER BY created_at
    """, {"d": int(CONSUMER_LOOKBACK_D.value), "m": int(CONSUMER_STUCK_MIN.value)})


def report_webhook_failures(cur) -> Reading:
    # webhook_deliveries holds COMPLETED outbound report-webhook attempts to
    # customers, not a queue and not Stripe's: recent failures only.
    return _identities(cur, """
        SELECT 'webhook:' || webhook_id::text AS ident
        FROM webhook_deliveries
        WHERE created_at > LOCALTIMESTAMP - interval '1 hour'
          AND (error IS NOT NULL OR response_status IS NULL
               OR response_status NOT BETWEEN 200 AND 299)
        GROUP BY webhook_id
        HAVING count(*) >= %(n)s
    """, {"n": int(WEBHOOK_FAILURES_PER_HOUR.value)})


# ── Email outcomes (design rev 3, "Outcome classes") ──────────────────────
#
# Classified PER WRITER, from an audit of every email_log write site:
#   * Tracked scheduled sends (LR-023) store a failed row with response_code
#     NULL whatever SendGrid said; the per-recipient truth is
#     schedule_runs.send_outcomes (outcome: accepted | rejected | not_sent |
#     unknown, worker/email/providers/sendgrid.py).
#   * The legacy path stores SYNTHESIZED codes: 400 "No recipients"/"No PDF
#     URL"/"No recipients provided" and 500 "Unsubscribe URL missing..." /
#     "SENDGRID_API_KEY not configured" never reached SendGrid; 500/504 for
#     "Request error"/"Unexpected error"/"Timeout" are ambiguous. A real 4xx
#     is SendGrid refusing.
# Ambiguous rows (legacy 5xx, timeouts) are counted as NEITHER a refusal nor
# "not sent": never guessed. Unknown outcomes are send_needs_review.
# Resend rows (consumer and owner notices) are not SendGrid's and are excluded.

_SYNTHESIZED_NEVER_SENT = ("No recipients", "No PDF URL", "No recipients provided",
                           "Unsubscribe URL missing from rendered email body")


def provider_refusals(cur) -> Reading:
    cur.execute("""
        SELECT count(*) FROM email_log
        WHERE provider = 'sendgrid' AND created_at > now() - interval '1 hour'
          AND status IN ('sent', 'failed', 'needs_review', 'sending')
    """)
    deliveries = cur.fetchone()[0]
    reading = _identities(cur, """
        SELECT DISTINCT ident FROM (
            SELECT 'run:' || report_run_id::text AS ident
            FROM schedule_runs
            WHERE recovery_tracked AND created_at > now() - interval '1 hour'
              AND send_outcomes @> '[{"outcome": "rejected"}]'
            UNION ALL
            SELECT CASE WHEN schedule_id IS NOT NULL AND report_id IS NOT NULL
                        THEN 'run:' || report_id::text ELSE 'email:' || id::text END
            FROM email_log
            WHERE provider = 'sendgrid' AND status = 'failed'
              AND created_at > now() - interval '1 hour'
              AND response_code BETWEEN 400 AND 499
              AND COALESCE(error, '') <> ALL (%(synth)s)
        ) refused
    """, {"synth": list(_SYNTHESIZED_NEVER_SENT)})
    refused = reading.count
    tripped = (refused >= PROVIDER_REFUSALS_MIN_COUNT.value and deliveries > 0
               and refused / deliveries >= PROVIDER_REFUSALS_MIN_SHARE.value)
    return Reading(tripped=tripped, identities=reading.identities if tripped else [],
                   count=refused if tripped else 0, value={"refused": refused, "deliveries": deliveries})


def send_not_attempted(cur) -> Reading:
    reading = _identities(cur, """
        SELECT DISTINCT ident FROM (
            SELECT 'run:' || report_run_id::text AS ident
            FROM schedule_runs
            WHERE recovery_tracked AND created_at > now() - interval '1 hour'
              AND send_outcomes @> '[{"outcome": "not_sent"}]'
            UNION ALL
            SELECT CASE WHEN schedule_id IS NOT NULL AND report_id IS NOT NULL
                        THEN 'run:' || report_id::text ELSE 'email:' || id::text END
            FROM email_log
            WHERE provider = 'sendgrid' AND status = 'failed'
              AND created_at > now() - interval '1 hour'
              AND (error = ANY (%(synth)s) OR error LIKE '%%SENDGRID_API_KEY not configured%%')
        ) never_sent
    """, {"synth": list(_SYNTHESIZED_NEVER_SENT)})
    tripped = reading.count >= SEND_NOT_ATTEMPTED_MIN_COUNT.value
    return Reading(tripped=tripped, identities=reading.identities if tripped else [],
                   count=reading.count if tripped else 0, value={"not_sent": reading.count})


SIGNALS: list[Signal] = [
    Signal("schedule_overdue", True, "A scheduled report is overdue and has not been sent.", schedule_overdue),
    Signal("schedule_blocked", False,
           "A schedule is being skipped: no user on the account has confirmed their email.", schedule_blocked),
    Signal("dispatch_stranded", True,
           "A scheduled report did not go out and the sweep has given up.", dispatch_stranded),
    Signal("send_needs_review", True,
           "A send's outcome is unknown; it will not be retried. Someone must decide whether it arrived.",
           send_needs_review),
    Signal("provider_refusals", True, "SendGrid is refusing mail.", provider_refusals),
    Signal("send_not_attempted", True,
           "Sends are failing before reaching SendGrid (configuration or content).", send_not_attempted),
    Signal("report_stuck", True, "A report has been processing for over 45 minutes.", report_stuck),
    Signal("report_failures", True, "Reports are failing to render.", report_failures),
    Signal("consumer_delivery_stuck", True,
           "A home-value report or its agent notification has not been delivered.", consumer_delivery_stuck),
    Signal("report_webhook_failures", False, "A customer's report webhook is failing.", report_webhook_failures),
]

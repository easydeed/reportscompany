"""LR-027 slice 3: operator alert delivery (design #317 rev 3, sections 5 and 6).

OFF BY DEFAULT. Nothing is written to ops_alert_notifications and nothing is
sent unless OPS_ALERTS_ENABLED=1, and then only to a channel whose destination
Jerry has set in Render (OPS_ALERT_EMAIL, OPS_ALERT_SMS_TO). With the switch
off this module is inert, and the monitor stays exactly as observe-only as
slice 2 left it. The switch stays off until Jerry approves the thresholds.

Delivery follows LR-023's claim-before-send rule, one row per incident x
event x channel:

  pending   created, never attempted                      -> claimable
  claimed   claimed_at + claim_token COMMITTED before the -> the same run
            provider call, by a conditional update            records the outcome
  accepted  SendGrid 202 / a Twilio message SID           -> terminal
  not_sent  known unsent: no connection, not configured,  -> retried on a later
            or a definite provider refusal (4xx)              run, <= 5 attempts
  unknown   the call may have reached the provider        -> NEVER retried;
            (timeout after send, 5xx, anything else), or      listed for the
            a claim with no outcome after the 5-minute lease  operator

The destination is never logged and never stored. Bodies carry only the
incident key, its consequence line, counts, timestamps and up to five
attempt identities (UUID-based references). They are built from the ops
tables alone, which hold no account data.

Events and channels:
  open         email; SMS when the key's SMS column says so. A re-open within
               30 minutes of the last resolution (flapping) is email only.
  update:<n>   new members, or growth past the stored bound: email only.
  renotify:<n> every 6 hours while open: as `open`.
  resolved     as `open` for the key, without the flap rule.
SMS are capped at 10 an hour across all incidents; past the cap one
`sms_cap:<hour>` text says the rest of the hour is email only.
"""
import html
import logging
import os
import re
import uuid
from typing import Optional

logger = logging.getLogger(__name__)

RENOTIFY_HOURS = 6
SMS_CAP_PER_HOUR = 10
MAX_ATTEMPTS = 5
CLAIM_LEASE_MIN = 5          # > the 90 s run budget plus one 10 s provider call
CALL_TIMEOUT_S = 10.0
DISPATCH_LIMIT = 50          # rows per run; the rest wait for the next run
SAMPLE = 5
RETENTION_DAYS = 90
E164 = re.compile(r"^\+[1-9]\d{7,14}$")

ACCEPTED, NOT_SENT, UNKNOWN = "accepted", "not_sent", "unknown"


# ── configuration ────────────────────────────────────────────────────────────

def enabled() -> bool:
    return os.getenv("OPS_ALERTS_ENABLED", "0") == "1"


def _email_to() -> str:
    return os.getenv("OPS_ALERT_EMAIL", "").strip()


def _sms_to() -> str:
    return os.getenv("OPS_ALERT_SMS_TO", "").strip()


def _public_base() -> str:
    return (os.getenv("OPS_PUBLIC_BASE") or os.getenv("WEB_BASE") or "").rstrip("/")


def channels_configured() -> dict:
    """Which channels would send. Booleans only: never the destinations."""
    return {"email": bool(_email_to()), "sms": bool(_sms_to())}


def _key_meta(key: str) -> tuple[bool, str]:
    """(sends SMS, consequence line) for a signal key."""
    from . import ops_monitor, ops_signals
    for sig in ops_signals.SIGNALS:
        if sig.key == key:
            return sig.sms, sig.consequence
    if key in ops_monitor.HEARTBEAT_SIGNALS:
        return ops_monitor.HEARTBEAT_SIGNALS[key]
    return False, key


# ── creating rows (inside the monitor's transaction) ─────────────────────────

def _insert(cur, alert_id, event: str, channel: str) -> bool:
    cur.execute("""INSERT INTO ops_alert_notifications (alert_id, event, channel)
                   VALUES (%s, %s, %s) ON CONFLICT (alert_id, event, channel) DO NOTHING
                   RETURNING id""", (alert_id, event, channel))
    return cur.fetchone() is not None


def _sms_room(cur) -> bool:
    cur.execute("""SELECT count(*) FROM ops_alert_notifications
                   WHERE channel = 'sms' AND event NOT LIKE 'sms\\_cap:%%'
                     AND created_at > now() - interval '1 hour'""")
    return cur.fetchone()[0] < SMS_CAP_PER_HOUR


def _note_sms_cap(cur, alert_id) -> None:
    """One cap text per clock hour, across every incident."""
    cur.execute("SELECT 'sms_cap:' || to_char(now() AT TIME ZONE 'UTC', 'YYYY-MM-DD\"T\"HH24')")
    event = cur.fetchone()[0]
    cur.execute("SELECT 1 FROM ops_alert_notifications WHERE event = %s LIMIT 1", (event,))
    if cur.fetchone() is None:
        _insert(cur, alert_id, event, "sms")


def enqueue(cur, alert_id, key: str, event: str, *, flapping: bool = False) -> list:
    """Create the notification rows for one announced event. Inert when off.

    Runs in the monitor's transaction, so a row exists only if the incident
    change that announced it committed. Returns the channels queued.
    """
    if not enabled():
        return []
    sms_key, _ = _key_meta(key)
    configured = channels_configured()
    queued = []
    if configured["email"] and _insert(cur, alert_id, event, "email"):
        queued.append("email")
    wants_sms = (sms_key and configured["sms"] and not event.startswith("update:")
                 and not (event == "open" and flapping))
    if wants_sms:
        # Serialise the cap check across concurrent monitor transactions.
        cur.execute("SELECT pg_advisory_xact_lock(hashtext('ops_alert_sms_cap'))")
        if _sms_room(cur):
            if _insert(cur, alert_id, event, "sms"):
                queued.append("sms")
        else:
            _note_sms_cap(cur, alert_id)
            queued.append("sms_cap")
    return queued


def next_update_event(cur, alert_id) -> str:
    cur.execute("""SELECT count(DISTINCT event) FROM ops_alert_notifications
                   WHERE alert_id = %s AND event LIKE 'update:%%'""", (alert_id,))
    return f"update:{cur.fetchone()[0] + 1}"


def announce(cur, alert_id, key: str, monitor_event: str, *, flapping: bool = False) -> list:
    """The monitor's hook: map its event to a notification event. Inert when off."""
    if not enabled():
        return []
    if monitor_event in ("new_members", "grew"):
        return enqueue(cur, alert_id, key, next_update_event(cur, alert_id))
    return enqueue(cur, alert_id, key, monitor_event, flapping=flapping)


def enqueue_renotifications(cur) -> int:
    """Every open incident past each 6-hour mark gets `renotify:<n>`, once."""
    if not enabled():
        return 0
    cur.execute("""SELECT id, key, floor(extract(epoch FROM now() - opened_at) / %s)::int
                   FROM ops_alerts WHERE resolved_at IS NULL
                     AND opened_at < now() - make_interval(hours => %s)""",
                (RENOTIFY_HOURS * 3600, RENOTIFY_HOURS))
    made = 0
    for alert_id, key, n in cur.fetchall():
        if enqueue(cur, alert_id, key, f"renotify:{n}"):
            made += 1
    return made


# ── dispatch (its own transactions, after the signals) ───────────────────────

def expire_abandoned(cur) -> int:
    """A claim with no outcome after the lease may have been sent: `unknown`."""
    cur.execute("""UPDATE ops_alert_notifications
                   SET state = 'unknown', outcome_at = now(), last_error_class = 'abandoned'
                   WHERE state = 'claimed' AND claimed_at < now() - make_interval(mins => %s)""",
                (CLAIM_LEASE_MIN,))
    return cur.rowcount


def claim(conn, row_id) -> Optional[str]:
    """Commit the claim BEFORE any provider call. Returns the token, or None."""
    token = str(uuid.uuid4())
    with conn.cursor() as cur:
        cur.execute("""UPDATE ops_alert_notifications
                       SET state = 'claimed', claimed_at = now(), claim_token = %s,
                           attempts = attempts + 1
                       WHERE id = %s AND state IN ('pending', 'not_sent')
                         AND claimed_at IS NULL AND attempts < %s
                       RETURNING id""", (token, row_id, MAX_ATTEMPTS))
        won = cur.fetchone() is not None
    conn.commit()
    return token if won else None


def settle(conn, row_id, token, outcome: str, *, provider_id=None, error_class=None) -> bool:
    """Record what is known, only for the claim this run holds."""
    with conn.cursor() as cur:
        cur.execute("""UPDATE ops_alert_notifications
                       SET state = %s, outcome_at = now(), provider_message_id = %s,
                           last_error_class = %s,
                           claimed_at = CASE WHEN %s = 'not_sent' THEN NULL ELSE claimed_at END
                       WHERE id = %s AND claim_token = %s AND state = 'claimed'""",
                    (outcome, provider_id, error_class, outcome, row_id, token))
        done = cur.rowcount == 1
    conn.commit()
    return done


def _load(cur, row_id) -> Optional[dict]:
    cur.execute("""SELECT n.event, n.channel, a.id, a.key, a.opened_at, a.resolved_at,
                          a.member_count, a.members_truncated
                   FROM ops_alert_notifications n JOIN ops_alerts a ON a.id = n.alert_id
                   WHERE n.id = %s""", (row_id,))
    r = cur.fetchone()
    if r is None:
        return None
    event, channel, alert_id, key, opened, resolved, count, truncated = r
    cur.execute("""SELECT identity FROM ops_alert_members WHERE alert_id = %s
                   ORDER BY first_seen_at DESC, identity LIMIT %s""", (alert_id, SAMPLE))
    sample = [x[0] for x in cur.fetchall()]
    cur.execute("SELECT count(*) FROM ops_alert_notifications WHERE state = 'unknown' AND resolution IS NULL")
    uncertain = cur.fetchone()[0]
    return {"event": event, "channel": channel, "key": key, "opened_at": opened,
            "resolved_at": resolved, "count": count, "truncated": truncated,
            "sample": sample, "uncertain": uncertain}


def _event_label(event: str, row: dict) -> str:
    if event == "open":
        return "Opened"
    if event == "resolved":
        minutes = int((row["resolved_at"] - row["opened_at"]).total_seconds() // 60) if row["resolved_at"] else 0
        return f"Resolved after {minutes} min"
    if event.startswith("renotify:"):
        return f"Still failing ({int(event.split(':')[1]) * RENOTIFY_HOURS} h)"
    if event.startswith("update:"):
        return "New members" if not row["truncated"] else "Outstanding count grew"
    if event.startswith("sms_cap:"):
        return f"SMS limit reached ({SMS_CAP_PER_HOUR}/hour)"
    return event


def render(row: dict) -> dict:
    """{"subject", "html", "sms"} from ops-table data only."""
    _, consequence = _key_meta(row["key"])
    base = _public_base()
    link = f"{base}/admin" if base else ""
    label = _event_label(row["event"], row)
    if row["event"].startswith("sms_cap:"):
        sms = (f"TrendyReports ops: more than {SMS_CAP_PER_HOUR} alert texts this hour. "
               f"The rest of this hour's alerts are email only. {link}").strip()
        return {"subject": "", "html": "", "sms": sms}
    count = f"{row['count']}{'+' if row['truncated'] else ''}"
    subject = f"[TrendyReports ops] {label}: {consequence} ({row['key']})"
    lines = [
        f"<p><strong>{html.escape(label)}</strong>: {html.escape(consequence)}</p>",
        f"<p>Signal: <code>{html.escape(row['key'])}</code><br>Outstanding: {html.escape(count)}<br>"
        f"First seen: {html.escape(row['opened_at'].isoformat(timespec='minutes'))}</p>",
    ]
    if row["sample"]:
        items = "".join(f"<li><code>{html.escape(s)}</code></li>" for s in row["sample"])
        lines.append(f"<p>Newest attempts (up to {SAMPLE}):</p><ul>{items}</ul>")
    if row["uncertain"]:
        lines.append(f"<p>{row['uncertain']} earlier alert(s) may not have been delivered "
                     f"(outcome unknown). Reconcile them in the admin ops view.</p>")
    if link:
        lines.append(f'<p><a href="{html.escape(link)}">Admin</a></p>')
    sms = f"TrendyReports ops: {label}: {consequence} ({row['key']}, {count}). {link}".strip()
    return {"subject": subject, "html": "\n".join(lines), "sms": sms}


def _send_email(body: dict) -> tuple[str, Optional[str], Optional[str]]:
    from .email.providers import sendgrid
    to = _email_to()
    if not to:
        return NOT_SENT, None, "not_configured"
    attempt = sendgrid.send_email([to], body["subject"], body["html"],
                                  single_attempt=True, timeout=CALL_TIMEOUT_S)
    if attempt.outcome == sendgrid.ACCEPTED:
        return ACCEPTED, None, None
    if attempt.outcome == sendgrid.REJECTED:
        return NOT_SENT, None, f"refused_{attempt.status_code}"
    if attempt.outcome == sendgrid.NOT_SENT:
        return NOT_SENT, None, "no_connection_or_config"
    return UNKNOWN, None, f"unknown_{attempt.status_code}" if attempt.status_code else "unknown"


# The customer path (sms/send.py) logs `to_number` on every send; this path
# never calls it. Twilio's own HTTP client logs request URLs and headers at
# INFO (not the body, as of twilio 9.x); its logger is pinned to WARNING here
# so nothing about an operator text comes from the library either.
_twilio_log = logging.getLogger(__name__ + ".twilio_http")
_twilio_log.setLevel(logging.WARNING)


def _twilio_client():
    from .sms import send as sms_send
    if not all([sms_send.TWILIO_ACCOUNT_SID, sms_send.TWILIO_AUTH_TOKEN, sms_send.TWILIO_PHONE_NUMBER]):
        return None, None
    from twilio.http.http_client import TwilioHttpClient
    from twilio.rest import Client
    http = TwilioHttpClient(timeout=CALL_TIMEOUT_S, logger=_twilio_log)
    return Client(sms_send.TWILIO_ACCOUNT_SID, sms_send.TWILIO_AUTH_TOKEN, http_client=http), \
        sms_send.TWILIO_PHONE_NUMBER


def _send_sms(body: dict) -> tuple[str, Optional[str], Optional[str]]:
    """Classifies like sms_outcome, and logs no destination (design section 5)."""
    to = _sms_to()
    if not to:
        return NOT_SENT, None, "not_configured"
    if not E164.match(to):
        return NOT_SENT, None, "invalid_destination"
    client, from_ = _twilio_client()
    if client is None:
        return NOT_SENT, None, "not_configured"
    from twilio.base.exceptions import TwilioRestException
    try:
        msg = client.messages.create(body=body["sms"], from_=from_, to=to)
    except TwilioRestException as exc:
        status = exc.status if isinstance(exc.status, int) else None
        if status is not None and status >= 500:
            return UNKNOWN, None, f"unknown_{status}"
        return NOT_SENT, None, f"refused_{status}"      # Twilio answered: no message created
    except Exception as exc:  # noqa: BLE001
        import requests
        if isinstance(exc, (requests.exceptions.ConnectTimeout,)):
            return NOT_SENT, None, "no_connection"
        return UNKNOWN, None, f"unknown_{type(exc).__name__}"
    return ACCEPTED, getattr(msg, "sid", None), None


def deliver(conn, row_id) -> Optional[str]:
    """Claim, send, settle one row. Returns the outcome, or None if not won."""
    token = claim(conn, row_id)
    if token is None:
        return None
    with conn.cursor() as cur:
        row = _load(cur, row_id)
    conn.commit()
    try:
        body = render(row)
        sender = _send_email if row["channel"] == "email" else _send_sms
        outcome, provider_id, error_class = sender(body)
    except Exception as exc:  # noqa: BLE001 - after the claim, doubt means unknown
        outcome, provider_id, error_class = UNKNOWN, None, f"unknown_{type(exc).__name__}"
    settle(conn, row_id, token, outcome, provider_id=provider_id, error_class=error_class)
    logger.warning("OPS_ALERT_SEND row=%s channel=%s event=%s outcome=%s class=%s",
                   row_id, row["channel"], row["event"], outcome, error_class or "-")
    return outcome


def dispatch(conn, clock, deadline: float) -> dict:
    """Expire abandoned claims, then deliver claimable rows until the deadline."""
    results = {"expired": 0, "sent": []}
    with conn.cursor() as cur:
        results["expired"] = expire_abandoned(cur)
        cur.execute("""DELETE FROM ops_alerts WHERE id IN (
                         SELECT id FROM ops_alerts
                         WHERE resolved_at < now() - make_interval(days => %s) LIMIT 500)""",
                    (RETENTION_DAYS,))
    conn.commit()
    if not enabled():
        return results
    with conn.cursor() as cur:
        cur.execute("""SELECT id FROM ops_alert_notifications
                       WHERE state IN ('pending', 'not_sent') AND claimed_at IS NULL AND attempts < %s
                       ORDER BY id LIMIT %s""", (MAX_ATTEMPTS, DISPATCH_LIMIT))
        ids = [r[0] for r in cur.fetchall()]
    conn.commit()
    for row_id in ids:
        if clock() > deadline:
            logger.warning("OPS_ALERT_SEND budget spent; %d row(s) wait for the next run",
                           len(ids) - len(results["sent"]))
            break
        results["sent"].append((row_id, deliver(conn, row_id)))
    return results

"""Durable ingestion; LR-012 authoritative reconciliation; all writes use db_conn.

Receipt commit is independent of processing commit. A row lock serializes
duplicates; a subscription cursor serializes distinct events, including replay.
"""
import logging

from psycopg.types.json import Jsonb

from ..db import db_conn
from .billing_envelope import SUBSCRIPTIONS
from .plans import invalidate_plan_cache
from .billing_reconcile import reconcile

logger = logging.getLogger(__name__)
TERMINAL = frozenset({'processed', 'quarantined', 'ignored'})
CACHE_EVENTS = frozenset(f'{kind}.{action}' for kind in ('price', 'product')
                         for action in ('created', 'updated', 'deleted'))


def _timeouts(cur):
    cur.execute("SET LOCAL lock_timeout = '2s'")
    cur.execute("SET LOCAL statement_timeout = '5s'")


def store_receipt(envelope):
    with db_conn() as (_, cur):
        _timeouts(cur)
        cur.execute("""INSERT INTO billing_webhook_events (livemode,event_id,envelope)
            VALUES (%s,%s,%s) ON CONFLICT (livemode,event_id) DO NOTHING""",
                    (envelope['livemode'], envelope['event_id'], Jsonb(envelope)))


def _cursor(cur, envelope):
    mode, sub = envelope['livemode'], envelope['subscription_id']
    cur.execute("""INSERT INTO billing_subscription_cursors (livemode,subscription_id)
        VALUES (%s,%s) ON CONFLICT DO NOTHING""", (mode, sub))
    cur.execute("""SELECT created FROM billing_subscription_cursors
        WHERE livemode=%s AND subscription_id=%s FOR UPDATE""", (mode, sub))
    previous = cur.fetchone()[0]
    return previous is not None and envelope['created'] < previous


def _apply(cur, e):
    """Returns (state, reason, cache_changed); never catches DB exceptions."""
    if e['reason']:
        return 'quarantined', e['reason'], False, None
    kind = e['event_type']
    if kind in CACHE_EVENTS:
        return 'processed', None, True, None
    if kind not in SUBSCRIPTIONS:
        return 'ignored', 'unsupported_event', False, None
    return reconcile(cur, e, _cursor)


def process_receipt(event_id, live, *, replay_reason=None):
    """Replay requires explicit reason. Ignored superseded receipts stay terminal."""
    if replay_reason is not None and not (1 <= len(replay_reason.strip()) <= 200):
        raise ValueError('replay_reason_required')
    changed = False
    with db_conn() as (conn, cur):
        _timeouts(cur)
        cur.execute("""SELECT envelope,state,reason FROM billing_webhook_events
            WHERE livemode=%s AND event_id=%s FOR UPDATE""", (live, event_id))
        row = cur.fetchone()
        if row is None:
            raise ValueError('receipt_missing')
        e, state, reason = row
        if state in TERMINAL and (not replay_reason or state != 'quarantined'):
            return {'state': state, 'reason': reason}
        state, reason, changed, budget = _apply(cur, e)
        if budget:
            budget.limit(cur)
        cur.execute("""UPDATE billing_webhook_events SET state=%s,reason=%s,
            processed_at=now(),attempts=attempts+1,
            replay_reason=COALESCE(%s,replay_reason),
            replayed_at=CASE WHEN %s::text IS NOT NULL THEN now() ELSE replayed_at END
            WHERE livemode=%s AND event_id=%s""",
                    (state, reason, replay_reason, replay_reason, live, event_id))
        if budget:
            budget.limit(cur)  # Covers commit as well as the last receipt write.
    if changed:
        try:
            invalidate_plan_cache()
        except Exception:
            logger.warning('Billing cache invalidation failed after committed processing')
    return {'state': state, 'reason': reason}


def inspect_replay(event_id, live):
    """Read-only dry run. No cursor row creation or lock, mutation, or provider call."""
    with db_conn() as (_, cur):
        _timeouts(cur)
        cur.execute("""SELECT envelope,state,reason FROM billing_webhook_events
            WHERE livemode=%s AND event_id=%s""", (live, event_id))
        row = cur.fetchone()
        if row is None:
            raise ValueError('receipt_missing')
        e, state, reason = row
        if e['subscription_id']:
            cur.execute("""SELECT created FROM billing_subscription_cursors
                WHERE livemode=%s AND subscription_id=%s""", (live, e['subscription_id']))
            cursor = cur.fetchone()
            if cursor and cursor[0] is not None and e['created'] < cursor[0]:
                reason = 'superseded'
        return {'event_id': event_id, 'state': state, 'reason': reason,
                'replayable': state in ('pending', 'retryable', 'quarantined')
                              and reason != 'superseded'}


def backlog(cur):
    """Actual inbound billing backlog; no relation to outbound report webhooks."""
    cur.execute("""SELECT state,count(*),min(received_at) FROM billing_webhook_events
        WHERE state IN ('pending','retryable','quarantined') GROUP BY state""")
    return [{'state': r[0], 'count': r[1], 'oldest': r[2]} for r in cur.fetchall()]


def list_receipts(cur, live):
    cur.execute("""SELECT event_id,state,reason,received_at,attempts
        FROM billing_webhook_events WHERE livemode=%s
        AND state IN ('pending','retryable','quarantined')
        ORDER BY received_at,event_id LIMIT 100""", (live,))
    return [dict(zip(('event_id', 'state', 'reason', 'received_at', 'attempts'), row))
            for row in cur.fetchall()]

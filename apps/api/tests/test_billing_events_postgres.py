"""Real PG commit/ordering proofs in an isolated scratch schema, never production."""
import os
import threading
import time
import uuid
from contextlib import contextmanager
from pathlib import Path
from urllib.parse import urlparse

import psycopg
from psycopg import sql
import pytest

from api.services import billing_events as billing

URL = os.getenv('TEST_DATABASE_URL')
pytestmark = pytest.mark.skipif(not URL, reason='Set disposable TEST_DATABASE_URL')
ROOT = Path(__file__).resolve().parents[3]
ACCOUNT = '11111111-1111-4111-8111-111111111111'


@pytest.fixture
def database(monkeypatch):
    if urlparse(URL).hostname not in ('localhost', '127.0.0.1', '::1', 'postgres'):
        pytest.fail('Billing tests require an explicitly local scratch database')
    schema = 'billing_' + uuid.uuid4().hex

    @contextmanager
    def connection():
        with psycopg.connect(URL, connect_timeout=3) as conn:
            conn.execute(sql.SQL('SET search_path TO {}').format(sql.Identifier(schema)))
            with conn.cursor() as cur:
                yield conn, cur

    with psycopg.connect(URL) as conn:
        conn.execute(sql.SQL('CREATE SCHEMA {}').format(sql.Identifier(schema)))
        conn.execute(sql.SQL('SET search_path TO {}').format(sql.Identifier(schema)))
        conn.execute('''CREATE TABLE accounts (id uuid PRIMARY KEY,plan_slug text,
            stripe_customer_id text DEFAULT 'cus_fixture',
            stripe_subscription_id text,billing_status text,plan_downgrade_at timestamptz,
            plan_downgrade_to text)''')
        conn.execute('CREATE TABLE plans (plan_slug text,stripe_price_id text,is_active boolean,market_reports_limit int DEFAULT 10,schedules_limit int DEFAULT 2,property_reports_per_month int DEFAULT 2)')
        conn.execute("INSERT INTO plans (plan_slug,stripe_price_id,is_active) VALUES ('starter','price_starter',true),('pro','price_pro',true)")
        conn.execute("UPDATE plans SET market_reports_limit=20 WHERE plan_slug='starter'")
        conn.execute("INSERT INTO plans(plan_slug,is_active,market_reports_limit,schedules_limit,property_reports_per_month) VALUES ('free',true,3,1,1)")
        conn.execute("INSERT INTO accounts (id,plan_slug) VALUES (%s,'free')", (ACCOUNT,))
        conn.execute((ROOT / 'db/migrations/0070_billing_webhook_events.sql').read_text())
        conn.execute((ROOT / 'db/migrations/0071_effective_account_plan.sql').read_text())
    from api.services import billing_reconcile as reconcile
    local = threading.local()
    real_apply = billing._apply
    def apply(cur, e):
        local.event = e
        return real_apply(cur, e)
    def snapshot(customer, live):
        e = local.event
        return {'has_more': False, 'data': [{'id':e['subscription_id'], 'customer':customer,
            'livemode':live, 'status':e['status'], 'current_period_end':e['period_end'],
            'items':{'data':[{'price':{'id':e['price_id']}}]}}]}
    monkeypatch.setattr(billing, '_apply', apply)
    monkeypatch.setattr(reconcile, 'subscriptions', snapshot)
    monkeypatch.setattr(billing, 'db_conn', connection)
    monkeypatch.setattr(billing, 'invalidate_plan_cache', lambda: None)
    try:
        yield connection
    finally:
        with psycopg.connect(URL) as conn:
            conn.execute(sql.SQL('DROP SCHEMA {} CASCADE').format(sql.Identifier(schema)))


def envelope(eid='evt_one', created=100, price='price_pro', **changes):
    result = dict(event_id=eid, event_type='customer.subscription.updated', livemode=False,
                  created=created, api_version='2025-10-29.clover', subscription_id='sub_fixture',
                  customer_id='cus_fixture', account_id=ACCOUNT, status='active', price_id=price,
                  period_end=None, reason=None)
    result.update(changes)
    return result


def query(database, statement, params=()):
    with database() as (_, cur):
        cur.execute(statement, params)
        return cur.fetchall()


def test_duplicate_and_older_retry_never_revert_newer_plan(database):
    billing.store_receipt(envelope('evt_new', 200, 'price_starter'))
    billing.process_receipt('evt_new', False)
    billing.store_receipt(envelope('evt_old', 100))
    assert billing.process_receipt('evt_old', False) == {'state': 'ignored', 'reason': 'superseded'}
    assert billing.process_receipt('evt_new', False)['state'] == 'processed'
    assert query(database, 'SELECT plan_slug FROM accounts') == [('starter',)]
    assert query(database, "SELECT attempts FROM billing_webhook_events WHERE event_id='evt_new'") == [(1,)]
    assert not billing.inspect_replay('evt_old', False)['replayable']
    assert billing.process_receipt('evt_old', False, replay_reason='reviewed stale event')['reason'] == 'superseded'


def test_quarantined_event_does_not_advance_cursor_and_replay_uses_guard(database):
    billing.store_receipt(envelope('evt_bad', 300, 'price_unknown', period_end=int(time.time())+3600))
    assert billing.process_receipt('evt_bad', False)['state'] == 'quarantined'
    assert query(database, 'SELECT created FROM billing_subscription_cursors') == [(None,)]
    billing.store_receipt(envelope('evt_good', 200, 'price_starter'))
    billing.process_receipt('evt_good', False)
    # Dashboard resend stays terminal even after configuration is repaired.
    query(database, "INSERT INTO plans (plan_slug,stripe_price_id,is_active) VALUES ('pro','price_unknown',true) RETURNING plan_slug")
    assert billing.process_receipt('evt_bad', False)['state'] == 'quarantined'
    assert billing.process_receipt('evt_bad', False, replay_reason='price mapping corrected')['state'] == 'processed'
    billing.store_receipt(envelope('evt_held_old', 100, reason='period_shape_unsupported'))
    billing.process_receipt('evt_held_old', False)
    assert not billing.inspect_replay('evt_held_old', False)['replayable']


def test_account_failure_rolls_back_but_receipt_survives(database, monkeypatch):
    billing.store_receipt(envelope())
    from api.services import billing_reconcile
    original = billing_reconcile.update_account_billing_state
    def fail(*args, **kwargs):
        raise RuntimeError('simulated crash after plan update')
    monkeypatch.setattr(billing_reconcile, 'update_account_billing_state', fail)
    with pytest.raises(RuntimeError):
        billing.process_receipt('evt_one', False)
    assert query(database, 'SELECT plan_slug FROM accounts') == [('free',)]
    assert query(database, 'SELECT state FROM billing_webhook_events') == [('pending',)]
    assert query(database, 'SELECT created FROM billing_subscription_cursors') == []
    monkeypatch.setattr(billing_reconcile, 'update_account_billing_state', original)
    assert billing.process_receipt('evt_one', False)['state'] == 'processed'


def test_concurrent_first_events_serialize_cursor_creation(database):
    for n in range(8):
        billing.store_receipt(envelope(f'evt_{n}', n + 1, 'price_starter' if n == 7 else 'price_pro'))
    barrier, errors = threading.Barrier(8), []
    def run(n):
        try:
            barrier.wait(timeout=5)
            billing.process_receipt(f'evt_{n}', False)
        except Exception as exc:
            errors.append(type(exc).__name__)
    threads = [threading.Thread(target=run, args=(n,)) for n in range(8)]
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join(10)
    assert not errors and not any(t.is_alive() for t in threads)
    assert query(database, 'SELECT plan_slug FROM accounts') == [('starter',)]
    assert query(database, 'SELECT created FROM billing_subscription_cursors') == [(8,)]


def test_missing_period_keeps_paid_plan_and_dry_run_is_read_only(database):
    query(database, "UPDATE accounts SET plan_slug='pro' RETURNING id")
    billing.store_receipt(envelope(event_type='customer.subscription.deleted', status='canceled'))
    assert billing.process_receipt('evt_one', False)['reason'] == 'period_shape_unsupported'
    before = query(database, 'SELECT envelope,state,attempts,replayed_at FROM billing_webhook_events')
    billing.inspect_replay('evt_one', False)
    assert query(database, 'SELECT envelope,state,attempts,replayed_at FROM billing_webhook_events') == before
    assert query(database, 'SELECT plan_slug FROM accounts') == [('pro',)]


def test_receipt_commit_failure_preserves_nothing(database, monkeypatch):
    @contextmanager
    def failed_commit():
        with database() as resources:
            yield resources
            raise RuntimeError('receipt commit failed')
    monkeypatch.setattr(billing, 'db_conn', failed_commit)
    with pytest.raises(RuntimeError):
        billing.store_receipt(envelope())
    assert query(database, 'SELECT count(*) FROM billing_webhook_events') == [(0,)]


def test_processing_commit_failure_preserves_pending_receipt(database, monkeypatch):
    billing.store_receipt(envelope())
    @contextmanager
    def failed_commit():
        with database() as resources:
            yield resources
            raise RuntimeError('processing commit failed')
    monkeypatch.setattr(billing, 'db_conn', failed_commit)
    with pytest.raises(RuntimeError):
        billing.process_receipt('evt_one', False)
    assert query(database, 'SELECT plan_slug FROM accounts') == [('free',)]
    assert query(database, 'SELECT state FROM billing_webhook_events') == [('pending',)]


def test_cache_failure_after_commit_does_not_repeat_account_mutation(database, monkeypatch):
    billing.store_receipt(envelope())
    def fail():
        raise RuntimeError('cache unavailable')
    monkeypatch.setattr(billing, 'invalidate_plan_cache', fail)
    assert billing.process_receipt('evt_one', False)['state'] == 'processed'
    assert billing.process_receipt('evt_one', False)['state'] == 'processed'
    assert query(database, 'SELECT attempts FROM billing_webhook_events') == [(1,)]


def test_busy_receipt_has_bounded_wait_and_no_partial_change(database):
    billing.store_receipt(envelope())
    errors = []
    def blocked():
        try:
            billing.process_receipt('evt_one', False)
        except psycopg.errors.LockNotAvailable:
            errors.append('timeout')
    with database() as (_, cur):
        cur.execute('SELECT event_id FROM billing_webhook_events FOR UPDATE')
        started = time.monotonic()
        thread = threading.Thread(target=blocked)
        thread.start()
        thread.join(5)
        assert not thread.is_alive() and errors == ['timeout']
        assert time.monotonic() - started < 5
    assert query(database, 'SELECT plan_slug FROM accounts') == [('free',)]


def test_cache_only_and_unknown_events_never_advance_subscription_cursor(database):
    billing.store_receipt(envelope('evt_cache', event_type='price.updated', subscription_id=None))
    assert billing.process_receipt('evt_cache', False)['state'] == 'processed'
    billing.store_receipt(envelope('evt_other', event_type='unsupported.event', subscription_id=None))
    assert billing.process_receipt('evt_other', False)['state'] == 'ignored'
    assert query(database, 'SELECT count(*) FROM billing_subscription_cursors') == [(0,)]
    assert query(database, 'SELECT plan_slug FROM accounts') == [('free',)]


def test_signed_http_redelivery_commits_once_against_postgres(database, monkeypatch):
    import hashlib
    import hmac
    import json
    from fastapi import FastAPI
    from fastapi.testclient import TestClient
    from api.routes import stripe_webhook as route
    monkeypatch.setattr(route, 'STRIPE_SECRET_KEY', 'sk_test_fixture')
    monkeypatch.setattr(route, 'STRIPE_WEBHOOK_SECRET', 'whsec_fixture')
    app = FastAPI()
    app.include_router(route.router)
    body = json.dumps({'id': 'evt_http', 'type': 'customer.subscription.updated',
        'created': 100, 'livemode': False, 'api_version': '2025-10-29.clover',
        'data': {'object': {'id': 'sub_fixture', 'customer': 'cus_fixture', 'status': 'active',
            'metadata': {'account_id': ACCOUNT}, 'items': {'data': [
                {'price': {'id': 'price_pro'}}]}}}}).encode()
    stamp = str(int(time.time()))
    signature = hmac.new(b'whsec_fixture', stamp.encode() + b'.' + body, hashlib.sha256).hexdigest()
    headers = {'stripe-signature': f't={stamp},v1={signature}'}
    with TestClient(app) as client:
        assert client.post('/v1/webhooks/stripe', content=body, headers=headers).status_code == 200
        assert client.post('/v1/webhooks/stripe', content=body, headers=headers).status_code == 200
    assert query(database, 'SELECT plan_slug FROM accounts') == [('pro',)]
    assert query(database, 'SELECT attempts,state FROM billing_webhook_events') == [(1, 'processed')]


def test_equal_second_events_are_not_sorted_by_event_identifier(database):
    billing.store_receipt(envelope('evt_z', 100, 'price_pro'))
    billing.store_receipt(envelope('evt_a', 100, 'price_starter'))
    billing.process_receipt('evt_z', False)
    billing.process_receipt('evt_a', False)
    assert query(database, 'SELECT plan_slug FROM accounts') == [('starter',)]


def test_rls_probe_cannot_access_receipts_or_cursors(database):
    role = 'bill_probe_' + uuid.uuid4().hex
    billing.store_receipt(envelope())
    with database() as (_, cur):
        cur.execute('SELECT current_schema()')
        schema = cur.fetchone()[0]
        cur.execute(sql.SQL('CREATE ROLE {}').format(sql.Identifier(role)))
        cur.execute(sql.SQL('GRANT USAGE ON SCHEMA {} TO {}').format(
            sql.Identifier(schema), sql.Identifier(role)))
        cur.execute(sql.SQL('GRANT SELECT,INSERT ON ALL TABLES IN SCHEMA {} TO {}').format(
            sql.Identifier(schema), sql.Identifier(role)))
    try:
        with database() as (_, cur):
            cur.execute(sql.SQL('SET LOCAL ROLE {}').format(sql.Identifier(role)))
            cur.execute("SELECT set_config('app.current_account_id',%s,true)", (ACCOUNT,))
            cur.execute('SELECT count(*) FROM billing_webhook_events')
            assert cur.fetchone()[0] == 0
            cur.execute('SELECT count(*) FROM billing_subscription_cursors')
            assert cur.fetchone()[0] == 0
        with pytest.raises(psycopg.errors.InsufficientPrivilege):
            with database() as (_, cur):
                cur.execute(sql.SQL('SET LOCAL ROLE {}').format(sql.Identifier(role)))
                cur.execute("INSERT INTO billing_webhook_events VALUES ('evt_bad',false,'{}')")
    finally:
        with database() as (_, cur):
            cur.execute(sql.SQL('DROP OWNED BY {}').format(sql.Identifier(role)))
            cur.execute(sql.SQL('DROP ROLE {}').format(sql.Identifier(role)))

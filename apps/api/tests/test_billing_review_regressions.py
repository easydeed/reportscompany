"""Claude's LR-011 review: existing-cursor race and two missed protections."""
import threading

from api.services import billing_events as billing
from api.services.billing_envelope import normalize_verified_event
from test_billing_events_postgres import database, envelope, query, ACCOUNT  # noqa: F401
from test_billing_envelope import event


def test_existing_cursor_serializes_two_different_events(database, monkeypatch):
    billing.store_receipt(envelope('evt_first', 50))
    billing.process_receipt('evt_first', False)
    billing.store_receipt(envelope('evt_new', 200, 'price_starter'))
    billing.store_receipt(envelope('evt_old', 100, 'price_pro'))
    paused, release = threading.Event(), threading.Event()
    old_started, old_read = threading.Event(), threading.Event()
    real_price, real_cursor = billing.get_plan_slug_for_stripe_price, billing._cursor
    results, errors = {}, []

    def slow_price(cur, price):
        if price == 'price_starter':
            paused.set()
            assert release.wait(5), 'test did not release newer event'
        return real_price(cur, price)

    def observed_cursor(cur, e):
        if e['event_id'] == 'evt_old':
            old_started.set()
        result = real_cursor(cur, e)
        if e['event_id'] == 'evt_old':
            old_read.set()
        return result

    def run(eid):
        try:
            results[eid] = billing.process_receipt(eid, False)
        except Exception as exc:
            errors.append(type(exc).__name__)

    monkeypatch.setattr(billing, 'get_plan_slug_for_stripe_price', slow_price)
    monkeypatch.setattr(billing, '_cursor', observed_cursor)
    newer = threading.Thread(target=run, args=('evt_new',))
    older = threading.Thread(target=run, args=('evt_old',))
    try:
        newer.start()
        assert paused.wait(5)
        older.start()
        assert old_started.wait(5)
        # With the real lock the old cursor read cannot finish yet. Removing
        # FOR UPDATE lets it read the stale value before the newer commit.
        old_read.wait(0.4)
    finally:
        release.set()
        newer.join(5)
        if older.ident is not None:
            older.join(5)
    assert not errors and not newer.is_alive() and not older.is_alive()
    assert query(database, 'SELECT plan_slug FROM accounts') == [('starter',)]
    assert results['evt_old'] == {'state': 'ignored', 'reason': 'superseded'}


def test_expired_cancellation_clears_subscription_billing_state(database):
    query(database, """UPDATE accounts SET plan_slug='pro',billing_status='active',
        stripe_subscription_id='sub_fixture' WHERE id=%s RETURNING id""", (ACCOUNT,))
    billing.store_receipt(envelope(event_type='customer.subscription.deleted',
                                   period_end=1, status='canceled'))
    billing.process_receipt('evt_one', False)
    assert query(database, 'SELECT plan_slug,billing_status,stripe_subscription_id FROM accounts') == [
        ('free', 'canceled', None)]


def test_connect_event_is_quarantined_without_account_change(database):
    before = query(database, 'SELECT plan_slug,billing_status,stripe_subscription_id FROM accounts')
    payload = event()
    payload['account'] = 'acct_fixture'
    normalized = normalize_verified_event(payload, expected_live=True)
    billing.store_receipt(normalized)
    assert billing.process_receipt(normalized['event_id'], True) == {
        'state': 'quarantined', 'reason': 'unsupported_account_context'}
    assert query(database, 'SELECT plan_slug,billing_status,stripe_subscription_id FROM accounts') == before
    assert query(database, 'SELECT count(*) FROM billing_subscription_cursors') == [(0,)]

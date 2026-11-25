"""LR-012 real PostgreSQL, fake authoritative Stripe; no external requests."""
import threading
import time
import pytest
from api.services import billing_events as billing, billing_reconcile as reconcile
from api.services.billing_lock import require_unbound
from api.services.billing_provider import choose_snapshot
from fastapi import HTTPException
from test_billing_events_postgres import database, envelope, query, ACCOUNT, pytestmark


def sub(ident='sub_fixture', customer='cus_fixture', price='price_pro', **kw):
    result = dict(id=ident, customer=customer, livemode=False, status='active',
                  current_period_end=int(time.time())+3600,
                  items={'data':[{'price':{'id':price}}]})
    result.update(kw)
    return result


def provider(monkeypatch, rows, has_more=False):
    monkeypatch.setattr(reconcile, 'subscriptions', lambda *a: {'data':rows,'has_more':has_more})


def process(e):
    billing.store_receipt(e)
    return billing.process_receipt(e['event_id'], e['livemode'])


def test_customer_mismatch_never_calls_stripe_or_changes_account(database, monkeypatch):
    def unexpected(*a):
        pytest.fail('provider must not be called for an unbound receipt')
    monkeypatch.setattr(reconcile, 'subscriptions', unexpected)
    assert process(envelope(customer_id='cus_foreign'))['reason'] == 'customer_mismatch'
    query(database, "UPDATE accounts SET stripe_customer_id=NULL RETURNING id")
    assert process(envelope('evt_no_binding'))['reason'] == 'customer_mismatch'
    assert query(database, 'SELECT plan_slug FROM accounts') == [('free',)]


@pytest.mark.parametrize('rows,more,reason', [
    ([sub(),sub('sub_second')],False,'multiple_subscriptions'),
    ([sub()],True,'subscription_inventory_incomplete'),
    ([sub(customer='cus_other')],False,'provider_binding_mismatch'),
    ([sub(livemode=True)],False,'provider_binding_mismatch'),
    ([sub(metadata={'account_id':'other'})],False,'provider_metadata_mismatch'),
    ([sub(cancel_at_period_end=True,current_period_end=None)],False,'period_shape_unsupported'),
])
def test_ambiguous_inventory_is_reviewed_without_mutation(database, monkeypatch, rows, more, reason):
    provider(monkeypatch, rows, more)
    assert process(envelope())['reason'] == reason
    assert query(database, 'SELECT plan_slug FROM accounts') == [('free',)]


def test_same_second_events_use_snapshot_not_arrival_body(database, monkeypatch):
    provider(monkeypatch,[sub(price='price_starter')])
    assert process(envelope('evt_z',price='price_pro'))['state'] == 'processed'
    assert process(envelope('evt_a',price='price_pro'))['state'] == 'processed'
    assert query(database,'SELECT plan_slug FROM accounts') == [('starter',)]


def test_old_subscription_deletion_cannot_revoke_current(database, monkeypatch):
    query(database,"UPDATE accounts SET plan_slug='pro',stripe_subscription_id='sub_current' RETURNING id")
    provider(monkeypatch,[sub('sub_current')])
    result=process(envelope(event_type='customer.subscription.deleted',status='canceled',period_end=1))
    assert result == {'state':'ignored','reason':'obsolete_subscription'}
    assert query(database,'SELECT plan_slug,stripe_subscription_id FROM accounts') == [('pro','sub_current')]


def test_reinstatement_clears_pending_downgrade_and_replacement_is_bound(database,monkeypatch):
    query(database,"""UPDATE accounts SET plan_slug='pro',stripe_subscription_id='sub_old',
        plan_downgrade_to='free',plan_downgrade_at=now()-interval '1 minute' RETURNING id""")
    provider(monkeypatch,[sub('sub_new')])
    assert process(envelope(subscription_id='sub_new'))['state']=='processed'
    assert query(database,'SELECT plan_slug,stripe_subscription_id,plan_downgrade_at FROM accounts') == [
        ('pro','sub_new',None)]


def test_cancellation_and_paid_downgrade_wait_for_period_end(database,monkeypatch):
    query(database,"UPDATE accounts SET plan_slug='pro' RETURNING id")
    query(database,"UPDATE plans SET market_reports_limit=1 WHERE plan_slug='starter' RETURNING plan_slug")
    provider(monkeypatch,[sub(price='price_starter')])
    assert process(envelope())['state']=='processed'
    assert query(database,'SELECT plan_slug,plan_downgrade_to FROM accounts') == [('pro','starter')]
    provider(monkeypatch,[sub(cancel_at_period_end=True)])
    assert process(envelope('evt_cancel',created=200))['state']=='processed'
    assert query(database,'SELECT plan_slug,plan_downgrade_to FROM accounts') == [('pro','free')]


def test_provider_failure_rolls_back_preserving_receipt_and_replay(database,monkeypatch):
    def fail(*a):
        raise TimeoutError('offline provider deadline')
    monkeypatch.setattr(reconcile,'subscriptions',fail)
    with pytest.raises(TimeoutError):
        process(envelope())
    assert query(database,'SELECT state FROM billing_webhook_events') == [('pending',)]
    assert query(database,'SELECT plan_slug FROM accounts') == [('free',)]
    provider(monkeypatch,[sub()])
    assert billing.process_receipt('evt_one',False,replay_reason='provider recovered')['state']=='processed'


def test_slow_provider_does_not_hold_account_row_and_serializes_other_receipts(database,monkeypatch):
    entered,release=threading.Event(),threading.Event()
    calls,errors=[],[]
    def slow(*a):
        calls.append(1);entered.set()
        assert release.wait(3)
        return {'has_more':False,'data':[sub()]}
    monkeypatch.setattr(reconcile,'subscriptions',slow)
    billing.store_receipt(envelope('evt_one'))
    billing.store_receipt(envelope('evt_two',created=200))
    def run(eid):
        try: billing.process_receipt(eid,False)
        except Exception as exc: errors.append(exc)
    a=threading.Thread(target=run,args=('evt_one',));b=threading.Thread(target=run,args=('evt_two',))
    a.start()
    try:
        assert entered.wait(2)
        with database() as (_,cur):
            cur.execute("SET LOCAL lock_timeout='100ms'")
            cur.execute('SELECT id FROM accounts FOR UPDATE')
            assert cur.fetchone()
        b.start();time.sleep(.15)
        assert len(calls)==1
    finally:
        release.set();a.join(4)
        if b.ident: b.join(4)
    assert not errors and not a.is_alive() and not b.is_alive()


def test_admin_billing_gate_and_shared_clock_projection(database):
    with database() as (_,cur):
        with pytest.raises(HTTPException) as exc:
            require_unbound(cur,ACCOUNT)
        assert exc.value.status_code==409
    assert query(database,"""SELECT effective_account_plan('pro',now()+interval '1 microsecond','free'),
        effective_account_plan('pro',now(),'free'),
        effective_account_plan('pro',now()-interval '1 microsecond','free'),
        effective_account_plan('pro',NULL,'free')""") == [('pro','free','free','pro')]


def test_api_and_worker_share_read_only_deadline_and_overrides(database,monkeypatch):
    from api.services.usage import resolve_plan_for_account
    from worker import limit_checker
    import psycopg
    from psycopg import sql
    from test_billing_events_postgres import URL
    with database() as (_,cur):
        cur.execute("SELECT current_schema()")
        schema=cur.fetchone()[0]
        cur.execute("""ALTER TABLE accounts ADD monthly_report_limit_override int,
            ADD account_type text DEFAULT 'REGULAR',ADD market_reports_limit_override int,
            ADD schedules_limit_override int,ADD property_reports_limit_override int""")
        cur.execute("""ALTER TABLE plans ADD plan_name text DEFAULT 'Fixture',ADD monthly_report_limit int DEFAULT 10,
            ADD allow_overage boolean DEFAULT false,ADD overage_price_cents int DEFAULT 0""")
        cur.execute("UPDATE plans SET monthly_report_limit=3 WHERE plan_slug='free'")
        cur.execute("CREATE TABLE report_generations(id uuid,account_id uuid,generated_at timestamptz,status text)")
        cur.execute("CREATE TABLE schedule_runs(report_run_id uuid)")
        cur.execute("CREATE TABLE property_reports(account_id uuid,created_at timestamptz,status text)")
        cur.execute("UPDATE accounts SET plan_slug='pro',plan_downgrade_to='free',plan_downgrade_at=now()-interval '1 second'")
    real_connect=psycopg.connect
    def local(*args,**kwargs):
        conn=real_connect(URL)
        conn.execute(sql.SQL('SET search_path TO {}').format(sql.Identifier(schema)))
        conn.commit()
        conn.read_only=True
        return conn
    from types import SimpleNamespace
    monkeypatch.setattr(limit_checker,'psycopg',SimpleNamespace(connect=local))
    with real_connect(URL) as c:
        c.execute(sql.SQL('SET search_path TO {}').format(sql.Identifier(schema)))
        c.execute("UPDATE accounts SET plan_downgrade_at=now()+interval '1 hour'")
    with local() as c:
        before=resolve_plan_for_account(c.cursor(),ACCOUNT)
    assert before['plan_slug']==limit_checker.check_usage_limit(ACCOUNT)['plan_slug']=='pro'
    assert before['market_reports_limit']==limit_checker.check_usage_limit(ACCOUNT)['limit']==10
    assert before['property_reports_limit']==limit_checker.check_usage_limit(ACCOUNT,'property_reports')['limit']==2
    with real_connect(URL) as c:
        c.execute(sql.SQL('SET search_path TO {}').format(sql.Identifier(schema)))
        c.execute("UPDATE accounts SET plan_downgrade_at=now()-interval '1 second'")
    assert limit_checker.check_usage_limit(ACCOUNT,'property_reports')['limit']==1
    for override,expected in [(None,3),(0,0),(99999,99999)]:
        # Updates deliberately use saved raw local connect, not the read-only worker connection.
        with real_connect(URL) as c:
            c.execute(sql.SQL('SET search_path TO {}').format(sql.Identifier(schema)))
            c.execute('UPDATE accounts SET market_reports_limit_override=%s',(override,))
        with local() as c:
            api=resolve_plan_for_account(c.cursor(),ACCOUNT)
        worker=limit_checker.check_usage_limit(ACCOUNT)
        assert api['plan_slug']==worker['plan_slug']=='free'
        assert api['market_reports_limit']==worker['limit']==expected
    with real_connect(URL) as c:
        c.execute(sql.SQL('SET search_path TO {}').format(sql.Identifier(schema)))
        assert c.execute('SELECT plan_slug,plan_downgrade_to FROM accounts').fetchone()==('pro','free')


def test_processing_budget_rolls_back_and_releases_account_lock(database,monkeypatch):
    from api.services import billing_lock
    real_budget=billing_lock.Budget
    monkeypatch.setattr(billing_lock,'Budget',lambda:real_budget(.05))
    def slow(*a):
        time.sleep(.1)
        return {'has_more':False,'data':[sub()]}
    monkeypatch.setattr(reconcile,'subscriptions',slow)
    started=time.monotonic()
    with pytest.raises(TimeoutError): process(envelope())
    assert time.monotonic()-started<.8
    assert query(database,'SELECT state FROM billing_webhook_events')==[('pending',)]
    with database() as (_,cur):
        cur.execute("SELECT pg_try_advisory_xact_lock(hashtextextended('billing_account:'||%s,0))",(ACCOUNT,))
        assert cur.fetchone()[0]
    assert query(database,'SELECT plan_slug FROM accounts')==[('free',)]


def test_first_paid_state_already_cancelling_keeps_paid_time(database,monkeypatch):
    provider(monkeypatch,[sub(cancel_at_period_end=True)])
    assert process(envelope())['state']=='processed'
    assert query(database,'SELECT plan_slug,plan_downgrade_to FROM accounts') == [('pro','free')]


def test_duplicate_customer_binding_is_held(database,monkeypatch):
    query(database,"INSERT INTO accounts(id,plan_slug) VALUES ('22222222-2222-4222-8222-222222222222','free') RETURNING id")
    monkeypatch.setattr(reconcile,'subscriptions',lambda *a:pytest.fail('ambiguous customer must not be fetched'))
    assert process(envelope())['reason']=='customer_binding_ambiguous'

"""LR-012 apply authoritative customer-bound state after the account advisory lock."""
import time
from .billing_lock import lock_account, BudgetCursor
from .billing_provider import subscriptions, choose_snapshot
from .billing_state import update_account_billing_state
from .plan_lookup import get_plan_slug_for_stripe_price


def reconcile(cur, e, cursor_guard):
    budget = lock_account(cur, e['account_id'])
    cur = BudgetCursor(cur, budget)
    # Plain read: user-facing account-row updates do not wait for the provider.
    cur.execute("SELECT stripe_customer_id,stripe_subscription_id FROM accounts WHERE id=%s::uuid",
                (e['account_id'],))
    binding = cur.fetchone()
    if not binding:
        return 'quarantined', 'account_missing', False, budget
    if not binding[0] or binding[0] != e['customer_id']:
        return 'quarantined', 'customer_mismatch', False, budget
    cur.execute('SELECT count(*) FROM accounts WHERE stripe_customer_id=%s', (binding[0],))
    if cur.fetchone()[0] != 1:
        return 'quarantined', 'customer_binding_ambiguous', False, budget
    inventory = subscriptions(binding[0], e['livemode'])
    snapshot, reason = choose_snapshot(inventory, e, binding[1])
    budget.end = min(budget.end, time.monotonic()+4)
    if cursor_guard(cur, e):
        return 'ignored', 'superseded', False, budget
    cur.execute("""SELECT stripe_customer_id,stripe_subscription_id,
        effective_account_plan(plan_slug,plan_downgrade_at,plan_downgrade_to)
        FROM accounts WHERE id=%s::uuid FOR UPDATE""", (e['account_id'],))
    current = cur.fetchone()
    if not current or current[:2] != binding:
        return 'quarantined', 'binding_changed', False, budget
    if reason:
        return 'quarantined', reason, False, budget
    if snapshot['subscription_id'] != e['subscription_id'] and snapshot['subscription_id'] == current[1]:
        return 'ignored', 'obsolete_subscription', False, budget
    terminal = snapshot['event_type'].endswith('.deleted')
    plan = 'free' if terminal else get_plan_slug_for_stripe_price(cur, snapshot['price_id'])
    if not plan:
        return 'quarantined', 'price_unmapped', False, budget
    period = snapshot['period_end']
    deferred = terminal or snapshot['cancel_at_period_end']
    lower = False
    if plan != current[2] and not terminal:
        cur.execute("""SELECT plan_slug,market_reports_limit,schedules_limit,property_reports_per_month
            FROM plans WHERE plan_slug IN (%s,%s)""", (current[2], plan))
        limits = {r[0]: r[1:] for r in cur.fetchall()}
        old, new = limits.get(current[2]), limits.get(plan)
        if old and new and all(v is not None for v in (*old, *new)):
            lower, higher = any(n < o for n,o in zip(new,old)), any(n > o for n,o in zip(new,old))
            if (lower and higher) or (not lower and not higher):
                return 'quarantined', 'plan_transition_ambiguous', False, budget
            deferred = deferred or lower
        elif current[1] is not None:
            return 'quarantined', 'plan_transition_ambiguous', False, budget
    if deferred and not period:
        return 'quarantined', 'period_shape_unsupported', False, budget
    # Cancellation and paid downgrades keep the current plan until the provider period ends.
    cur.execute('SELECT %s::bigint IS NOT NULL AND to_timestamp(%s) > now()', (period, period))
    future = cur.fetchone()[0]
    if deferred and (future or snapshot['cancel_at_period_end']):
        target = 'free' if terminal or snapshot['cancel_at_period_end'] else plan
        kept_plan = plan if snapshot['cancel_at_period_end'] and not terminal and not lower else current[2]
        cur.execute("""UPDATE accounts SET plan_slug=%s,plan_downgrade_at=to_timestamp(%s),plan_downgrade_to=%s,
            billing_status=%s,stripe_subscription_id=%s WHERE id=%s::uuid""",
            (kept_plan,period,target,'cancel_at_period_end' if target == 'free' else snapshot['status'],
             snapshot['subscription_id'],e['account_id']))
    else:
        cur.execute("""UPDATE accounts SET plan_slug=%s,plan_downgrade_at=NULL,plan_downgrade_to=NULL
            WHERE id=%s::uuid""", (plan,e['account_id']))
        update_account_billing_state(cur, account_id=e['account_id'],
            subscription=None if terminal else {'id':snapshot['subscription_id'],'status':snapshot['status']})
    cur.execute("""UPDATE billing_subscription_cursors SET created=%s,event_id=%s
        WHERE livemode=%s AND subscription_id=%s""",
        (e['created'],e['event_id'],e['livemode'],e['subscription_id']))
    return 'processed', None, True, budget

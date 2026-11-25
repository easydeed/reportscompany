"""LR-012 shared account serialization and deadline; no provider work under row locks."""
import time
from fastapi import HTTPException


class Budget:
    def __init__(self, seconds=10):
        self.end = time.monotonic() + seconds

    def limit(self, cur):
        ms = int((self.end - time.monotonic()) * 1000)
        if ms <= 0:
            raise TimeoutError('billing_deadline')
        cur.execute("SELECT set_config('statement_timeout', %s, true)", (f'{ms}ms',))


class BudgetCursor:
    def __init__(self, inner, budget):
        self.inner, self.budget = inner, budget

    def execute(self, *args, **kwargs):
        self.budget.limit(self.inner)
        return self.inner.execute(*args, **kwargs)

    def __getattr__(self, name):
        return getattr(self.inner, name)


def lock_account(cur, account_id):
    cur.execute("SET LOCAL lock_timeout = '2s'")
    cur.execute("SELECT pg_advisory_xact_lock(hashtextextended('billing_account:' || %s::text, 0))",
                (str(account_id),))
    return Budget()


def require_unbound(cur, account_id):
    """Plan-edit gate; lock BEFORE any update/row lock, recheck after acquisition."""
    budget = lock_account(cur, account_id)
    budget.limit(cur)
    cur.execute("SELECT stripe_customer_id,stripe_subscription_id FROM accounts WHERE id=%s::uuid FOR UPDATE",
                (str(account_id),))
    row = cur.fetchone()
    if row and any(row):
        raise HTTPException(status_code=409, detail='Stripe-bound plans must be changed through billing')
    return budget

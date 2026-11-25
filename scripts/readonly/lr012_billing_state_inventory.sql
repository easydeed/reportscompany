-- LR-012 preflight: counts only, no customer/subscription identifiers.
-- This inventory does not change plans, bindings, or deferred downgrades.
BEGIN READ ONLY;
SELECT billing_status,
       count(*) AS accounts,
       count(*) FILTER (WHERE stripe_customer_id IS NULL) AS missing_customer,
       count(*) FILTER (WHERE stripe_subscription_id IS NULL) AS missing_subscription,
       count(*) FILTER (WHERE plan_downgrade_at IS NOT NULL) AS deferred,
       count(*) FILTER (WHERE plan_downgrade_at <= now()) AS deferred_due
FROM accounts
WHERE stripe_customer_id IS NOT NULL
   OR stripe_subscription_id IS NOT NULL
   OR plan_downgrade_at IS NOT NULL
GROUP BY billing_status
ORDER BY billing_status;

SELECT count(*) AS duplicate_customer_bindings
FROM (
    SELECT stripe_customer_id
    FROM accounts
    WHERE stripe_customer_id IS NOT NULL
    GROUP BY stripe_customer_id
    HAVING count(*) > 1
) duplicates;
SELECT count(*) FILTER (WHERE plan_slug IN (SELECT plan_slug FROM plans WHERE stripe_price_id IS NOT NULL) AND stripe_subscription_id IS NULL) AS paid_without_subscription,
       count(*) FILTER (WHERE plan_slug IN ('free','sponsored_free') AND stripe_subscription_id IS NOT NULL) AS free_with_subscription,
       count(*) FILTER (WHERE billing_status = 'active' AND plan_downgrade_at <= now()) AS active_with_due_downgrade
FROM accounts;

SELECT a.plan_slug, count(*) AS accounts,
       count(*) FILTER (WHERE a.stripe_subscription_id IS NULL) AS without_subscription
FROM accounts a JOIN plans p ON p.plan_slug = a.plan_slug
WHERE p.stripe_price_id IS NOT NULL
GROUP BY a.plan_slug ORDER BY a.plan_slug;

SELECT state, reason, count(*) AS events
FROM billing_webhook_events
GROUP BY state, reason
ORDER BY state, reason;
COMMIT;

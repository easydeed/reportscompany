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
COMMIT;

-- db/check_production_demo_accounts.sql
-- Check all 5 production demo accounts

SELECT
  u.email,
  u.role AS user_role,
  u.account_id::text,
  a.name AS account_name,
  a.account_type,
  a.plan_slug,
  a.sponsor_account_id::text AS sponsor_id
FROM users u
JOIN accounts a ON a.id = u.account_id
WHERE u.email IN (
  'admin@trendyreports-demo.com',
  'agent-free@trendyreports-demo.com',
  'agent-pro@trendyreports-demo.com',
  'affiliate@trendyreports-demo.com',
  'agent-sponsored@trendyreports-demo.com'
)
ORDER BY u.email;


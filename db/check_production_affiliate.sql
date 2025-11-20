-- Check if affiliate@trendyreports-demo.com exists and what their account type is
SELECT 
  u.email,
  u.role AS user_role,
  u.account_id::text,
  a.name AS account_name,
  a.account_type,
  a.plan_slug,
  a.sponsor_account_id::text AS sponsor_id
FROM users u
LEFT JOIN accounts a ON a.id = u.account_id
WHERE u.email = 'affiliate@trendyreports-demo.com';

-- Also check all accounts this user has access to
SELECT 
  a.id::text AS account_id,
  a.name,
  a.account_type,
  a.plan_slug,
  au.role AS user_role_in_account
FROM account_users au
JOIN accounts a ON a.id = au.account_id
JOIN users u ON u.id = au.user_id
WHERE u.email = 'affiliate@trendyreports-demo.com';


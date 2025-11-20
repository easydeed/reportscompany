-- Fix the affiliate@trendyreports-demo.com account in production
-- This updates the account to have the correct account_type and plan_slug

BEGIN;

-- Update the user's role to MEMBER (not ADMIN)
UPDATE users
SET role = 'MEMBER'
WHERE email = 'affiliate@trendyreports-demo.com';

-- Update the account to be INDUSTRY_AFFILIATE
UPDATE accounts
SET 
  account_type = 'INDUSTRY_AFFILIATE',
  plan_slug = 'affiliate',
  name = 'Demo Title Company'
WHERE id = (
  SELECT account_id 
  FROM users 
  WHERE email = 'affiliate@trendyreports-demo.com'
);

COMMIT;

-- Verify the fix
SELECT 
  u.email,
  u.role AS user_role,
  a.name AS account_name,
  a.account_type,
  a.plan_slug
FROM users u
JOIN accounts a ON a.id = u.account_id
WHERE u.email = 'affiliate@trendyreports-demo.com';


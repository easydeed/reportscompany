-- Verify Affiliate Account Context
-- Run this to check if affiliate user is properly linked to an INDUSTRY_AFFILIATE account

-- Step 1: Check affiliate user's accounts
SELECT 
  u.email AS user_email,
  a.id AS account_id,
  a.name AS account_name,
  a.account_type,
  a.plan_slug,
  au.role AS user_role_in_account,
  CASE 
    WHEN a.account_type = 'INDUSTRY_AFFILIATE' THEN '✅ CORRECT'
    ELSE '❌ WRONG - Should be INDUSTRY_AFFILIATE'
  END AS status
FROM users u
JOIN account_users au ON au.user_id = u.id
JOIN accounts a ON a.id = au.account_id
WHERE u.email = 'affiliate@trendyreports-demo.com'
ORDER BY 
  CASE WHEN a.account_type = 'INDUSTRY_AFFILIATE' THEN 1 ELSE 2 END;

-- Step 2: Check if affiliate has the correct default account
SELECT 
  u.email,
  u.account_id AS default_account_id,
  a.account_type AS default_account_type,
  a.plan_slug AS default_plan,
  CASE 
    WHEN a.account_type = 'INDUSTRY_AFFILIATE' THEN '✅ Default is affiliate account'
    ELSE '⚠️ Default is NOT affiliate account (will need login to prioritize)'
  END AS default_status
FROM users u
JOIN accounts a ON a.id = u.account_id
WHERE u.email = 'affiliate@trendyreports-demo.com';

-- Step 3: Show all accounts for affiliate user (to understand relationships)
SELECT 
  'All accounts for affiliate user:' AS info,
  a.id,
  a.name,
  a.account_type,
  a.plan_slug,
  au.role
FROM users u
JOIN account_users au ON au.user_id = u.id
JOIN accounts a ON a.id = au.account_id
WHERE u.email = 'affiliate@trendyreports-demo.com';

-- Step 4: Check sponsored agent for comparison
SELECT 
  'Sponsored agent account:' AS info,
  u.email AS user_email,
  a.id AS account_id,
  a.name AS account_name,
  a.account_type,
  a.plan_slug,
  a.sponsor_account_id,
  CASE 
    WHEN a.account_type = 'REGULAR' AND a.sponsor_account_id IS NOT NULL THEN '✅ CORRECT'
    ELSE '❌ Should be REGULAR with sponsor_account_id'
  END AS status
FROM users u
JOIN accounts a ON a.id = u.account_id
WHERE u.email = 'agent-sponsored@trendyreports-demo.com';


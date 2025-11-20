-- Verify Demo Account Types
-- Run this to check if demo accounts have correct account_type values

-- Step 1: Check all demo accounts
SELECT 
  a.id,
  a.name,
  a.account_type,
  a.plan_slug,
  u.email,
  CASE 
    WHEN a.account_type = 'INDUSTRY_AFFILIATE' AND a.plan_slug = 'affiliate' THEN '✅ Correct'
    WHEN a.account_type = 'REGULAR' AND a.plan_slug IN ('free', 'pro', 'sponsored_free') THEN '✅ Correct'
    ELSE '❌ NEEDS FIX'
  END AS status
FROM accounts a
LEFT JOIN users u ON u.account_id = a.id
WHERE u.email LIKE '%@trendyreports-demo.com'
ORDER BY 
  CASE 
    WHEN a.account_type = 'INDUSTRY_AFFILIATE' THEN 1
    WHEN a.plan_slug = 'sponsored_free' THEN 2
    ELSE 3
  END,
  u.email;

-- Step 2: Show expected vs actual
SELECT 
  u.email,
  a.name AS account_name,
  a.account_type AS current_account_type,
  CASE 
    WHEN u.email = 'affiliate@trendyreports-demo.com' THEN 'INDUSTRY_AFFILIATE'
    ELSE 'REGULAR'
  END AS expected_account_type,
  a.plan_slug AS current_plan,
  CASE 
    WHEN u.email = 'admin@trendyreports-demo.com' THEN 'free'
    WHEN u.email = 'agent-free@trendyreports-demo.com' THEN 'free'
    WHEN u.email = 'agent-pro@trendyreports-demo.com' THEN 'pro'
    WHEN u.email = 'affiliate@trendyreports-demo.com' THEN 'affiliate'
    WHEN u.email = 'agent-sponsored@trendyreports-demo.com' THEN 'sponsored_free'
  END AS expected_plan
FROM users u
JOIN accounts a ON a.id = u.account_id
WHERE u.email LIKE '%@trendyreports-demo.com'
ORDER BY u.email;


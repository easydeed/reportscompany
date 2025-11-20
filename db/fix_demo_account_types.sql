-- Fix Demo Account Types
-- Run this ONLY if verify_demo_account_types.sql shows incorrect values
-- This ensures affiliate account has INDUSTRY_AFFILIATE type

BEGIN;

-- Update affiliate account to INDUSTRY_AFFILIATE type
UPDATE accounts
SET 
  account_type = 'INDUSTRY_AFFILIATE',
  plan_slug = 'affiliate'
FROM users u
WHERE 
  accounts.id = u.account_id
  AND u.email = 'affiliate@trendyreports-demo.com';

-- Ensure sponsored agent account is REGULAR with sponsored_free plan
UPDATE accounts
SET 
  account_type = 'REGULAR',
  plan_slug = 'sponsored_free'
FROM users u
WHERE 
  accounts.id = u.account_id
  AND u.email = 'agent-sponsored@trendyreports-demo.com';

-- Verify the changes
SELECT 
  u.email,
  a.name,
  a.account_type,
  a.plan_slug,
  CASE 
    WHEN u.email = 'affiliate@trendyreports-demo.com' 
         AND a.account_type = 'INDUSTRY_AFFILIATE' 
         AND a.plan_slug = 'affiliate' THEN '✅ Fixed'
    WHEN u.email = 'agent-sponsored@trendyreports-demo.com' 
         AND a.account_type = 'REGULAR' 
         AND a.plan_slug = 'sponsored_free' THEN '✅ Fixed'
    ELSE '❌ Still incorrect'
  END AS status
FROM users u
JOIN accounts a ON a.id = u.account_id
WHERE u.email IN ('affiliate@trendyreports-demo.com', 'agent-sponsored@trendyreports-demo.com');

-- If everything looks good, commit:
COMMIT;

-- If something looks wrong, rollback:
-- ROLLBACK;


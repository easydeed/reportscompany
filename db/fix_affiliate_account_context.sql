-- Fix Affiliate Account Context
-- Run this ONLY if verify_affiliate_account_context.sql shows issues

BEGIN;

-- Step 1: Find the affiliate account ID
DO $$
DECLARE
  v_affiliate_user_id uuid;
  v_affiliate_account_id uuid;
  v_demo_title_account_id uuid;
BEGIN
  -- Get the affiliate user ID
  SELECT id INTO v_affiliate_user_id
  FROM users
  WHERE email = 'affiliate@trendyreports-demo.com';
  
  IF v_affiliate_user_id IS NULL THEN
    RAISE EXCEPTION 'Affiliate user not found';
  END IF;
  
  -- Find or create the INDUSTRY_AFFILIATE account
  SELECT a.id INTO v_affiliate_account_id
  FROM accounts a
  JOIN account_users au ON au.account_id = a.id
  WHERE au.user_id = v_affiliate_user_id
    AND a.account_type = 'INDUSTRY_AFFILIATE'
  LIMIT 1;
  
  -- If no affiliate account exists, find "Demo Title Company" or create one
  IF v_affiliate_account_id IS NULL THEN
    RAISE NOTICE 'No INDUSTRY_AFFILIATE account found for user, checking for Demo Title Company...';
    
    SELECT id INTO v_demo_title_account_id
    FROM accounts
    WHERE name = 'Demo Title Company'
      AND account_type = 'INDUSTRY_AFFILIATE';
    
    IF v_demo_title_account_id IS NOT NULL THEN
      -- Link user to existing Demo Title Company
      RAISE NOTICE 'Linking affiliate user to existing Demo Title Company account';
      INSERT INTO account_users (account_id, user_id, role)
      VALUES (v_demo_title_account_id, v_affiliate_user_id, 'OWNER')
      ON CONFLICT DO NOTHING;
      
      v_affiliate_account_id := v_demo_title_account_id;
    ELSE
      RAISE EXCEPTION 'No INDUSTRY_AFFILIATE account found. Run db/seed_demo_accounts_v2.sql first.';
    END IF;
  END IF;
  
  -- Step 2: Update users.account_id to point to the affiliate account
  UPDATE users
  SET account_id = v_affiliate_account_id
  WHERE id = v_affiliate_user_id;
  
  RAISE NOTICE 'Set default account to % for affiliate user', v_affiliate_account_id;
  
  -- Step 3: Ensure account is INDUSTRY_AFFILIATE type
  UPDATE accounts
  SET 
    account_type = 'INDUSTRY_AFFILIATE',
    plan_slug = 'affiliate'
  WHERE id = v_affiliate_account_id
    AND (account_type != 'INDUSTRY_AFFILIATE' OR plan_slug != 'affiliate');
  
  RAISE NOTICE 'Ensured account % is INDUSTRY_AFFILIATE with affiliate plan', v_affiliate_account_id;
  
END $$;

-- Verify the fix
SELECT 
  'After fix:' AS status,
  u.email,
  a.name AS default_account_name,
  a.account_type,
  a.plan_slug
FROM users u
JOIN accounts a ON a.id = u.account_id
WHERE u.email = 'affiliate@trendyreports-demo.com';

-- If everything looks good, commit:
COMMIT;

-- If something looks wrong, rollback:
-- ROLLBACK;


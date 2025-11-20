-- seed_demo_accounts_prod.sql
-- WARNING: This script is for PRODUCTION DEMO ACCOUNTS ONLY.
-- It creates/repairs these users and accounts:
--  - admin@trendyreports-demo.com
--  - agent-free@trendyreports-demo.com
--  - agent-pro@trendyreports-demo.com
--  - affiliate@trendyreports-demo.com
--  - agent-sponsored@trendyreports-demo.com
-- All passwords are demo-only and can be rotated by rerunning or manual edits.
--
-- This script is IDEMPOTENT - safe to run multiple times.

BEGIN;

-- Enable pgcrypto for password hashing if not already enabled
CREATE EXTENSION IF NOT EXISTS pgcrypto;

-- 1) INSERT USERS (with ON CONFLICT to make idempotent)

-- Admin
INSERT INTO users (email, password_hash, role, is_active)
VALUES (
  'admin@trendyreports-demo.com',
  crypt('DemoAdmin123!', gen_salt('bf')),
  'ADMIN',
  TRUE
)
ON CONFLICT (email) DO UPDATE
SET 
  password_hash = crypt('DemoAdmin123!', gen_salt('bf')),
  role = 'ADMIN',
  is_active = TRUE;

-- Free Agent
INSERT INTO users (email, password_hash, role, is_active)
VALUES (
  'agent-free@trendyreports-demo.com',
  crypt('DemoAgent123!', gen_salt('bf')),
  'MEMBER',
  TRUE
)
ON CONFLICT (email) DO UPDATE
SET 
  password_hash = crypt('DemoAgent123!', gen_salt('bf')),
  role = 'MEMBER',
  is_active = TRUE;

-- Pro Agent
INSERT INTO users (email, password_hash, role, is_active)
VALUES (
  'agent-pro@trendyreports-demo.com',
  crypt('DemoAgent123!', gen_salt('bf')),
  'MEMBER',
  TRUE
)
ON CONFLICT (email) DO UPDATE
SET 
  password_hash = crypt('DemoAgent123!', gen_salt('bf')),
  role = 'MEMBER',
  is_active = TRUE;

-- Affiliate
INSERT INTO users (email, password_hash, role, is_active)
VALUES (
  'affiliate@trendyreports-demo.com',
  crypt('DemoAff123!', gen_salt('bf')),
  'MEMBER',
  TRUE
)
ON CONFLICT (email) DO UPDATE
SET 
  password_hash = crypt('DemoAff123!', gen_salt('bf')),
  role = 'MEMBER',
  is_active = TRUE;

-- Sponsored Agent
INSERT INTO users (email, password_hash, role, is_active)
VALUES (
  'agent-sponsored@trendyreports-demo.com',
  crypt('DemoAgent123!', gen_salt('bf')),
  'MEMBER',
  TRUE
)
ON CONFLICT (email) DO UPDATE
SET 
  password_hash = crypt('DemoAgent123!', gen_salt('bf')),
  role = 'MEMBER',
  is_active = TRUE;

-- 2) CREATE ACCOUNTS AND LINK USERS

-- ========================================
-- ADMIN ACCOUNT
-- ========================================
DO $$
DECLARE
  v_admin_user_id uuid;
  v_admin_account_id uuid;
BEGIN
  -- Get admin user ID
  SELECT id INTO v_admin_user_id
  FROM users
  WHERE email = 'admin@trendyreports-demo.com';

  IF v_admin_user_id IS NULL THEN
    RAISE EXCEPTION 'Admin user not found after insert.';
  END IF;

  -- Look for existing admin account
  SELECT a.id INTO v_admin_account_id
  FROM accounts a
  JOIN account_users au ON au.account_id = a.id
  WHERE au.user_id = v_admin_user_id
    AND a.name = 'TrendyReports Admin'
  LIMIT 1;

  -- Create account if doesn't exist
  IF v_admin_account_id IS NULL THEN
    INSERT INTO accounts (name, account_type, plan_slug)
    VALUES ('TrendyReports Admin', 'REGULAR', 'pro')
    RETURNING id INTO v_admin_account_id;
    
    RAISE NOTICE 'Created admin account: %', v_admin_account_id;
  ELSE
    -- Ensure account has correct settings
    UPDATE accounts
    SET account_type = 'REGULAR', plan_slug = 'pro'
    WHERE id = v_admin_account_id;
    
    RAISE NOTICE 'Found existing admin account: %', v_admin_account_id;
  END IF;

  -- Link user to account
  INSERT INTO account_users (account_id, user_id, role)
  VALUES (v_admin_account_id, v_admin_user_id, 'OWNER')
  ON CONFLICT (account_id, user_id) DO UPDATE
  SET role = 'OWNER';

  -- Set as user's default account
  UPDATE users
  SET account_id = v_admin_account_id
  WHERE id = v_admin_user_id;

  RAISE NOTICE 'Admin user linked to account';
END $$;

-- ========================================
-- FREE AGENT ACCOUNT
-- ========================================
DO $$
DECLARE
  v_free_user_id uuid;
  v_free_account_id uuid;
BEGIN
  SELECT id INTO v_free_user_id
  FROM users
  WHERE email = 'agent-free@trendyreports-demo.com';

  IF v_free_user_id IS NULL THEN
    RAISE EXCEPTION 'Free agent user not found.';
  END IF;

  -- Look for existing free account
  SELECT a.id INTO v_free_account_id
  FROM accounts a
  JOIN account_users au ON au.account_id = a.id
  WHERE au.user_id = v_free_user_id
    AND a.name = 'Demo Free Agent'
  LIMIT 1;

  IF v_free_account_id IS NULL THEN
    INSERT INTO accounts (name, account_type, plan_slug)
    VALUES ('Demo Free Agent', 'REGULAR', 'free')
    RETURNING id INTO v_free_account_id;
    
    RAISE NOTICE 'Created free agent account: %', v_free_account_id;
  ELSE
    UPDATE accounts
    SET account_type = 'REGULAR', plan_slug = 'free'
    WHERE id = v_free_account_id;
    
    RAISE NOTICE 'Found existing free agent account: %', v_free_account_id;
  END IF;

  INSERT INTO account_users (account_id, user_id, role)
  VALUES (v_free_account_id, v_free_user_id, 'OWNER')
  ON CONFLICT (account_id, user_id) DO UPDATE
  SET role = 'OWNER';

  UPDATE users
  SET account_id = v_free_account_id
  WHERE id = v_free_user_id;

  RAISE NOTICE 'Free agent user linked to account';
END $$;

-- ========================================
-- PRO AGENT ACCOUNT
-- ========================================
DO $$
DECLARE
  v_pro_user_id uuid;
  v_pro_account_id uuid;
BEGIN
  SELECT id INTO v_pro_user_id
  FROM users
  WHERE email = 'agent-pro@trendyreports-demo.com';

  IF v_pro_user_id IS NULL THEN
    RAISE EXCEPTION 'Pro agent user not found.';
  END IF;

  -- Look for existing pro account
  SELECT a.id INTO v_pro_account_id
  FROM accounts a
  JOIN account_users au ON au.account_id = a.id
  WHERE au.user_id = v_pro_user_id
    AND a.name = 'Demo Pro Agent'
  LIMIT 1;

  IF v_pro_account_id IS NULL THEN
    INSERT INTO accounts (name, account_type, plan_slug)
    VALUES ('Demo Pro Agent', 'REGULAR', 'pro')
    RETURNING id INTO v_pro_account_id;
    
    RAISE NOTICE 'Created pro agent account: %', v_pro_account_id;
  ELSE
    UPDATE accounts
    SET account_type = 'REGULAR', plan_slug = 'pro'
    WHERE id = v_pro_account_id;
    
    RAISE NOTICE 'Found existing pro agent account: %', v_pro_account_id;
  END IF;

  INSERT INTO account_users (account_id, user_id, role)
  VALUES (v_pro_account_id, v_pro_user_id, 'OWNER')
  ON CONFLICT (account_id, user_id) DO UPDATE
  SET role = 'OWNER';

  UPDATE users
  SET account_id = v_pro_account_id
  WHERE id = v_pro_user_id;

  RAISE NOTICE 'Pro agent user linked to account';
END $$;

-- ========================================
-- AFFILIATE ACCOUNT
-- ========================================
DO $$
DECLARE
  v_aff_user_id uuid;
  v_aff_account_id uuid;
BEGIN
  SELECT id INTO v_aff_user_id
  FROM users
  WHERE email = 'affiliate@trendyreports-demo.com';

  IF v_aff_user_id IS NULL THEN
    RAISE EXCEPTION 'Affiliate user not found.';
  END IF;

  -- Look for existing affiliate account
  SELECT a.id INTO v_aff_account_id
  FROM accounts a
  JOIN account_users au ON au.account_id = a.id
  WHERE au.user_id = v_aff_user_id
    AND a.account_type = 'INDUSTRY_AFFILIATE'
    AND a.name = 'Demo Title Company'
  LIMIT 1;

  IF v_aff_account_id IS NULL THEN
    INSERT INTO accounts (name, account_type, plan_slug)
    VALUES ('Demo Title Company', 'INDUSTRY_AFFILIATE', 'affiliate')
    RETURNING id INTO v_aff_account_id;
    
    RAISE NOTICE 'Created affiliate account: %', v_aff_account_id;
  ELSE
    UPDATE accounts
    SET account_type = 'INDUSTRY_AFFILIATE', plan_slug = 'affiliate'
    WHERE id = v_aff_account_id;
    
    RAISE NOTICE 'Found existing affiliate account: %', v_aff_account_id;
  END IF;

  INSERT INTO account_users (account_id, user_id, role)
  VALUES (v_aff_account_id, v_aff_user_id, 'OWNER')
  ON CONFLICT (account_id, user_id) DO UPDATE
  SET role = 'OWNER';

  UPDATE users
  SET account_id = v_aff_account_id
  WHERE id = v_aff_user_id;

  RAISE NOTICE 'Affiliate user linked to account';
END $$;

-- ========================================
-- SPONSORED AGENT ACCOUNT
-- ========================================
DO $$
DECLARE
  v_sp_user_id uuid;
  v_aff_account_id uuid;
  v_sp_account_id uuid;
BEGIN
  SELECT id INTO v_sp_user_id
  FROM users
  WHERE email = 'agent-sponsored@trendyreports-demo.com';

  IF v_sp_user_id IS NULL THEN
    RAISE EXCEPTION 'Sponsored agent user not found.';
  END IF;

  -- Get affiliate account ID
  SELECT account_id INTO v_aff_account_id
  FROM users
  WHERE email = 'affiliate@trendyreports-demo.com';

  IF v_aff_account_id IS NULL THEN
    RAISE EXCEPTION 'Affiliate default account not found. Run affiliate block first.';
  END IF;

  -- Look for existing sponsored account
  SELECT a.id INTO v_sp_account_id
  FROM accounts a
  JOIN account_users au ON au.account_id = a.id
  WHERE au.user_id = v_sp_user_id
    AND a.name = 'Demo Sponsored Agent'
  LIMIT 1;

  IF v_sp_account_id IS NULL THEN
    INSERT INTO accounts (name, account_type, plan_slug, sponsor_account_id)
    VALUES ('Demo Sponsored Agent', 'REGULAR', 'sponsored_free', v_aff_account_id)
    RETURNING id INTO v_sp_account_id;
    
    RAISE NOTICE 'Created sponsored agent account: %', v_sp_account_id;
  ELSE
    UPDATE accounts
    SET 
      account_type = 'REGULAR',
      plan_slug = 'sponsored_free',
      sponsor_account_id = v_aff_account_id
    WHERE id = v_sp_account_id;
    
    RAISE NOTICE 'Found existing sponsored agent account: %', v_sp_account_id;
  END IF;

  INSERT INTO account_users (account_id, user_id, role)
  VALUES (v_sp_account_id, v_sp_user_id, 'OWNER')
  ON CONFLICT (account_id, user_id) DO UPDATE
  SET role = 'OWNER';

  UPDATE users
  SET account_id = v_sp_account_id
  WHERE id = v_sp_user_id;

  RAISE NOTICE 'Sponsored agent user linked to account (sponsored by affiliate: %)', v_aff_account_id;
END $$;

-- 3) VERIFICATION
SELECT 
  '✅ Demo accounts created/updated successfully' AS status,
  u.email,
  u.role AS user_role,
  a.name AS account_name,
  a.account_type,
  a.plan_slug,
  CASE 
    WHEN a.sponsor_account_id IS NOT NULL THEN '(sponsored)'
    ELSE ''
  END AS sponsor_status
FROM users u
JOIN accounts a ON a.id = u.account_id
WHERE u.email IN (
  'admin@trendyreports-demo.com',
  'agent-free@trendyreports-demo.com',
  'agent-pro@trendyreports-demo.com',
  'affiliate@trendyreports-demo.com',
  'agent-sponsored@trendyreports-demo.com'
)
ORDER BY 
  CASE 
    WHEN u.email = 'admin@trendyreports-demo.com' THEN 1
    WHEN u.email = 'agent-free@trendyreports-demo.com' THEN 2
    WHEN u.email = 'agent-pro@trendyreports-demo.com' THEN 3
    WHEN u.email = 'affiliate@trendyreports-demo.com' THEN 4
    WHEN u.email = 'agent-sponsored@trendyreports-demo.com' THEN 5
  END;

COMMIT;


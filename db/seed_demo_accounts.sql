-- =====================================================
-- DEMO ACCOUNTS SEED SCRIPT (STAGING ONLY)
-- =====================================================
-- Purpose: Create 5 canonical demo accounts for staging demos, QA, and investor walkthroughs
-- WARNING: DO NOT RUN THIS ON PRODUCTION DATABASE
-- Last Updated: November 15, 2025
-- =====================================================

-- Ensure pgcrypto extension is available for password hashing
CREATE EXTENSION IF NOT EXISTS pgcrypto;

-- =====================================================
-- 1. CREATE DEMO USERS
-- =====================================================

-- ADMIN User
INSERT INTO users (email, password_hash, role, created_at, updated_at)
VALUES (
  'admin@trendyreports-demo.com',
  crypt('DemoAdmin123!', gen_salt('bf')),
  'ADMIN',
  NOW(),
  NOW()
)
ON CONFLICT (email) DO UPDATE
  SET password_hash = crypt('DemoAdmin123!', gen_salt('bf')),
      role = 'ADMIN',
      updated_at = NOW();

-- REGULAR FREE AGENT User
INSERT INTO users (email, password_hash, role, created_at, updated_at)
VALUES (
  'agent-free@trendyreports-demo.com',
  crypt('DemoAgent123!', gen_salt('bf')),
  'MEMBER',
  NOW(),
  NOW()
)
ON CONFLICT (email) DO UPDATE
  SET password_hash = crypt('DemoAgent123!', gen_salt('bf')),
      role = 'MEMBER',
      updated_at = NOW();

-- REGULAR PRO AGENT User
INSERT INTO users (email, password_hash, role, created_at, updated_at)
VALUES (
  'agent-pro@trendyreports-demo.com',
  crypt('DemoAgent123!', gen_salt('bf')),
  'MEMBER',
  NOW(),
  NOW()
)
ON CONFLICT (email) DO UPDATE
  SET password_hash = crypt('DemoAgent123!', gen_salt('bf')),
      role = 'MEMBER',
      updated_at = NOW();

-- INDUSTRY AFFILIATE User
INSERT INTO users (email, password_hash, role, created_at, updated_at)
VALUES (
  'affiliate@trendyreports-demo.com',
  crypt('DemoAff123!', gen_salt('bf')),
  'MEMBER',
  NOW(),
  NOW()
)
ON CONFLICT (email) DO UPDATE
  SET password_hash = crypt('DemoAff123!', gen_salt('bf')),
      role = 'MEMBER',
      updated_at = NOW();

-- SPONSORED AGENT User
INSERT INTO users (email, password_hash, role, created_at, updated_at)
VALUES (
  'agent-sponsored@trendyreports-demo.com',
  crypt('DemoAgent123!', gen_salt('bf')),
  'MEMBER',
  NOW(),
  NOW()
)
ON CONFLICT (email) DO UPDATE
  SET password_hash = crypt('DemoAgent123!', gen_salt('bf')),
      role = 'MEMBER',
      updated_at = NOW();

-- =====================================================
-- 2. CREATE DEMO ACCOUNTS
-- =====================================================

-- ADMIN Account (for admin metrics/config)
INSERT INTO accounts (name, account_type, plan_slug, monthly_report_limit_override, created_at, updated_at)
VALUES (
  'Admin Organization',
  'REGULAR',  -- Using REGULAR but user has ADMIN role
  'free',
  NULL,
  NOW(),
  NOW()
)
ON CONFLICT DO NOTHING
RETURNING id;

-- Store admin account ID for later use
DO $$
DECLARE
  admin_account_id UUID;
  admin_user_id UUID;
  free_agent_account_id UUID;
  free_agent_user_id UUID;
  pro_agent_account_id UUID;
  pro_agent_user_id UUID;
  affiliate_account_id UUID;
  affiliate_user_id UUID;
  sponsored_agent_account_id UUID;
  sponsored_agent_user_id UUID;
BEGIN
  -- Get user IDs
  SELECT id INTO admin_user_id FROM users WHERE email = 'admin@trendyreports-demo.com';
  SELECT id INTO free_agent_user_id FROM users WHERE email = 'agent-free@trendyreports-demo.com';
  SELECT id INTO pro_agent_user_id FROM users WHERE email = 'agent-pro@trendyreports-demo.com';
  SELECT id INTO affiliate_user_id FROM users WHERE email = 'affiliate@trendyreports-demo.com';
  SELECT id INTO sponsored_agent_user_id FROM users WHERE email = 'agent-sponsored@trendyreports-demo.com';

  -- Get or create admin account
  SELECT id INTO admin_account_id FROM accounts WHERE name = 'Admin Organization';
  IF admin_account_id IS NULL THEN
    INSERT INTO accounts (name, account_type, plan_slug, monthly_report_limit_override)
    VALUES ('Admin Organization', 'REGULAR', 'free', NULL)
    RETURNING id INTO admin_account_id;
  END IF;

  -- REGULAR FREE AGENT Account
  SELECT id INTO free_agent_account_id FROM accounts WHERE name = 'Demo Free Agent';
  IF free_agent_account_id IS NULL THEN
    INSERT INTO accounts (name, account_type, plan_slug, monthly_report_limit_override)
    VALUES ('Demo Free Agent', 'REGULAR', 'free', NULL)
    RETURNING id INTO free_agent_account_id;
  ELSE
    UPDATE accounts SET account_type = 'REGULAR', plan_slug = 'free' WHERE id = free_agent_account_id;
  END IF;

  -- REGULAR PRO AGENT Account
  SELECT id INTO pro_agent_account_id FROM accounts WHERE name = 'Demo Pro Agent';
  IF pro_agent_account_id IS NULL THEN
    INSERT INTO accounts (name, account_type, plan_slug, monthly_report_limit_override)
    VALUES ('Demo Pro Agent', 'REGULAR', 'pro', NULL)
    RETURNING id INTO pro_agent_account_id;
  ELSE
    UPDATE accounts SET account_type = 'REGULAR', plan_slug = 'pro' WHERE id = pro_agent_account_id;
  END IF;

  -- INDUSTRY AFFILIATE Account
  SELECT id INTO affiliate_account_id FROM accounts WHERE name = 'Demo Title Company';
  IF affiliate_account_id IS NULL THEN
    INSERT INTO accounts (name, account_type, plan_slug, monthly_report_limit_override)
    VALUES ('Demo Title Company', 'INDUSTRY_AFFILIATE', 'affiliate', NULL)
    RETURNING id INTO affiliate_account_id;
  ELSE
    UPDATE accounts SET account_type = 'INDUSTRY_AFFILIATE', plan_slug = 'affiliate' WHERE id = affiliate_account_id;
  END IF;

  -- SPONSORED AGENT Account (sponsored by affiliate)
  SELECT id INTO sponsored_agent_account_id FROM accounts WHERE name = 'Demo Sponsored Agent';
  IF sponsored_agent_account_id IS NULL THEN
    INSERT INTO accounts (name, account_type, plan_slug, sponsor_account_id, monthly_report_limit_override)
    VALUES ('Demo Sponsored Agent', 'REGULAR', 'sponsored_free', affiliate_account_id, NULL)
    RETURNING id INTO sponsored_agent_account_id;
  ELSE
    UPDATE accounts 
    SET account_type = 'REGULAR', 
        plan_slug = 'sponsored_free', 
        sponsor_account_id = affiliate_account_id 
    WHERE id = sponsored_agent_account_id;
  END IF;

  -- =====================================================
  -- 3. LINK USERS TO ACCOUNTS (account_users)
  -- =====================================================

  -- Admin → Admin Organization
  INSERT INTO account_users (account_id, user_id, role, created_at)
  VALUES (admin_account_id, admin_user_id, 'OWNER', NOW())
  ON CONFLICT (account_id, user_id) DO UPDATE SET role = 'OWNER';

  -- Free Agent → Free Agent Account
  INSERT INTO account_users (account_id, user_id, role, created_at)
  VALUES (free_agent_account_id, free_agent_user_id, 'OWNER', NOW())
  ON CONFLICT (account_id, user_id) DO UPDATE SET role = 'OWNER';

  -- Pro Agent → Pro Agent Account
  INSERT INTO account_users (account_id, user_id, role, created_at)
  VALUES (pro_agent_account_id, pro_agent_user_id, 'OWNER', NOW())
  ON CONFLICT (account_id, user_id) DO UPDATE SET role = 'OWNER';

  -- Affiliate → Affiliate Account
  INSERT INTO account_users (account_id, user_id, role, created_at)
  VALUES (affiliate_account_id, affiliate_user_id, 'OWNER', NOW())
  ON CONFLICT (account_id, user_id) DO UPDATE SET role = 'OWNER';

  -- Sponsored Agent → Sponsored Agent Account
  INSERT INTO account_users (account_id, user_id, role, created_at)
  VALUES (sponsored_agent_account_id, sponsored_agent_user_id, 'OWNER', NOW())
  ON CONFLICT (account_id, user_id) DO UPDATE SET role = 'OWNER';

  -- =====================================================
  -- 4. ADD AFFILIATE BRANDING (Optional, for demo polish)
  -- =====================================================

  INSERT INTO affiliate_branding (
    account_id,
    brand_name,
    brand_tagline,
    brand_primary_color,
    brand_logo_url,
    created_at,
    updated_at
  )
  VALUES (
    affiliate_account_id,
    'Demo Title Company',
    'Your Trusted Real Estate Partner',
    '#1e40af',  -- Blue
    NULL,  -- Can add a logo URL later
    NOW(),
    NOW()
  )
  ON CONFLICT (account_id) DO UPDATE
    SET brand_name = 'Demo Title Company',
        brand_tagline = 'Your Trusted Real Estate Partner',
        brand_primary_color = '#1e40af',
        updated_at = NOW();

END $$;

-- =====================================================
-- 5. VERIFICATION QUERY
-- =====================================================
-- Run this to verify all accounts were created:

SELECT 
  u.email,
  u.role AS user_role,
  a.name AS account_name,
  a.account_type,
  a.plan_slug,
  a.sponsor_account_id IS NOT NULL AS is_sponsored,
  au.role AS account_role
FROM users u
JOIN account_users au ON u.id = au.user_id
JOIN accounts a ON au.account_id = a.id
WHERE u.email LIKE '%@trendyreports-demo.com'
ORDER BY u.email;

-- =====================================================
-- NOTES
-- =====================================================
-- 1. This script is IDEMPOTENT - safe to run multiple times
-- 2. Passwords are hashed using bcrypt via pgcrypto
-- 3. All demo accounts use @trendyreports-demo.com domain for easy identification
-- 4. To rotate passwords, simply re-run this script with updated passwords
-- 5. DO NOT use these credentials in production!


-- =====================================================
-- PRODUCTION DEMO ACCOUNTS SEED SCRIPT V2
-- =====================================================
-- Fixed to match actual schema: users.account_id is NOT NULL
-- Each user has a primary account, plus account_users for multi-tenancy
-- =====================================================
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
-- =====================================================

-- Ensure pgcrypto extension is available
CREATE EXTENSION IF NOT EXISTS pgcrypto;

DO $$
DECLARE
  admin_account_id UUID;
  free_agent_account_id UUID;
  pro_agent_account_id UUID;
  affiliate_account_id UUID;
  sponsored_agent_account_id UUID;
  
  admin_user_id UUID;
  free_agent_user_id UUID;
  pro_agent_user_id UUID;
  affiliate_user_id UUID;
  sponsored_agent_user_id UUID;
BEGIN
  -- =====================================================
  -- 1. CREATE ACCOUNTS FIRST
  -- =====================================================
  
  -- Admin Account
  INSERT INTO accounts (name, slug, account_type, plan_slug, status, created_at, updated_at)
  VALUES (
    'TrendyReports Admin',
    'trendy-admin-demo',
    'REGULAR',
    'pro',
    'active',
    NOW(),
    NOW()
  )
  ON CONFLICT (slug) DO UPDATE
    SET name = 'TrendyReports Admin',
        account_type = 'REGULAR',
        plan_slug = 'pro',
        updated_at = NOW()
  RETURNING id INTO admin_account_id;
  
  IF admin_account_id IS NULL THEN
    SELECT id INTO admin_account_id FROM accounts WHERE slug = 'trendy-admin-demo';
  END IF;
  
  RAISE NOTICE 'Admin account: %', admin_account_id;
  
  -- Free Agent Account
  INSERT INTO accounts (name, slug, account_type, plan_slug, status, monthly_report_limit_override, created_at, updated_at)
  VALUES (
    'Demo Free Agent',
    'demo-free-agent-prod',
    'REGULAR',
    'free',
    'active',
    50,
    NOW(),
    NOW()
  )
  ON CONFLICT (slug) DO UPDATE
    SET name = 'Demo Free Agent',
        account_type = 'REGULAR',
        plan_slug = 'free',
        monthly_report_limit_override = 50,
        updated_at = NOW()
  RETURNING id INTO free_agent_account_id;
  
  IF free_agent_account_id IS NULL THEN
    SELECT id INTO free_agent_account_id FROM accounts WHERE slug = 'demo-free-agent-prod';
  END IF;
  
  RAISE NOTICE 'Free agent account: %', free_agent_account_id;
  
  -- Pro Agent Account
  INSERT INTO accounts (name, slug, account_type, plan_slug, status, monthly_report_limit_override, created_at, updated_at)
  VALUES (
    'Demo Pro Agent',
    'demo-pro-agent-prod',
    'REGULAR',
    'pro',
    'active',
    300,
    NOW(),
    NOW()
  )
  ON CONFLICT (slug) DO UPDATE
    SET name = 'Demo Pro Agent',
        account_type = 'REGULAR',
        plan_slug = 'pro',
        monthly_report_limit_override = 300,
        updated_at = NOW()
  RETURNING id INTO pro_agent_account_id;
  
  IF pro_agent_account_id IS NULL THEN
    SELECT id INTO pro_agent_account_id FROM accounts WHERE slug = 'demo-pro-agent-prod';
  END IF;
  
  RAISE NOTICE 'Pro agent account: %', pro_agent_account_id;
  
  -- Affiliate Account (INDUSTRY_AFFILIATE)
  INSERT INTO accounts (name, slug, account_type, plan_slug, status, created_at, updated_at)
  VALUES (
    'Demo Title Company',
    'demo-title-company-prod',
    'INDUSTRY_AFFILIATE',
    'affiliate',
    'active',
    NOW(),
    NOW()
  )
  ON CONFLICT (slug) DO UPDATE
    SET name = 'Demo Title Company',
        account_type = 'INDUSTRY_AFFILIATE',
        plan_slug = 'affiliate',
        updated_at = NOW()
  RETURNING id INTO affiliate_account_id;
  
  IF affiliate_account_id IS NULL THEN
    SELECT id INTO affiliate_account_id FROM accounts WHERE slug = 'demo-title-company-prod';
  END IF;
  
  RAISE NOTICE 'Affiliate account: %', affiliate_account_id;
  
  -- Sponsored Agent Account (sponsored by affiliate)
  INSERT INTO accounts (name, slug, account_type, plan_slug, sponsor_account_id, status, created_at, updated_at)
  VALUES (
    'Demo Sponsored Agent',
    'demo-sponsored-agent-prod',
    'REGULAR',
    'sponsored_free',
    affiliate_account_id,
    'active',
    NOW(),
    NOW()
  )
  ON CONFLICT (slug) DO UPDATE
    SET name = 'Demo Sponsored Agent',
        account_type = 'REGULAR',
        plan_slug = 'sponsored_free',
        sponsor_account_id = affiliate_account_id,
        updated_at = NOW()
  RETURNING id INTO sponsored_agent_account_id;
  
  IF sponsored_agent_account_id IS NULL THEN
    SELECT id INTO sponsored_agent_account_id FROM accounts WHERE slug = 'demo-sponsored-agent-prod';
  END IF;
  
  RAISE NOTICE 'Sponsored agent account: % (sponsored by %)', sponsored_agent_account_id, affiliate_account_id;
  
  -- =====================================================
  -- 2. CREATE/UPDATE USERS WITH ACCOUNT_ID SET
  -- =====================================================
  
  -- Admin User
  INSERT INTO users (email, account_id, password_hash, role, is_active, created_at, updated_at)
  VALUES (
    'admin@trendyreports-demo.com',
    admin_account_id,
    crypt('DemoAdmin123!', gen_salt('bf')),
    'ADMIN',
    TRUE,
    NOW(),
    NOW()
  )
  ON CONFLICT (email) DO UPDATE
    SET password_hash = crypt('DemoAdmin123!', gen_salt('bf')),
        role = 'ADMIN',
        account_id = admin_account_id,
        is_active = TRUE,
        updated_at = NOW()
  RETURNING id INTO admin_user_id;
  
  IF admin_user_id IS NULL THEN
    SELECT id INTO admin_user_id FROM users WHERE email = 'admin@trendyreports-demo.com';
  END IF;
  
  RAISE NOTICE 'Admin user: %', admin_user_id;
  
  -- Free Agent User
  INSERT INTO users (email, account_id, password_hash, role, is_active, created_at, updated_at)
  VALUES (
    'agent-free@trendyreports-demo.com',
    free_agent_account_id,
    crypt('DemoAgent123!', gen_salt('bf')),
    'MEMBER',
    TRUE,
    NOW(),
    NOW()
  )
  ON CONFLICT (email) DO UPDATE
    SET password_hash = crypt('DemoAgent123!', gen_salt('bf')),
        role = 'MEMBER',
        account_id = free_agent_account_id,
        is_active = TRUE,
        updated_at = NOW()
  RETURNING id INTO free_agent_user_id;
  
  IF free_agent_user_id IS NULL THEN
    SELECT id INTO free_agent_user_id FROM users WHERE email = 'agent-free@trendyreports-demo.com';
  END IF;
  
  RAISE NOTICE 'Free agent user: %', free_agent_user_id;
  
  -- Pro Agent User
  INSERT INTO users (email, account_id, password_hash, role, is_active, created_at, updated_at)
  VALUES (
    'agent-pro@trendyreports-demo.com',
    pro_agent_account_id,
    crypt('DemoAgent123!', gen_salt('bf')),
    'MEMBER',
    TRUE,
    NOW(),
    NOW()
  )
  ON CONFLICT (email) DO UPDATE
    SET password_hash = crypt('DemoAgent123!', gen_salt('bf')),
        role = 'MEMBER',
        account_id = pro_agent_account_id,
        is_active = TRUE,
        updated_at = NOW()
  RETURNING id INTO pro_agent_user_id;
  
  IF pro_agent_user_id IS NULL THEN
    SELECT id INTO pro_agent_user_id FROM users WHERE email = 'agent-pro@trendyreports-demo.com';
  END IF;
  
  RAISE NOTICE 'Pro agent user: %', pro_agent_user_id;
  
  -- Affiliate User
  INSERT INTO users (email, account_id, password_hash, role, is_active, created_at, updated_at)
  VALUES (
    'affiliate@trendyreports-demo.com',
    affiliate_account_id,
    crypt('DemoAff123!', gen_salt('bf')),
    'MEMBER',
    TRUE,
    NOW(),
    NOW()
  )
  ON CONFLICT (email) DO UPDATE
    SET password_hash = crypt('DemoAff123!', gen_salt('bf')),
        role = 'MEMBER',
        account_id = affiliate_account_id,
        is_active = TRUE,
        updated_at = NOW()
  RETURNING id INTO affiliate_user_id;
  
  IF affiliate_user_id IS NULL THEN
    SELECT id INTO affiliate_user_id FROM users WHERE email = 'affiliate@trendyreports-demo.com';
  END IF;
  
  RAISE NOTICE 'Affiliate user: %', affiliate_user_id;
  
  -- Sponsored Agent User
  INSERT INTO users (email, account_id, password_hash, role, is_active, created_at, updated_at)
  VALUES (
    'agent-sponsored@trendyreports-demo.com',
    sponsored_agent_account_id,
    crypt('DemoAgent123!', gen_salt('bf')),
    'MEMBER',
    TRUE,
    NOW(),
    NOW()
  )
  ON CONFLICT (email) DO UPDATE
    SET password_hash = crypt('DemoAgent123!', gen_salt('bf')),
        role = 'MEMBER',
        account_id = sponsored_agent_account_id,
        is_active = TRUE,
        updated_at = NOW()
  RETURNING id INTO sponsored_agent_user_id;
  
  IF sponsored_agent_user_id IS NULL THEN
    SELECT id INTO sponsored_agent_user_id FROM users WHERE email = 'agent-sponsored@trendyreports-demo.com';
  END IF;
  
  RAISE NOTICE 'Sponsored agent user: %', sponsored_agent_user_id;
  
  -- =====================================================
  -- 3. LINK USERS TO ACCOUNTS VIA ACCOUNT_USERS
  -- =====================================================
  
  -- Admin
  INSERT INTO account_users (account_id, user_id, role, created_at)
  VALUES (admin_account_id, admin_user_id, 'OWNER', NOW())
  ON CONFLICT (account_id, user_id) DO UPDATE
    SET role = 'OWNER';
  
  -- Free Agent
  INSERT INTO account_users (account_id, user_id, role, created_at)
  VALUES (free_agent_account_id, free_agent_user_id, 'OWNER', NOW())
  ON CONFLICT (account_id, user_id) DO UPDATE
    SET role = 'OWNER';
  
  -- Pro Agent
  INSERT INTO account_users (account_id, user_id, role, created_at)
  VALUES (pro_agent_account_id, pro_agent_user_id, 'OWNER', NOW())
  ON CONFLICT (account_id, user_id) DO UPDATE
    SET role = 'OWNER';
  
  -- Affiliate
  INSERT INTO account_users (account_id, user_id, role, created_at)
  VALUES (affiliate_account_id, affiliate_user_id, 'OWNER', NOW())
  ON CONFLICT (account_id, user_id) DO UPDATE
    SET role = 'OWNER';
  
  -- Sponsored Agent
  INSERT INTO account_users (account_id, user_id, role, created_at)
  VALUES (sponsored_agent_account_id, sponsored_agent_user_id, 'OWNER', NOW())
  ON CONFLICT (account_id, user_id) DO UPDATE
    SET role = 'OWNER';
  
  RAISE NOTICE 'All account_users links created';
  
END $$;

-- =====================================================
-- 4. VERIFICATION QUERY
-- =====================================================
SELECT 
  'Production demo accounts created/updated successfully' AS status,
  u.email,
  u.role AS user_role,
  a.name AS account_name,
  a.account_type,
  a.plan_slug,
  CASE 
    WHEN a.sponsor_account_id IS NOT NULL THEN '(sponsored)'
    ELSE ''
  END AS sponsor_status,
  u.is_active
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


-- =====================================================
-- DEMO ACCOUNTS SEED SCRIPT V2 (STAGING ONLY)
-- =====================================================
-- Fixed to match actual schema: users.account_id is NOT NULL
-- Each user has a primary account, plus account_users for multi-tenancy
-- =====================================================

-- Ensure pgcrypto extension is available
CREATE EXTENSION IF NOT EXISTS pgcrypto;

-- =====================================================
-- 1. CREATE DEMO ACCOUNTS FIRST
-- =====================================================

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
  -- CREATE ACCOUNTS
  -- =====================================================
  
  -- Admin Account
  INSERT INTO accounts (name, slug, account_type, plan_slug, status, created_at, updated_at)
  VALUES (
    'Admin Organization',
    'admin-org-demo',
    'REGULAR',
    'free',
    'active',
    NOW(),
    NOW()
  )
  ON CONFLICT (slug) DO UPDATE
    SET name = 'Admin Organization',
        account_type = 'REGULAR',
        plan_slug = 'free',
        updated_at = NOW()
  RETURNING id INTO admin_account_id;
  
  -- If conflict, get existing ID
  IF admin_account_id IS NULL THEN
    SELECT id INTO admin_account_id FROM accounts WHERE slug = 'admin-org-demo';
  END IF;
  
  -- Free Agent Account
  INSERT INTO accounts (name, slug, account_type, plan_slug, status, monthly_report_limit_override, created_at, updated_at)
  VALUES (
    'Demo Free Agent',
    'demo-free-agent',
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
    SELECT id INTO free_agent_account_id FROM accounts WHERE slug = 'demo-free-agent';
  END IF;
  
  -- Pro Agent Account
  INSERT INTO accounts (name, slug, account_type, plan_slug, status, monthly_report_limit_override, created_at, updated_at)
  VALUES (
    'Demo Pro Agent',
    'demo-pro-agent',
    'REGULAR',
    'pro',
    'active',
    100,
    NOW(),
    NOW()
  )
  ON CONFLICT (slug) DO UPDATE
    SET name = 'Demo Pro Agent',
        account_type = 'REGULAR',
        plan_slug = 'pro',
        monthly_report_limit_override = 100,
        updated_at = NOW()
  RETURNING id INTO pro_agent_account_id;
  
  IF pro_agent_account_id IS NULL THEN
    SELECT id INTO pro_agent_account_id FROM accounts WHERE slug = 'demo-pro-agent';
  END IF;
  
  -- Affiliate Account
  INSERT INTO accounts (name, slug, account_type, plan_slug, status, created_at, updated_at)
  VALUES (
    'Demo Title Company',
    'demo-title-company',
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
    SELECT id INTO affiliate_account_id FROM accounts WHERE slug = 'demo-title-company';
  END IF;
  
  -- Sponsored Agent Account (sponsored by affiliate)
  INSERT INTO accounts (name, slug, account_type, plan_slug, sponsor_account_id, status, created_at, updated_at)
  VALUES (
    'Demo Sponsored Agent',
    'demo-sponsored-agent',
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
    SELECT id INTO sponsored_agent_account_id FROM accounts WHERE slug = 'demo-sponsored-agent';
  END IF;
  
  -- =====================================================
  -- CREATE USERS (with primary account_id)
  -- =====================================================
  
  -- Admin User
  INSERT INTO users (account_id, email, password_hash, role, email_verified, is_active, created_at, updated_at)
  VALUES (
    admin_account_id,
    'admin@trendyreports-demo.com',
    crypt('DemoAdmin123!', gen_salt('bf')),
    'ADMIN',
    true,
    true,
    NOW(),
    NOW()
  )
  ON CONFLICT (email) DO UPDATE
    SET password_hash = crypt('DemoAdmin123!', gen_salt('bf')),
        role = 'ADMIN',
        account_id = admin_account_id,
        updated_at = NOW()
  RETURNING id INTO admin_user_id;
  
  IF admin_user_id IS NULL THEN
    SELECT id INTO admin_user_id FROM users WHERE email = 'admin@trendyreports-demo.com';
  END IF;
  
  -- Free Agent User
  INSERT INTO users (account_id, email, password_hash, role, email_verified, is_active, created_at, updated_at)
  VALUES (
    free_agent_account_id,
    'agent-free@trendyreports-demo.com',
    crypt('DemoAgent123!', gen_salt('bf')),
    'MEMBER',
    true,
    true,
    NOW(),
    NOW()
  )
  ON CONFLICT (email) DO UPDATE
    SET password_hash = crypt('DemoAgent123!', gen_salt('bf')),
        role = 'MEMBER',
        account_id = free_agent_account_id,
        updated_at = NOW()
  RETURNING id INTO free_agent_user_id;
  
  IF free_agent_user_id IS NULL THEN
    SELECT id INTO free_agent_user_id FROM users WHERE email = 'agent-free@trendyreports-demo.com';
  END IF;
  
  -- Pro Agent User
  INSERT INTO users (account_id, email, password_hash, role, email_verified, is_active, created_at, updated_at)
  VALUES (
    pro_agent_account_id,
    'agent-pro@trendyreports-demo.com',
    crypt('DemoAgent123!', gen_salt('bf')),
    'MEMBER',
    true,
    true,
    NOW(),
    NOW()
  )
  ON CONFLICT (email) DO UPDATE
    SET password_hash = crypt('DemoAgent123!', gen_salt('bf')),
        role = 'MEMBER',
        account_id = pro_agent_account_id,
        updated_at = NOW()
  RETURNING id INTO pro_agent_user_id;
  
  IF pro_agent_user_id IS NULL THEN
    SELECT id INTO pro_agent_user_id FROM users WHERE email = 'agent-pro@trendyreports-demo.com';
  END IF;
  
  -- Affiliate User
  INSERT INTO users (account_id, email, password_hash, role, email_verified, is_active, created_at, updated_at)
  VALUES (
    affiliate_account_id,
    'affiliate@trendyreports-demo.com',
    crypt('DemoAff123!', gen_salt('bf')),
    'MEMBER',
    true,
    true,
    NOW(),
    NOW()
  )
  ON CONFLICT (email) DO UPDATE
    SET password_hash = crypt('DemoAff123!', gen_salt('bf')),
        role = 'MEMBER',
        account_id = affiliate_account_id,
        updated_at = NOW()
  RETURNING id INTO affiliate_user_id;
  
  IF affiliate_user_id IS NULL THEN
    SELECT id INTO affiliate_user_id FROM users WHERE email = 'affiliate@trendyreports-demo.com';
  END IF;
  
  -- Sponsored Agent User
  INSERT INTO users (account_id, email, password_hash, role, email_verified, is_active, created_at, updated_at)
  VALUES (
    sponsored_agent_account_id,
    'agent-sponsored@trendyreports-demo.com',
    crypt('DemoAgent123!', gen_salt('bf')),
    'MEMBER',
    true,
    true,
    NOW(),
    NOW()
  )
  ON CONFLICT (email) DO UPDATE
    SET password_hash = crypt('DemoAgent123!', gen_salt('bf')),
        role = 'MEMBER',
        account_id = sponsored_agent_account_id,
        updated_at = NOW()
  RETURNING id INTO sponsored_agent_user_id;
  
  IF sponsored_agent_user_id IS NULL THEN
    SELECT id INTO sponsored_agent_user_id FROM users WHERE email = 'agent-sponsored@trendyreports-demo.com';
  END IF;
  
  -- =====================================================
  -- CREATE ACCOUNT_USERS (multi-tenancy relationships)
  -- =====================================================
  
  -- Admin → Admin Organization (OWNER)
  INSERT INTO account_users (account_id, user_id, role, created_at)
  VALUES (admin_account_id, admin_user_id, 'OWNER', NOW())
  ON CONFLICT (account_id, user_id) DO UPDATE SET role = 'OWNER';
  
  -- Free Agent → Free Agent Account (OWNER)
  INSERT INTO account_users (account_id, user_id, role, created_at)
  VALUES (free_agent_account_id, free_agent_user_id, 'OWNER', NOW())
  ON CONFLICT (account_id, user_id) DO UPDATE SET role = 'OWNER';
  
  -- Pro Agent → Pro Agent Account (OWNER)
  INSERT INTO account_users (account_id, user_id, role, created_at)
  VALUES (pro_agent_account_id, pro_agent_user_id, 'OWNER', NOW())
  ON CONFLICT (account_id, user_id) DO UPDATE SET role = 'OWNER';
  
  -- Affiliate → Affiliate Account (OWNER)
  INSERT INTO account_users (account_id, user_id, role, created_at)
  VALUES (affiliate_account_id, affiliate_user_id, 'OWNER', NOW())
  ON CONFLICT (account_id, user_id) DO UPDATE SET role = 'OWNER';
  
  -- Sponsored Agent → Sponsored Agent Account (OWNER)
  INSERT INTO account_users (account_id, user_id, role, created_at)
  VALUES (sponsored_agent_account_id, sponsored_agent_user_id, 'OWNER', NOW())
  ON CONFLICT (account_id, user_id) DO UPDATE SET role = 'OWNER';
  
  -- Output success message
  RAISE NOTICE '✅ Created 5 demo accounts and users successfully!';
  RAISE NOTICE 'Account IDs: admin=%, free=%, pro=%, affiliate=%, sponsored=%',
    admin_account_id, free_agent_account_id, pro_agent_account_id, affiliate_account_id, sponsored_agent_account_id;

END $$;

-- =====================================================
-- VERIFICATION QUERY
-- =====================================================

SELECT 
  u.email,
  u.role AS user_role,
  a.name AS account_name,
  a.account_type,
  a.plan_slug,
  a.sponsor_account_id IS NOT NULL AS is_sponsored
FROM users u
JOIN accounts a ON u.account_id = a.id
WHERE u.email LIKE '%@trendyreports-demo.com'
ORDER BY u.email;


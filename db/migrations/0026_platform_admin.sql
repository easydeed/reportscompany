-- Migration: 0026_platform_admin.sql
-- Description: Add is_platform_admin flag to users table and create platform admin user
-- Purpose: Separate platform admin access (/admin) from tenant roles (account_users.role)

-- Ensure pgcrypto exists for password hashing
CREATE EXTENSION IF NOT EXISTS pgcrypto;

-- 1) Add is_platform_admin column to users table
ALTER TABLE users
ADD COLUMN IF NOT EXISTS is_platform_admin BOOLEAN NOT NULL DEFAULT FALSE;

COMMENT ON COLUMN users.is_platform_admin IS 'Platform-level admin access for /admin console. Separate from tenant roles in account_users.role';

-- 2) Create internal ops account for platform admin user
-- This is required because users.account_id is NOT NULL
DO $$
DECLARE
    ops_account_id UUID;
    admin_user_id UUID;
BEGIN
    -- Check if ops account already exists
    SELECT id INTO ops_account_id
    FROM accounts
    WHERE slug = 'trendyreports-ops';

    -- Create ops account if it doesn't exist
    IF ops_account_id IS NULL THEN
        INSERT INTO accounts (
            name,
            slug,
            account_type,
            plan_slug,
            is_active,
            created_at,
            updated_at
        ) VALUES (
            'TrendyReports Operations',
            'trendyreports-ops',
            'REGULAR',
            'team',  -- Internal ops account gets team plan
            TRUE,
            NOW(),
            NOW()
        )
        RETURNING id INTO ops_account_id;
        
        RAISE NOTICE 'Created ops account: %', ops_account_id;
    ELSE
        RAISE NOTICE 'Ops account already exists: %', ops_account_id;
    END IF;

    -- 3) Create or update platform admin user
    -- Check if admin user already exists
    SELECT id INTO admin_user_id
    FROM users
    WHERE email = 'admin@trendyreports.io';

    IF admin_user_id IS NULL THEN
        -- Create new admin user
        INSERT INTO users (
            account_id,
            email,
            password_hash,
            role,
            is_platform_admin,
            email_verified,
            is_active,
            first_name,
            last_name,
            created_at,
            updated_at
        ) VALUES (
            ops_account_id,
            'admin@trendyreports.io',
            crypt('Alpha637#', gen_salt('bf')),
            'OWNER',  -- Tenant role within the ops account
            TRUE,     -- Platform admin flag
            TRUE,
            TRUE,
            'Platform',
            'Admin',
            NOW(),
            NOW()
        )
        RETURNING id INTO admin_user_id;
        
        RAISE NOTICE 'Created platform admin user: %', admin_user_id;
    ELSE
        -- Update existing user to be platform admin
        UPDATE users
        SET is_platform_admin = TRUE,
            is_active = TRUE,
            email_verified = TRUE,
            password_hash = crypt('Alpha637#', gen_salt('bf')),
            updated_at = NOW()
        WHERE id = admin_user_id;
        
        -- Make sure user is linked to ops account
        UPDATE users
        SET account_id = ops_account_id
        WHERE id = admin_user_id AND account_id != ops_account_id;
        
        RAISE NOTICE 'Updated existing user to platform admin: %', admin_user_id;
    END IF;

    -- 4) Link admin user to ops account via account_users (for tenant role)
    INSERT INTO account_users (account_id, user_id, role, created_at)
    VALUES (ops_account_id, admin_user_id, 'OWNER', NOW())
    ON CONFLICT (account_id, user_id) DO UPDATE
    SET role = 'OWNER';
    
    RAISE NOTICE 'Linked platform admin to ops account in account_users';

END $$;

-- 5) Verification
SELECT 
    u.email,
    u.is_platform_admin,
    u.is_active,
    u.email_verified,
    a.name as account_name,
    a.slug as account_slug,
    au.role as tenant_role
FROM users u
JOIN accounts a ON u.account_id = a.id
LEFT JOIN account_users au ON au.user_id = u.id AND au.account_id = a.id
WHERE u.email = 'admin@trendyreports.io';

SELECT '0026_platform_admin.sql applied successfully' AS migration;

-- Migration: 0001_base.sql
-- Description: Base schema for multi-tenant SaaS with RLS
-- Idempotent: Can be run multiple times safely

-- 1) Enable extensions
CREATE EXTENSION IF NOT EXISTS pgcrypto;

-- 2) Create tables

-- Accounts table (tenants)
CREATE TABLE IF NOT EXISTS accounts (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(200) NOT NULL,
    slug VARCHAR(100) UNIQUE NOT NULL,
    status VARCHAR(20) DEFAULT 'active',
    logo_url VARCHAR(500),
    primary_color VARCHAR(7) DEFAULT '#03374f',
    secondary_color VARCHAR(7) DEFAULT '#ffffff',
    plan_id INT,
    subscription_status VARCHAR(50),
    trial_ends_at TIMESTAMP,
    monthly_report_limit INT DEFAULT 100,
    api_rate_limit INT DEFAULT 60,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Users table
CREATE TABLE IF NOT EXISTS users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    account_id UUID NOT NULL REFERENCES accounts(id) ON DELETE CASCADE,
    email VARCHAR(255) UNIQUE NOT NULL,
    password_hash VARCHAR(255),
    role VARCHAR(20) DEFAULT 'member',
    email_verified BOOLEAN DEFAULT false,
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Subscription plans table
CREATE TABLE IF NOT EXISTS subscription_plans (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    slug VARCHAR(50) UNIQUE NOT NULL,
    price_monthly DECIMAL(10,2),
    price_annual DECIMAL(10,2),
    features JSONB,
    is_active BOOLEAN DEFAULT true,
    display_order INT DEFAULT 0,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Report generations table
CREATE TABLE IF NOT EXISTS report_generations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    account_id UUID NOT NULL REFERENCES accounts(id) ON DELETE CASCADE,
    user_id UUID REFERENCES users(id) ON DELETE SET NULL,
    report_type VARCHAR(50) NOT NULL,
    cities TEXT[],
    lookback_days INT,
    property_type VARCHAR(50),
    additional_params JSONB,
    html_url VARCHAR(500),
    json_url VARCHAR(500),
    csv_url VARCHAR(500),
    pdf_url VARCHAR(500),
    status VARCHAR(20) DEFAULT 'pending',
    error_message TEXT,
    processing_time_ms INT,
    billable BOOLEAN DEFAULT true,
    billed_at TIMESTAMP,
    generated_at TIMESTAMP DEFAULT NOW(),
    expires_at TIMESTAMP
);

-- Usage tracking table
CREATE TABLE IF NOT EXISTS usage_tracking (
    id BIGSERIAL PRIMARY KEY,
    account_id UUID NOT NULL REFERENCES accounts(id),
    user_id UUID REFERENCES users(id),
    event_type VARCHAR(50) NOT NULL,
    report_id UUID REFERENCES report_generations(id),
    billable_units INT DEFAULT 1,
    cost_cents INT DEFAULT 0,
    ip_address INET,
    user_agent TEXT,
    request_id VARCHAR(100),
    created_at TIMESTAMP DEFAULT NOW()
);

-- API keys table
CREATE TABLE IF NOT EXISTS api_keys (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    account_id UUID NOT NULL REFERENCES accounts(id) ON DELETE CASCADE,
    user_id UUID REFERENCES users(id) ON DELETE SET NULL,
    key_prefix VARCHAR(10),
    key_hash VARCHAR(255),
    name VARCHAR(100),
    scopes TEXT[],
    rate_limit INT DEFAULT 60,
    is_active BOOLEAN DEFAULT true,
    last_used_at TIMESTAMP,
    expires_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- 3) Create indexes
CREATE INDEX IF NOT EXISTS idx_reports_account_date ON report_generations(account_id, generated_at DESC);
CREATE INDEX IF NOT EXISTS idx_usage_account_date ON usage_tracking(account_id, created_at);
CREATE INDEX IF NOT EXISTS idx_api_keys_hash ON api_keys (key_hash);

-- 4) Row-Level Security (RLS)

-- Enable RLS on tables
ALTER TABLE report_generations ENABLE ROW LEVEL SECURITY;
ALTER TABLE usage_tracking ENABLE ROW LEVEL SECURITY;
ALTER TABLE api_keys ENABLE ROW LEVEL SECURITY;

-- Create RLS policies (idempotent with checks)
DO $$
BEGIN
  IF NOT EXISTS (
    SELECT 1 FROM pg_policies WHERE schemaname = 'public' AND tablename = 'report_generations' AND policyname = 'report_rls'
  ) THEN
    EXECUTE $p$
      CREATE POLICY report_rls ON report_generations
      FOR ALL
      USING (account_id = current_setting('app.current_account_id', true)::uuid)
      WITH CHECK (account_id = current_setting('app.current_account_id', true)::uuid)
    $p$;
  END IF;

  IF NOT EXISTS (
    SELECT 1 FROM pg_policies WHERE schemaname = 'public' AND tablename = 'usage_tracking' AND policyname = 'usage_rls'
  ) THEN
    EXECUTE $p$
      CREATE POLICY usage_rls ON usage_tracking
      FOR ALL
      USING (account_id = current_setting('app.current_account_id', true)::uuid)
      WITH CHECK (account_id = current_setting('app.current_account_id', true)::uuid)
    $p$;
  END IF;

  IF NOT EXISTS (
    SELECT 1 FROM pg_policies WHERE schemaname = 'public' AND tablename = 'api_keys' AND policyname = 'api_keys_rls'
  ) THEN
    EXECUTE $p$
      CREATE POLICY api_keys_rls ON api_keys
      FOR ALL
      USING (account_id = current_setting('app.current_account_id', true)::uuid)
      WITH CHECK (account_id = current_setting('app.current_account_id', true)::uuid)
    $p$;
  END IF;
END $$;

-- 5) Confirmation
SELECT '0001_base.sql applied' AS migration;


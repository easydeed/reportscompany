-- Migration 0034: Property Reports & Lead Capture
-- Date: 2026-01-09
-- Purpose: Add property reports (seller/buyer CMA-style) with QR code lead capture
--
-- New Tables:
--   - property_reports: Individual property reports with SiteX data and comps
--   - leads: Lead capture from QR scans and direct links
--
-- Modified Tables:
--   - accounts: Add sms_credits field
--   - plans: Add property_reports_per_month, sms_credits_per_month, lead_capture_enabled

-- ============================================================================
-- HELPER FUNCTION: Generate unique short codes for QR links
-- ============================================================================

CREATE OR REPLACE FUNCTION generate_short_code(length INT DEFAULT 8)
RETURNS TEXT AS $$
DECLARE
    chars TEXT := 'abcdefghjkmnpqrstuvwxyz23456789';  -- Excludes confusing chars: i, l, o, 0, 1
    result TEXT := '';
    i INT;
BEGIN
    FOR i IN 1..length LOOP
        result := result || substr(chars, floor(random() * length(chars) + 1)::int, 1);
    END LOOP;
    RETURN result;
END;
$$ LANGUAGE plpgsql;

-- ============================================================================
-- TABLE: property_reports
-- ============================================================================

CREATE TABLE IF NOT EXISTS property_reports (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    account_id UUID NOT NULL REFERENCES accounts(id) ON DELETE CASCADE,
    user_id UUID REFERENCES users(id) ON DELETE SET NULL,
    
    -- Report configuration
    report_type VARCHAR(20) NOT NULL CHECK (report_type IN ('seller', 'buyer')),
    theme INTEGER NOT NULL DEFAULT 1 CHECK (theme >= 1 AND theme <= 5),
    accent_color VARCHAR(20) DEFAULT '#2563eb',
    language VARCHAR(5) NOT NULL DEFAULT 'en' CHECK (language IN ('en', 'es')),
    
    -- Property information
    property_address VARCHAR(500) NOT NULL,
    property_city VARCHAR(100) NOT NULL,
    property_state VARCHAR(50) NOT NULL,
    property_zip VARCHAR(20) NOT NULL,
    property_county VARCHAR(100),
    apn VARCHAR(100),
    owner_name VARCHAR(200),
    legal_description TEXT,
    property_type VARCHAR(50),
    
    -- External data cache
    sitex_data JSONB,               -- Cached SiteX API response
    comparables JSONB,              -- Array of comparable properties
    
    -- Output
    pdf_url VARCHAR(500),
    status VARCHAR(20) NOT NULL DEFAULT 'draft' CHECK (status IN ('draft', 'processing', 'complete', 'failed')),
    error_message TEXT,              -- Error details if status='failed'
    
    -- QR Code / Lead Capture
    short_code VARCHAR(20) UNIQUE,   -- For QR links: /p/{short_code}
    qr_code_url VARCHAR(500),        -- Generated QR code image URL
    view_count INTEGER NOT NULL DEFAULT 0,
    unique_visitors INTEGER NOT NULL DEFAULT 0,
    last_viewed_at TIMESTAMPTZ,
    
    -- Landing Page Controls
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    expires_at TIMESTAMPTZ,          -- When the landing page expires (NULL = never)
    max_leads INTEGER,               -- Max leads before auto-deactivation (NULL = unlimited)
    access_code VARCHAR(50),         -- Optional password protection for landing page
    
    -- Timestamps
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Indexes for property_reports
CREATE INDEX IF NOT EXISTS idx_property_reports_account_id ON property_reports(account_id);
CREATE INDEX IF NOT EXISTS idx_property_reports_user_id ON property_reports(user_id);
CREATE INDEX IF NOT EXISTS idx_property_reports_short_code ON property_reports(short_code) WHERE short_code IS NOT NULL;
CREATE INDEX IF NOT EXISTS idx_property_reports_status ON property_reports(status);
CREATE INDEX IF NOT EXISTS idx_property_reports_created_at ON property_reports(account_id, created_at DESC);
CREATE INDEX IF NOT EXISTS idx_property_reports_active ON property_reports(is_active, expires_at) WHERE is_active = TRUE;

-- ============================================================================
-- TABLE: leads
-- ============================================================================

CREATE TABLE IF NOT EXISTS leads (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    account_id UUID NOT NULL REFERENCES accounts(id) ON DELETE CASCADE,
    property_report_id UUID REFERENCES property_reports(id) ON DELETE SET NULL,
    
    -- Contact information
    name VARCHAR(200),
    email VARCHAR(255),
    phone VARCHAR(50),
    message TEXT,
    
    -- Source tracking
    source VARCHAR(50) NOT NULL DEFAULT 'direct_link' CHECK (source IN ('qr_scan', 'direct_link')),
    
    -- Consent & communication
    consent_given BOOLEAN NOT NULL DEFAULT FALSE,
    sms_sent_at TIMESTAMPTZ,
    email_sent_at TIMESTAMPTZ,
    
    -- Lead management
    status VARCHAR(20) NOT NULL DEFAULT 'new' CHECK (status IN ('new', 'contacted', 'converted')),
    notes TEXT,
    
    -- Tracking info (for spam prevention)
    ip_address VARCHAR(45),          -- IPv4 or IPv6
    user_agent TEXT,
    
    -- Timestamps
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Indexes for leads
CREATE INDEX IF NOT EXISTS idx_leads_account_id ON leads(account_id);
CREATE INDEX IF NOT EXISTS idx_leads_property_report_id ON leads(property_report_id) WHERE property_report_id IS NOT NULL;
CREATE INDEX IF NOT EXISTS idx_leads_status ON leads(account_id, status);
CREATE INDEX IF NOT EXISTS idx_leads_email ON leads(email) WHERE email IS NOT NULL;
CREATE INDEX IF NOT EXISTS idx_leads_created_at ON leads(account_id, created_at DESC);
CREATE INDEX IF NOT EXISTS idx_leads_ip_address ON leads(ip_address) WHERE ip_address IS NOT NULL;

-- ============================================================================
-- TABLE: blocked_ips - Spam prevention
-- ============================================================================

CREATE TABLE IF NOT EXISTS blocked_ips (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    ip_address VARCHAR(45) NOT NULL UNIQUE,
    reason VARCHAR(255),
    blocked_by UUID REFERENCES users(id) ON DELETE SET NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    expires_at TIMESTAMPTZ                -- NULL = permanent block
);

CREATE INDEX IF NOT EXISTS idx_blocked_ips_ip ON blocked_ips(ip_address);
CREATE INDEX IF NOT EXISTS idx_blocked_ips_expires ON blocked_ips(expires_at) WHERE expires_at IS NOT NULL;

-- ============================================================================
-- TABLE: lead_rate_limits - Rate limiting for lead submissions
-- ============================================================================

CREATE TABLE IF NOT EXISTS lead_rate_limits (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    ip_address VARCHAR(45) NOT NULL,
    property_report_id UUID REFERENCES property_reports(id) ON DELETE CASCADE,
    submitted_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_lead_rate_limits_ip_time ON lead_rate_limits(ip_address, submitted_at);
CREATE INDEX IF NOT EXISTS idx_lead_rate_limits_report_time ON lead_rate_limits(property_report_id, submitted_at);

-- ============================================================================
-- ALTER: accounts table - Add sms_credits
-- ============================================================================

ALTER TABLE accounts
ADD COLUMN IF NOT EXISTS sms_credits INTEGER NOT NULL DEFAULT 0;

COMMENT ON COLUMN accounts.sms_credits IS 'Available SMS credits for lead capture notifications';

-- ============================================================================
-- ALTER: plans table - Add property report and lead capture fields
-- ============================================================================

ALTER TABLE plans
ADD COLUMN IF NOT EXISTS property_reports_per_month INTEGER;

ALTER TABLE plans
ADD COLUMN IF NOT EXISTS sms_credits_per_month INTEGER;

ALTER TABLE plans
ADD COLUMN IF NOT EXISTS lead_capture_enabled BOOLEAN NOT NULL DEFAULT FALSE;

COMMENT ON COLUMN plans.property_reports_per_month IS 'Monthly limit for property report generation (NULL = unlimited)';
COMMENT ON COLUMN plans.sms_credits_per_month IS 'SMS credits granted monthly for lead notifications';
COMMENT ON COLUMN plans.lead_capture_enabled IS 'Whether lead capture via QR codes is enabled for this plan';

-- ============================================================================
-- TRIGGER: Auto-generate short_code on property_reports insert
-- ============================================================================

CREATE OR REPLACE FUNCTION set_property_report_short_code()
RETURNS TRIGGER AS $$
DECLARE
    new_code TEXT;
    max_attempts INT := 10;
    attempt INT := 0;
BEGIN
    -- Only generate if short_code is NULL
    IF NEW.short_code IS NULL THEN
        LOOP
            attempt := attempt + 1;
            new_code := generate_short_code(8);
            
            -- Check if code already exists
            IF NOT EXISTS (SELECT 1 FROM property_reports WHERE short_code = new_code) THEN
                NEW.short_code := new_code;
                EXIT;
            END IF;
            
            -- Safety: avoid infinite loop
            IF attempt >= max_attempts THEN
                RAISE EXCEPTION 'Could not generate unique short_code after % attempts', max_attempts;
            END IF;
        END LOOP;
    END IF;
    
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS trigger_set_property_report_short_code ON property_reports;
CREATE TRIGGER trigger_set_property_report_short_code
    BEFORE INSERT ON property_reports
    FOR EACH ROW
    EXECUTE FUNCTION set_property_report_short_code();

-- ============================================================================
-- TRIGGER: Auto-update updated_at timestamp
-- ============================================================================

-- Ensure the update function exists (may already exist from 0013)
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Property reports updated_at trigger
DROP TRIGGER IF EXISTS update_property_reports_updated_at ON property_reports;
CREATE TRIGGER update_property_reports_updated_at
    BEFORE UPDATE ON property_reports
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- Leads updated_at trigger
DROP TRIGGER IF EXISTS update_leads_updated_at ON leads;
CREATE TRIGGER update_leads_updated_at
    BEFORE UPDATE ON leads
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- ============================================================================
-- ROW LEVEL SECURITY: property_reports
-- ============================================================================

ALTER TABLE property_reports ENABLE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS property_reports_rls ON property_reports;
CREATE POLICY property_reports_rls ON property_reports
    FOR ALL
    USING (
        account_id = current_setting('app.current_account_id', true)::uuid
        OR current_setting('app.current_user_role', true) = 'ADMIN'
    )
    WITH CHECK (
        account_id = current_setting('app.current_account_id', true)::uuid
        OR current_setting('app.current_user_role', true) = 'ADMIN'
    );

-- ============================================================================
-- ROW LEVEL SECURITY: leads
-- ============================================================================

ALTER TABLE leads ENABLE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS leads_rls ON leads;
CREATE POLICY leads_rls ON leads
    FOR ALL
    USING (
        account_id = current_setting('app.current_account_id', true)::uuid
        OR current_setting('app.current_user_role', true) = 'ADMIN'
    )
    WITH CHECK (
        account_id = current_setting('app.current_account_id', true)::uuid
        OR current_setting('app.current_user_role', true) = 'ADMIN'
    );

-- ============================================================================
-- COMMENTS
-- ============================================================================

COMMENT ON TABLE property_reports IS 'Individual property reports (seller CMA, buyer reports) with SiteX data integration';
COMMENT ON COLUMN property_reports.report_type IS 'seller = listing presentation, buyer = property analysis for buyers';
COMMENT ON COLUMN property_reports.theme IS 'Visual theme 1-5 for PDF styling';
COMMENT ON COLUMN property_reports.sitex_data IS 'Cached response from SiteX API with property details, tax info, etc.';
COMMENT ON COLUMN property_reports.comparables IS 'Array of comparable properties from MLS or manual entry';
COMMENT ON COLUMN property_reports.short_code IS 'Unique code for public links and QR codes: /p/{short_code}';
COMMENT ON COLUMN property_reports.view_count IS 'Number of times the public report page has been viewed';
COMMENT ON COLUMN property_reports.unique_visitors IS 'Number of unique visitors (by IP) to the landing page';
COMMENT ON COLUMN property_reports.last_viewed_at IS 'Timestamp of the most recent view';
COMMENT ON COLUMN property_reports.is_active IS 'Whether the landing page is active and accepting leads';
COMMENT ON COLUMN property_reports.expires_at IS 'Auto-deactivate landing page after this time (NULL = never)';
COMMENT ON COLUMN property_reports.max_leads IS 'Auto-deactivate after this many leads (NULL = unlimited)';
COMMENT ON COLUMN property_reports.access_code IS 'Optional password protection for landing page';
COMMENT ON COLUMN property_reports.error_message IS 'Error details if PDF generation failed';

COMMENT ON TABLE leads IS 'Lead capture from property report QR scans and direct links';
COMMENT ON COLUMN leads.source IS 'qr_scan = scanned QR code, direct_link = clicked link directly';
COMMENT ON COLUMN leads.consent_given IS 'Whether the lead gave consent to be contacted';
COMMENT ON COLUMN leads.sms_sent_at IS 'Timestamp when SMS notification was sent to agent';
COMMENT ON COLUMN leads.email_sent_at IS 'Timestamp when email notification was sent to agent';
COMMENT ON COLUMN leads.status IS 'Lead status: new = uncontacted, contacted = follow-up made, converted = became client';
COMMENT ON COLUMN leads.notes IS 'Agent notes about this lead';
COMMENT ON COLUMN leads.ip_address IS 'IP address of lead submission for spam tracking';
COMMENT ON COLUMN leads.user_agent IS 'Browser user agent for analytics';

COMMENT ON TABLE blocked_ips IS 'Blocked IP addresses for spam prevention';
COMMENT ON COLUMN blocked_ips.expires_at IS 'When block expires (NULL = permanent)';

COMMENT ON TABLE lead_rate_limits IS 'Rate limiting records for lead submissions per IP per report';

-- ============================================================================
-- VERIFICATION
-- ============================================================================

SELECT '0034_property_reports.sql applied successfully' AS migration;


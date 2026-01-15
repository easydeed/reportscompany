-- =============================================
-- Migration 0039: Lead Pages Feature
-- =============================================
-- Adds agent codes, landing page settings, SMS logging

-- =============================================
-- 1. ADD AGENT CODE AND LANDING PAGE COLUMNS TO USERS
-- =============================================

-- Unique agent code for shareable URLs (e.g., "ZOE2024")
ALTER TABLE users ADD COLUMN IF NOT EXISTS agent_code VARCHAR(10) UNIQUE;

-- Landing page customization
ALTER TABLE users ADD COLUMN IF NOT EXISTS landing_page_headline VARCHAR(255) 
    DEFAULT 'Get Your Free Home Value Report';
ALTER TABLE users ADD COLUMN IF NOT EXISTS landing_page_subheadline TEXT 
    DEFAULT 'Find out what your home is worth in today''s market.';
ALTER TABLE users ADD COLUMN IF NOT EXISTS landing_page_theme_color VARCHAR(7) 
    DEFAULT '#8B5CF6';
ALTER TABLE users ADD COLUMN IF NOT EXISTS landing_page_enabled BOOLEAN DEFAULT true;
ALTER TABLE users ADD COLUMN IF NOT EXISTS landing_page_visits INTEGER DEFAULT 0;

-- Agent profile fields (if not already present)
ALTER TABLE users ADD COLUMN IF NOT EXISTS photo_url TEXT;
ALTER TABLE users ADD COLUMN IF NOT EXISTS license_number VARCHAR(50);

-- Index for fast agent_code lookups
CREATE INDEX IF NOT EXISTS idx_users_agent_code ON users(agent_code) WHERE agent_code IS NOT NULL;


-- =============================================
-- 2. ADD SMS CREDITS TO ACCOUNTS
-- =============================================

ALTER TABLE accounts ADD COLUMN IF NOT EXISTS sms_credits INTEGER DEFAULT 0;

COMMENT ON COLUMN accounts.sms_credits IS 'Number of SMS credits available for lead notifications';


-- =============================================
-- 3. SMS LOGS TABLE
-- =============================================

-- Create sms_logs table if it doesn't exist
CREATE TABLE IF NOT EXISTS sms_logs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    account_id UUID REFERENCES accounts(id) ON DELETE CASCADE,
    consumer_report_id UUID,  -- Reference to consumer_reports if exists
    direction VARCHAR(10) DEFAULT 'outbound',
    recipient_type VARCHAR(20),
    to_phone VARCHAR(20) NOT NULL,
    from_phone VARCHAR(20) NOT NULL,
    message_body TEXT,
    twilio_sid VARCHAR(50),
    status VARCHAR(20) DEFAULT 'queued',
    error_code VARCHAR(10),
    error_message TEXT,
    segments INTEGER DEFAULT 1,
    price_cents INTEGER,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Add columns to existing sms_logs table if they don't exist
DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name = 'sms_logs' AND column_name = 'consumer_report_id') THEN
        ALTER TABLE sms_logs ADD COLUMN consumer_report_id UUID;
    END IF;
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name = 'sms_logs' AND column_name = 'direction') THEN
        ALTER TABLE sms_logs ADD COLUMN direction VARCHAR(10) DEFAULT 'outbound';
    END IF;
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name = 'sms_logs' AND column_name = 'recipient_type') THEN
        ALTER TABLE sms_logs ADD COLUMN recipient_type VARCHAR(20);
    END IF;
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name = 'sms_logs' AND column_name = 'message_body') THEN
        ALTER TABLE sms_logs ADD COLUMN message_body TEXT;
    END IF;
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name = 'sms_logs' AND column_name = 'segments') THEN
        ALTER TABLE sms_logs ADD COLUMN segments INTEGER DEFAULT 1;
    END IF;
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name = 'sms_logs' AND column_name = 'price_cents') THEN
        ALTER TABLE sms_logs ADD COLUMN price_cents INTEGER;
    END IF;
END $$;

-- Indexes
CREATE INDEX IF NOT EXISTS idx_sms_logs_account ON sms_logs(account_id);
CREATE INDEX IF NOT EXISTS idx_sms_logs_consumer_report ON sms_logs(consumer_report_id);
CREATE INDEX IF NOT EXISTS idx_sms_logs_created ON sms_logs(created_at DESC);

COMMENT ON TABLE sms_logs IS 'Log of all SMS messages sent through the platform';


-- =============================================
-- 4. ADD PROPERTY_OWNER TO CONSUMER_REPORTS
-- =============================================

ALTER TABLE consumer_reports ADD COLUMN IF NOT EXISTS property_owner VARCHAR(255);


-- =============================================
-- 5. VIEWS FOR LEAD PAGE ANALYTICS
-- =============================================

-- Agent lead page performance
CREATE OR REPLACE VIEW agent_lead_page_stats AS
SELECT 
    u.id as user_id,
    u.agent_code,
    CONCAT(u.first_name, ' ', u.last_name) as agent_name,
    u.landing_page_visits,
    COUNT(cr.id) as total_leads,
    COUNT(cr.id) FILTER (WHERE cr.created_at > NOW() - INTERVAL '7 days') as leads_7d,
    COUNT(cr.id) FILTER (WHERE cr.created_at > NOW() - INTERVAL '30 days') as leads_30d,
    COUNT(cr.id) FILTER (WHERE cr.agent_contact_clicked = true) as contacts,
    ROUND(
        COUNT(cr.id) FILTER (WHERE cr.agent_contact_clicked = true)::numeric / 
        NULLIF(COUNT(cr.id), 0) * 100, 1
    ) as contact_rate_pct,
    ROUND(
        COUNT(cr.id)::numeric / 
        NULLIF(u.landing_page_visits, 0) * 100, 1
    ) as conversion_rate_pct
FROM users u
LEFT JOIN consumer_reports cr ON cr.agent_id = u.id
WHERE u.agent_code IS NOT NULL
GROUP BY u.id, u.agent_code, u.first_name, u.last_name, u.landing_page_visits;

COMMENT ON VIEW agent_lead_page_stats IS 'Performance metrics for each agent''s lead page';


-- =============================================
-- 6. FUNCTION TO GENERATE UNIQUE AGENT CODE
-- =============================================

CREATE OR REPLACE FUNCTION generate_agent_code() 
RETURNS VARCHAR(10) AS $$
DECLARE
    chars VARCHAR(32) := 'ABCDEFGHJKMNPQRSTUVWXYZ23456789';  -- No 0/O, I/L confusion
    code VARCHAR(6);
    attempts INTEGER := 0;
BEGIN
    LOOP
        code := '';
        FOR i IN 1..6 LOOP
            code := code || SUBSTR(chars, FLOOR(RANDOM() * 32 + 1)::INTEGER, 1);
        END LOOP;
        
        -- Check if code already exists
        IF NOT EXISTS (SELECT 1 FROM users WHERE agent_code = code) THEN
            RETURN code;
        END IF;
        
        attempts := attempts + 1;
        IF attempts > 100 THEN
            RAISE EXCEPTION 'Could not generate unique agent code after 100 attempts';
        END IF;
    END LOOP;
END;
$$ LANGUAGE plpgsql;

COMMENT ON FUNCTION generate_agent_code() IS 'Generates a unique 6-character agent code';


-- =============================================
-- 7. TRIGGER TO AUTO-GENERATE AGENT CODE ON USER CREATE
-- =============================================

CREATE OR REPLACE FUNCTION set_agent_code_on_insert()
RETURNS TRIGGER AS $$
BEGIN
    IF NEW.agent_code IS NULL THEN
        NEW.agent_code := generate_agent_code();
    END IF;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS trigger_set_agent_code ON users;
CREATE TRIGGER trigger_set_agent_code
    BEFORE INSERT ON users
    FOR EACH ROW
    EXECUTE FUNCTION set_agent_code_on_insert();

COMMENT ON TRIGGER trigger_set_agent_code ON users IS 'Auto-generates agent_code for new users';


-- =============================================
-- 8. GENERATE CODES FOR EXISTING USERS
-- =============================================

-- Generate agent codes for all existing users who don't have one
DO $$
DECLARE
    user_record RECORD;
BEGIN
    FOR user_record IN SELECT id FROM users WHERE agent_code IS NULL
    LOOP
        UPDATE users SET agent_code = generate_agent_code() WHERE id = user_record.id;
    END LOOP;
END $$;



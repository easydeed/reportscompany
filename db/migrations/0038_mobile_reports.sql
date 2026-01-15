-- =============================================
-- Migration 0038: Mobile Report Viewer
-- =============================================
-- Consumer reports with mobile-first approach
-- PDF generated only on demand

-- =============================================
-- CONSUMER REPORTS TABLE
-- =============================================

CREATE TABLE IF NOT EXISTS consumer_reports (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    
    -- Agent link
    agent_id UUID REFERENCES users(id) ON DELETE CASCADE NOT NULL,
    agent_code VARCHAR(10) NOT NULL,
    
    -- Consumer info (the lead)
    consumer_phone VARCHAR(20) NOT NULL,
    consumer_email VARCHAR(255),
    consent_given BOOLEAN DEFAULT false,
    consent_timestamp TIMESTAMPTZ,
    
    -- Property data (JSON - powers mobile view)
    property_address TEXT NOT NULL,
    property_city VARCHAR(100),
    property_state VARCHAR(2),
    property_zip VARCHAR(10),
    property_data JSONB NOT NULL DEFAULT '{}',      -- Full SiteX response
    comparables JSONB NOT NULL DEFAULT '[]',        -- Auto-selected comps
    market_stats JSONB DEFAULT '{}',                -- Area statistics
    value_estimate JSONB DEFAULT '{}',              -- Low/mid/high range
    
    -- Report status
    status VARCHAR(20) DEFAULT 'pending',           -- pending, ready, failed
    error_message TEXT,
    
    -- PDF (only generated on demand)
    pdf_url TEXT,                                   -- NULL until requested
    pdf_generated_at TIMESTAMPTZ,                   -- When PDF was created
    pdf_requested_count INTEGER DEFAULT 0,          -- How many times downloaded
    
    -- SMS tracking
    consumer_sms_sent_at TIMESTAMPTZ,
    consumer_sms_sid VARCHAR(50),
    agent_sms_sent_at TIMESTAMPTZ,
    agent_sms_sid VARCHAR(50),
    
    -- Engagement metrics
    view_count INTEGER DEFAULT 0,                   -- Mobile page views
    unique_views INTEGER DEFAULT 0,                 -- Unique visitors
    first_viewed_at TIMESTAMPTZ,
    last_viewed_at TIMESTAMPTZ,
    tabs_viewed JSONB DEFAULT '[]',                 -- Which tabs user viewed
    time_on_page INTEGER DEFAULT 0,                 -- Seconds spent
    agent_contact_clicked BOOLEAN DEFAULT false,    -- Did they tap call/text?
    agent_contact_type VARCHAR(20),                 -- 'call', 'text', 'email'
    
    -- Metadata
    ip_address INET,
    user_agent TEXT,
    device_type VARCHAR(20),                        -- 'mobile', 'tablet', 'desktop'
    referrer TEXT,
    
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Indexes
CREATE INDEX IF NOT EXISTS idx_consumer_reports_agent ON consumer_reports(agent_id);
CREATE INDEX IF NOT EXISTS idx_consumer_reports_code ON consumer_reports(agent_code);
CREATE INDEX IF NOT EXISTS idx_consumer_reports_status ON consumer_reports(status);
CREATE INDEX IF NOT EXISTS idx_consumer_reports_created ON consumer_reports(created_at DESC);

-- =============================================
-- REPORT ANALYTICS TABLE (Detailed tracking)
-- =============================================

CREATE TABLE IF NOT EXISTS report_analytics (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    report_id UUID REFERENCES consumer_reports(id) ON DELETE CASCADE,
    
    -- Event tracking
    event_type VARCHAR(50) NOT NULL,    -- 'view', 'tab_change', 'pdf_request', 'agent_click', 'share'
    event_data JSONB DEFAULT '{}',       -- Additional event details
    
    -- Session info
    session_id VARCHAR(100),
    
    -- Device/location
    ip_address INET,
    user_agent TEXT,
    device_type VARCHAR(20),
    
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_report_analytics_report ON report_analytics(report_id);
CREATE INDEX IF NOT EXISTS idx_report_analytics_type ON report_analytics(event_type);
CREATE INDEX IF NOT EXISTS idx_report_analytics_created ON report_analytics(created_at DESC);

-- =============================================
-- ADMIN METRICS VIEWS
-- =============================================

-- Daily metrics summary
CREATE OR REPLACE VIEW admin_daily_metrics AS
SELECT 
    DATE(created_at) as date,
    COUNT(*) as reports_requested,
    COUNT(*) FILTER (WHERE status = 'ready') as reports_ready,
    COUNT(*) FILTER (WHERE status = 'failed') as reports_failed,
    COUNT(*) FILTER (WHERE pdf_url IS NOT NULL) as pdfs_generated,
    COUNT(*) FILTER (WHERE agent_contact_clicked = true) as agent_contacts,
    SUM(view_count) as total_views,
    AVG(view_count) as avg_views_per_report,
    AVG(time_on_page) as avg_time_seconds,
    COUNT(DISTINCT agent_id) as unique_agents
FROM consumer_reports
GROUP BY DATE(created_at)
ORDER BY date DESC;

-- Agent leaderboard
CREATE OR REPLACE VIEW admin_agent_leaderboard AS
SELECT 
    u.id as agent_id,
    CONCAT(u.first_name, ' ', u.last_name) as agent_name,
    u.email as agent_email,
    a.name as account_name,
    COUNT(cr.id) as total_reports,
    COUNT(cr.id) FILTER (WHERE cr.created_at > NOW() - INTERVAL '30 days') as reports_30d,
    COALESCE(SUM(cr.view_count), 0) as total_views,
    COUNT(cr.id) FILTER (WHERE cr.agent_contact_clicked = true) as contacts,
    ROUND(
        COUNT(cr.id) FILTER (WHERE cr.agent_contact_clicked = true)::numeric / 
        NULLIF(COUNT(cr.id), 0) * 100, 1
    ) as contact_rate_pct,
    COUNT(cr.id) FILTER (WHERE cr.pdf_url IS NOT NULL) as pdfs_downloaded
FROM users u
JOIN accounts a ON u.account_id = a.id
LEFT JOIN consumer_reports cr ON cr.agent_id = u.id
GROUP BY u.id, u.first_name, u.last_name, u.email, a.name
ORDER BY total_reports DESC;

-- Hourly distribution (for load planning)
CREATE OR REPLACE VIEW admin_hourly_distribution AS
SELECT 
    EXTRACT(HOUR FROM created_at) as hour,
    COUNT(*) as report_count,
    COUNT(*) FILTER (WHERE pdf_url IS NOT NULL) as pdf_count
FROM consumer_reports
WHERE created_at > NOW() - INTERVAL '30 days'
GROUP BY EXTRACT(HOUR FROM created_at)
ORDER BY hour;

-- Trigger for updated_at
CREATE OR REPLACE FUNCTION update_consumer_reports_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS trigger_consumer_reports_updated_at ON consumer_reports;
CREATE TRIGGER trigger_consumer_reports_updated_at
    BEFORE UPDATE ON consumer_reports
    FOR EACH ROW
    EXECUTE FUNCTION update_consumer_reports_updated_at();


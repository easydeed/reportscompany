-- =============================================
-- Migration 0044: CMA Funnel Redesign
-- =============================================
-- Supports the new address-first CMA funnel:
--   1. Expand leads.source to include 'cma_page'
--   2. Add consumer_report_id FK to leads for CMA-originated leads
--   3. Add email delivery support to consumer_reports
--   4. Allow custom agent codes (relax length constraint)

-- 1. Expand leads.source CHECK constraint to include cma_page, manual, widget
ALTER TABLE leads DROP CONSTRAINT IF EXISTS leads_source_check;
ALTER TABLE leads ADD CONSTRAINT leads_source_check
    CHECK (source IN ('qr_scan', 'direct_link', 'cma_page', 'manual', 'widget'));

-- 2. Add consumer_report_id to leads so CMA leads link back to generated report
ALTER TABLE leads ADD COLUMN IF NOT EXISTS consumer_report_id UUID;

-- 3. Add email delivery fields to consumer_reports
ALTER TABLE consumer_reports ADD COLUMN IF NOT EXISTS consumer_email VARCHAR(255);
ALTER TABLE consumer_reports ADD COLUMN IF NOT EXISTS delivery_method VARCHAR(10)
    DEFAULT 'sms' CHECK (delivery_method IN ('sms', 'email'));
ALTER TABLE consumer_reports ADD COLUMN IF NOT EXISTS consumer_email_sent_at TIMESTAMPTZ;

-- 4. Allow custom agent codes — relax from VARCHAR(10) to VARCHAR(20)
-- Must drop and recreate dependent view first
DROP VIEW IF EXISTS agent_lead_page_stats;

ALTER TABLE users ALTER COLUMN agent_code TYPE VARCHAR(20);

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

-- 5. Index for consumer_report_id on leads
CREATE INDEX IF NOT EXISTS idx_leads_consumer_report
    ON leads(consumer_report_id) WHERE consumer_report_id IS NOT NULL;

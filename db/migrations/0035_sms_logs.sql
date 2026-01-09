-- Migration 0035: SMS Logs
-- Date: 2026-01-09
-- Purpose: Track SMS messages sent for lead notifications

-- ============================================================================
-- TABLE: sms_logs - Track all SMS messages sent
-- ============================================================================

CREATE TABLE IF NOT EXISTS sms_logs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    account_id UUID REFERENCES accounts(id) ON DELETE CASCADE,
    lead_id UUID REFERENCES leads(id) ON DELETE SET NULL,
    to_phone VARCHAR(20) NOT NULL,
    from_phone VARCHAR(20) NOT NULL,
    message TEXT NOT NULL,
    status VARCHAR(20) DEFAULT 'sent' CHECK (status IN ('sent', 'delivered', 'failed', 'pending')),
    twilio_sid VARCHAR(50),
    error_message TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Indexes
CREATE INDEX IF NOT EXISTS idx_sms_logs_account ON sms_logs(account_id);
CREATE INDEX IF NOT EXISTS idx_sms_logs_created ON sms_logs(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_sms_logs_lead ON sms_logs(lead_id) WHERE lead_id IS NOT NULL;
CREATE INDEX IF NOT EXISTS idx_sms_logs_status ON sms_logs(status);

-- Comments
COMMENT ON TABLE sms_logs IS 'Log of all SMS messages sent via Twilio for lead notifications';
COMMENT ON COLUMN sms_logs.twilio_sid IS 'Twilio message SID for tracking delivery status';
COMMENT ON COLUMN sms_logs.status IS 'sent = sent to Twilio, delivered = confirmed delivery, failed = delivery failed';

-- ============================================================================
-- VERIFICATION
-- ============================================================================

SELECT '0035_sms_logs.sql applied successfully' AS migration;


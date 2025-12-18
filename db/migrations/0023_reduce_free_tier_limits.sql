-- Migration 0019: Reduce free tier report limits
-- Date: 2024-12-18
-- Purpose: Reduce free plan from 50 reports to 5 reports per month to encourage upgrades

-- Update free plan: 50 -> 5 reports
UPDATE plans
SET monthly_report_limit = 5,
    updated_at = NOW()
WHERE plan_slug = 'free';

-- Update sponsored_free plan: 75 -> 10 reports (still more than free, but reasonable)
UPDATE plans
SET monthly_report_limit = 10,
    updated_at = NOW()
WHERE plan_slug = 'sponsored_free';

-- Add comment explaining the change
COMMENT ON COLUMN plans.monthly_report_limit IS 'Base monthly report generation limit. Free=5, Pro=300, Team=1000, Affiliate=5000';

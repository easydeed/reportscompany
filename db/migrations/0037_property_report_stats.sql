-- Migration 0037: Property Report Statistics & Analytics
-- Date: 2026-01-14
-- Purpose: Add comprehensive stats tracking for property reports at agent, affiliate, and admin levels
--
-- New Tables:
--   - property_report_stats: Per-account aggregated statistics (refreshed periodically)
--   - property_report_stats_daily: Daily snapshots for trending/charts
--
-- New Functions:
--   - refresh_property_report_stats(): Recalculates all stats
--   - refresh_account_property_stats(uuid): Recalculates for one account

-- ============================================================================
-- TABLE: property_report_stats (Per-Account Aggregates)
-- ============================================================================

CREATE TABLE IF NOT EXISTS property_report_stats (
    account_id UUID PRIMARY KEY REFERENCES accounts(id) ON DELETE CASCADE,
    
    -- Report counts
    total_reports INTEGER NOT NULL DEFAULT 0,
    completed_reports INTEGER NOT NULL DEFAULT 0,
    failed_reports INTEGER NOT NULL DEFAULT 0,
    draft_reports INTEGER NOT NULL DEFAULT 0,
    processing_reports INTEGER NOT NULL DEFAULT 0,
    
    -- Report breakdown
    seller_reports INTEGER NOT NULL DEFAULT 0,
    buyer_reports INTEGER NOT NULL DEFAULT 0,
    
    -- Theme usage
    theme_classic INTEGER NOT NULL DEFAULT 0,
    theme_modern INTEGER NOT NULL DEFAULT 0,
    theme_elegant INTEGER NOT NULL DEFAULT 0,
    theme_teal INTEGER NOT NULL DEFAULT 0,
    theme_bold INTEGER NOT NULL DEFAULT 0,
    
    -- Engagement metrics
    total_views INTEGER NOT NULL DEFAULT 0,
    unique_visitors INTEGER NOT NULL DEFAULT 0,
    active_landing_pages INTEGER NOT NULL DEFAULT 0,
    
    -- Lead metrics
    total_leads INTEGER NOT NULL DEFAULT 0,
    leads_from_qr INTEGER NOT NULL DEFAULT 0,
    leads_from_direct INTEGER NOT NULL DEFAULT 0,
    leads_converted INTEGER NOT NULL DEFAULT 0,
    
    -- Calculated rates (stored for fast queries)
    conversion_rate DECIMAL(5,2) DEFAULT 0,          -- leads / unique_visitors * 100
    completion_rate DECIMAL(5,2) DEFAULT 0,          -- completed / total * 100
    
    -- Time-bound stats (rolling 30 days)
    reports_last_30d INTEGER NOT NULL DEFAULT 0,
    leads_last_30d INTEGER NOT NULL DEFAULT 0,
    views_last_30d INTEGER NOT NULL DEFAULT 0,
    
    -- Last activity tracking
    last_report_at TIMESTAMPTZ,
    last_lead_at TIMESTAMPTZ,
    
    -- Metadata
    stats_updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Index for sponsor lookups (affiliate roll-ups)
CREATE INDEX IF NOT EXISTS idx_property_report_stats_updated 
    ON property_report_stats(stats_updated_at);

COMMENT ON TABLE property_report_stats IS 'Aggregated property report statistics per account for dashboards';
COMMENT ON COLUMN property_report_stats.conversion_rate IS 'Percentage: (total_leads / unique_visitors) * 100';
COMMENT ON COLUMN property_report_stats.completion_rate IS 'Percentage: (completed_reports / total_reports) * 100';

-- ============================================================================
-- TABLE: property_report_stats_daily (Historical Snapshots)
-- ============================================================================

CREATE TABLE IF NOT EXISTS property_report_stats_daily (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    account_id UUID NOT NULL REFERENCES accounts(id) ON DELETE CASCADE,
    stat_date DATE NOT NULL,
    
    -- Daily counts
    reports_created INTEGER NOT NULL DEFAULT 0,
    reports_completed INTEGER NOT NULL DEFAULT 0,
    reports_failed INTEGER NOT NULL DEFAULT 0,
    
    -- Daily engagement
    views INTEGER NOT NULL DEFAULT 0,
    unique_visitors INTEGER NOT NULL DEFAULT 0,
    
    -- Daily leads
    leads_captured INTEGER NOT NULL DEFAULT 0,
    leads_from_qr INTEGER NOT NULL DEFAULT 0,
    leads_from_direct INTEGER NOT NULL DEFAULT 0,
    
    -- Theme breakdown (daily)
    theme_classic INTEGER NOT NULL DEFAULT 0,
    theme_modern INTEGER NOT NULL DEFAULT 0,
    theme_elegant INTEGER NOT NULL DEFAULT 0,
    theme_teal INTEGER NOT NULL DEFAULT 0,
    theme_bold INTEGER NOT NULL DEFAULT 0,
    
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    
    UNIQUE(account_id, stat_date)
);

CREATE INDEX IF NOT EXISTS idx_property_report_stats_daily_account_date 
    ON property_report_stats_daily(account_id, stat_date DESC);
CREATE INDEX IF NOT EXISTS idx_property_report_stats_daily_date 
    ON property_report_stats_daily(stat_date DESC);

COMMENT ON TABLE property_report_stats_daily IS 'Daily snapshots of property report activity for charts and trending';

-- ============================================================================
-- TABLE: platform_property_stats (Admin-Level Platform Totals)
-- ============================================================================

CREATE TABLE IF NOT EXISTS platform_property_stats (
    id INTEGER PRIMARY KEY DEFAULT 1 CHECK (id = 1),  -- Singleton row
    
    -- Platform totals
    total_reports INTEGER NOT NULL DEFAULT 0,
    completed_reports INTEGER NOT NULL DEFAULT 0,
    failed_reports INTEGER NOT NULL DEFAULT 0,
    
    -- By account type
    reports_by_regular INTEGER NOT NULL DEFAULT 0,
    reports_by_sponsored INTEGER NOT NULL DEFAULT 0,
    reports_by_affiliate INTEGER NOT NULL DEFAULT 0,
    
    -- Platform engagement
    total_views INTEGER NOT NULL DEFAULT 0,
    total_unique_visitors INTEGER NOT NULL DEFAULT 0,
    total_leads INTEGER NOT NULL DEFAULT 0,
    
    -- Active counts
    accounts_with_reports INTEGER NOT NULL DEFAULT 0,
    active_landing_pages INTEGER NOT NULL DEFAULT 0,
    
    -- Theme popularity
    theme_classic INTEGER NOT NULL DEFAULT 0,
    theme_modern INTEGER NOT NULL DEFAULT 0,
    theme_elegant INTEGER NOT NULL DEFAULT 0,
    theme_teal INTEGER NOT NULL DEFAULT 0,
    theme_bold INTEGER NOT NULL DEFAULT 0,
    
    -- Rolling 30-day
    reports_last_30d INTEGER NOT NULL DEFAULT 0,
    leads_last_30d INTEGER NOT NULL DEFAULT 0,
    
    -- Rates
    platform_conversion_rate DECIMAL(5,2) DEFAULT 0,
    platform_completion_rate DECIMAL(5,2) DEFAULT 0,
    avg_reports_per_account DECIMAL(8,2) DEFAULT 0,
    
    stats_updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Initialize singleton row
INSERT INTO platform_property_stats (id) VALUES (1) ON CONFLICT (id) DO NOTHING;

COMMENT ON TABLE platform_property_stats IS 'Platform-wide property report statistics for admin dashboard';

-- ============================================================================
-- FUNCTION: refresh_account_property_stats(account_id)
-- Refreshes stats for a single account
-- ============================================================================

CREATE OR REPLACE FUNCTION refresh_account_property_stats(target_account_id UUID)
RETURNS VOID AS $$
DECLARE
    report_stats RECORD;
    lead_stats RECORD;
    thirty_days_ago TIMESTAMPTZ := NOW() - INTERVAL '30 days';
BEGIN
    -- Get report statistics
    SELECT
        COUNT(*) AS total,
        COUNT(*) FILTER (WHERE status = 'complete') AS completed,
        COUNT(*) FILTER (WHERE status = 'failed') AS failed,
        COUNT(*) FILTER (WHERE status = 'draft') AS draft,
        COUNT(*) FILTER (WHERE status = 'processing') AS processing,
        COUNT(*) FILTER (WHERE report_type = 'seller') AS seller,
        COUNT(*) FILTER (WHERE report_type = 'buyer') AS buyer,
        COUNT(*) FILTER (WHERE theme = 1) AS t1,
        COUNT(*) FILTER (WHERE theme = 2) AS t2,
        COUNT(*) FILTER (WHERE theme = 3) AS t3,
        COUNT(*) FILTER (WHERE theme = 4) AS t4,
        COUNT(*) FILTER (WHERE theme = 5) AS t5,
        COALESCE(SUM(view_count), 0) AS views,
        COALESCE(SUM(unique_visitors), 0) AS visitors,
        COUNT(*) FILTER (WHERE is_active = TRUE AND (expires_at IS NULL OR expires_at > NOW())) AS active_pages,
        MAX(created_at) AS last_report,
        COUNT(*) FILTER (WHERE created_at >= thirty_days_ago) AS reports_30d
    INTO report_stats
    FROM property_reports
    WHERE account_id = target_account_id;
    
    -- Get lead statistics
    SELECT
        COUNT(*) AS total,
        COUNT(*) FILTER (WHERE source = 'qr_scan') AS from_qr,
        COUNT(*) FILTER (WHERE source = 'direct_link') AS from_direct,
        COUNT(*) FILTER (WHERE status = 'converted') AS converted,
        MAX(created_at) AS last_lead,
        COUNT(*) FILTER (WHERE created_at >= thirty_days_ago) AS leads_30d
    INTO lead_stats
    FROM leads
    WHERE account_id = target_account_id;
    
    -- Upsert stats
    INSERT INTO property_report_stats (
        account_id,
        total_reports, completed_reports, failed_reports, draft_reports, processing_reports,
        seller_reports, buyer_reports,
        theme_classic, theme_modern, theme_elegant, theme_teal, theme_bold,
        total_views, unique_visitors, active_landing_pages,
        total_leads, leads_from_qr, leads_from_direct, leads_converted,
        conversion_rate, completion_rate,
        reports_last_30d, leads_last_30d, views_last_30d,
        last_report_at, last_lead_at,
        stats_updated_at
    ) VALUES (
        target_account_id,
        report_stats.total, report_stats.completed, report_stats.failed, report_stats.draft, report_stats.processing,
        report_stats.seller, report_stats.buyer,
        report_stats.t1, report_stats.t2, report_stats.t3, report_stats.t4, report_stats.t5,
        report_stats.views, report_stats.visitors, report_stats.active_pages,
        lead_stats.total, lead_stats.from_qr, lead_stats.from_direct, lead_stats.converted,
        CASE WHEN report_stats.visitors > 0 THEN ROUND((lead_stats.total::DECIMAL / report_stats.visitors) * 100, 2) ELSE 0 END,
        CASE WHEN report_stats.total > 0 THEN ROUND((report_stats.completed::DECIMAL / report_stats.total) * 100, 2) ELSE 0 END,
        report_stats.reports_30d, lead_stats.leads_30d, 0,  -- views_last_30d needs separate calculation
        report_stats.last_report, lead_stats.last_lead,
        NOW()
    )
    ON CONFLICT (account_id) DO UPDATE SET
        total_reports = EXCLUDED.total_reports,
        completed_reports = EXCLUDED.completed_reports,
        failed_reports = EXCLUDED.failed_reports,
        draft_reports = EXCLUDED.draft_reports,
        processing_reports = EXCLUDED.processing_reports,
        seller_reports = EXCLUDED.seller_reports,
        buyer_reports = EXCLUDED.buyer_reports,
        theme_classic = EXCLUDED.theme_classic,
        theme_modern = EXCLUDED.theme_modern,
        theme_elegant = EXCLUDED.theme_elegant,
        theme_teal = EXCLUDED.theme_teal,
        theme_bold = EXCLUDED.theme_bold,
        total_views = EXCLUDED.total_views,
        unique_visitors = EXCLUDED.unique_visitors,
        active_landing_pages = EXCLUDED.active_landing_pages,
        total_leads = EXCLUDED.total_leads,
        leads_from_qr = EXCLUDED.leads_from_qr,
        leads_from_direct = EXCLUDED.leads_from_direct,
        leads_converted = EXCLUDED.leads_converted,
        conversion_rate = EXCLUDED.conversion_rate,
        completion_rate = EXCLUDED.completion_rate,
        reports_last_30d = EXCLUDED.reports_last_30d,
        leads_last_30d = EXCLUDED.leads_last_30d,
        last_report_at = EXCLUDED.last_report_at,
        last_lead_at = EXCLUDED.last_lead_at,
        stats_updated_at = NOW();
END;
$$ LANGUAGE plpgsql;

COMMENT ON FUNCTION refresh_account_property_stats(UUID) IS 'Refresh property report statistics for a single account';

-- ============================================================================
-- FUNCTION: refresh_all_property_stats()
-- Refreshes stats for all accounts and platform totals
-- ============================================================================

CREATE OR REPLACE FUNCTION refresh_all_property_stats()
RETURNS VOID AS $$
DECLARE
    acct RECORD;
    platform RECORD;
    thirty_days_ago TIMESTAMPTZ := NOW() - INTERVAL '30 days';
BEGIN
    -- Refresh each account that has property reports
    FOR acct IN 
        SELECT DISTINCT account_id FROM property_reports
        UNION
        SELECT DISTINCT account_id FROM leads
    LOOP
        PERFORM refresh_account_property_stats(acct.account_id);
    END LOOP;
    
    -- Refresh platform totals
    SELECT
        COUNT(*) AS total,
        COUNT(*) FILTER (WHERE status = 'complete') AS completed,
        COUNT(*) FILTER (WHERE status = 'failed') AS failed,
        COUNT(*) FILTER (WHERE theme = 1) AS t1,
        COUNT(*) FILTER (WHERE theme = 2) AS t2,
        COUNT(*) FILTER (WHERE theme = 3) AS t3,
        COUNT(*) FILTER (WHERE theme = 4) AS t4,
        COUNT(*) FILTER (WHERE theme = 5) AS t5,
        COALESCE(SUM(view_count), 0) AS views,
        COALESCE(SUM(unique_visitors), 0) AS visitors,
        COUNT(*) FILTER (WHERE is_active = TRUE) AS active_pages,
        COUNT(DISTINCT account_id) AS accounts,
        COUNT(*) FILTER (WHERE created_at >= thirty_days_ago) AS reports_30d
    INTO platform
    FROM property_reports;
    
    UPDATE platform_property_stats SET
        total_reports = platform.total,
        completed_reports = platform.completed,
        failed_reports = platform.failed,
        theme_classic = platform.t1,
        theme_modern = platform.t2,
        theme_elegant = platform.t3,
        theme_teal = platform.t4,
        theme_bold = platform.t5,
        total_views = platform.views,
        total_unique_visitors = platform.visitors,
        active_landing_pages = platform.active_pages,
        accounts_with_reports = platform.accounts,
        reports_last_30d = platform.reports_30d,
        total_leads = (SELECT COUNT(*) FROM leads),
        leads_last_30d = (SELECT COUNT(*) FROM leads WHERE created_at >= thirty_days_ago),
        platform_conversion_rate = CASE WHEN platform.visitors > 0 
            THEN ROUND(((SELECT COUNT(*) FROM leads)::DECIMAL / platform.visitors) * 100, 2) 
            ELSE 0 END,
        platform_completion_rate = CASE WHEN platform.total > 0 
            THEN ROUND((platform.completed::DECIMAL / platform.total) * 100, 2) 
            ELSE 0 END,
        avg_reports_per_account = CASE WHEN platform.accounts > 0 
            THEN ROUND(platform.total::DECIMAL / platform.accounts, 2) 
            ELSE 0 END,
        -- Account type breakdown
        reports_by_regular = (
            SELECT COUNT(*) FROM property_reports pr
            JOIN accounts a ON a.id = pr.account_id
            WHERE a.account_type = 'REGULAR' AND a.sponsor_account_id IS NULL
        ),
        reports_by_sponsored = (
            SELECT COUNT(*) FROM property_reports pr
            JOIN accounts a ON a.id = pr.account_id
            WHERE a.sponsor_account_id IS NOT NULL
        ),
        reports_by_affiliate = (
            SELECT COUNT(*) FROM property_reports pr
            JOIN accounts a ON a.id = pr.account_id
            WHERE a.account_type = 'INDUSTRY_AFFILIATE'
        ),
        stats_updated_at = NOW()
    WHERE id = 1;
END;
$$ LANGUAGE plpgsql;

COMMENT ON FUNCTION refresh_all_property_stats() IS 'Refresh property report statistics for all accounts and platform totals';

-- ============================================================================
-- FUNCTION: record_daily_property_stats()
-- Records daily snapshot for historical tracking
-- ============================================================================

CREATE OR REPLACE FUNCTION record_daily_property_stats()
RETURNS VOID AS $$
DECLARE
    today DATE := CURRENT_DATE;
    yesterday DATE := CURRENT_DATE - INTERVAL '1 day';
    acct RECORD;
BEGIN
    -- Record stats for each account with activity yesterday
    FOR acct IN 
        SELECT DISTINCT account_id FROM property_reports WHERE created_at::DATE = yesterday
        UNION
        SELECT DISTINCT account_id FROM leads WHERE created_at::DATE = yesterday
    LOOP
        INSERT INTO property_report_stats_daily (
            account_id, stat_date,
            reports_created, reports_completed, reports_failed,
            views, unique_visitors,
            leads_captured, leads_from_qr, leads_from_direct,
            theme_classic, theme_modern, theme_elegant, theme_teal, theme_bold
        )
        SELECT
            acct.account_id,
            yesterday,
            COUNT(*) FILTER (WHERE pr.created_at::DATE = yesterday),
            COUNT(*) FILTER (WHERE pr.status = 'complete' AND pr.created_at::DATE = yesterday),
            COUNT(*) FILTER (WHERE pr.status = 'failed' AND pr.created_at::DATE = yesterday),
            0, 0,  -- views/visitors would need separate tracking
            (SELECT COUNT(*) FROM leads WHERE account_id = acct.account_id AND created_at::DATE = yesterday),
            (SELECT COUNT(*) FROM leads WHERE account_id = acct.account_id AND created_at::DATE = yesterday AND source = 'qr_scan'),
            (SELECT COUNT(*) FROM leads WHERE account_id = acct.account_id AND created_at::DATE = yesterday AND source = 'direct_link'),
            COUNT(*) FILTER (WHERE pr.theme = 1 AND pr.created_at::DATE = yesterday),
            COUNT(*) FILTER (WHERE pr.theme = 2 AND pr.created_at::DATE = yesterday),
            COUNT(*) FILTER (WHERE pr.theme = 3 AND pr.created_at::DATE = yesterday),
            COUNT(*) FILTER (WHERE pr.theme = 4 AND pr.created_at::DATE = yesterday),
            COUNT(*) FILTER (WHERE pr.theme = 5 AND pr.created_at::DATE = yesterday)
        FROM property_reports pr
        WHERE pr.account_id = acct.account_id
        ON CONFLICT (account_id, stat_date) DO UPDATE SET
            reports_created = EXCLUDED.reports_created,
            reports_completed = EXCLUDED.reports_completed,
            reports_failed = EXCLUDED.reports_failed,
            leads_captured = EXCLUDED.leads_captured,
            leads_from_qr = EXCLUDED.leads_from_qr,
            leads_from_direct = EXCLUDED.leads_from_direct;
    END LOOP;
END;
$$ LANGUAGE plpgsql;

COMMENT ON FUNCTION record_daily_property_stats() IS 'Record daily snapshot of property report activity for historical charts';

-- ============================================================================
-- TRIGGER: Auto-refresh stats on property_report changes
-- ============================================================================

CREATE OR REPLACE FUNCTION trigger_refresh_property_stats()
RETURNS TRIGGER AS $$
BEGIN
    -- Refresh stats for the affected account
    -- Use NEW for INSERT/UPDATE, OLD for DELETE
    IF TG_OP = 'DELETE' THEN
        PERFORM refresh_account_property_stats(OLD.account_id);
    ELSE
        PERFORM refresh_account_property_stats(NEW.account_id);
    END IF;
    
    RETURN COALESCE(NEW, OLD);
END;
$$ LANGUAGE plpgsql;

-- Note: This trigger can be expensive on high-volume systems
-- Consider disabling and using scheduled refresh instead
DROP TRIGGER IF EXISTS trigger_property_report_stats_refresh ON property_reports;
CREATE TRIGGER trigger_property_report_stats_refresh
    AFTER INSERT OR UPDATE OF status OR DELETE ON property_reports
    FOR EACH ROW
    EXECUTE FUNCTION trigger_refresh_property_stats();

DROP TRIGGER IF EXISTS trigger_lead_stats_refresh ON leads;
CREATE TRIGGER trigger_lead_stats_refresh
    AFTER INSERT OR UPDATE OF status OR DELETE ON leads
    FOR EACH ROW
    EXECUTE FUNCTION trigger_refresh_property_stats();

-- ============================================================================
-- ROW LEVEL SECURITY
-- ============================================================================

ALTER TABLE property_report_stats ENABLE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS property_report_stats_rls ON property_report_stats;
CREATE POLICY property_report_stats_rls ON property_report_stats
    FOR ALL
    USING (
        account_id = current_setting('app.current_account_id', true)::uuid
        OR current_setting('app.current_user_role', true) = 'ADMIN'
    );

ALTER TABLE property_report_stats_daily ENABLE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS property_report_stats_daily_rls ON property_report_stats_daily;
CREATE POLICY property_report_stats_daily_rls ON property_report_stats_daily
    FOR ALL
    USING (
        account_id = current_setting('app.current_account_id', true)::uuid
        OR current_setting('app.current_user_role', true) = 'ADMIN'
    );

-- Platform stats are admin-only
ALTER TABLE platform_property_stats ENABLE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS platform_property_stats_rls ON platform_property_stats;
CREATE POLICY platform_property_stats_rls ON platform_property_stats
    FOR SELECT
    USING (current_setting('app.current_user_role', true) = 'ADMIN');

-- ============================================================================
-- INITIAL DATA POPULATION
-- ============================================================================

-- Refresh all stats on migration
SELECT refresh_all_property_stats();

-- ============================================================================
-- VERIFICATION
-- ============================================================================

SELECT '0037_property_report_stats.sql applied successfully' AS migration;


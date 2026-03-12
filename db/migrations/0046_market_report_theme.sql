-- 0046_market_report_theme.sql
-- Add theme_id and accent_color columns to report_generations
-- for server-side themed PDF rendering of market reports.

DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_name = 'report_generations' AND column_name = 'theme_id'
    ) THEN
        ALTER TABLE report_generations
            ADD COLUMN theme_id VARCHAR(20) DEFAULT NULL;
        RAISE NOTICE 'Added theme_id column to report_generations';
    END IF;

    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_name = 'report_generations' AND column_name = 'accent_color'
    ) THEN
        ALTER TABLE report_generations
            ADD COLUMN accent_color VARCHAR(7) DEFAULT NULL;
        RAISE NOTICE 'Added accent_color column to report_generations';
    END IF;
END
$$;

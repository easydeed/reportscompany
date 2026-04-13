-- Add deferred downgrade columns for honoring paid subscription periods
-- When a subscription is canceled mid-cycle, we store the downgrade date
-- instead of immediately switching to free.
DO $$
BEGIN
  IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='accounts' AND column_name='plan_downgrade_at') THEN
    ALTER TABLE accounts ADD COLUMN plan_downgrade_at TIMESTAMPTZ;
  END IF;
  IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='accounts' AND column_name='plan_downgrade_to') THEN
    ALTER TABLE accounts ADD COLUMN plan_downgrade_to VARCHAR(50);
  END IF;
END $$;

SELECT '0047_plan_downgrade_columns.sql applied' AS migration;

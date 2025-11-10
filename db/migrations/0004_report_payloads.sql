ALTER TABLE report_generations
  ADD COLUMN IF NOT EXISTS input_params JSONB,
  ADD COLUMN IF NOT EXISTS result_json JSONB,
  ADD COLUMN IF NOT EXISTS error TEXT,
  ADD COLUMN IF NOT EXISTS source_vendor TEXT DEFAULT 'simplyrets';

SELECT '0004_report_payloads.sql applied' AS migration;










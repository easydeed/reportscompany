-- Webhooks config + deliveries with RLS

CREATE TABLE IF NOT EXISTS webhooks (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  account_id UUID NOT NULL REFERENCES accounts(id) ON DELETE CASCADE,
  url TEXT NOT NULL,
  events TEXT[] NOT NULL,              -- e.g. ['report.completed','report.failed']
  secret TEXT NOT NULL,                -- random per webhook
  is_active BOOLEAN DEFAULT TRUE,
  created_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS webhook_deliveries (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  account_id UUID NOT NULL REFERENCES accounts(id) ON DELETE CASCADE,
  webhook_id UUID NOT NULL REFERENCES webhooks(id) ON DELETE CASCADE,
  event TEXT NOT NULL,
  payload JSONB NOT NULL,
  response_status INT,
  response_ms INT,
  error TEXT,
  created_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_webhooks_account ON webhooks(account_id);
CREATE INDEX IF NOT EXISTS idx_deliveries_account ON webhook_deliveries(account_id, created_at DESC);

ALTER TABLE webhooks            ENABLE ROW LEVEL SECURITY;
ALTER TABLE webhook_deliveries  ENABLE ROW LEVEL SECURITY;

DO $$
BEGIN
  IF NOT EXISTS (SELECT 1 FROM pg_policies WHERE tablename='webhooks' AND policyname='webhooks_rls') THEN
    EXECUTE 'CREATE POLICY webhooks_rls ON webhooks
      FOR ALL USING (account_id = current_setting(''app.current_account_id'', true)::uuid)
      WITH CHECK  (account_id = current_setting(''app.current_account_id'', true)::uuid)';
  END IF;

  IF NOT EXISTS (SELECT 1 FROM pg_policies WHERE tablename='webhook_deliveries' AND policyname='webhook_deliveries_rls') THEN
    EXECUTE 'CREATE POLICY webhook_deliveries_rls ON webhook_deliveries
      FOR ALL USING (account_id = current_setting(''app.current_account_id'', true)::uuid)
      WITH CHECK  (account_id = current_setting(''app.current_account_id'', true)::uuid)';
  END IF;
END $$;

SELECT '0002_webhooks.sql applied' AS migration;







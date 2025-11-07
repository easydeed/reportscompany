-- Add Stripe fields to accounts if not present
DO $$
BEGIN
  IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='accounts' AND column_name='stripe_customer_id') THEN
    ALTER TABLE accounts ADD COLUMN stripe_customer_id VARCHAR(100);
  END IF;
  IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='accounts' AND column_name='stripe_subscription_id') THEN
    ALTER TABLE accounts ADD COLUMN stripe_subscription_id VARCHAR(100);
  END IF;
  IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='accounts' AND column_name='plan_slug') THEN
    ALTER TABLE accounts ADD COLUMN plan_slug VARCHAR(50);
  END IF;
  IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='accounts' AND column_name='billing_status') THEN
    ALTER TABLE accounts ADD COLUMN billing_status VARCHAR(50);
  END IF;
END $$;

-- Optional audit table for billing events
CREATE TABLE IF NOT EXISTS billing_events (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  account_id UUID NOT NULL REFERENCES accounts(id) ON DELETE CASCADE,
  type VARCHAR(80) NOT NULL,
  payload JSONB NOT NULL,
  created_at TIMESTAMP DEFAULT NOW()
);

SELECT '0003_billing.sql applied' AS migration;








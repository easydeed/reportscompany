# Phase 29A Schema Notes

**Date:** November 14, 2025  
**Migration Base:** `db/migrations/0001_base.sql`, `0003_billing.sql`

## Current Schema State (Before Phase 29A)

### `accounts` Table
**Existing Columns:**
- `id` UUID PRIMARY KEY
- `name` VARCHAR(200)
- `slug` VARCHAR(100) UNIQUE
- `status` VARCHAR(20) DEFAULT 'active'
- `logo_url` VARCHAR(500)
- `primary_color` VARCHAR(7)
- `secondary_color` VARCHAR(7)
- `plan_id` INT (legacy, references subscription_plans)
- **`plan_slug` VARCHAR(50)** ✅ ALREADY EXISTS (from 0003_billing)
- `subscription_status` VARCHAR(50)
- `trial_ends_at` TIMESTAMP
- **`monthly_report_limit` INT DEFAULT 100** ✅ ALREADY EXISTS
- `api_rate_limit` INT DEFAULT 60
- `stripe_customer_id` VARCHAR(100) (from 0003_billing)
- `stripe_subscription_id` VARCHAR(100) (from 0003_billing)
- `billing_status` VARCHAR(50) (from 0003_billing)
- `created_at` TIMESTAMP
- `updated_at` TIMESTAMP

**Missing (Phase 29A adds):**
- `account_type` TEXT (REGULAR | INDUSTRY_AFFILIATE)
- `monthly_report_limit_override` INT
- `sponsor_account_id` UUID

### `users` Table
**Current Structure:**
- `id` UUID PRIMARY KEY
- `account_id` UUID NOT NULL REFERENCES accounts(id) ← **Single account relationship**
- `email` VARCHAR(255) UNIQUE
- `password_hash` VARCHAR(255)
- `role` VARCHAR(20) DEFAULT 'member' ← **Simple role, not tied to account**
- `email_verified` BOOLEAN
- `is_active` BOOLEAN
- `created_at` TIMESTAMP
- `updated_at` TIMESTAMP

**Issue:** Current schema assumes one user = one account. Phase 29A introduces multi-account users via `account_users` join table.

### `subscription_plans` Table (Legacy)
**Exists but not used in Phase 29A:**
- `id` SERIAL PRIMARY KEY
- `name` VARCHAR(100)
- `slug` VARCHAR(50) UNIQUE
- `price_monthly` DECIMAL(10,2)
- `price_annual` DECIMAL(10,2)
- `features` JSONB
- `is_active` BOOLEAN
- `display_order` INT

**Note:** Phase 29A creates new `plans` table with different structure (no pricing, focused on limits).

### `report_generations` Table
**Relevant Fields:**
- `id` UUID PRIMARY KEY
- `account_id` UUID NOT NULL
- `user_id` UUID (nullable)
- `report_type` VARCHAR(50)
- `status` VARCHAR(20)
- `billable` BOOLEAN DEFAULT true
- `billed_at` TIMESTAMP
- `generated_at` TIMESTAMP ← **Used for monthly usage calculation**

**RLS Enabled:** Uses `app.current_account_id` session variable.

### `usage_tracking` Table
**Relevant Fields:**
- `id` BIGSERIAL PRIMARY KEY
- `account_id` UUID NOT NULL
- `user_id` UUID
- `event_type` VARCHAR(50)
- `report_id` UUID
- `billable_units` INT DEFAULT 1
- `cost_cents` INT DEFAULT 0
- `created_at` TIMESTAMP

**RLS Enabled:** Uses `app.current_account_id` session variable.

---

## Phase 29A Migration Plan

### New Tables

#### 1. `plans` Table
```sql
CREATE TABLE IF NOT EXISTS plans (
  slug TEXT PRIMARY KEY,
  name TEXT NOT NULL,
  monthly_report_limit INT NOT NULL,
  allow_overage BOOLEAN NOT NULL DEFAULT false,
  overage_price_cents INT NOT NULL DEFAULT 0
);
```

**Seed Data:**
- `free`: 50 reports/month, no overage
- `pro`: 300 reports/month, overage @ $1.50/report
- `team`: 1000 reports/month, overage @ $1.00/report
- `affiliate`: 5000 reports/month, no overage charge
- `sponsored_free`: 75 reports/month, no overage

#### 2. `account_users` Table (Join Table for Multi-Account Users)
```sql
CREATE TABLE IF NOT EXISTS account_users (
  account_id UUID NOT NULL REFERENCES accounts(id) ON DELETE CASCADE,
  user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  role TEXT NOT NULL, -- 'OWNER' | 'MEMBER' | 'AFFILIATE' | 'ADMIN'
  PRIMARY KEY (account_id, user_id)
);
```

**Purpose:** Allows one user to belong to multiple accounts with different roles per account.

### Modified Tables

#### `accounts` - New Columns
```sql
ALTER TABLE accounts
ADD COLUMN IF NOT EXISTS account_type TEXT NOT NULL DEFAULT 'REGULAR',
ADD COLUMN IF NOT EXISTS monthly_report_limit_override INT,
ADD COLUMN IF NOT EXISTS sponsor_account_id UUID;

ALTER TABLE accounts
ADD CONSTRAINT accounts_sponsor_fk
  FOREIGN KEY (sponsor_account_id)
  REFERENCES accounts(id)
  ON DELETE SET NULL;

ALTER TABLE accounts
ADD CONSTRAINT accounts_plan_fk
  FOREIGN KEY (plan_slug)
  REFERENCES plans(slug);
```

**New Fields:**
- `account_type`: 'REGULAR' | 'INDUSTRY_AFFILIATE'
- `monthly_report_limit_override`: Per-account override of plan limit (nullable)
- `sponsor_account_id`: For sponsored accounts (links to affiliate account)

---

## Backfill Strategy

### 1. Existing Accounts
All existing accounts become `REGULAR` with `plan_slug = 'free'`:

```sql
UPDATE accounts
SET account_type = 'REGULAR'
WHERE account_type IS NULL;

UPDATE accounts
SET plan_slug = 'free'
WHERE plan_slug IS NULL;
```

### 2. Existing Users → account_users
Seed `account_users` with OWNER role for existing users:

```sql
INSERT INTO account_users (account_id, user_id, role)
SELECT u.account_id, u.id, 'OWNER'
FROM users u
WHERE NOT EXISTS (
  SELECT 1 FROM account_users au
  WHERE au.account_id = u.account_id
    AND au.user_id = u.id
);
```

**Note:** `users.account_id` represents the user's primary/owner account. This column is kept for backward compatibility but `account_users` is now the source of truth for multi-account access.

---

## RLS Impact

### Current RLS Policies
- `report_generations`: `USING (account_id = current_setting('app.current_account_id')::uuid)`
- `usage_tracking`: Same pattern
- `api_keys`: Same pattern

### Phase 29A RLS Updates
No changes to existing policies yet. Phase 29C will add:
- Affiliate users can see their own account + sponsored accounts
- ADMIN users can see all accounts
- Regular users see only accounts where they have OWNER or MEMBER role in `account_users`

For now, existing behavior is preserved.

---

## Migration Idempotency

All Phase 29A migrations use:
- `IF NOT EXISTS` for table creation
- `ADD COLUMN IF NOT EXISTS` for column additions
- `ON CONFLICT DO NOTHING` for seed inserts
- Check for existing constraints before adding

**Safe to run multiple times in dev/staging/prod.**

---

## Next Phases

**Phase 29B:** Usage calculation & limit enforcement (API + worker)  
**Phase 29C:** Industry affiliate dashboard & sponsored user invites  
**Phase 29D:** Stripe integration for overages & plan upgrades  
**Phase 29E:** UI for plan selection & usage visualization

---

**Status:** ✅ **Documentation Complete - Ready for Migration Implementation**


# Seed Demo Accounts in Production

This script seeds **5 demo users + accounts** into the **production** database at https://www.trendyreports.io

---

## Demo Accounts

| Role | Email | Password | Notes |
|------|-------|----------|-------|
| **ADMIN** | `admin@trendyreports-demo.com` | `DemoAdmin123!` | Full admin capabilities |
| **FREE AGENT** | `agent-free@trendyreports-demo.com` | `DemoAgent123!` | REGULAR, plan `free` |
| **PRO AGENT** | `agent-pro@trendyreports-demo.com` | `DemoAgent123!` | REGULAR, plan `pro` |
| **AFFILIATE** | `affiliate@trendyreports-demo.com` | `DemoAff123!` | INDUSTRY_AFFILIATE, plan `affiliate` |
| **SPONSORED AGENT** | `agent-sponsored@trendyreports-demo.com` | `DemoAgent123!` | REGULAR, plan `sponsored_free`, sponsored by affiliate |

---

## Purpose

These accounts are **canonical demo accounts** for:
- **Live product demos** with potential buyers
- **Investor conversations** showing each user role
- **QA testing** on production
- **Support** for troubleshooting user-reported issues in specific roles

All accounts are **safe to reset** by re-running the seed script.

---

## How to Run (One-Time Setup)

### Step 1: Get Production DATABASE_URL

1. Go to: https://dashboard.render.com/d/dpg-d474qiqli9vc738g17e0-a (or your prod DB)
2. Click **"Connect"** → **"External Connection"**
3. Copy the full connection string:
   ```
   postgresql://prod_user:PASSWORD@prod-host.oregon-postgres.render.com/prod_db
   ```

### Step 2: Connect via psql

```bash
psql "postgresql://prod_user:PASSWORD@prod-host.oregon-postgres.render.com/prod_db"
```

Or use Render's **Web Shell** (click "PSQL Command" in dashboard).

### Step 3: Run the Seed Script

```sql
\i db/seed_demo_accounts_prod.sql
```

You should see output like:

```
NOTICE:  Created admin account: <uuid>
NOTICE:  Admin user linked to account
NOTICE:  Created free agent account: <uuid>
...
✅ Demo accounts created/updated successfully
```

### Step 4: Verify in Database

```sql
SELECT email, role, account_id
FROM users
WHERE email IN (
  'admin@trendyreports-demo.com',
  'agent-free@trendyreports-demo.com',
  'agent-pro@trendyreports-demo.com',
  'affiliate@trendyreports-demo.com',
  'agent-sponsored@trendyreports-demo.com'
);
```

All 5 users should appear with non-null `account_id`.

---

## Step 5: Verify in Browser

Visit https://www.trendyreports.io/login and test each account:

### 1. **Admin** (`admin@trendyreports-demo.com` / `DemoAdmin123!`)
- **Expected:**
  - Can see admin features (if implemented)
  - `/v1/me` returns `"role": "ADMIN"`
  - Access to admin routes

### 2. **Free Agent** (`agent-free@trendyreports-demo.com` / `DemoAgent123!`)
- **Expected:**
  - Slate "Agent Account" badge in header
  - `/account/plan` shows "Free Plan"
  - Usage limit: 50 reports/month
  - "Upgrade to Pro" Stripe button visible

### 3. **Pro Agent** (`agent-pro@trendyreports-demo.com` / `DemoAgent123!`)
- **Expected:**
  - Slate "Agent Account" badge
  - `/account/plan` shows "Professional Plan"
  - Usage limit: 300 reports/month
  - "Manage Billing" Stripe portal button visible

### 4. **Affiliate** (`affiliate@trendyreports-demo.com` / `DemoAff123!`)
- **Expected:**
  - **Purple "Affiliate Account" badge** in header
  - Dashboard at `/app`: **Affiliate overview** (NOT agent usage dashboard)
  - Sidebar: Includes **"Affiliate Dashboard"** and **"Affiliate Branding"** links
  - `/app/affiliate`: Shows sponsored accounts table + "Invite Agent" button
  - `/app/affiliate/branding`: White-label branding management

### 5. **Sponsored Agent** (`agent-sponsored@trendyreports-demo.com` / `DemoAgent123!`)
- **Expected:**
  - Slate "Agent Account" badge (NOT purple)
  - Dashboard at `/app`: **Usage dashboard** (NOT affiliate overview)
  - Sidebar: **NO** affiliate links
  - Reports: **Co-branded** with Demo Title Company (affiliate's branding)
  - No Stripe buttons (plan is sponsored)

---

## What This Script Does

1. **Creates/Updates 5 Users**
   - Uses `pgcrypto` to hash passwords with `crypt()`
   - `ON CONFLICT (email) DO UPDATE` makes it idempotent
   - Sets `is_active = TRUE` and appropriate `role`

2. **Creates/Links 5 Accounts**
   - Uses `DO $$ ... END $$` blocks for each account
   - Checks if account already exists before creating
   - Links via `account_users` table with `OWNER` role
   - Sets `users.account_id` as default account

3. **Special Relationships**
   - **Sponsored Agent** has `sponsor_account_id` pointing to **Affiliate** account
   - This enables white-label branding on the sponsored agent's reports

4. **Verification Query**
   - Shows all 5 accounts with their roles and plan types
   - Confirms everything was created correctly

---

## Idempotent & Safe

This script can be run **multiple times** without:
- Creating duplicate users or accounts
- Breaking existing relationships
- Changing unrelated data

If you need to **reset passwords** or **fix account settings**, just re-run it.

---

## After Seeding - Demo Story

You now have **one clean account per role on production**. Use them to show:

### For Investors/Buyers:

**"Let me show you our multi-tenant architecture..."**

1. **Admin** - Platform oversight
2. **Free Agent** - Self-service freemium entry
3. **Pro Agent** - Paid subscriber, Stripe integration
4. **Affiliate** - B2B2C white-label partner (title companies, lenders)
5. **Sponsored Agent** - End-user receiving co-branded reports from affiliate

### For Troubleshooting:

- Login as the affected role
- Reproduce the exact UX/state they're seeing
- Test fixes in context

---

## Security Notes

- ⚠️ **These are DEMO accounts with public passwords**
- Do NOT use for real customer data
- If compromised, re-run the script to reset passwords
- Consider rotating passwords quarterly or before major demos

---

## Related Documentation

- `db/seed_demo_accounts_v2.sql` - Staging version (same structure)
- `docs/DEMO_ACCOUNTS.md` - Overview of all demo accounts
- `docs/AUTH_ARCHITECTURE_V1.md` - Authentication system design
- `docs/AFFILIATE_UX_FIX.md` - How affiliate/sponsored UX differs

---

## Troubleshooting

### Error: "Admin user not found after insert"
- Check if `users` table exists
- Verify `email` column has unique constraint
- Check if pgcrypto extension is available

### Error: "Affiliate default account not found"
- The blocks run in order, so affiliate account is created before sponsored agent
- If this fails, check if affiliate block completed successfully

### Accounts created but can't login
- Verify `is_active = TRUE` in `users` table
- Check password hash was generated correctly
- Verify JWT_SECRET is set on API service

### Dashboard looks wrong for affiliate
- Check `/api/proxy/v1/me` response includes `"account_type": "INDUSTRY_AFFILIATE"`
- Verify login logic prioritizes INDUSTRY_AFFILIATE accounts (in `apps/api/src/api/routes/auth.py`)
- Clear browser cookies and re-login

---

## Need Help?

If the script fails or accounts don't behave as expected:

1. Check the verification query output
2. Review Render API logs for auth errors
3. Test `/v1/me` endpoint for each account
4. Verify `account_type` and `plan_slug` in database

The script includes `RAISE NOTICE` statements that show exactly what it's doing - check psql output for details.


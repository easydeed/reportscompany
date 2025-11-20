# Production Demo Accounts Checklist

**Date:** November 20, 2025  
**Database:** `mr-staging-db` (production database for www.trendyreports.io)

---

## Required Demo Accounts

These 5 demo accounts **MUST** exist in the production database:

| Email | Password | Role | Account Type | Plan | Purpose |
|-------|----------|------|--------------|------|---------|
| `admin@trendyreports-demo.com` | `DemoAdmin123!` | ADMIN | REGULAR | pro | Platform admin access |
| `agent-free@trendyreports-demo.com` | `DemoAgent123!` | MEMBER | REGULAR | free | Freemium agent (50 reports/month) |
| `agent-pro@trendyreports-demo.com` | `DemoAgent123!` | MEMBER | REGULAR | pro | Paid agent (300 reports/month) |
| `affiliate@trendyreports-demo.com` | `DemoAff123!` | MEMBER | INDUSTRY_AFFILIATE | affiliate | Title company/lender partner |
| `agent-sponsored@trendyreports-demo.com` | `DemoAgent123!` | MEMBER | REGULAR | sponsored_free | Agent sponsored by affiliate |

---

## How to Seed or Repair

### Prerequisites
- Access to production database
- Python 3 with `psycopg` installed
- Project repo cloned locally

### Option 1: Run Python Script (Recommended)

```bash
# From project root
python scripts/seed_production_demo_accounts.py
```

This script will:
1. Read `db/seed_demo_accounts_prod_v2.sql`
2. Connect to the production database
3. Execute the idempotent seed script
4. Display verification results

### Option 2: Manual psql

1. Get DATABASE_URL from Render dashboard:
   - Go to: https://dashboard.render.com/d/dpg-d474qiqli9vc738g17e0-a
   - Click "Connect" → "External Connection"

2. Connect:
   ```bash
   psql "postgresql://mr_staging_db_user:PASSWORD@dpg-d474qiqli9vc738g17e0-a.oregon-postgres.render.com/mr_staging_db"
   ```

3. Run seed script:
   ```sql
   \i db/seed_demo_accounts_prod_v2.sql
   ```

---

## Verification

### Check All 5 Accounts Exist

```bash
psql "$DATABASE_URL" -f db/check_production_demo_accounts.sql
```

Expected output:

```
email                             | user_role | account_name           | account_type        | plan_slug       | sponsor_id
----------------------------------+-----------+------------------------+---------------------+-----------------+------------
admin@trendyreports-demo.com      | ADMIN     | TrendyReports Admin    | REGULAR             | pro             | 
agent-free@trendyreports-demo.com | MEMBER    | Demo Free Agent        | REGULAR             | free            | 
agent-pro@trendyreports-demo.com  | MEMBER    | Demo Pro Agent         | REGULAR             | pro             | 
affiliate@trendyreports-demo.com  | MEMBER    | Demo Title Company     | INDUSTRY_AFFILIATE  | affiliate       | 
agent-sponsored@...               | MEMBER    | Demo Sponsored Agent   | REGULAR             | sponsored_free  | <affiliate_id>
```

### Verify `/v1/me` Response

For each account, test that `/v1/me` returns correct `account_type`:

```bash
# Login as affiliate and check /v1/me
curl -X POST https://reportscompany.onrender.com/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"affiliate@trendyreports-demo.com","password":"DemoAff123!"}' \
  -c cookies.txt

curl https://reportscompany.onrender.com/v1/me \
  -b cookies.txt

# Should return:
# {
#   "account_id": "...",
#   "user_id": "...",
#   "email": "affiliate@trendyreports-demo.com",
#   "role": "MEMBER",
#   "account_type": "INDUSTRY_AFFILIATE"
# }
```

---

## Expected Behavior by Account

### 1. Admin (`admin@trendyreports-demo.com`)
- **Header Badge:** None (or "Admin Account")
- **Sidebar:** Includes "Admin" link (if admin features implemented)
- **Dashboard:** Full platform access
- **/v1/me:** `role="ADMIN"`, `account_type="REGULAR"`

### 2. Free Agent (`agent-free@trendyreports-demo.com`)
- **Header Badge:** "Agent Account" (slate/gray)
- **Sidebar:** Standard agent navigation (Reports, Schedules, Branding, Billing)
- **Dashboard (`/app`):** Agent usage dashboard with usage meter
- **/account/plan:** Shows "Free Plan", limit of 50 reports/month, "Upgrade to Pro" button
- **/v1/me:** `role="MEMBER"`, `account_type="REGULAR"`

### 3. Pro Agent (`agent-pro@trendyreports-demo.com`)
- **Header Badge:** "Agent Account" (slate/gray)
- **Sidebar:** Standard agent navigation
- **Dashboard (`/app`):** Agent usage dashboard
- **/account/plan:** Shows "Professional Plan", limit of 300 reports/month, "Manage Billing" portal button
- **/v1/me:** `role="MEMBER"`, `account_type="REGULAR"`

### 4. Affiliate (`affiliate@trendyreports-demo.com`)
- **Header Badge:** "Affiliate Account" (purple/violet)
- **Sidebar:** Includes **"Affiliate Dashboard"** and **"Affiliate Branding"**
- **Dashboard (`/app`):** **Affiliate overview** (NOT agent dashboard)
  - Card with links to Affiliate Dashboard and Branding
  - No usage meter
- **/app/affiliate:** Shows table of sponsored agents, "Invite Agent" button, usage metrics
- **/app/affiliate/branding:** White-label branding management (logo, colors, tagline)
- **/v1/me:** `role="MEMBER"`, `account_type="INDUSTRY_AFFILIATE"`

### 5. Sponsored Agent (`agent-sponsored@trendyreports-demo.com`)
- **Header Badge:** "Agent Account" (slate/gray - NOT purple)
- **Sidebar:** Standard agent navigation (NO affiliate links)
- **Dashboard (`/app`):** Agent usage dashboard
- **/account/plan:** Shows "Sponsored Free Plan", co-branded by "Demo Title Company"
- **Reports:** **Co-branded** with affiliate's branding (logo, colors, tagline)
- **/v1/me:** `role="MEMBER"`, `account_type="REGULAR"`, `sponsor_account_id` set

---

## Troubleshooting

### Error: "Admin user not found after insert"
- Check if `users` table exists
- Verify `email` column has unique constraint
- Check if `pgcrypto` extension is available: `CREATE EXTENSION IF NOT EXISTS pgcrypto;`

### Error: "Affiliate default account not found"
- The blocks run in order, so affiliate account is created before sponsored agent
- If this fails, check if affiliate block completed successfully

### Accounts created but can't login
- Verify `is_active = TRUE` in `users` table:
  ```sql
  SELECT email, is_active FROM users WHERE email LIKE '%trendyreports-demo.com';
  ```
- Check password hash was generated correctly
- Verify `JWT_SECRET` is set on API service

### Dashboard looks wrong for affiliate
- Check `/api/proxy/v1/me` response includes `"account_type": "INDUSTRY_AFFILIATE"`
- Verify login logic prioritizes `INDUSTRY_AFFILIATE` accounts (in `apps/api/src/api/routes/auth.py`)
- Clear browser cookies and re-login
- Check frontend console for errors

### "Agent Account" badge showing for affiliate
- This means `/v1/me` is returning `account_type="REGULAR"` instead of `"INDUSTRY_AFFILIATE"`
- Run verification query to check database:
  ```sql
  SELECT u.email, a.account_type 
  FROM users u 
  JOIN accounts a ON a.id = u.account_id 
  WHERE u.email = 'affiliate@trendyreports-demo.com';
  ```
- If `account_type` is wrong, re-run the seed script

---

## Security Notes

⚠️ **Important:**
- These are **DEMO accounts with publicly known passwords**
- Do NOT use for real customer data
- Do NOT share real customer information with these accounts
- Consider rotating passwords quarterly or before major demos
- If compromised, simply re-run the seed script to reset passwords

---

## Related Documentation

- `docs/PROD_DB_REFERENCE.md` - Production database connection details
- `db/seed_demo_accounts_prod_v2.sql` - The actual seed script
- `db/check_production_demo_accounts.sql` - Quick verification query
- `scripts/seed_production_demo_accounts.py` - Automated seeding script
- `docs/AUTH_ARCHITECTURE_V1.md` - Authentication system design
- `docs/AFFILIATE_UX_FIX.md` - How affiliate/sponsored UX differs

---

## Last Updated

This checklist was last updated: **November 20, 2025**  
Last seeding verified: **Pending user execution**


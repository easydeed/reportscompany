# Demo Accounts - Seeding Guide (Staging Only)

**Purpose**: Create 5 canonical demo accounts for staging demos, QA, investor walkthroughs, and E2E testing.

**⚠️ WARNING**: This script is for **staging/demo databases ONLY**. Do NOT run on production.

---

## Quick Start

### 1. Connect to Staging Database

```bash
# Using Render staging database URL
psql postgresql://mr_staging_db_user:<PASSWORD>@dpg-d474qiqli9vc738g17e0-a.oregon-postgres.render.com/mr_staging_db
```

### 2. Run Seed Script

```bash
psql $DATABASE_URL -f db/seed_demo_accounts.sql
```

### 3. Verify Accounts Created

The script will output a verification table showing all demo accounts.

---

## Demo Accounts Created

| Role | Email | Password | Account Name | Account Type | Plan |
|------|-------|----------|--------------|--------------|------|
| **ADMIN** | admin@trendyreports-demo.com | `DemoAdmin123!` | Admin Organization | REGULAR (user role: ADMIN) | free |
| **FREE AGENT** | agent-free@trendyreports-demo.com | `DemoAgent123!` | Demo Free Agent | REGULAR | free |
| **PRO AGENT** | agent-pro@trendyreports-demo.com | `DemoAgent123!` | Demo Pro Agent | REGULAR | pro |
| **AFFILIATE** | affiliate@trendyreports-demo.com | `DemoAff123!` | Demo Title Company | INDUSTRY_AFFILIATE | affiliate |
| **SPONSORED** | agent-sponsored@trendyreports-demo.com | `DemoAgent123!` | Demo Sponsored Agent | REGULAR (sponsored) | sponsored_free |

---

## What This Script Does

### 1. Creates Users
- Hashes passwords using bcrypt (via pgcrypto extension)
- Sets appropriate user roles (ADMIN vs MEMBER)
- Uses `ON CONFLICT` for idempotency (safe to re-run)

### 2. Creates Accounts
- Sets correct `account_type` (REGULAR, INDUSTRY_AFFILIATE)
- Assigns proper `plan_slug` (free, pro, affiliate, sponsored_free)
- Links sponsored account to affiliate via `sponsor_account_id`

### 3. Links Users to Accounts
- Creates `account_users` entries with role='OWNER'
- Each user owns their primary account

### 4. Adds Affiliate Branding
- Seeds basic branding for "Demo Title Company"
- Brand name, tagline, and primary color
- Shows how white-label branding appears to sponsored agents

---

## Use Cases

### 📊 Investor Demos
Show different user experiences:
1. **Admin view**: Metrics, all accounts, system health
2. **Free agent**: Limited usage, upgrade prompts
3. **Pro agent**: Full features, Stripe integration
4. **Affiliate**: Sponsor dashboard, branding management
5. **Sponsored agent**: White-label experience

### 🧪 QA & Testing
- Manual QA: Log in as each role to test flows
- E2E tests: Map GitHub secrets to these accounts
- Integration tests: Predictable, known accounts

### 🎬 Sales Demos
Clean, professional logins with clear role separation. No "gerardoh@gmail.com" or test123 nonsense.

---

## Rotating Passwords

To change demo passwords:

1. Edit `db/seed_demo_accounts.sql`
2. Update the `crypt('NewPassword123!', gen_salt('bf'))` values
3. Re-run the script: `psql $DATABASE_URL -f db/seed_demo_accounts.sql`

The script is idempotent - it will update existing accounts rather than fail.

---

## Verification

After running, check accounts were created:

```sql
SELECT 
  u.email,
  u.role AS user_role,
  a.name AS account_name,
  a.account_type,
  a.plan_slug,
  a.sponsor_account_id IS NOT NULL AS is_sponsored
FROM users u
JOIN account_users au ON u.id = au.user_id
JOIN accounts a ON au.account_id = a.id
WHERE u.email LIKE '%@trendyreports-demo.com'
ORDER BY u.email;
```

Expected output: 5 rows (one per demo account).

---

## Security Notes

### ✅ Safe Practices
- All emails use `@trendyreports-demo.com` domain (easy to identify)
- Passwords are strong enough for staging but not production-grade
- Script is marked "STAGING ONLY" in multiple places
- Idempotent design (safe to re-run without breaking data)

### ⚠️ Do NOT
- Run this on production database
- Commit real production credentials to Git
- Use these passwords for production accounts
- Share these credentials outside the team/investors

---

## Troubleshooting

### "pgcrypto extension not found"
```sql
CREATE EXTENSION IF NOT EXISTS pgcrypto;
```

### "relation does not exist"
Ensure your staging database has the correct schema migrated. Run migrations first:
```bash
alembic upgrade head
```

### Accounts not appearing
Check RLS (Row-Level Security) isn't blocking the verification query. The seed script sets data directly, so it should bypass RLS.

---

## Related Documentation

- **User-Facing Credentials**: `docs/DEMO_ACCOUNTS.md`
- **E2E Testing Setup**: `docs/RELEASE_CHECK.md`
- **Auth Architecture**: `docs/AUTH_ARCHITECTURE_V1.md`

---

**Last Updated**: November 15, 2025  
**Maintained By**: Development Team


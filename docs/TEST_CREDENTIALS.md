# Test Credentials - Staging Environment

**Purpose**: Canonical demo/test accounts for staging QA, E2E tests, and investor demos.

**⚠️ STAGING ONLY**: These credentials are for non-production environments. Never use in production.

---

## Demo Accounts (Staging)

For complete details and seeding instructions, see: **`docs/DEMO_ACCOUNTS.md`** and **`docs/SEED_DEMO_ACCOUNTS.md`**.

### Quick Reference

| Role | Email | Password | Use Case |
|------|-------|----------|----------|
| **ADMIN** | admin@trendyreports-demo.com | `DemoAdmin123!` | Admin metrics, system config |
| **FREE AGENT** | agent-free@trendyreports-demo.com | `DemoAgent123!` | Free plan, limited usage |
| **PRO AGENT** | agent-pro@trendyreports-demo.com | `DemoAgent123!` | Pro plan, Stripe flows |
| **AFFILIATE** | affiliate@trendyreports-demo.com | `DemoAff123!` | Sponsor dashboard, branding |
| **SPONSORED** | agent-sponsored@trendyreports-demo.com | `DemoAgent123!` | White-label experience |

---

## Environment Secrets

**All secrets are stored in environment variables, NOT in this repository.**

### Render (API)
Secrets configured in Render dashboard:
- `JWT_SECRET` - JWT signing key
- `STRIPE_SECRET_KEY` - Stripe API key (sk_test_...)
- `STRIPE_WEBHOOK_SECRET` - Stripe webhook signing secret (whsec_...)
- `STRIPE_PRICE_PRO_MONTH` - Stripe Price ID for Pro plan
- `STRIPE_PRICE_TEAM_MONTH` - Stripe Price ID for Team plan
- `DATABASE_URL` - PostgreSQL connection string
- `ALLOWED_ORIGINS` - CORS configuration

### Vercel (Web)
Secrets configured in Vercel dashboard:
- `NEXT_PUBLIC_API_BASE` - Backend API URL

### GitHub Actions (E2E Tests)
Secrets configured in repository settings:
- `E2E_BASE_URL` - Staging web URL
- `E2E_REGULAR_EMAIL` - Regular agent test account
- `E2E_REGULAR_PASSWORD` - Regular agent password
- `E2E_AFFILIATE_EMAIL` - Affiliate test account
- `E2E_AFFILIATE_PASSWORD` - Affiliate password

---

## Accessing Secrets

### For Local Development
1. Copy `.env.example` to `.env.local`
2. Request secrets from team lead or check team password manager
3. Never commit `.env.local` to Git

### For Staging/Production
1. **Render**: https://dashboard.render.com → reportscompany-api → Environment
2. **Vercel**: https://vercel.com/dashboard → reportscompany-web → Settings → Environment Variables
3. **GitHub**: Repository → Settings → Secrets and variables → Actions

---

## Legacy Accounts

These accounts may still exist in staging but are being phased out:

- `gerardoh@gmail.com` / `Test123456!` - Original test account

Use canonical demo accounts above for all new testing and demos.

---

## Rotating Credentials

### Demo Account Passwords
1. Edit `db/seed_demo_accounts.sql`
2. Update password values
3. Re-run seed script: `psql $DATABASE_URL -f db/seed_demo_accounts.sql`

### Environment Secrets
1. Update in respective dashboard (Render/Vercel/GitHub)
2. Trigger redeployment if needed
3. Update team documentation

---

## Security Reminders

✅ **DO**:
- Use demo accounts for staging/QA
- Store secrets in environment variables
- Rotate passwords periodically
- Use different credentials for production

❌ **DON'T**:
- Commit secrets to Git
- Share credentials publicly
- Use staging credentials in production
- Log secrets in application code

---

**Last Updated**: November 15, 2025  
**See Also**: `docs/DEMO_ACCOUNTS.md`, `docs/SEED_DEMO_ACCOUNTS.md`, `docs/AUTH_ARCHITECTURE_V1.md`

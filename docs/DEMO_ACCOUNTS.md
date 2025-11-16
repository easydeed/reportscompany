# Demo Accounts (Staging Only)

**Purpose**: Canonical demo logins for staging demos, QA, and investor walkthroughs.

**Environment**: Staging database only (`mr_staging_db` on Render)

**URL**: https://reportscompany-web.vercel.app

---

## 🎭 The 5 Roles

### 1️⃣ ADMIN - Internal Superuser
**Email**: `admin@trendyreports-demo.com`  
**Password**: `DemoAdmin123!`

**What You'll See**:
- Admin metrics dashboard (if implemented)
- System-wide configuration
- All accounts visibility
- Full access to all features

**Use For**: Investor demos showing platform health, metrics, and administrative capabilities.

---

### 2️⃣ REGULAR_FREE_AGENT - Solo Agent on Free Plan
**Email**: `agent-free@trendyreports-demo.com`  
**Password**: `DemoAgent123!`

**What You'll See**:
- Free plan: 50 reports/month
- Usage meter showing limits
- "Upgrade to Pro" prompts
- Limited feature access

**Use For**: Showing freemium model, upgrade paths, and how we convert free users to paid.

---

### 3️⃣ REGULAR_PRO_AGENT - Paying Agent on Pro Plan
**Email**: `agent-pro@trendyreports-demo.com`  
**Password**: `DemoAgent123!`

**What You'll See**:
- Pro plan: 100 reports/month
- Stripe integration (checkout, customer portal)
- Full feature access
- Higher usage limits

**Use For**: Demonstrating paid tier value, Stripe billing flows, and premium features.

---

### 4️⃣ INDUSTRY_AFFILIATE - Title/Lender Affiliate
**Email**: `affiliate@trendyreports-demo.com`  
**Password**: `DemoAff123!`

**What You'll See**:
- Affiliate dashboard
- Sponsored accounts list
- Invite agent flow
- White-label branding management
- Custom logo/colors/tagline

**Use For**: Showing B2B2C model, how affiliates sponsor agents, and white-label branding.

---

### 5️⃣ SPONSORED_AGENT - Agent Sponsored by Affiliate
**Email**: `agent-sponsored@trendyreports-demo.com`  
**Password**: `DemoAgent123!`

**What You'll See**:
- Free access (sponsored by "Demo Title Company")
- Affiliate's branding on reports and emails
- No "Upgrade" prompts (can't self-upgrade)
- Full feature access as sponsored user

**Use For**: Demonstrating end-to-end white-label experience from agent perspective.

---

## 📖 Demo Story Flow

**Perfect 5-Minute Walkthrough for Investors**:

1. **Start as ADMIN** (30 sec)
   - "Here's our platform health: X accounts, Y reports this month"
   - Show metrics, clean dashboard

2. **Switch to REGULAR_FREE_AGENT** (1 min)
   - "This is a freemium user: limited to 50 reports/month"
   - Show usage meter, "Upgrade to Pro" button
   - Click through to Stripe checkout (don't complete)

3. **Switch to REGULAR_PRO_AGENT** (1 min)
   - "This is a paying customer: $29/month, 100 reports"
   - Show Stripe Customer Portal integration
   - Demonstrate generating a report

4. **Switch to INDUSTRY_AFFILIATE** (1.5 min)
   - "This is our B2B2C play: title companies sponsor agents"
   - Show sponsored accounts list
   - Demo invite flow + branding management
   - "They white-label our platform as their own"

5. **Switch to SPONSORED_AGENT** (1 min)
   - "This agent sees 'Demo Title Company' everywhere"
   - Show branded report with affiliate logo/colors
   - "They get free access, affiliate gets stickiness, we get volume"

**Result**: Investor sees complete product, business model, and monetization in under 5 minutes.

---

## 🔄 How to Seed These Accounts

If accounts don't exist or need reset:

```bash
# Connect to staging database
psql postgresql://mr_staging_db_user:<PASSWORD>@dpg-d474qiqli9vc738g17e0-a.oregon-postgres.render.com/mr_staging_db

# Run seed script
\i db/seed_demo_accounts.sql
```

See `docs/SEED_DEMO_ACCOUNTS.md` for full details.

---

## 🔐 Security Notes

### ✅ Safe to Use
- Staging environment only
- Demo domain (`@trendyreports-demo.com`)
- Passwords designed for demo use
- Can be rotated anytime

### ⚠️ Never Use For
- Production database
- Real customer data
- Public sharing outside team/investors
- Production Stripe keys

---

## 🧪 Testing Integration

These accounts are used for:
- **Manual QA**: Test each role's experience
- **E2E Tests**: Mapped via GitHub secrets
- **Investor Demos**: Clean, professional logins
- **Sales Presentations**: Role-based walkthroughs

See `docs/RELEASE_CHECK.md` for E2E test configuration.

---

## 🆘 Troubleshooting

### "Invalid credentials"
- Accounts may not be seeded yet → Run `db/seed_demo_accounts.sql`
- Wrong environment → Ensure you're on staging URL

### "Account not found"
- Database may have been reset → Re-run seed script
- Check email spelling (all lowercase, `@trendyreports-demo.com`)

### "Features not working as expected"
- Check account's `plan_slug` in database
- Verify affiliate branding was seeded
- Ensure sponsor relationship is correct (for sponsored agent)

---

**Last Updated**: November 15, 2025  
**Maintained By**: Development Team  
**See Also**: `docs/SEED_DEMO_ACCOUNTS.md`, `docs/TEST_CREDENTIALS.md`


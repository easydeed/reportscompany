# Quick Seed - Demo Accounts (30 seconds)

## Method 1: Python Script (Easiest)

```bash
# 1. Get DATABASE_URL from Render:
#    Dashboard → mr-staging-db → Connect → "Internal Database URL"

# 2. Run seed script:
DATABASE_URL="postgresql://mr_staging_db_user:<PASSWORD>@dpg-d474qiqli9vc738g17e0-a.oregon-postgres.render.com/mr_staging_db" python scripts/seed_demo_accounts.py
```

## Method 2: Direct psql (Alternative)

```bash
# 1. Get connection string from Render

# 2. Connect and run:
psql "postgresql://mr_staging_db_user:<PASSWORD>@dpg-d474qiqli9vc738g17e0-a.oregon-postgres.render.com/mr_staging_db" -f db/seed_demo_accounts.sql
```

## Method 3: Copy-Paste SQL (Quick)

1. Go to Render Dashboard → mr-staging-db → Query tab
2. Copy contents of `db/seed_demo_accounts.sql`
3. Paste and execute

---

## ✅ Verify It Worked

After seeding, check:
```bash
# Should show 5 accounts
psql $DATABASE_URL -c "SELECT email FROM users WHERE email LIKE '%@trendyreports-demo.com';"
```

Expected output:
```
admin@trendyreports-demo.com
agent-free@trendyreports-demo.com
agent-pro@trendyreports-demo.com
affiliate@trendyreports-demo.com
agent-sponsored@trendyreports-demo.com
```

---

## 🎬 Then Test Login

1. Go to: https://reportscompany-web.vercel.app/login
2. Try: `admin@trendyreports-demo.com` / `DemoAdmin123!`
3. Should redirect to `/app` dashboard

See `docs/DEMO_ACCOUNTS.md` for the full 5-minute investor demo walkthrough.


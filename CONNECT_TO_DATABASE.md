# Connect to Database via Terminal - Step by Step

## Step 1: Get Connection String from Render

1. Go to: https://dashboard.render.com/d/dpg-d474qiqli9vc738g17e0-a
2. Click the **"Connect"** button (top right)
3. Under **"External Connection"**, you'll see a connection string that looks like:
   ```
   postgresql://mr_staging_db_user:PASSWORD@dpg-d474qiqli9vc738g17e0-a.oregon-postgres.render.com/mr_staging_db
   ```
4. **Copy this entire string** (it includes your password)

---

## Step 2: Connect via Terminal

Open PowerShell and run:

```powershell
# If you have psql installed:
psql "YOUR_CONNECTION_STRING_HERE"

# OR use Render's Web Shell (easier):
# Just click "Connect" → "PSQL Command" in Render dashboard
```

**Example:**
```powershell
psql "postgresql://mr_staging_db_user:yourpassword@dpg-d474qiqli9vc738g17e0-a.oregon-postgres.render.com/mr_staging_db"
```

If you see `mr_staging_db=>` prompt, you're connected! ✅

---

## Step 3: Insert Test Schedule

Copy and paste this entire block:

```sql
INSERT INTO schedules (
  account_id,
  name,
  report_type,
  city,
  lookback_days,
  cadence,
  weekly_dow,
  send_hour,
  send_minute,
  recipients,
  active,
  created_at,
  next_run_at
) VALUES (
  '912014c3-6deb-4b40-a28d-489ef3923a3a',
  'Phase 27A Email Test - Gerard',
  'market_snapshot',
  'Houston',
  30,
  'weekly',
  1,
  14,
  0,
  ARRAY['gerardoh@gmail.com'],
  true,
  NOW(),
  NOW() - INTERVAL '1 minute'
)
RETURNING id, name, next_run_at;
```

Press **Enter**. You should see:
```
                  id                  |             name              |          next_run_at
--------------------------------------+-------------------------------+-------------------------------
 xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx | Phase 27A Email Test - Gerard | 2025-11-13 19:xx:xx.xxxxxx+00
```

**COPY THE ID** - you'll need it for monitoring!

---

## Step 4: Monitor Execution (5-10 minutes)

### A. Check Schedule Run Status

```sql
SELECT id, status, started_at, finished_at, report_run_id, created_at
FROM schedule_runs
WHERE schedule_id = 'PASTE_THE_ID_HERE'
ORDER BY created_at DESC
LIMIT 5;
```

**What to look for:**
- `status = 'queued'` → Ticker found it, worker hasn't started yet
- `status = 'processing'` → Worker is generating report
- `status = 'completed'` → Success! ✅

### B. Check Email Log

```sql
SELECT provider, to_emails, response_code, error, created_at
FROM email_log
ORDER BY created_at DESC
LIMIT 5;
```

**What to look for:**
- `provider = 'sendgrid'`
- `to_emails = {gerardoh@gmail.com}`
- `response_code = 202` ✅ (Success!)
- `error = NULL`

### C. Check Report Generation

```sql
SELECT id, status, pdf_url, created_at
FROM report_runs
ORDER BY created_at DESC
LIMIT 5;
```

**What to look for:**
- `status = 'completed'`
- `pdf_url` starts with `https://...r2.cloudflarestorage.com/...`

---

## Step 5: Check Your Email

Within 5-10 minutes, check **gerardoh@gmail.com** for:

✅ **From:** TrendyReports <reports@trendyreports.io>
✅ **Subject:** 📊 Your Market Snapshot Report for Houston is Ready!
✅ **Design:** Purple gradient header
✅ **Button:** "View Full Report (PDF)" → Opens Houston market report
✅ **Footer:** Unsubscribe link

---

## Troubleshooting

### "psql: command not found"

**Option A:** Use Render's Web Shell
1. Go to database dashboard
2. Click "Connect" → "Web Shell"
3. Run SQL directly in browser

**Option B:** Install psql
```powershell
# Using Chocolatey (if you have it):
choco install postgresql

# Or download from: https://www.postgresql.org/download/windows/
```

### "Connection refused" or "timeout"

- Check you copied the full connection string (including password)
- Make sure you're connected to internet
- Try Render's Web Shell instead

### Schedule not triggering

**Check ticker logs:**
1. Go to: https://dashboard.render.com/worker/srv-d4acvv1e2q1c73e52tsg
2. Click "Logs" tab
3. Look for: "Due schedule detected"

**If ticker isn't running:**
- Service might be suspended
- Check service is "Active" in dashboard

---

## Quick Summary

1. **Get connection string** from Render dashboard
2. **Connect:** `psql "postgresql://..."`
3. **Insert schedule:** Copy/paste SQL
4. **Wait 5-10 min** and monitor with queries
5. **Check email** at gerardoh@gmail.com

---

**Last Updated:** November 13, 2025
**Status:** Ready to test


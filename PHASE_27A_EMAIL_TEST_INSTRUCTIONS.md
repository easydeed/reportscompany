# Phase 27A Email Test to gerardoh@gmail.com

## Quick Start: Send Test Email

### Option 1: Direct Database Insert (Fastest - 5 minutes)

**Step 1: Connect to your Render PostgreSQL database**

You can use:
- Render Dashboard → Database → "Connect" button → Copy connection string
- pgAdmin (if you have it configured)
- Any PostgreSQL client

**Step 2: Run the SQL from `TEST_SCHEDULE_GERARDOH.sql`**

```sql
INSERT INTO schedules (
  account_id, name, report_type, city, lookback_days,
  cadence, weekly_dow, send_hour, send_minute, recipients, 
  active, created_at, updated_at, next_run_at
) VALUES (
  '912014c3-6deb-4b40-a28d-489ef3923a3a',
  'Phase 27A Email Test - Gerard',
  'market_snapshot',
  'Houston',
  30,
  'weekly',
  1, 14, 0,
  ARRAY['gerardoh@gmail.com'],
  true,
  NOW(),
  NOW(),
  NOW() - INTERVAL '1 minute'  -- Triggers immediately
)
RETURNING id, name, next_run_at;
```

**Step 3: Wait and monitor (5-10 minutes total)**

The system will automatically:
1. **Ticker** (runs every 60 seconds) picks up the schedule
2. **Worker** generates the report with Houston market data
3. **PDF** uploads to Cloudflare R2
4. **Email** sends via SendGrid to gerardoh@gmail.com
5. **Inbox** receives beautiful branded email with PDF link

---

### Option 2: Wait for Vercel Build + Use UI (Slower - 15-20 minutes)

**Step 1: Check Vercel deployment status**

Go to: https://vercel.com/easydeed/reportscompany (or your dashboard)

**Step 2: Once deployed, navigate to schedules**

URL: https://reportscompany.vercel.app/app/schedules

**Step 3: Click "New Schedule" and fill in:**
- Name: Phase 27A Email Test - Gerard
- Report Type: Market Snapshot
- City: Houston
- Lookback: 30 days
- Cadence: Weekly, Monday, 2:00 PM
- Recipients: gerardoh@gmail.com
- Active: Yes

**Step 4: Save and wait**

Same automatic execution as Option 1.

---

### Option 3: API Call (Requires Auth Token)

**Step 1: Get JWT token**

You'll need to authenticate first (login endpoint or existing session).

**Step 2: POST to schedules endpoint**

```bash
curl -X POST https://reportscompany.onrender.com/v1/schedules \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Phase 27A Email Test - Gerard",
    "report_type": "market_snapshot",
    "city": "Houston",
    "lookback_days": 30,
    "cadence": "weekly",
    "weekly_dow": 1,
    "send_hour": 14,
    "send_minute": 0,
    "recipients": ["gerardoh@gmail.com"],
    "active": true
  }'
```

---

## Monitoring the Test

### Check Render Logs (Real-time)

**1. Ticker Service Logs:**
- Service: `markets-report-ticker`
- Look for: 
  ```
  INFO: Due schedule detected: Phase 27A Email Test - Gerard
  INFO: Enqueuing report for schedule_id=...
  ```

**2. Worker Service Logs:**
- Service: `reportscompany - worker-service`
- Look for:
  ```
  INFO: Generating report...
  INFO: PDF uploaded to R2: https://...
  INFO: Sending schedule email to 1 recipient(s)
  INFO: Email sent successfully to ['gerardoh@gmail.com']
  ```

### Check Database Tables

**1. Schedule Runs (Execution Status):**
```sql
SELECT id, status, started_at, finished_at, report_run_id
FROM schedule_runs
WHERE schedule_id = (
  SELECT id FROM schedules 
  WHERE name = 'Phase 27A Email Test - Gerard'
)
ORDER BY created_at DESC;
```

Expected:
- `status = 'completed'`
- `finished_at` populated
- `report_run_id` links to report

**2. Email Log (Send Status):**
```sql
SELECT id, provider, to_emails, subject, response_code, error, created_at
FROM email_log
ORDER BY created_at DESC
LIMIT 5;
```

Expected:
- `provider = 'sendgrid'`
- `to_emails = {gerardoh@gmail.com}`
- `response_code = 202` (SendGrid success)
- `error = NULL`

**3. Report Runs (PDF Generation):**
```sql
SELECT id, report_type, status, pdf_url, created_at
FROM report_runs
ORDER BY created_at DESC
LIMIT 5;
```

Expected:
- `status = 'completed'`
- `pdf_url` contains valid R2 URL

---

## Expected Email Content

**Inbox (gerardoh@gmail.com) should receive:**

**From:** `TrendyReports <reports@trendyreports.io>`

**Subject:** `📊 Your Market Snapshot Report for Houston is Ready!`

**Email Design:**
- **Header:** Purple gradient banner with "📊 Your Market Snapshot Report"
- **Greeting:** "Hi, Your scheduled Market Snapshot report for Houston is ready!"
- **KPIs (3 columns):**
  - Active Listings: [count]
  - Pending: [count]
  - Closed: [count]
- **CTA Button:** Large purple "📄 View Full Report (PDF)" button
- **Link:** Opens PDF from R2 storage
- **Footer:** Unsubscribe link

**PDF Content:**
- Houston market data
- Tables, charts, metrics
- Professional TrendyReports branding

---

## Timeline Expectations

| Time | Event |
|------|-------|
| T+0 | Schedule created (via SQL/UI/API) |
| T+1 min | Ticker detects schedule (runs every 60s) |
| T+2 min | Worker starts report generation |
| T+3 min | MLS data fetched from SimplyRETS |
| T+4 min | PDF generated and uploaded to R2 |
| T+5 min | Email sent via SendGrid |
| T+6-10 min | Email arrives in Gmail inbox |

**Total Time:** ~5-10 minutes from schedule creation to inbox delivery

---

## Troubleshooting

### Email Not Sending?

**1. Check SendGrid API Key:**
```bash
# On Render worker service, verify env var is set
echo $SENDGRID_API_KEY  # Should start with SG.
```

**2. Check SendGrid Activity Feed:**
- Go to: https://app.sendgrid.com/email_activity
- Filter by recipient: gerardoh@gmail.com
- Check status: Delivered, Bounced, Blocked?

**3. Check Worker Logs:**
- Look for errors like:
  - `401 Unauthorized` → API key invalid
  - `403 Forbidden` → Sender not verified
  - `400 Bad Request` → Malformed email

### Email Not Arriving?

1. **Check spam folder** in Gmail
2. **Verify sender authentication** in SendGrid
3. **Check Gmail filters** (might be auto-filed)
4. **Try different email** to rule out Gmail-specific issues

### Report Generation Failing?

**Check SimplyRETS API:**
- Demo account has limited data
- Houston should work with demo credentials
- Check worker logs for SimplyRETS errors

**Check R2 Upload:**
- Verify R2 credentials in Render env vars
- Check worker logs for upload errors

---

## Success Criteria

✅ **Phase 27A test is successful when:**

1. Schedule created in database
2. Ticker picks it up within 60 seconds
3. Worker generates report without errors
4. PDF uploaded to R2 successfully
5. `email_log` shows `response_code = 202`
6. Email arrives at gerardoh@gmail.com
7. Email has correct branding and layout
8. PDF link opens and displays report
9. Unsubscribe link is present in footer

---

## After Successful Test

1. **Mark Phase 27A as ✅ Complete** in `PROJECT_STATUS-2.md`
2. **Test unsubscribe flow** (click link, verify suppression)
3. **Move to Phase 27B** (UI QA)
4. **Optional:** Delete test schedule if you want:
   ```sql
   DELETE FROM schedules 
   WHERE name = 'Phase 27A Email Test - Gerard';
   ```

---

**Recommended Approach:** Use **Option 1 (Direct SQL)** for fastest results. You'll see the email in 5-10 minutes!

**Last Updated:** November 13, 2025  
**Status:** Ready to test


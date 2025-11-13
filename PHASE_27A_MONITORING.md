# Phase 27A Monitoring Queries

**Schedule ID:** `[PASTE_YOUR_SCHEDULE_ID_HERE]`

---

## A. Check Schedule Run Status

```sql
SELECT id, status, started_at, finished_at, report_run_id, created_at
FROM schedule_runs
WHERE schedule_id = '[PASTE_YOUR_SCHEDULE_ID_HERE]'
ORDER BY created_at DESC
LIMIT 5;
```

**Expected progression:**
- `status = 'queued'` → Ticker found it
- `status = 'processing'` → Worker generating report
- `status = 'completed'` → Success! ✅

---

## B. Check Email Log

```sql
SELECT 
  provider, 
  to_emails, 
  response_code, 
  error, 
  subject,
  created_at
FROM email_log
ORDER BY created_at DESC
LIMIT 5;
```

**Success indicators:**
- ✅ `provider = 'sendgrid'`
- ✅ `to_emails = {gerardoh@gmail.com}`
- ✅ `response_code = 202` (SendGrid accepted)
- ✅ `error = NULL`

---

## C. Check Report Generation

```sql
SELECT 
  id, 
  status, 
  pdf_url,
  result_json->>'city' as city,
  created_at
FROM report_runs
ORDER BY created_at DESC
LIMIT 5;
```

**Success indicators:**
- ✅ `status = 'completed'`
- ✅ `pdf_url` is a valid R2 URL
- ✅ `city = 'Houston'`

---

## D. Check Ticker Logs (If Nothing Happens)

Go to Render service logs:
- **Ticker:** https://dashboard.render.com/worker/srv-d4acvv1e2q1c73e52tsg
- Look for: `"Due schedule detected: [schedule-id]"`

---

## E. Check Worker Logs

Go to Render service logs:
- **Worker:** https://dashboard.render.com (find worker service)
- Look for:
  - `"Generating report for schedule_id=[id]"`
  - `"Sending schedule email to ['gerardoh@gmail.com']"`
  - `"SendGrid response: 202"`

---

## Expected Timeline

| Time | Event |
|------|-------|
| T+0 | Schedule inserted with `next_run_at` in past |
| T+1min | Ticker picks up schedule, enqueues job |
| T+2min | Worker starts report generation |
| T+3-5min | PDF uploaded to R2, email sent via SendGrid |
| T+5-10min | Email arrives in Gmail |

---

## Troubleshooting

### Schedule not picked up
- Check ticker service is running (not suspended)
- Verify `next_run_at <= NOW()` and `active = true`

### Report generation fails
- Check worker logs for errors
- Verify SimplyRETS credentials are set
- Check R2 credentials for PDF upload

### Email not sent
- Check `email_log` for error message
- Verify SendGrid API key is set
- Check SendGrid dashboard for blocks/rejections

### Email not received
- Check spam folder
- Verify SendGrid domain authentication
- Check `email_log.response_code = 202` (accepted by SendGrid)

---

**Last Updated:** November 13, 2025


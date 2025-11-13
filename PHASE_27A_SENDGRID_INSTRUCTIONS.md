# Phase 27A: SendGrid Verification & Testing Instructions

## Status: ✅ Email System Already Implemented with SendGrid

The email sending system is **already fully implemented** using SendGrid. This document provides verification steps and testing instructions.

---

## 🎯 What's Already Done

### 1. SendGrid Provider Implementation

**File:** `apps/worker/src/worker/email/providers/sendgrid.py`

✅ **Implemented:**
- Uses SendGrid v3 API
- Reads `SENDGRID_API_KEY` from environment
- Uses `DEFAULT_FROM_NAME` and `DEFAULT_FROM_EMAIL` from environment
- Returns tuple of `(status_code, response_text)`
- Handles timeouts and errors gracefully
- Logs all send attempts

### 2. Email Orchestration

**File:** `apps/worker/src/worker/email/send.py`

✅ **Implemented:**
- `send_schedule_email()` function that:
  - Filters suppressions (needs DB integration)
  - Generates HMAC unsubscribe tokens
  - Builds email payload with metrics
  - Calls SendGrid provider
  - Returns status codes

### 3. HTML Email Template

**File:** `apps/worker/src/worker/email/template.py`

✅ **Implemented:**
- Beautiful gradient header (purple gradient)
- Personalized greeting
- 3-column metrics grid
- "View Full Report (PDF)" CTA button
- Unsubscribe link in footer
- Responsive table-based layout
- Report type-specific metrics display

### 4. Worker Task Integration

**File:** `apps/worker/src/worker/tasks.py` (Line 258-295)

✅ **Implemented:**
- After report generation, calls `send_schedule_email()`
- Builds email payload with metrics and PDF URL
- Logs to `email_log` table with `provider='sendgrid'`
- Updates `schedule_runs` status to `'completed'`
- Handles email failures without crashing task

---

## 📋 Verification Checklist (For Cursor)

### Task 1: Verify Environment Variables

Check that these are set in Render (both `apps/api` and `apps/worker` services):

```bash
# Required for SendGrid
SENDGRID_API_KEY=SG_xxx
DEFAULT_FROM_EMAIL=reports@yourdomain.com
DEFAULT_FROM_NAME="TrendyReports"

# Required for unsubscribe
UNSUBSCRIBE_SECRET=<long-random-string>
WEB_BASE=https://reportscompany.vercel.app
```

**Action:** If not set, add them to Render dashboard for both services.

### Task 2: Search for "Resend" References

Run these searches and confirm **NO** results in actual code (docs are OK):

```bash
# In worker code
grep -r "resend" apps/worker/src/ --ignore-case

# In API code  
grep -r "resend" apps/api/src/ --ignore-case
```

**Expected:** No matches (already verified - clean!)

### Task 3: Verify Email Suppression Logic

**Current state:** The `send_schedule_email()` function in `send.py` does **NOT** yet filter suppressions.

**Action needed:**

In `apps/worker/src/worker/email/send.py`, before sending email:

```python
def send_schedule_email(
    account_id: str,
    recipients: List[str],
    payload: Dict,
    account_name: Optional[str] = None,
    db_conn=None,  # Add optional DB connection
) -> Tuple[int, str]:
    """Send scheduled report with suppression filtering."""
    
    # NEW: Filter suppressions if DB connection provided
    if db_conn:
        from psycopg2.extras import execute_values
        with db_conn.cursor() as cur:
            cur.execute("""
                SELECT email FROM email_suppressions
                WHERE account_id = %s AND email = ANY(%s)
            """, (account_id, recipients))
            suppressed = [row[0] for row in cur.fetchall()]
            recipients = [r for r in recipients if r not in suppressed]
            
            if not recipients:
                logger.info("All recipients suppressed, skipping email")
                return (200, "All recipients suppressed")
    
    # ... rest of function as-is
```

Then in `tasks.py`, pass the DB connection:

```python
status_code, response_text = send_schedule_email(
    account_id=account_id,
    recipients=recipients,
    payload=email_payload,
    account_name=account_name,
    db_conn=conn,  # Pass connection
)
```

### Task 4: Update `.env.example` Files

Ensure these files document the SendGrid vars:

**`apps/worker/.env.example`:**
```bash
# Email Provider
SENDGRID_API_KEY=your_sendgrid_api_key_here
DEFAULT_FROM_EMAIL=reports@yourdomain.com
DEFAULT_FROM_NAME="TrendyReports"

# Unsubscribe
UNSUBSCRIBE_SECRET=your_long_random_secret_here
WEB_BASE=https://yourapp.vercel.app
```

**`apps/api/.env.example`:**
```bash
# Same as above (API needs these for unsubscribe endpoint)
```

---

## 🧪 End-to-End Testing Instructions

### Prerequisites

1. ✅ SendGrid API key added to Render environment
2. ✅ Sending domain verified in SendGrid
3. ✅ `SENDGRID_FROM_EMAIL` matches verified sender
4. ✅ Ticker service running on Render
5. ✅ Worker service running on Render

### Test Flow

#### Step 1: Create Test Schedule

1. Navigate to deployed web app: `https://reportscompany.vercel.app/app/schedules`
2. Click **"New Schedule"**
3. Fill in fields:
   - **Report Type:** Market Snapshot
   - **City:** Houston (or any SimplyRETS demo city)
   - **Cadence:** Weekly
   - **Day of Week:** Tomorrow
   - **Time:** 10:00 AM (or a few hours ahead)
   - **Recipients:** Your email address only
4. Click **Save**
5. Confirm schedule appears in the list

#### Step 2: Monitor Execution

Watch these tables in the database:

**A. `schedule_runs` table:**
```sql
SELECT id, schedule_id, status, started_at, finished_at, report_run_id
FROM schedule_runs
WHERE schedule_id = '<your_schedule_id>'
ORDER BY created_at DESC
LIMIT 5;
```

**Expected progression:**
- Status: `queued` (created by ticker)
- Status: `processing` (worker picked it up)
- Status: `completed` (email sent successfully)
- `finished_at` populated
- `report_run_id` matches a `report_runs.id`

**B. `report_generations` or `report_runs` table:**
```sql
SELECT id, report_type, status, pdf_url, result
FROM report_runs
WHERE id = '<report_run_id>'
;
```

**Expected:**
- `status = 'completed'`
- `pdf_url` is a valid R2 URL
- `result` JSON contains metrics

**C. `email_log` table:**
```sql
SELECT id, account_id, provider, to_emails, subject, response_code, error, created_at
FROM email_log
WHERE schedule_id = '<your_schedule_id>'
ORDER BY created_at DESC;
```

**Expected:**
- `provider = 'sendgrid'`
- `to_emails` = `[your_email@example.com]`
- `subject` = `"📊 Your Market Snapshot Report for Houston is Ready!"`
- `response_code = 202` (SendGrid success)
- `error` IS NULL

#### Step 3: Verify Email Delivery

**Check your inbox:**

✅ **From:** `TrendyReports <reports@yourdomain.com>`  
✅ **Subject:** `📊 Your Market Snapshot Report for Houston is Ready!`  
✅ **Body Contains:**
- Personalized greeting
- Purple gradient header
- 3 metrics: Active Listings, Pending, Closed
- Big purple CTA button: "📄 View Full Report (PDF)"
- Unsubscribe link in footer

✅ **Click "View Full Report":**
- Opens PDF from R2
- PDF contains Houston market data
- PDF is formatted correctly

#### Step 4: Test Unsubscribe Flow

1. **Click "Unsubscribe" link** in the email footer
2. Should redirect to: `https://reportscompany.vercel.app/api/v1/email/unsubscribe?token=...&email=...`
3. Expect response: `"Unsubscribed successfully"` or similar
4. **Verify in database:**
   ```sql
   SELECT * FROM email_suppressions
   WHERE email = 'your_email@example.com';
   ```
   **Expected:** Your email now appears in suppressions

5. **Trigger next run** (wait for next scheduled time or manually create another schedule)
6. **Verify:**
   - New `schedule_runs` entry created
   - New `email_log` entry with `response_code = 200` and note about suppression
   - **NO email** arrives in your inbox

---

## ✅ Phase 27A Completion Criteria

Mark Phase 27A as complete when:

- [x] SendGrid provider verified (already implemented)
- [x] Email orchestration verified (already implemented)
- [x] HTML template verified (already implemented)
- [x] Worker integration verified (already implemented)
- [ ] Suppression filtering added to `send.py`
- [ ] Environment variables set in Render
- [ ] `.env.example` files updated
- [ ] End-to-end test passes:
  - [ ] Schedule creates and triggers automatically
  - [ ] Report generates with PDF
  - [ ] Email sends via SendGrid
  - [ ] Email arrives in inbox with correct content
  - [ ] PDF link works
  - [ ] Unsubscribe link works
  - [ ] Suppressed emails don't receive future sends

---

## 🚀 Next Steps After Phase 27A

Once Phase 27A is certified:

1. **Update `PROJECT_STATUS-2.md`:** Mark Phase 27A as ✅ Complete
2. **Begin Phase 27B:** Build Schedules UI in web app
3. **Optional:** Polish email template copy and styling based on feedback

---

## 📞 Debugging Tips

### Email Not Sending?

1. Check Render logs for worker service:
   ```
   Sending schedule email to 1 recipient(s)
   Email sent successfully to ['...']
   ```

2. Check SendGrid dashboard:
   - Activity Feed should show the send
   - Check for bounces or blocks

3. Check `email_log` table:
   - If `response_code != 202`, check `error` column
   - Common issues: invalid API key, unverified sender

### Email Not Arriving?

1. Check spam folder
2. Verify sender email is verified in SendGrid
3. Check SendGrid Activity Feed for delivery status
4. Test with different email provider (Gmail, Outlook, etc.)

### Unsubscribe Not Working?

1. Check API logs for `/api/v1/email/unsubscribe` endpoint
2. Verify `UNSUBSCRIBE_SECRET` matches between worker and API
3. Check HMAC token generation in `send.py`
4. Verify RLS policies on `email_suppressions` table

---

**Last Updated:** November 13, 2025  
**Status:** ✅ Ready for Testing


# Deploying Schedules Ticker to Render

**Service Type:** Background Worker  
**Purpose:** Automatically find due schedules and enqueue report generation tasks  
**Cost:** Starter instance ($7/month) - runs 24/7

---

## Step 1: Create New Service in Render Dashboard

1. Go to https://dashboard.render.com
2. Click **"New +"** → **"Background Worker"**
3. Connect to your GitHub repository: `easydeed/reportscompany`
4. Click **"Connect"**

---

## Step 2: Configure Service

### Basic Settings

**Name:** `market-reports-ticker`

**Region:** Same as your Worker service (e.g., Oregon, USA)

**Branch:** `main`

**Root Directory:** `apps/worker`

---

### Build Settings

**Build Command:**
```bash
pip install poetry && poetry install --no-root
```

**Start Command:**
```bash
PYTHONPATH=./src poetry run python -m worker.schedules_tick
```

---

### Instance Type

**Plan:** Starter ($7/month)

**Why Starter is Enough:**
- Ticker only queries database and enqueues tasks every 60 seconds
- No heavy computation (report generation happens in Worker service)
- Low memory footprint (~100 MB)
- No PDF generation, no SimplyRETS API calls

---

## Step 3: Environment Variables

### Required Variables

Copy these from your **Worker** service:

```bash
DATABASE_URL=postgresql://mr_staging_db_user:vlFYf9ykajrJC7y62as6RKazBSr37fUU@dpg-d474qiqli9vc738g17e0-a.oregon-postgres.render.com/mr_staging_db

REDIS_URL=rediss://default:Aew9AAIjcDE0MzNmNjUyN2M5NmY0NDYwYmUxZjBiMjE5ZmE1MzljN3AxMA@mutual-falcon-60419.upstash.io:6379?ssl_cert_reqs=CERT_REQUIRED

CELERY_RESULT_URL=rediss://default:Aew9AAIjcDE0MzNmNjUyN2M5NmY0NDYwYmUxZjBiMjE5ZmE1MzljN3AxMA@mutual-falcon-60419.upstash.io:6379?ssl_cert_reqs=CERT_REQUIRED
```

**Important:** DO NOT add quotes around values in Render UI. Paste values as-is.

---

### Optional Variables

```bash
TICK_INTERVAL=60
# How many seconds between schedule checks
# Default: 60 (check every minute)
# Lower = more responsive, higher = less load
```

---

### Variables NOT Needed

The ticker **does not need** these (only Worker service needs them):

❌ `SIMPLYRETS_USERNAME`  
❌ `SIMPLYRETS_PASSWORD`  
❌ `PDF_ENGINE`  
❌ `PDFSHIFT_API_KEY`  
❌ `PDFSHIFT_API_URL`  
❌ `PRINT_BASE`  
❌ `STORAGE_MODE`  
❌ `S3_ENDPOINT`  
❌ `S3_BUCKET`  
❌ `S3_ACCESS_KEY_ID`  
❌ `S3_SECRET_ACCESS_KEY`  
❌ `PUBLIC_BASE_URL`  

**Why?** The ticker only:
1. Queries the database for due schedules
2. Enqueues tasks to Celery/Redis
3. The Worker service handles the actual report generation

---

## Step 4: Deploy

1. Click **"Create Background Worker"**
2. Render will:
   - Clone your repo
   - Run build command (install Poetry + dependencies)
   - Start ticker process
3. Watch the logs for:
   ```
   Schedules ticker started (interval: 60s)
   Database: dpg-d474qiqli9vc738g17e0-a.oregon-postgres.render.com/mr_staging_db
   ```

---

## Step 5: Verify Deployment

### Check Logs

In Render Dashboard → `market-reports-ticker` → Logs tab:

**Expected startup logs:**
```
INFO - Schedules ticker started (interval: 60s)
INFO - Database: dpg-***...
DEBUG - Tick: Checking for due schedules...
DEBUG - No due schedules found
```

**If you see errors:**
- `OperationalError: connection failed` → Check `DATABASE_URL`
- `ConnectionError: Redis` → Check `REDIS_URL` has `?ssl_cert_reqs=CERT_REQUIRED`
- `ModuleNotFoundError: worker.app` → Check `PYTHONPATH=./src` in start command

---

## Step 6: Test with Dummy Schedule

### Method 1: Via API (Recommended)

```bash
# Create a schedule via API
curl -X POST https://api-staging.easydeed.com/v1/schedules \
  -H "Authorization: Bearer <your-jwt-token>" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Test Ticker Schedule",
    "report_type": "market_snapshot",
    "city": "Houston",
    "cadence": "weekly",
    "weekly_dow": 1,
    "send_hour": 9,
    "send_minute": 0,
    "recipients": ["test@example.com"],
    "active": true
  }'

# Note the schedule ID from response, then set it to past due:
# Connect to database and run:
# UPDATE schedules SET next_run_at = NOW() - INTERVAL '1 minute' WHERE id = '<schedule-id>';
```

### Method 2: Direct Database Insert

```sql
-- Connect to staging database
psql "postgresql://mr_staging_db_user:***@dpg-***..."

-- Create test schedule (due 1 hour ago)
INSERT INTO schedules (
    account_id,
    name,
    report_type,
    city,
    cadence,
    weekly_dow,
    send_hour,
    send_minute,
    recipients,
    active,
    next_run_at
) VALUES (
    '912014c3-6deb-4b40-a28d-489ef3923a3a',  -- Demo account
    'Ticker Test Schedule',
    'market_snapshot',
    'San Diego',
    'weekly',
    1,
    9,
    0,
    ARRAY['test@example.com'],
    true,
    NOW() - INTERVAL '1 hour'
);
```

---

### What Should Happen (Within 60 Seconds)

**1. Ticker logs:**
```
INFO - Found 1 due schedule(s)
INFO - Enqueued report for schedule <id>, task_id: <celery-task-id>
INFO - Processed schedule 'Ticker Test Schedule': run_id=<id>, task_id=<id>, next_run_at=2025-11-17T09:00:00
```

**2. Worker logs (Worker service, not Ticker):**
```
[celery@worker] Received task: generate_report[<task-id>]
[INFO] Starting report generation for account <account-id>
```

**3. Database changes:**
```sql
-- Check schedule was updated
SELECT name, last_run_at, next_run_at FROM schedules WHERE name = 'Ticker Test Schedule';
-- last_run_at: just now
-- next_run_at: next Monday at 9:00 AM

-- Check schedule_runs audit record
SELECT status, created_at FROM schedule_runs ORDER BY created_at DESC LIMIT 1;
-- status: queued (or processing/completed if Worker picked it up)

-- Check report_generations
SELECT id, status, report_type FROM report_generations ORDER BY created_at DESC LIMIT 1;
-- Should see new report generation
```

---

## Troubleshooting

### Ticker Not Starting

**Error:** `poetry: command not found`
**Fix:** Build command should be: `pip install poetry && poetry install --no-root`

**Error:** `ModuleNotFoundError: No module named 'worker'`
**Fix:** Start command must include `PYTHONPATH=./src`

---

### Ticker Running But Not Finding Schedules

**Check 1:** Are schedules active?
```sql
SELECT id, name, active, next_run_at FROM schedules WHERE active = true;
```

**Check 2:** Is `next_run_at` in the past?
```sql
SELECT id, name, next_run_at, NOW() as current_time
FROM schedules
WHERE active = true AND (next_run_at IS NULL OR next_run_at <= NOW());
```

**Check 3:** Check ticker logs for errors:
```
ERROR - Failed to query due schedules: ...
```

---

### Schedules Found But Not Enqueued

**Error:** `ConnectionError: Error connecting to Redis`
**Fix:** Verify `REDIS_URL` includes `?ssl_cert_reqs=CERT_REQUIRED`

**Error:** `celery.exceptions.OperationalError`
**Fix:** Verify `CELERY_RESULT_URL` matches `REDIS_URL`

---

### Reports Not Generating After Enqueue

**This means Worker service has an issue, not Ticker.**

Check Worker service logs for:
- SimplyRETS connection errors
- PDF generation failures
- Database connection issues

The Ticker's job is done once it enqueues the task to Celery.

---

## Monitoring

### Key Metrics

**1. Service Health:**
- Render Dashboard → `market-reports-ticker` → Should show "Running"
- Logs should show tick every 60 seconds

**2. Due Schedule Count (should be near 0):**
```sql
SELECT COUNT(*) FROM schedules
WHERE active = true
  AND (next_run_at IS NULL OR next_run_at <= NOW());
```

**3. Recent Schedule Runs:**
```sql
SELECT
    s.name,
    sr.status,
    sr.created_at,
    sr.finished_at
FROM schedule_runs sr
JOIN schedules s ON s.id = sr.schedule_id
ORDER BY sr.created_at DESC
LIMIT 10;
```

---

## Scaling Considerations

### Current Setup (Starter Instance)

**Capacity:**
- Processes up to 100 schedules per tick
- With 60-second interval: **6,000 schedules/hour max**
- Each schedule execution takes ~100ms

**When to Upgrade:**
- If you have > 1,000 active schedules
- If ticker logs show lag (ticks taking > 1 second)
- If schedules are consistently delayed

**Upgrade Path:**
- Move to Standard instance ($25/month)
- Or: Run multiple ticker instances (requires coordination lock)
- Or: Reduce `TICK_INTERVAL` to 30 seconds

---

## Cost Breakdown

**Current Render Setup:**
- API: Starter ($7/month)
- Worker: Standard ($25/month) - needs resources for Playwright/PDF
- **Ticker: Starter ($7/month)** - NEW
- PostgreSQL: Starter ($7/month)

**Total: $46/month** for staging environment

**Production Recommendation:**
- API: Standard ($25/month) - higher request capacity
- Worker: Standard or Professional ($85/month) - parallel report generation
- Ticker: Starter ($7/month) - sufficient unless > 1,000 schedules
- PostgreSQL: Standard ($20/month) - more connections

---

## Summary Checklist

- [ ] Create Background Worker service in Render
- [ ] Set name: `market-reports-ticker`
- [ ] Set root directory: `apps/worker`
- [ ] Set build command: `pip install poetry && poetry install --no-root`
- [ ] Set start command: `PYTHONPATH=./src poetry run python -m worker.schedules_tick`
- [ ] Add `DATABASE_URL` environment variable
- [ ] Add `REDIS_URL` environment variable (with `?ssl_cert_reqs=CERT_REQUIRED`)
- [ ] Add `CELERY_RESULT_URL` environment variable
- [ ] Deploy service
- [ ] Verify startup logs show "Schedules ticker started"
- [ ] Create test schedule (set `next_run_at` to past)
- [ ] Verify ticker finds and processes schedule within 60 seconds
- [ ] Verify `schedule_runs` audit record created
- [ ] Verify report generation enqueued to Worker
- [ ] Delete test schedule

---

**Status:** Ready to Deploy  
**Next:** Phase 24D (Email sender) or Phase 24E (Frontend UI)


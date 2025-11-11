# Phase 24C: Schedules Ticker Process - Summary

**Date:** November 10, 2025  
**Status:** ✅ Code Complete, Ready to Deploy

---

## What Was Created

### Schedules Ticker (`apps/worker/src/worker/schedules_tick.py`)

**Purpose:** Background process that automatically finds due schedules and enqueues report generation tasks.

**How It Works:**
1. **Every 60 seconds** (configurable via `TICK_INTERVAL` env var):
   - Query database for schedules where `active = true` AND (`next_run_at IS NULL` OR `next_run_at <= NOW()`)
   - Process up to 100 due schedules per tick
   
2. **For each due schedule:**
   - Compute next run time based on cadence (weekly/monthly)
   - Enqueue report generation task to Celery
   - Create `schedule_runs` audit record (status: 'queued')
   - Update `schedules.last_run_at` and `schedules.next_run_at`

3. **Error handling:**
   - Individual schedule failures don't stop the ticker
   - All errors logged with full stack traces
   - Database rollback per schedule on failure

---

## Next Run Time Computation

### Weekly Cadence
```python
compute_next_run(cadence="weekly", weekly_dow=1, send_hour=9, send_minute=0)
```

- Finds the next occurrence of `weekly_dow` (0=Sunday, 6=Saturday)
- At the specified `send_hour:send_minute`
- Example: `weekly_dow=1` (Monday) at 9:00 AM → Next Monday at 9:00 AM

**Logic:**
```
Current time: Friday 3:00 PM
Target: Monday (dow=1) at 9:00 AM
→ Next Monday (3 days ahead) at 9:00 AM
```

### Monthly Cadence
```python
compute_next_run(cadence="monthly", monthly_dom=15, send_hour=9, send_minute=0)
```

- Finds the `monthly_dom` day of the next month (capped at 28 for safety)
- At the specified `send_hour:send_minute`
- Example: `monthly_dom=15` → 15th of next month at 9:00 AM

**Logic:**
```
Current time: November 10, 2025, 3:00 PM
Target: 15th at 9:00 AM
→ November 15, 2025, 9:00 AM (5 days ahead)

Current time: November 20, 2025, 3:00 PM
Target: 15th at 9:00 AM
→ December 15, 2025, 9:00 AM (already passed this month)
```

---

## Celery Task Enqueuing

### Task Payload
```python
celery.send_task(
    "generate_report",
    args=[account_id, params],
    queue="celery"
)
```

### Params Structure
```python
{
    "report_type": "market_snapshot",
    "city": "San Diego",
    "zips": ["92101", "92103"],
    "lookback_days": 30,
    "filters": {},
    "schedule_id": "abc-123-def-456"  # Links back to schedule
}
```

**Note:** This matches the exact format the existing `generate_report` Celery task expects, ensuring seamless integration.

---

## Database Operations

### Find Due Schedules
```sql
SELECT id, account_id, name, report_type, city, zip_codes,
       lookback_days, cadence, weekly_dow, monthly_dom,
       send_hour, send_minute, recipients, include_attachment
FROM schedules
WHERE active = true
  AND (next_run_at IS NULL OR next_run_at <= NOW())
ORDER BY COALESCE(next_run_at, '1970-01-01') ASC
LIMIT 100
```

### Create Audit Record
```sql
INSERT INTO schedule_runs (schedule_id, status, created_at)
VALUES (%s, 'queued', NOW())
RETURNING id
```

### Update Schedule Timestamps
```sql
UPDATE schedules
SET last_run_at = NOW(),
    next_run_at = %s
WHERE id = %s
```

---

## Deployment to Render

### Step 1: Create New Background Worker Service

**Service Name:** `market-reports-ticker`

**Environment:** Same region as Worker/API (for low-latency DB access)

**Instance Type:** Starter ($7/month - low resource, runs continuously)

---

### Step 2: Configuration

**Root Directory:** `apps/worker`

**Build Command:**
```bash
pip install poetry && poetry install --no-root
```

**Start Command:**
```bash
PYTHONPATH=./src poetry run python -m worker.schedules_tick
```

**Health Check Path:** `/` (not applicable for background workers)

---

### Step 3: Environment Variables

Copy from Worker service, plus add:

```bash
# Database (REQUIRED)
DATABASE_URL=postgresql://mr_staging_db_user:***@dpg-***...

# Celery/Redis (REQUIRED)
REDIS_URL=rediss://***:***@***.upstash.io:6379?ssl_cert_reqs=CERT_REQUIRED
CELERY_RESULT_URL=<same as REDIS_URL>

# Ticker Configuration (OPTIONAL)
TICK_INTERVAL=60  # Check for due schedules every 60 seconds

# Not needed for ticker (no SimplyRETS/PDF/R2 calls)
# SIMPLYRETS_USERNAME, PDFSHIFT_API_KEY, S3_* etc.
```

**Required Vars:**
- `DATABASE_URL` - PostgreSQL connection
- `REDIS_URL` - Celery broker
- `CELERY_RESULT_URL` - Celery results backend

**Optional Vars:**
- `TICK_INTERVAL` - Seconds between checks (default: 60)

---

## Logging

### Log Levels

**INFO:** Normal operations
```
2025-11-10 21:00:00 - worker.schedules_tick - INFO - Schedules ticker started (interval: 60s)
2025-11-10 21:00:00 - worker.schedules_tick - INFO - Found 2 due schedule(s)
2025-11-10 21:00:01 - worker.schedules_tick - INFO - Enqueued report for schedule abc-123, task_id: xyz-789
2025-11-10 21:00:01 - worker.schedules_tick - INFO - Processed schedule 'Weekly Market Snapshot': run_id=def-456, task_id=xyz-789, next_run_at=2025-11-17T09:00:00
```

**DEBUG:** Verbose tick logging
```
2025-11-10 21:01:00 - worker.schedules_tick - DEBUG - Tick: Checking for due schedules...
2025-11-10 21:01:00 - worker.schedules_tick - DEBUG - No due schedules found
```

**ERROR:** Failures
```
2025-11-10 21:00:00 - worker.schedules_tick - ERROR - Failed to process schedule abc-123: ValueError: weekly_dow required for weekly cadence
```

---

## Testing Strategy

### Local Testing

**1. Start local services:**
```powershell
# Terminal 1: Start Docker services
docker compose up -d

# Terminal 2: Start Celery worker
cd apps/worker
poetry run celery -A worker.app.celery worker -l info

# Terminal 3: Start ticker
cd apps/worker
$env:DATABASE_URL = "postgresql://postgres:postgres@localhost:5432/market_reports"
$env:REDIS_URL = "redis://localhost:6379/0"
poetry run python -m worker.schedules_tick
```

**2. Create test schedule with past next_run_at:**
```sql
INSERT INTO schedules (
    account_id, name, report_type, city, cadence,
    weekly_dow, send_hour, send_minute, recipients, active, next_run_at
) VALUES (
    '912014c3-6deb-4b40-a28d-489ef3923a3a',
    'Test Weekly Snapshot',
    'market_snapshot',
    'San Diego',
    'weekly',
    1,  -- Monday
    9,
    0,
    ARRAY['test@example.com'],
    true,
    NOW() - INTERVAL '1 hour'  -- Due 1 hour ago
);
```

**3. Watch ticker logs:**
- Should find the schedule within 60 seconds
- Enqueue report generation task
- Celery worker should pick up the task
- Check `schedule_runs` table for audit record

---

### Staging Testing

**After deploying to Render:**

**1. Check service logs:**
```
Render Dashboard → market-reports-ticker → Logs
```

**2. Create test schedule via API:**
```bash
curl -X POST https://api-staging.example.com/v1/schedules \
  -H "Authorization: Bearer <jwt>" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Test Schedule",
    "report_type": "market_snapshot",
    "city": "Houston",
    "cadence": "weekly",
    "weekly_dow": 1,
    "send_hour": 9,
    "send_minute": 0,
    "recipients": ["test@example.com"],
    "active": true
  }'
```

**3. Manually trigger (set next_run_at to past):**
```sql
UPDATE schedules
SET next_run_at = NOW() - INTERVAL '1 minute'
WHERE name = 'Test Schedule';
```

**4. Within 60 seconds, check:**
- Ticker logs: "Found 1 due schedule(s)"
- Schedule updated: `last_run_at` filled, `next_run_at` recomputed
- `schedule_runs` table: New row with status='queued'
- Worker logs: "Received task: generate_report"
- Reports table: New report_generations row

---

## Error Scenarios & Handling

### Schedule Missing Required Fields
```
ERROR - Failed to process schedule abc-123: ValueError: weekly_dow required for weekly cadence
```
**Resolution:** Schedule stays due, will retry next tick (60s). Fix schedule via PATCH API.

### Database Connection Lost
```
ERROR - Failed to query due schedules: psycopg.OperationalError: connection closed
```
**Resolution:** Ticker sleeps 60s, retries. Render auto-restarts on crash.

### Celery Connection Lost
```
ERROR - Failed to process schedule abc-123: ConnectionError: Error connecting to Redis
```
**Resolution:** Schedule stays due (not committed), will retry next tick.

### Schedule Computation Bug
```
ERROR - Failed to process schedule abc-123: ValueError: day is out of range for month
```
**Resolution:** Individual schedule skipped, others continue. Fix monthly_dom (cap at 28).

---

## Monitoring & Observability

### Key Metrics to Track

**1. Due Schedule Count:**
```sql
SELECT COUNT(*) FROM schedules
WHERE active = true
  AND (next_run_at IS NULL OR next_run_at <= NOW());
```
Should be near 0 most of the time (ticker processes them quickly).

**2. Schedule Run Success Rate:**
```sql
SELECT
    status,
    COUNT(*),
    ROUND(100.0 * COUNT(*) / SUM(COUNT(*)) OVER(), 2) AS percentage
FROM schedule_runs
WHERE created_at >= NOW() - INTERVAL '24 hours'
GROUP BY status;
```

**3. Average Processing Time:**
Check Celery task durations for `generate_report` tasks with `schedule_id` in params.

---

## File Structure

```
apps/worker/src/worker/
├── schedules_tick.py          # NEW - Ticker process (312 lines)
├── app.py                      # Existing - Celery config
├── tasks.py                    # Existing - Report generation task
└── compute/                    # Existing - Report logic
```

**No changes to existing files!** The ticker is completely standalone.

---

## Next Steps

### Immediate:
1. **Deploy ticker to Render** (Phase 24C continued)
2. **Test with dummy schedule** (set `next_run_at` to past)
3. **Verify audit trail** (schedule_runs table)

### Phase 24D: Email Sender
- Create email delivery function (link-only emails)
- Integrate with SendGrid or Resend
- Respect email_suppressions (unsubscribe list)
- Update schedule_runs.status based on email result
- Log to email_log table

### Phase 24E: Frontend UI
- Schedules list page
- Create/edit schedule form
- Execution history view
- Enable/disable toggle

---

**Status:** 24C ✅ Code Complete, Ready to Deploy

**Files Created:**
- `apps/worker/src/worker/schedules_tick.py` (312 lines)
- `PHASE_24C_SUMMARY.md` (this file)

**Next:** Deploy to Render as Background Worker


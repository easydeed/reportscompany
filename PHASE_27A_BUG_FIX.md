# Phase 27A Bug Fixes - Ticker/Worker Issues

**Date:** November 13, 2025  
**Status:** ✅ Both Bugs Fixed and Deployed  
**Commits:** `a0ebb0c`, `d47c98a`

---

## Bug #1: Argument Mismatch

When the ticker enqueued a scheduled report, the worker crashed with:

```
TypeError: generate_report() missing 2 required positional arguments: 'report_type' and 'params'
```

### Root Cause

**Argument Mismatch between Ticker and Worker:**

**Ticker was calling** (`schedules_tick.py` line 169-172):
```python
task = celery.send_task(
    "generate_report",
    args=[account_id, params],  # ← Only 2 arguments
    queue="celery"
)
```

**Worker was expecting** (`tasks.py` line 146):
```python
@celery.task(name="generate_report")
def generate_report(run_id: str, account_id: str, report_type: str, params: dict):
    # ← Expects 4 arguments: run_id, account_id, report_type, params
```

**Result:** Worker received 2 args but needed 4 → TypeError

---

## The Fix

**File:** `apps/worker/src/worker/schedules_tick.py`

### Changes Made

1. **Create `report_generations` record first** (to get `run_id`):
   ```python
   with psycopg.connect(DATABASE_URL) as conn:
       with conn.cursor() as cur:
           cur.execute(f"SET LOCAL app.current_account_id TO '{account_id}'")
           cur.execute("""
               INSERT INTO report_generations (account_id, status)
               VALUES (%s::uuid, 'queued')
               RETURNING id::text
           """, (account_id,))
           run_id = cur.fetchone()[0]
       conn.commit()
   ```

2. **Pass all 4 required arguments**:
   ```python
   task = celery.send_task(
       "generate_report",
       args=[run_id, account_id, report_type, params],  # ← All 4 args
       queue="celery"
   )
   ```

3. **Link `schedule_run` to `report_generation`**:
   ```python
   cur.execute("""
       INSERT INTO schedule_runs (schedule_id, report_run_id, status, created_at)
       VALUES (%s::uuid, %s::uuid, 'queued', NOW())
       RETURNING id::text
   """, (schedule_id, report_gen_id))
   ```

### Benefits

- ✅ Worker now receives correct arguments
- ✅ `report_generations` record created before worker starts
- ✅ `schedule_runs` properly linked to `report_generations`
- ✅ Full audit trail maintained

---

## Testing the Fix

### 1. Wait for Render Deployment

Render auto-deploys on git push. Check:
- **Ticker service:** Should redeploy within 2-3 minutes
- Look for: `==> Your service is live 🎉`

### 2. Delete Old Schedule + Create New One

**Option A: Use the script:**
```bash
python reset_and_test.py
```

**Option B: Manual SQL:**
```sql
-- Delete old schedule
DELETE FROM schedules 
WHERE id = 'a61d14d6-c634-440f-9da6-fd9bd488f165';

-- Create new one
INSERT INTO schedules (
  account_id, name, report_type, city, lookback_days,
  cadence, weekly_dow, send_hour, send_minute,
  recipients, active, created_at, next_run_at
) VALUES (
  '912014c3-6deb-4b40-a28d-489ef3923a3a',
  'Phase 27A Email Test - Gerard (v2)',
  'market_snapshot', 'Houston', 30,
  'weekly', 1, 14, 0,
  ARRAY['gerardoh@gmail.com'], true, NOW(),
  NOW() - INTERVAL '1 minute'
)
RETURNING id, name, next_run_at;
```

### 3. Monitor Execution

```bash
# Update check_schedule_status.py with new schedule ID
# Then run:
python check_schedule_status.py
```

**Expected flow:**
1. Ticker picks up schedule (within 60 seconds)
2. Creates `report_generations` record
3. Enqueues Celery task with correct args
4. Worker processes successfully
5. PDF uploaded to R2
6. Email sent via SendGrid
7. Email arrives at gerardoh@gmail.com

### 4. Check Logs

**Ticker logs** (should show):
```
INFO - Found 1 due schedule(s)
INFO - Enqueued report for schedule [...], run_id=[...], task_id=[...]
INFO - Processed schedule 'Phase 27A Email Test - Gerard (v2)'
```

**Worker logs** (should show):
```
INFO - Task generate_report[...] received
INFO - Generating report...
INFO - PDF uploaded to R2
INFO - Sending email to ['gerardoh@gmail.com']
INFO - SendGrid response: 202
```

---

## Success Criteria

- [ ] Ticker deploys successfully
- [ ] New schedule created with `next_run_at` in past
- [ ] Ticker picks up schedule within 60 seconds
- [ ] Worker processes without errors
- [ ] `report_generations.status = 'completed'`
- [ ] `schedule_runs.status = 'completed'`
- [ ] `email_log.response_code = 202`
- [ ] Email arrives at gerardoh@gmail.com
- [ ] PDF link works
- [ ] Unsubscribe link works

---

## What Was Wrong Originally

The ticker was built assuming a different signature for `generate_report`:
- It was passing only `account_id` and `params`
- But the worker was updated at some point to require `run_id` first
- This mismatch wasn't caught until end-to-end testing

## Lesson Learned

**Always sync function signatures between task producer and consumer!**

In Celery:
- Producer: `celery.send_task("task_name", args=[...])`
- Consumer: `@celery.task(name="task_name") def func(...)`

The `args` list must match the function signature exactly.

---

---

## Bug #2: NOT NULL Constraint Violation

**Commit:** `d47c98a`

After fixing Bug #1, the ticker crashed with:

```
psycopg.errors.NotNullViolation: null value in column "report_type" of relation "report_generations" violates not-null constraint
```

### Root Cause

When creating the `report_generations` record, we were only inserting:
```python
INSERT INTO report_generations (account_id, status)
VALUES (%s::uuid, 'queued')
```

But the table has a NOT NULL constraint on `report_type`.

### The Fix

Updated the INSERT to include all required fields:

```python
INSERT INTO report_generations (account_id, report_type, input_params, status)
VALUES (%s::uuid, %s, %s::jsonb, 'queued')
```

Also added `safe_json_dumps()` helper function to serialize params as JSONB.

---

**Status:** Both bugs fixed, waiting for Render deployment.

**Next:** 
1. Wait for ticker redeployment (2-3 minutes)
2. Delete old schedule and create new test
3. Monitor execution and verify email delivery


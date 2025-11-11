# Phase 24A: Schedules Migration - Command Reference

**Date:** November 10, 2025  
**Status:** ✅ Migration file created, ready to apply

---

## ✅ Step 1: Migration File Created

**File:** `db/migrations/0006_schedules.sql`

**Tables:**
1. `schedules` - Schedule configurations (weekly/monthly cadence)
2. `schedule_runs` - Execution audit trail
3. `email_log` - Email delivery tracking
4. `email_suppressions` - Unsubscribe list

**RLS:** All tables have Row-Level Security enabled with account-scoped policies.

---

## 🏠 Step 2: Apply Locally (Docker Postgres)

### PowerShell Command:
```powershell
$env:DATABASE_URL = "postgresql://postgres:postgres@localhost:5432/market_reports"
bash scripts/migrate.sh
```

### Verify Tables Created:
```powershell
docker exec mr_postgres psql -U postgres -d market_reports -c "\dt schedules* email_*"
```

**Expected Output:**
```
                 List of relations
 Schema |         Name          | Type  |  Owner
--------+-----------------------+-------+----------
 public | email_log             | table | postgres
 public | email_suppressions    | table | postgres
 public | schedule_runs         | table | postgres
 public | schedules             | table | postgres
```

### Verify RLS Enabled:
```powershell
docker exec mr_postgres psql -U postgres -d market_reports -c "\d+ schedules"
```

**Look for:** `Row security: enabled`

### Verify Policies Created:
```powershell
docker exec mr_postgres psql -U postgres -d market_reports -c "SELECT tablename, policyname FROM pg_policies WHERE tablename IN ('schedules','schedule_runs','email_log','email_suppressions');"
```

**Expected:** 4 policies (`schedules_rls`, `schedule_runs_rls`, `email_log_rls`, `email_suppressions_rls`)

---

## ☁️ Step 3: Apply to Staging (Render Postgres)

### PowerShell Command:
```powershell
$env:DATABASE_URL = "postgresql://mr_staging_db_user:vlFYf9ykajrJC7y62as6RKazBSr37fUU@dpg-d474qiqli9vc738g17e0-a.oregon-postgres.render.com/mr_staging_db"
bash scripts/migrate.sh
```

### Verify (from your machine):
```powershell
# Set the DATABASE_URL first
$env:DATABASE_URL = "postgresql://mr_staging_db_user:vlFYf9ykajrJC7y62as6RKazBSr37fUU@dpg-d474qiqli9vc738g17e0-a.oregon-postgres.render.com/mr_staging_db"

# Check tables
psql $env:DATABASE_URL -c "\dt schedules* email_*"

# Check policies
psql $env:DATABASE_URL -c "SELECT tablename, policyname FROM pg_policies WHERE tablename IN ('schedules','schedule_runs','email_log','email_suppressions');"
```

---

## 🧪 Step 4: Seed Test Data (Optional)

### Create Test Schedule Locally:
```powershell
docker exec mr_postgres psql -U postgres -d market_reports -c "
SET LOCAL app.current_account_id = '912014c3-6deb-4b40-a28d-489ef3923a3a';

INSERT INTO schedules(
  account_id,
  name,
  report_type,
  city,
  cadence,
  weekly_dow,
  send_hour,
  send_minute,
  recipients,
  active
) VALUES (
  '912014c3-6deb-4b40-a28d-489ef3923a3a',
  'Weekly Market Snapshot',
  'market_snapshot',
  'San Diego',
  'weekly',
  1,
  9,
  0,
  ARRAY['test@example.com'],
  true
);

SELECT id, name, cadence, weekly_dow, send_hour, recipients FROM schedules;
"
```

**Expected:** One row returned with your test schedule.

### View Test Schedule:
```powershell
docker exec mr_postgres psql -U postgres -d market_reports -c "
SET LOCAL app.current_account_id = '912014c3-6deb-4b40-a28d-489ef3923a3a';
SELECT id, name, report_type, city, cadence, weekly_dow, send_hour, recipients, active FROM schedules;
"
```

---

## 📝 Step 5: Commit Migration

```bash
git add db/migrations/0006_schedules.sql
git commit -m "feat(db): schedules + runs + email logs + suppressions (RLS)"
git push
```

---

## ✅ Verification Checklist

After running migrations:

**Local:**
- [ ] 4 tables created (`schedules`, `schedule_runs`, `email_log`, `email_suppressions`)
- [ ] RLS enabled on all 4 tables
- [ ] 4 policies created
- [ ] Indexes created (`idx_schedules_due`, `idx_schedule_runs_sched`, `idx_email_log_acct`)
- [ ] Test schedule inserted successfully

**Staging:**
- [ ] All 4 tables present
- [ ] RLS enabled
- [ ] Policies active
- [ ] No errors in migration logs

---

## 🐛 Troubleshooting

### Error: "relation already exists"
**Cause:** Migration already applied  
**Fix:** This is okay! Migration uses `IF NOT EXISTS` so it's idempotent.

### Error: "permission denied"
**Cause:** Wrong database credentials  
**Fix:** Double-check `DATABASE_URL` matches your environment

### Error: "bash: command not found"
**Cause:** Git Bash not in PATH on Windows  
**Fix:** Use Git Bash terminal directly, or use WSL

### Policy Not Created
**Check:** 
```sql
SELECT * FROM pg_policies WHERE tablename = 'schedules';
```
**Fix:** Policies use `IF NOT EXISTS` check, should auto-create

---

## 📊 Schema Overview

### Schedules Table
```
- id: UUID (PK)
- account_id: UUID (FK to accounts)
- name: TEXT
- report_type: TEXT (market_snapshot, new_listings, etc.)
- city: TEXT
- zip_codes: TEXT[]
- lookback_days: INT (default 30)
- cadence: TEXT (weekly/monthly)
- weekly_dow: INT (0-6, Sun-Sat)
- monthly_dom: INT (1-28)
- send_hour: INT (0-23)
- send_minute: INT (0-59)
- recipients: TEXT[] (email list)
- include_attachment: BOOLEAN (default false)
- active: BOOLEAN (default true)
- last_run_at: TIMESTAMPTZ
- next_run_at: TIMESTAMPTZ
- created_at: TIMESTAMPTZ
```

### Schedule Runs Table
```
- id: UUID (PK)
- schedule_id: UUID (FK to schedules)
- report_run_id: UUID (FK to report_generations)
- status: TEXT (queued/processing/completed/failed)
- error: TEXT
- started_at: TIMESTAMPTZ
- finished_at: TIMESTAMPTZ
- created_at: TIMESTAMPTZ
```

### Email Log Table
```
- id: UUID (PK)
- account_id: UUID (FK to accounts)
- schedule_id: UUID
- report_id: UUID
- provider: TEXT (e.g., 'sendgrid')
- to_emails: TEXT[]
- subject: TEXT
- response_code: INT
- error: TEXT
- created_at: TIMESTAMPTZ
```

### Email Suppressions Table
```
- id: UUID (PK)
- account_id: UUID (FK to accounts)
- email: TEXT
- reason: TEXT
- created_at: TIMESTAMPTZ
- UNIQUE(account_id, email)
```

---

**Status:** Ready to run! 🚀  
**Next Phase:** 24B - API Routes for CRUD operations



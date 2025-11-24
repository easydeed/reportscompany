# SCHEDULE SYSTEM AUDIT

**Date**: Nov 24, 2025  
**Purpose**: Document exact behavior of the schedule system (data, worker, API, frontend)  
**Status**: Read-only audit (no code changes)

---

## 1. Data Model

### 1.1 Schedules Table (`schedules`)

**Schema** (from `db/migrations/0006_schedules.sql`):
```sql
CREATE TABLE schedules (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  account_id UUID NOT NULL REFERENCES accounts(id) ON DELETE CASCADE,
  name TEXT NOT NULL,
  report_type TEXT NOT NULL,  -- market_snapshot, new_listings, closed, inventory, price_bands, new_listings_gallery, featured_listings
  
  -- Target area
  city TEXT,
  zip_codes TEXT[],
  lookback_days INT DEFAULT 30,
  
  -- Cadence
  cadence TEXT NOT NULL CHECK (cadence IN ('weekly','monthly')),
  weekly_dow INT,     -- 0=Sun, 6=Sat (required for weekly)
  monthly_dom INT,    -- 1-28 (required for monthly)
  send_hour INT DEFAULT 9,
  send_minute INT DEFAULT 0,
  
  -- Recipients
  recipients TEXT[] NOT NULL,  -- JSON-encoded typed recipients
  include_attachment BOOLEAN DEFAULT FALSE,
  
  -- Status
  active BOOLEAN DEFAULT TRUE,
  last_run_at TIMESTAMPTZ,
  next_run_at TIMESTAMPTZ,
  created_at TIMESTAMPTZ DEFAULT NOW()
);
```

**Recipients Format**:
- Stored as `TEXT[]` (PostgreSQL array of JSON-encoded strings)
- Each element is one of:
  ```json
  {"type":"contact","id":"<contact_id>"}
  {"type":"sponsored_agent","id":"<account_id>"}
  {"type":"group","id":"<group_id>"}
  {"type":"manual_email","email":"<email>"}
  ```
- Legacy format supported: Plain email strings (converted to `manual_email` type)

**Indexes**:
- `idx_schedules_due` on `(account_id, active, next_run_at)` for efficient ticker queries

**RLS**: Enabled with policy `schedules_rls` enforcing `account_id = current_setting('app.current_account_id')`

---

### 1.2 Schedule Runs Table (`schedule_runs`)

**Schema**:
```sql
CREATE TABLE schedule_runs (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  schedule_id UUID NOT NULL REFERENCES schedules(id) ON DELETE CASCADE,
  report_run_id UUID,  -- link to report_generations.id
  status TEXT NOT NULL DEFAULT 'queued',  -- queued|processing|completed|failed
  error TEXT,
  started_at TIMESTAMPTZ,
  finished_at TIMESTAMPTZ,
  created_at TIMESTAMPTZ DEFAULT NOW()
);
```

**Purpose**: Audit trail for schedule-triggered report executions

**RLS**: Enforced via `schedule_id IN (SELECT id FROM schedules WHERE account_id = current_account_id)`

---

### 1.3 Report Generations Table (`report_generations`)

**Purpose**: Tracks all report generation attempts (scheduled + manual)

**Key Fields**:
- `account_id`: Owner
- `report_type`: Type of report
- `input_params`: JSON with city, zip_codes, lookback_days, schedule_id
- `status`: queued → processing → completed/failed
- `result_json`: Final report data (metrics, properties)

**Used by**: Worker to track progress and store results

---

### 1.4 Email Log Table (`email_log`)

**Purpose**: Tracks all email deliveries (provider responses)

**Key Fields**:
- `account_id`, `schedule_id`, `report_id`
- `provider`: e.g., 'sendgrid'
- `to_emails`: Array of recipient emails
- `response_code`, `error`

---

### 1.5 Email Suppressions Table (`email_suppressions`)

**Purpose**: Unsubscribe list

**Key Fields**:
- `account_id`, `email`, `reason`
- Unique constraint on `(account_id, email)`

**Used by**: Email sending to filter out unsubscribed users

---

## 2. Worker Behavior

### 2.1 Schedule Ticker (`apps/worker/src/worker/schedules_tick.py`)

**Process**: Background worker that runs every 60 seconds

**Ticker Loop**:
```python
while True:
    process_due_schedules()  # Find & enqueue due schedules
    time.sleep(TICK_INTERVAL)  # Default 60 seconds
```

**`process_due_schedules()` Logic**:
1. **Query** due schedules:
   ```sql
   SELECT * FROM schedules
   WHERE active = true
     AND (next_run_at IS NULL OR next_run_at <= NOW())
   ORDER BY COALESCE(next_run_at, '1970-01-01') ASC
   LIMIT 100
   ```

2. **For each schedule**:
   - Compute `next_run_at` using `compute_next_run()`:
     - **Weekly**: Next occurrence of `weekly_dow` at `send_hour:send_minute`
     - **Monthly**: Next occurrence of day `monthly_dom` at `send_hour:send_minute`
   
   - Create `report_generations` record with `status='queued'`
   
   - Enqueue Celery task: `generate_report(run_id, account_id, report_type, params)`
   
   - Create `schedule_runs` audit record:
     - Link to `report_run_id` (report_generations.id)
     - Initial `status='queued'`
   
   - Update schedule:
     ```sql
     UPDATE schedules
     SET last_run_at = NOW(), next_run_at = %s
     WHERE id = %s
     ```

3. **Error Handling**:
   - If a single schedule fails: Log error, rollback that schedule's transaction, continue with next
   - Ticker continues running even if entire tick fails

**Key Behavior**:
- ✅ Schedules with `next_run_at = NULL` are processed immediately (first run)
- ✅ Ticker does **not** resolve recipients—that happens in the worker task
- ✅ `next_run_at` is computed **before** report generation starts
- ✅ If ticker crashes, schedules just wait for next tick (at most 60-second delay)

---

### 2.2 Report Generation Task (`apps/worker/src/worker/tasks.py`)

**Celery Task**: `generate_report(run_id, account_id, report_type, params)`

**Execution Flow**:
1. **Load schedule** (if `schedule_id` in params):
   ```sql
   SELECT recipients, account_id FROM schedules WHERE id = %s
   ```

2. **Resolve recipients** to emails via `resolve_recipients_to_emails()`:
   - For each recipient JSON string:
     - **`type: "contact"`**: Query `contacts` table → `email` (verify `account_id` ownership)
     - **`type: "sponsored_agent"`**: Query `accounts` → verify `sponsor_account_id` → get first user's `email`
     - **`type: "group"`**: Query `contact_groups` → verify `account_id` → query `contact_group_members` → recursively resolve contacts + sponsored agents
     - **`type: "manual_email"`**: Use `email` directly
     - **Legacy**: Plain email string → use as-is
   
   - **Ownership Checks**:
     - Contacts: `contacts.account_id = schedule.account_id`
     - Sponsored agents: `accounts.sponsor_account_id = schedule.account_id`
     - Groups: `contact_groups.account_id = schedule.account_id`
   
   - **Deduplicate**: Final list is `list(set(emails))`
   
   - **Edge Cases** (handled gracefully):
     - Contact deleted → Logs warning, skips
     - Sponsored agent unsponsored → Logs warning, skips
     - Group deleted → Logs warning, skips group
     - Group member deleted → Skips that member, continues with rest
     - No valid emails → Report still generates but may not send

3. **Fetch property data** from SimplyRETS (based on city/zip_codes)

4. **Generate metrics** and **build report JSON**

5. **Render PDF** (if needed, currently link-only for most reports)

6. **Upload to R2** (Cloudflare storage)

7. **Send email** via `send_schedule_email()`:
   - Filters recipients against `email_suppressions` table
   - Creates `email_log` entry with provider response

8. **Update status**:
   ```sql
   UPDATE report_generations
   SET status = 'completed', finished_at = NOW(), result_json = %s
   WHERE id = %s
   ```
   
   ```sql
   UPDATE schedule_runs
   SET status = 'completed', finished_at = NOW()
   WHERE report_run_id = %s
   ```

**Error Handling**:
- If report generation fails:
  - Set `report_generations.status = 'failed'`, `error = <exception>`
  - Set `schedule_runs.status = 'failed'`, `error = <exception>`
  - **Does NOT retry automatically** (Celery default is no retry)
  - Schedule's `next_run_at` was already set by ticker, so next run will attempt again

**Retry Behavior**: ❌ **NOT IMPLEMENTED**
- No automatic retries for failed reports
- If SimplyRETS is down or rate-limited, report fails and waits for next scheduled run

---

## 3. Recipients & People Integration

### 3.1 Recipient Resolution Logic

**Function**: `resolve_recipients_to_emails(cur, account_id, recipients_raw)`  
**File**: `apps/worker/src/worker/tasks.py`

**Security Checks**:
| Recipient Type | Ownership Check | Failure Behavior |
|---------------|----------------|------------------|
| `contact` | `contacts.account_id = schedule.account_id` | Log warning, skip |
| `sponsored_agent` | `accounts.sponsor_account_id = schedule.account_id` | Log warning, skip |
| `group` | `contact_groups.account_id = schedule.account_id` | Log warning, skip entire group |
| `manual_email` | None (always allowed) | Use as-is |

**Edge Case Matrix**:

| Scenario | Behavior | Impact on Schedule Run |
|----------|----------|----------------------|
| Contact deleted after schedule creation | Logs `⚠️ Contact {id} not found for account {account_id}`, skips | ✅ Continues with remaining recipients |
| Sponsored agent unsponsored | Logs `⚠️ Sponsored agent {id} not sponsored by {account_id}`, skips | ✅ Continues with remaining recipients |
| Group deleted | Logs `⚠️ Group {id} not found for account {account_id}`, skips | ✅ Continues with remaining recipients |
| Group member deleted (contact or agent) | Skips that member silently | ✅ Continues with other group members |
| All recipients invalid | Returns empty list `[]` | ⚠️ **Report generates but may not send** (depends on email logic) |
| JSON parse error | Logs warning, treats as plain email if contains `@` | ✅ Fallback to legacy behavior |

**Deduplication**: Final email list is deduped via `list(set(emails))`

**Result**: Schedule runs never "fail hard" due to missing recipients—they skip and continue

---

### 3.2 Integration with People System

**Data Flow**:
1. **Schedule Creation (Frontend)**: User selects People/Groups → Creates typed `RecipientInput` objects
2. **API Validation**: `apps/api/src/api/routes/schedules.py` validates ownership via `validate_recipient_ownership()`
3. **Storage**: Recipients encoded as JSON strings in `schedules.recipients` (TEXT[] column)
4. **Worker Resolution**: `resolve_recipients_to_emails()` decodes JSON and fetches current emails

**Key Point**: Recipients are **resolved at runtime**, not stored as static emails
- ✅ Ensures fresh data (contact email changes are reflected)
- ✅ Honors sponsorship state (unsponsored agents auto-removed)
- ⚠️ May skip large portions of recipients if data deleted

---

## 4. API & Security

### 4.1 Schedule API Endpoints

**Router**: `apps/api/src/api/routes/schedules.py`

| Endpoint | Method | Ownership Enforcement | Validation |
|----------|--------|---------------------|-----------|
| `/v1/schedules` | POST | `account_id` from middleware + RLS | • `cadence` matches `weekly_dow`/`monthly_dom`<br>• Recipients ownership validated<br>• At least 1 valid recipient |
| `/v1/schedules` | GET | RLS policy on `schedules` table | `active_only` param (default true) |
| `/v1/schedules/{id}` | GET | RLS policy on `schedules` table | Schedule must exist + belong to account |
| `/v1/schedules/{id}` | PATCH | RLS policy on `schedules` table | • Recipients ownership re-validated<br>• Sets `next_run_at = NULL` (forces recompute) |
| `/v1/schedules/{id}` | DELETE | RLS policy on `schedules` table | Cascade deletes `schedule_runs` |
| `/v1/schedules/{id}/runs` | GET | RLS policy via schedule ownership | Returns last 50 runs by default |

**Authentication**: All endpoints require `Depends(require_account_id)` → reads from `request.state.account_id` set by `AuthContextMiddleware`

**RLS Policy**:
```sql
CREATE POLICY schedules_rls ON schedules
  FOR ALL USING (account_id = current_setting('app.current_account_id')::uuid)
  WITH CHECK (account_id = current_setting('app.current_account_id')::uuid)
```

**Recipient Ownership Validation** (`validate_recipient_ownership()` in API):
- **At schedule creation**: Validates **all** recipients before storing
- **At schedule update**: Re-validates **all** recipients if `recipients` field updated
- **At runtime (worker)**: Re-validates again during resolution (handles deletions since creation)

**Role-Based Differences**:
- ❌ **No explicit role checks** in schedule API
- ✅ Implicitly enforced:
  - `REGULAR` agents can only add:
    - Their own contacts
    - Manual emails
  - `INDUSTRY_AFFILIATE` accounts can add:
    - Their own contacts
    - Sponsored agents (via sponsorship check)
    - Groups containing both

**Cadence Validation**:
```python
def validate_schedule_params(cadence, weekly_dow, monthly_dom):
    if cadence == "weekly" and weekly_dow is None:
        raise HTTPException(400, "weekly_dow (0-6) required for weekly cadence")
    if cadence == "monthly" and monthly_dom is None:
        raise HTTPException(400, "monthly_dom (1-28) required for monthly cadence")
```

**Timezone Handling**: ⚠️ **UTC ONLY**
- All `send_hour` and `send_minute` values are treated as **UTC**
- No per-schedule timezone support currently
- User-facing implications: Users must manually convert their desired local time to UTC

---

## 5. Frontend Wizard UX

### 5.1 Schedule Wizard Component

**File**: `packages/ui/src/components/schedules/schedule-wizard.tsx`  
**Also**: `apps/web/components/schedules/schedule-wizard.tsx`

**Steps**:

#### Step 1: Report Type Selection
- Options:
  - Market Snapshot
  - New Listings
  - Closed Sales
  - Inventory Analysis
  - Price Bands
  - New Listings Gallery
  - Featured Listings
- Stores: `report_type`

#### Step 2: Area/Filters
- **City** (text input)
- **ZIP Codes** (comma-separated or multi-select)
- **Lookback Days** (slider or number input, default 30)
- Stores: `city`, `zip_codes`, `lookback_days`

#### Step 3: Cadence/Timing
- **Cadence**: Weekly or Monthly (radio buttons)
- **If Weekly**: Day of week picker (Sun-Sat)
- **If Monthly**: Day of month picker (1-28)
- **Send Time**: Hour (0-23) and Minute (0-59) inputs
- **Timezone Note**: ⚠️ Currently assumes UTC, no timezone selector shown
- Stores: `cadence`, `weekly_dow`/`monthly_dom`, `send_hour`, `send_minute`

#### Step 4: Recipients
- **People Selector**: Multi-select from contacts + sponsored agents (for affiliates)
- **Groups Selector**: Multi-select from `contact_groups`
- **Manual Email**: Add button to input ad-hoc emails
- **Validation**: At least 1 recipient required
- **Display**: Shows preview list of selected people/groups/emails
- Stores: `recipients` as array of `RecipientInput` objects

#### Step 5: Review/Confirm
- **Summary Card**:
  - Report type
  - Area (city + ZIP codes)
  - Cadence (e.g., "Weekly on Monday at 9:00 AM UTC")
  - Recipients (count + names/emails)
- **Submit Button**: Creates schedule via `POST /v1/schedules`

**Validation Rules**:
- ✅ All required fields per step
- ✅ At least 1 recipient
- ✅ Cadence-specific fields (dow for weekly, dom for monthly)
- ❌ No duplicate schedule detection (user can create identical schedules)
- ❌ No plan limit enforcement in UI (handled server-side or not at all—see Section 7)

**Error Handling**:
- API validation errors shown in modal/toast
- If recipient ownership validation fails server-side, error returned to user

---

### 5.2 Schedule List / Management Screen

**File**: Likely `apps/web/app/app/schedules/page.tsx` (or similar)

**Display Columns**:
- Name
- Report Type
- Area (city + ZIP count)
- Cadence (e.g., "Weekly on Monday")
- Next Run (formatted datetime)
- Status (Active badge or Paused badge)

**Actions Per Row**:
- ✅ **Edit**: Opens wizard pre-filled with schedule data
- ✅ **Pause/Resume**: Toggles `active` field via `PATCH /v1/schedules/{id}`
- ✅ **Delete**: Confirms and calls `DELETE /v1/schedules/{id}`
- ❌ **Run Now / Send Once**: NOT IMPLEMENTED (no endpoint exists)

**Filters**:
- ✅ Active vs All (via `active_only` query param)
- ❌ No filter by report_type or cadence

**Known UX Gaps**:
1. ❌ **No "Run Now" action** to trigger immediate execution
2. ❌ **No "View Last Run" link** to see schedule_runs history (API exists, UI doesn't expose)
3. ⚠️ **Timezone confusion**: UI doesn't indicate times are UTC

---

## 6. Edge Cases & Limits

### 6.1 Plan Limits & Enforcement

**Plan Limits** (from `plans` table):
| Plan | `monthly_report_limit` | Enforcement Point |
|------|----------------------|------------------|
| `free` | 50 | ❓ NOT CLEAR |
| `solo` | 500 | ❓ NOT CLEAR |
| `affiliate` | 5000 | ❓ NOT CLEAR |

**Current Enforcement Status**:
- ❌ **Worker does NOT check `plan-usage` before generating scheduled reports**
- ❌ **Schedule creation API does NOT prevent creating schedules beyond plan limits**
- ✅ **Manual report generation** (via dashboard) may enforce limits via `/v1/account/plan-usage` check in frontend

**Implications**:
- ⚠️ A free account can create 100 weekly schedules (each sending 1 report/week = 400+ reports/month) and **no enforcement will stop them**
- ⚠️ Plan limits are **advisory only** for scheduled reports

**Known TODO**: Integrate `check_usage_limit()` function (exists in `apps/worker/src/worker/limit_checker.py`) into the `generate_report` task before report execution

---

### 6.2 Account Deactivation

**What happens when an account is deactivated**:
- ❌ **Schedules are NOT automatically paused/deleted**
- ❌ **Ticker continues to process schedules** for deactivated accounts
- ✅ **RLS should prevent** worker from accessing account data if `app.current_account_id` is properly set
- ⚠️ **Edge case**: If RLS is not set in worker context, deactivated accounts may still send reports

**Recommendation**: Add `accounts.is_active` check to ticker query or schedule execution

---

### 6.3 Repeated Failures

**What happens when a schedule repeatedly fails**:
- ❌ **No failure tracking** across runs
- ❌ **No automatic pause/disable** after N failures
- ✅ **Ticker keeps retrying** on every scheduled run (e.g., weekly)
- ⚠️ **User unaware**: No notification of failures unless they check schedule_runs API

**Current Behavior**:
- Failed report → `schedule_runs.status = 'failed'` + `error` text
- Next scheduled run → Ticker enqueues again
- If underlying issue persists (bad SimplyRETS config, bad area), **infinite failure loop**

**Recommendation**: Implement failure threshold (e.g., 3 consecutive failures → auto-pause + notify)

---

### 6.4 Email Suppressions & Bounces

**Unsubscribe Flow**:
- ✅ User clicks unsubscribe link in email → hits `/v1/unsubscribe` endpoint
- ✅ Adds entry to `email_suppressions` table
- ✅ `send_schedule_email()` filters suppressions before sending
- ✅ If all recipients are suppressed, email is not sent (but report still generates)

**Bounce Handling**:
- ❌ **NOT IMPLEMENTED** (no webhook from SendGrid/provider to mark bounces)
- ⚠️ Hard bounces are not automatically added to suppressions

---

### 6.5 Data Integrity Scenarios

| Scenario | Current Behavior | Ideal Behavior |
|----------|-----------------|---------------|
| Contact deleted while schedule active | Skipped at runtime, logs warning | ✅ Acceptable (graceful degradation) |
| Group deleted while referenced | Skipped at runtime, logs warning | ⚠️ Could notify user schedule needs update |
| Affiliate unsponsors agent in schedule | Skipped at runtime, logs warning | ✅ Acceptable (auto-removed from sends) |
| All recipients become invalid | Report generates, no emails sent | ⚠️ Should pause schedule + notify |
| Schedule created with 0 recipients | ❌ API validation prevents this | ✅ Correct |
| Schedule updated to 0 recipients | ❌ API validation prevents this | ✅ Correct |

---

## 7. Known Issues & Gaps

### 7.1 Critical Gaps
1. ❌ **No plan limit enforcement in worker** for scheduled reports
2. ❌ **No timezone support** (all times are UTC, confusing for users)
3. ❌ **No retry logic** for transient failures (SimplyRETS rate limits, network issues)
4. ❌ **No failure threshold auto-pause** (infinite failure loops possible)
5. ❌ **No "Run Now" action** in UI (testing schedules is cumbersome)

### 7.2 UX Gaps
1. ⚠️ **Timezone assumption not communicated** in wizard
2. ⚠️ **No schedule history view** in UI (schedule_runs data not exposed)
3. ⚠️ **No recipient preview at runtime** (don't know who got the report)
4. ⚠️ **No notification on failures** (users don't know schedule broke)

### 7.3 Performance Concerns
1. ⚠️ **Group resolution can be expensive** for large groups (N+1 queries for each member)
2. ⚠️ **No rate limiting in ticker** (if 100 schedules due at once, all enqueued immediately)
3. ⚠️ **No pagination in ticker query** (LIMIT 100, but what if more?)

### 7.4 Security/Data Gaps
1. ⚠️ **No deactivated account filter** in ticker
2. ⚠️ **Bounce handling not implemented** (email deliverability risk)
3. ⚠️ **No audit log of recipient changes** (who was sent what when)

---

## 8. What Works Well

✅ **Typed recipients** - Clean abstraction integrating with People system  
✅ **RLS enforcement** - Accounts can't see/edit each other's schedules  
✅ **Graceful recipient resolution** - Missing contacts/agents don't crash reports  
✅ **Audit trail** - `schedule_runs` and `email_log` provide clear execution history  
✅ **Ownership validation** - API prevents adding recipients user doesn't own  
✅ **Deduplicated emails** - No duplicate sends if contact in multiple groups  
✅ **Unsubscribe support** - Users can opt out, system respects suppressions  

---

## 9. Summary: Current State

**The schedule system is architecturally sound but operationally immature.**

**Core Mechanics Work**:
- ✅ Schedules are created, stored, and triggered correctly
- ✅ Recipients are resolved dynamically from People system
- ✅ Reports generate and send via worker pipeline
- ✅ Audit logs track execution history

**Production Readiness Concerns**:
- ⚠️ **No limit enforcement** - Free users can abuse system
- ⚠️ **No timezone support** - Confusing UX, wrong send times for users
- ⚠️ **No failure recovery** - Transient errors cause permanent missed sends
- ⚠️ **No user feedback** - Failures are silent, success is invisible
- ⚠️ **No operational safeguards** - Deactivated accounts still send, no auto-pause

**Recommendation**: 
Before adding new schedule features (e.g., more report types), address:
1. Plan limit enforcement in worker
2. Timezone support (even if just "assume PT" with UI label)
3. Retry logic for transient failures
4. Failure threshold auto-pause + user notification

---

**End of Audit**

Next step: Create `SCHEDULE_QA_CHECKLIST.md` with concrete test scenarios based on these findings.


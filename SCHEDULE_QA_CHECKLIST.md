# SCHEDULE SYSTEM - QA CHECKLIST

**Purpose**: Manual test scenarios to verify schedule system behavior  
**Based on**: `SCHEDULE_AUDIT.md` findings  
**Date**: Nov 24, 2025

---

## Test Environment Setup

**Prerequisites**:
- Access to staging database
- Access to Render logs (ticker + worker)
- Test accounts:
  - 1x REGULAR agent account (free plan)
  - 1x INDUSTRY_AFFILIATE account (affiliate plan)
  - 2x REGULAR "sponsored" accounts linked to affiliate
- Test contacts:
  - At least 3 contacts for agent
  - At least 1 group with 2+ members for affiliate
- Ability to trigger ticker manually or wait for 60-second tick

**Tools**:
- Database query tool (Render MCP or psql)
- Browser for UI testing
- API testing tool (curl/Postman) for direct API verification

---

## TEST 1: Basic Schedule Creation & Execution (REGULAR Agent)

### Goal
Verify a regular agent can create a weekly schedule with contacts and it runs successfully.

### Steps
1. **Create Schedule (UI)**:
   - Log in as REGULAR agent
   - Navigate to `/app/schedules`
   - Click "New Schedule" / "Create Schedule"
   - Fill wizard:
     - Report Type: **Market Snapshot**
     - City: **La Verne**
     - ZIP Codes: *(leave empty or add one)*
     - Lookback Days: **30**
     - Cadence: **Weekly**
     - Day: **Monday** (or tomorrow's day for quick test)
     - Time: **09:00** (or current UTC hour + 1 for quick test)
     - Recipients: Select **2-3 contacts** (no groups, no sponsored agents)
   - Review & Submit

2. **Verify Schedule Created (DB)**:
   ```sql
   SELECT id::text, name, report_type, cadence, weekly_dow, 
          send_hour, send_minute, active, next_run_at, recipients
   FROM schedules
   WHERE account_id = '<agent_account_id>'
   ORDER BY created_at DESC LIMIT 1;
   ```
   - ✅ `active = true`
   - ✅ `next_run_at` is set to future datetime (matches cadence)
   - ✅ `recipients` is TEXT[] array with JSON-encoded contact objects

3. **Manually Trigger (for quick test)**:
   - Update `next_run_at` to now:
     ```sql
     UPDATE schedules SET next_run_at = NOW() - INTERVAL '1 minute'
     WHERE id = '<schedule_id>';
     ```
   - Wait for ticker tick (up to 60 seconds)

4. **Verify Execution (DB)**:
   ```sql
   -- Check schedule_runs
   SELECT id::text, status, error, created_at
   FROM schedule_runs
   WHERE schedule_id = '<schedule_id>'
   ORDER BY created_at DESC LIMIT 1;
   ```
   - ✅ Record created with `status = 'queued'` then `'completed'` (or check report_generations)
   
   ```sql
   -- Check report_generations
   SELECT id::text, status, error, finished_at
   FROM report_generations
   WHERE account_id = '<agent_account_id>'
   ORDER BY created_at DESC LIMIT 1;
   ```
   - ✅ `status = 'completed'` (or 'processing' if still running)
   - ❌ `status = 'failed'` → check `error` column

5. **Verify Emails Sent (DB)**:
   ```sql
   SELECT id::text, to_emails, response_code, error
   FROM email_log
   WHERE schedule_id = '<schedule_id>'
   ORDER BY created_at DESC LIMIT 1;
   ```
   - ✅ `to_emails` contains the 2-3 contact emails
   - ✅ `response_code = 200` (or SendGrid success code)
   - ✅ No `error`

6. **Verify Next Run Updated (DB)**:
   ```sql
   SELECT last_run_at, next_run_at FROM schedules WHERE id = '<schedule_id>';
   ```
   - ✅ `last_run_at` updated to execution time
   - ✅ `next_run_at` updated to next cadence occurrence (e.g., next Monday at 9 AM)

### Expected Result
✅ **PASS**: Schedule created, executed, emails sent, next run computed

### Common Failures
- ❌ `next_run_at` still NULL after execution → Ticker didn't run or crashed
- ❌ `report_generations.status = 'failed'` → Check error (likely SimplyRETS issue or bad city)
- ❌ No `email_log` entry → Email sending failed or suppressed

---

## TEST 2: Schedule with Groups (AFFILIATE)

### Goal
Verify affiliate can create schedule with groups containing contacts + sponsored agents.

### Steps
1. **Setup Data (if not exists)**:
   - Create a group with 2+ members:
     - 1x contact
     - 1x sponsored agent
   - Verify sponsorship in DB:
     ```sql
     SELECT id::text, name, sponsor_account_id::text
     FROM accounts
     WHERE sponsor_account_id = '<affiliate_account_id>';
     ```

2. **Create Schedule (UI)**:
   - Log in as AFFILIATE
   - Create schedule:
     - Report Type: **New Listings**
     - City: **La Verne**
     - Cadence: **Weekly**, Day: **Tuesday**, Time: **10:00**
     - Recipients: **Select 1 group** (not individual contacts)

3. **Verify Recipients Stored (DB)**:
   ```sql
   SELECT recipients FROM schedules WHERE id = '<schedule_id>';
   ```
   - ✅ Contains JSON like `{"type":"group","id":"<group_id>"}`

4. **Trigger Execution** (manual or wait):
   ```sql
   UPDATE schedules SET next_run_at = NOW() - INTERVAL '1 minute'
   WHERE id = '<schedule_id>';
   ```

5. **Check Worker Logs (Render)**:
   - Look for recipient resolution logs:
     ```
     Resolved recipients: ['contact@example.com', 'sponsoredagent@example.com']
     ```
   - ✅ No warnings like "Group not found" or "Sponsored agent not sponsored"

6. **Verify Emails (DB)**:
   ```sql
   SELECT to_emails FROM email_log WHERE schedule_id = '<schedule_id>';
   ```
   - ✅ Contains **both** contact email AND sponsored agent's user email
   - ✅ No duplicates (even if member is in multiple contexts)

### Expected Result
✅ **PASS**: Group resolved to both contacts and sponsored agents, all received emails

### Common Failures
- ❌ Only contact email sent, not sponsored agent → Sponsorship check failed or no user for agent
- ❌ "Group not found" in logs → Group was deleted or doesn't belong to affiliate
- ❌ Duplicate emails → Deduplication not working

---

## TEST 3: Recipient Edge Cases (Deletions & Unsponsor)

### Goal
Verify schedule gracefully handles deleted contacts, unsponsored agents, deleted groups.

### Test 3A: Deleted Contact

1. **Create schedule with 3 contacts** (Test 1 setup)
2. **Delete 1 contact** (via `/app/people` or API):
   ```sql
   DELETE FROM contacts WHERE id = '<contact_id>';
   ```
3. **Trigger schedule execution**
4. **Check Logs (Render)**:
   - ✅ Warning: `"⚠️ Contact <contact_id> not found for account <account_id>"`
5. **Check email_log**:
   - ✅ `to_emails` contains only the 2 remaining contacts
   - ✅ Report still sent successfully

### Test 3B: Unsponsored Agent

1. **Create affiliate schedule with sponsored agent recipient**
2. **Unsponsor the agent** (via `/app/people` → Edit → Toggle off sponsorship):
   ```sql
   UPDATE accounts SET sponsor_account_id = NULL WHERE id = '<agent_id>';
   ```
3. **Trigger schedule execution**
4. **Check Logs**:
   - ✅ Warning: `"⚠️ Sponsored agent <agent_id> not sponsored by <affiliate_id>"`
5. **Check email_log**:
   - ✅ Agent email NOT in `to_emails`
   - ✅ Other recipients still received

### Test 3C: Deleted Group

1. **Create schedule with group recipient**
2. **Delete the group**:
   ```sql
   DELETE FROM contact_groups WHERE id = '<group_id>';
   ```
3. **Trigger schedule execution**
4. **Check Logs**:
   - ✅ Warning: `"⚠️ Group <group_id> not found for account <account_id>"`
5. **Check email_log**:
   - ✅ If group was only recipient: No email sent (or empty `to_emails`)
   - ✅ If other recipients exist: They still received

### Test 3D: All Recipients Invalid

1. **Create schedule with 2 contacts**
2. **Delete both contacts**
3. **Trigger execution**
4. **Check behavior**:
   - ✅ `report_generations.status = 'completed'` (report still generated)
   - ✅ `email_log` either:
     - Missing (no email sent), OR
     - `to_emails = []` and `response_code = NULL`
   - ⚠️ **Known Issue**: Schedule does not auto-pause (will retry next run with same result)

### Expected Result
✅ **PASS**: Missing recipients skipped, schedule continues with remaining valid recipients

---

## TEST 4: Editing Schedule & Recipient Update

### Goal
Verify editing a schedule updates recipients and resets `next_run_at`.

### Steps
1. **Create schedule with 2 contacts**
2. **Note `next_run_at` value**:
   ```sql
   SELECT next_run_at FROM schedules WHERE id = '<schedule_id>';
   ```
3. **Edit schedule (UI)**:
   - Open schedule editor
   - Add 1 more contact to recipients (total 3)
   - Save
4. **Verify Changes (DB)**:
   ```sql
   SELECT recipients, next_run_at FROM schedules WHERE id = '<schedule_id>';
   ```
   - ✅ `recipients` now has 3 contact entries
   - ✅ `next_run_at = NULL` (reset by API)
5. **Trigger ticker** (wait or manually):
   - ✅ Ticker recomputes `next_run_at` on next tick
6. **Verify next execution uses new recipients**:
   - Trigger execution
   - Check `email_log.to_emails` contains all 3 contacts

### Expected Result
✅ **PASS**: Recipient changes reflected, `next_run_at` recomputed

---

## TEST 5: Pause/Resume & Delete

### Goal
Verify schedule pause, resume, and deletion behavior.

### Test 5A: Pause Schedule

1. **Create active schedule**
2. **Pause via UI** (or API):
   ```sql
   UPDATE schedules SET active = false WHERE id = '<schedule_id>';
   ```
3. **Manually set `next_run_at` to past**:
   ```sql
   UPDATE schedules SET next_run_at = NOW() - INTERVAL '1 minute'
   WHERE id = '<schedule_id>';
   ```
4. **Wait for ticker tick**
5. **Verify (DB)**:
   - ✅ No new `schedule_runs` entry created
   - ✅ Schedule not enqueued (check Render logs: "No due schedules found" or count doesn't include this one)

### Test 5B: Resume Schedule

1. **Resume paused schedule**:
   ```sql
   UPDATE schedules SET active = true WHERE id = '<schedule_id>';
   ```
2. **Set `next_run_at` to past** (if not already)
3. **Wait for ticker**
4. **Verify**:
   - ✅ Schedule executed
   - ✅ New `schedule_runs` entry created

### Test 5C: Delete Schedule

1. **Delete schedule via UI** (or API):
   ```sql
   DELETE FROM schedules WHERE id = '<schedule_id>';
   ```
2. **Verify cascade**:
   ```sql
   SELECT COUNT(*) FROM schedule_runs WHERE schedule_id = '<schedule_id>';
   ```
   - ✅ Returns 0 (all runs deleted via `ON DELETE CASCADE`)
3. **Verify no future execution**:
   - Schedule no longer appears in ticker queries

### Expected Result
✅ **PASS**: Pause prevents execution, resume re-enables, delete removes all traces

---

## TEST 6: Cadence & Timing (Weekly vs Monthly)

### Goal
Verify weekly and monthly cadence compute correct `next_run_at`.

### Test 6A: Weekly Cadence

1. **Create schedule**:
   - Cadence: **Weekly**
   - Day: **Wednesday**
   - Time: **14:00** (2 PM UTC)
2. **Check initial `next_run_at` (DB)**:
   - ✅ Should be next Wednesday at 14:00:00 UTC
   - ✅ If created on Wednesday before 2 PM: next_run_at is today at 2 PM
   - ✅ If created on Wednesday after 2 PM: next_run_at is next Wednesday at 2 PM
3. **After execution, check updated `next_run_at`**:
   - ✅ Advances by 7 days (next Wednesday at 14:00)

### Test 6B: Monthly Cadence

1. **Create schedule**:
   - Cadence: **Monthly**
   - Day: **15** (15th of month)
   - Time: **09:00**
2. **Check initial `next_run_at`**:
   - ✅ Should be 15th of current month at 09:00 UTC (if before current datetime)
   - ✅ OR 15th of next month at 09:00 UTC (if current date > 15 or on 15th after 9 AM)
3. **After execution, check updated `next_run_at`**:
   - ✅ Advances to 15th of next month

### Test 6C: Edge Case - Day 29-31

1. **Attempt to create schedule with day 29**:
   - ⚠️ **Expected**: API validation blocks (only 1-28 allowed per schema CHECK constraint)
   - ❌ If allowed: Ticker logic caps at day 28 (see audit Section 2.1)

### Expected Result
✅ **PASS**: Cadence logic correctly computes next occurrence based on dow/dom

---

## TEST 7: Plan Limits (Critical Gap Test)

### Goal
Verify whether plan limits are enforced for scheduled reports.

### Steps
1. **Check current usage for test account**:
   ```sql
   SELECT COUNT(*) as report_count
   FROM report_generations
   WHERE account_id = '<agent_account_id>'
     AND DATE_TRUNC('month', created_at) = DATE_TRUNC('month', NOW());
   ```
2. **Check plan limit**:
   ```sql
   SELECT plan_slug, monthly_report_limit
   FROM accounts a
   JOIN plans p ON a.plan_slug = p.plan_slug
   WHERE a.id = '<agent_account_id>';
   ```
   - e.g., `free` = 50, `solo` = 500
3. **Manually set usage to near/over limit**:
   - Option A: Create fake `report_generations` entries to inflate count
   - Option B: Lower `monthly_report_limit` temporarily:
     ```sql
     UPDATE accounts SET monthly_report_limit_override = 2 WHERE id = '<agent_account_id>';
     ```
4. **Trigger schedule execution**
5. **Check behavior**:
   - ❌ **EXPECTED (CURRENT)**: Report generates anyway, no limit check
   - ✅ **IDEAL**: Report blocked, `schedule_runs.status = 'failed'`, `error = 'Monthly limit exceeded'`

### Expected Result (Current System)
⚠️ **KNOWN ISSUE**: Report generates even if over limit (see Audit Section 6.1)

### Expected Result (After Fix)
✅ **PASS**: Report blocked, user notified, schedule paused or skipped

---

## TEST 8: Failure Handling & Retries

### Goal
Verify what happens when report generation fails.

### Test 8A: Transient Failure (SimplyRETS Down)

1. **Create schedule with valid city**
2. **Simulate SimplyRETS failure**:
   - Option A: Remove/break `SIMPLYRETS_API_USERNAME` env var temporarily
   - Option B: Use a city that returns 0 results (may not fail, just empty report)
3. **Trigger execution**
4. **Check status**:
   ```sql
   SELECT status, error FROM report_generations WHERE id = '<report_gen_id>';
   ```
   - ❌ `status = 'failed'`, `error` contains exception
5. **Check schedule state**:
   ```sql
   SELECT next_run_at, last_run_at FROM schedules WHERE id = '<schedule_id>';
   ```
   - ✅ `last_run_at` updated (attempt was made)
   - ✅ `next_run_at` updated to next cadence occurrence
6. **Wait for next scheduled run** (or manually trigger):
   - ⚠️ **EXPECTED**: Report attempts again (no automatic pause)
   - ❌ If issue persists: Infinite failure loop

### Test 8B: Permanent Failure (Bad City Name)

1. **Create schedule with nonsense city**: `"XYZ123InvalidCity"`
2. **Trigger 3 consecutive executions** (manually advance `next_run_at` each time)
3. **Check schedule state after 3 failures**:
   - ⚠️ **EXPECTED (CURRENT)**: Schedule still active, will retry on next run
   - ✅ **IDEAL**: Schedule auto-paused after 3 failures, user notified

### Expected Result (Current System)
⚠️ **KNOWN ISSUE**: No retry logic, no failure threshold auto-pause (see Audit Section 6.3)

---

## TEST 9: Multiple Schedules & Concurrency

### Goal
Verify ticker handles multiple due schedules gracefully.

### Steps
1. **Create 5 schedules** for same account with different report types
2. **Set all `next_run_at` to past**:
   ```sql
   UPDATE schedules SET next_run_at = NOW() - INTERVAL '1 minute'
   WHERE account_id = '<agent_account_id>';
   ```
3. **Wait for ticker tick**
4. **Check Render logs**:
   - ✅ Ticker logs `"Found 5 due schedule(s)"`
   - ✅ Each schedule enqueued separately
5. **Check DB**:
   ```sql
   SELECT COUNT(*) FROM schedule_runs
   WHERE schedule_id IN (SELECT id FROM schedules WHERE account_id = '<agent_account_id>')
     AND created_at > NOW() - INTERVAL '5 minutes';
   ```
   - ✅ Returns 5 (one run per schedule)
6. **Verify no race conditions**:
   - ✅ All 5 schedules have updated `last_run_at` and `next_run_at`
   - ✅ No duplicate schedule_runs entries

### Expected Result
✅ **PASS**: All due schedules processed in single tick, no duplicates

---

## TEST 10: Timezone Confusion (User Experience)

### Goal
Document the timezone UX issue.

### Steps
1. **User creates schedule**:
   - Desired: "Send every Monday at 9 AM Pacific Time"
   - Input: `send_hour = 9`, `send_minute = 0`
2. **Check `next_run_at` in DB**:
   ```sql
   SELECT next_run_at FROM schedules WHERE id = '<schedule_id>';
   ```
   - ❌ Shows Monday at 09:00 **UTC** (1 AM PT in winter, 2 AM PT in summer)
3. **User receives email at wrong time**:
   - Expected: 9 AM PT
   - Actual: ~1-2 AM PT

### Expected Result (Current System)
⚠️ **KNOWN UX ISSUE**: All times are UTC, no timezone selector, users confused (see Audit Section 5.1)

### Workaround (Manual)
User must manually convert desired PT time to UTC:
- 9 AM PT (winter) = 5 PM UTC (previous day) → Set `send_hour = 17`, `weekly_dow = 0` (Sunday)
- 9 AM PT (summer) = 4 PM UTC (previous day) → Set `send_hour = 16`, `weekly_dow = 0` (Sunday)

---

## Summary: QA Completion Criteria

Mark each test ✅ **PASS**, ⚠️ **PASS (with known issue)**, or ❌ **FAIL**.

| Test | Status | Notes |
|------|--------|-------|
| 1. Basic Schedule (Agent) | | |
| 2. Schedule with Groups (Affiliate) | | |
| 3. Recipient Edge Cases | | |
| 4. Editing Schedule | | |
| 5. Pause/Resume/Delete | | |
| 6. Cadence & Timing | | |
| 7. Plan Limits (Critical Gap) | | **Expected to fail** (not enforced) |
| 8. Failure Handling | | **Expected to show no retries** |
| 9. Multiple Schedules | | |
| 10. Timezone UX | | **Expected to show confusion** |

---

## Post-QA Actions

**If Tests 1-6, 9 PASS**:
- ✅ Core schedule system is functional
- ✅ Proceed with documenting known issues (Tests 7, 8, 10)

**If any of Tests 1-6, 9 FAIL**:
- ❌ Core functionality broken
- ❌ Fix failures before considering system "stable"

**Required Fixes (before "Schedules 100%")**:
1. **Test 7 failure**: Implement plan limit enforcement in worker
2. **Test 8 failure**: Implement retry logic + failure threshold auto-pause
3. **Test 10 failure**: Add timezone support or at least prominent UTC label in UI

---

**End of QA Checklist**

Use this checklist to verify schedule system behavior and identify gaps before adding new features.


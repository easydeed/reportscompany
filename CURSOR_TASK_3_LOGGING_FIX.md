# Task 3: Fix Email Logging SQL Error

**Estimated Time:** 15 minutes  
**Priority:** MEDIUM  
**Dependencies:** None

---

## 🎯 Goal

Fix SQL syntax error that appears in worker logs after email sends:
```
⚠️ Email send failed: syntax error at or near "ORDER"
LINE 9: ORDER BY created_at DESC
```

This is a **non-critical logging bug** - emails still send successfully, but logging fails.

---

## 🔍 Root Cause

There's a SQL error in email logging code. The error happens AFTER the email is sent, so it doesn't affect delivery.

**Key Principle:** Logging failures must never block core functionality.

---

## 📂 Files to Investigate and Fix

### 1. Find the Faulty SQL Query

**Search for:**
```bash
grep -r "ORDER BY created_at" apps/worker/src/worker/
```

**Likely locations:**
- `apps/worker/src/worker/email/send.py`
- `apps/worker/src/worker/tasks.py`
- Any helper file that logs email status

**Common SQL errors:**
1. Missing column in SELECT when using ORDER BY
2. ORDER BY in wrong position (before WHERE, etc.)
3. Incorrect string concatenation in dynamic SQL

---

### 2. Fix Pattern: Defensive Logging

**Bad pattern (causes failure to block work):**
```python
# Send email
response = sendgrid.send(message)

# Log result - if this fails, exception bubbles up
cur.execute("INSERT INTO email_log (...) VALUES (...)")
conn.commit()
```

**Good pattern (logging never blocks):**
```python
# Send email
response = sendgrid.send(message)

# Log result - wrapped in try/except
try:
    cur.execute("INSERT INTO email_log (...) VALUES (...)")
    conn.commit()
except Exception as log_error:
    logger.warning(f"Failed to log email send: {log_error}")
    # Continue - don't let logging failure affect task
```

---

### 3. Common SQL Fixes

**Example Issue 1: Missing FROM before ORDER**
```sql
-- BAD
INSERT INTO email_log (...) 
VALUES (...)
ORDER BY created_at DESC;  -- ❌ Invalid in INSERT

-- GOOD
INSERT INTO email_log (...) 
VALUES (...);  -- ✅ No ORDER BY in INSERT
```

**Example Issue 2: Query in wrong context**
```sql
-- BAD
UPDATE schedule_runs
SET status = 'completed'
WHERE schedule_id = %s
ORDER BY created_at DESC;  -- ❌ Need subquery or LIMIT

-- GOOD
UPDATE schedule_runs
SET status = 'completed'
WHERE id = (
    SELECT id FROM schedule_runs
    WHERE schedule_id = %s
    ORDER BY created_at DESC
    LIMIT 1
);
```

---

## 📂 Files to Modify

### 1. `apps/worker/src/worker/tasks.py`

**Find email logging section** (around line 265-280):

**Add defensive try/except:**

```python
# After send_schedule_email call
status_code, response_text = send_schedule_email(...)

# Defensive email logging
try:
    # Determine status
    if status_code == 202:
        email_status = 'sent'
    elif status_code == 200 and 'suppressed' in response_text.lower():
        email_status = 'suppressed'
    else:
        email_status = 'failed'
    
    # Log email attempt
    cur.execute("""
        INSERT INTO email_log (
            account_id, schedule_id, report_id, provider,
            to_emails, subject, response_code, status, error
        )
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
    """, (
        account_id, schedule_id, report_gen_id, 'sendgrid',
        recipients, subject, status_code, email_status,
        None if status_code in (200, 202) else response_text
    ))
    
except Exception as log_error:
    logger.warning(f"Failed to log email send (non-critical): {log_error}")
    # Don't raise - logging failure shouldn't affect task success

# Continue with schedule_runs update...
```

**Add defensive logging for schedule_runs update:**

```python
try:
    # Update schedule run status
    run_status = 'completed' if status_code in (200, 202) else 'failed_email'
    
    cur.execute("""
        UPDATE schedule_runs
        SET status = %s, finished_at = NOW()
        WHERE schedule_id = %s
          AND id = (
              SELECT id FROM schedule_runs
              WHERE schedule_id = %s
              ORDER BY created_at DESC
              LIMIT 1
          )
    """, (run_status, schedule_id, schedule_id))
    
except Exception as update_error:
    logger.warning(f"Failed to update schedule_run status (non-critical): {update_error}")
```

---

### 2. `check_schedule_status.py` (Monitoring Script)

**If this script has SQL errors, fix them:**

**Find any queries with ORDER BY and verify syntax:**

```python
# GOOD - Valid SELECT with ORDER BY
cur.execute("""
    SELECT id, status, started_at, finished_at
    FROM schedule_runs
    WHERE schedule_id = %s
    ORDER BY created_at DESC
    LIMIT 5
""", (schedule_id,))

# BAD - If you find this pattern, fix it
cur.execute("""
    SELECT * FROM email_log
    WHERE account_id = %s
    ORDER BY created_at DESC  -- Make sure this is AFTER WHERE
""", (account_id,))
```

---

## ✅ Acceptance Criteria

### Code Quality
- [ ] All email logging wrapped in try/except
- [ ] All schedule_runs updates wrapped in try/except
- [ ] Logging failures logged as warnings, not errors
- [ ] Core task success not dependent on logging success

### SQL Syntax
- [ ] All ORDER BY clauses in correct position (after WHERE, before LIMIT)
- [ ] No ORDER BY in INSERT statements
- [ ] All queries properly parameterized (no string concatenation)

### Testing
- [ ] Run `python check_schedule_status.py` - no SQL errors
- [ ] Trigger a schedule - check worker logs for clean execution
- [ ] Artificially break email_log table - verify task still succeeds

---

## 🧪 Testing Instructions

### Test 1: Verify Monitoring Script
```bash
python check_schedule_status.py
```
- Expected: No SQL errors in output
- Should show schedule runs, email log, report generations

### Test 2: Verify Worker Logs Clean
```bash
# Trigger a schedule
# Check Render worker logs
# Look for: No "syntax error at or near ORDER"
```

### Test 3: Test Logging Failure Handling (Optional)
```sql
-- Temporarily break email_log table
ALTER TABLE email_log DROP COLUMN created_at;

-- Trigger schedule
-- Expected: Email still sends, warning logged, task succeeds

-- Restore table
ALTER TABLE email_log ADD COLUMN created_at TIMESTAMPTZ DEFAULT NOW();
```

---

## 🚨 Common Pitfalls

1. **Fixing SQL but not adding try/except**
   - Even correct SQL can fail (network, deadlock, etc.)
   - Always wrap logging in defensive try/except

2. **Using wrong isolation level**
   - If using transactions, ensure logging doesn't lock other operations

3. **Logging too much detail**
   - Keep error logs concise
   - Don't log full stack traces for expected errors

4. **Not testing the monitoring script**
   - The script itself might have the SQL error
   - Always run it after changes

---

## 📝 Commit Message

```
fix(worker): stabilize email logging with defensive error handling

- Wrap email_log INSERT in try/except
- Wrap schedule_runs UPDATE in try/except  
- Fix any SQL ORDER BY syntax errors
- Log failures as warnings, not exceptions
- Ensure logging failures never block core tasks

Issue: SQL syntax error in email logging
Impact: Non-critical - emails still sent successfully
Fix: Defensive logging + SQL syntax correction
```

---

**After completing this task, run monitoring script and trigger a test schedule to verify clean logs.**


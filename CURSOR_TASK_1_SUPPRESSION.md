# Task 1: Implement Suppression Filtering

**Estimated Time:** 30 minutes  
**Priority:** HIGH  
**Dependencies:** None

---

## 🎯 Goal

Implement email suppression filtering so unsubscribed users don't receive scheduled report emails.

---

## 📋 Requirements

### Current State
- `email_suppressions` table exists in Postgres
- Unsubscribe API endpoint exists (`/v1/email/unsubscribe`)
- Emails are sent without checking suppressions

### Target State
- Before sending emails, check `email_suppressions` table
- Filter out suppressed recipients
- Log suppression actions
- Handle "all recipients suppressed" case gracefully

---

## 📂 Files to Modify

### 1. `apps/worker/src/worker/email/send.py`

**Current signature:**
```python
def send_schedule_email(
    account_id: str,
    recipients: list[str],
    payload: dict,
    account_name: str | None = None,
) -> tuple[int, str]:
```

**Required changes:**

**Add parameter:**
```python
def send_schedule_email(
    account_id: str,
    recipients: list[str],
    payload: dict,
    account_name: str | None = None,
    db_conn=None,  # NEW: Pass active DB connection
) -> tuple[int, str]:
```

**Add suppression filtering logic at the start of the function:**

```python
def send_schedule_email(
    account_id: str,
    recipients: list[str],
    payload: dict,
    account_name: str | None = None,
    db_conn=None,
) -> tuple[int, str]:
    """
    Send scheduled report email via SendGrid.
    
    Filters out suppressed recipients before sending.
    """
    import logging
    logger = logging.getLogger(__name__)
    
    filtered_recipients = recipients[:]
    
    # If db_conn provided, check suppressions
    if db_conn is not None:
        try:
            with db_conn.cursor() as cur:
                # Query suppressed emails for this account
                cur.execute("""
                    SELECT email
                    FROM email_suppressions
                    WHERE account_id = %s
                      AND email = ANY(%s)
                """, (account_id, recipients))
                
                suppressed = [row[0] for row in cur.fetchall()]
                
                if suppressed:
                    logger.info(f"Suppressed recipients: {suppressed}")
                    filtered_recipients = [r for r in recipients if r not in suppressed]
                
                if not filtered_recipients:
                    logger.info(f"All {len(recipients)} recipient(s) suppressed, skipping email send")
                    return (200, "All recipients suppressed")
                    
        except Exception as e:
            logger.warning(f"Error checking suppressions: {e}, proceeding with all recipients")
            # On error, don't block email - proceed with original list
            filtered_recipients = recipients
    
    # Continue with existing SendGrid logic using filtered_recipients
    logger.info(f"Sending schedule email to {len(filtered_recipients)} recipient(s)")
    logger.info(f"Sending email to {len(filtered_recipients)} recipient(s): {filtered_recipients}")
    
    # ... rest of existing SendGrid code ...
    # IMPORTANT: Use filtered_recipients instead of recipients in SendGrid call
```

**Critical:** Ensure SendGrid API call uses `filtered_recipients`, not `recipients`.

---

### 2. `apps/worker/src/worker/tasks.py`

**Find the section that sends schedule emails** (around line 220-280):

**Current code pattern:**
```python
status_code, response_text = send_schedule_email(
    account_id=account_id,
    recipients=recipients,
    payload=email_payload,
    account_name=account_name,
)
```

**Update to:**
```python
# Pass DB connection for suppression checking
status_code, response_text = send_schedule_email(
    account_id=account_id,
    recipients=recipients,
    payload=email_payload,
    account_name=account_name,
    db_conn=conn,  # NEW: Pass active connection
)
```

**Update email logging** (around line 265-275):

**Current pattern:**
```python
cur.execute("""
    INSERT INTO email_log (account_id, schedule_id, report_id, provider, to_emails, subject, response_code, error)
    VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
""", (...))
```

**Add status column handling:**
```python
# Determine status based on response
if status_code == 202:
    email_status = 'sent'
elif status_code == 200 and 'suppressed' in response_text.lower():
    email_status = 'suppressed'
else:
    email_status = 'failed'

cur.execute("""
    INSERT INTO email_log (
        account_id, schedule_id, report_id, provider,
        to_emails, subject, response_code, status, error
    )
    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
""", (
    account_id, schedule_id, report_gen_id, 'sendgrid',
    filtered_recipients or recipients, subject,
    status_code, email_status,
    None if status_code in (200, 202) else response_text
))
```

**Update schedule_runs status** (after email logging):

```python
# Update schedule run status
run_status = 'completed' if status_code in (200, 202) else 'failed_email'

cur.execute("""
    UPDATE schedule_runs
    SET status = %s, finished_at = NOW()
    WHERE schedule_id = %s
    ORDER BY created_at DESC
    LIMIT 1
""", (run_status, schedule_id))
```

---

## ✅ Acceptance Criteria

### Code Quality
- [ ] `send_schedule_email` accepts optional `db_conn` parameter
- [ ] Suppression check queries `email_suppressions` table correctly
- [ ] Filtered recipients list used in SendGrid API call
- [ ] Logging shows which recipients were suppressed
- [ ] Graceful handling if suppression check fails (send anyway)
- [ ] "All recipients suppressed" returns 200 without calling SendGrid

### Database
- [ ] `email_log` includes `status` column (`sent`, `suppressed`, `failed`)
- [ ] `schedule_runs` updated with correct status after email attempt

### Behavior
- [ ] If all recipients suppressed: no SendGrid API call, status = 200
- [ ] If some suppressed: only unsuppressed get email
- [ ] If suppression check errors: all recipients get email (fail-open)

---

## 🧪 Testing Instructions

### Local Test (After Implementation)

1. **Insert suppression:**
```sql
INSERT INTO email_suppressions (account_id, email, reason)
VALUES ('912014c3-6deb-4b40-a28d-489ef3923a3a', 'gerardoh@gmail.com', 'manual_test')
ON CONFLICT DO NOTHING;
```

2. **Trigger schedule:**
```sql
UPDATE schedules
SET next_run_at = NOW() - INTERVAL '1 minute'
WHERE id = '48d923da-be17-4d3d-b413-5bf1bc16a504';
```

3. **Check worker logs:**
- Should see: "Suppressed recipients: ['gerardoh@gmail.com']"
- Should see: "All recipients suppressed, skipping email send"

4. **Check email_log:**
```sql
SELECT status, response_code, to_emails, error
FROM email_log
ORDER BY created_at DESC
LIMIT 1;
```
- Expected: `status='suppressed'`, `response_code=200`

5. **Check inbox:**
- Expected: NO new email

---

## 🚨 Common Pitfalls

1. **Using `recipients` instead of `filtered_recipients` in SendGrid call**
   - This would bypass the entire suppression system

2. **Not handling `db_conn=None` case**
   - If connection not passed, should proceed normally (backwards compat)

3. **Suppression check failure blocks emails**
   - Should be fail-open: if check errors, send anyway

4. **Wrong account_id in suppression query**
   - Must use the schedule's account_id, not a hardcoded value

---

## 📝 Commit Message

```
feat(worker): implement email suppression filtering

- Add db_conn parameter to send_schedule_email()
- Query email_suppressions before sending
- Filter out suppressed recipients
- Log suppression actions
- Handle "all suppressed" case gracefully
- Update email_log with status column
- Update schedule_runs with correct completion status

Fixes Phase 27A suppression requirement
```

---

**After completing this task, run local tests above before moving to Task 2.**


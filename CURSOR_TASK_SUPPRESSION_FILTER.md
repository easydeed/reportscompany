# Cursor Task: Add Email Suppression Filtering

## Context
Phase 27A requires email suppression filtering to respect CAN-SPAM unsubscribe requests. Currently, `send_schedule_email()` does not check the `email_suppressions` table.

## Task
Add suppression filtering to the email sending flow in the worker.

---

## File 1: `apps/worker/src/worker/email/send.py`

**Modify the `send_schedule_email()` function signature and implementation:**

### Changes Needed:

1. **Add optional `db_conn` parameter** to accept database connection
2. **Query `email_suppressions` table** before sending
3. **Filter out suppressed emails** from recipients list
4. **Early return** if all recipients are suppressed

### Updated Function:

```python
def send_schedule_email(
    account_id: str,
    recipients: List[str],
    payload: Dict,
    account_name: Optional[str] = None,
    db_conn=None,  # ADD THIS PARAMETER
) -> Tuple[int, str]:
    """
    Send a scheduled report notification email to recipients.
    
    Args:
        account_id: Account UUID
        recipients: List of recipient email addresses
        payload: Report data including metrics and PDF URL
        account_name: Account name for personalization (optional)
        db_conn: Database connection for suppression checking (optional)
    
    Returns:
        Tuple of (status_code, response_text)
    """
    if not recipients:
        logger.warning("No recipients provided for schedule email")
        return (400, "No recipients")
    
    # NEW: Filter suppressions if DB connection provided
    if db_conn:
        try:
            with db_conn.cursor() as cur:
                # Query suppressions for this account
                cur.execute("""
                    SELECT email FROM email_suppressions
                    WHERE account_id = %s AND email = ANY(%s)
                """, (account_id, recipients))
                
                suppressed = [row[0] for row in cur.fetchall()]
                
                if suppressed:
                    logger.info(f"Filtered {len(suppressed)} suppressed email(s): {suppressed}")
                
                # Remove suppressed emails from recipients
                recipients = [r for r in recipients if r not in suppressed]
                
                if not recipients:
                    logger.info("All recipients suppressed, skipping email send")
                    return (200, "All recipients suppressed")
        except Exception as e:
            logger.error(f"Error checking suppressions: {e}")
            # Continue anyway - better to send than to fail completely
    
    # Rest of function continues as-is...
    # Extract data from payload
    report_type = payload.get("report_type", "market_snapshot")
    # ... etc
```

---

## File 2: `apps/worker/src/worker/tasks.py`

**Update the call to `send_schedule_email()` to pass the database connection:**

### Find the section where email is sent (around line 258):

```python
# Send email
status_code, response_text = send_schedule_email(
    account_id=account_id,
    recipients=recipients,
    payload=email_payload,
    account_name=account_name,
)
```

### Change to:

```python
# Send email with suppression filtering
status_code, response_text = send_schedule_email(
    account_id=account_id,
    recipients=recipients,
    payload=email_payload,
    account_name=account_name,
    db_conn=conn,  # ADD THIS LINE - pass the existing DB connection
)
```

**Note:** The `conn` variable should already exist in the scope (it's the PostgreSQL connection used for inserting `email_log` entries).

---

## Testing

After making these changes:

1. **Create a test schedule** with your email as recipient
2. **Let it send** - you should receive the email
3. **Click unsubscribe** - your email gets added to `email_suppressions`
4. **Trigger the schedule again** - check logs for:
   ```
   INFO: Filtered 1 suppressed email(s): ['your-email@example.com']
   INFO: All recipients suppressed, skipping email send
   ```
5. **Verify no email arrives** in your inbox

---

## Expected Behavior

**Before suppression:**
- Recipients: `['user@example.com']`
- Email sent: Yes
- Status code: 202

**After user unsubscribes:**
- Recipients (original): `['user@example.com']`
- Recipients (after filter): `[]`
- Email sent: No
- Status code: 200
- Response text: "All recipients suppressed"

**Partial suppression:**
- Recipients (original): `['user1@example.com', 'user2@example.com']`
- Suppressed: `['user1@example.com']`
- Recipients (after filter): `['user2@example.com']`
- Email sent: Yes (to user2 only)
- Status code: 202

---

## Implementation Notes

1. **Database Connection:** The `db_conn` parameter is optional to maintain backward compatibility. If not provided, suppression checking is skipped (safe fallback).

2. **Error Handling:** If suppression query fails, we log the error but continue sending. This prevents database issues from blocking critical notifications.

3. **Logging:** We log both suppressed emails and the decision to skip sending for audit purposes.

4. **Return Codes:**
   - `200` = "All recipients suppressed" (no email sent, but not an error)
   - `202` = Email sent successfully via SendGrid
   - `400` = Bad request (no recipients or no PDF URL)
   - `500+` = SendGrid errors

---

## Verification Queries

After implementation, verify with these SQL queries:

```sql
-- Check suppression was recorded
SELECT * FROM email_suppressions 
WHERE email = 'your-email@example.com';

-- Check email log shows suppression
SELECT provider, to_emails, response_code, error, created_at 
FROM email_log 
ORDER BY created_at DESC 
LIMIT 5;

-- Verify schedule run completed despite suppression
SELECT status, started_at, finished_at 
FROM schedule_runs 
ORDER BY created_at DESC 
LIMIT 5;
```

---

**Status:** Ready for implementation  
**Estimated Time:** 10-15 minutes  
**Risk:** Low (backward compatible, includes error handling)


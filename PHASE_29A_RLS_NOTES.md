# Phase 29A RLS Notes

**Date:** November 14, 2025  
**Status:** No changes to existing RLS in Phase 29A (deferred to Phase 29C)

## Current RLS Policies (Unchanged)

### Pattern
All RLS policies currently use the `app.current_account_id` session variable pattern:

```sql
USING (account_id = current_setting('app.current_account_id', true)::uuid)
WITH CHECK (account_id = current_setting('app.current_account_id', true)::uuid)
```

### Tables with RLS Enabled

#### 1. `report_generations`
**Policy Name:** `report_rls`  
**Effect:** Users can only see/modify reports for the account set in the session variable.

#### 2. `usage_tracking`
**Policy Name:** `usage_rls`  
**Effect:** Users can only see/modify usage records for the account set in the session variable.

#### 3. `api_keys`
**Policy Name:** `api_keys_rls`  
**Effect:** Users can only see/modify API keys for the account set in the session variable.

### How `app.current_account_id` is Set

**In API (apps/api/src/api/db.py):**
```python
def set_rls(cur, account_id: str):
    # Enforce RLS using Postgres session variable
    cur.execute(f"SET LOCAL app.current_account_id TO '{account_id}'")
```

**Called from route handlers:**
```python
with db_conn() as (conn, cur):
    set_rls(cur, account_id)  # Sets RLS context
    cur.execute("SELECT * FROM report_generations ...")  # Only sees account's data
```

## Phase 29A Impact

**No changes to RLS behavior in Phase 29A.**

Existing code continues to work:
- Single-account context via `app.current_account_id`
- All queries automatically filtered to that account
- New tables (`plans`, `account_users`) do NOT have RLS enabled (read-only or join tables)

## Future: Phase 29C RLS Enhancements

Phase 29C will introduce multi-account RLS logic using `account_users`:

### Planned Changes:

#### 1. **REGULAR Users** (via `account_users` membership)
Allow users to see accounts where they have OWNER or MEMBER role:

```sql
-- Example future policy
CREATE POLICY report_rls_multiuser ON report_generations
FOR ALL
USING (
  account_id = current_setting('app.current_account_id', true)::uuid
  OR
  EXISTS (
    SELECT 1 FROM account_users au
    WHERE au.account_id = report_generations.account_id
      AND au.user_id = current_setting('app.current_user_id', true)::uuid
      AND au.role IN ('OWNER', 'MEMBER')
  )
);
```

#### 2. **INDUSTRY_AFFILIATE Users** (sponsor visibility)
Affiliates can see:
- Their own account
- Sponsored accounts (where `sponsor_account_id` points to their account)

```sql
-- Example future policy
USING (
  account_id = current_setting('app.current_account_id', true)::uuid
  OR
  EXISTS (
    SELECT 1 FROM accounts a
    WHERE a.id = report_generations.account_id
      AND a.sponsor_account_id = current_setting('app.current_account_id', true)::uuid
  )
);
```

#### 3. **ADMIN Users** (global access)
Platform admins see everything:

```sql
-- Example future policy
USING (
  current_setting('app.current_user_role', true) = 'ADMIN'
  OR
  account_id = current_setting('app.current_account_id', true)::uuid
);
```

### Required Session Variables (Phase 29C)
- `app.current_account_id` ✅ (already exists)
- `app.current_user_id` (new, from auth token)
- `app.current_user_role` (new, from account_users)

### Migration Strategy (Phase 29C)
1. Drop existing RLS policies
2. Create new multi-context policies
3. Update `set_rls()` helper to set all 3 session variables
4. Test thoroughly with different user roles

## Why Not Change RLS Now?

**Phase 29A Goals:**
- Schema foundation only
- Backwards compatibility
- No disruption to existing auth flow

**Phase 29C Goals:**
- Multi-account user experience
- Affiliate dashboards
- Role-based access control

Separating schema (29A) from access control (29C) reduces risk and allows incremental rollout.

---

**Status:** ✅ **RLS Notes Complete - No Changes in Phase 29A**  
**Next:** RLS enhancements in Phase 29C after usage tracking (29B) is stable.


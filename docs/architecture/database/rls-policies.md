# Row-Level Security (RLS) Policies

## Overview

TrendyReports uses PostgreSQL Row-Level Security to enforce tenant isolation at the database level. Every query automatically filters rows based on the current account context, preventing cross-tenant data access.

## Tables with RLS Enabled

| Table | Policy Type |
|-------|-------------|
| `report_generations` | Standard + Admin bypass |
| `usage_tracking` | Standard + Admin bypass |
| `api_keys` | Standard + Admin bypass |
| `webhooks` | Standard + Admin bypass |
| `webhook_deliveries` | Standard + Admin bypass |
| `schedules` | Standard + Admin bypass |
| `schedule_runs` | Subquery (via schedule ownership) |
| `email_log` | Standard + Admin bypass |
| `email_suppressions` | Standard + Admin bypass |
| `contacts` | Standard + Admin bypass |
| `property_reports` | Standard + Admin bypass |
| `leads` | Standard + Admin bypass |
| `consumer_reports` | Standard + Admin bypass |

## Standard Policy Pattern

Most tables use this policy:

```sql
CREATE POLICY tenant_isolation ON <table_name>
  FOR ALL
  USING (
    account_id = current_setting('app.current_account_id', true)::uuid
    OR current_setting('app.current_user_role', true) = 'ADMIN'
  );
```

- `account_id = current_setting(...)` ensures only rows belonging to the current account are visible
- `OR ... = 'ADMIN'` allows platform administrators to access all rows

## Special Policies

### schedule_runs

`schedule_runs` does not have a direct `account_id` column. Instead, it uses a subquery through the parent `schedules` table:

```sql
CREATE POLICY tenant_isolation ON schedule_runs
  FOR ALL
  USING (
    schedule_id IN (
      SELECT id FROM schedules
      WHERE account_id = current_setting('app.current_account_id', true)::uuid
    )
    OR current_setting('app.current_user_role', true) = 'ADMIN'
  );
```

## How Context Is Set

The API middleware sets the RLS context on every database request:

1. JWT is decoded from the `mr_token` cookie
2. `account_id` and user role are extracted from the token claims
3. Before executing any query, the middleware runs:

```sql
SET LOCAL app.current_account_id = '<account_id>';
SET LOCAL app.current_user_role = '<role>';
```

`SET LOCAL` scopes the setting to the current transaction, ensuring it does not leak across requests.

## Common Gotchas

### 1. Missing context in background workers

Celery tasks run outside the HTTP request cycle. If a worker task queries an RLS-protected table without setting the context first, it will return zero rows. Worker tasks must explicitly set the RLS context before querying:

```python
await conn.execute("SET LOCAL app.current_account_id = $1", str(account_id))
```

### 2. Admin queries returning all data

Any query with `app.current_user_role = 'ADMIN'` will bypass tenant isolation entirely. Ensure admin role is only set for verified platform administrators.

### 3. Migrations and schema changes

RLS policies must be updated whenever new tenant-scoped tables are added. Forgetting to add RLS to a new table means it has no tenant isolation.

### 4. JOIN queries

When joining across RLS-protected tables, both tables are filtered independently. If one table in the join has a different account_id context expectation, the join may return unexpected results.

### 5. The `true` parameter in current_setting

`current_setting('app.current_account_id', true)` returns NULL instead of raising an error when the setting is not defined. This means queries will return zero rows (NULL != any UUID) rather than failing, which is the safe default behavior.

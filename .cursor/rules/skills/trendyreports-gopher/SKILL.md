---
name: trendyreports-gopher
description: Run database queries, generate verification SQL, prep migrations, and handle any database-focused task for TrendyReports. Use this skill whenever a ticket asks to "query the DB", "check production data", "generate SQL", "verify a migration", "find accounts/users/reports", "clean up data", "prep a kill list", "run a transaction", or anything where the primary deliverable is SQL or DB-derived data. Trigger especially for data cleanup tasks, production data audits, or anything that requires running BEGIN/COMMIT transactions. The gopher is allowed to execute SELECTs freely but must NEVER execute UPDATE/DELETE/INSERT without explicit user approval — only prep the SQL for review.
---

# TrendyReports Gopher

You handle database tasks. Read-only queries are free. Destructive operations require approval.

## Always Read First

1. `.cursor/rules/db-schema.md` — database schema reference (THIS IS CRITICAL)
2. `../references/architecture.md` — system overview
3. `../references/forbidden.md` — accounts and tables you must never touch without approval

## Permissions

### You CAN
- Run any `SELECT` query
- Run `EXPLAIN ANALYZE` on queries
- Generate `BEGIN` / `UPDATE` / `DELETE` / `INSERT` / `COMMIT` SQL
- Show the user the generated SQL for review
- Verify migration state (`SELECT * FROM schema_migrations`)

### You MUST NOT
- Execute `UPDATE`, `DELETE`, or `INSERT` without explicit user approval IN THIS TURN
- Run `DROP TABLE`, `TRUNCATE`, or any DDL outside migrations
- Modify Row-Level Security policies
- Touch the demo accounts or PCT accounts (see `../references/forbidden.md`)

## Workflow

### For Read Queries (SELECT)

1. Identify what data the user needs
2. Write the query — use schema reference for column names
3. Run it
4. Format the output clearly (table, JSON, or summary as appropriate)
5. Suggest follow-up queries if relevant

### For Destructive Operations

1. Identify what change is needed
2. Run SELECTs to understand the current state
3. Generate the destructive SQL inside a `BEGIN; ... COMMIT;` block
4. Add a verification `SELECT` between the update and the commit
5. Show the user the full transaction
6. WAIT for explicit approval ("go", "send it", "execute") before running
7. After running, run the verification SELECT and report the result

### For Migrations

1. Check the latest migration number in `db/migrations/`
2. Use the next number
3. Make it idempotent (`IF NOT EXISTS`, `IF EXISTS`)
4. Include rollback comments
5. Test on a non-production DB if available
6. Do NOT run it directly — let the deploy pipeline apply it

## SQL Patterns

### Safe Transaction Template

```sql
BEGIN;

-- 1. State the intent
-- Update X for accounts Y

-- 2. Do the change
UPDATE accounts SET col = 'value'
WHERE id IN ('xxx'::uuid, 'yyy'::uuid);

-- 3. Verify before commit
SELECT id, col FROM accounts WHERE id IN ('xxx'::uuid, 'yyy'::uuid);

-- 4. Commit only if verification looks right
COMMIT;
-- OR if something's off:
-- ROLLBACK;
```

### Finding Accounts

```sql
-- By name
SELECT id, name, account_type, plan_slug, is_active
FROM accounts
WHERE name ILIKE '%search%';

-- By owner email
SELECT a.id, a.name, u.email
FROM accounts a
JOIN account_users au ON au.account_id = a.id AND au.role = 'OWNER'
JOIN users u ON u.id = au.user_id
WHERE u.email ILIKE '%search%';

-- By tier
SELECT id, name FROM accounts
WHERE account_type = 'TITLE_COMPANY' AND is_active = true;
```

### Finding Reports

```sql
-- Recent reports for an account
SELECT id, report_type, status, generated_at, pdf_url
FROM report_generations
WHERE account_id = 'xxx'::uuid
ORDER BY generated_at DESC
LIMIT 10;

-- Failed reports across all accounts
SELECT account_id, report_type, error_message, generated_at
FROM report_generations
WHERE status = 'failed' AND generated_at > NOW() - INTERVAL '24 hours'
ORDER BY generated_at DESC;
```

### Finding Schedules

```sql
-- Active schedules sending to an email
SELECT id, name, recipients, active, last_run_at, next_run_at
FROM schedules
WHERE active = true
  AND recipients::text ILIKE '%email@example.com%';
```

### Migration Status

```sql
SELECT filename FROM schema_migrations ORDER BY filename DESC LIMIT 10;
```

## Common Gotchas

### UUID Casting

```sql
-- WRONG (string vs uuid mismatch in IN/ANY clauses)
WHERE id IN ('abc-123', 'def-456')

-- RIGHT
WHERE id IN ('abc-123'::uuid, 'def-456'::uuid)

-- For dynamic lists from Python:
WHERE id = ANY(%s::uuid[])
-- Pass: [str(uuid1), str(uuid2)]
```

### JSONB Queries

```sql
-- Get a field
SELECT recipients->>'emails' FROM schedules;

-- Filter on a field
WHERE filters_intent->>'price_strategy' = 'maxprice_pct_of_median_list';

-- Update a field
UPDATE schedules
SET filters_intent = jsonb_set(filters_intent, '{price_pct}', '85'::jsonb)
WHERE id = 'xxx'::uuid;
```

### Timezone Handling

- All `TIMESTAMPTZ` columns are UTC
- `NOW()` returns UTC
- Convert for display: `created_at AT TIME ZONE 'America/Los_Angeles'`
- Never compare timestamptz to a naive timestamp

### RLS Context

If queries return empty when they shouldn't, RLS may be filtering:

```sql
-- Bypass RLS for an admin query (use sparingly)
SET LOCAL row_security = off;
-- Run the query
SELECT ...;
```

Production code should always set:

```sql
SET app.current_account_id = '<account_id>';
```

## Protected Data

### Demo Accounts (Already Archived — Do Not Modify)
- `912014c3-6deb-4b40-a28d-489ef3923a3a` — [ARCHIVED] Demo Account
- `6588ca4a-9509-4118-9359-d1cbf72dcd52` — [ARCHIVED] Demo Title Company
- `d84a771e-1add-408b-bd82-7feb198121d4` — [ARCHIVED] Demo Sponsored Agent
- `cf7d8fde-4bb4-4603-88f0-39459053117b` — [ARCHIVED] Demo Free Agent
- `c059d968-e171-4549-9667-70eb7f3735cc` — [ARCHIVED] Demo Pro Agent

### Live Customer (Pacific Coast Title)
- `494f23ee-e8be-4fa2-9d7e-c18c1fb24a5b` — Pacific Coast Title Company

Never modify these without explicit user approval.

## Output Format

### For Read Queries

**Query Run**

`<the SQL>`

**Results**

`<formatted table or JSON>`

**Summary**

What the data shows in plain English.

**Suggested Follow-ups (if relevant)**

- Query X to dig deeper
- Verify Y

### For Destructive Operations

**Intent**

What change is being made and why.

**Current State (verified via SELECT)**

`<the SELECT results showing the rows that will be affected>`

**Proposed SQL (NOT EXECUTED)**

```sql
BEGIN;
  <the update/delete/insert>
  <verification SELECT>
COMMIT;
```

**Expected Outcome**

What the verification SELECT should show after running.

**Awaiting Approval**

"Run it" / "execute" / "go" before I proceed.

## Things to Flag, Not Fix

- Tables without indexes on frequently-queried columns
- Stale `is_active` rows
- Orphaned FK references
- Inconsistent NULL handling
- Pre-existing data quality issues

Mention them; don't try to fix them in a single ticket.

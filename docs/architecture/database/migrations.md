# Database Migrations

## Overview

TrendyReports uses sequential SQL migration files applied against PostgreSQL. Migrations are numbered and applied in order.

## Location

```
db/migrations/
  0001_init.sql
  0002_webhooks.sql
  0003_api_keys.sql
  ...
  0041_*.sql
```

Currently 41+ migration files, numbered from `0001` to `0041`.

## Naming Convention

```
{NNNN}_{description}.sql
```

- `NNNN`: Zero-padded 4-digit sequential number
- `description`: Snake-case description of the migration's purpose

Examples:
- `0001_init.sql` - Initial schema creation
- `0002_webhooks.sql` - Add webhooks tables
- `0015_rls_policies.sql` - Add RLS policies

## Migration Runners

### Shell script (psql)

```bash
scripts/migrate.sh
```

Applies all pending migrations using `psql` directly against the database.

### Python script

```bash
scripts/run_migrations.py
```

Python-based migration runner with tracking of applied migrations.

## Key Migrations

| Migration | Description |
|-----------|-------------|
| `0001_init.sql` | Core tables: accounts, users, account_users, plans |
| `0002_webhooks.sql` | Webhook and webhook_deliveries tables |
| `0003_api_keys.sql` | API keys table |
| Early migrations | Auth tables (jwt_blacklist, password_reset_tokens, email_verification_tokens) |
| Mid-range | Report tables (report_generations, schedules, schedule_runs) |
| Mid-range | Property report tables (property_reports, leads, blocked_ips) |
| Mid-range | Consumer report tables (consumer_reports, report_analytics) |
| Mid-range | Communication tables (email_log, email_suppressions, sms_logs) |
| Later migrations | RLS policies, views, functions, indexes |
| Recent | Branding, contacts, billing events, usage tracking |

## How to Add a New Migration

1. Determine the next sequential number by checking the highest existing migration file number
2. Create a new file in `db/migrations/` with the pattern `{NNNN}_{description}.sql`
3. Write idempotent SQL where possible (use `IF NOT EXISTS`, `CREATE OR REPLACE`, etc.)
4. Include both the schema change and any necessary data migrations
5. If adding a new tenant-scoped table, add RLS policies in the same migration
6. Test the migration against a local database before deploying
7. Run the migration using either `scripts/migrate.sh` or `scripts/run_migrations.py`

## Best Practices

- **Never modify an existing migration** that has been applied to production. Always create a new migration.
- **Use transactions** - each migration file should be wrapped in a transaction (or rely on the runner's transaction handling).
- **Idempotent operations** - prefer `IF NOT EXISTS` and `CREATE OR REPLACE` to make migrations safe to re-run.
- **Include rollback comments** - document what the reverse operation would be, even if automatic rollback is not supported.
- **Test locally first** - always apply migrations to a local/staging database before production.

# Migrations and deploys

**Apply, then deploy.** Render deploys do not run migrations. Since D-310 the
API, the Celery worker, the schedules ticker and the bridge refuse to start
when the database has not applied the newest migration their code needs
(`schema_guard.REQUIRED_MIGRATION`). A refused start fails the deploy, and the
version already running keeps serving.

## A PR that adds a migration

1. The PR adds `db/migrations/NNNN_name.sql` and sets `REQUIRED_MIGRATION` to
   that filename in **both** `apps/api/src/api/schema_guard.py` and
   `apps/worker/src/worker/schema_guard.py`. CI fails if either is missed.
2. Merge. The deploy that follows fails on purpose: the logs say
   `refusing to start: this code needs NNNN_name.sql; the newest migration the
   database has applied is …`. Nothing changes for users; the old version is
   still up.
3. Apply it: read-only checks for anything that changes rows, then
   `python scripts/run_migrations.py --status` (expect exactly the new file
   pending), then `python scripts/run_migrations.py`.
4. Deploy again (Render: "Deploy latest commit") on the API and worker services.
   `GET /health` returns `"schema": "NNNN_name.sql"` once the new code is live.

## The bypass

For an urgent fix that has to ship while a migration is deliberately held back,
set `SCHEMA_BEHIND_ACKNOWLEDGED=NNNN_name.sql` (the exact missing file) on the
service. It starts with a CRITICAL line in its log. The bypass names one
migration: as soon as the code needs a newer one, it no longer matches and the
check is back on. Remove it once the migration is applied.

## What the check does not cover

- A database it cannot reach at startup: the service starts and logs a
  warning, so a database blip does not become a crash loop.
- Render's behaviour on a failed start depends on the service settings.
  Confirm each service keeps the previous version running when a deploy fails
  (zero-downtime deploys). For a background worker without it, a refused start
  means the worker is down until the migration is applied; that is loud,
  where running ahead of the schema failed one request at a time.

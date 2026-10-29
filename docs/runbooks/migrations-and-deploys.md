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

## When a deploy fails, the old version keeps running

Checked 2026-10-29 for every service. The API is a web service with Health
Check Path `/health`; the worker, the ticker and the consumer bridge are
Background Workers. Render's deploy docs (render.com/docs/deploys): if the
build, pre-deploy or start command fails or times out, "the entire deploy
fails" and the service keeps running its last successful deploy; this
zero-downtime sequence "applies to web services, private services, background
workers, and cron jobs". Seen in production the same day: the bridge's deploy
of `09c8b71` failed and Render kept `229ee8b` live.

So a refused start never takes a service down. **The cost is that it is
silent**: a service whose deploy failed keeps serving the older code, and
nothing tells you. On 2026-10-29 the worker and ticker ran `09c8b71` while the
bridge sat on `229ee8b`. Closed the same day: "Deploy latest commit" on the
bridge went Live, so the failure was a one-off in the deploy, not the code
(the bridge's start path was unchanged between the two commits, and
`09c8b71`'s bridge started cleanly against a database at 0061 locally). After
it, all four services read Live on the same commit — the check below, passed.

After every merge to `main`, and after every "Deploy latest commit":

1. In Render, check that each of the four services' **newest** deploy reads
   Live, not Failed, and that all four show the same commit.
2. API: `GET /health` returns the `schema` the code needs.
3. A Failed deploy: open it and read the last lines of its log.
   - `refusing to start: this code needs NNNN_….sql` — the schema guard;
     apply the migration (above), then deploy again.
   - A build error (dependency install, out of memory, timeout) — fix or
     re-run the build; the code was never started.
   - `Exited with status …` after the service's own output — the start
     command or the code failed; the lines above it say which.

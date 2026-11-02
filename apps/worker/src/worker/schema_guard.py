"""Refuse to start when the database is behind the code.

WHY. Deploys do not run migrations. On 2026-10-28 #224 and #226 went live
expecting 0060 and 0061; production stopped at 0055, and for a day every
unsubscribe, every rep invite and the company dashboard returned 500 (board
D-310). Nothing said so: the service started, answered /health, and failed
one request at a time.

WHAT. At startup the service asks `schema_migrations` whether the newest
migration its code needs has been applied. If not, it logs why and exits.
A failed start fails the deploy, and the version already running keeps
serving — so code can no longer go live ahead of its schema. The order is
apply, then deploy.

  * A database AHEAD of the code (a rollback) is fine: only the one row is
    asked for.
  * A database that cannot be reached is NOT refused: the service could not
    serve anyway, and refusing would turn a database blip into a crash loop
    that outlasts it. It is logged, and the request path fails as before.
  * The bypass, for an emergency fix that must ship while a migration waits:
    `SCHEMA_BEHIND_ACKNOWLEDGED=<the missing migration's filename>`. It names
    one migration, so once the code needs a newer one the bypass no longer
    matches and the check is back on. It cannot be left switched off.

`REQUIRED_MIGRATION` is kept at the newest file in db/migrations by
tests/test_schema_guard.py, so a PR that adds a migration and forgets this
line fails CI. The worker carries the same module
as the API (apps/api/src/api/schema_guard.py); neither can import the other,
and the same test holds the two identical.
"""
import logging
import os
import sys

REQUIRED_MIGRATION = "0062_email_log_status_comment.sql"

logger = logging.getLogger("schema_guard")


class SchemaBehind(RuntimeError):
    """The database has not applied a migration this code needs."""


def check(cur) -> None:
    """Raise SchemaBehind unless REQUIRED_MIGRATION is recorded."""
    cur.execute("SELECT to_regclass('schema_migrations') IS NOT NULL")
    if not cur.fetchone()[0]:
        raise SchemaBehind(
            f"the database has no schema_migrations table; this code needs "
            f"{REQUIRED_MIGRATION}")
    cur.execute("SELECT 1 FROM schema_migrations WHERE filename = %s", (REQUIRED_MIGRATION,))
    if cur.fetchone():
        return
    cur.execute(
        "SELECT max(filename) FROM schema_migrations WHERE filename ~ '^[0-9]{4}_'")
    newest = cur.fetchone()[0]
    raise SchemaBehind(
        f"this code needs {REQUIRED_MIGRATION}; the newest migration the database "
        f"has applied is {newest}")


def enforce(dsn, service: str) -> None:
    """Run `check` against `dsn`; exit the process if the database is behind."""
    import psycopg

    try:
        with psycopg.connect(dsn, connect_timeout=10) as conn, conn.cursor() as cur:
            check(cur)
    except SchemaBehind as behind:
        if os.environ.get("SCHEMA_BEHIND_ACKNOWLEDGED") == REQUIRED_MIGRATION:
            logger.critical(
                "%s: STARTING WITH THE DATABASE BEHIND THE CODE (%s). "
                "SCHEMA_BEHIND_ACKNOWLEDGED is set for it; anything that needs it will fail.",
                service, behind)
            return
        logger.critical(
            "%s: refusing to start: %s. Apply the pending migrations "
            "(scripts/run_migrations.py), then deploy again.", service, behind)
        sys.exit(1)
    except psycopg.Error as unreachable:
        logger.warning(
            "%s: could not check the database schema at startup (%s); starting anyway",
            service, unreachable)

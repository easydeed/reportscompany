#!/usr/bin/env python3
"""
Apply pending migrations from db/migrations, once each.

    DATABASE_URL=postgresql://... python scripts/run_migrations.py
    DATABASE_URL=postgresql://... python scripts/run_migrations.py --bootstrap
    DATABASE_URL=postgresql://... python scripts/run_migrations.py --status

--bootstrap records every unrecorded file as applied WITHOUT executing it. It is
for a database that already has the schema but no tracking table — i.e. every
database that existed before tracking was added. Run it there once, BEFORE a
normal run, or the first normal run re-executes 50+ historical migrations
against live data.

scripts/migrate.sh implements the same contract against the same table; the
table and that contract are defined in db/schema_migrations.sql.

Each file is executed whole, in one transaction. It is not split on semicolons:
splitting breaks DO $$ ... $$ blocks and silently dropped any statement that
followed a comment line.
"""
import hashlib
import os
import sys
from pathlib import Path

import psycopg

REPO_ROOT = Path(__file__).resolve().parent.parent
MIGRATIONS_DIR = REPO_ROOT / "db" / "migrations"
TRACKING_DDL = REPO_ROOT / "db" / "schema_migrations.sql"


def checksum(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> None:
    mode = "apply"
    if len(sys.argv) > 1:
        if sys.argv[1] == "--bootstrap":
            mode = "bootstrap"
        elif sys.argv[1] == "--status":
            mode = "status"
        else:
            print(
                f"unknown option: {sys.argv[1]} "
                "(expected --bootstrap, --status, or no argument)",
                file=sys.stderr,
            )
            sys.exit(2)

    database_url = os.environ.get("DATABASE_URL")
    if not database_url:
        print(
            "ERROR: DATABASE_URL is not set.\n"
            "Usage: DATABASE_URL=postgresql://... python scripts/run_migrations.py",
            file=sys.stderr,
        )
        sys.exit(1)

    if not MIGRATIONS_DIR.exists():
        print(f"ERROR: migrations directory not found: {MIGRATIONS_DIR}", file=sys.stderr)
        sys.exit(1)

    files = sorted(MIGRATIONS_DIR.glob("*.sql"))
    if not files:
        print("ERROR: no migration files found", file=sys.stderr)
        sys.exit(1)

    print(f"Migrations: {len(files)} files on disk (mode: {mode})")

    applied = skipped = recorded = pending = 0

    with psycopg.connect(database_url, autocommit=False) as conn:
        # The tracking table has to exist before we can ask what has been applied.
        with conn.cursor() as cur:
            cur.execute(TRACKING_DDL.read_text())
        conn.commit()

        with conn.cursor() as cur:
            cur.execute("SELECT filename, checksum FROM schema_migrations")
            already = dict(cur.fetchall())

        for path in files:
            name = path.name
            digest = checksum(path)

            if name in already:
                if already[name] != digest:
                    print(f"  ! {name} — already applied, but the file has changed since (not re-run)")
                skipped += 1
                continue

            if mode == "status":
                print(f"  pending: {name}")
                pending += 1
                continue

            if mode == "bootstrap":
                with conn.cursor() as cur:
                    cur.execute(
                        "INSERT INTO schema_migrations (filename, checksum) VALUES (%s, %s)"
                        " ON CONFLICT (filename) DO NOTHING",
                        (name, digest),
                    )
                conn.commit()
                print(f"  marked applied WITHOUT running: {name}")
                recorded += 1
                continue

            print(f">>> Running migration: {name}")
            try:
                with conn.cursor() as cur:
                    cur.execute(path.read_text())
                    cur.execute(
                        "INSERT INTO schema_migrations (filename, checksum) VALUES (%s, %s)"
                        " ON CONFLICT (filename) DO NOTHING",
                        (name, digest),
                    )
                conn.commit()
            except psycopg.Error as exc:
                conn.rollback()
                print(f"[ERROR] {name} failed, rolled back: {exc}", file=sys.stderr)
                sys.exit(1)
            applied += 1

    if mode == "status":
        print(f"Status: {skipped} applied, {pending} pending.")
    elif mode == "bootstrap":
        print(f"Bootstrap complete: {recorded} marked as applied without running, {skipped} already recorded.")
        print("Normal runs will now apply only genuinely new migrations.")
    else:
        print(f"All migrations applied. ({applied} newly applied, {skipped} already recorded)")


if __name__ == "__main__":
    main()

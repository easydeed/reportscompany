#!/usr/bin/env python3
"""
Apply pending migrations from db/migrations, once each.

    DATABASE_URL=postgresql://... python scripts/run_migrations.py
    DATABASE_URL=postgresql://... python scripts/run_migrations.py --status
    DATABASE_URL=postgresql://... python scripts/run_migrations.py --bootstrap --through <file>
    DATABASE_URL=postgresql://... python scripts/run_migrations.py --bootstrap --except <file>

--bootstrap records files as applied WITHOUT executing them. It is for a
database that already has the schema but no tracking table — i.e. every database
that existed before tracking was added. Run it there once, BEFORE a normal run,
or the first normal run re-executes 50+ historical migrations against live data.

WHY --through AND --except EXIST
--------------------------------
Bare `--bootstrap` marks *every* unrecorded file, including migrations that have
never run anywhere. That is a silent no-op with a green result: the run prints
"N marked as applied", a following `--status` prints "0 pending", and the
migration's changes are simply never made — with the tracking table asserting
that they were. Nothing re-runs it afterwards, because the loop skips anything
already recorded.

This is not hypothetical. The runbook for this repository was written twice with
0054_growth_plan_report_limit.sql already in the tree; following it would have
reported complete success and left the Growth plan limit unchanged.

So the boundary is now explicit:

  --through NAME   record NAME and everything sorting before it; leave the rest
                   genuinely pending. Use when the database is "at" a point in
                   history: everything up to NAME is already in the schema.

  --except NAME    record everything EXCEPT the named files (repeatable). Use
                   when you know precisely which migrations have not run.

  (neither)        still allowed, but it now WARNS, lists every file it would
                   mark, and requires confirmation — `--yes`, or an interactive
                   answer. Non-interactive without `--yes` refuses rather than
                   proceeding, because the dangerous case and the safe case were
                   previously the same command.

CHOOSING BETWEEN THEM — a real trap in this repository
------------------------------------------------------
`--through` splits on SORTED order, and not every file here is numbered.
`seed_demo_account.sql` sorts AFTER every `NNNN_` migration, so

    --bootstrap --through 0053_phase4_indexes_and_signup_tokens.sql

leaves BOTH 0054 and seed_demo_account.sql pending — and the next normal run
would execute the seeder, inserting a hardcoded "Demo Account" into production.
Whatever is left pending is printed with that consequence spelled out; read it.
When the set of un-run migrations is known exactly, `--except` says so directly
and has no ordering surprise.

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
from typing import List, Optional, Sequence, Tuple

REPO_ROOT = Path(__file__).resolve().parent.parent
MIGRATIONS_DIR = REPO_ROOT / "db" / "migrations"
TRACKING_DDL = REPO_ROOT / "db" / "schema_migrations.sql"

USAGE = (
    "usage: run_migrations.py [--status]\n"
    "       run_migrations.py [--bootstrap [--through NAME | --except NAME ...] [--yes]]"
)


class ArgError(Exception):
    """Bad command line. Carries the message shown to the operator."""


def checksum(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def parse_args(argv: Sequence[str]) -> dict:
    """
    Parse argv (without the program name).

    Pure and exception-based so the argument rules can be tested without a
    database — the defect this guard exists to prevent lives entirely in which
    files get selected, never in the SQL.
    """
    opts = {"mode": "apply", "through": None, "excepts": [], "assume_yes": False}
    i = 0
    while i < len(argv):
        arg = argv[i]
        if arg == "--status":
            opts["mode"] = "status"
        elif arg == "--bootstrap":
            opts["mode"] = "bootstrap"
        elif arg == "--yes":
            opts["assume_yes"] = True
        elif arg in ("--through", "--except"):
            i += 1
            if i >= len(argv) or argv[i].startswith("--"):
                raise ArgError(f"{arg} requires a migration filename")
            if arg == "--through":
                if opts["through"] is not None:
                    raise ArgError("--through may only be given once")
                opts["through"] = argv[i]
            else:
                opts["excepts"].append(argv[i])
        else:
            raise ArgError(f"unknown option: {arg}")
        i += 1

    if opts["through"] is not None and opts["excepts"]:
        raise ArgError("--through and --except are alternatives; use one or the other")
    if opts["mode"] != "bootstrap" and (opts["through"] is not None or opts["excepts"]):
        raise ArgError("--through and --except only apply to --bootstrap")
    return opts


def partition_bootstrap(
    names: Sequence[str],
    through: Optional[str] = None,
    excepts: Sequence[str] = (),
) -> Tuple[List[str], List[str]]:
    """
    Split `names` into (record_without_running, leave_pending).

    `names` must already be in the order the runner walks them — sorted, the
    same order `--status` reports. `through` is inclusive.

    Raises ArgError for a name that is not present, rather than silently
    matching nothing: a typo in --except is how a migration you meant to
    protect gets marked applied anyway.
    """
    names = list(names)
    known = set(names)

    if through is not None:
        if through not in known:
            raise ArgError(f"--through names a file that is not in {MIGRATIONS_DIR.name}/: {through}")
        cut = names.index(through) + 1
        record, pending = names[:cut], names[cut:]
    else:
        record, pending = list(names), []

    for name in excepts:
        if name not in known:
            raise ArgError(f"--except names a file that is not in {MIGRATIONS_DIR.name}/: {name}")

    if excepts:
        excluded = set(excepts)
        pending = pending + [n for n in record if n in excluded]
        record = [n for n in record if n not in excluded]
        pending = [n for n in names if n in set(pending)]  # keep sorted order

    return record, pending


def _confirm_blanket_bootstrap(unrecorded: Sequence[str], assume_yes: bool) -> bool:
    """
    Bare --bootstrap marks everything. Make the operator see what that means.

    Returns True to proceed. Non-interactive without --yes returns False:
    defaulting to "proceed" is what made the dangerous invocation and the safe
    one the same command.
    """
    print("")
    print("WARNING: --bootstrap with no --through or --except marks ALL of these")
    print("         as applied WITHOUT running them:")
    for name in unrecorded:
        print(f"           {name}")
    print("")
    print("  Any of these that has NOT already been applied to this database will")
    print("  never run: the tracking table will claim it did, and later runs skip")
    print("  anything already recorded. The result looks like success.")
    print("")
    print("  If some of these are genuinely new, name the boundary instead:")
    print("    --bootstrap --through <last-migration-already-in-this-database>")
    print("    --bootstrap --except <migration-that-has-not-run> [--except ...]")
    print("")

    if assume_yes:
        print("  Proceeding: --yes was given.")
        return True

    if not sys.stdin.isatty():
        print(
            "REFUSED: no terminal to confirm on. Re-run with --through, --except,\n"
            "         or --yes if marking every file listed above is genuinely correct.",
            file=sys.stderr,
        )
        return False

    answer = input(f"  Mark all {len(unrecorded)} files as applied without running them? [y/N] ")
    return answer.strip().lower() in ("y", "yes")


def main() -> None:
    # Imported here, not at module scope, so the argument and selection logic
    # above can be unit-tested without a database driver installed.
    import psycopg

    try:
        opts = parse_args(sys.argv[1:])
    except ArgError as exc:
        print(f"{exc}\n{USAGE}", file=sys.stderr)
        sys.exit(2)

    mode = opts["mode"]

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

    all_names = [p.name for p in files]
    try:
        to_record, to_leave_pending = partition_bootstrap(
            all_names, opts["through"], opts["excepts"]
        )
    except ArgError as exc:
        print(f"{exc}", file=sys.stderr)
        sys.exit(2)

    print(f"Migrations: {len(files)} files on disk (mode: {mode})")

    applied = skipped = recorded = pending = left_pending = 0

    with psycopg.connect(database_url, autocommit=False) as conn:
        # The tracking table has to exist before we can ask what has been applied.
        with conn.cursor() as cur:
            cur.execute(TRACKING_DDL.read_text())
        conn.commit()

        with conn.cursor() as cur:
            cur.execute("SELECT filename, checksum FROM schema_migrations")
            already = dict(cur.fetchall())

        # Confirm BEFORE writing anything, and only about files that would
        # actually be marked — already-recorded files are not at risk.
        if mode == "bootstrap" and opts["through"] is None and not opts["excepts"]:
            unrecorded = [n for n in all_names if n not in already]
            if unrecorded and not _confirm_blanket_bootstrap(unrecorded, opts["assume_yes"]):
                print("Nothing was changed.", file=sys.stderr)
                sys.exit(3)

        record_set = set(to_record)

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
                if name not in record_set:
                    print(f"  left PENDING (will run on the next normal run): {name}")
                    left_pending += 1
                    continue
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
        if left_pending:
            print("")
            print(f"{left_pending} file(s) were deliberately LEFT PENDING and WILL EXECUTE")
            print("on the next normal run:")
            for name in to_leave_pending:
                if name not in already:
                    print(f"    {name}")
            print("")
            print("Read that list before running. Anything there that should NOT execute")
            print("against this database needs --except, or it runs.")
        else:
            print("Normal runs will now apply only genuinely new migrations.")
    else:
        print(f"All migrations applied. ({applied} newly applied, {skipped} already recorded)")


if __name__ == "__main__":
    main()

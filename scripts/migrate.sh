#!/usr/bin/env bash
#
# Apply pending migrations from db/migrations, once each.
#
#   bash scripts/migrate.sh              apply every file not yet recorded
#   bash scripts/migrate.sh --bootstrap  record every unrecorded file as applied
#                                        WITHOUT executing it
#   bash scripts/migrate.sh --status     list applied / pending, change nothing
#
# --bootstrap is for a database that already has the schema but no tracking
# table (i.e. every database that existed before tracking was added). Run it
# once there, immediately, BEFORE a normal run — otherwise the first normal run
# re-executes 50+ historical migrations against live data.
#
# scripts/run_migrations.py implements the same contract against the same table;
# see db/schema_migrations.sql.
#
set -euo pipefail

DB_URL="${DATABASE_URL:-postgresql://postgres:postgres@localhost:5432/market_reports}"
MODE="apply"
case "${1:-}" in
  --bootstrap) MODE="bootstrap" ;;
  --status)    MODE="status" ;;
  "")          ;;
  *) echo "unknown option: $1 (expected --bootstrap, --status, or no argument)" >&2; exit 2 ;;
esac

q() { psql "$DB_URL" -tAc "$1"; }

# The tracking table has to exist before we can ask what has been applied.
psql "$DB_URL" -v ON_ERROR_STOP=1 -q -f db/schema_migrations.sql

echo "Migrations: ${DB_URL%%\?*}  (mode: $MODE)"

shopt -s nullglob
applied=0; skipped=0; recorded=0; pending=0

for f in db/migrations/*.sql; do
  base="$(basename "$f")"
  sum="$(sha256sum "$f" | cut -d' ' -f1)"
  prev="$(q "SELECT checksum FROM schema_migrations WHERE filename = '${base//\'/\'\'}'")"

  if [ -n "$prev" ]; then
    if [ "$prev" != "$sum" ]; then
      echo "  ! $base — already applied, but the file has changed since (not re-run)"
    fi
    skipped=$((skipped + 1))
    continue
  fi

  case "$MODE" in
    status)
      echo "  pending: $base"
      pending=$((pending + 1))
      ;;
    bootstrap)
      psql "$DB_URL" -v ON_ERROR_STOP=1 -q -c \
        "INSERT INTO schema_migrations (filename, checksum) VALUES ('${base//\'/\'\'}', '$sum') ON CONFLICT (filename) DO NOTHING"
      echo "  marked applied WITHOUT running: $base"
      recorded=$((recorded + 1))
      ;;
    apply)
      echo ">>> Running migration: $base"
      # -1 wraps the file in a single transaction: a failure leaves nothing behind.
      psql "$DB_URL" -v ON_ERROR_STOP=1 -1 -f "$f"
      psql "$DB_URL" -v ON_ERROR_STOP=1 -q -c \
        "INSERT INTO schema_migrations (filename, checksum) VALUES ('${base//\'/\'\'}', '$sum') ON CONFLICT (filename) DO NOTHING"
      applied=$((applied + 1))
      ;;
  esac
done

case "$MODE" in
  status)    echo "Status: $skipped applied, $pending pending." ;;
  bootstrap) echo "Bootstrap complete: $recorded marked as applied without running, $skipped already recorded."
             echo "Normal runs will now apply only genuinely new migrations." ;;
  apply)     echo "All migrations applied. ($applied newly applied, $skipped already recorded)" ;;
esac

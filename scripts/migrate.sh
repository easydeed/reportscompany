#!/usr/bin/env bash
#
# Apply pending migrations from db/migrations, once each.
#
#   bash scripts/migrate.sh              apply every file not yet recorded
#   bash scripts/migrate.sh --status     list applied / pending, change nothing
#   bash scripts/migrate.sh --bootstrap --through NAME
#   bash scripts/migrate.sh --bootstrap --except NAME [--except NAME ...]
#
# --bootstrap records files as applied WITHOUT executing them. It is for a
# database that already has the schema but no tracking table (i.e. every
# database that existed before tracking was added). Run it once there,
# immediately, BEFORE a normal run — otherwise the first normal run re-executes
# 50+ historical migrations against live data.
#
# Bare --bootstrap marks EVERY unrecorded file, including migrations that have
# never run anywhere. That is a silent no-op with a green result: the run says
# "N marked as applied", --status then says "0 pending", and the migration's
# changes are never made while the tracking table claims they were. So the
# boundary is now explicit:
#
#   --through NAME   record NAME and everything sorting before it; the rest stay
#                    genuinely pending.
#   --except NAME    record everything except the named files (repeatable).
#   (neither)        warns, lists what it would mark, and requires --yes.
#
# NOTE --through splits on SORTED order and not every file is numbered:
# seed_demo_account.sql sorts after every NNNN_ migration, so a boundary of
# 0053 leaves the seeder pending too and a normal run would execute it. What is
# left pending is printed; read it. --except has no ordering surprise.
#
# scripts/run_migrations.py implements the same contract against the same table;
# see db/schema_migrations.sql.
#
set -euo pipefail

DB_URL="${DATABASE_URL:-postgresql://postgres:postgres@localhost:5432/market_reports}"
MODE="apply"
THROUGH=""
ASSUME_YES=0
EXCEPTS=""   # newline-separated
while [ $# -gt 0 ]; do
  case "$1" in
    --bootstrap) MODE="bootstrap" ;;
    --status)    MODE="status" ;;
    --yes)       ASSUME_YES=1 ;;
    --through)
      shift
      [ $# -gt 0 ] || { echo "--through requires a migration filename" >&2; exit 2; }
      [ -z "$THROUGH" ] || { echo "--through may only be given once" >&2; exit 2; }
      THROUGH="$1" ;;
    --except)
      shift
      [ $# -gt 0 ] || { echo "--except requires a migration filename" >&2; exit 2; }
      EXCEPTS="$EXCEPTS$1"$'\n' ;;
    *) echo "unknown option: $1 (expected --bootstrap, --status, --through, --except, --yes)" >&2; exit 2 ;;
  esac
  shift
done

if [ -n "$THROUGH" ] && [ -n "$EXCEPTS" ]; then
  echo "--through and --except are alternatives; use one or the other" >&2; exit 2
fi
if [ "$MODE" != "bootstrap" ] && { [ -n "$THROUGH" ] || [ -n "$EXCEPTS" ]; }; then
  echo "--through and --except only apply to --bootstrap" >&2; exit 2
fi

# Validate the named files exist before touching the database — a typo in
# --except is how a migration you meant to protect gets marked applied anyway.
for want in $THROUGH $(printf '%s' "$EXCEPTS"); do
  [ -f "db/migrations/$want" ] || { echo "names a file that is not in db/migrations/: $want" >&2; exit 2; }
done

q() { psql "$DB_URL" -tAc "$1"; }

# The tracking table has to exist before we can ask what has been applied.
psql "$DB_URL" -v ON_ERROR_STOP=1 -q -f db/schema_migrations.sql

echo "Migrations: ${DB_URL%%\?*}  (mode: $MODE)"

shopt -s nullglob

# Is $1 in the set this run will record without executing?
should_record() {
  local base="$1"
  # --except: named files are never recorded.
  if [ -n "$EXCEPTS" ]; then
    while IFS= read -r ex; do
      [ -z "$ex" ] && continue
      [ "$base" = "$ex" ] && return 1
    done <<< "$EXCEPTS"
  fi
  # --through: sorted order, boundary inclusive.
  if [ -n "$THROUGH" ] && [[ "$base" > "$THROUGH" ]]; then
    return 1
  fi
  return 0
}

# Bare --bootstrap marks everything. Show the operator what that means, and
# refuse non-interactively rather than defaulting to "proceed" — the dangerous
# invocation and the safe one used to be the same command.
if [ "$MODE" = "bootstrap" ] && [ -z "$THROUGH" ] && [ -z "$EXCEPTS" ]; then
  unrecorded=""
  for f in db/migrations/*.sql; do
    b="$(basename "$f")"
    if [ -z "$(q "SELECT 1 FROM schema_migrations WHERE filename = '${b//\'/\'\'}'")" ]; then
      unrecorded="$unrecorded  $b"$'\n'
    fi
  done
  if [ -n "$unrecorded" ]; then
    echo ""
    echo "WARNING: --bootstrap with no --through or --except marks ALL of these"
    echo "         as applied WITHOUT running them:"
    printf '%s' "$unrecorded"
    echo ""
    echo "  Any of these not already applied to this database will never run:"
    echo "  the tracking table will claim it did, and later runs skip anything"
    echo "  already recorded. The result looks like success."
    echo ""
    echo "  If some are genuinely new, name the boundary instead:"
    echo "    --bootstrap --through <last-migration-already-in-this-database>"
    echo "    --bootstrap --except <migration-that-has-not-run> [--except ...]"
    echo ""
    if [ "$ASSUME_YES" = "1" ]; then
      echo "  Proceeding: --yes was given."
    elif [ -t 0 ]; then
      read -r -p "  Mark all of them as applied without running? [y/N] " ans
      case "$ans" in y|Y|yes|YES) ;; *) echo "Nothing was changed." >&2; exit 3 ;; esac
    else
      echo "REFUSED: no terminal to confirm on. Re-run with --through, --except," >&2
      echo "         or --yes if marking every file above is genuinely correct." >&2
      echo "Nothing was changed." >&2
      exit 3
    fi
  fi
fi

applied=0; skipped=0; recorded=0; pending=0; left_pending=0; pending_list=""

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
      if ! should_record "$base"; then
        echo "  left PENDING (will run on the next normal run): $base"
        left_pending=$((left_pending + 1))
        pending_list="$pending_list    $base"$'\n'
        continue
      fi
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
             if [ "$left_pending" -gt 0 ]; then
               echo ""
               echo "$left_pending file(s) were deliberately LEFT PENDING and WILL EXECUTE"
               echo "on the next normal run:"
               printf '%s' "$pending_list"
               echo ""
               echo "Read that list before running. Anything there that should NOT execute"
               echo "against this database needs --except, or it runs."
             else
               echo "Normal runs will now apply only genuinely new migrations."
             fi ;;
  apply)     echo "All migrations applied. ($applied newly applied, $skipped already recorded)" ;;
esac

#!/usr/bin/env bash
set -euo pipefail

DB_URL="${DATABASE_URL:-postgresql://postgres:postgres@localhost:5432/market_reports}"
echo "Applying SQL migrations to ${DB_URL}"

# Apply all *.sql in db/migrations in alphanumeric order
shopt -s nullglob
for f in db/migrations/*.sql; do
  echo ">>> Running migration: $f"
  psql "${DB_URL}" -v ON_ERROR_STOP=1 -f "$f"
done
echo "All migrations applied."


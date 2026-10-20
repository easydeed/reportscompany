#!/usr/bin/env bash
# Bring up Postgres + Redis + the API + Next so a rendered page has data in it.
#
#   scripts/local_stack.sh up      # start everything, migrate, seed
#   scripts/local_stack.sh down    # stop the servers (keeps the database)
#   scripts/local_stack.sh nuke     # stop and delete the database cluster
#   scripts/local_stack.sh status
#
# WHY THIS EXISTS
# ---------------
# `scripts/render_routes.mjs` alone measures CHROME. Without an API the token
# is unsigned, every call 401s, and 16 of 22 routes come back `degraded` — the
# shell is real, the content is a skeleton. Reviewing Design's steps 4-7 that
# way is reviewing an empty page, which this project has already done twice
# (gallery continuation on the old architecture, the 101px trend chart) and
# both numbers were real and meant nothing.
#
# With the stack up: 22 rendered, 0 degraded. Noise floor across two runs: 0/25
# routes changed.
#
# WHAT IT DOES NOT COVER — read this before scoping a batch against it
# --------------------------------------------------------------------
#   SimplyRETS    No MLS feed. `result_json` on seeded reports is a fixture
#                 shaped like a report, not one the worker produced. Anything
#                 asserting real market numbers, trend series, or the field
#                 sweep needs the vendor (and the credential trips in §T2).
#   PDFShift      No PDF rendering. `pdf_url` is null on every seeded row, so
#                 /print/[runId], the PDF download and the social image are
#                 out of reach. The embedded report PREVIEW is React and does
#                 render.
#   SiteX         No property data. Property reports are seeded rows; the
#                 address lookup and comps map are not exercised.
#   Stripe        No billing. /app/billing renders its shell; checkout, the
#                 plan-change confirm panel and invoices need Stripe keys.
#   Resend        No email. Schedules can be created and listed; nothing sends,
#                 so delivery state never advances past what is seeded.
#   Twilio        No SMS.
#   The worker    Not started. Nothing moves a report from `queued` to
#                 `completed`; the seeded rows are already in their final state.
#
# ONE MORE THING, AND IT IS NOT A VENDOR
# --------------------------------------
# A MEASUREMENT HARNESS HITTING A RATE-LIMITED API PRODUCES DEGRADED DATA THAT
# LOOKS LIKE REAL DATA. `RateLimitMiddleware` allows `accounts.api_rate_limit`
# requests per minute, default 60; 25 routes of several calls each is several
# hundred. On the first live run four endpoints returned 429 and the dashboard
# rendered 47 skeletons — indistinguishable, in a screenshot, from a dashboard
# whose data is genuinely missing.
#
# NOTHING CHECKED A VALUE TO CATCH THAT. It was caught by the harness's health
# gate refusing to photograph a page it could not prove had arrived. A
# value-level assertion ("the reports table has rows") would have failed and
# been read as a product defect; the health gate said "content absent" and
# named the spinner count, which is a different and much more useful sentence.
#
# So: `seed_render_fixture.py` raises `api_rate_limit` to 100000 on the five
# accounts the manifest logs in as, and Redis is flushed between runs. **If you
# add routes to the manifest or raise the request count per route, this is what
# you will hit first**, and it will arrive as plausible emptiness rather than
# as an error.
#
# So: chrome, layout, tables, pills, type, tokens, lists, forms and navigation
# are all verifiable. Report CONTENT, PDFs, billing flows and delivery are not.
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
PGBIN=/usr/lib/postgresql/16/bin
PGPORT=5433
DB=market_reports
export DATABASE_URL="postgresql://postgres@127.0.0.1:${PGPORT}/${DB}"
export REDIS_URL="redis://127.0.0.1:6379/0"

# The one value the API and the harness must agree on: the API verifies the
# signature, so a token minted with a different secret renders the shell and
# nothing else. Override both together or neither.
export JWT_SECRET="${JWT_SECRET:-local-render-secret}"
export RENDER_JWT_SECRET="$JWT_SECRET"

API_PORT=8099
WEB_PORT=3100
LOG="${ROOT}/.render/stack-logs"
PY="${LOCAL_STACK_PYTHON:-python3}"

msg() { printf '\n== %s\n' "$*"; }

# `initdb` and `postgres` REFUSE TO RUN AS ROOT. In a container that is the
# only user there is, so those commands go through `su postgres`; on a
# developer machine the current user already cannot be root for this, so they
# run directly. Written as a wrapper rather than branching at every call site,
# and `PGDATA` lands somewhere the running user can actually write — the
# container default is root-owned, which is what made the first attempt fail
# with "could not start server" and an EMPTY log, because `pg_ctl -l` could
# not create the file either.
if [ "$(id -u)" = "0" ]; then
  PGDATA="${PGDATA_OVERRIDE:-/var/lib/postgresql/16/trendy}"
  as_pg() { su postgres -c "$*"; }
  pg_own() { mkdir -p "$1" && chown postgres:postgres "$1"; }
else
  PGDATA="${PGDATA_OVERRIDE:-${HOME}/.trendy-pgdata}"
  as_pg() { bash -c "$*"; }
  pg_own() { mkdir -p "$1"; }
fi

# `pg_ctl` needs a real binary directory; a non-container install may not use
# the Debian layout.
if [ ! -x "${PGBIN}/initdb" ]; then
  if command -v pg_ctl >/dev/null 2>&1; then
    PGBIN="$(dirname "$(command -v pg_ctl)")"
  else
    echo "no postgres server found: looked in ${PGBIN} and on PATH" >&2
    echo "install postgres, or set PGBIN to its bin directory" >&2
    exit 2
  fi
fi

pg_up() {
  if [ ! -d "$PGDATA" ]; then
    msg "initdb ${PGDATA}"
    pg_own "$PGDATA"
    as_pg "$PGBIN/initdb -D $PGDATA -U postgres --auth=trust -E UTF8" >/dev/null
  fi
  if ! as_pg "$PGBIN/pg_ctl -D $PGDATA status" >/dev/null 2>&1; then
    msg "starting postgres on ${PGPORT}"
    # The log goes inside PGDATA because whoever runs the server must be able
    # to write it — pointing -l at a directory they do not own fails with
    # "could not start server" and an empty log, which is a confusing half
    # hour the first time.
    as_pg "$PGBIN/pg_ctl -D $PGDATA -l $PGDATA/server.log \
      -o '-p ${PGPORT} -c listen_addresses=127.0.0.1' start" >/dev/null
  fi
  psql -h 127.0.0.1 -p "$PGPORT" -U postgres -tAc \
    "SELECT 1 FROM pg_database WHERE datname='${DB}'" | grep -q 1 \
    || psql -h 127.0.0.1 -p "$PGPORT" -U postgres -c "CREATE DATABASE ${DB}" >/dev/null
}

redis_up() {
  redis-cli ping >/dev/null 2>&1 && return
  msg "starting redis"
  redis-server --port 6379 --daemonize yes >/dev/null
}

case "${1:-}" in
up)
  mkdir -p "$LOG"
  pg_up
  redis_up

  msg "migrations"
  "$PY" "${ROOT}/scripts/run_migrations.py" | tail -2

  msg "seeds"
  "$PY" "${ROOT}/scripts/seed_test_accounts.py" up | tail -1
  "$PY" "${ROOT}/scripts/seed_render_fixture.py" up | tail -10

  msg "api on ${API_PORT}"
  pkill -f "uvicorn api.main:app" 2>/dev/null || true
  ( cd "${ROOT}/apps/api" && ENVIRONMENT=development PYTHONPATH=src \
      "$PY" -m uvicorn api.main:app --host 127.0.0.1 --port "$API_PORT" \
      > "${LOG}/api.log" 2>&1 & )

  msg "web on ${WEB_PORT}"
  ( cd "${ROOT}/apps/web" && NEXT_PUBLIC_API_BASE="http://127.0.0.1:${API_PORT}" \
      INTERNAL_RENDER_TOKEN=local-render-token \
      "${ROOT}/node_modules/.bin/next" dev -p "$WEB_PORT" \
      > "${LOG}/web.log" 2>&1 & )

  for _ in $(seq 1 40); do
    curl -sf "http://127.0.0.1:${API_PORT}/health" >/dev/null 2>&1 \
      && curl -sf "http://127.0.0.1:${WEB_PORT}/login" >/dev/null 2>&1 && break
    "$PY" -c "import time;time.sleep(1)"
  done

  msg "up"
  echo "  api   http://127.0.0.1:${API_PORT}/health"
  echo "  web   http://127.0.0.1:${WEB_PORT}"
  echo "  logs  ${LOG}"
  echo
  echo "  RENDER_JWT_SECRET=${JWT_SECRET} node scripts/render_routes.mjs --out .render/before"
  echo
  echo "  Redis is flushed between runs on purpose: the rate limiter counts"
  echo "  per minute per account, and the fixture raises api_rate_limit to"
  echo "  100000 because a harness loading 25 routes is not a user. Without"
  echo "  both, calls 429 and the pages render skeletons the harness honestly"
  echo "  reports as degraded."
  ;;
down)
  msg "stopping web and api"
  pkill -f "uvicorn api.main:app" 2>/dev/null || true
  pkill -f "next dev -p ${WEB_PORT}" 2>/dev/null || true
  as_pg "$PGBIN/pg_ctl -D $PGDATA stop" >/dev/null 2>&1 || true
  redis-cli shutdown nosave >/dev/null 2>&1 || true
  echo "stopped (database kept — use \`nuke\` to delete it)"
  ;;
nuke)
  "$0" down || true
  rm -rf "$PGDATA"
  echo "cluster deleted"
  ;;
status)
  as_pg "$PGBIN/pg_ctl -D $PGDATA status" 2>&1 | head -2 || true
  redis-cli ping 2>&1 | head -1
  curl -s -o /dev/null -w "api  %{http_code}\n" "http://127.0.0.1:${API_PORT}/health" || true
  curl -s -o /dev/null -w "web  %{http_code}\n" "http://127.0.0.1:${WEB_PORT}/login" || true
  "$PY" "${ROOT}/scripts/seed_render_fixture.py" status 2>/dev/null || true
  ;;
*)
  sed -n '2,12p' "${BASH_SOURCE[0]}"
  exit 2
  ;;
esac

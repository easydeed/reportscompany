#!/usr/bin/env bash
# QA-RUN-ALL-REPORTS — bash + curl fallback for environments without Python.
#
# Usage:
#   export QA_TOKEN="<paste JWT here>"
#   # optional, defaults to production:
#   export QA_API_BASE="https://reportscompany-api.onrender.com"
#   bash scripts/qa_generate_all_reports.sh
#
# Requirements: curl, jq
#
# How to get a JWT:
#   1. Log in at https://trendyreports.io
#   2. Open DevTools → Network tab
#   3. Click any in-app page that loads data
#   4. Find a /v1/... request and copy the "Authorization: Bearer <token>"
#      header value (just the part after "Bearer ")
#   5. export QA_TOKEN="<token>"

set -u
set -o pipefail

# ─── dependencies ──────────────────────────────────────────────────────────
for cmd in curl jq; do
  if ! command -v "$cmd" >/dev/null 2>&1; then
    echo "ERROR: '$cmd' is required but not installed." >&2
    exit 2
  fi
done

# ─── config ────────────────────────────────────────────────────────────────
TOKEN="${QA_TOKEN:-}"
if [ -z "$TOKEN" ]; then
  cat >&2 <<'MSG'
ERROR: QA_TOKEN is not set.

Set it before running:
    export QA_TOKEN="<paste JWT here>"

How to get a JWT:
  1. Log in to https://trendyreports.io
  2. Open DevTools → Network tab
  3. Click any in-app page that loads data
  4. Pick any /v1/... request and copy the
     "Authorization: Bearer <token>" header value (just the part after "Bearer ")
  5. export QA_TOKEN="<token>"
MSG
  exit 2
fi

API="${QA_API_BASE:-https://reportscompany-api.onrender.com}"
CITY="${QA_CITY:-Irvine}"
LOOKBACK="${QA_LOOKBACK:-30}"
THEME="${QA_THEME:-1}"
POLL_INTERVAL=5
MAX_ATTEMPTS=24   # 24 × 5s = 120s budget per report

REPORT_TYPES=(
  market_snapshot
  new_listings_gallery
  new_listings
  closed
  inventory
  featured_listings
  open_houses
  price_bands
)

echo "=============================================================================="
echo "  QA-RUN-ALL-REPORTS (bash)"
echo "=============================================================================="
echo "  API base : $API"
echo "  City     : $CITY"
echo "  Lookback : $LOOKBACK days"
echo "  theme_id : $THEME"
echo "  Reports  : ${#REPORT_TYPES[@]} types"
echo "=============================================================================="
echo

declare -a SUMMARY=()
SUCCESS_COUNT=0

for TYPE in "${REPORT_TYPES[@]}"; do
  echo "  → $TYPE: creating…"
  START_TS=$(date +%s)

  CREATE_RESP=$(curl -sS -X POST "$API/v1/reports" \
    -H "Authorization: Bearer $TOKEN" \
    -H "Content-Type: application/json" \
    -d "{\"report_type\":\"$TYPE\",\"city\":\"$CITY\",\"lookback_days\":$LOOKBACK,\"theme_id\":\"$THEME\"}")

  REPORT_ID=$(printf '%s' "$CREATE_RESP" | jq -r '.report_id // .id // empty')
  if [ -z "$REPORT_ID" ] || [ "$REPORT_ID" = "null" ]; then
    SUMMARY+=("❌ $TYPE → FAILED: could not create report — $CREATE_RESP")
    echo "     $TYPE: create failed → $CREATE_RESP"
    continue
  fi

  echo "     $TYPE: queued ($REPORT_ID); polling every ${POLL_INTERVAL}s up to $((POLL_INTERVAL * MAX_ATTEMPTS))s…"

  STATUS=""
  PDF_URL=""
  ERROR_MSG=""
  for i in $(seq 1 "$MAX_ATTEMPTS"); do
    sleep "$POLL_INTERVAL"
    STATUS_RESP=$(curl -sS "$API/v1/reports/$REPORT_ID" \
      -H "Authorization: Bearer $TOKEN")
    STATUS=$(printf '%s' "$STATUS_RESP" | jq -r '.status // empty')

    if [ "$STATUS" = "completed" ]; then
      PDF_URL=$(printf '%s' "$STATUS_RESP" | jq -r '.pdf_url // empty')
      break
    fi
    if [ "$STATUS" = "failed" ] || [ "$STATUS" = "error" ]; then
      ERROR_MSG=$(printf '%s' "$STATUS_RESP" | jq -r '.error_message // .error // empty')
      break
    fi
  done

  END_TS=$(date +%s)
  DURATION=$((END_TS - START_TS))

  if [ "$STATUS" = "completed" ] && [ -n "$PDF_URL" ] && [ "$PDF_URL" != "null" ]; then
    SIZE_BYTES=$(curl -sSI -L "$PDF_URL" | awk 'BEGIN{IGNORECASE=1} /^Content-Length:/ {gsub("\r",""); print $2}' | tail -n1)
    if [ -n "$SIZE_BYTES" ]; then
      SIZE_KB=$(awk -v b="$SIZE_BYTES" 'BEGIN { printf "%.1f KB", b/1024 }')
      LINE="✅ $TYPE → $PDF_URL  ($SIZE_KB, ${DURATION}s)"
    else
      LINE="✅ $TYPE → $PDF_URL  (size ?, ${DURATION}s)"
    fi
    SUCCESS_COUNT=$((SUCCESS_COUNT + 1))
    SUMMARY+=("$LINE")
    echo "     $LINE"
  else
    if [ -z "$ERROR_MSG" ]; then
      if [ -z "$STATUS" ]; then
        ERROR_MSG="timed out after $((POLL_INTERVAL * MAX_ATTEMPTS))s with no status"
      else
        ERROR_MSG="non-completed status: $STATUS"
      fi
    fi
    LINE="❌ $TYPE → FAILED: $ERROR_MSG  (${DURATION}s)"
    SUMMARY+=("$LINE")
    echo "     $LINE"
  fi
done

echo
echo "=============================================================================="
echo "  QA-RUN-ALL-REPORTS — Summary"
echo "=============================================================================="
for line in "${SUMMARY[@]}"; do
  echo "  $line"
done
echo
echo "  Total: $SUCCESS_COUNT/${#REPORT_TYPES[@]} succeeded"
echo "=============================================================================="

if [ "$SUCCESS_COUNT" -eq "${#REPORT_TYPES[@]}" ]; then
  exit 0
else
  exit 1
fi

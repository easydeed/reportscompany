#!/usr/bin/env bash
set -euo pipefail

echo "Starting local dev helpers..."
echo "• Web (Next.js): will run in Section 2 (apps/web)"
echo "• API (FastAPI): will run in Section 3 (apps/api)"
echo "• Worker (Celery): will run in Section 4 (apps/worker)"
echo ""
echo "For now, bring up Postgres & Redis:"
echo "  make db-up"
echo ""
echo "After Sections 2–4 you will run web/api/worker concurrently here."


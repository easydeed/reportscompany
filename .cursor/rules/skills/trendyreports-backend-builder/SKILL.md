---
name: trendyreports-backend-builder
description: Make backend changes to TrendyReports — FastAPI routes, Celery worker tasks, Jinja2 templates, SQL migrations, business logic in services/. Use this skill whenever a ticket involves modifying API endpoints under apps/api/, worker tasks under apps/worker/, database migrations under db/migrations/, PDF/email templates, or any server-side logic. Trigger even when the ticket doesn't explicitly say "backend" — if Python files, SQL files, or Jinja2 templates are touched, this skill applies. Especially trigger for any work involving PDF generation, email rendering, report builders, market data, property data, comparables, AI narratives, or scheduled jobs.
---

# TrendyReports Backend Builder

You implement backend changes for TrendyReports. FastAPI + Celery + PostgreSQL + Jinja2.

## Always Read First

1. `.cursor/rules/db-schema.md` — database schema reference
2. `../references/architecture.md` — system overview
3. `../references/forbidden.md` — what NEVER to change
4. `../references/conventions.md` — coding patterns
5. `../references/pdf-pipeline.md` — when touching PDF generation

## Your Workflow

For every ticket:

1. **Read the ticket fully.** Identify exact files. Identify which layer (API / Worker / DB).
2. **Read the existing code.** Don't pattern-match from memory — read the actual file.
3. **Check the schema.** Before writing SQL, confirm column names and types exist.
4. **Make the minimum change.** Don't refactor adjacent code.
5. **Test the failure modes.** What happens if the input is None? What if the user lacks permission? What if the row doesn't exist?
6. **Do NOT execute destructive operations.** Never run UPDATE/DELETE in production without explicit user approval.
7. **Do NOT commit or push.** Stage changes; let the user review.

## Backend Architecture

### Layers

| Layer | Path | Purpose |
|-------|------|---------|
| API | `apps/api/src/api/` | HTTP request handling, auth, request validation |
| Worker | `apps/worker/src/worker/` | Async jobs: report generation, email, PDF |
| DB | `db/migrations/` | Schema changes |
| Services | `apps/api/src/api/services/` and `apps/worker/src/worker/` | Business logic |

### API Layer (FastAPI)

**Route structure:**

```python
from fastapi import APIRouter, Depends, HTTPException, Request
from api.deps import require_account_id

router = APIRouter()

@router.get("/v1/reports")
async def list_reports(
    request: Request,
    account_id: str = Depends(require_account_id),
):
    with db_conn() as conn:
        with conn.cursor() as cur:
            cur.execute("SET app.current_account_id = %s", (account_id,))
            cur.execute("SELECT ... FROM reports WHERE account_id = %s", (account_id,))
            return [dict(row) for row in cur.fetchall()]
```

**Auth dependencies:**
- `require_account_id` — any authenticated user
- `require_platform_admin` — admin only
- `require_company_admin` — company tier
- `require_affiliate` — title rep tier

**Always:**
- Set RLS context before queries
- Use parameterized queries
- Return HTTPException with structured detail on errors

### Worker Layer (Celery)

**Task pattern:**

```python
@celery.task(bind=True, autoretry_for=(Exception,), retry_backoff=True, max_retries=3)
def generate_report(self, run_id, account_id, report_type, params):
    try:
        # 1. Fetch data
        # 2. Build report
        # 3. Render HTML
        # 4. Render PDF (PDFShift)
        # 5. Upload to R2
        # 6. Update DB
        cur.execute("UPDATE report_generations SET status='completed', pdf_url=%s WHERE id=%s",
                    (pdf_url, run_id))
    except Exception as e:
        cur.execute("UPDATE report_generations SET status='failed', error_message=%s WHERE id=%s",
                    (str(e), run_id))
        raise
```

**For PDF tasks specifically:** Read `../references/pdf-pipeline.md` before any PDF-related work.

### Database Layer

**Connection pool:**

```python
from api.db import db_conn

with db_conn() as conn:
    with conn.cursor() as cur:
        cur.execute("...")
        # autocommit per statement (with default config)
```

**RLS:**

```python
cur.execute("SET app.current_account_id = %s", (account_id,))
# Now SELECTs against tenant tables are filtered to this account
```

**Migrations:**
- New migration: increment number, descriptive name (e.g., `0052_add_xxx.sql`)
- Include both UP and rollback comments
- Always idempotent (`IF NOT EXISTS`, `IF EXISTS`)
- Run via `scripts/run_migrations.py`
- Latest applied is 0051

**Common gotchas:**
- UUID/str mixed types in `ANY(%s)` will fail — coerce all to `str()` first
- JSONB fields: use `::jsonb` cast and `jsonb_set()` for updates
- Don't forget `NOW()` for timestamps; use `created_at TIMESTAMPTZ DEFAULT NOW()`
- Foreign keys with `ON DELETE CASCADE` for tenant-scoped data
- Always index foreign keys

## Worker Module Patterns

### Report Builders

| File | Purpose |
|------|---------|
| `market_builder.py` | Market reports (8 types), uses PDF_CONFIG |
| `property_builder.py` | Property reports (5 themes), uses Smart Color System |
| `report_builders.py` | Per-type data shapers (build_closed_result, etc.) |
| `filter_resolver.py` | Market-adaptive filters (price_strategy) |
| `ai_market_narrative.py` | GPT-4o commentary for market reports |
| `ai_overview.py` | GPT-4o executive summary for property reports |
| `pdf_adapter.py` | PDFShift HTTP client |

### Email Templates

`apps/worker/src/worker/email/template.py` — V16 modular architecture:
- `schedule_email_html()` is the entry point
- `LAYOUT_MAP` routes report_type → body builder
- Layout builders: `_build_market_narrative_body`, `_build_gallery_2x2_body`, etc.
- Component helpers: `_build_hero_stat`, `_build_cta`, `_build_truncation_note`
- All colors parameterized — no hardcoded brand colors

### Jinja2 Templates

Located in `apps/worker/src/worker/templates/`:
- `market/` — single template with theme variables
- `property/{classic,modern,elegant,teal,bold}/` — 5 themes
- `_base/base.jinja2` — shared base for property report themes
- `_base/macros.jinja2` — shared macros (listing cards, headers)

**Multi-page support:**
- `.report-page` uses `min-height: 11in` (NOT `height: 11in; overflow: hidden`)
- `.listing-card` has `page-break-inside: avoid`
- `@page` rule defines letter size + 0.5in margins

**Per-type config:**
`PDF_CONFIG` dict in `market_builder.py` has cap, section_label, truncation_template, more_template per report type.

## SQL Patterns

### Safe Update Transaction

```sql
BEGIN;

UPDATE accounts SET plan_slug = 'starter' WHERE id = 'xxx'::uuid;

-- Verify before commit
SELECT id, plan_slug FROM accounts WHERE id = 'xxx'::uuid;

-- Inspect, then either:
COMMIT;
-- OR:
ROLLBACK;
```

### Migration Template

```sql
-- Migration 0052: <description>
-- Up
ALTER TABLE accounts
ADD COLUMN IF NOT EXISTS new_column TEXT DEFAULT NULL;

-- Index if querying often
CREATE INDEX IF NOT EXISTS idx_accounts_new_column
  ON accounts(new_column)
  WHERE new_column IS NOT NULL;

-- Backfill if needed
UPDATE accounts SET new_column = 'default' WHERE new_column IS NULL;

-- Rollback comment:
-- ALTER TABLE accounts DROP COLUMN new_column;
```

## API Response Patterns

### Success

```python
return {"data": [...], "total": count, "page": page}
```

### Error

```python
raise HTTPException(
    status_code=400,
    detail={
        "error": "validation_failed",
        "message": "City is required",
        "field": "city",
    }
)
```

### Empty list

```python
return {"data": [], "total": 0}  # NOT 404
```

## Testing Approach

- Smoke test scripts: `scripts/test_simplyrets.py`, `scripts/test_sitex.py`, `scripts/test_property_report_flow.py`
- Template tests: `tests/test_property_templates.py` (pytest)
- E2E: `e2e/*.spec.ts` (Playwright)
- Local report generation: `scripts/gen_market_reports.py`

After changes:
- Run relevant smoke tests if applicable
- For DB changes, verify with a SELECT before committing
- For template changes, generate one local PDF and inspect

## Output Format

**Files Changed**

```
apps/api/src/api/routes/file.py (+15 -3)
apps/worker/src/worker/file.py (+5 -2)
db/migrations/0052_xxx.sql (new)
```

**Summary**

What changed and why, one-paragraph max.

**SQL Generated (if any)**

- New migration file
- Verification queries to run

**Failure Modes Considered**

- What happens if input is None: ...
- What happens if user lacks permission: ...
- What happens if row doesn't exist: ...

**Verification Steps**

What the user should do to confirm the change works:

1. ...
2. ...

**Not Touched**

Files I intentionally did not modify and why.

**Notes / Flags**

Things to mention but not fix.

## Things to Flag, Not Fix

- Unrelated SQL inefficiencies in queries near your changes
- Pre-existing N+1 patterns
- Missing indexes (mention but don't add unless ticket asks)
- Stale dependencies in pyproject.toml / requirements
- Inconsistent error response shapes in other routes

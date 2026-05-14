# TrendyReports — Coding Conventions

## Frontend (Next.js / React)

### File Locations

| What | Where |
|------|-------|
| Pages | `apps/web/app/**/page.tsx` |
| Layouts | `apps/web/app/**/layout.tsx` |
| Domain components | `apps/web/components/{domain}/` (e.g., `schedules/`, `property-wizard/`) |
| Shared components | `apps/web/components/shared/` |
| UI primitives | `apps/web/components/ui/` (shadcn) |
| API proxy routes | `apps/web/app/api/proxy/v1/**/route.ts` |
| React Query hooks | `apps/web/hooks/use-api.ts` |
| Types | `apps/web/lib/types/` |

### State Management

- Server state: React Query (`@tanstack/react-query`)
- Local state: `useState` / `useReducer`
- Form state: `react-hook-form` + zod
- NEVER use Redux or Zustand for this app

### React Query

- `QueryProvider` MUST live at `apps/web/app/app/layout.tsx` root, above any layout branching
- Default `staleTime`: 30 seconds for lists, 5 minutes for static data
- After mutations, ALWAYS call `queryClient.invalidateQueries({ queryKey: [...] })`
- Use `queryKeys` factory in `apps/web/hooks/use-api.ts` for consistent keys

### Styling

- Tailwind classes via `cn()` helper from `apps/web/lib/utils.ts`
- shadcn primitives — don't reinvent (Button, Card, Dialog, etc.)
- Brand colors come from `account.primary_color` and `account.secondary_color`, NOT hardcoded
- Default indigo (`#4F46E5`) is for unbranded states ONLY

### Navigation / Routing

- Use `next/link` for navigation, never `<a href>` for internal routes
- Use `useRouter()` from `next/navigation` (App Router), NOT `next/router`
- Active route highlighting: `pathname === item.href`
- For "builder mode" routes (wizards, edit pages), check `isBuilderRoute(pathname)` from `app-layout.tsx`

## Backend (FastAPI)

### File Locations

| What | Where |
|------|-------|
| Route handlers | `apps/api/src/api/routes/{domain}.py` |
| Business logic | `apps/api/src/api/services/{domain}.py` |
| Pydantic schemas | `apps/api/src/api/schemas/{domain}.py` |
| Middleware | `apps/api/src/api/middleware/{name}.py` |
| DB connection | `apps/api/src/api/db.py` |

### Auth Patterns

- Routes use `Depends(require_account_id)` for tenant isolation
- Admin routes use `Depends(require_platform_admin)`
- Company routes use `Depends(require_company_admin)`
- Affiliate routes use `Depends(require_affiliate)`
- Get account_id from `request.state.account_id` (set by middleware)

### Database

- Always use the connection pool: `with db_conn() as conn:`
- Set RLS context before queries: `cur.execute("SET app.current_account_id = %s", (account_id,))`
- Use parameterized queries: `cur.execute("SELECT ... WHERE id = %s", (id,))`
- NEVER use string concatenation for SQL
- For UUIDs in IN clauses, cast: `'uuid-string'::uuid`
- Mixed UUID/str types in `ANY(%s)` will fail — coerce all to `str()` first

### Error Handling

- Raise `HTTPException(status_code=..., detail={...})` for API errors
- Use structured error responses: `{"error": "code", "message": "human readable"}`
- Log exceptions with `logger.exception()`, never `logger.error()` + traceback

## Worker (Celery)

### Tasks

- All tasks in `apps/worker/src/worker/tasks.py`
- Use `@celery.task(bind=True, autoretry_for=(Exception,))` for resilience
- Update `report_generations.status` at each stage: `pending` → `generating` → `completed` / `failed`
- Store `error_message` on failure for debugging

### PDF Generation Pipeline

1. Build HTML via `MarketReportBuilder` or `PropertyReportBuilder`
2. Embed images as base64 (`embed_images_as_base64()`)
3. Send to PDFShift via `pdf_adapter.render_pdf()`
4. Upload PDF to R2 via `upload_to_r2()`
5. Update `pdf_url` on report row

### Templates

- Jinja2, inheritance via `_base/base.jinja2`
- 5 themes for property reports: classic, modern, elegant, teal, bold
- 1 unified template for market reports with theme variables
- Section labels + truncation notes via `PDF_CONFIG` in `market_builder.py`

## Database

### Migrations

- Located in `db/migrations/0001_*.sql` through current
- Latest applied: 0051 (per-product pricing)
- New migrations: increment number, descriptive name
- Always include rollback comments
- Run via `scripts/run_migrations.py`

### Common Tables

| Table | Purpose |
|-------|---------|
| `accounts` | Multi-tenant accounts |
| `users` | Platform users |
| `account_users` | Many-to-many: user belongs to account with role |
| `plans` | Plan catalog with limits |
| `report_generations` | Every market report |
| `schedules` | Automated report schedules |
| `property_reports` | Property report records |
| `leads` | Captured leads from CMA pages |
| `email_log` | Sent email tracking |

## Naming Conventions

- Files: kebab-case (`my-component.tsx`, `lead_pages.py`)
- TypeScript: PascalCase types, camelCase variables/functions
- Python: snake_case for everything
- SQL: snake_case for tables and columns
- React components: PascalCase
- React hooks: `useXxx`

## Commit Messages

Format: `<type>(<scope>): <subject>`

Types: `feat`, `fix`, `refactor`, `chore`, `docs`, `test`, `hotfix`

Examples:
- `feat(billing): allow sponsored agents to self-upgrade`
- `fix(schedules): stop /app/schedules entering builder mode`
- `refactor(layout): hoist QueryProvider to /app root`
- `chore(qa): add script for local PDF generation`

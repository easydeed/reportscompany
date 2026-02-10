# Reports API

> Market report CRUD with plan limit enforcement.
> File: `apps/api/src/api/routes/reports.py`

## Endpoints

| Method | Path | Purpose | Auth |
|--------|------|---------|------|
| POST | /v1/reports | Create report with limit check | Required |
| GET | /v1/reports | List reports with filters | Required |
| GET | /v1/reports/{id} | Get single report | Required |
| GET | /v1/reports/{id}/data | Public report data for PDF gen | Public |

## Key Functions

### POST /v1/reports
- **Input:** `ReportCreate {report_type, city, zips, polygon, lookback_days, filters, additional_params}`
- **Status code:** 202 Accepted (async processing)
- Calls `evaluate_report_limit(cur, account_id)` to check plan limits
- Three possible outcomes from limit check:
  - `LimitDecision.ALLOW` -- proceed normally
  - `LimitDecision.ALLOW_WITH_WARNING` -- proceed + set `X-TrendyReports-Usage-Warning` header
  - `LimitDecision.BLOCK` -- return 429 with usage/plan info
- Inserts into `report_generations` table with status `pending`
- Enqueues `generate_report` task via `worker_client.enqueue_generate_report()`
- If enqueue fails: updates status to `failed` with error message
- Returns `{report_id, status}`

### GET /v1/reports
- **Query params:** `report_type`, `status`, `from_date`, `to_date`, `limit` (1-100), `offset`
- Always filters by `account_id` (data isolation)
- Orders by `generated_at DESC`
- Returns `{reports: [...], pagination: {limit, offset, count}}`

### GET /v1/reports/{id}
- Returns single report row as `ReportRow`
- Filters by both `id` and `account_id`
- 404 if not found

### GET /v1/reports/{id}/data
- **Public endpoint** (no auth required)
- Used by the print page (`/print/[runId]`) as the data source for PDF generation
- Listed in AuthContextMiddleware's public paths

## Dependencies
- `services/__init__.py`: `evaluate_report_limit()`, `log_limit_decision()`, `LimitDecision`
- `worker_client.py`: `enqueue_generate_report()` -- sends task to Redis/Celery
- `db.py`: `db_conn()`, `set_rls()`, `fetchone_dict()`, `fetchall_dicts()`

## Related Files
- Frontend: `/app/reports` (list), `/app/reports/new` (wizard)
- Worker: `tasks.py` processes the `generate_report` task
- Print page: `/print/[runId]` fetches data from `/v1/reports/{id}/data`

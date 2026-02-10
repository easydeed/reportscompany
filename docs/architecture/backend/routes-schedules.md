# Schedules API

> Automated report delivery configuration: CRUD, pause/resume, recipients, cadence, filters.
> File: `apps/api/src/api/routes/schedules.py`

## Endpoints

| Method | Path | Purpose | Auth |
|--------|------|---------|------|
| POST | /v1/schedules | Create schedule | Required |
| GET | /v1/schedules | List schedules | Required |
| GET | /v1/schedules/{id} | Get single schedule | Required |
| PATCH | /v1/schedules/{id} | Update schedule | Required |
| DELETE | /v1/schedules/{id} | Delete schedule | Required |
| GET | /v1/schedules/{id}/runs | List execution history | Required |

## Key Functions

### POST /v1/schedules
- **Input:** `ScheduleCreate` with name, report_type, city, zip_codes, lookback_days, cadence, time settings, recipients, filters
- Validates cadence params (weekly needs weekly_dow, monthly needs monthly_dom)
- Encodes recipients to JSON strings with ownership validation
- Supports typed recipients: contact, sponsored_agent, group, manual_email
- Stores filters as JSONB (supports market-adaptive pricing via `PriceStrategy`)
- Returns created schedule with `resolved_recipients` (decoded for frontend)

### GET /v1/schedules
- Query param: `active_only` (default true)
- Returns all schedules with decoded recipients
- Always filters by account_id

### PATCH /v1/schedules/{id}
- Dynamic UPDATE: only provided fields are changed
- Nulls out `next_run_at` on any update so the background ticker recomputes it
- Validates recipient ownership when recipients are updated
- Returns `{id, message}`

### DELETE /v1/schedules/{id}
- Returns 204 No Content
- Cascade deletes schedule_runs via foreign key

### GET /v1/schedules/{id}/runs
- Lists execution history for a schedule (up to 50 runs)
- Verifies schedule ownership before returning runs
- Returns `{runs: [...], count}`

## Recipient System

Recipients are stored as a PostgreSQL TEXT[] array where each element is a JSON string:

```json
{"type": "contact", "id": "<contact_uuid>"}
{"type": "sponsored_agent", "id": "<account_uuid>"}
{"type": "group", "id": "<group_uuid>"}
{"type": "manual_email", "email": "user@example.com"}
```

**Validation:** `validate_recipient_ownership()` checks:
- contact: belongs to account
- sponsored_agent: has sponsor_account_id matching account
- group: belongs to account
- manual_email: no ownership check needed

## Filter System (Smart Presets)

Filters are stored as JSONB with the `ReportFilters` schema:

| Field | Type | Description |
|-------|------|-------------|
| minbeds | int | Minimum bedrooms |
| minbaths | int | Minimum bathrooms |
| minprice | int | Absolute minimum price |
| maxprice | int | Absolute maximum price |
| subtype | text | SingleFamilyResidence or Condominium |
| price_strategy | object | Market-adaptive pricing |
| preset_display_name | text | Display name for PDF headers |

`price_strategy` supports modes like `maxprice_pct_of_median_list` (e.g., 70% of median) which resolve to dollar amounts at runtime via the worker's `filter_resolver.py`.

## Dependencies
- `db.py`: `db_conn()`, `set_rls()`, `fetchone_dict()`, `fetchall_dicts()`
- No external API calls -- schedule execution happens in the Worker service

## Related Files
- Frontend: `/app/schedules` (list), `/app/schedules/new` (wizard), `/app/schedules/[id]` (detail)
- Worker: `schedules_tick.py` finds due schedules and enqueues them
- Worker: `tasks.py` executes the report generation

# Module: Worker Core

> `apps/worker/src/worker/app.py` (65 lines)
> `apps/worker/src/worker/schedules_tick.py` (462 lines)
> `apps/worker/src/worker/limit_checker.py`
> `apps/worker/src/worker/cache.py`

---

## Change Log

| Date | Change |
|------|--------|
| 2026-04 | **Audit:** Full rewrite against code. Fixed: `app.py` uses `Celery("market_reports")` not `Celery("worker")`. `schedules_tick.py` runs as a separate process via `run_forever()`, NOT via Celery beat. Main function is `process_due_schedules()` not `tick()`. Uses `zoneinfo.ZoneInfo` not `pytz`. Uses `psycopg` (v3) not `psycopg2`. Added all real function signatures with line numbers. Beat schedule only has `keep_alive_ping`. |
| 2026-01 | Added `ai_insights` cache (24h TTL) to reduce OpenAI costs. |
| 2025-12 | Added `schedules_tick` with `SELECT FOR UPDATE SKIP LOCKED`. |
| 2025-11 | Added `limit_checker.py` for worker-context plan enforcement. |
| 2025-10 | Initial `app.py` and `cache.py`. |

---

## Purpose

Core worker infrastructure: Celery application setup, the schedule tick executor (runs as a separate process), plan-limit enforcement in the worker context, and the Redis caching layer.

---

## `app.py` — Celery Application (65 lines)

Initialises the Celery application with Redis broker and result backend. Handles SSL configuration for production Redis (Render).

```python
celery = Celery(
    "market_reports",
    broker=BROKER,
    backend=BACKEND,
)
```

**Key configuration (L34–55):**

| Setting | Value |
|---------|-------|
| `task_serializer` | `json` |
| `task_time_limit` | 300 seconds |
| `timezone` | UTC |
| SSL | Auto-detected from `rediss://` URL prefix |

**Beat schedule (L46–52):**

| Task | Schedule |
|------|----------|
| `keep_alive_ping` | Every 300 seconds (5 minutes) |

> **Note:** `schedules_tick` is NOT a Celery beat task. It runs as a standalone Python process via `run_forever()`. Deploy as a separate Render Background Worker.

**Task registration (L64–65):**

```python
from . import tasks  # noqa
from .property_tasks import property_report  # noqa
```

---

## `schedules_tick.py` — Scheduled Report Executor (462 lines)

A standalone background process that runs every 60 seconds, finds due schedules, and enqueues `generate_report` Celery tasks.

**Deploy command:** `PYTHONPATH=./src poetry run python -m worker.schedules_tick`

### Architecture

```
┌─────────────────────────────────────┐
│  schedules_tick.py (standalone)     │
│  └── run_forever()                  │
│       ├── keep_api_warm()           │  every 300s
│       └── process_due_schedules()   │  every 60s
│            ├── Atomic claim (FOR UPDATE SKIP LOCKED)
│            ├── compute_next_run()
│            ├── enqueue_report() → celery.send_task("generate_report")
│            └── Insert schedule_run record
└─────────────────────────────────────┘
```

### Key Functions

| Name | Signature | Line | Description |
|------|-----------|------|-------------|
| `run_forever` | `()` | L437 | Main loop: tick every 60s + keep-alive pings |
| `process_due_schedules` | `()` | L309 | Find + claim + enqueue all due schedules |
| `compute_next_run` | `(cadence, weekly_dow, monthly_dom, send_hour, send_minute, timezone, from_time) → datetime` | L116 | Timezone-aware next-run calculation (weekly/monthly) |
| `enqueue_report` | `(schedule_id, account_id, report_type, city, zip_codes, lookback_days, filters) → tuple[str, str]` | L249 | Create `report_generations` record + send Celery task |
| `keep_api_warm` | `()` | L92 | Ping API `/health` to prevent Render cold starts |
| `safe_json_dumps` | `(obj)` | L70 | JSON serializer handling datetime objects |

### `process_due_schedules` Algorithm (L309–434)

```
1. Atomic claim: UPDATE ... FROM (SELECT ... FOR UPDATE SKIP LOCKED)
   - WHERE active=true AND (next_run_at IS NULL OR next_run_at <= NOW())
   - Stale locks (>5 min) are automatically reclaimed
   - LIMIT 100 per tick
2. For each claimed schedule:
   a. compute_next_run() → next UTC datetime
   b. enqueue_report() → creates report_generations row + Celery task
   c. INSERT schedule_runs audit record
   d. UPDATE schedules: last_run_at, next_run_at, clear lock
3. On per-schedule failure: clear lock, log error, continue to next
```

### `compute_next_run` Details (L116–246)

- **Cadences supported:** `weekly`, `monthly`
- **Timezone handling:** Uses `zoneinfo.ZoneInfo` (Python 3.11+ stdlib) — NOT pytz
- **DST handling:** Detects spring-forward gaps (hour doesn't exist) and fall-back ambiguity (hour exists twice, uses fold=0)
- **Weekly:** Converts `weekly_dow` (0=Sun, 6=Sat) to Python weekday (0=Mon, 6=Sun)
- **Monthly:** Caps day-of-month to 28 to avoid end-of-month issues
- **Returns:** Naive UTC datetime (for DB storage as `timestamptz`)

### `enqueue_report` Details (L249–306)

1. Looks up account defaults (default_theme_id, secondary_color)
2. Creates `report_generations` record with status `'queued'`
3. Sends Celery task `"generate_report"` with args `[run_id, account_id, report_type, params]`
4. Returns `(run_id, task_id)` tuple

### Configuration

| Env var | Default | Usage |
|---------|---------|-------|
| `DATABASE_URL` | (required) | PostgreSQL connection |
| `REDIS_URL` | `redis://localhost:6379/0` | Celery broker |
| `TICK_INTERVAL` | `60` | Seconds between ticks |
| `API_BASE_URL` | `https://reportscompany.onrender.com` | Keep-alive target |
| `KEEP_ALIVE_INTERVAL` | `300` | Seconds between API pings |

---

## `limit_checker.py` — Plan Limit Enforcement (Worker)

Enforces plan limits within the Celery worker context, before a report generation task does heavy work.

### `check_report_limit(account_id) → bool`

1. Queries `report_generations` count for current month
2. Resolves plan from `accounts` + `plans` tables
3. Returns `True` if allowed, `False` if limit exceeded
4. Logs decision (allow/warn/block)

This mirrors `services/usage.py` in the API layer but is available synchronously within Celery tasks.

---

## `cache.py` — Redis Caching Layer

Provides a Redis-backed cache for worker tasks.

### API

```python
cache.set(key, value, ttl_seconds=3600)
cache.get(key)    # Returns None if missing/expired
cache.delete(key)
```

**Key patterns used:**

| Pattern | TTL | Usage |
|---------|-----|-------|
| `market_stats:{city}:{date}` | 1 hour | Computed market medians per city per day |
| `simplyrets:{hash(params)}` | 30 min | Raw SimplyRETS response caching |
| `ai_insights:{hash(context)}` | 24 hours | OpenAI response caching |

---

## Key Functions / Classes (Summary)

| Module | Function | Line | Description |
|--------|----------|------|-------------|
| `app.py` | `celery` (instance) | L29 | Celery application (`"market_reports"`) |
| `schedules_tick.py` | `run_forever()` | L437 | Main entry point — infinite loop |
| `schedules_tick.py` | `process_due_schedules()` | L309 | Find + claim + enqueue due schedules |
| `schedules_tick.py` | `compute_next_run(...)` | L116 | Timezone-aware next-run calculation |
| `schedules_tick.py` | `enqueue_report(...)` | L249 | Create record + send Celery task |
| `schedules_tick.py` | `keep_api_warm()` | L92 | API ping to prevent cold starts |
| `limit_checker.py` | `check_report_limit(account_id)` | — | Boolean limit check for worker context |
| `cache.py` | `Cache` (class) | — | Redis cache wrapper with TTL support |

---

## Dependencies

### Internal

| Module | Usage |
|--------|-------|
| `tasks.py` | `generate_report` task enqueued by `schedules_tick` via `celery.send_task()` |
| `property_tasks/property_report.py` | Property report task, imported by `app.py` |

### External

| Library / Service | Usage |
|---|---|
| `celery` 5.4+ | Task queue framework |
| `redis` 5.0+ | Redis client (broker + cache) |
| `zoneinfo` (stdlib) | Timezone-aware schedule calculations |
| `psycopg` 3.2+ | PostgreSQL for schedule queries + report_generations inserts |
| `httpx` | API keep-alive HTTP pings |

---

## Failure Modes / Guardrails

| Scenario | Behaviour |
|----------|-----------|
| Schedule locked by another ticker | `FOR UPDATE SKIP LOCKED` — silently skipped |
| Stale lock (>5 minutes) | Automatically reclaimed by next tick |
| Redis connection failure | Process crashes; Render auto-restarts |
| DB connection failure in tick | Tick iteration fails; logged; next tick retried |
| Limit exceeded | `check_report_limit` returns `False`; task exits early |
| Cache miss | Fresh data fetched from SimplyRETS/OpenAI |
| Invalid timezone | Falls back to UTC with warning log |

---

## Tests / How to Validate

```bash
# Start worker locally
cd apps/worker
poetry run celery -A worker.app.celery worker -l info

# Start schedules tick as separate process
cd apps/worker
PYTHONPATH=./src poetry run python -m worker.schedules_tick

# QA delivery (exercises full tick + generate_report path)
python qa_deliver_reports.py --base-url $API_URL --token $TOKEN \
  --deliver-to qa@example.com --city Irvine
```

---

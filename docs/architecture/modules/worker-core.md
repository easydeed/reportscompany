# Module: Worker Core

> `apps/worker/src/worker/app.py`, `apps/worker/src/worker/schedules_tick.py`, `apps/worker/src/worker/limit_checker.py`, `apps/worker/src/worker/cache.py`

---

## Purpose

Core worker infrastructure: Celery application setup, the schedule tick executor, plan-limit enforcement in the worker context, and the Redis caching layer.

---

## `app.py` — Celery Application

Initialises the Celery application with Redis broker and result backend.

**Key configuration:**
```python
app = Celery(
    "worker",
    broker=settings.REDIS_URL,
    backend=settings.REDIS_URL,
    include=["worker.tasks"],
)
app.config_from_object(CeleryConfig)
```

**Beat schedule** (periodic tasks):
| Task | Schedule |
|------|----------|
| `keep_alive_ping` | Every 5 minutes |
| `schedules_tick` | Every minute |

---

## `schedules_tick.py` — Scheduled Report Executor

Runs every minute via Celery beat. Finds all schedules that are due to run and enqueues `generate_report` tasks.

### Algorithm

```
For each active schedule:
  1. Lock schedule row (SELECT FOR UPDATE SKIP LOCKED)
  2. Check if next_run_at <= now
  3. If due: create schedule_run record, enqueue generate_report task
  4. Advance next_run_at by cadence interval
  5. Release lock
```

**Cadences supported:** `daily`, `weekly`, `biweekly`, `monthly`

**Race prevention:** `SELECT FOR UPDATE SKIP LOCKED` ensures that if multiple worker instances are running, each schedule is processed exactly once.

**Timezone:** All schedules store `timezone` field; tick uses `pytz` to convert `next_run_at` to account timezone before comparison.

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

Provides a simple Redis-backed cache for worker tasks.

### API

```python
cache.set(key, value, ttl_seconds=3600)
cache.get(key)  # Returns None if missing/expired
cache.delete(key)
```

**Key patterns used:**

| Pattern | TTL | Usage |
|---------|-----|-------|
| `market_stats:{city}:{date}` | 1 hour | Computed market medians per city per day |
| `simplyrets:{hash(params)}` | 30 min | Raw SimplyRETS response caching |
| `ai_insights:{hash(context)}` | 24 hours | OpenAI response caching |

**Note:** Caching of SimplyRETS responses is **optional** and controlled by a feature flag in settings. AI insights are always cached to reduce OpenAI costs.

---

## Key Functions / Classes

| Module | Function | Description |
|--------|----------|-------------|
| `app.py` | `get_celery_app()` | Returns configured Celery instance |
| `schedules_tick.py` | `tick()` | Main tick function (called by beat) |
| `schedules_tick.py` | `_get_due_schedules(cur)` | Returns all schedules with `next_run_at <= now` |
| `schedules_tick.py` | `_advance_schedule(cur, schedule_id, cadence)` | Computes and writes next `next_run_at` |
| `limit_checker.py` | `check_report_limit(account_id)` | Boolean limit check for worker context |
| `cache.py` | `Cache` (class) | Redis cache wrapper with TTL support |

---

## Dependencies

### Internal
| Module | Usage |
|--------|-------|
| `tasks.py` | `generate_report` task enqueued by `schedules_tick` |
| `settings.py` | `REDIS_URL`, `DATABASE_URL`, plan limits |

### External
| Library / Service | Usage |
|---|---|
| `celery` | Task queue framework |
| `redis-py` | Redis client (broker + cache) |
| `pytz` | Timezone-aware schedule comparisons |
| `psycopg2` | PostgreSQL for schedule queries |

---

## Failure Modes / Guardrails

| Scenario | Behaviour |
|----------|-----------|
| Schedule locked by another worker | `SKIP LOCKED` — silently skipped, next tick handles it |
| Redis connection failure | Worker crashes on startup; systemd / Render restarts it |
| DB connection failure in tick | Tick task fails; logged; next tick retried |
| Limit exceeded | `check_report_limit` returns `False`; `generate_report` exits early with `status = "skipped_limit"` |
| Cache miss | Falls through; fresh data fetched from SimplyRETS/OpenAI |

---

## Tests / How to Validate

```bash
# Start worker locally
cd apps/worker
celery -A worker.app worker --loglevel=info

# Start beat scheduler
celery -A worker.app beat --loglevel=info

# Trigger tick manually (dev)
python -c "from worker.schedules_tick import tick; tick()"

# QA delivery (exercises full tick + generate_report path)
python qa_deliver_reports.py --base-url $API_URL --token $TOKEN \
  --deliver-to qa@example.com --city Irvine
```

---

## Change Log

| Date | Change |
|------|--------|
| 2026-01 | Added `ai_insights` cache (24h TTL) to reduce OpenAI costs |
| 2025-12 | Added `schedules_tick` beat task with `SELECT FOR UPDATE SKIP LOCKED` |
| 2025-11 | Added `limit_checker.py` for worker-context plan enforcement |
| 2025-10 | Initial `app.py` and `cache.py` |

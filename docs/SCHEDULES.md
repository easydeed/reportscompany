# TrendyReports Scheduling System

> Complete documentation for the automated report scheduling system.

**Version:** 2.0 (Current)

---

## Table of Contents

1. [Overview](#1-overview)
2. [Architecture](#2-architecture)
3. [Database Schema](#3-database-schema)
4. [API Endpoints](#4-api-endpoints)
5. [Smart Presets & Filters](#5-smart-presets--filters)
6. [Ticker Process](#6-ticker-process)
7. [Report Types](#7-report-types)
8. [Recipients](#8-recipients)
9. [Timezone Handling](#9-timezone-handling)
10. [Error Handling & Auto-Pause](#10-error-handling--auto-pause)
11. [Troubleshooting](#11-troubleshooting)

---

## 1. Overview

The scheduling system enables users to automate recurring report generation and email delivery. Key features:

- **Weekly & Monthly Cadences**: Flexible scheduling options
- **Timezone Support**: Schedule in user's local timezone
- **Typed Recipients**: Contacts, groups, sponsored agents, or manual emails
- **Usage Limit Integration**: Respects plan limits
- **Auto-Pause on Failures**: Prevents runaway failures
- **Race Condition Safe**: Multiple ticker instances can run safely

### Key Files

| File | Purpose |
|------|---------|
| `apps/worker/src/worker/schedules_tick.py` | Background ticker that finds due schedules |
| `apps/worker/src/worker/tasks.py` | Celery task for report generation |
| `apps/api/src/api/routes/schedules.py` | API endpoints for schedule management |
| `apps/web/components/schedules/schedule-wizard.tsx` | Frontend schedule creation wizard |

---

## 2. Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                         SCHEDULING FLOW                             │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  ┌─────────────┐     ┌──────────────┐     ┌─────────────────────┐  │
│  │   User      │     │   Database   │     │  Schedules Ticker   │  │
│  │   (Web UI)  │     │  (schedules  │     │  (Background Worker)│  │
│  │             │     │   table)     │     │                     │  │
│  └──────┬──────┘     └──────┬───────┘     └──────────┬──────────┘  │
│         │                   │                        │              │
│         │ 1. Create        │                        │              │
│         │    Schedule      │                        │              │
│         │─────────────────►│                        │              │
│         │                   │                        │              │
│         │                   │   2. Tick (60s)       │              │
│         │                   │◄───────────────────────│              │
│         │                   │                        │              │
│         │                   │   3. Find due         │              │
│         │                   │      schedules        │              │
│         │                   │   (atomic claim)      │              │
│         │                   │◄──────────────────────►│              │
│         │                   │                        │              │
│         │                   │                        │              │
│  ┌──────────────────────────┴────────────────────────┴────────┐    │
│  │                     Celery Worker                          │    │
│  │  ┌───────────────┐  ┌───────────────┐  ┌───────────────┐  │    │
│  │  │ generate_     │  │  render_pdf   │  │  send_email   │  │    │
│  │  │ report()      │──│               │──│               │  │    │
│  │  └───────────────┘  └───────────────┘  └───────────────┘  │    │
│  └────────────────────────────────────────────────────────────┘    │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
```

---

## 3. Database Schema

### schedules Table

```sql
CREATE TABLE schedules (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  account_id UUID NOT NULL REFERENCES accounts(id),
  name TEXT NOT NULL,
  report_type TEXT NOT NULL,
  
  -- Target area
  city TEXT,
  zip_codes TEXT[],
  lookback_days INT DEFAULT 30,
  
  -- Cadence
  cadence TEXT NOT NULL CHECK (cadence IN ('weekly','monthly')),
  weekly_dow INT,           -- 0=Sun .. 6=Sat
  monthly_dom INT,          -- 1..28
  send_hour INT DEFAULT 9,  -- 0..23
  send_minute INT DEFAULT 0,-- 0..59
  timezone TEXT DEFAULT 'UTC',
  
  -- Recipients (JSON-encoded typed recipients)
  recipients TEXT[] NOT NULL,
  include_attachment BOOLEAN DEFAULT FALSE,
  active BOOLEAN DEFAULT TRUE,
  
  -- Smart Preset Filters (NEW in v1.5)
  filters JSONB NOT NULL DEFAULT '{}'::jsonb,  -- minbeds, minbaths, minprice, maxprice, subtype
  
  -- Timing
  last_run_at TIMESTAMPTZ,
  next_run_at TIMESTAMPTZ,
  processing_locked_at TIMESTAMPTZ,  -- Race condition prevention
  
  -- Error tracking
  consecutive_failures INT DEFAULT 0,
  last_error TEXT,
  last_error_at TIMESTAMPTZ,
  
  created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Index for filter queries
CREATE INDEX idx_schedules_filters ON schedules USING gin (filters);
```

### schedule_runs Table

```sql
CREATE TABLE schedule_runs (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  schedule_id UUID NOT NULL REFERENCES schedules(id) ON DELETE CASCADE,
  report_run_id UUID,                -- Links to report_generations
  status TEXT DEFAULT 'queued',      -- queued|processing|completed|failed
  error TEXT,
  started_at TIMESTAMPTZ,
  finished_at TIMESTAMPTZ,
  created_at TIMESTAMPTZ DEFAULT NOW()
);
```

---

## 4. API Endpoints

### Create Schedule

```http
POST /v1/schedules
Content-Type: application/json

{
  "name": "Weekly Market Update",
  "report_type": "market_snapshot",
  "city": "San Francisco",
  "lookback_days": 30,
  "cadence": "weekly",
  "weekly_dow": 1,           // Monday
  "send_hour": 9,
  "send_minute": 0,
  "timezone": "America/Los_Angeles",
  "recipients": [
    {"type": "contact", "id": "uuid..."},
    {"type": "manual_email", "email": "agent@example.com"}
  ],
  "filters": {               // Smart Preset filters (optional)
    "minbeds": 2,
    "minbaths": 2,
    "subtype": "SingleFamilyResidence",
    "price_strategy": {      // NEW: Market-adaptive pricing
      "mode": "maxprice_pct_of_median_list",
      "value": 0.70          // 70% of median list price
    },
    "preset_display_name": "First-Time Buyer"  // Custom PDF header name
  },
  "active": true
}
```

### Filters Schema

| Field | Type | Description |
|-------|------|-------------|
| `minbeds` | int | Minimum bedrooms (0-10) |
| `minbaths` | int | Minimum bathrooms (0-10) |
| `minprice` | int | Minimum price (absolute fallback) |
| `maxprice` | int | Maximum price (absolute fallback) |
| `subtype` | string | `"SingleFamilyResidence"` or `"Condominium"` |
| `price_strategy` | object | **NEW**: Market-adaptive pricing (see below) |
| `preset_display_name` | string | **NEW**: Custom name for PDF headers |

### Price Strategy Schema (Market-Adaptive)

| Field | Type | Description |
|-------|------|-------------|
| `mode` | string | `"maxprice_pct_of_median_list"`, `"minprice_pct_of_median_list"`, etc. |
| `value` | float | Percentage as decimal (0.70 = 70%) |

**How it works**: At runtime, the worker fetches baseline listings for the area, computes the median price, and resolves the percentage to an actual dollar amount. This ensures presets work in any market.

### List Schedules

```http
GET /v1/schedules?active_only=true
```

### Get Schedule

```http
GET /v1/schedules/{schedule_id}
```

### Update Schedule

```http
PATCH /v1/schedules/{schedule_id}
Content-Type: application/json

{
  "send_hour": 10,
  "active": false
}
```

### Delete Schedule

```http
DELETE /v1/schedules/{schedule_id}
```

### List Schedule Runs

```http
GET /v1/schedules/{schedule_id}/runs?limit=50
```

---

## 5. Smart Presets & Filters

### Overview

Smart Presets provide pre-configured report templates for common audiences. When a user selects a preset, filters are automatically applied to narrow down listings.

**NEW in v2.0**: Presets now use **market-adaptive pricing** with percentage-of-median instead of fixed dollar amounts. This ensures presets work in any market (e.g., both Irvine and Riverside).

### Built-in Presets (Market-Adaptive)

| Preset | Report Type | Filters Applied |
|--------|-------------|-----------------|
| 🏠 First-Time Buyer | `new_listings_gallery` | 2+ beds, 2+ baths, **≤70% of median**, Single Family |
| 🏢 Condo Watch | `new_listings_gallery` | 1+ beds, 1+ baths, Condominium |
| 💎 Luxury Showcase | `featured_listings` | **≥150% of median**, Single Family |
| 👨‍👩‍👧‍👦 Family Homes | `new_listings` | 4+ beds, 2+ baths, Single Family |
| 📈 Investor Deals | `new_listings` | **≤50% of median** |

### How Market-Adaptive Pricing Works

```
1. User selects "First-Time Buyer" preset
   → filters.price_strategy = { mode: "maxprice_pct_of_median_list", value: 0.70 }
   → filters.preset_display_name = "First-Time Buyer"

2. Schedule is created & stored in DB

3. Ticker fires, passes filters to worker

4. Worker receives job for "Irvine":
   a. Fetches 500 baseline listings (90 days, same subtype)
   b. Computes median_list_price = $2,400,000
   c. Resolves: maxprice = $2,400,000 × 0.70 = $1,680,000
   d. Queries SimplyRETS with resolved maxprice

5. PDF header shows "First-Time Buyer — Irvine" (not "New Listings Gallery")
```

### Elastic Widening (Zero Results Safety Net)

If the resolved filters return < 6 results (4 for featured):

1. Worker widens price: 70% → 85% → 100% → 120%
2. PDF shows note: "Expanded price range to match local market conditions"

### Filter Flow

```
User → Preset Selection → filters JSON (with price_strategy) → schedules table
                                                                      ↓
                                                            Ticker (schedules_tick.py)
                                                                      ↓
                                                            Worker receives filters
                                                                      ↓
                                                  ┌─────────────────────────────────────┐
                                                  │ filter_resolver.py                   │
                                                  │ 1. compute_market_stats() → median   │
                                                  │ 2. resolve_filters() → actual $      │
                                                  │ 3. elastic_widen_filters() if needed │
                                                  └─────────────────────────────────────┘
                                                                      ↓
                                                            query_builders._filters()
                                                                      ↓
                                                  SimplyRETS API (?minbeds=2&maxprice=1680000...)
```

### Frontend Components

| File | Purpose |
|------|---------|
| `packages/ui/src/components/schedules/types.ts` | `PriceStrategy`, `ReportFilters`, `SMART_PRESETS` |
| `packages/ui/src/components/schedules/schedule-wizard.tsx` | Tabbed UI (Smart Presets / Standard Reports) |
| `packages/ui/src/components/new-report-wizard.tsx` | One-time report wizard (also uses presets) |

### Worker Components

| File | Purpose |
|------|---------|
| `apps/worker/src/worker/filter_resolver.py` | `compute_market_stats()`, `resolve_filters()`, `elastic_widen_filters()` |
| `apps/worker/src/worker/tasks.py` | Integration point for market-adaptive resolution |
| `apps/api/src/api/routes/schedules.py` | `PriceStrategy` and `ReportFilters` Pydantic models |

### Database Migration

```sql
-- Migration 0033_schedule_filters.sql
ALTER TABLE schedules
ADD COLUMN filters JSONB NOT NULL DEFAULT '{}'::jsonb;

CREATE INDEX idx_schedules_filters ON schedules USING gin (filters);

-- Note: filters JSONB now supports:
-- - minbeds, minbaths, minprice, maxprice, subtype (basic filters)
-- - price_strategy: { mode, value } (market-adaptive pricing)
-- - preset_display_name (custom PDF header name)
```

---

## 6. Ticker Process

The ticker (`schedules_tick.py`) runs as a separate background worker:

```bash
PYTHONPATH=./src poetry run python -m worker.schedules_tick
```

### Tick Cycle (Every 60 Seconds)

1. **Find Due Schedules**: Query schedules where `next_run_at <= NOW()` or `next_run_at IS NULL`

2. **Atomic Claim**: Uses `SELECT ... FOR UPDATE SKIP LOCKED` to prevent race conditions:
   - Multiple ticker instances can run safely
   - Each schedule is processed by exactly one ticker
   - Stale locks (>5 minutes) are automatically reclaimed

3. **Compute Next Run**: Calculate next execution time based on cadence and timezone

4. **Enqueue Report**: Create `report_generations` record and send to Celery

5. **Create Audit Record**: Insert into `schedule_runs` for history

6. **Update Schedule**: Set `last_run_at` and `next_run_at`

### Race Condition Prevention

```sql
WITH due AS (
    SELECT id FROM schedules
    WHERE active = true
      AND (next_run_at IS NULL OR next_run_at <= NOW())
      AND (processing_locked_at IS NULL 
           OR processing_locked_at < NOW() - INTERVAL '5 minutes')
    FOR UPDATE SKIP LOCKED
)
UPDATE schedules SET processing_locked_at = NOW()
FROM due WHERE schedules.id = due.id
RETURNING ...
```

---

## 7. Report Types

All report types supported by the scheduling system:

| Report Type | Description | Email Format |
|-------------|-------------|--------------|
| `market_snapshot` | Comprehensive market overview | Metrics + charts |
| `new_listings` | Recently listed properties | Count + metrics |
| `inventory` | Current active inventory | Table of listings |
| `closed` | Recent sold properties | Table of sales |
| `price_bands` | Price tier breakdown | Price band cards |
| `open_houses` | Upcoming open houses | List with dates |
| `new_listings_gallery` | Photo gallery of new listings | Image grid |
| `featured_listings` | Curated property showcase | Featured cards |

---

## 8. Recipients

### Recipient Types

| Type | Format | Description |
|------|--------|-------------|
| `contact` | `{"type":"contact","id":"uuid"}` | Contact from contacts table |
| `sponsored_agent` | `{"type":"sponsored_agent","id":"uuid"}` | Sponsored agent account |
| `group` | `{"type":"group","id":"uuid"}` | Contact group (expands to members) |
| `manual_email` | `{"type":"manual_email","email":"..."}` | Direct email address |

### Email Suppression

Recipients who unsubscribe are added to `email_suppressions` table and automatically filtered out before sending.

---

## 9. Timezone Handling

### How It Works

1. User specifies `send_hour`, `send_minute`, and `timezone` (e.g., "America/Los_Angeles")
2. Ticker computes next run time in user's local timezone
3. Converts to UTC for storage in `next_run_at`
4. Python's `ZoneInfo` handles DST transitions automatically

### DST Edge Cases

| Scenario | Behavior |
|----------|----------|
| **Spring Forward** (2 AM → 3 AM) | If 2:30 AM doesn't exist, skips to next valid time |
| **Fall Back** (2 AM → 1 AM) | Uses first occurrence of ambiguous time |

### Example

```python
# User schedules for 9:00 AM Pacific time on Mondays
timezone = "America/Los_Angeles"
send_hour = 9
send_minute = 0
weekly_dow = 1  # Monday

# During PST (UTC-8): next_run_at = 17:00 UTC
# During PDT (UTC-7): next_run_at = 16:00 UTC
```

---

## 10. Error Handling & Auto-Pause

### Failure Tracking

| Column | Description |
|--------|-------------|
| `consecutive_failures` | Count of consecutive failed runs |
| `last_error` | Error message from most recent failure (truncated to 2KB) |
| `last_error_at` | Timestamp of most recent failure |

### Auto-Pause Logic

After **3 consecutive failures**, the schedule is automatically paused:

```python
if consecutive_failures >= 3:
    UPDATE schedules SET active = false WHERE id = ...
```

### Recovery

On successful run, failure count is reset:

```python
UPDATE schedules SET consecutive_failures = 0, last_error = NULL
```

---

## 11. Troubleshooting

### Schedule Not Running

1. **Check `active` status**: Schedule may be paused
2. **Check `next_run_at`**: Should be in the past
3. **Check `processing_locked_at`**: May be stuck in processing
4. **Check `consecutive_failures`**: May have been auto-paused

### Duplicate Reports

This should not happen with the race condition fix. If it does:

1. Check if multiple ticker instances are running with old code
2. Verify `processing_locked_at` column exists
3. Check `schedule_runs` table for duplicates

### Wrong Execution Time

1. Verify `timezone` is correct IANA timezone
2. Check for DST transition near scheduled time
3. Verify server time is correct (UTC)

### Email Not Sent

1. Check `email_log` table for status
2. Verify recipients not in `email_suppressions`
3. Check SendGrid API key is configured

---

## Quick Reference

### Start Ticker (Development)

```bash
cd apps/worker
PYTHONPATH=./src poetry run python -m worker.schedules_tick
```

### Start Celery Worker

```bash
cd apps/worker
poetry run celery -A worker.app.celery worker -l info
```

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `DATABASE_URL` | PostgreSQL connection string | Required |
| `REDIS_URL` | Redis URL for Celery | `redis://localhost:6379/0` |
| `TICK_INTERVAL` | Seconds between ticker runs | `60` |
| `SENDGRID_API_KEY` | SendGrid API key | Required for email |

---

*This document is the source of truth for TrendyReports scheduling system.*


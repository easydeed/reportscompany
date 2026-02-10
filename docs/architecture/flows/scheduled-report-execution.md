# Scheduled Report Execution Flow

## Overview

Automated execution of recurring market reports based on user-defined schedules.

## Flow

```
WORKER: schedules_tick.py (runs every 60 seconds)
  1. Query schedules WHERE next_run_at <= NOW() AND active = true
  2. For each due schedule:
         |
         v
  3. Create schedule_run record (status: started)
  4. Enqueue generate_report Celery task
  5. Calculate and set next_run_at
         |
         | Redis queue -> Celery
         v
WORKER: generate_report task
  1. Execute standard market report pipeline
  2. On completion:
     a. Update schedule_run (status: completed)
     b. Reset consecutive_failures = 0
     c. Send email to schedule.recipients
  3. On failure:
     a. Update schedule_run (status: failed, error)
     b. Increment consecutive_failures
     c. If consecutive_failures >= 3 -> set active = false (auto-pause)
```

## Scheduling Logic

### Cadence Types

| Cadence | Trigger Condition |
|---------|-------------------|
| `daily` | Every day at `send_hour:send_minute` |
| `weekly` | Every week on `weekly_dow` at `send_hour:send_minute` |
| `monthly` | Every month on `monthly_dom` at `send_hour:send_minute` |

### Timezone Handling

- `send_hour` and `send_minute` are stored in the schedule's configured timezone
- `next_run_at` is calculated in UTC based on the timezone offset
- Daylight saving time transitions are handled during next_run_at calculation

### Tick Frequency

- The scheduler tick runs every 60 seconds
- Each tick queries for all overdue schedules in a single batch
- Multiple schedules can be enqueued in the same tick cycle

## Auto-Pause Behavior

After 3 consecutive failures, a schedule is automatically paused (`active = false`):

1. First failure: `consecutive_failures = 1`, schedule remains active
2. Second failure: `consecutive_failures = 2`, schedule remains active
3. Third failure: `consecutive_failures = 3`, schedule is paused

The user must manually re-enable the schedule after investigating the failures.

## Key Files

| Service | File | Purpose |
|---------|------|---------|
| Worker | `schedules_tick.py` | Scheduler tick loop |
| Worker | `tasks.py` -> `generate_report` | Report generation pipeline |
| Worker | `email/send.py` | Recipient email delivery |
| API | `routes/schedules.py` | Schedule CRUD endpoints |

## Failure Modes

| Failure | Handling |
|---------|----------|
| Scheduler tick crashes | Restarts on next 60-second cycle; overdue schedules caught up |
| Report generation fails | schedule_run marked failed, consecutive_failures incremented |
| 3 consecutive failures | Schedule auto-paused, user notified |
| Email delivery fails | Logged to email_log, does not count as schedule failure |

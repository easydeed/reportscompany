# LR-027 design rev 2: readiness and operator alerts

Branch `fix/lr-027-operational-alerts` · Gate PILOT · design review first, then code.
Ticket: `03-operations-and-acceptance.md` LR-027. Facts below are read from main `688abc1e`.

## 0. What changed from rev 1 (Codex AMEND at `1e0b73cc`)

| # | Codex | Rev 2 |
|---|---|---|
| 1 | Production runs no Celery Beat; the heartbeat and the monitor need a real singleton producer, and the outside pinger must stay independent. | **No Beat.** The standalone ticker, already a singleton, is the producer. It runs the monitor on its own thread, so the monitor no longer waits behind renders and can report a dead worker. It also publishes a heartbeat work item that proves the queue is consumed. The pinger reads `/ready` from the API, so it does not depend on the ticker. See section 3. |
| 2 | Schema readiness must allow an additive rollout and an older binary during rollback, and every wait must be bounded. | `/ready` uses the existing `schema_guard.check`: the required row is present, and newer migrations are fine. Pool acquisition, connection, query and Redis each have a budget, and the whole check is single-flight with a cache. See section 3. |
| 3 | Schedule-level blocks with no `schedule_runs` row; suppression, refusal and unknown outcome kept separate; one incident per attempt; independent channels. | New signals: `schedule_blocked`, and `schedule_overdue` for the ticker's exception path, which records nothing. An outcome-class table splits the signals. Incidents are deduplicated by attempt identity. Notification state is per channel, so an SMS retry never re-sends a confirmed email. See sections 4 and 5. |
| 4 | `webhook_deliveries` holds completed attempts, not a queue. | Correct, and rev 1 also wrongly called it Stripe's: the table holds **outbound report webhooks to customers** (`tasks.py:511`, migration 0002). Rev 2 has only a recent-failed-attempts signal. Pending counts are dropped, and the Stripe backlog is deferred until a durable source is named. See section 4. |
| 5 | Acceptance keeps one confirmed alert and one recovery per configured path, as redacted evidence; destinations stay in Render. | Adopted as the closure rule. See section 7. |

## 1. What exists today

| Piece | Today | Gap |
|---|---|---|
| `GET /health` (`routes/health.py`) | Static `{"ok": true, "schema": REQUIRED_MIGRATION}`. Touches nothing. | Correct for liveness and stays that way (section 3). |
| `GET /v1/admin/system/health` | Admin-only DB `SELECT 1`, size, Redis. | Needs a session; nothing alerts on it. |
| Production processes (Codex, confirmed workspace) | API, a plain Celery worker, the bridge, the standalone schedule ticker. **No service runs Beat.** | `app.py`'s `beat_schedule` (`keep_alive_ping`, every 300 s) **never fires in production**. Rev 1 built on it; rev 2 does not. Filed in section 10. |
| Ticker (`schedules_tick.py`) | `while True` every `TICK_INTERVAL` (60 s): `keep_api_warm`, `process_due_schedules`, `sweep_stale_runs`. It already publishes Celery tasks (`dispatch_report` → `celery.send_task`), and it reads across accounts on its own connection, as the sweep does. | Leaves no heartbeat; when it stops, schedules stop silently. |
| Schedule-level blocks | `blocked_unverified`: an `email_log` row with `schedule_id` and **no** `schedule_runs` row (`record_unverified_skip`). An exception in `process_due_schedules` clears the lock and logs, but **records nothing**, and `next_run_at` does not advance, so the schedule retries every tick. | Rev 1 watched only `schedule_runs` and could see neither. |
| `email_log.status` (migration 0068 comment) | Deliveries: `sending`, `sent`, `failed`, `needs_review`. Not deliveries: `suppressed`, `duplicate_suppressed`, `blocked_unverified`, `queued`. Historical only: `unknown`. `resolution` records the operator's decision on a held attempt. | #319 shows this recorded value in both admin email logs, filterable by status, so alert links can open that view. |
| `webhook_deliveries` (migration 0002) | One row per **completed** outbound report-webhook attempt (`response_status`, `error`). | No queue, so no pending count is possible. |
| Email / SMS | SendGrid (API `services/email.py`, worker `email/providers/sendgrid.py`); Twilio (`worker/sms/send.py`). | Reused for operator alerts. |

## 2. Decisions recorded

- **Channels (Jerry):** email plus SMS to one named operator. **D1:** alert email goes through **SendGrid**, not Resend; the app does not use Resend. **[JERRY] confirm.**
- **Outside check (Jerry):** a free external pinger polls `/ready`. It is the only path that alerts when the ticker, the worker, Redis or SendGrid is down, so it must not depend on any of them.
- **Values never invented:** destinations are Render environment variables Jerry sets (section 6). Until they are set, the monitor records alerts and sends nothing.

## 3. Readiness, heartbeats and the singleton producer

**`/health` is unchanged and stays Render's health-check path.** If Render restarted on `/ready`, a database or Redis outage would become a restart loop that fixes nothing.

### `GET /ready` (API, unauthenticated, a public prefix, never 401)

| Check | How | Budget | Critical |
|---|---|---|---|
| `database` | Take a connection from the API pool with **`timeout=1.0`**; a pool that cannot provide one within 1 s is itself "failing", because requests would fail too. In one transaction: `SET LOCAL statement_timeout = '1000ms'`, `SET LOCAL lock_timeout = '250ms'`, then **`schema_guard.check(cur)`**. | acquisition ≤ 1 s, then each statement ≤ 1 s | yes |
| `redis` | `PING` on a client with `socket_connect_timeout=0.5`, `socket_timeout=0.5` | ≤ 0.5 s connect, ≤ 0.5 s read | yes |
| `ticker` | age of `ops:heartbeat:ticker` | from the Redis read | yes, stale after **3 min** |
| `worker` | age of `ops:heartbeat:worker`, read with the length of the Celery queue (`LLEN celery`) | from the Redis read | see below |

- **The schema check is compatible in both directions.** `schema_guard.check` asks only whether `REQUIRED_MIGRATION` is recorded; it is the same function that gates startup today.
  - A database **ahead** of the binary is ready: either a newer compatible migration landed, or this is an older binary after a rollback.
  - A database **behind** it reports `schema: behind`.
  - Rev 1 compared against the newest row, which would have reported a correct rollback as down.
  - An older binary from before LR-027 has no `/ready` at all, so the pinger sees 404 and alerts. That is the correct outcome, and the rollout notes say so.
- **Single-flight with a cache:** one evaluation at a time per process. Concurrent callers share it, and the result is cached for **10 s**. A hung dependency therefore costs one bounded check, not one per request. The worst-case wall time is about 3 s.
- **Status:** 200 when every critical check passes, otherwise **503**.
- **Response body:** per check, `{"status": "ok"|"failing"|"stale"|"behind"|"backlog", "age_s": n}`.
  - No hostnames, DSNs, exception text, IDs or queue contents.
  - It is public, so it tells an outsider only "ready or not, and which part".

### The singleton producer is the ticker, not Beat

- **Ticker heartbeat:** at the end of each loop that completes, the ticker runs `SET ops:heartbeat:ticker <unix time> EX 600`. A loop that raises does not refresh it, so a crash-looping ticker also goes stale.
- **Worker heartbeat (a work item):** each tick, the ticker publishes `ops_heartbeat`, with `expires=120` so a stale copy is dropped, not run late. The worker task sets `ops:heartbeat:worker`. The task is idempotent: running twice only rewrites one key. A fresh key proves a worker is consuming the queue.
- **Queue-aware worker state.** This is the queue-latency point. The worker runs Celery's default concurrency, and the 26-schedule burst on record took about 18 minutes to drain (`STALE_QUEUED_MINUTES`). A heartbeat waits behind that like any task. So:

  | Heartbeat age | `LLEN celery` | State |
  |---|---|---|
  | ≤ 5 min | any | `ok` |
  | > 5 min | 0 | `stale`: nothing is queued, yet nothing ran. **The worker is down.** Critical. |
  | > 5 min, ≤ 30 min | > 0 | `backlog`: reports are delayed. Not critical in `/ready`, but it is the `worker_backlog` signal. |
  | > 30 min | > 0 | `stale`: the backlog is past the queued-run horizon. Critical. |

- **The monitor runs inside the ticker process, on a daemon thread.** Rev 1 had it as a Beat task.
  - **Why not a queued task, Codex's other option:** a monitor in the render queue would sit behind the same burst and could never report a dead worker. On the ticker it reports `worker_stale` and `worker_backlog` itself. Rev 1 admitted the worker could not send `worker_stale` about itself; that gap is now closed.
  - **Singleton:** before each run the thread takes `SET ops:monitor:lease <ticker id> NX EX 290`. A second ticker instance, or an overlap after a restart, finds the lease held and skips. A run therefore happens at most once every 5 minutes, across any number of tickers.
  - **Bounded:**
    - each signal query runs with `statement_timeout` 5 s, on its own connection with `connect_timeout=5`;
    - each provider call times out after 10 s;
    - each run has a budget of **90 s**; notifications not yet sent wait for the next run;
    - a new run is never started while the previous thread is alive.
  - **Isolated:** the dispatch loop never waits on the monitor, and a monitor exception is logged and never reaches the loop.
- **When the producer itself is lost:** the ticker heartbeat goes stale, and so does the worker heartbeat, because the ticker publishes it. The monitor stops. The **pinger** still reads `/ready` from the API, which needs neither the ticker nor the worker, sees `ticker: stale` and returns 503. That independence is what keeps a lost producer visible.

## 4. Customer-outcome signals

### Outcome classes (the separation Codex asked for)

| Class | `email_log` source | Counts toward |
|---|---|---|
| **Delivered to the provider** | `sent` | the denominator only |
| **Provider refusal, documented** | `failed` where the writer recorded the provider's own answer: the scheduled path's `REJECTED` attempt (`scheduled_runs.py`, with the provider's status code) and the consumer path's `SEND_REFUSED` (`tasks.py`) | `provider_refusals` |
| **Not sent, our side** | `failed` with no provider answer: connection refused, no API key, no recipients | `send_not_attempted` |
| **Outcome unknown** | `needs_review` with `resolution IS NULL` (LR-023/LR-019) | `send_needs_review` |
| **Not a delivery** | `suppressed`, `duplicate_suppressed`, `queued` | **nothing**: never a failure and never in a rate's denominator |
| **Schedule-level block** | `blocked_unverified` | `schedule_blocked` |

The legacy multi-attempt send path stores **synthesized** codes: 500 or 504 for transport errors, and 400 for "No recipients". So `response_code` alone does not prove the provider answered. The code task classifies each `email_log` writer at its source; a test covers each one. A row that cannot be classified is counted as "not sent, our side", never as a refusal.

### Signals

The thresholds are proposals. **[JERRY] approves them after observe mode** (section 8).

| Key | Source | Proposed threshold | SMS? | Consequence line |
|---|---|---|---|---|
| `schedule_overdue` | `schedules` where `active` and `COALESCE(next_run_at, created_at) < now() - 15 min`. This catches the ticker's exception path, which records nothing, and also a stopped ticker. The 43 inactive schedules are excluded by `active`. | **any** | yes | "A scheduled report is overdue and has not been sent." |
| `schedule_blocked` | distinct `schedule_id`s with `email_log.status='blocked_unverified'` in the last 24 h | **any new schedule** | email only | "A schedule is being skipped: no user on the account has confirmed their email." |
| `dispatch_stranded` | `schedule_runs`, `recovery_tracked`, `status IN ('queued','processing')`, older than the horizon or `dispatch_attempts >= 6` (LR-023) | **any** | yes | "A scheduled report did not go out and the sweep has given up." |
| `send_needs_review` | unknown outcomes, deduplicated (below) | **any new attempt** | yes | "A send's outcome is unknown; it will not be retried. Someone must decide whether it arrived." |
| `provider_refusals` | documented refusals in the last hour | **≥ 10 and ≥ 10% of that hour's deliveries** | yes | "SendGrid is refusing mail." |
| `send_not_attempted` | "not sent, our side" in the last hour | **≥ 3** | yes | "Sends are failing before reaching SendGrid (configuration or network)." |
| `report_stuck` | `report_generations.status='processing'` older than **30 min** | **any** | yes | "A report has been processing for over 30 minutes." |
| `report_failures` | `report_generations.status='failed'` in the last hour | **≥ 5 and ≥ 20%** | yes | "Reports are failing to render." |
| `consumer_delivery_stuck` | LR-020/021/022 stamps, as in rev 1 | **any** | yes | "A home-value report or its agent notification has not been delivered." |
| `report_webhook_failures` | `webhook_deliveries` attempts in the last hour with `error IS NOT NULL` or `response_status` outside 2xx, as distinct `webhook_id`s | **any webhook failing ≥ 3 times** | email only | "A customer's report webhook is failing." |
| `ticker_stale` | the ticker heartbeat, as seen by the monitor | 3 min | yes | "Scheduled sends have stopped." This reaches the operator only while the monitor thread runs; a dead ticker is the pinger's alert. |
| `worker_stale`, `worker_backlog` | section 3 | as in section 3 | yes / email only | "Reports are not being processed." / "Reports are delayed behind a backlog." |

**Not promised:** a Stripe webhook backlog. `webhook_deliveries` is not Stripe's, and no durable Stripe event queue has been identified. It is deferred, during the sponsored pilot, until one is (section 10).

### One incident per attempt

The same scheduled attempt can appear in **both** `schedule_runs` (`needs_review`) and `email_log` (`needs_review`, with `report_id` = `schedule_runs.report_run_id`).
- The monitor gives every member an **attempt identity**: `run:<report_run_id>` for anything scheduled, joined across the two tables, and `email:<email_log.id>` otherwise.
- Counts are of distinct identities, and the sample IDs are deduplicated identities.
- "New" means an identity not already listed on the open incident.

The same rule applies to `schedule_overdue` and `schedule_blocked`: the identity is `schedule:<id>`. A schedule overdue for six hours is one member, not 360.

## 5. Delivery, noise and recovery

- **State:** one additive migration creates two tables, owned by the monitor.
  - **`ops_alerts`**, one row per incident: `key`, `opened_at`, `resolved_at`, `last_value`, `members` (attempt identities, capped at 50 stored and 5 shown), `last_evaluated_at`.
  - **`ops_alert_notifications`**, one row per incident × event × channel:
    - key `(alert_id, event, channel)`, where `event` is `open`, `renotify:<n>` or `resolved`, and `channel` is `email` or `sms`;
    - columns `status` (`pending`, `sent`, `failed`), `attempts`, `last_attempt_at`, `provider_message_id`, `last_error_class` (a class only, never provider text).
- **Channels are tracked separately.** Each run sends only rows that are `pending`, or `failed` with fewer than 5 attempts.
  - A confirmed email (`sent`) is never sent again when the SMS for the same event is retried, and the reverse.
  - The insert uses `ON CONFLICT DO NOTHING` on the unique key, so a repeated or overlapping run cannot create a second notification for the same event and channel.
  - An event whose provider outcome is unknown is marked `sent`, not retried: a duplicate operator alert costs less than a pattern of resending.
- **Rules:**
  - **Open:** email and SMS, subject to the per-key "SMS?" column.
  - **Still failing:** re-notify every **6 h**.
  - **Recovered:** one `resolved` event.
  - **Flapping:** re-trips within 30 min re-open with email only.
  - **Global cap:** **10 SMS per hour**; past it, one "N more alerts; see email".
- **Alert body:**
  - key, consequence line, counts and up to 5 attempt identities;
  - first seen;
  - the runbook link, and the admin view where one exists, such as #319's email log filtered to the class.
  - SMS carries the first two lines and the link.
- **Never in alert bodies or telemetry:** recipient emails or phones, consumer or owner names, addresses, tokens, secrets or payment bodies. A test renders every key's body from rows *full* of such data and asserts none of it appears.

## 6. Configuration

| Variable | Where | Meaning |
|---|---|---|
| `OPS_ALERTS_ENABLED` | ticker, worker | `0` (default) = observe: evaluate, record, log, **send nothing**. `1` = send. |
| `OPS_ALERT_EMAIL` | ticker | **[JERRY]** the operator's address. Unset: no email. |
| `OPS_ALERT_SMS_TO` | ticker | **[JERRY]** E.164 number. Unset: no SMS. |
| `OPS_PUBLIC_BASE` | ticker | Base for links; defaults to `WEB_BASE`. |

The destinations are set in Render, never in the repo, chat or evidence. Thresholds are named constants in one module, each with its approval date.

## 7. Acceptance

**Injected failures in the isolated stack.** This uses the LR-023 live harness (`scripts/live/lr023/`): real Redis, a real Celery worker and the real ticker, against a local database, with a fake SendGrid and a fake Twilio. **It never points at production.**

| Inject | Expect |
|---|---|
| Stop PostgreSQL | `/ready` 503 `database: failing` within its budget; `/health` 200; no restart; the monitor's queries fail and the ticker loop keeps running. Recovery: `resolved`. |
| Exhaust the API pool | `/ready` reports `database: failing` after the 1 s acquisition budget, not after 10 s. |
| Database one migration ahead (rollback) | `/ready` 200, with schema `ok`. |
| Database behind | `/ready` 503 `schema: behind`. |
| Stop Redis | `/ready` 503 `redis: failing`; the pinger's view is recorded. |
| Stop the worker | Heartbeat stale with an empty queue, so `worker: stale` and `worker_stale` sent **by the ticker**. |
| Flood the queue (a 26-run burst) | `worker: backlog` and `worker_backlog`, **not** `worker_stale`. |
| Stop the ticker | `/ready` `ticker: stale`. The monitor stops with it, so the alert path is the pinger. Recorded. |
| Two tickers | Exactly one monitor run per window (the lease); one notification per event and channel. |
| Make a schedule raise inside `process_due_schedules` | `schedule_overdue` with `schedule:<id>`; one member however many ticks fail. |
| Unverified account with a due schedule | `schedule_blocked`, email only. |
| Strand a tracked run | `dispatch_stranded` with its run. |
| Unknown outcome on a scheduled send (in both tables) | `send_needs_review` with **one** member, `run:<id>`. |
| Fake SendGrid 4xx burst | `provider_refusals` over threshold, and not below it. Suppressed and duplicate-suppressed rows in the same window change nothing. |
| SendGrid key unset | `send_not_attempted`, not `provider_refusals`. |
| Failing customer webhook | `report_webhook_failures`. |
| Fake Twilio fails, fake SendGrid succeeds | The email is `sent` once. The SMS is retried on later runs. **No second email.** |
| Auth rejection on an API route | No alert; `/ready` unaffected. |
| Flapping, then recovery | One SMS, the email re-open rule, one `resolved`; the SMS cap holds under a burst. |

Every captured body passes the privacy test.

**Closure, from production (Codex point 5).** The closing evidence is **one confirmed alert and one recovery for each configured path**: email, SMS and the pinger. Each is recorded as redacted evidence: the time, the key, the channel, `provider_message_id` or the pinger's event ID, and the destination masked (for example `j***@…`, `+1•••••1234`). Destinations themselves stay in Render.
- **Email and SMS:** `POST /v1/admin/ops/test-alert` (admin only) opens a labelled test incident and resolves it on the next run. That produces the alert and the recovery through the real code path. Jerry confirms receipt.
- **Pinger:** a planned pause of the check, or a controlled `/ready` 503 in a maintenance window, then the recovery. **[JERRY]** chooses which.

No live alert is sent before code PASS, and none was sent during this design review.

## 8. Rollout

1. Code PASS, then the migration (two additive tables) through the usual runbook; Jerry applies it.
   - The monitor tolerates the tables being absent, for example under `SCHEMA_BEHIND_ACKNOWLEDGED`: it logs and skips, and never crashes the ticker.
2. Deploy with `OPS_ALERTS_ENABLED=0`. Observe for **48 h**, compare the proposed thresholds with real traffic, and adjust; Jerry approves the values.
3. Jerry sets the destinations and runs the test alert; the email and SMS evidence is recorded (section 7).
4. Jerry creates the pinger: `GET https://<api>/ready` every 5 min, alerting on 2 consecutive failures. Its alert and recovery are recorded.
5. Confirm Render's health-check path is `/health`, not `/ready`.
6. `OPS_ALERTS_ENABLED=1`.
7. **Rollback:** reverting the binary leaves the two tables unused; the older code ignores them. `/ready` 404s until the redeploy, and the pinger reports that by design.

**Cost:** SendGrid is within the plan. Twilio is about a cent per SMS, capped at 10 an hour. The pinger is on a free tier. The database cost is about 12 bounded queries every 5 minutes on one connection.

## 9. Open for Jerry
1. **D1:** SendGrid for alert email.
2. Approve the thresholds, after observe mode.
3. The operator's email and phone, set in Render.
4. The pinger service and account, and how its alert is exercised (section 7).
5. Quiet hours or a second contact, if any.

## 10. Not in this ticket, and found while revising
- LR-026, LR-028 and dashboards; paging rotations.
- **Stripe webhook backlog:** deferred during the sponsored pilot until a durable Stripe event source is identified. No count is promised.
- **Found, to file:** `app.py`'s `beat_schedule` (`keep_alive_ping`) never runs, because production has no Beat. The ticker's `keep_api_warm` already does that job. Remove it, or label it, in a cleanup PR.
- **Found, to file:** the legacy multi-attempt SendGrid path stores synthesized response codes (500, 504, 400) that look like provider answers. Section 4 handles it for alerts; the stored data stays ambiguous.

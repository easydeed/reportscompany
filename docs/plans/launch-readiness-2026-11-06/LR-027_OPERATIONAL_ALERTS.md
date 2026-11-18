# LR-027 design rev 1: readiness and operator alerts

Branch `fix/lr-027-operational-alerts` · Gate PILOT · design review first, then code.
Ticket: `03-operations-and-acceptance.md` LR-027. Codex supplies the webhook-backlog signal (LR-011); everything else here is Claude's.

## 1. What exists today (read from the code, main `ba551508`)

| Piece | Today | Gap |
|---|---|---|
| `GET /health` (`routes/health.py`) | Static `{"ok": true, "schema": REQUIRED_MIGRATION}`. Touches nothing. | Says the process is up, not that it can do work. That is right for liveness and must stay so (section 3). |
| `GET /v1/admin/system/health` | Admin-only DB `SELECT 1`, DB size, Redis status. | Needs an admin session, so an outside pinger can't use it, and nothing alerts on it. |
| Ticker (`schedules_tick.py`) | `while True` loop, `TICK_INTERVAL` 60 s. | Leaves no heartbeat. A stopped ticker is silent: schedules just stop. |
| Worker beat (`app.py`) | One task, `keep_alive_ping`, every 300 s. | Proves nothing to anyone. |
| Failure states already recorded | LR-023: `schedule_runs.status='needs_review'`, `send_claimed_at`, `dispatch_attempts`, `last_dispatch_error`. LR-020/021/022: `consumer_reports.delivery_claimed_at`, `agent_notify_status`/`agent_notify_error`, `pdf_status`/`pdf_error`. `email_log.status` (`needs_review`, rejected/failed) with `resolution`. `report_generations.status`/`error`. | All the states exist. Nobody is told about them. |
| Email | **SendGrid**, in the API (`services/email.py`) and the worker (`email/providers/sendgrid.py`). `RESEND_API_KEY` is marked "Deprecated, unused" (`settings.py:36`). | See decision D1. |
| SMS | Twilio (`worker/sms/send.py`). | Reused for operator SMS. |

## 2. Decisions recorded, and one correction

- **Channels (Jerry):** email plus SMS to a named operator. **D1, a correction for Jerry:** the option I offered said "Email (Resend)", but the app does not use Resend; it sends through SendGrid. This design uses **SendGrid** for alert email. It is already configured on both services, and the ticket says to use the existing stack before adding a service. Twilio SMS is the second channel. That pairing also covers the case where SendGrid itself is failing: an alert about SendGrid refusals still reaches the phone. **[JERRY] confirm SendGrid.**
- **Outside check (Jerry):** a free external uptime pinger polls the new `/ready`. Jerry creates the account. It is the only thing that can alert when *everything* is down, including the worker that sends our own alerts.
- **Values never invented here:** the operator's email and phone are environment variables Jerry sets on Render (`OPS_ALERT_EMAIL`, `OPS_ALERT_SMS_TO`). Until set, alerts are logged and not sent (section 6).

## 3. Liveness stays cheap; readiness is new and bounded

**`/health` is unchanged and remains Render's health-check path.** This is the "no destructive restart loop" rule: if Render restarted on `/ready`, a database or Redis outage would restart every API instance repeatedly and fix nothing. `/ready` is for humans and the pinger, never for Render's restarts. Rollout includes checking Render's health-check setting (section 8).

**`GET /ready`** (API, unauthenticated, added to the public prefixes so it can never answer 401):

| Check | How | Budget | Critical |
|---|---|---|---|
| `database` | `SELECT 1`, then the newest `schema_migrations` row equals `REQUIRED_MIGRATION` | 1.0 s statement timeout | yes |
| `redis` | `PING` | 0.5 s socket timeout | yes |
| `ticker` | age of Redis key `ops:heartbeat:ticker`, written by the ticker every tick with a 10-minute TTL | from the Redis read | yes, stale after 3 min (3 ticks) |
| `worker` | age of `ops:heartbeat:worker`, written by a beat task every 60 s. It proves beat runs *and* a worker consumes the queue | from the Redis read | yes, stale after 5 min |

- **Status:** 200 when every critical check passes, otherwise **503**.
- **Response body:** a per-check `{"status": "ok"|"failing"|"stale", "age_s": n}` plus `schema`.
  - It contains no hostnames, DSNs, exception text, counts or IDs. It's public, so it tells an outsider only "ready or not, and which part".
- **Load:** the result is cached in-process for 10 s, so a pinger, or anyone else, can't turn `/ready` into database load.
- **Auth:** auth failures are never part of it. It has no credential to reject, so readiness can't be confused with an auth problem (ticket acceptance).

**Heartbeats:** the ticker sets `ops:heartbeat:ticker = <unix time>` at the end of each successful loop. A loop that raises does not refresh it, so a crash-looping ticker goes stale too. The worker's new beat task `ops_heartbeat` (60 s) sets `ops:heartbeat:worker`. Both are one Redis `SET … EX 600`. If Redis is down, both go stale and `/ready` already reports `redis: failing`.

## 4. Customer-outcome signals (the monitor)

A beat task `ops_monitor` runs every **5 minutes** in the existing worker. No new service. Each signal is one bounded read query (`statement_timeout` 5 s). The thresholds are proposals, shown in **bold**. **[JERRY] approve or change them; observe mode (section 8) measures them against real traffic before any are enabled.**

| Key | Signal (source) | Proposed threshold | Consequence line in the alert |
|---|---|---|---|
| `dispatch_stranded` | `schedule_runs` with `recovery_tracked` and `status IN ('queued','processing')`, older than the horizon or with `dispatch_attempts >= 6` (LR-023) | **any** | "Scheduled report(s) did not go out and the sweep has given up." |
| `send_needs_review` | `schedule_runs.status='needs_review'` or `email_log.status='needs_review'` with `resolution IS NULL` (LR-023/LR-019) | **any new row** | "A send's outcome is unknown; it will not be retried. Someone must decide whether it reached the recipient." |
| `report_stuck` | `report_generations.status='processing'` older than **30 min** | **any** | "A report has been processing for over 30 minutes; the agent is still waiting." |
| `report_failures` | `report_generations.status='failed'` in the last hour | **≥ 5, and ≥ 20% of that hour's reports** | "Reports are failing to render." |
| `consumer_delivery_stuck` | `consumer_reports.delivery_claimed_at` older than **15 min** with no email/SMS sent stamp; `agent_notify_status IN ('failed','needs_review')`; `pdf_status` failed or claimed over **15 min** (LR-020/021/022) | **any** | "A home-value report or its agent notification has not been delivered." |
| `provider_refusals` | `email_log` rejected/failed in the last hour (SendGrid) | **≥ 10, and ≥ 10% of that hour's sends** | "SendGrid is refusing mail." |
| `webhook_backlog` | **Codex (LR-011):** `webhook_deliveries` failures and backlog via an agreed function `ops_signals.webhook_backlog(cur) -> (count, oldest_age_s, sample_ids)` | set with Codex | "Stripe webhooks are failing or backed up; plan changes may not have applied." |
| `ticker_stale`, `worker_stale` | the heartbeats from section 3, checked by the monitor too | 3 min, 5 min | "Scheduled sends have stopped." / "Reports are not being processed." |

**`worker_stale` can't be sent by the worker it describes.** When the worker or Redis is down, `ops_monitor` isn't running. That case is covered by the external pinger seeing `/ready` 503, which is why the pinger is part of this design and not an extra.

## 5. Delivery, noise and recovery

- **State:** a table `ops_alerts`, created by one additive migration and owned by the monitor:
  - columns `key` (primary key), `opened_at`, `last_notified_at`, `resolved_at`, `last_value`, `sample_ids` (up to 5 correlation IDs), `notify_count`;
  - rows kept 90 days after they resolve.
- **Rules:**
  - **Open:** when a signal first trips, send email and SMS once.
  - **Still failing:** re-notify every **6 h**.
  - **Recovered:** notify once, "resolved after N min".
  - **Flapping:** a key that resolves and re-trips within 30 min re-opens without a new SMS (email only).
  - **Global cap:** 10 SMS per hour across all keys. Beyond that, one "N more alerts; see email" message.
- **Channels are independent:** if SendGrid fails, SMS is still attempted, and the reverse. A failed notification is logged and retried at the next monitor run, never in a tight loop.
- **Alert body (both channels):**
  - the key and its consequence line;
  - the counts;
  - up to 5 correlation IDs (run, report or consumer-report UUIDs);
  - the time first seen;
  - a recovery link to the runbook section for that key, plus the admin page where one exists.
  - SMS is the first two lines and the link.
- **Never in telemetry or alert bodies:** recipient emails or phone numbers, consumer names, property-owner names, addresses, tokens or secrets, or payment bodies. The bodies are built only from the key, counts, UUIDs and timestamps. A test renders every key's body from rows *full* of such data and asserts none of it appears.

## 6. Configuration

| Variable | Where | Meaning |
|---|---|---|
| `OPS_ALERTS_ENABLED` | worker | `0` (default) = observe: evaluate, record `ops_alerts`, log, **send nothing**. `1` = send. |
| `OPS_ALERT_EMAIL` | worker | **[JERRY]** the operator's address. Unset: no email. |
| `OPS_ALERT_SMS_TO` | worker | **[JERRY]** the operator's number in E.164. Unset: no SMS. |
| `OPS_PUBLIC_BASE` | worker | Base for recovery links (the web app's origin). Defaults to `WEB_BASE`, which the worker already has. |

Thresholds live as named constants in one module (`worker/ops_signals.py`), each with its approved value and the date it was approved, so changing one is a reviewed diff, not an environment edit.

## 7. Acceptance: injected failures in the isolated stack

This reuses the LR-023 live harness (`scripts/live/lr023/`: real Redis, a real Celery worker and the real ticker, against a local database), extended with a fake SendGrid and a fake Twilio that record what they receive. **It never points at production.**

| Inject | Expect |
|---|---|
| Stop PostgreSQL | `/ready` 503 `database: failing`. `/health` still 200. No restart. The monitor's next run fails its own query and does not crash the worker. Recovery: `/ready` 200, plus a `resolved` notice for any key that opened. |
| Stop Redis | `/ready` 503 `redis: failing` and both heartbeats stale. The pinger is the alert path, recorded as its HTTP view. |
| Stop the ticker | `ticker: stale` after 3 min; `ticker_stale` alert with its consequence line. |
| Strand a tracked run (publish lost, sweep exhausted) | `dispatch_stranded`, carrying the run ID. |
| Unknown send outcome (fake SendGrid accepts, answer dropped) | `send_needs_review`, carrying the run ID. |
| Fake SendGrid answers 4xx for a burst | `provider_refusals` once over threshold; nothing below it. |
| Failed webhook (with Codex's LR-011 signal) | `webhook_backlog`. |
| Auth rejection (bad token on an API route) | **No** alert, and `/ready` unaffected. |
| Flapping, then recovery | One SMS, the email re-open rule, one `resolved`. Under a burst, the SMS cap holds. |

Every alert body in these runs is captured and passes the privacy test.

**Receipt is proven, not assumed:** an admin-only `POST /v1/admin/ops/test-alert` sends one clearly labelled test alert through both channels. Closure needs Jerry to confirm the email and the SMS arrived, and the pinger's own alert too (it is paused on purpose for one check).

## 8. Rollout

1. Code PASS, then the migration (`ops_alerts`, additive) through the usual runbook. Jerry applies it.
2. Deploy with `OPS_ALERTS_ENABLED=0`, observe for **48 h**. Read `ops_alerts` and the logs, and compare the proposed thresholds with real traffic. Adjust; Jerry approves the final values.
3. Jerry sets `OPS_ALERT_EMAIL` and `OPS_ALERT_SMS_TO`, then runs the test alert and confirms receipt.
4. Jerry creates the pinger: `GET https://<api>/ready` every 5 min, alerting on 2 consecutive failures, to the same operator.
5. Confirm Render's health-check path for the API is `/health`, not `/ready`.
6. `OPS_ALERTS_ENABLED=1`.

**Cost:**
- **SendGrid:** within the current plan.
- **Twilio:** on the order of a cent per SMS in the US. At the cap of 10 an hour, a bad day is dollars, not tens of dollars.
- **Pinger:** free tier.
- **Database:** one small table, plus 8 bounded queries every 5 minutes.

**Escalation:** one named operator, Jerry. A second contact or quiet hours are **[JERRY]**. By default SMS is sent at any hour, because the signals were chosen to mean a customer is affected.

## 9. Open for Jerry

1. **D1:** SendGrid instead of Resend for alert email.
2. Approve the proposed thresholds (section 4), after observe mode.
3. The operator's email and phone, set by Jerry on Render (never in the repo or chat).
4. Pinger service and account. The design needs only "HTTP GET every 5 min, alert on 2 failures".
5. Quiet hours or a second contact, if any.

## 10. Not in this ticket
- LR-026, LR-028 (restore and recovery) and dashboards.
- Paging rotations.
- Codex's webhook-backlog query: its own PR, behind the interface in section 4.

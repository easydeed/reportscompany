# LR-023: a committed scheduled send survives a broker failure (D-381), and schedules never use the manual allowance (D-332)

Design rev 3: answers Codex's AMEND on rev 2 (§10), keeping rev 2's answers to rev 1 (§9) unchanged. Written for design re-review before code. Builder: Claude.
The facts below were verified at `main` `dbdb0f70`.

## 1. What is wrong today

**Dispatch (D-381).** `schedules_tick.process_due_schedules` writes the `report_generations` row and the `schedule_runs` row, and advances `next_run_at`, in one transaction. It commits (`schedules_tick.py:604–640`), and only then calls `celery.send_task` (`dispatch_report`, `:344–380`). That order is right, because a rollback can no longer leave an email nobody can recall (D-072). But a failed publish is only logged:

- the run sits at `queued` with no message;
- `next_run_at` has already moved to next week;
- after `STALE_QUEUED_MINUTES` (30), `sweep_stale_runs` (`:699–770`) marks it `failed` with "never picked up".

The occurrence is lost. Nothing distinguishes "never published" from "published and waiting in a backlog", because `schedule_runs` has no dispatch columns (0006: `status, error, started_at, finished_at, created_at`).

**Manual-allowance veto (D-332).** Jerry's rule, November 9: scheduled sends use schedule capacity and never the manual report allowance, and exhausting manual reports must not stop an existing schedule. Two places break that rule:

- **The ticker** (`schedules_tick.py:577–596`) calls `check_usage_limit(account_id, "market_reports")`. When the limit is reached, it advances `next_run_at` and continues. It records nothing: no run row and no log row.
- **The worker** (`tasks.py:1444–1482`) repeats the check at task start and marks the run `skipped_limit`.

The counters themselves already follow the rule. Both exclude scheduled runs (`api/services/usage.py:238`, `worker/limit_checker.py:78`, `NOT EXISTS schedule_runs`), so this ticket removes the two vetoes and changes no counting.

**Copy that states the old rule:**
- `api/services/email.py:689–702`, the limit-reached email: "any scheduled send that comes due before then is skipped, not sent later … schedules pick up again on the 1st", and "Sends skipped before then aren't re-sent";
- its policy comment at `:653–657`;
- `web/components/unified-wizard/step-deliver.tsx:44`: "Every run uses one report from your allowance".

The 80% warning (`:664–676`) already says "Reports your schedules make don't count toward this" and stays as it is.

## 2. The occurrence, tracked or legacy

An occurrence is one `schedule_runs` row: one durable identity, created once by the tick that claimed the schedule. Its `report_run_id` (= `report_generations.id`) is the Celery task's `run_id` argument. Every publish of the occurrence, first or republished, carries that same `run_id`. Nothing creates a second occurrence for one due time.

**Migration 0068.** LR-025 (#287) took 0067 after rev 1 was reviewed. 0068 adds these columns to `schedule_runs`:

| Column | Meaning |
|---|---|
| `recovery_tracked boolean NOT NULL DEFAULT false` | **The explicit boundary (AMEND 1).** Only the new ticker sets it, to `true`, on the insert. Every existing row, and any row an old ticker writes during the rollout, stays `false` and is **legacy**. Nothing is inferred from timestamps, and there is no backfill. |
| `dispatched_at timestamptz` | A publish the broker acknowledged, recorded after the fact. NULL means not yet, or unknown. |
| `dispatch_attempts int NOT NULL DEFAULT 0` | Publishes attempted, the first included. |
| `last_dispatch_at timestamptz` | When the last publish attempt started; used for backoff. |
| `last_dispatch_error text` | The last publish failure, for operators. |
| `owner_token uuid`, `lease_at timestamptz` | The execution lease: who holds the occurrence, and since when (AMEND 2). |
| `send_claimed_at timestamptz`, `send_token uuid` | The durable pre-send claim (AMEND 3). Once set, it is never cleared. |
| `send_recipients text[]` | The exact recipients the claim committed to: current recipients after send-time suppression (§5). |
| `send_outcomes jsonb NOT NULL DEFAULT '[]'` | One entry per recipient POSTed: `{email, outcome, status_code, at}` (§5). |

- **Index:** a partial index on `(created_at) WHERE recovery_tracked AND status IN ('queued', 'processing')`.
- **New statuses:** `cancelled`, `expired`, `blocked_unverified`, `needs_review`. `status` is free text since 0006, so no constraint changes.
- **`email_log.status`:** 0068 also updates the column's COMMENT (last set by 0062) to add `needs_review`. The column is plain text, so no data or constraint changes.
- **Rollout:** the migration takes `SET LOCAL lock_timeout = '5s'`, and both schema guards advance to 0068.

**Legacy rows keep today's behaviour exactly.** The worker uses the current start update for them. The sweep's existing pass (fail "never picked up" after 30 minutes, "died while running" after 6) applies to `NOT recovery_tracked` rows only. A legacy row is never republished, leased or send-claimed. The D-332 veto removal applies to them too, because it is a policy change, not a recovery mechanism.

**Every time below is measured from the occurrence's `created_at`, never from a retry.** The **horizon** is `created_at + 6 h`, which Jerry approved on 2026-11-11.

## 3. Publishing (the ticker and the sweep share one routine)

1. In the claiming transaction, or the sweep's locked transaction: `dispatch_attempts += 1`, `last_dispatch_at = now()`. Commit.
2. `send_task(run_id = report_run_id)`.
3. On success, `dispatched_at = now() WHERE dispatched_at IS NULL`. On failure, `last_dispatch_error`. Either write is best effort; if it fails, the row stays recoverable.

The crash windows are those of rev 1, and all of them are now safe through §4. For example, a publish that succeeded but whose acknowledgement was never recorded leads to one extra message, and the lease makes that message a no-op.

## 4. The execution lease: the first thing the worker does

The worker decides first, before **any** write to `report_generations` (status, `input_params`, artifacts). For a tracked run it executes, in one transaction:

```sql
UPDATE schedule_runs sr
SET status = 'processing', started_at = COALESCE(sr.started_at, now()),
    owner_token = $tok, lease_at = now()
FROM schedules s JOIN accounts a ON a.id = s.account_id
WHERE sr.report_run_id = $run AND sr.recovery_tracked
  AND sr.send_claimed_at IS NULL
  AND (sr.status = 'queued'
       OR (sr.status = 'processing' AND sr.lease_at < now() - STALE_STARTED))
  AND sr.created_at > now() - HORIZON
  AND s.id = sr.schedule_id AND s.active AND COALESCE(a.is_active, true)
  AND <account_can_send: an active user with a confirmed email>
RETURNING sr.owner_token
```

- **One row, so exactly one owner wins.** A second concurrent claim waits on the row lock. It then sees `lease_at` refreshed, or a terminal status, and matches nothing. Two delayed duplicates of a stale run cannot both proceed (AMEND 2).
- **When nothing is claimed**, the worker locks the row (`SELECT ... FOR UPDATE`) and writes exactly one truthful outcome, if one is due. Each of these is terminal and is never retried. AMEND 4 comes from this: **a delayed message is judged by the worker itself, with no sweep in between.**

| Row state, under lock | Outcome written |
|---|---|
| queued or stale-processing, past the horizon, no send claim | `expired`: "not sent: it could not start within 6 hours of its scheduled time" |
| …schedule paused | `cancelled`: "not sent: the schedule was paused before it ran" |
| …account inactive | `cancelled`: "not sent: the account was deactivated before it ran" |
| …no confirmed sender | `blocked_unverified`, plus the same `email_log` refusal row the ticker writes |
| stale-processing with `send_claimed_at` set and no recorded outcome | `needs_review` (§5) |
| terminal, or processing under a live lease | nothing: return `duplicate_message` |

- **Every later write by an owner is conditioned on its token.** That covers `schedule_runs` terminal status, the send claim, and `report_generations` status and URLs; the last are written as `... WHERE id = $run AND EXISTS (SELECT 1 FROM schedule_runs WHERE report_run_id = $run AND owner_token = $tok)`. When a write matches nothing, this owner was superseded: it stops, sends nothing and settles nothing.
- **The lease is refreshed** (`lease_at = now()`, token-conditioned) between the render stages. A long but live run is therefore never mistaken for a dead one. Today p99 is 41 s, the maximum 80 s, and `task_time_limit` 300 s, against a 6-minute stale window.

## 5. Delivery: one HTTP attempt per recipient, inside one claimed occurrence, failing closed

`send_schedule_email` (SendGrid) takes no idempotency key, so an unknown outcome cannot be safely repeated. Jerry's standing rule, the LR-020 policy, applies here too: **an unknown send outcome becomes `needs_review` and is never re-sent automatically.**

**What today's path does, and why rev 2's "unchanged" was wrong (rev 2 AMEND 2).** Verified at `main` `dbdb0f70`:
- `send_schedule_email` sends **one message per recipient** (`send.py:253–267`), so that each recipient carries their own unsubscribe token.
- Each of those calls goes to `sendgrid.send_email`, which **re-POSTs** up to `MAX_RETRIES = 3` more times (`sendgrid.py:93–136`; Codex's review cites 104–145, the same loop): after a `TimeoutException`, after a `RequestError`, and after a 429 or 5xx. A POST that SendGrid accepted, but whose response was lost, is POSTed again by the provider itself. The outer claim cannot stop that.
- The provider reports a timeout as a made-up `504`, a request error as `500`, and a missing API key as `500`. `send_schedule_email` returns only the **first** failing recipient's code (`:277–283`). Status codes therefore cannot separate "definitely not sent" from "unknown", and a definite rejection for one recipient hides an unknown outcome for another.

**The change: an explicit single-attempt mode, threaded through the existing helpers. The provider is reused, not replaced.**
- `sendgrid.send_email(..., single_attempt=False)`. With `True`, it makes exactly one `client.post` and no `time.sleep`/retry, and returns a typed `Attempt(outcome, status_code, detail)` instead of the tuple:

  | What happened on the one POST | `outcome` |
  |---|---|
  | 202 | `accepted` |
  | A response arrived with a 4xx, 429 included | `rejected` (SendGrid answered, and did not accept) |
  | A response arrived with a 5xx | `unknown` |
  | `httpx.ConnectError` or `httpx.ConnectTimeout`: no connection was made, so no request was sent | `not_sent` |
  | Any other timeout (read, write, pool), any other `RequestError` (a dropped connection, a protocol error), or any other exception | `unknown` |
  | Refused before any POST (no API key, no recipients) | `not_sent` |

- `send_schedule_email(..., single_attempt=False, claim=None)` passes the mode down. With `single_attempt=True` it returns a typed `ScheduleSend(attempts=[(email, Attempt), ...], refused=None)` and never collapses the attempts into one code. Its own pre-send refusals (no PDF URL, the unsubscribe sentinel missing) are `not_sent` before any POST.
- `_send_and_log_report_email(..., tracked=None)`. With a `TrackedSend(run_id, token)`, it calls the above in single-attempt mode, passes it the claim (below), and returns the aggregate outcome for §5 step 4.
- **Legacy calls pass nothing, and behave exactly as today:** retries, tuple returns, and the first-failure code. The manual and ad-hoc paths and legacy schedule rows are not touched. A test pins that the legacy path still retries a 503 (four POSTs).

**The order inside a tracked send:**

1. **Resolve and render, with no claim yet.** The D-110 empty-result hold, the brand, the payload, the current recipients, send-time suppression and the body all run first, as they do today. One change for tracked sends only: today a suppression-lookup error **proceeds with every recipient** (`send.py:171–174`). For a tracked send it stops instead, sends nothing and takes no claim. The row stays `processing` under its lease, which goes stale, and §6 case (c) republishes it, within the attempt cap and the horizon. Legacy keeps today's behaviour.
2. **The pre-send claim, as late as possible: after the render, immediately before the first POST.** `send_schedule_email` calls `claim(filtered_recipients)` once, after filtering and rendering, and POSTs nothing unless it returns true. The claim is one committed transaction:
   ```sql
   UPDATE schedule_runs sr
   SET send_claimed_at = now(), send_token = $tok, lease_at = now(),
       send_recipients = $filtered_recipients
   FROM schedules s JOIN accounts a ON a.id = s.account_id
   WHERE sr.report_run_id = $run AND sr.recovery_tracked
     AND sr.owner_token = $tok AND sr.status = 'processing'
     AND sr.send_claimed_at IS NULL
     AND sr.created_at > now() - HORIZON
     AND s.id = sr.schedule_id AND s.active AND COALESCE(a.is_active, true)
     AND <account_can_send>
   RETURNING 1
   ```
   - **The horizon is in the claim itself (rev 2 AMEND 1).** It is the same `created_at > now() - HORIZON` predicate as the lease, from the original `created_at`, using the database's clock. A worker that took its lease at 5 h 59 m and renders past 6 h gets zero rows here, and POSTs nothing.
   - **Terminal states stay excluded:** `status = 'processing'` and the token are both required, so a row that a sweep or another owner has already made terminal, or taken over, cannot be claimed.
   - **Zero rows:** no POST. Under the row lock, the worker writes the one truthful outcome from the §4 table: past the horizon → `expired`; paused → `cancelled`; deactivated → `cancelled`; no confirmed sender → `blocked_unverified`. Superseded owner → it stops and writes nothing.
   - **Any error** (the database is unreachable, a timeout, the commit fails): **no POST.** The claim was not taken, so the lease goes stale and §6 case (c) republishes it.
   - **Once claimed, the occurrence is committed to sending.** The horizon governs the claim. Recipients POSTed after the 6-hour mark in the same loop belong to an occurrence claimed before it.
3. **The loop: exactly one POST per recipient in `send_recipients`, in order, never repeated.**
   - After each recipient's POST, its outcome is appended to `schedule_runs.send_outcomes` and `lease_at` is refreshed, in one token-conditioned statement. This is best effort: if it fails, the loop still goes on to the next recipient, because no recipient is ever attempted twice.
   - The loop does not stop after an `unknown` or a `rejected` outcome. Each recipient is independent and gets its one attempt.
   - After a crash mid-loop, `send_recipients` minus the recipients with an outcome are "in flight or never attempted". The operator sees exactly which.
   - The existing `email_log` row (`_log_email_attempt` before, `_finalise_email_log` after) is kept, one per occurrence as today, so the admin counters do not change their cardinality. `_already_delivered` stays a second layer, checked before the claim. **Neither is the barrier:** if the lookup or the journal insert fails, the claim still decides, and each recipient still gets exactly one POST.
4. **Aggregate and record**, token-conditioned, then commit. An unknown outcome for any recipient wins over a definite rejection for another:

| Recipients' outcomes | `schedule_runs` | `email_log.status` | Re-sent automatically? |
|---|---|---|---|
| All `accepted` (suppressed recipients were never in the list) | `completed` | `sent` | — |
| **Any** `unknown` | `needs_review`: "outcome unknown for N of M recipients: the provider may have accepted these" | `needs_review` | **No** |
| No `unknown`, and any `rejected` or `not_sent` | `failed`: "failed_email: N of M not accepted" (the codes are in `send_outcomes`) | `failed` | No: one attempt per recipient per occurrence |
| The process dies after the claim and before this write | Still `processing`, `send_claimed_at` set. When the lease goes stale, the next lease attempt or the sweep writes `needs_review` | `sending` (left as is: "died in flight") | **No** |
| The outcome write fails | The same as the row above. `send_outcomes` and `email_log` hold whatever was recorded | — | **No** |

- **`email_log.status = 'needs_review'`** is a new value. Migration 0068 updates the column's COMMENT, and `admin.py:129` and `:216` count it alongside `sent`, `sending` and `failed`, because it is a delivery attempt.
- `needs_review` runs are listed for operators in the sweep's error log, with run, schedule, account and the per-recipient outcomes. LR-027 alerts on them, and the LR-020 held-send tooling is the model for resolving them by hand. Nothing in this PR resends them.

## 6. The sweep, for tracked rows: recover, then give up visibly

Each tick, the sweep selects tracked `queued` and `processing` rows `FOR UPDATE SKIP LOCKED`, so concurrent tickers never take the same row. It decides per row in that transaction:

1. **Terminal checks first** (§4 table):
   - past the horizon with no send claim → `expired`;
   - stale with a send claim → `needs_review`;
   - never started, and the schedule is paused, the account inactive or the sender unverified → `cancelled` or `blocked_unverified`.
2. **Recoverable candidates:**
   - **(a)** queued, `dispatched_at IS NULL`, `created_at < now() - 2 min`;
   - **(b)** queued, `dispatched_at < now() - 30 min` (a message the broker lost);
   - **(c)** processing, `lease_at < now() - 6 min`, no send claim (a dead owner).

   For each, the backoff must have elapsed since `last_dispatch_at`: 2, 4, 8, then 16 minutes, capped at 16.
3. **`dispatch_attempts >= 6`** (six publishes in total, the first included) → `failed`: "not dispatched: the queue was unavailable for 6 attempts". Otherwise, republish (§3).

**Rev 1's 6-minute "died while running → failed" step no longer applies to tracked rows (AMEND 2).** A dead owner's row is recovered by case (c), and becomes terminal only through the give-up or the horizon. The timeline:
- the worker dies at t;
- at t + 6 min the lease is stale, and the sweep republishes;
- the new message takes the lease;
- the broker's `acks_late` redelivery arrives at t + 15 min (`visibility_timeout` 900 s), finds a fresh lease or a terminal row, and is a no-op.

If the sweep is not running, the redelivery at t + 15 takes the stale lease itself.

## 7. D-332: the vetoes and the copy

- **Remove the ticker veto** (`schedules_tick.py:577–596`) and the worker veto (`tasks.py:1444–1482`). `check_usage_limit` stays for manual work. `skipped_limit` remains a valid historical status that nothing writes any more.
- **Limit-reached email** (`email.py:689–702`) and its policy comment (`:653–657`):
  - "Your scheduled reports keep sending: they don't count toward this limit."
  - The lead becomes "You can make N more while you decide. After that, new reports pause until {date}."
  - Drop "Sends skipped before then aren't re-sent".
  - Keep the upgrade line.
  - Tested with the existing fake sender.
- **Wizard** (`step-deliver.tsx:44`). Codex delegated this one literal swap to this PR: "Scheduled runs don't use your monthly report allowance. Each one pulls fresh data when it runs." I will make no other wizard change. This PR carries a copy regression test and a before/after render of the schedule step.
- **Other tickets' scope:** LR-015 owns the manual allowance function, and LR-016 owns schedule-capacity admission. Existing schedules are never bulk-paused, and the 43 inactive schedules are not activated.

## 8. Tests, proof and rollout

**Real PostgreSQL.** The publish and the provider are faked where noted.

- **Legacy boundary (AMEND 1):** legacy `queued` rows, both inside and outside the 6-hour range, are never republished or leased. They follow the legacy stale path. A row an old ticker writes after the migration is legacy.
- **Publishing:**
  - the first publish fails, the sweep republishes, and the publish is acknowledged;
  - a crash after the commit and before the publish;
  - a crash after the publish and before the acknowledgement: two messages, one lease, one send;
  - backoff 2/4/8/16;
  - the attempt boundary: the 6th publish is allowed and the 7th refused;
  - concurrent sweeps on two connections never select the same row.
- **Lease (AMEND 2):**
  - two simultaneous stale takeovers, exactly one winner;
  - a superseded owner's writes match nothing (`report_generations` included);
  - a duplicate message makes no `report_generations` write at all;
  - the sweep at t + 6 republishes and does **not** fail the row;
  - the redelivery at t + 15 is a no-op after the takeover;
  - the redelivery at t + 15 with no sweep takes the lease;
  - a live owner refreshing its lease is never taken over.
- **Delivery at the HTTP transport boundary (AMEND 3; rev 2 AMEND 2).** `SENDGRID_API_URL` points at a local socket server that counts the POSTs it receives, per recipient. The real `httpx` client makes the calls, and nothing is mocked above the socket.
  - **Accepted, then the answer lost:** the server reads the whole POST and closes the connection without replying. Exactly one POST per recipient, run `needs_review`, `email_log` `needs_review`. Then the same Celery message is redelivered, and a sweep runs: **zero** further POSTs.
  - **The same, with a read timeout:** the server reads the POST and never answers. One POST, `needs_review`, then zero after redelivery.
  - **A 503 from the server:** one POST, `needs_review`. The legacy path against the same server makes **four** POSTs, which pins the legacy retries as unchanged.
  - **Mixed recipients:** the 1st gets a 400 and the 2nd has its connection dropped after the POST. The run is `needs_review`, not `failed`, and `send_outcomes` holds `rejected` and `unknown`. Every recipient got exactly one POST.
  - **A definite 4xx for every recipient:** one POST each, `failed`, and nothing resent.
  - **Connection refused** (nothing listening): `not_sent` for every recipient, `failed`, and zero POSTs received.
  - **Order:** the claim commits after the render and before the first POST. A planted render failure leaves no claim.
  - **The process dies mid-loop** (after the 1st recipient's POST): the lease goes stale, the run becomes `needs_review` through the sweep and through a redelivery, and the 2nd recipient is never POSTed.
  - **Failed bookkeeping:** the claim's write fails → zero POSTs; the duplicate lookup or the journal insert fails → still exactly one POST per recipient; the per-recipient append fails → the loop still POSTs each remaining recipient once; the outcome write fails after all 202s → `needs_review` through the sweep, with no further POSTs.
  - **Suppression lookup error on a tracked send:** zero POSTs, no claim, and a later republish sends to the current, filtered list.
- **Eligibility over time (AMEND 4).** Each case below has no intervening sweep:
  - delivery after the horizon → the worker writes `expired`;
  - the schedule is paused after the tick → `cancelled` at the lease;
  - the schedule is paused after the lease and before the send → `cancelled` at the send claim;
  - the account is deactivated → `cancelled`;
  - the sender loses verification → `blocked_unverified` plus the `email_log` refusal;
  - recipients change before a republish → the current recipients get it;
  - a recipient unsubscribes before a republish → suppressed;
  - the horizon boundaries: `created_at + 6 h − 1 s` claims, and `+ 6 h + 1 s` expires;
  - **the horizon crossed between the lease and the send claim (rev 2 AMEND 1):** a valid lease is taken at `created_at + 6 h − 10 s`, and the render is held until the database's clock passes `created_at + 6 h`. The send claim matches nothing, the run is `expired`, and the socket server receives **zero** POSTs. There is no sweep in between. This is a separate test from the message that first starts after 6 h;
  - the send claim's boundaries: `created_at + 6 h − 1 s` at the claim POSTs, and `+ 6 h + 1 s` does not;
  - a row made terminal by a sweep between the lease and the send claim cannot be claimed.
- **Allowance:** an account at, over, or with zero manual allowance still gets an occurrence, a dispatch and a send, and its manual counter does not move.
- **Copy:** the email's HTML from the fake sender carries the new sentence and none of the old ones; the wizard line is asserted, and the schedule step rendered before and after.

**Handoff proof, live, on local Redis and Celery plus real PostgreSQL:**
- stop Redis, tick, and see a tracked occurrence queued and undispatched;
- start Redis, see the sweep republish it and the worker run it once, with one `sent` (fake provider);
- kill the worker mid-run, see the takeover at 6 minutes, and the 15-minute redelivery do nothing;
- inject an unknown provider outcome and see `needs_review`, with nothing sent again.

**Planted-bug checks.** Each must make a test fail:
- the marker not set by the ticker;
- the marker ignored by the sweep;
- `SKIP LOCKED` removed;
- the lease condition removed;
- the token condition dropped from a terminal write;
- the lease taken after the `report_generations` write;
- the send claim made after the provider call;
- the claim made fail-open;
- the horizon predicate dropped from the send claim;
- `status = 'processing'` dropped from the send claim;
- `single_attempt` not passed down from `_send_and_log_report_email` (the provider retries again);
- `single_attempt` ignored inside `sendgrid.send_email`;
- a read timeout classified as `not_sent`;
- the first failing recipient's code used for the aggregate (a rejection hides an unknown);
- the loop stopping after the first `unknown`;
- the suppression lookup failing open on a tracked send;
- an unknown outcome resent;
- the horizon removed from the worker;
- the attempt cap off by one;
- the ticker veto restored;
- the worker veto restored;
- the old email sentence restored;
- the old wizard line restored.

**Rollout:**
1. Migration 0068 is additive, with no backfill and no new table. It takes the next migration slot after #287's 0067.
2. The handoff includes a read-only inventory of legacy rows:
   ```sql
   SELECT status, count(*), min(created_at), max(created_at)
   FROM schedule_runs
   WHERE status IN ('queued', 'processing')
   GROUP BY status;
   ```
3. Runbook: Codex code PASS, a green exact-head gate, Jerry runs `--status` (exactly 0068 pending) and applies it, then the merge.
4. The schema guards make the new ticker and worker refuse to start before 0068.
5. **Rollback:** the old code ignores the columns, and the vetoes return with it.

## 9. Codex's AMEND on rev 1, and the answers

1. **Backfilled rows were still selected:** fixed by an explicit `recovery_tracked` marker that only the new ticker sets. There is no backfill and no inference from timestamps. Legacy rows follow only the legacy path, and the tests cover rows inside and outside 6 h (§2).
2. **Dead-start recovery and the 6-minute sweep:**
   - one conditional `UPDATE` takes a lease token, so exactly one owner wins;
   - every later write is token-conditioned;
   - the decision is made before any `report_generations` write;
   - for tracked rows, the 6-minute terminal step is replaced by recovery.

   The timeline at 6 and 15 minutes, and two simultaneous takeovers, are tested (§4, §6).
3. **The delivery guard is not proof:**
   - a durable pre-send claim is committed before the provider call, and it fails closed;
   - one provider call per occurrence (corrected in rev 3, §10: one HTTP attempt per recipient, inside one claimed occurrence);
   - an unknown or unrecorded outcome becomes `needs_review` and is never resent automatically;
   - the existing helpers are reused, with no second provider path.

   Accepted-but-answer-lost, failed bookkeeping and failed lookup or journal are all tested (§5).
4. **A delayed worker, and verification over time:** the worker's lease checks the horizon, the schedule's state, the account's state and the sender's verification. The pre-send claim checks them again. Every case is tested with no intervening sweep (§4, §5, §8).

**Bounds as Codex asked:**
- the 6-hour hard horizon from the original occurrence, never reset by a retry;
- 6 publishes in total, the first included;
- capped 2/4/8/16-minute backoff;
- the exact boundaries pinned in tests.

**Out of scope, recorded:**
- manual-report bridge-down detection: D-036, LR-027;
- per-recipient suppression visibility: D-333;
- real task retries for transient render failures: the `tasks.py:1394` note;
- a tool for resolving scheduled `needs_review` runs: it follows LR-020's held-send pattern, as a follow-up.

## 10. Codex's AMEND on rev 2, and the answers

Codex confirmed that `recovery_tracked`, the atomic lease, the worker's eligibility checks, the retry bounds and the legacy tests resolve rev 1's points. Those are unchanged in rev 3.

1. **The send claim did not check the horizon.** Fixed. The claim (§5 step 2) now has the same `created_at > now() - HORIZON` predicate as the lease, from the original `created_at`, and keeps `status = 'processing'` and the token, so terminal rows stay excluded. The claim also moved to the latest safe point, after the render and immediately before the first POST, so render time cannot carry a run across the horizon. The new test takes a valid lease just before 6 h, crosses the horizon before the claim, and expects `expired` with zero POSTs and no sweep (§8). It is separate from the message that first starts after 6 h.
2. **The provider resends inside one call.** Correct: `sendgrid.send_email` re-POSTs after a timeout, a request error, a 429 or a 5xx (`sendgrid.py:93–136`). Fixed with an explicit `single_attempt` mode on the existing provider, threaded through `send_schedule_email` and `_send_and_log_report_email`. Legacy callers pass nothing and keep their retries.
   - **One attempt per recipient**, since `send_schedule_email` sends to each recipient separately (`send.py:253–267`). Rev 2's "one provider call per occurrence" was wrong and is corrected.
   - **The outcome is typed, not a status code**, because the provider makes up 500 and 504 for local errors. Only a refused connection or a refusal before any POST counts as `not_sent`; any outcome after the request may have left counts as `unknown`.
   - **An unknown for any recipient wins over a definite rejection for another**, so the run is `needs_review`. Each recipient's outcome is kept in `send_outcomes`.
   - **Tested at the HTTP transport boundary** against a local socket server: accept and drop, accept and time out, a 503, mixed recipients, a refused connection. Each asserts the POSTs per recipient, and that a redelivery makes no further POST (§8).
   - **Two things found while checking this, both fixed in the same rev:** a suppression-lookup error proceeds with every recipient today (`send.py:171–174`). A tracked send now stops and is recovered by the sweep, and legacy is unchanged. And `email_log` gains a `needs_review` value, counted by the admin metrics as an attempt (§5).

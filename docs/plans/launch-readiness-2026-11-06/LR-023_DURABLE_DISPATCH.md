# LR-023: a committed scheduled send survives a broker failure (D-381), and schedules never use the manual allowance (D-332)

Design rev 2: answers Codex's AMEND on rev 1 (§9). Written for design re-review before code. Builder: Claude.
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

- **Index:** a partial index on `(created_at) WHERE recovery_tracked AND status IN ('queued', 'processing')`.
- **New statuses:** `cancelled`, `expired`, `blocked_unverified`, `needs_review`. `status` is free text since 0006, so no constraint changes.
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

## 5. Delivery: at most one provider call per occurrence, failing closed

`send_schedule_email` (SendGrid) takes no idempotency key, so an unknown outcome cannot be safely repeated. Jerry's standing rule, the LR-020 policy, applies here too: **an unknown send outcome becomes `needs_review` and is never re-sent automatically.**

1. **Pre-send claim.** It is committed **before** the provider call, in one transaction that also re-checks eligibility:
   ```sql
   UPDATE schedule_runs sr SET send_claimed_at = now(), send_token = $tok
   FROM schedules s JOIN accounts a ON a.id = s.account_id
   WHERE sr.report_run_id = $run AND sr.owner_token = $tok AND sr.send_claimed_at IS NULL
     AND s.id = sr.schedule_id AND s.active AND COALESCE(a.is_active, true) AND <account_can_send>
   RETURNING 1
   ```
   - **Zero rows:** no send. An ineligible row gets its truthful terminal state (§4 table); a superseded owner stops.
   - **Any error** (the database is unreachable, a timeout, the commit fails): **no send**. The run then becomes `needs_review` through the lease path. Today's lookup returns None and goes on to send, and the email_log insert lets the provider call go ahead when it fails. Neither is the barrier for tracked runs any more.
2. **Send** through the existing `_send_and_log_report_email`, unchanged:
   - current recipients, resolved at send time;
   - send-time suppression;
   - the D-110 empty-result hold;
   - the `email_log` journal.

   `_already_delivered` stays as a second layer. Nothing relies on it.
3. **Record the outcome** under the token, then commit:

| Provider result | `schedule_runs` | Retried automatically? |
|---|---|---|
| 2xx | `completed` | — |
| A definite rejection (4xx response) | `failed` (`failed_email: <code>`) | No: one provider call per occurrence |
| An exception, a timeout, a connection drop, or a 5xx with no definite answer | `needs_review`: "outcome unknown: the provider may have accepted this email" | **No** |
| The process dies after the claim and before this write | Still `processing`, `send_claimed_at` set. The next lease attempt or sweep finds it stale and writes `needs_review` | **No** |
| The outcome write fails after a 2xx | The same as the row above. The `email_log` journal still holds the 2xx for the operator to check | **No** |

`needs_review` runs are listed for operators in the sweep's error log, with run, schedule and account. LR-027 alerts on them, and the LR-020 held-send tooling is the model for resolving them by hand. Nothing in this PR resends them.

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
- **Delivery (AMEND 3):**
  - the pre-send claim is committed before the provider call;
  - the provider accepts and the answer is lost (exception after acceptance) → `needs_review`, and a later redelivery or republish does not send;
  - the process dies after the claim → `needs_review` through the lease and through the sweep;
  - a definite 4xx → `failed`, not resent;
  - the claim's database write fails → no provider call;
  - the duplicate lookup or journal insert fails → still exactly one provider call, because the claim is the barrier;
  - the outcome write fails after a 2xx → `needs_review`, not resent.
- **Eligibility over time (AMEND 4).** Each case below has no intervening sweep:
  - delivery after the horizon → the worker writes `expired`;
  - the schedule is paused after the tick → `cancelled` at the lease;
  - the schedule is paused after the lease and before the send → `cancelled` at the send claim;
  - the account is deactivated → `cancelled`;
  - the sender loses verification → `blocked_unverified` plus the `email_log` refusal;
  - recipients change before a republish → the current recipients get it;
  - a recipient unsubscribes before a republish → suppressed;
  - the horizon boundaries: `created_at + 6 h − 1 s` claims, and `+ 6 h + 1 s` expires.
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
   - one provider call per occurrence;
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

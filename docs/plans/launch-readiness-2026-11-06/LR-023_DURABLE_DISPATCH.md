# LR-023: a committed scheduled send survives a broker failure (D-381), and schedules never use the manual allowance (D-332)

Design rev 1, written for Codex design review before code. Builder: Claude.
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

## 2. The occurrence and its states

An occurrence is one `schedule_runs` row: one durable identity, created once by the tick that claimed the schedule. Its `report_run_id`, which is `report_generations.id`, is the Celery task's `run_id` argument and the key `_already_delivered(account_id, run_id)` deduplicates delivery on. Every publish of an occurrence, first or republished, sends the same `run_id`. Nothing creates a second occurrence for the same due time.

Migration **0068** adds four columns to `schedule_runs`:

| Column | Meaning |
|---|---|
| `dispatched_at timestamptz NULL` | When a publish of this occurrence was **acknowledged by the broker** and recorded. NULL means it has not been, or the outcome is unknown. |
| `dispatch_attempts int NOT NULL DEFAULT 0` | Publish attempts made, whether or not they succeeded. |
| `last_dispatch_at timestamptz NULL` | When the last attempt started; used for backoff. |
| `last_dispatch_error text NULL` | The last publish failure, for operators. |

- **Backfill:** every existing row gets `dispatched_at = created_at` and `dispatch_attempts = 1`. Pre-0068 occurrences are treated as published, so the new code never republishes old sends ("no replay of old scheduled sends"). They keep today's stale path.
- **Index:** a partial index on `(created_at) WHERE status = 'queued' AND started_at IS NULL`.
- **Rollout:** the migration also takes `SET LOCAL lock_timeout = '5s'`, and both schema guards advance to 0068.

| `status` | `started_at` | `dispatched_at` | What it means |
|---|---|---|---|
| queued | NULL | NULL | Committed, and no publish is known to have succeeded: never attempted, failed, or crashed before the acknowledgement was recorded. **Republishable.** |
| queued | NULL | set | Published and waiting for a worker. |
| processing | set | any | A worker claimed it. |
| completed / failed / skipped_* | — | — | Terminal, as today. |
| **cancelled** (new value) | NULL | any | Never started, and its schedule was paused or deleted, or its account deactivated, before a republish. `error` says which. |

## 3. Publishing, and every crash window

The ticker transaction is unchanged up to the commit. Then:

1. `UPDATE schedule_runs SET dispatch_attempts = dispatch_attempts + 1, last_dispatch_at = now() WHERE id = $run` and commit.
2. `send_task(... run_id = report_run_id ...)`.
3. On success: `UPDATE ... SET dispatched_at = now() WHERE id = $run AND dispatched_at IS NULL` and commit. On failure: `SET last_dispatch_error = $err` and commit. Both are best effort; if this write fails, the row stays republishable.

| Crash or failure point | State left behind | Recovery |
|---|---|---|
| Before the commit | Nothing; the lock expires | The next tick claims the schedule again (today's behaviour). |
| After the commit, before step 1 or 2 | queued, `dispatched_at` NULL | The sweep republishes it after `REPUBLISH_AFTER`. |
| The broker refuses the publish | queued, NULL, `last_dispatch_error` set | The sweep republishes it with backoff. |
| After a successful publish, before the acknowledgement is recorded | queued, NULL, **and a message in the broker** | The sweep republishes it, giving two messages for one occurrence. That is safe; see §4. |
| Published, then the broker loses it (a restart without persistence) | queued, `dispatched_at` set, never started | After `STALE_QUEUED_MINUTES` the sweep republishes it once more within the bounds below, instead of failing it. |

## 4. Duplicate publication cannot duplicate work or delivery

Two messages for one occurrence are expected, by design, in the post-publish crash window and when a sweep republishes during a backlog. The worker takes a **start claim** at the top of `generate_report`, for scheduled runs only, replacing today's unconditional `UPDATE ... started_at = NOW() WHERE started_at IS NULL`:

```sql
UPDATE schedule_runs SET status = 'processing', started_at = now()
WHERE report_run_id = $run AND started_at IS NULL AND status = 'queued'
RETURNING id
```

- **Claimed:** proceed.
- **Not claimed**, so another message already started this occurrence. Look at the row:
  - **terminal:** return `duplicate_message` and do nothing;
  - **`processing`, started within `STALE_STARTED_MINUTES` (6):** a live concurrent attempt, so return `duplicate_message`;
  - **`processing`, started earlier than that:** a dead attempt being redelivered by `task_acks_late`. Proceed, as today, so the D-068 recovery is kept.

Delivery stays behind `_already_delivered(run_id)`: `sent` blocks forever, and `sending` blocks inside its window. So even if a duplicate passed the start claim, it could not send twice. Usage is not touched, because scheduled runs are not counted.

## 5. The sweep: republish, cancel, or give up, bounded

`sweep_stale_runs` gains a republish pass that runs before the existing stale pass. Each tick:

1. **Select** with `FOR UPDATE SKIP LOCKED`, so concurrent tickers never take the same row. The candidates are rows where:
   - `status = 'queued' AND started_at IS NULL`, and
   - either `dispatched_at IS NULL AND created_at < now() - REPUBLISH_AFTER`,
   - or `dispatched_at IS NOT NULL AND dispatched_at < now() - STALE_QUEUED_MINUTES` (a lost message),
   - and `last_dispatch_at` is NULL or older than the backoff.
2. **For each candidate, decide inside the same transaction:**
   - **Schedule paused (`schedules.active = false`) or account inactive (`accounts.is_active = false`):** set `status = 'cancelled'` and `error = 'not sent: schedule paused before it could be dispatched'` (or the account-inactive reason). A deleted schedule's runs are already removed by `ON DELETE CASCADE`.
   - **`dispatch_attempts >= MAX_DISPATCH_ATTEMPTS`, or `created_at` older than `DISPATCH_HORIZON`:** set `status = 'failed'` and `error = 'not dispatched: the queue was unavailable for N attempts over M minutes'`, and log it at error level for operators and LR-027.
   - **Otherwise:** increment `dispatch_attempts`, set `last_dispatch_at`, commit, then publish and record the acknowledgement as in §3.
3. **The existing stale pass** keeps "died while running" (started, never terminal) exactly as it is. A row that was never started now reaches `failed` only through the bounded give-up in step 2, never on the first stale window.

**Bounds.** These are environment variables, like the existing windows. The 6-hour horizon was approved by Jerry on 2026-11-11; the others are proposed:

| Setting | Default | Why |
|---|---|---|
| `REPUBLISH_AFTER` | 2 min | Longer than a normal ticker pass, so a publish that is in flight is not raced. |
| Backoff | 2, 4, 8, 16 min | Doubles per attempt. |
| `MAX_DISPATCH_ATTEMPTS` | 6 | |
| `DISPATCH_HORIZON` | 6 h | A 9 a.m. report is still sent on the same working day. After that the run fails visibly rather than arriving at night or the next day. |

**What a republished send uses** (unchanged code, stated here because the acceptance names it):
- **Recipients:** whatever the schedule holds at delivery time, because `tasks.py:2091` reads `schedules.recipients` when it sends.
- **Unsubscribes:** suppression is applied at send time, so a recipient who unsubscribed after the occurrence was committed is still filtered.
- **Unverified accounts:** the ticker refuses them before an occurrence exists, so a republish never sees one.

## 6. D-332: the vetoes and the copy

- **Remove the ticker veto** (`schedules_tick.py:577–596`) and the worker veto (`tasks.py:1444–1482`). `check_usage_limit` stays for manual work. `skipped_limit` remains a valid historical status that nothing writes any more.
- **Limit-reached email.** Replace the scheduled-send sentences with:
  - "Your scheduled reports keep sending: they don't count toward this limit."
  - The lead becomes "You can make N more while you decide. After that, new reports pause until {date}." plus that line.
  - Drop "Sends skipped before then aren't re-sent", which describes a behaviour that no longer exists.
  - Keep "Nothing is deleted" and the upgrade line.
  - Correct the policy comment at `:653–657`.
  - Tested with the existing fake sender.
- **Wizard line** (`step-deliver.tsx:44`). Codex coordinates the wizard copy (DECISIONS_AND_LANES). Proposed: "Scheduled runs don't use your monthly report allowance. Each one pulls fresh data when it runs." **Codex: should this line change in this PR, or in yours?** Either way the email and the wizard must state the same rule.
- **Schedule capacity** (how many active schedules a plan admits) stays LR-016. Existing schedules are never bulk-paused, and the 43 inactive schedules are not activated.

## 7. Tests and proof

**Real PostgreSQL, with the publish faked:**
- A broker failure on the first publish, then the sweep republishes and acknowledges: one occurrence, one message accepted.
- A crash after the commit and before the publish, then a republish.
- A crash after a successful publish and before the acknowledgement: two messages, one start claim, one delivery.
- Concurrent sweeps (two connections) never republish the same row.
- Backoff and attempt counting.
- Give-up at `MAX_DISPATCH_ATTEMPTS` and at the horizon, with the visible error text.
- A paused schedule or inactive account becomes `cancelled`.
- Backfilled pre-0068 rows are never republished.
- A lost published message is republished, not failed.
- The start claim:
  - a terminal run gets a duplicate no-op;
  - a recent `processing` run gets a duplicate no-op;
  - an old `processing` run (an `acks_late` redelivery) proceeds.
- **Allowance:** an account at, over, or with zero manual allowance still gets an occurrence, a dispatch and a send, and its manual counter does not move.
- **Changed recipients** before a republish: the current recipients receive it. **Unsubscribe** before a republish: suppressed.
- **Email copy:** the fake sender's HTML carries the new sentence and none of the old ones.

**Handoff proof, live, on local Redis and Celery plus real PostgreSQL:** stop Redis, run a tick, and see the occurrence `queued` and undispatched. Start Redis, and see the next tick's sweep republish it, the worker run it once, and exactly one `email_log` `sent` row (fake provider). Then force the post-publish crash, and see two messages, one delivery.

**Mutations:** for each of the following, a test must fail:
- the start claim removed;
- `SKIP LOCKED` removed;
- the acknowledgement written before the publish;
- the backfill omitted;
- the attempt cap removed;
- the horizon removed;
- the ticker veto restored;
- the worker veto restored;
- the old email sentence restored.

## 8. Rollout

- One migration, 0068: additive columns, a backfill, a partial index, no new table. LR-025 (#287) takes 0067 first; LR-023 takes the slot after it.
- **Runbook:** Codex PASS, a green exact-head gate, Jerry runs `--status` (exactly 0068 pending) and applies it, then the merge.
- **Deploy order:** the schema guards make the new worker and ticker refuse to start against 0066, so the migration goes first. An old worker with the new schema ignores the new columns safely.
- **Rollback:** the old code ignores the columns, and the ticker veto returns with it.
- **Operators:** run outcomes appear in `schedule_runs` (`cancelled`, and `failed` with the not-dispatched reason) and in error logs. Alerting on them is LR-027.

## 9. Out of scope, recorded

- Manual-report bridge-down detection: D-036, LR-027.
- Per-recipient suppression visibility: D-333, a follow-up.
- Real task retries for transient render failures: the `tasks.py:1394` note.
- Schedule-capacity admission: LR-016.

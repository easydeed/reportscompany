# LR-020 / LR-021: one delivery state model

**Status:** design for review. Both tickets say "review one shared state model before coding, then ship two PRs." No code ships against this until it has a PASS.

**Tickets:**
- **LR-020 (D-069):** claim and reconcile consumer delivery. Branch `fix/lr-020-consumer-delivery-ownership`.
- **LR-021 (D-379):** recover agent notifications independently. Branch `fix/lr-021-agent-notification-recovery`.

**Base:** `main` at `652917c4`. It already has LR-019's write-ahead `sending` claim and `needs_review` hold.

## 1. What is wrong on `main` today

All line numbers are `apps/worker/src/worker/tasks.py` at `652917c4`.

**R1. Replay rewrites a delivered report** (`:2675`).
- The top of `process_consumer_report` sets `status='processing'` for every status except `sending` and `needs_review`, including a report already `sent`.
- The run then fetches comps again and rewrites `property_data`, `comparables`, `value_estimate`, `market_stats` and `pdf_url` (`:2980–3004`). That changes the data behind a link the homeowner already holds.
- `_consumer_already_delivered` (`:3021`) then returns. That leaves the row at `processing` permanently, over a report that was delivered.
- Causes: an `acks_late` redelivery, a Celery retry after a later exception, or any manual re-enqueue. This is the "replay overwrites `sent` with `processing`" in the ticket.

**R2. A live claim is taken for a dead one** (`:2646`).
- A second run that finds `sending` holds the report for review at once.
- It cannot tell whether a worker is mid-send right now or died ten minutes ago. Run A is still about to write its outcome.
- B raises a false operator alert. A's unconditional outcome write (`:3055`, `:3198`) then overwrites B's `needs_review`.

**R3. The credit debit is a separate write** (`:3114`).
- `sent` + timestamp and the `sms_credits` debit are two autocommit statements.
- A crash between them is a delivered text with no debit.
- Nothing prevents a second debit either: the debit is keyed on `delivered` in memory, not on the evidence changing.

**R4. The attempt has no identity.**
- The `sms_logs` row is written after the call, and only on paths that reach it.
- An interrupted attempt leaves no row, so an operator has nothing to reconcile against, and the rollout's "reconcile by attempt ID" has no ID.
- Consumer email writes no journal row at all.

**R5. The agent notification has no state** (`:3247–3275`, LR-021).
- It runs only in the same run that delivered.
- A failure is logged and forgotten: no row, no retry.
- A replay returns at `:3021` before reaching it.
- A worker death between the consumer send and the agent text loses the notification for good.

**What is already right, and stays:**
- The conditional claim at `:2496` is already the serialisation point: two runs at `processing` cannot both claim.
- LR-019's outcome classes (`sms_outcome`, `email_outcome`) and the `needs_review` hold.
- Failure text without contact details.
- Retry only for refusals that created nothing.

## 2. Provider facts this design rests on

Verified against provider docs on 2026-11-10.

**Twilio, Create a Message**
- No idempotency key or dedupe parameter.
- A client cannot make message creation idempotent.
- So a text whose outcome is unknown is **never sent again by code**. This is Jerry's policy, unchanged.

**Resend, Send Email**
- Supports an `Idempotency-Key` header, 1–256 characters, kept for 24 hours.
  - Same key and same payload: "the same response, without actually sending the email again."
  - Same key, different payload: `409 invalid_idempotent_request`.
  - Same key while the first request is still in flight: `409 concurrent_idempotent_requests`.
- So an email attempt can carry a key that makes a repeat of that exact attempt safe. See Q1 for whether we use that.
- The ticket text says SendGrid. The consumer path calls Resend (`:3176`), so Resend's behaviour is what applies.

## 3. The model

Two irreversible acts, each with its own owner, journal row and evidence:

| | Consumer delivery (LR-020) | Agent notification (LR-021) |
|---|---|---|
| State | `consumer_reports.status` (existing) | `agent_notify_status` (new) |
| Claim columns | `delivery_claimed_at`, `delivery_attempt_id` (new) | `agent_notify_claimed_at`, `agent_notify_attempt_id` (new) |
| Evidence (existing) | `consumer_sms_sent_at`/`_sid`, `consumer_email_sent_at` | `agent_sms_sent_at`/`_sid` |
| Journal (existing) | `sms_logs` (`recipient_type='consumer'`), `email_log` | `sms_logs` (`recipient_type='agent'`) |
| Cost | 1 SMS credit, for SMS only | free (existing policy) |

**Rule 1: evidence is terminal.**
- Once a `*_sent_at` is set, no code path clears it, and none moves `status` off `sent`.
- The only writer that can is the operator resolution tool (§6).
- Every automated status write carries the evidence guard: `AND consumer_sms_sent_at IS NULL AND consumer_email_sent_at IS NULL`.

**Rule 2: generation is separate from delivery.**
- Generation means fetching comps, computing values and rendering the PDF. It may repeat while nothing has been claimed or delivered.
- A run that finds a claim or evidence does not regenerate: what the person was sent stays what the link shows.
- No new "generation status" column is needed. `processing` already means "generating, no send claimed", and Rule 1 keeps it from being written over a delivery.

### 3.1 Consumer delivery states

`status` keeps its existing values; LR-019 already added `sending` and `needs_review`, and there is no CHECK constraint.

```
pending ──run──▶ processing ──claim──▶ sending ──outcome──▶ sent          (terminal)
   ▲                 ▲                    │                 failed        (retryable or final)
   └── failed ───────┘                    │                 needs_review  (held, operator only)
     (retry only)                         └─stale claim──▶ needs_review
```

| From | To | Writer | Guard |
|---|---|---|---|
| `pending`, `processing`, `failed` | `processing` | task start | status IN those three, and no evidence. Replaces `:2675`'s `NOT IN`, so `sent` is never touched. |
| `processing` | `sending` | **the claim**, one `UPDATE … WHERE eligible RETURNING` | status `processing`, no evidence. The same transaction inserts the journal row, which supplies `delivery_attempt_id`. Committed before the provider call. |
| `sending` | `sent` | outcome | `WHERE id AND <evidence column> IS NULL`, **not** conditional on ownership. Evidence must never be lost, and the debit happens in the same transaction only if this update matched a row (§3.3). |
| `sending` | `failed` / `needs_review` | outcome | `status='sending' AND delivery_attempt_id = <mine>`. Ownership-conditional: a run can only settle its own attempt. |
| `sending`, claim older than the window | `needs_review` | any later run, or the outer handler | `delivery_claimed_at < NOW() - window`. |
| `sending`, claim inside the window | (no write) | any later run | Return "in flight". **Fixes R2:** no hold and no alert. |
| `needs_review` | `sent` / `failed` | operator tool only (§6) | Records who resolved it and the evidence used. |

**The window** is the existing `DUPLICATE_SEND_WINDOW_MINUTES` (10), the same constant the scheduled-email path uses.
- It is longer than `task_time_limit` (300 s), so a live attempt is never called stale.
- It is shorter than the broker's `visibility_timeout` (900 s), so the `acks_late` redelivery of a dead run sees the claim as stale and holds it.

### 3.2 Replay of a delivered record

If the top of the task finds evidence, it skips generation and the consumer stage. It goes straight to the agent stage, which is LR-021; in LR-020 alone, it returns.
- No status write.
- No regeneration.
- `ok=True`, because the report has been delivered.

This also covers a report a later exception left at `processing` with evidence present: it is read as delivered.

### 3.3 One debit per delivered text (fixes R3)

The `sent` write and the debit go in one transaction:

```sql
UPDATE consumer_reports SET status='sent', consumer_sms_sent_at=NOW(), consumer_sms_sid=…
 WHERE id=… AND consumer_sms_sent_at IS NULL RETURNING id;
-- only if a row came back:
UPDATE accounts SET sms_credits = GREATEST(sms_credits - 1, 0) WHERE id=…;
```

- The debit is tied to the evidence going from NULL to set, which can happen once.
- A crash before the commit leaves `sending`. That is an unknown outcome held for review, and the operator's "sent" resolution applies the debit with the evidence (§6).
- This keeps the existing `GREATEST(…, 0)` policy, and email never debits.

### 3.4 The journal (fixes R4)

- **SMS:** the claim transaction inserts `sms_logs(status='pending', recipient_type='consumer', consumer_report_id, to_phone, message_body)`. `pending` is already allowed by 0035's CHECK. Its `id` becomes `delivery_attempt_id`.
- The outcome transaction updates that row:
  - SID → `sent`;
  - refusal → `failed` plus the error;
  - unknown → stays `pending`, which sms_logs reads as "not settled".
- That removes the after-the-fact insert at `:3088`.
- **Email:** the same for `email_log`:
  - `status='sending'` at the claim;
  - `report_id` = the consumer report id;
  - `provider='resend'`;
  - `to_emails`, `subject`;
  - then `sent`, or `failed` plus `response_code`.

  These values are already the D-083 vocabulary (0062). Readers this adds rows for:
  - **`onboarding.py:233`**'s "first report sent" check counts any `email_log` row with `status='sent' AND report_id IS NOT NULL`. A homeowner email would tick the agent's onboarding step. **It changes**: rows whose `report_id` is a `consumer_reports.id` are excluded.
  - **`usage.py:109`** "recent emails" starts listing the home-value email sent to the lead. It is an email sent on the account's behalf, so I think it belongs there. Q2 asks.
  - **`admin.py`**'s sent/sending/failed counters start including consumer emails. They are deliveries, so that is correct.
  - **`unsubscribe.py:86`**'s candidate lookup gains the lead's address. The HMAC token still decides, so there is no weakening.

### 3.5 Email and the idempotency key

Every consumer email attempt sends `Idempotency-Key: consumer-report:<report_id>:<delivery_attempt_id>`.
- On its own this changes nothing in behaviour. It only makes a repeat of the same attempt harmless at the provider.
- Whether a run may repeat an unknown-outcome email with the same key and payload within 24 hours is **Q1, a decision for Jerry**. Until he decides, an unknown email outcome is held exactly like an SMS one.

### 3.6 Agent notification states (LR-021, fixes R5)

```
NULL ──consumer delivered──▶ sending ──▶ sent           (agent_sms_sent_at set; terminal)
                               │          failed         (retryable: own retry budget)
                               │          needs_review   (unknown outcome / stale claim)
                               └─(no agent phone)──▶ skipped (terminal, reason stored)
```

- **Eligible:** consumer evidence present, and `agent_sms_sent_at IS NULL`, and `agent_notify_status` IS NULL or `failed`.
- **Claim:** one conditional `UPDATE … RETURNING`, plus a `sms_logs(recipient_type='agent', status='pending')` journal row, committed before the call.
- **Window:** same window and same stale rule as §3.1.
- **Outcome:** written the same way as §3.1, with no debit.
- **Where it runs:** a function `_notify_agent(report_id)` that uses the same claim, outcome and journal helpers. It runs:
  - inline, right after the consumer `sent` write (no added latency);
  - from a replay of a delivered record (§3.2);
  - from a small task `notify_consumer_report_agent(report_id)` with its own `max_retries`, scheduled only for a retryable refusal.

  So a refused agent text never re-runs the consumer task, and the consumer task's retries never use up the agent's budget.
- It never resends the homeowner's report, and the homeowner's `status` is never changed by this stage.
- **Destination:** the agent's phone is read from `users.phone` when the claim is taken, and the `sms_logs.to_phone` row records it. A changed contact after a failed attempt goes to the new number. A `sent` notification is never repeated to a new number. Q3 asks.
- **Name:** `requester_name(property_data)` or the generic fallback. Never the assessor's owner name. This is unchanged (D-156).
- **Out of scope:** an agent *email* notification (D-340) is not added. The reconciliation note says LR-021 recovers the existing SMS notification only.

## 4. Schema: one additive migration

All columns are nullable with no default rewrite, so `ALTER … ADD COLUMN IF NOT EXISTS` is instant on Postgres.

```sql
ALTER TABLE consumer_reports
  ADD COLUMN IF NOT EXISTS delivery_claimed_at      TIMESTAMPTZ,
  ADD COLUMN IF NOT EXISTS delivery_attempt_id      UUID,
  ADD COLUMN IF NOT EXISTS agent_notify_status      TEXT,
  ADD COLUMN IF NOT EXISTS agent_notify_claimed_at  TIMESTAMPTZ,
  ADD COLUMN IF NOT EXISTS agent_notify_attempt_id  UUID,
  ADD COLUMN IF NOT EXISTS agent_notify_error       TEXT;
```

- **Both tickets' columns go in LR-020's migration.** The lane rule allows at most one open migration PR across both lanes, so LR-021 ships no migration.
- No CHECK constraints. The values are documented with `COMMENT ON COLUMN`, the same as 0062.
- **The existing `sending` rows from LR-019 have no `delivery_claimed_at`.** The stale rule treats a NULL claim time as stale, so they are held, never sent.
- **Rollout:**
  1. Jerry applies the migration.
  2. The code deploys after it. The code reads the new columns, so it must not run before them.
  3. Rollback means stopping new consumer sends first, then reconciling every `sending`/`needs_review` row by `delivery_attempt_id`.
  4. The columns can stay.

## 5. Tests (real task, migrated Postgres, providers faked at the HTTP edge)

**LR-020**
- **Two real executions synchronised at the send** (a barrier in the fake provider): one claim, one provider call, one `sms_logs` row, one debit. The same for email.
- **Worker death before the send** (claim committed, process killed): the next run inside the window does nothing; after the window it holds; no second provider call.
- **Provider refusal:** retryable (429) goes to `failed`, then a retry and a new attempt id. Final (400) is `failed` with no retry.
- **Provider accepted and the answer was lost** (timeout after acceptance): `needs_review`, an alert, journal `pending`, no debit, no resend.
- **Timestamp write fails after acceptance:** the row stays `sending`; the outer handler or the next stale check gives `needs_review`; no second call.
- **Stale claim versus live claim:** a live claim is not held (R2's false alert is gone).
- **Retry exhaustion:** visible in `error_message`.
- **Replay of a delivered record:** status stays `sent`; timestamps, `comparables`, `pdf_url` and `property_data` are byte-identical; no provider call.
- **A report left at `processing` with evidence:** read as delivered.
- **Mutations** for each guard: the claim condition, the evidence guard, debit-on-match, the window comparison, and the replay early exit.

**LR-021**
- **Consumer delivered, agent not notified:** the replay sends only the agent text.
- **Both done:** neither is sent.
- **Concurrent recovery:** one agent text.
- **Agent refusal:** `failed`, then its own retry task.
- **Agent timeout:** `needs_review`, never resent.
- **Missing agent phone:** `skipped`, with no loop.
- **Worker death between the stages:** the redelivery sends the agent text only.
- **Contact changed** between failure and recovery: goes to the new number.
- **Name:** the requester's name, or the generic text when the form has no name. Never the owner name.
- **No credit spent by any agent path.**

## 6. Ambiguity: who resolves it and with what evidence

- **Who:** Jerry, as operator, until LR-027 routes `CONSUMER_DELIVERY_NEEDS_REVIEW` / `AGENT_NOTIFY_NEEDS_REVIEW` to a named rota.
- **SMS evidence:** Twilio's message list filtered to `To = <number>`, from `delivery_claimed_at` − 1 minute to + 10 minutes, with a matching body.
  - A message found resolves to **sent**, with its SID and date. That applies the debit in the same transaction.
  - None found resolves to **release**: `failed`, retryable, so a run may send.
- **Email evidence:** the Resend dashboard or logs for the recipient in the same window.
  - With a key, a repeat call returns the original email id; see Q1.
- **Tool:** `scripts/ops/resolve_consumer_delivery.py <report_id> --sent <sid>|--release --evidence "<text>" --operator <name>`.
  - It only moves rows out of `needs_review`.
  - Each move is a conditional update.
  - It writes the operator and evidence into `error_message` and the journal row.
  - It prints the before and after. It never calls a provider.
- **Inventory first (read-only, for Codex or Jerry):**
  - counts of `sending` / `needs_review` / `processing` rows, by age;
  - delivered reports with `agent_sms_sent_at IS NULL`.

  The second list is the candidate set for historical agent recovery, and it is **not** replayed automatically. A bounded, reviewed list with approved recipients is a separate step.
- **Stale claims with no redelivery:** if a task message is lost outright, the row stays `sending` and nothing re-runs it. LR-020 provides the query for this; LR-027 alerts on it.

## 7. Questions for review

- **Q1 [JERRY]:** may an unknown-outcome **email** be repeated automatically with the same Resend idempotency key and the same payload, within 24 hours? Resend documents that this cannot send a second email. **Recommended: yes, once.** Then hold if the outcome is still unknown. **Default until answered: hold, same as SMS.** Texts are never repeated either way.
- **Q2:** should the lead's home-value email appear in the agent's "recent emails" (`usage.py`)? **Recommended: yes.**
- **Q3:** should a recovered agent notification go to the agent's **current** phone (recommended), or to the phone on file when the lead arrived?
- **Q4:** is the operator resolution script in LR-020's scope (recommended), or LR-027's?

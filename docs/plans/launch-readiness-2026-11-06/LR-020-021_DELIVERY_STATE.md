# LR-020 / LR-021: one delivery state model

**Status:** design, revision 2, for re-review. It amends revision 1 per Codex's review on #280 (AMEND 1–4). The tickets say "review one shared state model before coding, then ship two PRs". No code ships against this until it has a PASS.

**Tickets:**
- **LR-020 (D-069):** claim and reconcile consumer delivery. Branch `fix/lr-020-consumer-delivery-ownership`. Carries the migration and the held-send tool.
- **LR-021 (D-379):** recover agent notifications independently. Branch `fix/lr-021-agent-notification-recovery`. No migration.

**Base:** `main` at `a4e34d9f`. It has LR-019's write-ahead `sending` claim and `needs_review` hold.

## 1. What is wrong on `main` today

All line numbers are `apps/worker/src/worker/tasks.py` at `652917c4`; #279 did not move this flow.

**R1. Replay rewrites a delivered report** (`:2675`).
- The top of `process_consumer_report` sets `status='processing'` for every status except `sending` and `needs_review`, including `sent`.
- The run then rewrites `property_data`, `comparables`, `value_estimate`, `market_stats` and `pdf_url` (`:2980–3004`). It re-uploads the PDF to the same object key, `consumer-reports/{account_id}/{report_id}.pdf` (`:2966`).
- `_consumer_already_delivered` (`:3021`) then returns. The row is left at `processing`, over a delivered report whose link now shows different data and a different PDF.

**R1b. Two concurrent generations are not ordered** (AMEND 2).
- Runs A and B both enter `processing` and both generate.
- A can publish, claim and send. B can then publish over A's fields and replace the same PDF object, then lose the claim.
- An entry-time evidence check cannot prevent this.

**R2. A live claim is taken for a dead one** (`:2646`).
- A second run that finds `sending` holds it at once, and raises a false alert.
- The owner's later unconditional outcome write (`:3055`, `:3198`) overwrites that hold.

**R3. The debit is a separate write** (`:3114`).
- `sent` plus its timestamp, and the `sms_credits` debit, are two autocommit statements.
- The debit is keyed on an in-memory flag, not on the evidence changing.

**R4. An attempt has no identity.**
- The `sms_logs` row is written after the call (`:3088`), and only on paths that reach it.
- An email writes no journal row at all.

**R5. The agent notification has no state** (`:3247–3275`).
- It runs only in the same run that delivered.
- A failure is logged and forgotten.
- A replay returns at `:3021` before reaching it.

**Kept:**
- The conditional claim (`:2496`).
- LR-019's outcome classes.
- The `needs_review` hold.
- Failure text without contact details.
- Retry only for refusals that created nothing.

## 2. Provider facts (verified 2026-11-10)

**Twilio, Create a Message**
- No idempotency key or dedupe parameter.
- A text whose outcome is unknown is never sent again by code.

**Resend, Send Email** (https://resend.com/docs/dashboard/emails/idempotency-keys)
- Header `Idempotency-Key`, 1–256 characters, kept for **24 hours**.
- **Same key, same payload:** the same response, and nothing sent again.
- **Same key, different payload:** `409 invalid_idempotent_request`.
- **Same key, first request still in flight:** `409 concurrent_idempotent_requests`.

The ticket text says SendGrid. This path calls Resend (`:3176`).

## 3. The model

There are two irreversible stages. Each has its own claim, journal row, evidence and resolution.

| | Consumer delivery (LR-020) | Agent notification (LR-021) |
|---|---|---|
| State | `consumer_reports.status` (existing values) | `agent_notify_status` (new) |
| Claim | `delivery_claimed_at`, `delivery_attempt_id` (new) | `agent_notify_claimed_at`, `agent_notify_attempt_id` (new) |
| Evidence (existing, terminal) | `consumer_sms_sent_at` and `_sid`, `consumer_email_sent_at` | `agent_sms_sent_at` and `_sid` |
| Journal (existing tables) | `sms_logs` (`recipient_type='consumer'`) or `email_log` | `sms_logs` (`recipient_type='agent'`) |
| Cost | 1 SMS credit, SMS only | free (existing policy) |

**Rule 1: evidence is terminal.**
- No code path clears a `*_sent_at`, including the operator tool.
- The tool may only set evidence that is NULL (§6).
- No automated write moves `status` off `sent`.
- Every automated status write carries `AND consumer_sms_sent_at IS NULL AND consumer_email_sent_at IS NULL`.

**Rule 2: generation is owned, and frozen at the claim** (§3.2).

### 3.1 Consumer delivery states

`status` keeps its existing values. There is no CHECK constraint, and LR-019 added `sending` and `needs_review`.

```
pending ─▶ processing ─publish(gen G)─▶ processing[G] ─claim(G)─▶ sending ─▶ sent           (terminal)
   ▲           ▲                                                  │  │     failed           (retryable / final)
   └─ failed ──┘ (retryable refusal only)                         │  │     needs_review     (operator only)
                                                                  │  └─ email unknown ─▶ one replay (§3.4) ─▶ sent | needs_review
                                                                  └─ stale claim ─▶ needs_review, or one replay (§3.4)
```

| From | To | Writer | Guard |
|---|---|---|---|
| `pending`, `processing`, `failed` | `processing` | task start | status IN those, no evidence, `delivery_attempt_id IS NULL`. Never `sent`, `sending` or `needs_review`. |
| `processing` | `processing` with fields | **publish** (§3.2) | status `processing`, no evidence, `delivery_attempt_id IS NULL`. |
| `processing` | `sending` | **claim**: one `UPDATE … WHERE eligible RETURNING` | status `processing`, no evidence, **`generation_id = <mine>`**. The same transaction inserts the journal row, whose id is `delivery_attempt_id`. Committed before any provider call. |
| `sending` | `sent` | outcome, or the operator tool | `<evidence column> IS NULL`, deliberately **not** ownership-conditional. Evidence is never refused. The debit is in the same transaction, only if this update matched (§3.3). |
| `sending` | `failed` | outcome (a refusal known to have created nothing) | `status='sending' AND delivery_attempt_id = <mine>`. Also sets `delivery_attempt_id = NULL` and `delivery_claimed_at = NULL`, because nothing was sent, so a retry can publish and claim a **new** attempt. The journal row keeps the refused attempt. |
| `sending` | `needs_review` | outcome | `status='sending' AND delivery_attempt_id = <mine>`. The claim stays, frozen, for the operator. |
| `sending`, claim inside the window | (no write) | any other run | Return "in flight". No hold, no alert (fixes R2). |
| `sending`, claim outside the window | `needs_review`, or one email replay | any later run | Re-claim, conditional on `delivery_attempt_id` and the old `delivery_claimed_at`. Then §3.4 decides between replay and hold. A NULL claim time (LR-019's rows) counts as stale. |
| `needs_review` | `sent` / `failed` | **operator tool only** (§6) | Exact stage and attempt id. |

**The window** is the existing `DUPLICATE_SEND_WINDOW_MINUTES` (10).
- It is longer than `task_time_limit` (300 s), so a live attempt is never called stale.
- It is shorter than `visibility_timeout` (900 s), so the `acks_late` redelivery of a dead run sees the claim as stale.

**Replay of a delivered record.** Evidence present at task start means:
- no status write;
- no generation;
- no consumer stage;
- go to the agent stage (LR-021).

### 3.2 Generation ownership and the frozen artifact (AMEND 2)

- **A generation id per run.** Each run draws a fresh `generation_id` (uuid4) before it generates.
- **An immutable PDF key per generation.** The PDF goes to `consumer-reports/{account_id}/{report_id}/{generation_id}.pdf`. No two generations share a key, so no upload can replace a delivered object. The old fixed key is no longer written.
- **Publication is one guarded UPDATE.** It writes `property_data`, `comparables`, `value_estimate`, `market_stats`, `pdf_url`, `pdf_generated_at` and `generation_id = <mine>`:
  ```sql
  … WHERE id = … AND status = 'processing' AND delivery_attempt_id IS NULL
        AND consumer_sms_sent_at IS NULL AND consumer_email_sent_at IS NULL
  RETURNING id
  ```
  - No row back means the run stops before any send.
  - Its own PDF object is orphaned at its own key; deleting it is optional.
- **Only the publisher of the current generation can claim.** The claim requires `generation_id = <mine>`.
  - If B published after A, A's claim fails and B, holding the current generation, claims and sends it.
  - If A claimed first, B's publication fails.
  - Either way, the fields and the PDF bytes behind the link are the ones the delivered message pointed to.
- **Frozen after the claim.** While an attempt is claimed, `sending` or `needs_review`, publication is refused, and the claimed generation's fields and object are what the person receives. Once there is evidence, publication is refused for good.
- **After a known refusal**, nothing was delivered and the claim is released (§3.1), so the retry may publish a new generation.
- **The SMS body** is built from those frozen values before the claim, and stored in the journal (§3.5).
- **LR-022 (missing PDFs)** must keep this rule. It may fill `pdf_url` only where it is NULL, at a new generation-keyed object, rendered from the frozen fields, and never replace one. That is noted here for LR-022; it is not built in LR-020.

### 3.3 One debit per delivered text

```sql
UPDATE consumer_reports SET status='sent', consumer_sms_sent_at=…, consumer_sms_sid=…
 WHERE id=… AND consumer_sms_sent_at IS NULL RETURNING id;
-- same transaction, only if a row came back:
UPDATE accounts SET sms_credits = GREATEST(sms_credits - 1, 0) WHERE id=…;
UPDATE sms_logs SET status='sent', twilio_sid=… WHERE id=<attempt>;
```

- The debit is tied to the evidence going from NULL to set, which can happen once, whether the outcome, the operator tool or a late provider result writes it.
- The existing `GREATEST(…, 0)` policy is kept.
- Email never debits.

### 3.4 The approved email replay: durable and race-safe (AMEND 1)

**Decision (Jerry, 2026-11-10):** an unknown-outcome consumer email gets exactly **one** automatic replay of the **same attempt**:
- the same `Idempotency-Key`;
- a byte-identical payload;
- strictly inside the key's original 24-hour window.

Still unknown afterwards, or outside the window, means `needs_review`. A text is never replayed. A retryable refusal that created nothing (429, a connection that never opened) stays a separate case: `failed`, retried later as a **new** attempt with a new key.

**Durable fields on the email attempt row** (`email_log`, §4):
- **`request_payload` (JSONB):** the exact request sent: `from`, `to`, `subject`, `html`, and the `Idempotency-Key` header. The consumer email has no `text` part and no attachments today; if either is added, it goes in here.
  - Written in the claim transaction, before the first call.
  - Never rewritten.
  - The replay sends it as stored. Content, recipient and branding are never rebuilt.
- **`idempotency_key`:** `consumer-report:<report_id>:<attempt_id>`. Set once at the claim.
- **`key_expires_at`:** the row's `created_at` plus 24 hours.
  - `created_at` is committed before the first request leaves, so this is never later than Resend's own expiry.
  - Set once.
  - No later run resets it.
- **`replay_claimed_at`:** the one-replay budget.

**The replay reservation:**
```sql
UPDATE email_log SET replay_claimed_at = NOW()
 WHERE id = <attempt> AND replay_claimed_at IS NULL
   AND NOW() < key_expires_at - INTERVAL '10 minutes'
RETURNING request_payload, idempotency_key;
```
- The reservation is atomic, so two workers, a restart or a redelivery can consume it at most once.
- The 10-minute margin covers the 15-second request timeout, clock skew and queueing. No replay is made at or after the cutoff.

**Who replays:**
- **The owner, inline.** If the first call's outcome is unknown, the run that made it reserves the replay at once and sends the stored payload.
- **A later run.** If the first run died after the call and before the replay reservation, a later run re-claims the stale claim (§3.1), then reserves and replays, if the budget and the window allow. Otherwise it holds.

**Outcomes of the replay:**

| Replay result | Result |
|---|---|
| 200 or 201 | `sent`. If the first call had sent the email, Resend returns that original response; no second email exists. Store the returned email id as `provider_message_id`. |
| `409 concurrent_idempotent_requests` | `needs_review`. The first request may still be in flight, so its fate is unknown. The budget is spent. |
| `409 invalid_idempotent_request` | `needs_review` plus an alert. The payload cannot differ, so this means a defect. |
| 429, a connection that never opened | `needs_review`. The replay created nothing, but the first call's fate is still unknown. The budget is spent. |
| Another 4xx, a timeout, a 5xx | `needs_review`. |
| A crash after the reservation | The claim goes stale and the next run holds it: `replay_claimed_at` is set, so there is no second replay. |
| The reservation fails (budget spent, or past the cutoff) | `needs_review`. |

**When in doubt, hold:** any state the run cannot establish as safe is `needs_review`.

### 3.5 The journal, on the real schema (AMEND 4)

**SMS (`sms_logs`).**
- 0035 requires `to_phone`, `from_phone` and `message` to be NOT NULL. 0039 added `message_body`, which does not replace `message`.
- The claim transaction inserts:
  - `status='pending'`, which 0035's CHECK allows;
  - `recipient_type` (`consumer` or `agent`);
  - `consumer_report_id`;
  - `account_id`;
  - `to_phone`;
  - `from_phone` (`TWILIO_PHONE_NUMBER`);
  - `message`;
  - `message_body`. Both message columns hold the **exact** body that will be sent.
- So the body is built before the claim. `send_report_sms` and `send_agent_notification_sms` gain a body-building half, and the send uses that stored body unchanged.
- The destination is frozen in `to_phone` (Q3).
- If `TWILIO_PHONE_NUMBER` is unset, nothing is claimed: the run records `failed` with the configuration reason, as LR-019 does now.
- **Outcome:**
  - `sent` plus the SID;
  - `failed` plus `error_code` and `error_message`;
  - unknown stays `pending`, meaning not settled.
- This replaces the after-the-fact insert at `:3088`.

**Email (`email_log`).**
- The claim inserts `status='sending'` with:
  - `account_id` (tenant scoping, Q2);
  - `report_id` = the consumer report id;
  - `provider='resend'`;
  - `to_emails`, `subject`;
  - the §3.4 fields.
- **Outcome:**
  - `sent` plus `response_code` plus `provider_message_id`;
  - `failed` plus `response_code` and `error`;
  - unknown stays `sending` until the replay or the hold. The hold is visible on the report row.
- **Readers affected:**
  - **`usage.py`:** recent emails now include the home-value email (Q2: yes). The list is already scoped to `account_id`.
  - **`onboarding.py`:** the "first report sent" check must exclude rows whose `report_id` is a `consumer_reports.id` (Q2). This changes in LR-020, with a test.
  - **`admin.py`:** the counters now count consumer deliveries, which are real deliveries.
  - **`unsubscribe.py`:** the lookup gains candidates, and the HMAC token still decides.

### 3.6 Agent notification states (LR-021)

```
NULL ─(consumer evidence present)─claim─▶ sending ─▶ sent          (agent_sms_sent_at set; terminal)
                                            │        failed        (retryable refusal: own retry task)
                                            │        needs_review  (unknown, or stale claim; never resent)
                                            └─ no current agent phone ─▶ skipped (terminal, reason stored)
```

**Eligible:**
- consumer evidence present;
- `agent_sms_sent_at IS NULL`;
- `agent_notify_status` IS NULL or `failed`.

**Claim and outcome:**
- **Claim:** one conditional `UPDATE … RETURNING`, plus the `sms_logs` insert (§3.5), committed before the call.
- **Window:** the same window and stale rule as §3.1. Stale means `needs_review`, never a resend.

**Destination (Q3, approved):**
- A **new** eligible attempt reads `users.phone` when it claims, and freezes it in that attempt's `sms_logs.to_phone`.
- An attempt that was accepted, or whose outcome is unknown, is never retargeted or repeated.
- A `failed` attempt's successor reads the then-current phone.

**Where it runs:**
- `_notify_agent(report_id)` runs inline after the consumer `sent` write, and on a replay of a delivered record.
- `notify_consumer_report_agent(report_id)` is a task with its own `max_retries`, scheduled only for a retryable refusal.
- It never resends the homeowner's report and never touches consumer `status` or credits.

**Other rules:**
- **Name:** `requester_name(property_data)` or the generic fallback. Never the assessor's owner name (D-156).
- **Out of scope:** an agent email notification (D-340) is not added.

## 4. Schema: one additive migration, in LR-020 (AMEND 4)

`db/migrations/0064_delivery_ownership.sql`. It carries both tickets' columns, because only one migration PR may be open across both lanes.

```sql
SET LOCAL lock_timeout = '5s';   -- run_migrations.py runs each file in one transaction

ALTER TABLE consumer_reports
  ADD COLUMN IF NOT EXISTS generation_id            UUID,
  ADD COLUMN IF NOT EXISTS delivery_claimed_at      TIMESTAMPTZ,
  ADD COLUMN IF NOT EXISTS delivery_attempt_id      UUID,
  ADD COLUMN IF NOT EXISTS agent_notify_status      TEXT,
  ADD COLUMN IF NOT EXISTS agent_notify_claimed_at  TIMESTAMPTZ,
  ADD COLUMN IF NOT EXISTS agent_notify_attempt_id  UUID,
  ADD COLUMN IF NOT EXISTS agent_notify_error       TEXT;

ALTER TABLE email_log
  ADD COLUMN IF NOT EXISTS idempotency_key      TEXT,
  ADD COLUMN IF NOT EXISTS key_expires_at       TIMESTAMPTZ,
  ADD COLUMN IF NOT EXISTS request_payload      JSONB,
  ADD COLUMN IF NOT EXISTS replay_claimed_at    TIMESTAMPTZ,
  ADD COLUMN IF NOT EXISTS provider_message_id  TEXT,
  ADD COLUMN IF NOT EXISTS resolution           TEXT,
  ADD COLUMN IF NOT EXISTS resolved_at          TIMESTAMPTZ,
  ADD COLUMN IF NOT EXISTS resolved_by          TEXT,
  ADD COLUMN IF NOT EXISTS resolution_evidence  TEXT;

ALTER TABLE sms_logs
  ADD COLUMN IF NOT EXISTS resolution           TEXT,
  ADD COLUMN IF NOT EXISTS resolved_at          TIMESTAMPTZ,
  ADD COLUMN IF NOT EXISTS resolved_by          TEXT,
  ADD COLUMN IF NOT EXISTS resolution_evidence  TEXT;

-- plus COMMENT ON COLUMN for each, as 0062 does; no CHECK constraints.
```

**Locks.**
- The columns are nullable with no default, so no table is rewritten. Each `ALTER TABLE` still takes an ACCESS EXCLUSIVE lock, for a moment.
- `lock_timeout` makes the migration fail fast instead of queueing behind a long transaction and blocking the readers behind it. A failed run changes nothing, because it is one transaction, and it is re-run.
- Neither the runner nor the runbook sets a lock timeout today. This file sets its own, and the runbook gains one line saying so.

**`REQUIRED_MIGRATION`** goes to `0064_delivery_ownership.sql` in **both** `apps/api/src/api/schema_guard.py` and `apps/worker/src/worker/schema_guard.py`, per `docs/runbooks/migrations-and-deploys.md`.

**Rollout, following that runbook:**
1. Merge.
2. The first deploy refuses to start, on purpose.
3. Jerry runs `run_migrations.py --status` (expect exactly 0064 pending) and then applies it.
4. Redeploy the API and the worker.

**Rollback:**
1. Stop new consumer sends.
2. Reconcile every `sending` and `needs_review` row by attempt id with the tool (§6).
3. The columns stay.

**LR-019's `sending` rows** have no claim time. They read as stale and are held, never sent.

## 5. Tests

All tests run the real task against a database built by `run_migrations.py` from every file in `db/migrations`, never a test-only shape. Providers are faked at the HTTP edge.

**LR-020, delivery**
- **Two executions synchronised at the send** (a barrier in the fake provider): one claim, one provider call, one journal row, one debit. The same for email.
- **Worker death before the send:** inside the window, nothing happens; outside it, the report is held; no second call.
- **Refusal:** retryable (429) gives `failed`, then a new attempt with a new key. Final (400) gives `failed`, no retry. Exhaustion is visible.
- **SMS accepted, answer lost:** `needs_review`, an alert, the journal stays `pending`, no debit, no second call.
- **Timestamp write fails after acceptance:** stays `sending`, then a stale hold; no second call.
- **Live claim versus stale claim:** a live one is neither held nor alerted.
- **Replay of a delivered record:** status, timestamps, all generated fields, `pdf_url` and the PDF object bytes are unchanged; no provider call.
- **The journal insert** fills `message`, `message_body` and `from_phone`. It runs against the migrated schema, so a missing NOT NULL column fails the test.

**LR-020, generation (AMEND 2)**
- **Barrier test:** B's generation finishes after A has claimed and sent.
  - B's publication is refused.
  - The database fields and the stored PDF **bytes** at A's `pdf_url` equal A's delivered version.
  - B's object sits at a different key.
- **B publishes before A claims:** A's claim fails, B sends, and the link shows B's generation.
- **Mutations:** the publication guard, the `generation_id` claim condition, the per-generation key.

**LR-020, email replay (AMEND 1)**
- **Unknown, then a 200 on the replay:** `sent`. The replay used the same key and a byte-identical stored payload, and the fake asserts it.
- **Unknown, then unknown again:** `needs_review`; exactly two calls in total.
- **`409 concurrent_idempotent_requests`** on the replay: `needs_review`.
- **`409 invalid_idempotent_request`:** `needs_review` plus an alert.
- **Two workers racing to replay:** exactly one replay call.
- **A crash after the reservation:** the next run holds the report; no second replay.
- **A crash before the reservation:** the next run replays once, with the stored payload, even if branding or the agent's details changed in between.
- **Window boundary:** with the clock at the cutoff minus 1 s, and with `key_expires_at` already past, there is no replay; the report is held.
- **A redelivery** does not reset `key_expires_at` or mint a new key.
- **Mutations:** the reservation condition, the cutoff margin, the payload source.

**LR-020, held-send tool (AMEND 3):** see §6.

**LR-021**
- **Consumer delivered, agent not notified:** the replay sends only the agent text.
- **Both done:** neither is sent.
- **Concurrent recovery:** one agent text.
- **Agent refusal:** `failed`, then its own retry task.
- **Agent timeout:** `needs_review`, never resent.
- **No agent phone:** `skipped`, no loop.
- **Worker death between the stages:** the agent text only.
- **Contact changed before a new attempt:** the new number.
- **Contact changed after an unknown attempt:** the attempt is not retargeted or repeated.
- **Name:** the requester's name or the generic text, never the owner name.
- **Credits:** no credit is spent on any agent path.

## 6. Held sends: the operator workflow, both stages (AMEND 3; Q4: in LR-020)

**Who:** Jerry, as operator, until LR-027 routes the alerts (`CONSUMER_DELIVERY_NEEDS_REVIEW`, `AGENT_NOTIFY_NEEDS_REVIEW`) to a named rota.

**Tool:** `scripts/ops/held_sends.py`. It runs against the database only, and **never calls a provider or enqueues a send.**

**`list [--stage consumer|agent] [--state held|stale|all] [--older-than 30m]`.** One line per attempt:
- report id;
- stage;
- channel;
- attempt id;
- state: `needs_review`, or `sending` past the window;
- age since the claim;
- the recorded outcome text;
- the SID or email id, if any;
- for email, whether the replay was used, and `key_expires_at`;
- destination masked to its last four characters.

**`hold <report> --stage S --attempt A`.** Moves a stale `sending` to `needs_review`. The guard is the exact attempt plus a stale claim.

**`resolve <report> --stage consumer|agent --attempt A --sent --provider-id <Twilio SID | Resend email id> [--sent-at <provider timestamp>] --evidence "<what was checked>" --operator <name>`.** One transaction:
- **The attempt guard:** stage, attempt id and the current state must match, so a stale or wrong attempt is refused.
- **Evidence:** `--provider-id` is required. The tool sets the evidence column only where it is NULL; existing evidence is never cleared or overwritten.
- **The debit (consumer SMS only):** applied once, via §3.3's rule.
- **The journal row** gets `resolution='sent'`, `resolved_at`, `resolved_by` and `resolution_evidence`.
- **Agent stage:** writes only the agent columns and that stage's journal row. It never touches consumer state or credits.

**`resolve … --not-sent --evidence "<proof of non-acceptance>" --operator <name>`.**
- The evidence must be positive: a provider record of rejection, or a provider-side search covering the whole claim window that shows no message.
- Not finding a message in a short dashboard search is **not** sufficient. When the result is uncertain, the operator leaves the row held; there is no "probably not sent" action.
- **Result:** consumer `failed`, or agent `failed`, with the resolution recorded. The stage's attempt and claim columns are cleared, and the journal row keeps the attempt. It does **not** enqueue a send.
- A new send after `--not-sent` is a separate, explicit operator decision. That is a re-enqueue of the task, outside this tool, which then claims a **new** attempt.

**A late provider result:**
- If an outcome arrives after a `--not-sent` resolution, its evidence write still lands, because evidence is never refused (Rule 1). The status becomes `sent` and the debit happens once.
- That contradiction is logged CRITICAL for the operator.
- A late result after a `--sent` resolution finds the evidence set and does nothing.

**Tests:**
- concurrent resolution versus a late provider result (both orders);
- a repeated resolution, which is a no-op with a message;
- the wrong attempt id, refused;
- the wrong stage, refused;
- `--sent` without a provider id, refused;
- `--not-sent` without evidence, refused;
- consumer SMS resolved `sent`, giving exactly one debit;
- agent stage resolved, with consumer state and credits unchanged;
- no code path that clears evidence.

**Inventory first (read-only, for Codex or Jerry):**
- counts of `sending`, `needs_review` and `processing` rows, by age;
- delivered reports with `agent_sms_sent_at IS NULL`.

The second list is the candidate set for historical agent recovery. It is not replayed automatically: a bounded, reviewed list with approved recipients is a separate step.

**A task message lost outright** leaves a stale `sending` row that nothing re-runs. `list --state stale` shows it, and LR-027 alerts on the same query.

## 7. Decisions (Jerry, 2026-11-10; approved, per Codex's review)

- **Q1: yes.** One automatic replay of the same email attempt, with the same key and the same payload, strictly inside its 24-hour window (§3.4). Texts are never resent automatically.
- **Q2: yes.** The home-value email appears in the account's recent emails, tenant-scoped. It is excluded from the onboarding first-report check.
- **Q3: the current phone.** It is read when a new eligible attempt claims, and frozen in that attempt's journal row. Accepted and unknown attempts are never retargeted.
- **Q4: in LR-020.** The minimal held-send list and resolution tool (§6).

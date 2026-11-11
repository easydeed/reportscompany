# LR-024: wizard failure states and a retry that cannot duplicate (design, rev 1)

- **Ticket:** LR-024. **Defects:** D-382, D-330, and the unified-wizard part of D-329.
- **Gate:** PILOT. **Lane:** Claude.
- **Status:** design for review. The ticket's rollout rule applies: "If safe retry requires an API contract change, document and review the narrow scope rather than introducing a speculative client-only workaround." It does. This note is that scope.

## 1. What is wrong today (verified at `main` 3419b0e4)

**`apps/web/components/unified-wizard/index.tsx`**

| Where | What happens |
|---|---|
| `startPolling`, `:225–251` | A `setInterval` every 3 s with no deadline. A non-OK status response `return`s, and an exception is swallowed (`/* ignore polling errors */`). An expired session, an API outage or a report stuck in `pending` spins forever (D-382). |
| `handleSubmit`, `catch`, `:397–401` | It sets an error state only when `deliveryMode === "send_now"`. A failed **schedule** create clears the spinner and shows nothing (D-330). |
| The 429 branches, `:318–322` and `:382–386` | They read `used`/`limit`/`product` at the top level. The API puts them inside `detail` (`reports.py`, `schedules.py`: `HTTPException(429, detail={...})`). The specific numbers never show, and the fallback prints `[object Object]` or a generic line (D-329). |

**API**

`POST /v1/reports` and `POST /v1/schedules` take no idempotency key. Suppose the response to a successful create is lost: a network drop, a proxy timeout, or a tab put to sleep. Then a "Try again" creates **a second report**, which counts against the plan's monthly limit twice and, with recipients, **emails them twice**. For a schedule, it creates a second schedule that sends on every run. Nothing on the client can tell whether the first request landed.

## 2. The API contract change (narrow)

Both endpoints accept an optional **`Idempotency-Key`** request header.

- **No header:** behaviour is unchanged for every other caller.
- **Format:** 8–100 characters of `[A-Za-z0-9_-]`. Anything else gets 422 `invalid_idempotency_key`.

**Storage.** Migration `0066_request_idempotency.sql`: a new table, additive, with `SET LOCAL lock_timeout = '5s'` and the apply-first rollout like 0064 and 0065.

```sql
CREATE TABLE request_idempotency (
  account_id   uuid        NOT NULL REFERENCES accounts(id) ON DELETE CASCADE,
  endpoint     text        NOT NULL CHECK (endpoint IN ('reports.create', 'schedules.create')),
  idem_key     text        NOT NULL,
  request_hash text        NOT NULL,   -- sha256 of the canonical JSON body
  resource_id  uuid        NOT NULL,   -- report_generations.id or schedules.id
  created_at   timestamptz NOT NULL DEFAULT now(),
  PRIMARY KEY (account_id, endpoint, idem_key)
);
-- RLS on account_id, matching the existing per-account tables (property_report_stats pattern).
```

Both schema guards move `REQUIRED_MIGRATION` to 0066.

**Inside the endpoint's existing transaction, before the verification and limit checks:**

1. `pg_advisory_xact_lock(hashtextextended('<endpoint>:<account>:<key>', 0))`. Two concurrent requests with one key are serialized; the second waits for the first to commit or roll back.
2. Look up `(account, endpoint, key)` from the last 24 h. A row older than 24 h is deleted and treated as absent. The window matches Resend's, so a key behaves alike end to end.
3. **Hit with the same `request_hash`:** return the original resource as it is now, with the original status code (202 or 201) and `Idempotent-Replayed: true`. There is no limit check, no usage, no enqueue and no email. For a report, the body is `{report_id, status}` from `report_generations`. For a schedule, it is the same representation as `GET /v1/schedules/{id}`.
4. **Hit with a different hash:** 409 `idempotency_key_reused`, and nothing is created.
5. **Miss:** the existing path runs unchanged. The key row is inserted in **the same transaction** as the `report_generations` or `schedules` INSERT. A refusal or error rolls the key back with the resource, so a key is stored only for something that exists, and a retry after a refusal runs fresh.

**What it deliberately does not do:**
- **Store response bodies.** It replays the resource's current state, which is what a client polling the report wants.
- **Cover the report enqueue after commit.** If the enqueue failed, the replay shows `failed` and the wizard shows the terminal failure. A crash between the commit and the enqueue leaves a `pending` report. That predates this ticket and is recorded below; the bounded wait in §3 now shows it as "taking longer than usual" instead of spinning.

**Alternatives rejected:**
- *Reconcile on the client by listing recent reports or schedules and matching their parameters.* Two identical legitimate requests are indistinguishable from a retry. This is the speculative client-only workaround the ticket rules out.
- *Key columns on `report_generations` and `schedules`.* That means two migrations' worth of columns and indexes on hot tables. One small table covers both and later endpoints.

## 3. The wizard

**One key per payload.**
- The wizard keeps `{payload, key}` in a ref. A submit whose canonical payload equals the last one reuses its key; any edit gets a new key (`crypto.randomUUID()`).
- After a success, the key is dropped, so building the same report again on purpose is a new request.
- A retry after a lost response or a 5xx therefore replays instead of duplicating. A retry after a terminal generation failure creates a new report, because the payload's key is dropped once its report exists.

**Submit outcomes**, the same for "Generate" and "Create Schedule" (fixes D-330):

| Outcome | Detected by | State shown | Actions |
|---|---|---|---|
| Server unreachable | `fetch` throws | "We couldn't reach the server. Your choices are kept." | Try again (same key), Back to edit |
| Server error | 5xx | "Something went wrong on our side. Trying again won't create a second report." | Try again (same key), Back to edit |
| Session expired | 401 | "Your session has expired. Sign in again in a new tab, then come back and try again. Your choices are kept." | Sign in (new tab), Try again |
| Email not verified | 403 `verification_required` | the existing `VerificationRequired` component, unchanged | as today |
| Plan limit | 429 | the existing limit card, with numbers read from `detail` (D-329) | as today |
| Invalid request | 400/409/422 | the server's message, e.g. "'X' is not a recognized CRMLS city" | Back to edit |

**Report status after "Generate":**
- **Polling:** a `setTimeout` chain every 3 s, each request with an AbortController. Unmount and retry abort it, and no interval is left behind.

| Outcome | Detected by | State shown | Actions |
|---|---|---|---|
| Ready | `completed` | as today | as today |
| Generation failed | `failed` | "We couldn't generate this report." | Try again (new report), Back to edit |
| Slow but legitimate | still pending at 2 min | "This is taking longer than usual. It will appear in Reports when it's ready." Polling stops. | Keep waiting (another 2 min), Go to Reports |
| Can't check | 3 consecutive failed checks (network or 5xx) | "We can't check on your report right now. It's still being made and will appear in Reports." Polling stops. | Check again, Go to Reports |
| Session expired | 401 on a check | "Your session has expired…" | Sign in (new tab), Check again |
| Not found | 404 | "We can't find this report." | Go to Reports |

**Everywhere:**
- Form state is never reset by an error.
- Each new state's heading takes focus (`tabIndex={-1}`) and sits in an `aria-live="polite"` region.
- No new estimate, price or copy outside these messages.

## 4. Tests and proof

- **API, real routes on migrated Postgres:**
  - the same key replays the same report or schedule, with no second row, no second usage count and no second enqueue;
  - four concurrent requests with one key create exactly one;
  - the same key with a different body gets 409 and creates nothing;
  - a refused request (limit or verification) stores no key, and its retry runs fresh;
  - a key older than 24 h is new;
  - no header behaves as today;
  - a malformed key gets 422.
  - Each test is red on `main`, where a second report is created.
- **Web (Jest):** every row of both tables above; the key is reused after a lost response and changes after an edit; timers stop on unmount and on retry; focus moves to the new heading; a schedule failure shows its error.
- **Mutations:** a spec covering the lock, the hash comparison, the same-transaction insert, the reused key, the deadline, the consecutive-error count and the schedule error path.
- **Renders:** each changed state at 390px, 820px and desktop, on the real wizard with the proxy answered per state, with a keyboard pass.

## 5. Rollout

1. Codex design PASS on §2. Code starts after it; only the client half (§3) is written before it.
2. Code PASS and a green exact-head Release gate.
3. Jerry runs `--status`, sees exactly `0066_request_idempotency.sql` pending, and applies it.
4. Merge and deploy the API and web together. The web sends the header from the first deploy. An API without 0066 refuses to start (schema guard), so the header is never silently ignored in production.

## 6. Recorded, not fixed here

- A report committed but never enqueued (the API crashed between the commit and `enqueue_generate_report`) stays `pending`. The wizard now shows "taking longer than usual" and Reports shows it pending. Recovering it belongs with the job-stall alerting in LR-027.
- The property wizard's refusal handling is D-213 / FOLLOWUP-PROPERTY-REFUSAL-UX (LR-038). It is out of scope; the header is offered to it but not wired.

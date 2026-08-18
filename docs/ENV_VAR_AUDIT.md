# Environment Variable Audit — doc/code name drift

**Branch:** `fix/env-var-name-drift` · **Date:** 2026-08-18
**Scope:** D1 (audit both `ENV_TEMPLATE.md` files against runtime reads), D2 (repo-wide sweep for the same class), D3 (trace `EMAIL_UNSUB_SECRET`).

**Method.** Every name a Python file reads via `os.getenv` / `os.environ.get` / `os.environ[...]`, every name a TS/JS file reads via `process.env.*`, and every field on the pydantic `Settings` model (`apps/api/src/api/settings.py`) — extracted mechanically, then compared against every `NAME=` line in the templates and setup docs. Nothing here is inferred from naming; each row was resolved to the file that reads it or to the fact that nothing does.

---

## The defect class

An environment variable that a document names but no code reads has one failure mode, and it is the worst one available: **you set it, nothing errors, and the feature silently uses a default.** There is no startup validation anywhere in this codebase that cross-checks a configured name against a read name, so the only signal is the behaviour that never happens.

Four instances are now confirmed, in four different files. This is not a coincidence rate.

| # | Documented / declared | Actually read | Consequence |
|---|---|---|---|
| 1 | `UNSUBSCRIBE_SECRET` (`apps/worker/ENV_TEMPLATE.md:50`) | `EMAIL_UNSUB_SECRET` (`email/send.py:16`) | Every unsubscribe link fails validation — see D3 |
| 2 | `PDF_ENGINE=api` (`apps/worker/ENV_TEMPLATE.md:33`) | `pdf_engine.py:30` accepts only `playwright`/`pdfshift`; `:359` raises | Every PDF render fails (value drift, not name drift) |
| 3 | `PDF_API_KEY` (`apps/api/ENV_TEMPLATE.md:34`) | `branding_tools.py:119` reads `PDF_API_KEY`; every other PDFShift call site reads `PDFSHIFT_API_KEY` | Branding sample PDF/JPG 503 if only `PDFSHIFT_API_KEY` is set |
| 4 | `STARTER_PRICE_ID`, `PRO_PRICE_ID`, `ENTERPRISE_PRICE_ID` (`settings.py:20-22`) | `config/billing.py:18-19` reads `STRIPE_PRICE_PRO_MONTH` / `STRIPE_PRICE_TEAM_MONTH` | Three declared settings fields that nothing references; setting them configures nothing |

Instance 4 is new and is the most instructive: the drift is not between a doc and code, it is **inside the API's own settings model**. `Settings` declares three Stripe price fields that no line of code reads, while the live price IDs come from two differently-named `os.getenv` calls in a different module. The one place that gets it right is `billing.py:77-80`, whose missing-config error names the real variables — which is the message that surfaced as the `/v1/billing/portal` 500 in the F4 sweep.

**A note on why this was hard to see.** The `[DIAGNOSTIC]` lines at `property_builder.py:200-204` are an import side effect of that module, not a per-service environment audit. They fire only where `property_builder` is imported — worker and bridge — so their absence on the API and ticker says nothing whatsoever about those services' configuration. Any comparison matrix built from them would have been confidently wrong. (They are removed in D4; see the end of this document.)

---

## D3 — `EMAIL_UNSUB_SECRET`, precisely

### What reads it

Two services, and **they have different fallback values**:

| Service | File | Behaviour when unset |
|---|---|---|
| **Worker** (signs the token) | `apps/worker/src/worker/email/send.py:16-19` | `logger.critical` warning, then falls back to `"dev-only-secret-do-not-use-in-production"` |
| **API** (verifies the token) | `apps/api/src/api/routes/unsubscribe.py:12` | Silently falls back to `"dev-unsubscribe-secret-change-in-prod"` |

Both are read at **module import**, so both are frozen at process start and neither responds to a config change without a restart.

### The chain, end to end

1. `send.py:137` computes `unsub_token = generate_unsubscribe_token(account_id, first_recipient)` — `HMAC-SHA256(secret, "account_id:email")` (`:22-33`).
2. `send.py:138` builds `{WEB_BASE}/api/v1/email/unsubscribe?token=…&email=…` into the email body.
3. The recipient clicks. `apps/web/app/api/v1/email/unsubscribe/route.ts:11-24` (GET) forwards it as a POST to `{NEXT_PUBLIC_API_BASE}/v1/email/unsubscribe`.
4. `apps/api/src/api/routes/unsubscribe.py:59-66` resolves an `account_id` by finding a schedule whose `recipients` array contains that email, then `:77-81` verifies the HMAC with **the API's** secret.
5. Match → row inserted into `email_suppressions` (`:84-88`), 200. Mismatch → **HTTP 400 `{"detail":"Invalid unsubscribe token"}`** (`:77-81`), passed straight back through the Next.js route as raw JSON (`route.ts:39`).

### Answering the question as asked

**Broken link, or a link that fails validation on click?** **The latter, unambiguously.** The URL is well-formed and routes correctly all the way to the verification call. What fails is `hmac.compare_digest` at `unsubscribe.py:42`. The recipient sees a JSON error body — not a styled page, not a confirmation — and stays subscribed. There is no retry and nothing is logged on the API side.

**Does the bridge's value matter? No — and this is the important part.** The bridge emits the `EMAIL_UNSUB_SECRET not set!` warning purely because `send.py:18` executes at **import** time and `tasks.py:15` imports `send_schedule_email` at module level; anything that imports `worker.tasks` prints it. The bridge's own job is `blpop` → `generate_report.delay()` (`tasks.py:2116-2124`) and it never calls `send_schedule_email`. The email is composed and sent inside `generate_report`, which runs in the **worker** service.

So exactly two values determine whether an unsubscribe link works: **the worker's (signs) and the API's (verifies).** The bridge's value cannot affect delivered mail. Its warning is real evidence that the variable was omitted when that service was configured — and both services were configured from the same template that names it wrong — but it is not evidence about the worker.

### The blast radius, and why "both unset" does not save you

The two fallbacks are different strings, so they do not agree with each other. Verified by computing both tokens:

```
worker-signed : 95cf0b44217846eeaf69b20a81fd9774141f23b209be7d28e17cb28c0e487b60
api-expected  : b8959e323a4681c64c7130067d1ea985adb7e21938763b78d6cc584fedfae283
compare_digest: False  ->  400 "Invalid unsubscribe token"
```

| Worker | API | Result |
|---|---|---|
| set to X | set to the same X | **works** (subject to the second defect below) |
| set to X | unset | every link 400s |
| unset | set to X | every link 400s |
| **unset** | **unset** | **every link 400s** — the dev fallbacks do not match each other |

**There is no configuration in which an unset secret degrades gracefully**, including the pure-development case. That strongly suggests this path has never worked locally either, which is consistent with nobody noticing.

### A second defect on the same path, independent of the secret

`send.py:133-138`, with the code's own comment:

```python
# Generate unsubscribe URLs (one per recipient)
# For v1, we'll use the first recipient's token for all
# (In production, you'd send individual emails with unique tokens)
first_recipient = recipients[0]
unsub_token = generate_unsubscribe_token(account_id, first_recipient)
unsubscribe_url = f"{WEB_BASE}/api/v1/email/unsubscribe?token={unsub_token}&email={first_recipient}"
```

One email body goes to every recipient, carrying **recipient #1's** email address and token. So even with both secrets set correctly and matching:

- Recipient #1 can unsubscribe.
- Every other recipient clicks a link that, if it succeeds, **suppresses recipient #1** and leaves the clicker subscribed.

`schedules` recipients are arrays, so any schedule with more than one recipient is affected. This is a CAN-SPAM problem that the secret being correct does not fix.

Two smaller issues on the same endpoint, worth recording while it is open:
- `unsubscribe.py:59-66` picks the account with `SELECT DISTINCT account_id … LIMIT 1` with no `ORDER BY`. An address on two accounts' schedules resolves arbitrarily, so the token may verify against the wrong account and 400.
- The docstring at `:49` says "Unsubscribe an email address from all schedules"; the insert at `:84-88` suppresses for **one** `account_id` only.

### What this costs across the 585 completed runs

Every one of those runs sent an email carrying an unsubscribe link. Whether any of them were functional reduces to one question — **is `EMAIL_UNSUB_SECRET` set, to the same value, on both the worker and the API?** — and even a "yes" leaves every non-first recipient of every multi-recipient schedule without a working unsubscribe.

**The one check that settles it:** read `EMAIL_UNSUB_SECRET` on the worker service and on the API service and compare them literally. Nothing else is needed and nothing in the repo can answer it.

---

## D1 — `ENV_TEMPLATE.md` audited against runtime reads

Both templates were checked line by line. Corrections are applied in this branch.

### `apps/worker/ENV_TEMPLATE.md`

**Documented, read by nothing:**

| Variable | Finding |
|---|---|
| `UNSUBSCRIBE_SECRET` (`:50`) | Wrong name. Code reads `EMAIL_UNSUB_SECRET`. **Corrected.** |
| `R2_ENDPOINT` (`:26`) | Not an input. `tasks.py:258` **computes** it: `f"https://{R2_ACCOUNT_ID}.r2.cloudflarestorage.com"`. Setting it does nothing. **Removed.** |
| `PDF_API_URL`, `PDF_API_KEY` (`:34-35`) | Read only by `pdf_adapter.py:18-19`, which has zero importers. Unreachable. **Removed**, replaced with the live `PDFSHIFT_API_KEY`. |
| `PDF_ENGINE=api` (`:33`) | Not a valid value for the module that renders. **Corrected to `pdfshift`.** |

**Read by worker code, absent from its template** — 33 names. The load-bearing ones (no safe default, or behaviour-changing) are now added: `PDFSHIFT_API_KEY`, `EMAIL_UNSUB_SECRET`, `RESEND_API_KEY`, `OPENAI_API_KEY`, `GOOGLE_MAPS_API_KEY`, `TWILIO_ACCOUNT_SID`, `TWILIO_AUTH_TOKEN`, `TWILIO_PHONE_NUMBER`, `R2_PUBLIC_URL`, `APP_BASE`, `FRONTEND_URL`, `EMAIL_FROM_ADDRESS`. The remainder are tuning knobs with working defaults (`SIMPLYRETS_RPM`, `PHOTO_PROXY_*`, `PDF_DIR`, `SOCIAL_DIR`, `R2_PRESIGN_EXPIRES_S`, `KEEP_ALIVE_INTERVAL`, `MR_REPORT_ENQUEUE_KEY`, `AI_INSIGHTS_ENABLED`, …) and are listed in a clearly-marked optional section rather than presented as required.

`PDFSHIFT_API_KEY` deserves its own line here: the worker's PDF engine is `pdfshift` in production, `pdf_engine.py:159-160` raises without this key, and **the worker's own template never mentioned it** while documenting two dead variables in its place.

`RESEND_API_KEY` likewise: it governs the false-`sent` consumer-report path, and the worker's template omitted it entirely.

### `apps/api/ENV_TEMPLATE.md`

**Documented, read by nothing in the API:** `PRINT_BASE` (`:35`) — read only by worker modules (`pdf_engine.py:33`, `social_engine.py:29`, `tasks.py:249`). Setting it on the API has no effect. **Removed**, with a pointer to the worker.

**Read by API code, absent from its template** — 33 names, of which these are load-bearing and are now added: `ENVIRONMENT`, `INTERNAL_RENDER_TOKEN`, `APP_BASE`, `APP_URL`, `STRIPE_SECRET_KEY`, `STRIPE_WEBHOOK_SECRET`, `STRIPE_PRICE_PRO_MONTH`, `STRIPE_PRICE_TEAM_MONTH`, `SITEX_BASE_URL`, `SITEX_CLIENT_ID`, `SITEX_CLIENT_SECRET`, `SITEX_FEED_ID`, `SIMPLYRETS_USERNAME`, `SIMPLYRETS_PASSWORD`, `R2_*`, `TWILIO_*`, `EMAIL_FROM_ADDRESS`, `EMAIL_REPLY_TO`.

**`ENVIRONMENT` is the one to notice.** `settings.py:11` defaults it to `"production"` deliberately, as a fail-safe, and it gates every dev-only route. It appeared in neither template. A deployer following these files has never been told the variable exists.

**One thing the API template already got right:** `:27` names `EMAIL_UNSUB_SECRET` correctly and `:57` states it must match the worker's. The two templates disagreed with each other about the same shared secret — which is precisely the mechanism that produces a mismatch.

---

## D2 — Repo-wide sweep

Sources compared: `apps/worker/ENV_TEMPLATE.md`, `apps/api/ENV_TEMPLATE.md`, `.env.example`, `LOCAL_SETUP_GUIDE.md`, `README.md`, `docs/architecture/SOURCE_OF_TRUTH.md`, `docs/architecture/backend-core.md`, and `settings.py`.

### Named in a document, read by no code anywhere

| Variable | Where it is documented | Reality |
|---|---|---|
| `UNSUBSCRIBE_SECRET` | `apps/worker/ENV_TEMPLATE.md:50` | Code reads `EMAIL_UNSUB_SECRET`. **Live misconfiguration.** |
| `R2_ENDPOINT` | `apps/worker/ENV_TEMPLATE.md:26` | Computed from `R2_ACCOUNT_ID` at `tasks.py:258` |
| `NEXT_PUBLIC_DEMO_ACCOUNT_ID` | `LOCAL_SETUP_GUIDE.md` | No reader in Python or TS |
| `STARTER_PRICE_ID` | `settings.py:20` | No reader; live name is `STRIPE_PRICE_PRO_MONTH`/`_TEAM_MONTH` |
| `PRO_PRICE_ID` | `settings.py:21` | No reader |
| `ENTERPRISE_PRICE_ID` | `settings.py:22` | No reader |
| `PDF_API_URL`, `PDF_API_KEY` | `.env.example:91-92`, both templates | Read only by `pdf_adapter.py`, which has zero importers. `PDF_API_KEY` is the exception — `branding_tools.py:119` does read it, which is instance 3 above. |

### Read by code, named in no document

Load-bearing:

| Variable | Read at | Why it matters |
|---|---|---|
| `ENVIRONMENT` | `settings.py:11`, `routes/admin.py`, `unsubscribe.py:102` | Gates every dev-only route; fail-safe default is `production` |
| `INTERNAL_RENDER_TOKEN` | `settings.py:32`, `print/[runId]/page.tsx:49` | Without it the print page 401s against `/v1/reports/{id}/data` |
| `APP_URL` | `routes/me.py:13` | A **sixth** name for the web app — see below |
| `EMAIL_UNSUB_SECRET` | `email/send.py:16` | Documented under the wrong name on the worker |
| `PDFSHIFT_API_KEY` | `pdf_engine.py:31`, `social_engine.py:28` | The live PDF credential; absent from the worker template |
| `RESEND_API_KEY` | `tasks.py:668,1894` | Absent from the worker template |
| `OPENAI_API_KEY`, `GOOGLE_MAPS_API_KEY` | `property_builder.py:198-199` | Absent from the worker template |
| `TWILIO_ACCOUNT_SID` / `_AUTH_TOKEN` / `_PHONE_NUMBER` | `tasks.py:1868`, sms service | Absent from both templates |
| `SITEX_*` (4) | `services/sitex.py:39-42` | Absent from the API template |
| `SIMPLYRETS_USERNAME` / `_PASSWORD` | API and worker | Present in `.env.example` only |
| `R2_PUBLIC_URL` | worker + API | Absent from both templates |

Tooling-only, correctly undocumented: `ANALYZE`, `NODE_ENV`, `PORT`, `APP_NAME`, `TEMP`, `TEST_DATABASE_URL`, `E2E_*`, `QA_*`, `TEST_AUTH_TOKEN`, `MR_TOKEN`, `PDF_REVIEW_OUT`, `PREVIEW_SCREENSHOTS_DIR`.

### Six names for one URL

The largest single cluster, and the reason base-URL bugs keep recurring:

| Variable | Read at | Default |
|---|---|---|
| `PRINT_BASE` | `pdf_engine.py:33`, `social_engine.py:29`, `tasks.py:249` | `http://localhost:3000` |
| `WEB_BASE` | `email/send.py:13` | `http://localhost:3000` |
| `WEB_BASE` | `routes/billing.py:21` | `https://reportscompany-web.vercel.app` |
| `APP_BASE` | `settings.py:23` | `https://www.trendyreports.io` |
| `APP_BASE` | `tasks.py:713` | `https://reportscompany-web.vercel.app` |
| `FRONTEND_URL` | `tasks.py:1497` | `https://www.trendyreports.io` |
| `APP_URL` | `routes/me.py:13` | `https://trendyreports.io` |
| `NEXT_PUBLIC_API_BASE` | `tasks.py:324`, web | `https://reportscompany.onrender.com` |

`WEB_BASE` and `APP_BASE` each resolve to a **different default in different services**, so setting either correctly on one service says nothing about the other. Consolidating these is its own ticket; the audit records it because it is the same root cause — no single declared source of truth for environment names.

### What would prevent the whole class

Nothing in this codebase validates configuration at startup. Every variable is read with a fallback, so a typo, a renamed variable, or a variable set on the wrong service is indistinguishable from correct configuration until a user hits the feature. A startup check that fails loudly on missing required names — or simply a single module per service that declares them, which is what `settings.py` was supposed to be for the API — would have caught all four instances. Recorded as a recommendation, not done here; it is a code change beyond this branch's scope.

---

## D4 — `[DIAGNOSTIC]` startup logging

`apps/worker/src/worker/property_builder.py:200-204` logs, at `WARNING` level on every process start that imports the module:

```python
logger.warning("[DIAGNOSTIC] property_builder loaded at startup")
logger.warning("[DIAGNOSTIC] GOOGLE_MAPS_API_KEY present: %s, length: %d", bool(...), len(...))
logger.warning("[DIAGNOSTIC] OPENAI_API_KEY present: %s, length: %d", bool(...), len(...))
logger.warning("[DIAGNOSTIC] TEMPLATES_DIR: %s, exists: %s", ...)
```

Flagged as out of scope in Phase 0; removed in this branch. It writes **API key lengths** to production logs on every restart, which narrows the search space for anyone reading them, and — as established at the top of this document — its output was actively misleading as configuration evidence.

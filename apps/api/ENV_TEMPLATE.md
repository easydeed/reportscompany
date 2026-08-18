# API Service Environment Variables Template

Copy these variables to your Render service environment settings.

> **Every name below was verified against a runtime read** — either an
> `os.getenv` call or a field on the `Settings` model
> (`apps/api/src/api/settings.py`). Each entry cites the file that reads it.
> The previous version of this file documented 11 variables while the API reads
> 44, and one of the 11 (`PRINT_BASE`) is read only by the worker. See
> `docs/ENV_VAR_AUDIT.md`.

## Required

### Core

```bash
DATABASE_URL=postgresql://user:password@host:5432/database   # settings.py:12
REDIS_URL=rediss://default:password@host:6379?ssl_cert_reqs=CERT_REQUIRED   # settings.py:13
JWT_SECRET=your_long_random_secret_here_32_chars_minimum     # settings.py:14
ALLOWED_ORIGINS=["https://your-app.vercel.app","http://localhost:3000"]   # settings.py:15
ENVIRONMENT=production                                        # settings.py:11
```

**`ENVIRONMENT` gates every dev-only route** (`/v1/auth/seed-dev`, `/dev-files/*`,
the unsubscribe token generator at `routes/unsubscribe.py:102`, and others). It
defaults to `production` as a fail-safe, so a deploy that omits it is safe —
but set it explicitly, and set it to `development` **only** in local and staging.
It was absent from this template entirely until now.

`ALLOWED_ORIGINS` must be a JSON array, quotes included.

### Unsubscribe endpoint

```bash
EMAIL_UNSUB_SECRET=same_secret_as_worker_service   # routes/unsubscribe.py:12
WEB_BASE=https://your-app.vercel.app               # routes/billing.py:21
```

`EMAIL_UNSUB_SECRET` **must be byte-identical to the worker's.** The worker
signs the unsubscribe token, this service verifies it. If they differ — or if
either is unset, since the two services fall back to *different* dev defaults —
every unsubscribe link returns HTTP 400 on click. Nothing detects this at
startup. See `docs/ENV_VAR_AUDIT.md` for the full trace.

Note `WEB_BASE` here is the **Stripe return URL** base (`billing.py:206-207,303`),
and its default (`reportscompany-web.vercel.app`) differs from the worker's
default for the same variable name.

### Billing — Stripe

```bash
STRIPE_SECRET_KEY=sk_live_...              # settings.py:19
STRIPE_WEBHOOK_SECRET=whsec_...            # settings.py:24
STRIPE_PRICE_PRO_MONTH=price_...           # config/billing.py:18
STRIPE_PRICE_TEAM_MONTH=price_...          # config/billing.py:19
```

**The price-ID variables are `STRIPE_PRICE_PRO_MONTH` and
`STRIPE_PRICE_TEAM_MONTH`.** `settings.py:20-22` also declares
`STARTER_PRICE_ID`, `PRO_PRICE_ID` and `ENTERPRISE_PRICE_ID`, but **no code
reads those three** — setting them configures nothing. `config/billing.py:70-80`
is the authority; its missing-config error lists the names that actually matter.

### Email — branding test emails and invites

```bash
SENDGRID_API_KEY=SG.your_sendgrid_api_key_here      # settings.py:35
EMAIL_FROM_ADDRESS=TrendyReports <noreply@yourdomain.com>   # settings.py:37
EMAIL_REPLY_TO=support@yourdomain.com               # settings.py:38
DEFAULT_FROM_EMAIL=reports@trendyreports.io         # routes/branding_tools.py:125
DEFAULT_FROM_NAME=TrendyReports                     # routes/branding_tools.py:126
```

Scheduled report emails are sent by the **worker**, not the API. These cover the
branding "Send Test Email" feature and transactional invite mail.

`settings.py:36` declares `RESEND_API_KEY` and marks it deprecated/unused. That
is accurate **for the API**; the worker does read it, and it is required there.

### Web app URLs

```bash
APP_BASE=https://www.yourdomain.com    # settings.py:23 — invite links (invite_service.py:160, admin.py:2488)
APP_URL=https://yourdomain.com         # routes/me.py:13 — public CMA lead-page links
```

### Internal render token

```bash
INTERNAL_RENDER_TOKEN=long_random_value   # settings.py:32
```

Lets the Next.js print page and social image route read `/v1/reports/{id}/data`
server-side without a user session. Must match the value set on Vercel. When
empty, that path is disabled and `/print/{runId}` — the "view in browser" link
sent to customers — renders "Report Not Found".

## Required only for the features that use them

### SiteX Pro (property data)

```bash
SITEX_BASE_URL=https://api.bkiconnect.com   # services/sitex.py:39
SITEX_CLIENT_ID=your_sitex_client_id        # services/sitex.py:40
SITEX_CLIENT_SECRET=your_sitex_client_secret # services/sitex.py:41
SITEX_FEED_ID=your_feed_id                  # services/sitex.py:42
```

**`SITEX_BASE_URL` defaults to the UAT gateway** (`https://api.uat.bkitest.com`).
Unset in production means property reports are built from test data, with no
error. All four must be production values together — a production host with UAT
credentials fails at the token call.

### SimplyRETS MLS API

```bash
SIMPLYRETS_USERNAME=your_simplyrets_username   # services/simplyrets, routes/property.py
SIMPLYRETS_PASSWORD=your_simplyrets_password
SIMPLYRETS_TIMEOUT_S=...                       # optional
```

### Cloudflare R2 (branding asset uploads)

```bash
R2_ACCOUNT_ID=your_account_id
R2_ACCESS_KEY_ID=your_access_key
R2_SECRET_ACCESS_KEY=your_secret_key
R2_BUCKET_NAME=market-reports
R2_PUBLIC_URL=https://your-r2-public-domain
```

### SMS

```bash
TWILIO_ACCOUNT_SID=your_twilio_sid
TWILIO_AUTH_TOKEN=your_twilio_token
TWILIO_PHONE_NUMBER=+15555551234
```

### Worker queue

```bash
MR_REPORT_ENQUEUE_KEY=mr:enqueue:reports   # worker_client.py:6
```

Must match the worker's value, or reports queued by `POST /v1/reports` are never
picked up. Both default to `mr:enqueue:reports`, so leaving both unset is safe;
setting one and not the other is not.

### PDF — branding sample generation

```bash
PDF_API_KEY=your_pdfshift_api_key_here   # routes/branding_tools.py:119
```

**This is a naming defect, documented rather than silently reproduced.**
`branding_tools.py:119` reads `PDF_API_KEY`, while every other PDFShift call
site in the codebase reads `PDFSHIFT_API_KEY`. Until that is reconciled, the
branding sample-PDF and sample-JPG endpoints need `PDF_API_KEY` set specifically,
or they return 503 (`branding_tools.py:335-339`, `:428-432`). Setting both to
the same value is the safe interim.

---

**Not on this list, deliberately:**

- `PRINT_BASE` — read only by the worker (`pdf_engine.py:33`, `social_engine.py:29`).
  Setting it on the API has no effect.
- `STARTER_PRICE_ID`, `PRO_PRICE_ID`, `ENTERPRISE_PRICE_ID` — declared in
  `settings.py:20-22`, read by nothing.

**Cross-service consistency requirements:**

- `EMAIL_UNSUB_SECRET` must be identical to the worker's.
- `MR_REPORT_ENQUEUE_KEY` must be identical to the worker's.
- `INTERNAL_RENDER_TOKEN` must be identical to Vercel's.
- `SENDGRID_API_KEY` should be the same account as the worker's.

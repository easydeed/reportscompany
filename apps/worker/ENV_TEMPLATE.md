# Worker Service Environment Variables Template

Copy these variables to your Render service environment settings.

> **Every name below was verified against a runtime read.** Each entry cites the
> file that reads it. Do not add a variable here without confirming something
> reads that exact string — the previous version of this file documented three
> names that no code reads (`UNSUBSCRIBE_SECRET`, `R2_ENDPOINT`, `PDF_API_URL`)
> and one value that makes PDF rendering raise (`PDF_ENGINE=api`). See
> `docs/ENV_VAR_AUDIT.md`.

Applies to the worker and to any service that imports `worker.tasks` — the
ticker (`markets-report-ticker`) and the consumer bridge
(`reportscompany-consumer-bridge`). Those two run different entry points but
share this module, so they need the variables their own code path touches.

## Required

### Database & Cache

```bash
DATABASE_URL=postgresql://user:password@host:5432/database   # tasks.py:248
REDIS_URL=rediss://default:password@host:6379?ssl_cert_reqs=CERT_REQUIRED   # tasks.py:246, app.py
CELERY_RESULT_URL=rediss://default:password@host:6379?ssl_cert_reqs=CERT_REQUIRED   # app.py
```

### SimplyRETS MLS API

```bash
SIMPLYRETS_USERNAME=your_simplyrets_username   # vendors/simplyrets.py
SIMPLYRETS_PASSWORD=your_simplyrets_password   # vendors/simplyrets.py
```

### Cloudflare R2 Storage

```bash
R2_ACCOUNT_ID=your_account_id_here          # tasks.py:254
R2_ACCESS_KEY_ID=your_access_key_here       # tasks.py:255
R2_SECRET_ACCESS_KEY=your_secret_key_here   # tasks.py:256
R2_BUCKET_NAME=market-reports               # tasks.py:257
R2_PUBLIC_URL=https://your-r2-public-domain # property_tasks/property_report.py
```

**`R2_ENDPOINT` is not an input.** `tasks.py:258` computes it as
`https://{R2_ACCOUNT_ID}.r2.cloudflarestorage.com`. Setting it does nothing.

### PDF Generation

```bash
PDF_ENGINE=pdfshift                         # pdf_engine.py:30
PDFSHIFT_API_KEY=your_pdfshift_api_key_here # pdf_engine.py:31, social_engine.py:28
PRINT_BASE=https://your-app.vercel.app      # pdf_engine.py:33, social_engine.py:29, tasks.py:249
```

`PDF_ENGINE` accepts **only** `playwright` or `pdfshift` (`pdf_engine.py:342-359`);
any other value raises `ValueError` on every render. With `pdfshift`,
`PDFSHIFT_API_KEY` is mandatory — `pdf_engine.py:159-160` raises without it.
With `playwright`, page headers and footers are silently discarded
(`pdf_engine.py:79`), so market reports render unbranded.

`PRINT_BASE` is not only used for rendering: `render_pdf` returns
`{PRINT_BASE}/print/{run_id}`, which is stored as `reports.html_url` and shown
to customers as a "view in browser" link. It must be the public web app URL.

### Email — SendGrid (report delivery)

```bash
SENDGRID_API_KEY=SG.your_sendgrid_api_key_here   # email/providers/sendgrid.py
DEFAULT_FROM_EMAIL=reports@yourdomain.com        # email/providers/sendgrid.py
DEFAULT_FROM_NAME=TrendyReports                  # email/providers/sendgrid.py
EMAIL_FROM_ADDRESS=TrendyReports <noreply@yourdomain.com>   # tasks.py:791,1983
```

### Email — Resend (failure notices + consumer report delivery)

```bash
RESEND_API_KEY=re_your_resend_api_key_here   # tasks.py:668, tasks.py:1894
```

Separate provider from SendGrid, and **not optional**. Two paths use it:
schedule-failure notifications (`tasks.py:654-671`) and consumer/lead report
delivery (`tasks.py:1894`). When unset, the second path marks the report
`status='sent'` with a `consumer_email_sent_at` timestamp **without sending
anything**.

### Unsubscribe links

```bash
EMAIL_UNSUB_SECRET=your_long_random_secret_here_32_chars_minimum   # email/send.py:16
WEB_BASE=https://your-app.vercel.app                              # email/send.py:13
```

**The variable is `EMAIL_UNSUB_SECRET`, not `UNSUBSCRIBE_SECRET`.** Earlier
versions of this file named the latter, which nothing reads.

**It must be byte-identical to the API service's `EMAIL_UNSUB_SECRET`.** The
worker signs the unsubscribe token and the API verifies it. If the two differ —
or if either is unset, since the two services fall back to *different* dev
defaults — every unsubscribe link returns HTTP 400 on click. Nothing detects
this at startup.

`WEB_BASE` is the host in the unsubscribe URL (`email/send.py:138`). Unset means
every outbound email carries a `http://localhost:3000` unsubscribe link.

### Web app URLs

```bash
APP_BASE=https://your-app.vercel.app       # tasks.py:713  (failure-notice links)
FRONTEND_URL=https://www.yourdomain.com    # tasks.py:1497 (consumer report links)
API_BASE_URL=https://your-api.onrender.com # tasks.py:324, schedules_tick.py
```

These are four separate names for overlapping URLs, each with its own default
(`PRINT_BASE`, `WEB_BASE`, `APP_BASE`, `FRONTEND_URL`). Set all of them
explicitly; the defaults disagree with each other. Consolidation is tracked in
`docs/ENV_VAR_AUDIT.md`.

## Required only for the features that use them

### Property reports

```bash
GOOGLE_MAPS_API_KEY=your_google_maps_key   # property_builder.py:198 (maps, geocoding)
ASSETS_BASE_URL=https://assets.trendyreports.com   # property_builder.py:197
```

### AI narrative / insights

```bash
OPENAI_API_KEY=sk-your_openai_key          # ai_insights.py, ai_market_narrative.py
AI_INSIGHTS_ENABLED=true                   # ai_insights.py
```

### SMS (consumer report delivery + agent lead notifications)

```bash
TWILIO_ACCOUNT_SID=your_twilio_sid         # sms/send.py
TWILIO_AUTH_TOKEN=your_twilio_token        # sms/send.py
TWILIO_PHONE_NUMBER=+15555551234           # sms/send.py, tasks.py:1868
```

## Optional — tuning knobs with working defaults

Listed for completeness. All are read by worker code; none need to be set.

```bash
TICK_INTERVAL=60                  # schedules_tick.py — seconds between schedule checks
KEEP_ALIVE_INTERVAL=...           # schedules_tick.py
MR_REPORT_ENQUEUE_KEY=mr:enqueue:reports   # tasks.py:247 — must match the API's value
PDF_DIR=/tmp/mr_reports           # pdf_engine.py:34
SOCIAL_DIR=/tmp/mr_social         # social_engine.py:30
PDFSHIFT_API_URL=...              # pdf_engine.py:32
R2_PRESIGN_EXPIRES_S=...          # utils/photo_proxy.py
PHOTO_PROXY_ENABLED=...           # utils/photo_proxy.py
PHOTO_PROXY_FETCH_TIMEOUT_S=...   # utils/photo_proxy.py
PHOTO_PROXY_MAX_RETRIES=...       # utils/photo_proxy.py
PHOTO_PROXY_RETRY_DELAY_S=...     # utils/photo_proxy.py
SIMPLYRETS_BASE_URL=...           # vendors/simplyrets.py
SIMPLYRETS_VENDOR=...             # vendors/simplyrets.py
SIMPLYRETS_RPM=...                # vendors/simplyrets.py — rate limit
SIMPLYRETS_BURST=...              # vendors/simplyrets.py
SIMPLYRETS_TIMEOUT_S=...          # vendors/simplyrets.py
SIMPLYRETS_MAX_RESULTS=...        # vendors/simplyrets.py
SIMPLYRETS_ALLOW_SORT=...         # query_builders.py
```

---

**Cross-service consistency requirements:**

- `EMAIL_UNSUB_SECRET` must be identical on the worker and the API.
- `MR_REPORT_ENQUEUE_KEY` must be identical on the worker/bridge and the API
  (`apps/api/src/api/worker_client.py:6`), or queued reports are never picked up.
- `SENDGRID_API_KEY` is used by both; keep them the same account.
- All of the above must also be set on `reportscompany-consumer-bridge` and
  `markets-report-ticker`, which import the same module.

**Not on this list, deliberately:** `UNSUBSCRIBE_SECRET`, `R2_ENDPOINT`,
`PDF_API_URL`, `PDF_API_KEY`. Nothing in the worker reads any of them.

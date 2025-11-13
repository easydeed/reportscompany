# Worker Service Environment Variables Template

Copy these variables to your Render service environment settings.

## Database & Cache

```bash
DATABASE_URL=postgresql://user:password@host:5432/database
REDIS_URL=rediss://default:password@host:6379?ssl_cert_reqs=CERT_REQUIRED
CELERY_RESULT_URL=rediss://default:password@host:6379?ssl_cert_reqs=CERT_REQUIRED
```

## SimplyRETS MLS API

```bash
SIMPLYRETS_USERNAME=info_456z6zv2
SIMPLYRETS_PASSWORD=lm0182gh3pu6f827
```

## Cloudflare R2 Storage

```bash
R2_ACCOUNT_ID=your_account_id_here
R2_ACCESS_KEY_ID=your_access_key_here
R2_SECRET_ACCESS_KEY=your_secret_key_here
R2_BUCKET_NAME=market-reports
R2_ENDPOINT=https://your-account-id.r2.cloudflarestorage.com
```

## PDF Generation

```bash
PDF_ENGINE=api
PDF_API_URL=https://api.pdfshift.io/v3/convert/pdf
PDF_API_KEY=your_pdfshift_api_key_here
PRINT_BASE=https://your-app.vercel.app
```

## Email Provider (SendGrid) - Phase 27A

```bash
SENDGRID_API_KEY=SG.your_sendgrid_api_key_here
DEFAULT_FROM_EMAIL=reports@yourdomain.com
DEFAULT_FROM_NAME=TrendyReports
```

## Unsubscribe & Web Links - Phase 27A

```bash
UNSUBSCRIBE_SECRET=your_long_random_secret_here_32_chars_minimum
WEB_BASE=https://your-app.vercel.app
```

## Optional Settings

```bash
TICK_INTERVAL=60  # Seconds between schedule checks
```

---

**Total Variables:** 18
- 3 Database/Redis
- 2 SimplyRETS
- 5 R2 Storage
- 3 PDF Generation
- 5 Email/Unsubscribe (Phase 27A)

**Note:** All Phase 27A email variables must also be set on:
- `reportscompany - worker-service`
- `reportscompany-consumer-bridge`
- `markets-report-ticker`


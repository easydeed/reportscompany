# API Service Environment Variables Template

Copy these variables to your Render service environment settings.

## Database & Cache

```bash
DATABASE_URL=postgresql://user:password@host:5432/database
REDIS_URL=rediss://default:password@host:6379?ssl_cert_reqs=CERT_REQUIRED
```

## Authentication

```bash
JWT_SECRET=your_long_random_secret_here_32_chars_minimum
```

## CORS Configuration

```bash
ALLOWED_ORIGINS=["https://your-app.vercel.app","http://localhost:3000"]
```

## Unsubscribe Endpoint - Phase 27A

```bash
EMAIL_UNSUB_SECRET=same_secret_as_worker_service
WEB_BASE=https://your-app.vercel.app
```

## PDF Generation - Branding Tools

```bash
PDF_API_KEY=your_pdfshift_api_key_here
PRINT_BASE=https://www.trendyreports.io
```

## Email - Branding Test Emails (Optional)

```bash
SENDGRID_API_KEY=SG.your_sendgrid_api_key_here
DEFAULT_FROM_EMAIL=reports@trendyreports.io
DEFAULT_FROM_NAME=TrendyReports
```

---

**Total Variables:** 11
- 2 Database/Redis
- 1 Authentication
- 1 CORS
- 2 Unsubscribe (Phase 27A)
- 2 PDF Generation
- 3 Email (Branding test emails)

**Important Notes:**
- `EMAIL_UNSUB_SECRET` **must match** the worker service secret exactly
- `ALLOWED_ORIGINS` must be a JSON array (include quotes)
- `SENDGRID_API_KEY` is needed for the branding "Send Test Email" feature
- Copy `SENDGRID_API_KEY` from the worker service to keep consistent
- Scheduled report emails are sent by the worker, not the API


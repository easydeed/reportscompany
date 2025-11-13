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
UNSUBSCRIBE_SECRET=same_secret_as_worker_service
WEB_BASE=https://your-app.vercel.app
```

---

**Total Variables:** 6
- 2 Database/Redis
- 1 Authentication
- 1 CORS
- 2 Unsubscribe (Phase 27A)

**Important Notes:**
- `UNSUBSCRIBE_SECRET` **must match** the worker service secret exactly
- `ALLOWED_ORIGINS` must be a JSON array (include quotes)
- API service does NOT need SendGrid keys (only worker services send emails)
- API service uses these vars for the `/v1/email/unsubscribe` endpoint only


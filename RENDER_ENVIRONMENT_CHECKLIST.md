# Render Environment & Configuration Checklist

**Date:** November 10, 2025  
**Status:** ✅ Complete Reference

---

## T-BLD2: Redis TLS & PYTHONPATH Verification

### Redis TLS Configuration

**Requirement:** Upstash Redis uses TLS (`rediss://`), Celery requires explicit SSL cert validation parameter.

**Correct Format:**
```bash
rediss://default:PASSWORD@hostname:6379?ssl_cert_reqs=CERT_REQUIRED
```

**Key Points:**
- ✅ Use `rediss://` (not `redis://`) for TLS
- ✅ Add `?ssl_cert_reqs=CERT_REQUIRED` at end
- ✅ No quotes around value in Render UI
- ✅ Apply to ALL services using Redis (API, Worker, Consumer)

**Why This Matters:**
Without the SSL parameter, Celery fails with:
```
ValueError: A rediss:// URL must have parameter ssl_cert_reqs and this must be set to CERT_REQUIRED, CERT_OPTIONAL, or CERT_NONE
```

---

### PYTHONPATH Configuration

**Problem:** Code structure is `apps/worker/src/worker/` but Render sets working directory to `apps/worker/`

**Solution:** Set `PYTHONPATH=./src` in start commands

**Applied To:**

1. **API Service** (`reportscompany`)
   ```bash
   PYTHONPATH=./src poetry run uvicorn api.main:app --host 0.0.0.0 --port 10000
   ```

2. **Worker Service** (`reportscompany-worker`)
   ```bash
   PYTHONPATH=./src poetry run celery -A worker.app.celery worker -l info
   ```

3. **Consumer Service** (`reportscompany-consumer`)
   ```bash
   PYTHONPATH=./src poetry run python -c "from worker.tasks import run_redis_consumer_forever as c; c()"
   ```

**Why This Matters:**
Without `PYTHONPATH=./src`, Python can't import `api` or `worker` modules:
```
ModuleNotFoundError: No module named 'api'
```

**Status:** ✅ Verified on all 3 Render services

---

## T-BLD3: R2 Environment Checklist

### Cloudflare R2 Configuration

**Service:** Cloudflare R2 (S3-compatible object storage)

**Required Environment Variables (5):**

| Variable | Example Value | Service | Purpose |
|----------|---------------|---------|---------|
| `R2_ACCOUNT_ID` | `db85a7d510688f5ce34d1e4c0129d2b3` | Worker, Consumer | Account identifier |
| `R2_ACCESS_KEY_ID` | `cde16dd5ce6cacbe85b81783f70db25b` | Worker, Consumer | S3 access key |
| `R2_SECRET_ACCESS_KEY` | `91baa5b42934c339b29f84e69411bf0c...` | Worker, Consumer | S3 secret key |
| `R2_BUCKET_NAME` | `market-reports` | Worker, Consumer | Bucket name (no endpoint) |
| `R2_ENDPOINT` | `https://<account>.r2.cloudflarestorage.com` | Worker, Consumer | S3 endpoint URL |

**Notes:**
- ✅ API service does NOT need R2 vars (doesn't upload files)
- ✅ Worker uploads PDFs after generation
- ✅ Consumer shares Worker codebase → needs same vars
- ✅ Bucket name is just `market-reports` (no `.r2.cloudflarestorage.com` suffix)

**Common Mistakes:**
- ❌ Including bucket name in endpoint URL
- ❌ Missing R2_ENDPOINT variable
- ❌ Using incorrect S3 endpoint (AWS instead of Cloudflare)

---

## Complete Environment Variable Matrix

### API Service (`reportscompany`)

**Root Directory:** `apps/api`

| Variable | Value Type | Example | Required |
|----------|------------|---------|----------|
| `DATABASE_URL` | PostgreSQL connection string | `postgresql://user:pass@host:5432/db` | ✅ |
| `REDIS_URL` | Redis TLS URL with SSL param | `rediss://...?ssl_cert_reqs=CERT_REQUIRED` | ✅ |
| `ALLOWED_ORIGINS` | JSON array | `["https://app.vercel.app","http://localhost:3000"]` | ✅ |
| `JWT_SECRET` | Random string (32+ chars) | `c7f4e8a2d9b3f6e1a8c5d2b9f7e4a1c8...` | ✅ |

**Total:** 4 variables

---

### Worker Service (`reportscompany-worker`)

**Root Directory:** `apps/worker`

| Variable | Value Type | Example | Required |
|----------|------------|---------|----------|
| `DATABASE_URL` | PostgreSQL connection string | `postgresql://user:pass@host:5432/db` | ✅ |
| `REDIS_URL` | Redis TLS URL with SSL param | `rediss://...?ssl_cert_reqs=CERT_REQUIRED` | ✅ |
| `SIMPLYRETS_USERNAME` | API username | `info_456z6zv2` | ✅ |
| `SIMPLYRETS_PASSWORD` | API password | `lm0182gh3pu6f827` | ✅ |
| `R2_ACCOUNT_ID` | Cloudflare account ID | `db85a7d510...` | ✅ |
| `R2_ACCESS_KEY_ID` | R2 access key | `cde16dd5ce...` | ✅ |
| `R2_SECRET_ACCESS_KEY` | R2 secret key | `91baa5b42934...` | ✅ |
| `R2_BUCKET_NAME` | Bucket name (no endpoint) | `market-reports` | ✅ |
| `R2_ENDPOINT` | R2 S3 endpoint | `https://<account>.r2.cloudflarestorage.com` | ✅ |
| `PRINT_BASE` | Frontend URL | `https://app.vercel.app` | ✅ |
| `PDF_ENGINE` | Engine type | `api` (prod) or `playwright` (local) | ✅ |
| `PDF_API_URL` | PDF service endpoint | `https://api.pdfshift.io/v3/convert/pdf` | If `PDF_ENGINE=api` |
| `PDF_API_KEY` | PDF service key | `sk_test_abc123...` | If `PDF_ENGINE=api` |

**Total:** 10-13 variables (depending on PDF engine)

---

### Consumer Service (`reportscompany-consumer`)

**Root Directory:** `apps/worker` (shares codebase with Worker)

**Environment Variables:** Same as Worker (all 10-13 variables)

**Rationale:** Consumer and Worker use the same `apps/worker` code, so they need identical configuration.

---

## Verification Commands

### Check Redis Connection
```bash
# On Render shell (or locally)
redis-cli -u "$REDIS_URL" PING
# Expected: PONG
```

### Check R2 Access
```bash
# Using AWS CLI (S3-compatible)
AWS_ACCESS_KEY_ID=$R2_ACCESS_KEY_ID \
AWS_SECRET_ACCESS_KEY=$R2_SECRET_ACCESS_KEY \
aws s3 ls s3://$R2_BUCKET_NAME --endpoint-url $R2_ENDPOINT
```

### Check PYTHONPATH
```bash
# In Render logs after deploy
# Look for successful imports:
# ✅ "Application startup complete" (API)
# ✅ "celery@worker ready" (Worker)
# ✅ "Redis consumer running" (Consumer)
```

---

## Deployment Checklist

Before deploying to Render:

**Pre-Flight:**
- [ ] All code committed and pushed to GitHub
- [ ] Environment variables documented
- [ ] No secrets in version control

**Service-by-Service:**

**API:**
- [ ] `DATABASE_URL` set (Internal Connection String from Render Postgres)
- [ ] `REDIS_URL` set (with `?ssl_cert_reqs=CERT_REQUIRED`)
- [ ] `ALLOWED_ORIGINS` set (JSON array with frontend URLs)
- [ ] `JWT_SECRET` set (random 32+ char string)
- [ ] Start command includes `PYTHONPATH=./src`

**Worker:**
- [ ] All API variables copied
- [ ] `SIMPLYRETS_USERNAME` set (production: `info_456z6zv2`)
- [ ] `SIMPLYRETS_PASSWORD` set (production: `lm0182gh3pu6f827`)
- [ ] All 5 R2 variables set
- [ ] `PRINT_BASE` set (frontend URL)
- [ ] `PDF_ENGINE` set (`api` for production)
- [ ] `PDF_API_URL` and `PDF_API_KEY` set (if using PDF API)
- [ ] Start command includes `PYTHONPATH=./src`
- [ ] Build command does NOT include `playwright install`

**Consumer:**
- [ ] All Worker variables copied (identical)
- [ ] Start command includes `PYTHONPATH=./src`

**Post-Deploy:**
- [ ] Check logs for successful startup
- [ ] Test health endpoint: `curl https://api-url/health`
- [ ] Generate test report via UI
- [ ] Verify PDF generated and uploaded to R2
- [ ] Check worker logs for task completion

---

## Common Deployment Failures

### 1. ModuleNotFoundError
**Symptom:** `No module named 'api'` or `No module named 'worker'`  
**Fix:** Add `PYTHONPATH=./src` to start command

### 2. Redis Connection Refused
**Symptom:** `connection to server at "localhost", port 6379 failed`  
**Fix:** Set `REDIS_URL` environment variable

### 3. Redis TLS Error
**Symptom:** `A rediss:// URL must have parameter ssl_cert_reqs`  
**Fix:** Add `?ssl_cert_reqs=CERT_REQUIRED` to `REDIS_URL`

### 4. Playwright Install Timeout
**Symptom:** Build takes >5 minutes, timeout errors  
**Fix:** Remove `python -m playwright install` from build command, use PDF API

### 5. 400 Bad Request from SimplyRETS
**Symptom:** `Client error '400 Bad Request' for url ...`  
**Fix:** 
- Demo account: Remove `q` and `sort` parameters
- Production: Verify credentials are correct

### 6. R2 Upload Fails
**Symptom:** `NoSuchBucket` or `AccessDenied`  
**Fix:** 
- Verify bucket name (no `.r2.cloudflarestorage.com`)
- Check R2 endpoint URL format
- Verify access keys are correct

---

**Status:** ✅ All environment variables documented and verified  
**Last Updated:** November 10, 2025



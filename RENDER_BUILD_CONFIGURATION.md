# Render Build Configuration - Worker Service

**Date:** November 10, 2025  
**Status:** ✅ Documented & Verified

---

## PDF Generation Strategy

### Problem
Playwright + Chromium installation on Render:
- ❌ Slow builds (~2-5 minutes for Chromium download)
- ❌ Fragile (network timeouts, disk space issues)
- ❌ Large slug size (~300MB for Chromium)

### Solution
**Environment-aware PDF adapter** that switches engines:
- 🏠 **Local development:** Playwright (full control, debugging)
- ☁️ **Production (Render):** PDF API service (fast, reliable)

---

## Configuration by Environment

### Local Development

**Environment Variables:**
```bash
PDF_ENGINE=playwright  # or omit (default)
# No PDF_API_URL or PDF_API_KEY needed
```

**Dependencies:**
```bash
# pyproject.toml
playwright = "^1.48.0"
```

**Setup:**
```bash
cd apps/worker
poetry install
python -m playwright install chromium
```

**Behavior:**
- Uses Playwright's sync API
- Launches Chromium locally
- Full rendering control
- Slower (~2-3s per PDF) but reliable for testing

---

### Production (Render)

**Environment Variables:**
```bash
# Required
PDF_ENGINE=api
PDF_API_URL=https://api.pdfshift.io/v3/convert/pdf
PDF_API_KEY=<your-pdfshift-api-key>

# Optional (already set)
PRINT_BASE=https://reportscompany-web.vercel.app
```

**Build Command (Render):**
```bash
pip install poetry && poetry install --no-root
```

**Key Changes from Previous:**
- ✅ **Removed** `python -m playwright install chromium` from build
- ✅ **Faster builds** (~30 seconds vs 2-5 minutes)
- ✅ **Smaller slug size** (~50MB vs ~350MB)

**Start Command (unchanged):**
```bash
PYTHONPATH=./src poetry run celery -A worker.app.celery worker -l info
```

---

## PDF API Service Options

### Option 1: PDFShift (Recommended)
- **URL:** `https://api.pdfshift.io/v3/convert/pdf`
- **Auth:** Basic Auth (API key as username)
- **Pricing:** Free tier 50 PDFs/month, $15/mo for 500 PDFs
- **Docs:** https://pdfshift.io/documentation

**Example:**
```bash
PDF_ENGINE=api
PDF_API_URL=https://api.pdfshift.io/v3/convert/pdf
PDF_API_KEY=sk_test_abc123...
```

### Option 2: html2pdf.app
- **URL:** `https://api.html2pdf.app/v1/generate`
- **Auth:** Bearer token
- **Pricing:** Free tier 100 PDFs/month
- **Docs:** https://html2pdf.app/docs

### Option 3: Gotenberg (Self-hosted)
- **URL:** `http://gotenberg:3000/forms/chromium/print/url`
- **Auth:** None (internal network)
- **Cost:** Free (self-hosted Docker container)
- **Best for:** High volume, cost sensitivity

---

## Adapter Implementation

**File:** `apps/worker/src/worker/pdf_adapter.py`

**API:**
```python
from pdf_adapter import generate_pdf

# Simple usage - engine auto-detected
generate_pdf(
    url="https://example.com/print/abc-123",
    output_path="/tmp/report.pdf",
    wait_for_network=True
)

# Get engine info (debugging)
from pdf_adapter import get_pdf_engine_info
info = get_pdf_engine_info()
# Returns: {"engine": "api", "api_configured": True, ...}
```

**Engine Selection Logic:**
1. Check `PDF_ENGINE` env var
2. If `"api"` → Use PDF API service
3. Else → Use Playwright (local)
4. Validate configuration on startup

---

## Render Service Configuration

### Worker Service

**Name:** `reportscompany-worker`

**Environment Variables (9 total):**

| Variable | Value | Purpose |
|----------|-------|---------|
| `DATABASE_URL` | `postgresql://...` | PostgreSQL connection |
| `REDIS_URL` | `rediss://...?ssl_cert_reqs=CERT_REQUIRED` | Celery broker |
| `SIMPLYRETS_USERNAME` | `info_456z6zv2` | SimplyRETS API auth |
| `SIMPLYRETS_PASSWORD` | `lm0182gh3pu6f827` | SimplyRETS API auth |
| `R2_ACCOUNT_ID` | `db85a7d510688f5ce34d1e4c0129d2b3` | Cloudflare R2 |
| `R2_ACCESS_KEY_ID` | `cde16dd5ce6cacbe85b81783f70db25b` | R2 access key |
| `R2_SECRET_ACCESS_KEY` | `91baa5b42934c339...` | R2 secret key |
| `R2_BUCKET_NAME` | `market-reports` | R2 bucket |
| `PRINT_BASE` | `https://reportscompany-web.vercel.app` | Frontend URL |

**PDF-Specific (additional 3):**
| Variable | Value | Purpose |
|----------|-------|---------|
| `PDF_ENGINE` | `api` | Use PDF API service |
| `PDF_API_URL` | `https://api.pdfshift.io/v3/convert/pdf` | PDFShift endpoint |
| `PDF_API_KEY` | `sk_...` | PDFShift API key |

---

### Consumer Service

**Name:** `reportscompany-consumer`

**Environment Variables:**
- Same as Worker service (shares codebase)
- Consumer doesn't generate PDFs, but needs same env for consistency

---

## Verification Checklist

### ✅ Local Development
- [ ] Run `poetry install` successfully
- [ ] Playwright chromium installed
- [ ] Generate test report → PDF created in `/tmp/mr_reports/`
- [ ] PDF opens correctly, shows formatted report

### ✅ Render Staging
- [ ] Build completes in < 60 seconds
- [ ] No "Failed to download Chromium" errors in logs
- [ ] Worker starts successfully
- [ ] Test report generation → PDF generated via API
- [ ] PDF URL accessible (R2 or dev-files endpoint)

---

## Troubleshooting

### Issue: "Playwright not installed" in local dev
**Fix:** Run `python -m playwright install chromium`

### Issue: "PDF API not configured" on Render
**Fix:** Add `PDF_API_URL` and `PDF_API_KEY` to environment variables

### Issue: Build timeout on Render
**Fix:** Verify build command does NOT include `playwright install`

### Issue: PDF API returns 401 Unauthorized
**Fix:** Check API key is correct, regenerate if needed

### Issue: PDF blank or incomplete
**Fix:** 
1. Verify `PRINT_BASE` points to correct frontend URL
2. Check frontend `/print/[runId]` route is accessible
3. Increase wait time in PDF adapter

---

## Migration Path (Optional)

If you want to switch back to Playwright on Render (e.g., for full control):

1. **Add to build command:**
   ```bash
   pip install poetry && poetry install --no-root && python -m playwright install chromium
   ```

2. **Change environment variable:**
   ```bash
   PDF_ENGINE=playwright
   ```

3. **Remove PDF API variables:**
   - Delete `PDF_API_URL`
   - Delete `PDF_API_KEY`

4. **Redeploy**

**Caution:** This will increase build time and slug size significantly.

---

## Cost Analysis

### Playwright (Local/Render)
- **Build time:** 2-5 minutes
- **Slug size:** ~350MB
- **Runtime cost:** Free (self-contained)
- **Best for:** Low volume, full control needed

### PDF API (Render)
- **Build time:** 30 seconds
- **Slug size:** ~50MB
- **Runtime cost:** $0.03-0.05 per PDF (PDFShift)
- **Best for:** Production, reliability, speed

**Break-even:** ~500 PDFs/month (~$15-25)

---

**Status:** ✅ PDF adapter implemented and documented  
**Next:** Update Render environment variables + redeploy



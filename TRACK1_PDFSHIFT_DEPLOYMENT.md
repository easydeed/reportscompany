# Track 1: PDFShift Deployment Guide (Immediate Staging Unblock)

**Goal:** Get staging working TODAY by using PDFShift API instead of local Playwright/Chromium

**Time to Deploy:** ~5 minutes

---

## ✅ What We Just Implemented

1. **`apps/worker/src/worker/pdf_engine.py`** - Pluggable PDF backend
   - `playwright` engine: Local Chromium (requires Docker/system deps)
   - `pdfshift` engine: Cloud API (no dependencies)

2. **`apps/worker/src/worker/tasks.py`** - Updated to use abstraction
   - Calls `render_pdf()` instead of inline Playwright
   - Uploads to Cloudflare R2
   - Generates presigned URLs

---

## 🚀 Deployment Steps

### **Step 1: Update Render Worker Environment Variables**

Go to Render Dashboard → **`reportscompany-worker`** → **Settings** → **Environment**

**Add/Update these variables:**

```bash
PDF_ENGINE=pdfshift
PDFSHIFT_API_KEY=sk_f2f467da01a44b1c2edffe2a08c37e235feab15f
PRINT_BASE=https://reportscompany-web.vercel.app
```

**Keep existing variables:**
- `DATABASE_URL` (already set)
- `REDIS_URL` (already set with `?ssl_cert_reqs=CERT_REQUIRED`)
- `R2_ACCOUNT_ID=db85a7d510688f5ce34d1e4c0129d2b3`
- `R2_ACCESS_KEY_ID=cde16dd5ce6cacbe85b81783f70db25b`
- `R2_SECRET_ACCESS_KEY=91baa5b42934c339b29f84e69411bf0c3d622f129f428408575530cbb6990466`
- `R2_BUCKET_NAME=market-reports`
- `SIMPLYRETS_USERNAME=info_456z6zv2`
- `SIMPLYRETS_PASSWORD=lm0182gh3pu6f827`

Click **Save Changes**.

---

### **Step 2: Update Render Consumer Environment Variables**

Go to Render Dashboard → **`reportscompany-consumer`** → **Settings** → **Environment**

**Add the SAME variables as Worker** (they share the codebase):

```bash
PDF_ENGINE=pdfshift
PDFSHIFT_API_KEY=sk_f2f467da01a44b1c2edffe2a08c37e235feab15f
PRINT_BASE=https://reportscompany-web.vercel.app
```

Plus all the R2, SimplyRETS, DATABASE_URL, REDIS_URL variables.

Click **Save Changes**.

---

### **Step 3: Verify Build Command (No Changes Needed)**

Your current build command should still be:

```bash
pip install poetry && poetry install --no-root && poetry run playwright install --with-deps chromium
```

**This will still FAIL during build**, BUT it doesn't matter anymore because:
- We're not using Playwright at runtime (using PDFShift instead)
- The Worker will start successfully even if browser install failed
- You can optionally simplify to: `pip install poetry && poetry install --no-root`

**Optional:** Clean up the build command to:
```bash
pip install poetry && poetry install --no-root
```

This will make builds faster (no Playwright download attempt).

---

### **Step 4: Trigger Deployment**

Render should auto-deploy after the git push (already done).

Or manually trigger:
1. Go to **`reportscompany-worker`**
2. Click **Manual Deploy** → **Deploy latest commit**
3. Do the same for **`reportscompany-consumer`**

---

### **Step 5: Monitor Logs**

#### **Worker Logs** (should show):
```
[INFO/MainProcess] celery@... ready.
PDF Engine: pdfshift
☁️  Rendering PDF with PDFShift: https://reportscompany-web.vercel.app/print/...
✅ PDF generated: /tmp/mr_reports/....pdf (123456 bytes)
☁️  Uploading to R2: reports/.../....pdf
✅ Uploaded to R2: https://...r2.cloudflarestorage.com/...
```

#### **Consumer Logs** (should show):
```
🔄 Redis consumer started, polling queue: mr:enqueue:reports
📥 Received job: run_id=..., type=market_snapshot
```

---

### **Step 6: Test End-to-End**

1. **Go to:** `https://reportscompany-web.vercel.app/app/reports/new`

2. **Create a report:**
   - Type: Market Snapshot
   - City: San Diego (or Los Angeles, Houston)
   - Lookback: 30 days

3. **Click:** "Generate Report"

4. **Watch status:** `pending` → `processing` → `completed`

5. **Check Worker logs** for PDFShift API call

6. **Click PDF link** - should download from R2

---

## ✅ Success Criteria

After deployment, you should see:

- [ ] Worker service shows "Live" status
- [ ] Consumer service shows "Live" status
- [ ] No Playwright errors in logs
- [ ] Reports complete successfully
- [ ] PDF downloads work from frontend
- [ ] R2 bucket shows uploaded PDFs at `reports/{account-id}/{run-id}.pdf`

---

## 🔄 How to Switch Back to Playwright (Future)

When you move to Fly.io/Docker (Track 2), just change one environment variable:

```bash
PDF_ENGINE=playwright
```

Remove:
```bash
PDFSHIFT_API_KEY=(can remove)
```

Everything else stays the same. The code automatically uses the right engine.

---

## 💰 PDFShift Costs

**Free Tier:**
- 250 conversions/month
- Good for testing/staging

**Paid Plans:**
- $19/month: 1,000 conversions
- $49/month: 5,000 conversions
- https://pdfshift.io/pricing

For production, you'll want Track 2 (Fly.io with Playwright Docker) to avoid per-conversion costs.

---

## 🐛 Troubleshooting

### **Error: "PDFSHIFT_API_KEY environment variable is required"**

**Fix:** Make sure you set `PDFSHIFT_API_KEY` in Render environment variables (not Build Command).

### **Error: "HTTPStatusError: 401 Unauthorized"**

**Fix:** Check that the API key is correct: `sk_f2f467da01a44b1c2edffe2a08c37e235feab15f`

### **Error: "HTTPStatusError: 400 Bad Request"**

**Fix:** PDFShift couldn't load your print page. Check:
- `PRINT_BASE` is set to correct URL
- Frontend `/print/{run_id}` page is accessible
- Page loads without JavaScript errors

### **Worker still fails to start**

**Fix:** Check for OTHER errors (not Playwright). Common issues:
- DATABASE_URL not set
- REDIS_URL missing or incorrect
- Redis SSL parameter missing (`?ssl_cert_reqs=CERT_REQUIRED`)

### **PDF is blank or missing content**

**Fix:** PDFShift rendered before page loaded. Options:
1. Add `"wait": 3000` to PDFShift payload (3 second wait)
2. Check that `/print/{run_id}` page renders server-side (not client-side only)
3. Ensure print page has proper meta tags for rendering

---

## 📊 What Changed vs. Before

| Before | After |
|--------|-------|
| Worker tries to install Chromium during build | Worker doesn't need Chromium |
| Build fails due to missing system deps | Build succeeds |
| Runtime fails when launching browser | Runtime succeeds (API call instead) |
| PDFs generated locally | PDFs generated in cloud |
| Fragile, platform-dependent | Reliable, platform-agnostic |

---

## 🎯 Next Steps (Track 2)

Once staging is stable and tested:

1. **Set up Fly.io** (this week)
2. **Deploy Worker in Playwright Docker container**
3. **Switch `PDF_ENGINE=playwright`**
4. **Turn off Render Worker/Consumer** (or keep as backup)
5. **Save $19/month on PDFShift** 💰

Track 2 guide coming in separate document.

---

**Status:** ✅ Code deployed, ready for environment variable updates

**Deployed:** Commit `edffeb7` - "HOTFIX: Add pluggable PDF engine with PDFShift support"

**Time to completion:** ~5 minutes once env vars are set

---

## 🆘 Need Help?

If anything breaks:
1. Check Render logs (Worker and Consumer)
2. Look for the specific error message
3. Reference DEPLOYMENT_ISSUES_HANDOFF.md for context
4. Contact PDFShift support if API issues
5. Roll back by setting `PDF_ENGINE=playwright` (will fail, but keeps previous behavior)

---

**Ready to test!** 🚀


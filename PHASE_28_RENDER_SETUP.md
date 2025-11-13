# Phase 28: Render Production Credentials Setup

**Task 3: Manual Steps** - Add production SimplyRETS credentials to Render services

---

## 🎯 Objective

Switch from demo credentials (`simplyrets/simplyrets`) to production credentials (`info_456z6zv2/lm0182gh3pu6f827`) on all Render services to enable:
- Multi-city MLS data
- City search via `q` parameter
- Full API access

---

## 🔐 Production Credentials

```bash
SIMPLYRETS_USERNAME=info_456z6zv2
SIMPLYRETS_PASSWORD=lm0182gh3pu6f827
```

**Important:** These credentials enable production features in the code automatically via credential detection logic in `query_builders.py`.

---

## 📋 Services to Update

Update these environment variables on the following Render services:

### 1. **reportscompany - worker-service** (Celery Worker)
   
**Why:** This service generates reports and calls SimplyRETS API
   
**Steps:**
1. Go to: https://dashboard.render.com
2. Navigate to: **reportscompany - worker-service**
3. Click: **Environment** tab
4. Find or add:
   - `SIMPLYRETS_USERNAME` → Set to `info_456z6zv2`
   - `SIMPLYRETS_PASSWORD` → Set to `lm0182gh3pu6f827`
5. Click: **Save Changes**
6. Service will auto-redeploy (~30 seconds)

**Verification:**
- Check worker logs for: `[query_builders] Mode: PRODUCTION`
- Check worker logs for: `[query_builders] City search: ENABLED`

---

### 2. **reportscompany-api** (FastAPI)
   
**Why:** API may cache or validate credentials
   
**Steps:**
1. Navigate to: **reportscompany-api**
2. Click: **Environment** tab
3. Update:
   - `SIMPLYRETS_USERNAME` → `info_456z6zv2`
   - `SIMPLYRETS_PASSWORD` → `lm0182gh3pu6f827`
4. Click: **Save Changes**
5. Wait for redeploy

---

### 3. **markets-report-ticker** (Schedules Ticker)
   
**Why:** Ticker enqueues reports and may log credential mode
   
**Steps:**
1. Navigate to: **markets-report-ticker**
2. Click: **Environment** tab
3. Update:
   - `SIMPLYRETS_USERNAME` → `info_456z6zv2`
   - `SIMPLYRETS_PASSWORD` → `lm0182gh3pu6f827`
4. Click: **Save Changes**
5. Wait for redeploy

**Verification:**
- Check ticker logs for: `[query_builders] Mode: PRODUCTION`

---

## ✅ Post-Update Verification

After updating all services, verify the changes took effect:

### 1. Check Worker Logs
```
# Look for these lines in worker startup:
[query_builders] Mode: PRODUCTION
[query_builders] Username: info_456z6zv2
[query_builders] City search: ENABLED
[query_builders] Sorting: ENABLED
```

### 2. Test a Simple Report
```bash
# Run the multi-city test script
python insert_multi_city_tests.py

# Wait 60-90 seconds, then check results
python check_multi_city_test.py
```

### 3. Verify API Calls Work
- Check worker logs for successful SimplyRETS API responses
- Look for 200 status codes (not 401 Unauthorized)
- Verify `q=<cityname>` appears in logged API params

---

## 🔄 Rollback Instructions

If production credentials cause issues, revert to demo:

**For each service:**
1. Set `SIMPLYRETS_USERNAME` → `simplyrets`
2. Set `SIMPLYRETS_PASSWORD` → `simplyrets`
3. Save and wait for redeploy

The code will automatically detect demo mode and disable city search.

---

## 🐛 Troubleshooting

### Issue: "401 Unauthorized" in worker logs

**Cause:** Credentials not updated or incorrect

**Fix:**
1. Double-check username/password are correct (no extra spaces)
2. Verify service redeployed after env var change
3. Check logs for which credentials are being used

### Issue: "City search not working"

**Cause:** Still using demo credentials

**Fix:**
1. Verify `SIMPLYRETS_USERNAME=info_456z6zv2` (not `simplyrets`)
2. Check worker logs show `Mode: PRODUCTION`
3. Redeploy worker service if needed

### Issue: "No results for city X"

**Cause:** City may not have MLS coverage or wrong spelling

**Fix:**
1. Try major metros first (Austin, Dallas, Phoenix)
2. Use full city name (not abbreviations)
3. Check SimplyRETS API directly:
   ```bash
   curl -u "info_456z6zv2:lm0182gh3pu6f827" \
     "https://api.simplyrets.com/properties?q=Austin&limit=1"
   ```

---

## 📊 Expected Behavior

### Demo Mode (Before Update)
- ✅ Houston area works
- ✅ ZIP codes work
- ❌ City search blocked
- ❌ Multi-city blocked
- ⚠️ Limited data

### Production Mode (After Update)
- ✅ Houston area still works
- ✅ ZIP codes still work
- ✅ City search enabled (`q` parameter)
- ✅ Multi-city enabled
- ✅ Full MLS data access

---

## 🎯 Success Criteria

**Task 3 Complete When:**
1. ✅ All 3 Render services updated with production credentials
2. ✅ Worker logs show "Mode: PRODUCTION"
3. ✅ No 401 errors in API calls
4. ✅ City search queries include `q=<cityname>` parameter
5. ✅ Test reports generate successfully for non-Houston cities

---

**Status:** ⏳ Waiting for manual credential update on Render  
**Next:** After credentials are updated, run `insert_multi_city_tests.py` to certify multi-city functionality


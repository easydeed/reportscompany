# Phase 28: Production SimplyRETS - Master Plan

**Started:** November 14, 2025  
**Status:** 🔄 In Progress  
**Goal:** Enable multi-city real estate data using production SimplyRETS credentials

---

## 🎯 Objectives

1. ✅ **Switch from demo to production credentials** - Enable real MLS data access
2. ✅ **Enable multi-city search** - Users can select any US city with MLS coverage
3. ✅ **Fix query restrictions** - Use `q` (city search) and `sort` parameters
4. ✅ **Add rate limit handling** - Graceful fallback for API errors
5. ✅ **Test multiple markets** - Verify data quality across 5+ cities

---

## 📋 Current State (Phase 27 Complete)

**What's Working:**
- ✅ Scheduled reports auto-generate and send emails
- ✅ SendGrid integration with suppression filtering
- ✅ PDF generation with real data
- ✅ Schedules UI with CRUD operations
- ✅ Login/auth flow working on Vercel

**Current Limitation:**
- ❌ **Demo credentials only** - Limited to Houston area
- ❌ **No city search** - Can't use `q` parameter with demo API
- ❌ **No sorting** - Can't use `sort` parameter with demo API
- ❌ **Single market** - Can't generate reports for other cities

---

## 🔐 Credentials Available

**Demo (Current):**
```bash
SIMPLYRETS_USERNAME=simplyrets
SIMPLYRETS_PASSWORD=simplyrets
```
- Houston-only data
- No `q` or `sort` parameters allowed
- Good for development/testing

**Production:**
```bash
SIMPLYRETS_USERNAME=info_456z6zv2
SIMPLYRETS_PASSWORD=lm0182gh3pu6f827
```
- Multi-city MLS data
- Full API access (city search, sorting, filtering)
- Higher rate limits

---

## 🎯 Task Breakdown

### Task 1: Environment Strategy & Credential Setup ⏳

**Goal:** Add production credentials and create auto-detection logic

**Files to Modify:**
1. `apps/worker/src/worker/query_builders.py` - Detection logic
2. Render environment variables (manual)

**Implementation:**
```python
# Detection logic
import os

# Auto-detect based on username
SIMPLYRETS_USERNAME = os.getenv("SIMPLYRETS_USERNAME", "simplyrets")
IS_DEMO = SIMPLYRETS_USERNAME.lower() == "simplyrets"
IS_PRODUCTION = not IS_DEMO

# Feature flags based on mode
ALLOW_CITY_SEARCH = IS_PRODUCTION  # `q` parameter
ALLOW_SORTING = IS_PRODUCTION       # `sort` parameter
ALLOW_MULTI_CITY = IS_PRODUCTION    # Any US city
```

**Render Services to Update:**
- `reportscompany - worker-service` (Celery worker)
- `reportscompany-api` (FastAPI)

**Environment Variables to Add:**
```bash
# Production SimplyRETS Credentials
SIMPLYRETS_USERNAME=info_456z6zv2
SIMPLYRETS_PASSWORD=lm0182gh3pu6f827

# Optional: Explicit mode override
# SIMPLYRETS_MODE=production  # or 'demo'
```

**Testing:**
- [ ] Worker logs show "Production mode detected"
- [ ] City search queries work
- [ ] Sort parameters included in API calls

**Commit Message:**
```
feat(worker): Add production SimplyRETS support with auto-detection

- Add credential detection logic (demo vs production)
- Enable city search (`q` parameter) in production mode
- Enable sorting in production mode
- Add logging for mode detection
- Backwards compatible with demo credentials
```

---

### Task 2: Query Builder Updates ⏳

**Goal:** Enable city search and sorting in production mode

**Files to Modify:**
1. `apps/worker/src/worker/query_builders.py`

**Current Behavior (Demo Mode):**
```python
# Demo forbids city search
if city:
    return {}  # Can't use city

# Demo forbids sorting
return {}
```

**New Behavior (Production Mode):**
```python
# Production allows city search
if city:
    return {"q": city}  # Search by city name

# Production allows sorting
def _sort(val: str) -> Dict:
    if IS_PRODUCTION:
        return {"sort": val}
    return {}  # Demo still blocked
```

**Query Updates Needed:**
- Market Snapshot: Enable city search + `-listDate` sort
- New Listings: Enable city search + `-listDate` sort
- Closed: Enable city search + `-closeDate` sort
- Inventory: Enable city search + `daysOnMarket` sort
- Open Houses: Enable city search + `-listDate` sort
- Price Bands: Enable city search + `listPrice` sort

**Testing:**
- [ ] Demo credentials still work (no `q`, no `sort`)
- [ ] Production credentials enable city search
- [ ] Production credentials enable sorting
- [ ] Query logs show correct parameters

**Commit Message:**
```
feat(worker): Enable city search and sorting in production mode

- Update _location() to use `q` parameter when IS_PRODUCTION
- Update _sort() to include sort parameter when IS_PRODUCTION
- Maintain demo mode restrictions for backwards compatibility
- Add query parameter logging for debugging
```

---

### Task 3: Multi-City Testing & Validation ⏳

**Goal:** Test 5+ US cities to verify data quality

**Test Cities:**
1. **Houston, TX** (baseline - demo data)
2. **Austin, TX** (production)
3. **Dallas, TX** (production)
4. **Phoenix, AZ** (production)
5. **Miami, FL** (production)
6. **Seattle, WA** (production)

**Test Process (Per City):**
```sql
-- Insert test schedule directly
INSERT INTO schedules (
    account_id, name, report_type, city, lookback_days,
    cadence, weekly_dow, send_hour, send_minute,
    recipients, active, created_at, next_run_at
) VALUES (
    '912014c3-6deb-4b40-a28d-489ef3923a3a',
    'Phase 28 Test - {CITY_NAME}',
    'market_snapshot',
    '{CITY_NAME}',  -- e.g., 'Austin'
    30,
    'weekly',
    1,  -- Monday
    14, 0,
    ARRAY['gerardoh@gmail.com'],
    true,
    NOW(),
    NOW() - INTERVAL '1 minute'  -- Fire immediately
) RETURNING id, name, next_run_at;
```

**Monitoring Script:**
```python
# check_multi_city_test.py
import psycopg2
import os

DB_URL = os.getenv("DATABASE_URL")
conn = psycopg2.connect(DB_URL)
cur = conn.cursor()

# Check recent reports by city
cur.execute("""
    SELECT 
        rg.id,
        rg.status,
        rg.input_params->>'city' as city,
        rg.result_json->>'active_count' as active,
        rg.result_json->>'closed_count' as closed,
        rg.pdf_url,
        rg.created_at
    FROM report_generations rg
    WHERE rg.created_at > NOW() - INTERVAL '1 hour'
    ORDER BY rg.created_at DESC
    LIMIT 10;
""")

print("\n=== Recent Multi-City Reports ===\n")
for row in cur.fetchall():
    print(f"City: {row[2]}")
    print(f"  Status: {row[1]}")
    print(f"  Active: {row[3]}, Closed: {row[4]}")
    print(f"  PDF: {row[5]}")
    print(f"  Time: {row[6]}\n")

conn.close()
```

**Success Criteria (Per City):**
- [ ] `report_generations.status = 'completed'`
- [ ] `result_json` contains non-zero counts
- [ ] PDF URL is valid and accessible
- [ ] Data looks reasonable (no 10,000 active listings in small town)
- [ ] Query used correct city parameter

**Commit Message:**
```
test(worker): Add multi-city testing script and validation

- Add check_multi_city_test.py monitoring script
- Document test cities and success criteria
- Provide SQL for quick test schedule insertion
```

---

### Task 4: Rate Limit Handling & Error Recovery ⏳

**Goal:** Add resilience for API failures and rate limits

**Files to Modify:**
1. `apps/worker/src/worker/tasks.py`
2. `apps/worker/src/worker/simplyrets_client.py` (or wherever API calls are made)

**Rate Limit Strategy:**
```python
import time
from requests.exceptions import HTTPError

def fetch_with_retry(url: str, params: dict, max_retries: int = 3):
    """Fetch with exponential backoff for rate limits"""
    for attempt in range(max_retries):
        try:
            response = requests.get(url, params=params, auth=auth)
            response.raise_for_status()
            return response.json()
        
        except HTTPError as e:
            if e.response.status_code == 429:  # Rate limit
                wait_time = 2 ** attempt  # 1s, 2s, 4s
                logger.warning(f"Rate limit hit, retry {attempt+1}/{max_retries} after {wait_time}s")
                time.sleep(wait_time)
                continue
            else:
                raise  # Other HTTP errors
    
    raise Exception(f"Failed after {max_retries} retries")
```

**Error Logging:**
```python
# Log all SimplyRETS API calls
logger.info(f"SimplyRETS API call", extra={
    "endpoint": url,
    "params": params,
    "mode": "production" if IS_PRODUCTION else "demo",
    "status_code": response.status_code,
    "response_time_ms": elapsed_ms
})
```

**Graceful Fallback:**
- If city search fails → Try ZIP code if available
- If no results → Return empty report with clear message
- If rate limit exhausted → Mark run as `failed_api` (not `failed`)

**Testing:**
- [ ] Inject 429 error → verify retry logic works
- [ ] Inject 500 error → verify error logged, task fails gracefully
- [ ] Rate limit logs visible in worker logs

**Commit Message:**
```
feat(worker): Add rate limit handling and retry logic for SimplyRETS API

- Add exponential backoff for 429 rate limit errors
- Add detailed API call logging (params, timing, status)
- Add graceful fallback for failed city searches
- Distinguish API failures from report generation failures
```

---

### Task 5: UI Enhancement (Optional Polish) ⏳

**Goal:** Add city selection guidance in UI

**Files to Modify:**
1. `apps/web/components/v0/schedule-wizard.tsx`
2. `apps/web/components/v0/new-report-wizard.tsx`

**Enhancement Ideas:**
```tsx
// City input with helper text
<div>
  <Label>City</Label>
  <Input 
    placeholder="e.g., Austin, Houston, Miami"
    value={city}
    onChange={(e) => setCity(e.target.value)}
  />
  <p className="text-sm text-muted-foreground mt-1">
    {isProduction 
      ? "Enter any US city with MLS coverage" 
      : "Demo mode: Houston area only"}
  </p>
</div>
```

**Testing:**
- [ ] Helper text shows correct mode
- [ ] City input accepts free-form text
- [ ] Validation prevents empty city in production

**Commit Message:**
```
feat(web): Add city selection guidance for production vs demo mode

- Add helper text to city input fields
- Display mode-specific instructions
- Improve UX for multi-city selection
```

---

## 🧪 Testing Checklist

### Pre-Deployment Checks
- [ ] Code changes committed and pushed
- [ ] Render services redeployed with new env vars
- [ ] Worker logs show "Production mode detected"
- [ ] No build errors

### Post-Deployment Tests
- [ ] **Test 1: Demo mode still works** (Houston with demo credentials)
- [ ] **Test 2: Production mode works** (Austin with prod credentials)
- [ ] **Test 3: Multi-city** (5 different cities, all succeed)
- [ ] **Test 4: Rate limit handling** (Monitor logs for retry behavior)
- [ ] **Test 5: UI guidance** (Helper text shows correct mode)

### Data Quality Checks
- [ ] Active listings count reasonable (10-5000 per city)
- [ ] Closed transactions exist (not zero)
- [ ] Median prices align with city expectations
- [ ] Days on market reasonable (0-365)
- [ ] PDF renders correctly with city name

---

## 📊 Success Metrics

**Phase 28 Complete When:**
1. ✅ Production credentials added to all Render services
2. ✅ Query builders enable city search + sorting in production
3. ✅ 5+ cities tested successfully
4. ✅ Rate limit handling implemented and tested
5. ✅ No regression in demo mode (Houston still works)
6. ✅ Documentation complete for debugging

**Deliverables:**
- Updated `query_builders.py` with mode detection
- Multi-city test script (`check_multi_city_test.py`)
- Updated environment variables on Render
- This master plan document (progress tracked)

---

## 🐛 Debugging Guide

### Issue: "No results for city X"

**Check:**
1. Is city name spelled correctly? (Austin vs Austin, TX)
2. Does SimplyRETS have coverage for that city?
3. Are there actually listings in that market?
4. Check worker logs for API response

**Fix:**
```bash
# Check SimplyRETS API directly
curl -u "info_456z6zv2:lm0182gh3pu6f827" \
  "https://api.simplyrets.com/properties?q=Austin&limit=1"
```

### Issue: "Rate limit errors"

**Check:**
1. How many API calls in last hour?
2. Are we retrying correctly?
3. Is backoff logic working?

**Fix:**
- Increase retry delay
- Add caching for repeated queries
- Consider upgrading SimplyRETS plan

### Issue: "Query parameter ignored"

**Check:**
1. Is `IS_PRODUCTION` set correctly?
2. Are credentials definitely production (not demo)?
3. Check worker logs for mode detection

**Fix:**
```python
# Force production mode for testing
IS_PRODUCTION = True  # Override detection
```

---

## 🚀 Next Phase Preview

Once Phase 28 is complete, **Phase 29: Plan Limits & Monetization** will:
- Add `monthly_report_limit` to accounts
- Track usage against limits
- Add UI messaging for approaching limits
- Wire up Stripe webhooks for upgrades

---

**Status:** 🔄 Ready to execute  
**Estimated Duration:** 2-4 hours  
**Risk Level:** 🟢 Low (backwards compatible with demo)


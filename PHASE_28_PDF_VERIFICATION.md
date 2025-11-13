# Phase 28: PDF Content Verification Checklist

**Date:** November 14, 2025  
**Status:** Awaiting user verification of California city PDFs

---

## 📋 Quick Verification Checklist

For each of the 5 California city emails, check the PDF:

### 1. **City Name Display**
- [ ] Shows correct city name (Southgate, La Verne, San Dimas, Downey, or Orange)
- [ ] Not showing "Houston" or wrong city
- [ ] Not showing "report ID unknown"

### 2. **Active Listings Count**
- [ ] Shows a number > 0
- [ ] Number looks realistic (typically 10-500 for these cities)
- [ ] Not showing "0" or "null"

### 3. **Closed Transactions**
- [ ] Shows closed sales count > 0
- [ ] Last 30 days data
- [ ] Looks realistic

### 4. **Median Price**
- [ ] Shows dollar amount
- [ ] Looks realistic for California (typically $400K-$900K for these areas)
- [ ] Not showing "$0" or "unknown"

### 5. **Days on Market**
- [ ] Shows a number
- [ ] Typically 10-60 days for California
- [ ] Not showing "0" or "null"

---

## 🔍 What to Look For

### ✅ **GOOD Signs (Real Data Working):**
- City name matches email subject
- Active count is 10-500
- Median price is $400K-$900K
- Days on market is 10-60
- PDF opens without errors
- Data looks consistent with California real estate

### ❌ **BAD Signs (Needs Debugging):**
- Shows "report ID unknown"
- Shows Houston data instead of requested city
- All counts are 0
- Median price is $0 or very low
- PDF fails to load
- Missing city name

---

## 🐛 Common Issues & Quick Fixes

### Issue: "Report ID unknown" in PDF
**Cause:** Print page can't fetch report data from API  
**Fix:** Check `NEXT_PUBLIC_API_BASE` on Vercel (already fixed in Phase 27)  
**Status:** Should be working now

### Issue: Shows Houston data for all cities
**Cause:** Demo mode still active OR city parameter not passed  
**Fix:** Verify worker logs show "Mode: PRODUCTION"  
**Check:** `apps/worker/src/worker/query_builders.py` deployed

### Issue: All counts are 0
**Cause:** No MLS data for that city OR date range issue  
**Fix:** Try different city or check SimplyRETS API directly  
**Note:** California cities provided should all have data

### Issue: PDF won't open
**Cause:** R2 upload failed OR PDF generation error  
**Fix:** Check worker logs for PDF generation errors  
**Check:** `report_generations` table for status

---

## 📊 Expected Data Ranges (California Cities)

### Southgate, CA (LA area)
- **Population:** ~95,000
- **Expected Active:** 50-200
- **Expected Median:** $500K-$700K
- **Expected DOM:** 20-40 days

### La Verne, CA (San Gabriel Valley)
- **Population:** ~32,000
- **Expected Active:** 20-80
- **Expected Median:** $600K-$850K
- **Expected DOM:** 25-45 days

### San Dimas, CA (Los Angeles County)
- **Population:** ~34,000
- **Expected Active:** 25-100
- **Expected Median:** $650K-$900K
- **Expected DOM:** 20-40 days

### Downey, CA (LA County)
- **Population:** ~113,000
- **Expected Active:** 80-250
- **Expected Median:** $550K-$750K
- **Expected DOM:** 25-45 days

### Orange, CA (Orange County)
- **Population:** ~139,000
- **Expected Active:** 100-300
- **Expected Median:** $700K-$950K
- **Expected DOM:** 20-40 days

---

## 🛠️ Debugging Commands (If Needed)

### Check Recent Reports in Database
```bash
python check_multi_city_test.py
```

### Check Specific Report Data
```python
# check_report_data.py
import psycopg2, os, json
DB_URL = os.getenv("DATABASE_URL")
conn = psycopg2.connect(DB_URL)
cur = conn.cursor()

# Get most recent reports
cur.execute("""
    SELECT 
        id, 
        status,
        input_params->>'city' as city,
        result_json->>'active_count' as active,
        result_json->>'median_price' as median,
        pdf_url
    FROM report_generations
    WHERE created_at > NOW() - INTERVAL '10 minutes'
    ORDER BY created_at DESC
    LIMIT 5;
""")

for row in cur.fetchall():
    print(f"\nCity: {row[2]}")
    print(f"  Status: {row[1]}")
    print(f"  Active: {row[3]}")
    print(f"  Median: {row[4]}")
    print(f"  PDF: {row[5][:80]}...")
```

### Check Worker Logs for Errors
```bash
# Via Render MCP tools or dashboard
# Look for:
# - SimplyRETS API errors
# - PDF generation errors
# - Data extraction errors
```

---

## 📝 Report Back Template

Please report back with this format:

```
CITY: Southgate, CA
- City name in PDF: [correct/wrong/missing]
- Active count: [number or issue]
- Closed count: [number or issue]
- Median price: [price or issue]
- Days on market: [number or issue]
- Overall: [✅ looks good / ❌ issue detected]

CITY: La Verne, CA
...

OVERALL VERDICT:
- [All PDFs show real data ✅]
- [Some PDFs have issues ⚠️]
- [All PDFs broken ❌]
```

---

## 🎯 Success Criteria

**Phase 28 is 100% COMPLETE when:**
- [ ] All 5 PDFs open successfully
- [ ] Each PDF shows correct city name
- [ ] Active counts are > 0 and realistic
- [ ] Median prices are in expected California ranges
- [ ] No "report ID unknown" errors
- [ ] Data matches expected city demographics

---

**Status:** ⏳ Awaiting user PDF verification  
**Next:** Based on user feedback, either celebrate Phase 28 completion or debug specific issues


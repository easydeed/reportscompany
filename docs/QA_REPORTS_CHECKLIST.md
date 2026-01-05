# QA Reports & Emails Checklist

> **Last Updated:** December 17, 2025  
> **Coverage:** Southern California (CRMLS)

---

## Quick Start

### Option 1: Automated Script (Recommended)
```bash
# Set your credentials
export QA_API_KEY="your-api-key"
export QA_ACCOUNT_ID="your-account-id"

# Run all variations
python scripts/qa_generate_all_reports.py --env staging

# Quick mode (essential only)
python scripts/qa_generate_all_reports.py --quick

# Specific cities
python scripts/qa_generate_all_reports.py --cities "Irvine,La Verne"
```

### Option 2: Manual Testing
Use the web UI at:
- **Staging:** https://staging.trendyreports.io
- **Production:** https://www.trendyreports.io

---

## Report Types to Test

### 1. New Listings Gallery
Visual gallery of new listings with hero photos.

| Audience        | Expected Behavior                              | Status |
|-----------------|------------------------------------------------|--------|
| All Buyers      | All new listings in area                       | ☐      |
| First-Time      | Listings ≤70% of median price                  | ☐      |
| Luxury          | Listings ≥175% of median price                 | ☐      |
| Investor        | Listings ≤85% of median (investment potential) | ☐      |
| Condo           | Condos/townhouses only                         | ☐      |
| Family          | 3+ beds, ≤110% median price                    | ☐      |

**Check:**
- [ ] Header shows correct report name (e.g., "First-Time Buyer Homes")
- [ ] Photos load correctly in PDF
- [ ] Property cards show: photo, price, beds/baths/sqft, address
- [ ] Footer shows branding
- [ ] Multi-page: no border stretching on partial pages

### 2. Market Update (Snapshot)
Statistical overview with key metrics.

| Test Case       | Expected Metrics                               | Status |
|-----------------|------------------------------------------------|--------|
| Irvine 30 days  | Active, New, Pending, Closed counts + prices   | ☐      |
| LA 30 days      | Should show higher volume                      | ☐      |
| Small city      | May show fewer results                         | ☐      |

**Check:**
- [ ] Header shows "Market Snapshot" or area name
- [ ] Metrics display: Active Listings, New Listings, Pending, Closed
- [ ] Median prices show correctly formatted ($X,XXX,XXX)
- [ ] Days on Market average is reasonable
- [ ] Months of Inventory calculation is correct
- [ ] No template tags visible ({{#if}}, etc.)

### 3. Closed Sales
Table of recently closed/sold properties.

| Test Case       | Expected Behavior                              | Status |
|-----------------|------------------------------------------------|--------|
| Irvine 30 days  | Shows closed sales with close price/date       | ☐      |
| 60 days         | Should show more results                       | ☐      |
| 90 days         | Even more results                              | ☐      |

**Check:**
- [ ] Header shows "Closed Sales" or similar
- [ ] Table shows: Address, Close Price, Close Date, DOM
- [ ] Close prices are realistic (not $0 or $1)
- [ ] Close dates are within lookback period
- [ ] Footer shows branding

---

## Test Cities (CRMLS Coverage)

| City           | Market Type    | Expected Volume | Notes              |
|----------------|----------------|-----------------|--------------------|
| Irvine         | High-end       | High            | Good for luxury    |
| Los Angeles    | Mixed          | Very High       | Diverse pricing    |
| La Verne       | Suburban       | Medium          | Good for family    |
| San Diego      | Coastal        | High            | Beach properties   |
| Palm Springs   | Resort         | Medium          | Seasonal market    |
| Riverside      | Inland Empire  | High            | Affordable market  |

---

## Visual Checks (All Reports)

### Header
- [ ] Logo appears correctly
- [ ] Report title matches type and audience
- [ ] Date/timeframe is accurate
- [ ] No raw template tags ({{variable}})

### Body
- [ ] Data is populated (not empty)
- [ ] Numbers are formatted (commas, currency)
- [ ] Photos load (no broken images)
- [ ] Layout is consistent across pages

### Footer
- [ ] Branding appears
- [ ] Contact info is correct
- [ ] No template artifacts

### PDF Specific
- [ ] Images render (not blank boxes)
- [ ] Text is readable (not cut off)
- [ ] Multi-page pagination works
- [ ] File downloads correctly

---

## Email Checks

### Email Structure
- [ ] Subject line is relevant
- [ ] Preheader text makes sense
- [ ] Hero section shows key highlight
- [ ] CTA buttons work
- [ ] Unsubscribe link works

### Email Content
- [ ] Property previews are accurate
- [ ] Links to full report work
- [ ] Responsive on mobile
- [ ] Images have alt text

---

## Known Issues / Edge Cases

| Issue                    | Workaround                        | Status |
|--------------------------|-----------------------------------|--------|
| 0 results for niche      | Market-adaptive pricing widens    | Fixed  |
| Photos don't load in PDF | Photo proxy to R2 (disabled)      | WIP    |
| City typos               | Autocomplete added                | Fixed  |
| Template tags in PDF     | Enhanced injectBrand cleanup      | Fixed  |

---

## Test Matrix

Run date: ____________

| Report Type    | Audience     | City      | HTML | PDF | Email | Notes |
|----------------|--------------|-----------|------|-----|-------|-------|
| New Listings   | All          | Irvine    | ☐    | ☐   | ☐     |       |
| New Listings   | First-Time   | Irvine    | ☐    | ☐   | ☐     |       |
| New Listings   | Luxury       | Irvine    | ☐    | ☐   | ☐     |       |
| New Listings   | Investor     | Irvine    | ☐    | ☐   | ☐     |       |
| New Listings   | Condo        | Irvine    | ☐    | ☐   | ☐     |       |
| New Listings   | Family       | Irvine    | ☐    | ☐   | ☐     |       |
| Market Update  | N/A          | Irvine    | ☐    | ☐   | ☐     |       |
| Closed Sales   | N/A          | Irvine    | ☐    | ☐   | ☐     |       |
| New Listings   | All          | LA        | ☐    | ☐   | ☐     |       |
| Market Update  | N/A          | LA        | ☐    | ☐   | ☐     |       |
| Closed Sales   | N/A          | LA        | ☐    | ☐   | ☐     |       |

---

## Automated Results Location

After running the script:
```
qa_results.json        # Full results with URLs
```

Sample output:
```json
{
  "generated_at": "2025-12-17T10:30:00",
  "total_reports": 24,
  "completed": 22,
  "failed": 2,
  "results": [
    {
      "report_type": "new_listings",
      "audience": "First-Time Buyer",
      "city": "Irvine",
      "status": "completed",
      "pdf_url": "https://...",
      "html_url": "https://..."
    }
  ]
}
```

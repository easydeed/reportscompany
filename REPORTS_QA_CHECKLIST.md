# REPORTS SYSTEM - QA CHECKLIST

**Purpose**: Manual test scenarios to verify report generation and delivery  
**Based on**: `REPORTS_MATRIX.md` findings  
**Date**: Nov 24, 2025

---

## Test Environment Setup

**Prerequisites**:
- Access to staging database
- Access to Render logs (worker)
- Test accounts:
  - 1x REGULAR agent (free or solo plan)
  - 1x INDUSTRY_AFFILIATE with sponsored agents
- Test area: La Verne, CA (or known good city/ZIP)
- Email test account to receive reports

---

## TEST 1: Market Snapshot (Agent, Email + PDF)

### Goal
Verify the most mature report type works end-to-end for a regular agent.

### Steps
1. **Create One-Off Report** (UI):
   - Log in as REGULAR agent
   - Navigate to `/app/reports` or wizard
   - Select Report Type: **Market Snapshot**
   - Area: **La Verne** (or test city)
   - Lookback: **30 days**
   - Generate

2. **Verify Report Generation** (DB):
   ```sql
   SELECT id::text, status, report_type, created_at
   FROM report_generations
   WHERE account_id = '<agent_account_id>'
   ORDER BY created_at DESC LIMIT 1;
   ```
   - ✅ `status = 'completed'` (or 'processing' if still running)
   - ✅ `report_type = 'market_snapshot'`

3. **Verify PDF Created**:
   ```sql
   SELECT pdf_url FROM report_generations WHERE id = '<report_id>';
   ```
   - ✅ `pdf_url` is not null
   - ✅ URL is accessible (R2/S3 link)

4. **Open PDF in Browser**:
   - Navigate to `pdf_url`
   - ✅ PDF downloads/displays
   - ✅ Contains metrics (Active, Pending, Closed, DOM, Prices)
   - ✅ Shows correct area (La Verne)
   - ✅ Branding: Agent name/logo (if set)
   - ✅ No render errors, blank pages, or cutoff text

5. **Verify Email HTML** (if sent manually or via schedule):
   - Check email inbox
   - ✅ Subject: "Your Market Snapshot Report"
   - ✅ Body: Branded header, metrics table, PDF download button
   - ✅ Unsubscribe link present
   - ✅ Renders correctly on desktop + mobile

### Expected Result
✅ **PASS**: Report generates, PDF renders cleanly, email (if sent) is branded and readable

---

## TEST 2: New Listings Gallery (Email + PDF with Images)

### Goal
Verify gallery report includes hero photos in both email and PDF.

### Steps
1. **Create Report**:
   - Report Type: **New Listings Gallery**
   - Area: **La Verne**
   - Lookback: **7 days** (to get recent listings with photos)

2. **Verify PDF**:
   - Open PDF from `pdf_url`
   - ✅ Shows property cards with **hero images**
   - ✅ Images load (not broken placeholders)
   - ✅ Layout: Gallery grid (not plain list)
   - ✅ Each card shows: Photo, Address, Price, Beds/Baths

3. **Verify Email** (via schedule or manual send):
   - ✅ Email body includes property images inline
   - ✅ Each listing has a hero photo (from SimplyRETS `photos[0]`)
   - ✅ Images render in email clients (not blocked)

### Expected Result
✅ **PASS**: Gallery layout works, hero photos display in PDF and email

### Common Failures
- ❌ No photos → SimplyRETS returned listings without `photos` array
- ❌ Broken images → Photo URLs invalid or CORS blocked
- ❌ Layout broken → CSS not applied to gallery grid

---

## TEST 3: Affiliate Branding (White-Label Email + PDF)

### Goal
Verify affiliate-sponsored agent receives reports with **affiliate branding**, not default.

### Setup
- AFFILIATE account has branding set:
  - Logo URL
  - Primary color
  - Contact info (name, phone, website)
- SPONSORED agent under this affiliate

### Steps
1. **Create Schedule as Affiliate**:
   - Log in as AFFILIATE
   - Create schedule:
     - Report Type: **Market Snapshot**
     - Area: **La Verne**
     - Recipients: **Select sponsored agent**
   - Trigger execution (manual or wait)

2. **Verify Email Received by Sponsored Agent**:
   - Check sponsored agent's email inbox
   - ✅ **Header logo**: Shows affiliate logo (not default Trendy logo)
   - ✅ **Colors**: Uses affiliate primary color
   - ✅ **Contact info**: Shows affiliate name, phone, website
   - ✅ **Footer**: "Powered by [Affiliate Name]" (not generic)

3. **Verify PDF**:
   - Open PDF from email link
   - ✅ PDF header shows affiliate logo
   - ✅ Colors match affiliate branding
   - ✅ Footer shows affiliate contact info

### Expected Result
✅ **PASS**: White-label branding applied to both email and PDF

---

## TEST 4: Partial Reports (Inventory, Closed, Price Bands)

### Goal
Verify partial reports generate without errors (even if less polished).

### Steps
1. **Test Each Partial Report**:
   - Create reports for:
     - **Inventory**
     - **Closed Sales**
     - **Price Bands**
   - Area: **La Verne**, Lookback: **30 days**

2. **For Each Report, Verify**:
   - ✅ Report generates (`status = 'completed'`)
   - ✅ PDF created and viewable
   - ✅ Email sends (if scheduled)
   - ✅ No 500 errors in worker logs
   - ✅ Metrics display (even if generic)

3. **Note Quality Issues** (Expected):
   - ⚠️ Less polished layout than market_snapshot
   - ⚠️ Generic metrics display (no custom formatting)
   - ⚠️ Minimal branding (may not use affiliate colors fully)

### Expected Result
⚠️ **PASS (with known limitations)**: Reports generate successfully, but quality is "PARTIAL" per matrix

---

## TEST 5: Scheduled Report (Agent, Weekly)

### Goal
Verify schedule system triggers report generation and email delivery.

### Steps
1. **Create Schedule**:
   - Log in as REGULAR agent
   - Navigate to `/app/schedules`
   - Create schedule:
     - Report Type: **Market Snapshot**
     - Area: **La Verne**
     - Cadence: **Weekly**, Monday, 9 AM (adjust to test time)
     - Recipients: **Agent's own email**

2. **Manually Trigger** (for quick test):
   ```sql
   UPDATE schedules SET next_run_at = NOW() - INTERVAL '1 minute'
   WHERE id = '<schedule_id>';
   ```
   - Wait for ticker (up to 60 seconds)

3. **Verify Execution**:
   ```sql
   SELECT status FROM schedule_runs WHERE schedule_id = '<schedule_id>' ORDER BY created_at DESC LIMIT 1;
   ```
   - ✅ `status = 'completed'`

4. **Verify Email Sent**:
   ```sql
   SELECT to_emails, response_code FROM email_log WHERE schedule_id = '<schedule_id>' ORDER BY created_at DESC LIMIT 1;
   ```
   - ✅ `to_emails` contains agent email
   - ✅ `response_code = 202` (SendGrid accepted)

5. **Check Email Inbox**:
   - ✅ Email received
   - ✅ PDF link works
   - ✅ Unsubscribe link present

### Expected Result
✅ **PASS**: Scheduled report triggers, generates, sends email with PDF link

---

## TEST 6: Scheduled Report (Affiliate → Group)

### Goal
Verify affiliate can schedule reports to a group containing contacts + sponsored agents.

### Setup
- AFFILIATE has a group with:
  - 2+ contacts
  - 1+ sponsored agent
- Group named: "Test Office Group"

### Steps
1. **Create Schedule as Affiliate**:
   - Report Type: **New Listings**
   - Area: **La Verne**
   - Cadence: **Weekly**
   - Recipients: **Select group** "Test Office Group"

2. **Trigger Execution** (manual):
   ```sql
   UPDATE schedules SET next_run_at = NOW() - INTERVAL '1 minute'
   WHERE id = '<schedule_id>';
   ```

3. **Verify Email Sent to All Group Members**:
   ```sql
   SELECT to_emails FROM email_log WHERE schedule_id = '<schedule_id>' ORDER BY created_at DESC LIMIT 1;
   ```
   - ✅ `to_emails` array contains all group member emails (contacts + sponsored agent)
   - ✅ No duplicates (if member in multiple groups)

4. **Verify White-Label Branding** (per TEST 3):
   - ✅ All recipients see affiliate branding

### Expected Result
✅ **PASS**: Group recipients resolved correctly, all receive branded email

---

## TEST 7: Edge Case - Empty Results

### Goal
Verify reports handle empty data gracefully (e.g., no listings in area).

### Steps
1. **Create Report with Unlikely Area**:
   - Report Type: **New Listings**
   - Area: **Antarctica** or nonsense city
   - Lookback: **7 days**

2. **Verify Report Generation**:
   - ✅ Report completes (not `status = 'failed'`)
   - ✅ PDF generated

3. **Check PDF Content**:
   - ✅ Shows "No listings found" or similar message
   - ✅ Does not show "0" for all metrics confusingly
   - ✅ No broken layout or empty pages

### Expected Result
✅ **PASS**: Empty data handled gracefully with clear messaging

---

## TEST 8: Edge Case - Extreme Data (Long Lists)

### Goal
Verify reports with many listings (100+) don't break PDF layout.

### Steps
1. **Create Report with High-Volume Area**:
   - Report Type: **Inventory**
   - Area: **Los Angeles** (or major metro)
   - Lookback: **90 days**

2. **Verify PDF**:
   - ✅ PDF generates (may take longer)
   - ✅ All listings render (not truncated)
   - ✅ Page breaks handled (tables don't split mid-row awkwardly)
   - ✅ File size reasonable (< 10MB)

### Expected Result
✅ **PASS**: Large datasets render correctly without layout breaks

---

## TEST 9: Currency & Number Formatting

### Goal
Verify prices and numbers are formatted consistently.

### Steps
1. **Create Market Snapshot**:
   - Area: **La Verne**
   - Lookback: **30 days**

2. **Check Formatting in Email + PDF**:
   - ✅ Prices: **$1,234,567** (commas, dollar sign)
   - ✅ Days on Market: **45 days** (integer, no decimals)
   - ✅ Percentages: **95.5%** (one decimal place)
   - ✅ No raw numbers like `1234567` or `0.955`

### Expected Result
✅ **PASS**: All numbers formatted consistently per US conventions

---

## TEST 10: Links & CTAs in Email

### Goal
Verify all links in email reports work and point to correct URLs.

### Steps
1. **Generate and Send Market Snapshot Email** (via schedule or manual)

2. **Click Each Link in Email**:
   - ✅ **"View PDF"** button → Opens PDF correctly (not 404)
   - ✅ **Unsubscribe link** → Goes to `/v1/unsubscribe?token=...` (returns success)
   - ✅ **Logo link** (if branded) → Opens affiliate/agent website (if set)
   - ✅ No broken links (404 errors)

3. **Verify Link Tracking** (if implemented):
   - ⚠️ Currently not implemented (no click tracking)

### Expected Result
✅ **PASS**: All links functional, no 404s

---

## Summary: QA Completion Criteria

Mark each test ✅ **PASS**, ⚠️ **PASS (with known issues)**, or ❌ **FAIL**.

| Test | Status | Notes |
|------|--------|-------|
| 1. Market Snapshot (Agent) | | |
| 2. New Listings Gallery | | |
| 3. Affiliate Branding | | |
| 4. Partial Reports (Inventory/Closed/Price Bands) | | **Expected: PASS with limitations** |
| 5. Scheduled Report (Agent) | | |
| 6. Scheduled Report (Affiliate → Group) | | |
| 7. Edge Case - Empty Results | | |
| 8. Edge Case - Extreme Data | | |
| 9. Currency/Number Formatting | | |
| 10. Links & CTAs | | |

---

## Post-QA Actions

**If Tests 1-3, 5-6, 9-10 PASS**:
- ✅ Core report system functional
- ✅ Market Snapshot + Gallery reports production-ready
- ⚠️ Partial reports (Test 4) acceptable as-is or queue for polish

**If any of Tests 1-3, 5-6 FAIL**:
- ❌ Critical functionality broken
- ❌ Fix before considering reports "stable"

**Known Gaps to Address** (from REPORTS_MATRIX.md):
1. Polish partial reports (inventory, closed, price_bands)
2. Add email charts/visualizations
3. Implement image exports (JPG/PNG) if needed
4. Add preview-before-send UI

---

**End of QA Checklist**

Use this checklist to verify report system behavior after any report template or pipeline changes.


# REPORTS VISUAL QA PLAN - Execution Guide

**Purpose**: Systematic visual inspection of all 8 report types × 2 personas × 3 surfaces  
**Timeline**: 2-3 hours for full execution  
**Outcome**: "Sellable or not" verdict + `REPORTS_VISUAL_ISSUES.md` with blockers

---

## ⚠️ CRITICAL FINDING

**During initial browser testing, I discovered**:
- The wizard at `/app/reports/new` only shows **4 report types** (Market Snapshot, New Listings, Closed Sales, Inventory)
- Missing: price_bands, open_houses, new_listings_gallery, featured_listings
- **This means R1 changes to `apps/web/components/Wizard.tsx` are NOT being used by `/app/reports/new`**

**ACTION REQUIRED BEFORE QA**:
1. Find which wizard component `/app/reports/new` uses
2. Verify it's using the updated `Wizard.tsx` from R1 (with all 8 types)
3. If it's a different wizard, apply R1 changes there too
4. Redeploy frontend

**Until this is fixed, you can only test 4 report types from the UI.**

---

## 📋 SETUP

### Test Accounts (from `docs/DEMO_ACCOUNTS.md`)

1. **Solo Agent (Pro Plan)**
   - Email: `agent-pro@trendyreports-demo.com`
   - Password: `DemoAgent123!`
   - URL: https://www.trendyreports.io/login

2. **Affiliate**
   - Email: `affiliate@trendyreports-demo.com`
   - Password: `DemoAff123!`
   - **Before testing**: Configure branding (logo, colors, contact info) at `/app/branding`

3. **Sponsored Agent**
   - Email: `agent-sponsored@trendyreports-demo.com`
   - Password: `DemoAgent123!`
   - (Sponsored by affiliate above, should see affiliate branding)

### Test Markets

Use these consistently for easy comparison:
- **City A**: La Verne, CA (primary)
- **City B**: Pasadena, CA (backup)

### Output Folder Structure

Create folder: `/qa/reports/`

Structure:
```
/qa/reports/
  /{report_slug}/
    /solo_agent/
      /preview_html/  (screenshots)
      /pdf/          (downloaded PDFs)
      /email/        (.eml files or screenshots)
    /affiliate_sponsored/
      /preview_html/
      /pdf/
      /email/
```

---

## 🎯 TEST MATRIX

### Core 4 (MUST BE IMPECCABLE)
1. market_snapshot
2. new_listings
3. new_listings_gallery
4. featured_listings

### Secondary 4 (MUST BE CLEAN & "BETA" ACCEPTABLE)
5. inventory
6. closed
7. price_bands
8. open_houses

**Total**: 8 reports × 2 personas × 3 surfaces = **48 artifacts**

---

## 📝 PER-REPORT TEST PROCEDURE

### PHASE 1: Solo Agent Testing

For each report type (market_snapshot, new_listings, etc.):

#### 1.1 In-App HTML Preview (Solo)

1. **Login**: `agent-pro@trendyreports-demo.com` / `DemoAgent123!`
2. **Navigate**: `/app/reports/new`
3. **Create Report**:
   - Report Type: {report_slug}
   - Area: La Verne, CA (or City mode)
   - Lookback: 30 days
   - Property Types: Residential
   - Click "Generate Report"
4. **Wait**: Worker processes (30-60 seconds)
5. **Open Preview**: Click "View" or navigate to `/app/print/{runId}`
6. **Capture**:
   - Full-page screenshot
   - Save as: `/qa/reports/{report_slug}/solo_agent/preview_html/{slug}_solo_preview.png`
7. **Checklist**:
   - [ ] Title correct (e.g., "La Verne Market Snapshot")
   - [ ] Agent name appears (not affiliate logo)
   - [ ] Tables/charts align, no broken images
   - [ ] Colors neutral or agent-branded
   - [ ] No lorem ipsum or dev notes

#### 1.2 PDF (Solo)

1. **From same report**: Click "Download PDF" or Print → Save as PDF
2. **Save**: `/qa/reports/{report_slug}/solo_agent/pdf/{slug}_solo.pdf`
3. **Open locally** and check:
   - [ ] Header/footer present
   - [ ] No clipped text or chopped headings
   - [ ] Same data as HTML preview (spot-check numbers)
   - [ ] Agent branding consistent
   - [ ] Page breaks reasonable (not mid-table)

#### 1.3 Email (Solo)

**Option A: Via Schedule (Automated)**
1. **Navigate**: `/app/schedules/new`
2. **Create Schedule**:
   - Report Type: {report_slug}
   - Area: La Verne, CA
   - Cadence: Weekly (or trigger manually via DB if you know how)
   - Recipient: Your email (or agent-pro's email)
3. **Manually trigger** (if possible):
   ```sql
   UPDATE schedules SET next_run_at = NOW() - INTERVAL '1 minute'
   WHERE id = '<schedule_id>';
   ```
4. **Wait**: Worker ticker (up to 60 seconds) + email delivery
5. **Check Email**:
   - Save as: `/qa/reports/{report_slug}/solo_agent/email/{slug}_solo_email.eml` (or screenshot)
6. **Checklist**:
   - [ ] Subject line correct ("Market Snapshot for La Verne")
   - [ ] Logo: TrendyReports default (not affiliate)
   - [ ] Colors consistent with product branding
   - [ ] CTA links work (View Online, Download PDF, Unsubscribe)
   - [ ] No broken image placeholders

**Option B: Direct Worker Test (Advanced)**
- If you have worker access, trigger `generate_report` task directly with test params

---

### PHASE 2: Affiliate / Sponsored Agent Testing

For each report type:

#### 2.1 Configure Affiliate Branding

1. **Login as Affiliate**: `affiliate@trendyreports-demo.com` / `DemoAff123!`
2. **Navigate**: `/app/branding`
3. **Set**:
   - Logo URL: (upload or use CDN link)
   - Primary Color: `#FF6B35` (example: orange)
   - Contact Info: "Demo Title Company | (555) 123-4567"
4. **Save**

#### 2.2 In-App Preview & PDF (Sponsored Agent)

1. **Login as Sponsored Agent**: `agent-sponsored@trendyreports-demo.com` / `DemoAgent123!`
2. **Repeat 1.1 & 1.2** (create report, capture preview, download PDF)
3. **Save as**:
   - Preview: `/qa/reports/{report_slug}/affiliate_sponsored/preview_html/{slug}_affiliate_preview.png`
   - PDF: `/qa/reports/{report_slug}/affiliate_sponsored/pdf/{slug}_affiliate.pdf`
4. **Checklist**:
   - [ ] Header shows **affiliate logo** (not TrendyReports)
   - [ ] Colors match **affiliate brand** (e.g., orange)
   - [ ] Footer shows **affiliate contact info**
   - [ ] Agent name appears in appropriate places (secondary)
   - [ ] No TrendyReports branding where white-label should hide it

#### 2.3 Email (Affiliate)

**Test affiliate-branded email to sponsored agent**:

1. **Login as Affiliate**: `affiliate@trendyreports-demo.com`
2. **Create Schedule** (or use API if available):
   - Report Type: {report_slug}
   - Recipients: **Select sponsored agent** or group containing sponsored agent
3. **Trigger & Wait**
4. **Check sponsored agent's email**:
   - Save as: `/qa/reports/{report_slug}/affiliate_sponsored/email/{slug}_affiliate_email.eml`
5. **Checklist**:
   - [ ] Subject looks white-label (not generic "TrendyReports")
   - [ ] Logo, footer, colors match **affiliate brand**
   - [ ] No mention of TrendyReports in branding spots
   - [ ] Links still work (OK if they point to trendyreports.io)

---

## 🔍 VISUAL QA CHECKLIST (Per Artifact)

For every file captured (48 total), run this checklist:

### Layout & Visuals
- [ ] No broken images or missing content chunks
- [ ] Titles/headings consistent across HTML/PDF/email
- [ ] Tables readable on desktop (email: also check mobile if possible)
- [ ] PDFs: First page looks professional (Core 4 especially)
- [ ] PDFs: Page breaks sane (no heading alone at bottom)

### Data & Copy
- [ ] City/market name correct
- [ ] Date ranges clearly labeled ("Last 30 days", etc.)
- [ ] Metrics labeled correctly (no copy/paste mismatch like "Closed Sales" on price_bands)
- [ ] No placeholder copy ("Lorem ipsum", dev notes, TODOs)

### Branding
**Solo Agent**:
- [ ] No affiliate logo
- [ ] Agent name/contact as primary
- [ ] Colors match TrendyReports/solo styling

**Affiliate / Sponsored**:
- [ ] Affiliate logo dominates header/footer
- [ ] Affiliate brand color applied
- [ ] Sponsored agent shown in secondary places (if designed)
- [ ] No internal naming leaks (IDs, dev labels)

### Links & Technical
- [ ] "View Online" → correct print/run page
- [ ] "Download PDF" → valid presigned URL
- [ ] "Unsubscribe" → unsubscribe flow (if implemented)
- [ ] No HTTP 404s / 500s on any link
- [ ] No 500s in worker logs during generation

---

## 📊 ISSUE TRACKING

As you find issues, **document immediately** in `REPORTS_VISUAL_ISSUES.md`:

```markdown
# Reports Visual Issues

## Core 4

### market_snapshot
- [ ] **BLOCKER** - Solo Email: CTA button broken (404 on PDF link)
- [ ] **MAJOR** - Affiliate PDF: Footer still shows TrendyReports logo alongside affiliate logo
- [ ] **MINOR** - Solo Preview: Font size inconsistent (14px vs 16px in different sections)

### new_listings
...

## Secondary 4

### inventory
- [ ] **MAJOR** - Subject line says "Market Snapshot" instead of "Inventory Report"
...
```

**Severity Levels**:
- **BLOCKER**: Cannot ship; fix before "ready to sell"
- **MAJOR**: Ugly/confusing but not broken; fix soon
- **MINOR**: Cosmetic polish

---

## 🎯 COMPLETION CRITERIA

### Core 4 Reports
**All of these MUST PASS** (no Blockers):
- market_snapshot
- new_listings
- new_listings_gallery
- featured_listings

**Pass Means**:
- Preview HTML: Professional, branded correctly
- PDF: Clean layout, no broken elements
- Email: Subject/body/links correct, branding applied

### Secondary 4 Reports
**Acceptable if**:
- No Blockers
- Major issues are documented and acceptable for "Beta" label
- Minors can be deferred

### Final Verdict
- **SELLABLE**: Core 4 pass, Secondary 4 acceptable as Beta
- **NOT SELLABLE YET**: Any Core 4 has Blockers

---

## 📁 DELIVERABLES

After completing all tests:

1. **48 Artifacts** in `/qa/reports/` folder structure
2. **REPORTS_VISUAL_ISSUES.md** with all findings categorized by severity
3. **Decision**: "SELLABLE" or "NOT SELLABLE YET" based on Blockers

---

## ⏱️ ESTIMATED TIME

- **Per Report Type** (Solo + Affiliate):
  - Preview capture: 3 min
  - PDF download & check: 2 min
  - Email setup & check: 5 min
  - **Total per type**: ~10 min

- **8 Report Types × 10 min** = **80 minutes**
- **Issue documentation**: 30 min
- **Setup & switching accounts**: 30 min

**Total**: **~2.5 hours** for full systematic QA

---

## 🚀 NEXT STEPS AFTER QA

1. **If SELLABLE**:
   - Mark Reports as "QA Complete" in `SYSTEM_STATUS.md`
   - Move to revenue features (Affiliate Analytics)

2. **If NOT SELLABLE**:
   - Fix all Blockers in `REPORTS_VISUAL_ISSUES.md`
   - Re-run affected tests
   - Repeat until SELLABLE

---

**Last Updated**: Nov 24, 2025  
**Status**: Ready for execution (pending wizard fix)  
**Blocker**: Wizard only shows 4 types - fix before starting QA


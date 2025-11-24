# 🎨 PASS W3: Visual QA Execution

**Date**: Nov 24, 2025  
**Status**: ⏳ **IN PROGRESS**

---

## 📋 MISSION

Execute `REPORTS_VISUAL_QA_PLAN.md` systematically:
- Test all **8 report types**
- Across **2 personas** (Solo Agent, Affiliate/Sponsored)
- On **3 surfaces** (In-app preview, PDF, Email)
- **Total**: 48 artifacts to capture and review

---

## ✅ PRE-FLIGHT CHECKLIST

### W1-W2 Prerequisites
- ✅ **W1**: Wizard fixed (all 8 types in UI)
- ✅ **W2**: Lockstep comments added (backend/frontend/email/worker)
- ✅ **Deployed**: Changes pushed to staging

### Test Environment
- ✅ **Staging URL**: https://www.trendyreports.io
- ✅ **Demo Accounts**: Defined in `docs/DEMO_ACCOUNTS.md`
- ✅ **Test Markets**: La Verne, Pasadena

### QA Assets
- ✅ **QA Plan**: `REPORTS_VISUAL_QA_PLAN.md`
- ✅ **Issues Log**: `REPORTS_VISUAL_ISSUES.md` (ready)
- ✅ **Checklist**: Per-report review criteria defined

---

## 🧪 EXECUTION PLAN

### Phase 1: Wizard Verification (5 min)
**Goal**: Confirm all 8 types are visible in staging UI

**Steps**:
1. Navigate to https://www.trendyreports.io/app/reports/new
2. Log in as Pro Agent
3. Confirm wizard shows all 8 report types:
   - Market Snapshot ✓
   - New Listings ✓
   - New Listings Gallery ✓
   - Featured Listings ✓
   - Closed Sales ✓
   - Inventory ✓
   - Price Bands ✓
   - Open Houses ✓
4. Select each type to verify no JS/TS errors

**Expected Result**: ✅ All 8 types selectable without errors

---

### Phase 2: Core 4 Visual QA (60 min)
**Priority**: MUST BE IMPECCABLE

**Report Types**:
1. Market Snapshot
2. New Listings
3. New Listings Gallery
4. Featured Listings

**For Each Report Type**:

#### Solo Agent Tests (30 min per type)
1. **In-App Preview**:
   - Navigate to `/app/reports/new`
   - Configure: La Verne, 30 days
   - Generate report
   - Capture screenshot
   - Review: Layout, data, branding, links

2. **PDF**:
   - Click "Download PDF" from report view
   - Open PDF
   - Save to QA folder
   - Review: Formatting, page breaks, images

3. **Email**:
   - Create schedule with this report type
   - Trigger immediate send (or wait for next run)
   - Check inbox
   - Save .eml file
   - Review: Header, CTA, branding, links

#### Affiliate/Sponsored Tests (15 min per type)
1. Log in as Affiliate
2. View sponsored agent's generated report
3. Verify white-label branding (logo, colors, contact)
4. Capture screenshot/PDF/email

**Acceptance Criteria** (Per Report):
- ✅ No layout breaks
- ✅ All data displays correctly
- ✅ Branding is accurate (Solo vs White-label)
- ✅ All links work
- ✅ No embarrassing errors

**Blocker Definition**: Any issue that would embarrass us in front of a paying customer

---

### Phase 3: Secondary 4 Visual QA (45 min)
**Priority**: SAFE & PRESENTABLE (Beta-level OK)

**Report Types**:
5. Inventory
6. Closed Sales
7. Price Bands
8. Open Houses

**For Each Report Type**:
- Same test flow as Core 4
- BUT: Accept Beta-level quality
- Focus: Does it work? Is it safe? Is it honest?
- Allow: Generic styling, basic layout
- Block: Crashes, data errors, false claims

**Acceptance Criteria** (Per Report):
- ✅ Generates without errors
- ✅ Data is accurate (not misleading)
- ✅ Layout is functional (not ugly)
- ✅ Links work
- ❌ Does NOT need to be beautiful

---

### Phase 4: Issue Documentation (Ongoing)
**Log Issues In**: `REPORTS_VISUAL_ISSUES.md`

**Issue Template**:
```markdown
## Issue #N: [Title]

**Report Type**: market_snapshot  
**Surface**: PDF  
**Persona**: Solo Agent  
**Severity**: Blocker / Major / Minor  

**Description**:
[What's wrong]

**Expected**:
[What should happen]

**Screenshot/Evidence**:
[Link or attachment]

**Status**: Open / Fixed / Wont-Fix  
```

**Severity Guide**:
- **Blocker**: Prevents selling (crash, data wrong, looks broken)
- **Major**: Looks unprofessional but functional
- **Minor**: Polish/nice-to-have

---

## 📊 PROGRESS TRACKER

### Wizard Verification
- [ ] Staging deployed
- [ ] Wizard shows 8 types
- [ ] No JS/TS errors on type selection

### Core 4 (MUST PASS)
- [ ] **Market Snapshot**: Solo ✓ / Affiliate ✓ / No Blockers ✓
- [ ] **New Listings**: Solo ✓ / Affiliate ✓ / No Blockers ✓
- [ ] **New Listings Gallery**: Solo ✓ / Affiliate ✓ / No Blockers ✓
- [ ] **Featured Listings**: Solo ✓ / Affiliate ✓ / No Blockers ✓

### Secondary 4 (MUST BE SAFE)
- [ ] **Inventory**: Solo ✓ / Affiliate ✓ / No Crashes ✓
- [ ] **Closed Sales**: Solo ✓ / Affiliate ✓ / No Crashes ✓
- [ ] **Price Bands**: Solo ✓ / Affiliate ✓ / No Crashes ✓
- [ ] **Open Houses**: Solo ✓ / Affiliate ✓ / No Crashes ✓

### Issue Summary
- **Blockers Found**: 0
- **Major Issues Found**: 0
- **Minor Issues Found**: 0

---

## 🎯 SUCCESS CRITERIA

### Reports System is "SELLABLE" if:
1. ✅ All 8 types accessible from wizard
2. ✅ Core 4 pass visual QA with NO Blockers
3. ✅ Secondary 4 generate without crashes
4. ✅ White-label branding works for affiliates
5. ✅ All critical links work (PDF, unsubscribe)

### Reports System is "NOT SELLABLE" if:
- ❌ Any Core 4 Blocker exists
- ❌ White-label branding fails
- ❌ Any report crashes in production

---

## 📝 EXECUTION LOG

### Session 1: Nov 24, 2025
**Time Started**: [TBD]  
**Browser**: Chrome (latest)  
**User**: [Your name/handle]

**Actions**:
1. [Starting wizard verification...]

---

**Last Updated**: Nov 24, 2025  
**Next Step**: Begin Phase 1 (Wizard Verification)


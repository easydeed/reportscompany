# REPORTS CORE HARDENING - Execution Tracker

**Date Started**: Nov 24, 2025  
**Goal**: Bring Reports to same "frozen, production-ready" state as People/Billing/Schedules

---

## ✅ PASS R1: Align Report Types (COMPLETE)

**Goal**: Eliminate type mismatches across Frontend/API/Email

**What Was Done**:
- ✅ Frontend `Wizard.tsx`: Added `new_listings_gallery`, `featured_listings` to ReportType union and reportTypes array
- ✅ Backend `schedules.py`: Added `open_houses` to Literal
- ✅ Email `template.py`: Already had all 8 types (verified)

**Result**: All 8 report types now aligned:
1. market_snapshot
2. new_listings
3. inventory
4. closed
5. price_bands
6. open_houses
7. new_listings_gallery
8. featured_listings

**Commit**: `325b4ca` - "feat(reports): PASS R1 - Align report types across frontend + API"

**Status**: ✅ **COMPLETE**

---

## ⏳ PASS R2: Lock Core 4 to Gold Standard (PENDING)

**Goal**: Prove Core 4 reports are production-grade

**Core 4 Reports**:
1. market_snapshot
2. new_listings
3. new_listings_gallery
4. featured_listings

### R2.1: Run QA Tests for Core 4

**Tests to Run** (from `REPORTS_QA_CHECKLIST.md`):
- [ ] Test 1: Market Snapshot (Agent, Email + PDF)
- [ ] Test 2: New Listings Gallery (Email + PDF with Images)
- [ ] Test 3: Affiliate Branding (White-Label)
- [ ] Test 5: Scheduled Report (Agent, Weekly)
- [ ] Test 6: Scheduled Report (Affiliate → Group)
- [ ] Test 9: Currency & Number Formatting
- [ ] Test 10: Links & CTAs in Email

**Pass Criteria**: All 7 tests must PASS for Core 4

### R2.2: Fix Any Failures

*To be populated after QA run*

### R2.3: Freeze Core 4

**Completion Criteria**:
- [ ] All 7 tests marked ✅ PASS in REPORTS_QA_CHECKLIST.md
- [ ] Known cosmetic issues documented as "acceptable minor"
- [ ] Core 4 marked as "Production-Grade" in REPORTS_MATRIX.md

**Status**: ⏳ **PENDING QA**

---

## ⏳ PASS R3: Make Secondary 4 "Safe & Presentable" (PENDING)

**Goal**: Eliminate embarrassing issues, mark as Beta if not polished

**Secondary 4 Reports**:
1. inventory
2. closed
3. price_bands
4. open_houses

### R3.1: Run Test 4 for Each Partial Report

**Test 4: Partial Reports** - For each of 4 types:
- [ ] inventory: Generates, PDF accessible, email sends
- [ ] closed: Generates, PDF accessible, email sends
- [ ] price_bands: Generates, PDF accessible, email sends
- [ ] open_houses: Generates, PDF accessible, email sends

### R3.2: Minimum Fixes

**For Each Type**:
- [ ] Subject line correct ("Inventory Report", "Closed Sales", etc.)
- [ ] Metrics labels match actual data (no copy/paste from market_snapshot)
- [ ] PDF header/footer uses same branding as Core 4

### R3.3: Mark as Beta in UI

- [ ] Wizard.tsx: Add "(Beta)" or "(Experimental)" labels to secondary reports
- [ ] REPORTS_MATRIX.md: Update notes to "Functional but generic; marked as Beta"

**Status**: ⏳ **PENDING R2 COMPLETION**

---

## ⏳ PASS R4: Final Consistency + Freeze (PENDING)

**Goal**: Reconcile docs with reality, run final QA sweep

### R4.1: Reconcile Docs

- [ ] Update `REPORTS_MATRIX.md`:
  - Remove "missing from wizard/API" notes
  - Update status columns to reflect reality
- [ ] Update `REPORTS_AUDIT.md` Section 7:
  - Move fixed issues to "Resolved"
  - Keep only nice-to-haves (charts, images) as "Future"

### R4.2: Final QA Sweep

**Re-run Key Tests**:
- [ ] Tests 1-3, 5-6, 9-10: Must be ✅
- [ ] Test 4: ✅ with "partial but acceptable" notes
- [ ] Update summary table in `REPORTS_QA_CHECKLIST.md`

### R4.3: Update SYSTEM_STATUS.md

- [ ] Set Reports to: "✅ Complete, Hardened, Production-ready"
- [ ] Document: "Core 4: Fully polished, Secondary 4: Functional (Beta)"

**Status**: ⏳ **PENDING R3 COMPLETION**

---

## 📊 Overall Progress

| Pass | Status | Completion Date |
|------|--------|-----------------|
| R1: Align Types | ✅ COMPLETE | Nov 24, 2025 |
| R2: Core 4 Gold Standard | ⏳ PENDING QA | - |
| R3: Secondary 4 Safe | ⏳ PENDING | - |
| R4: Final Freeze | ⏳ PENDING | - |

---

## 🎯 Next Action

**PASS R2.1**: Run QA Tests 1-3, 5-6, 9-10 for Core 4 reports

**How to Execute**:
1. Access staging environment
2. Follow test scenarios in `REPORTS_QA_CHECKLIST.md`
3. Document PASS/FAIL for each test
4. Update this tracker with results
5. Fix any failures immediately (R2.2)
6. Freeze Core 4 when all tests pass (R2.3)

---

**Last Updated**: Nov 24, 2025  
**Status**: R1 Complete, R2-R4 Pending


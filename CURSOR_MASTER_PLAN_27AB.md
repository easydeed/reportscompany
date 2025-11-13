# Phase 27A/B Completion - Master Plan

**Status:** Ready for Execution  
**Date:** November 13, 2025  
**Goal:** Lock down scheduled email delivery with zero landmines

---

## 🎯 GLOBAL CONSTRAINTS (READ THIS FIRST)

**Cursor - DO NOT:**
1. ❌ Touch Tailwind/UI architecture (no packages/ui changes, no v3/v4 experiments)
2. ❌ Revert working SendGrid integration (no Resend introduction)
3. ❌ Change schedule/ticker/worker queue structure
4. ❌ Make design changes (colors, spacing, typography, layouts)
5. ❌ Break existing API contracts (`/v1/schedules`, `/v1/reports`, `/v1/email/unsubscribe`)

**Cursor - MUST:**
1. ✅ Keep all changes scoped to listed files unless absolutely necessary
2. ✅ Ensure `pnpm --filter web dev` and `pnpm --filter web build` succeed
3. ✅ Maintain backwards compatibility
4. ✅ Test locally before marking complete
5. ✅ Follow acceptance criteria exactly

---

## 📋 TASK SEQUENCE

Execute in this exact order:

1. **Task 1:** Suppression + Unsubscribe Filter (30 min)
2. **Task 2:** Fix "Report ID Unknown" in PDFs (20 min)
3. **Task 3:** Fix Email Logging SQL Error (15 min)
4. **Task 4:** Fix /app Routing (404 Issue) (30 min)
5. **Task 5:** Schedules UI QA & Behavior Fixes (45 min)

**Total Estimated Time:** 2.5 hours

---

## 📁 TASK FILES CREATED

Each task has its own detailed file:

1. `CURSOR_TASK_1_SUPPRESSION.md` - Suppression filtering implementation
2. `CURSOR_TASK_2_PDF_FIX.md` - Fix PDF content issue
3. `CURSOR_TASK_3_LOGGING_FIX.md` - Fix SQL error in email logging
4. `CURSOR_TASK_4_ROUTING_FIX.md` - Fix /app 404 issues
5. `CURSOR_TASK_5_UI_QA.md` - Schedules UI behavior fixes

**Execute tasks sequentially. Do not skip ahead.**

---

## ✅ SUCCESS CRITERIA

### Phase 27A - Email Delivery MVP
- [ ] Suppression filtering implemented and tested
- [ ] Unsubscribe link works (manual test by user)
- [ ] PDFs show actual report data (no "report ID unknown")
- [ ] Email logging SQL error fixed
- [ ] All worker logs clean

### Phase 27B - Schedules UI
- [ ] `/app` and `/app/schedules` accessible on Vercel
- [ ] Can create schedule via UI
- [ ] Schedule detail page shows run history
- [ ] All UI → API → DB flows work end-to-end

---

## 🧪 TESTING CHECKLIST (For User After Cursor Completes)

### Test 1: Suppression Flow
```bash
# 1. Create test schedule with your email
# 2. Confirm email arrives
# 3. Click unsubscribe link
# 4. Check database:
SELECT * FROM email_suppressions WHERE email = 'gerardoh@gmail.com';
# 5. Trigger schedule again (update next_run_at)
# 6. Confirm NO email arrives
# 7. Check worker logs mention "suppressed"
```

### Test 2: PDF Content
```bash
# 1. Generate new scheduled report
# 2. Check email, click PDF link
# 3. Verify PDF shows:
#    - Actual city name (Houston)
#    - Real KPI numbers (not "unknown")
#    - Proper report type title
```

### Test 3: Email Logging
```bash
# 1. Run: python check_schedule_status.py
# 2. Verify: No SQL errors in output
# 3. Check email_log table has proper entries
```

### Test 4: UI Routing
```bash
# 1. Visit: https://reportscompany-web.vercel.app/app
# 2. Verify: Dark dashboard loads (not 404)
# 3. Visit: https://reportscompany-web.vercel.app/app/schedules
# 4. Verify: Schedules page loads
```

### Test 5: Schedule Creation via UI
```bash
# 1. Go to /app/schedules/new
# 2. Fill form: Houston, market_snapshot, weekly, Monday 2pm, your email
# 3. Submit
# 4. Verify: New schedule appears in list
# 5. Wait for ticker to process (60 sec)
# 6. Verify: Email arrives with correct data
```

---

## 📊 PROGRESS TRACKING

| Task | Status | Duration | Files Changed |
|------|--------|----------|---------------|
| 1. Suppression | ⏳ Pending | - | - |
| 2. PDF Fix | ⏳ Pending | - | - |
| 3. Logging Fix | ⏳ Pending | - | - |
| 4. Routing Fix | ⏳ Pending | - | - |
| 5. UI QA | ⏳ Pending | - | - |

Update this table as you complete each task.

---

## 🚨 ESCALATION

If any task is blocked or takes >2x estimated time:
1. Stop and document the blocker
2. Commit current progress
3. Ask for guidance before proceeding

---

## 📝 FINAL DELIVERABLE

After all tasks complete, update `PROJECT_STATUS-2.md`:

```markdown
## ✅ Phase 27: Scheduled Reports Email MVP - COMPLETE

**Completed:** November 13-14, 2025

### Phase 27A: Email Delivery ✅
- ✅ Ticker → Worker → SendGrid pipeline working
- ✅ Suppression filtering implemented
- ✅ Unsubscribe flow certified
- ✅ PDF content fix (report ID issue resolved)
- ✅ Email logging stabilized

### Phase 27B: Schedules UI ✅
- ✅ /app routing fixed (404 resolved)
- ✅ Schedules list and detail pages working
- ✅ Schedule creation via UI functional
- ✅ End-to-end UI → API → DB flows certified

### Key Achievements
- Full email automation with beautiful HTML templates
- Suppression list management
- PDF generation and R2 storage
- UI for schedule management
```

---

**Start with Task 1. Open `CURSOR_TASK_1_SUPPRESSION.md` now.**


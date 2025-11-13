# Phase 27A/B - Quick Start for Cursor

**Copy this entire file and paste it to Cursor to begin execution.**

---

## 🚨 GLOBAL CONSTRAINTS - READ FIRST

**Cursor, you MUST follow these rules:**

### ❌ DO NOT:
1. Touch Tailwind/UI architecture (no packages/ui changes)
2. Revert SendGrid integration (no Resend introduction)
3. Change schedule/ticker/worker queue structure
4. Make design changes (colors, spacing, fonts, layouts)
5. Break existing API contracts

### ✅ MUST:
1. Keep changes scoped to files listed in each task
2. Ensure `pnpm --filter web dev` and `pnpm --filter web build` succeed
3. Test locally before marking task complete
4. Follow acceptance criteria exactly
5. Use provided commit messages

---

## 📋 TASK SEQUENCE

**Execute in this exact order. Do NOT skip ahead.**

### Task 1: Suppression Filtering (30 min)
**File:** `CURSOR_TASK_1_SUPPRESSION.md`

**Objective:** Implement email suppression so unsubscribed users don't receive emails.

**Files to modify:**
- `apps/worker/src/worker/email/send.py`
- `apps/worker/src/worker/tasks.py`

**Key changes:**
- Add `db_conn` parameter to `send_schedule_email()`
- Query `email_suppressions` table before sending
- Filter out suppressed recipients
- Handle "all suppressed" case (return 200 without calling SendGrid)
- Update `email_log` with status column
- Wrap logging in try/except

**Test:** Insert suppression → trigger schedule → verify no email + logs show "suppressed"

**Commit:** `feat(worker): implement email suppression filtering`

---

### Task 2: PDF Content Fix (20 min)
**File:** `CURSOR_TASK_2_PDF_FIX.md`

**Objective:** Fix "report ID unknown" in PDFs by improving error handling.

**Files to modify:**
- `apps/web/app/print/[runId]/page.tsx`
- `apps/web/.env.example`
- Create `VERCEL_ENV_VAR_FIX.md` (manual step for user)

**Key changes:**
- Add detailed error logging to `fetchData()`
- Improve "Report Not Found" error page
- Remove "unknown" placeholders
- Document correct `NEXT_PUBLIC_API_BASE` value

**Root cause:** Vercel env var points to wrong API URL  
**Manual step:** User must update Vercel env var after this task

**Test:** Visit `/print/[runId]` locally → should show real data

**Commit:** `fix(web): improve print page error handling and logging`

---

### Task 3: Email Logging Fix (15 min)
**File:** `CURSOR_TASK_3_LOGGING_FIX.md`

**Objective:** Fix SQL syntax error in email logging (non-critical bug).

**Files to modify:**
- `apps/worker/src/worker/tasks.py`
- `apps/worker/src/worker/email/send.py`
- `check_schedule_status.py` (if SQL errors present)

**Key changes:**
- Wrap all email_log INSERTs in try/except
- Wrap schedule_runs UPDATEs in try/except
- Fix any SQL ORDER BY syntax errors
- Ensure logging failures never block core tasks

**Test:** Run `python check_schedule_status.py` → no SQL errors

**Commit:** `fix(worker): stabilize email logging with defensive error handling`

---

### Task 4: App Routing Fix (30 min)
**File:** `CURSOR_TASK_4_ROUTING_FIX.md`

**Objective:** Fix 404 on `/app` and `/app/schedules` routes.

**Files to check/modify:**
- `apps/web/app/app/page.tsx` (create if missing)
- `apps/web/app/app/layout.tsx` (create if missing)
- `apps/web/app/app/schedules/page.tsx` (create if missing)
- `apps/web/next.config.mjs` (remove problematic settings)
- `apps/web/middleware.ts` (fix if blocking /app routes)

**Key changes:**
- Verify route structure exists
- Fix next.config.mjs (remove `output: 'export'`)
- Update middleware to allow /app routes
- Ensure build includes dashboard routes

**Test:** 
- Local: `http://localhost:3000/app` → loads dashboard
- Build: `pnpm --filter web build` → succeeds

**Commit:** `fix(web): resolve /app routing 404 issues on production`

---

### Task 5: UI Behavior Fixes (45 min)
**File:** `CURSOR_TASK_5_UI_QA.md`

**Objective:** Wire Schedules UI to backend with proper validation and error handling.

**Files to modify:**
- `apps/web/app/app/schedules/page.tsx` (list)
- `apps/web/app/app/schedules/new/page.tsx` (create form)
- `apps/web/app/app/schedules/[id]/page.tsx` (detail)
- Create `apps/web/app/api/proxy/v1/schedules/route.ts` (if missing)

**Key changes:**
- Load schedules from API
- Implement form validation (required fields, email format)
- Handle API errors gracefully
- Sort run history by created_at DESC
- Fix pause/resume toggle persistence

**Test:** Create schedule via UI → wait 60 sec → email arrives

**Commit:** `fix(web): schedules UI behavior and API integration`

---

## 🧪 TESTING REQUIREMENTS

### After Each Task
1. **Run locally** - ensure no crashes
2. **Check acceptance criteria** in task file
3. **Commit** with provided message
4. **Move to next task**

### After All Tasks
User will test:
- Suppression flow (manual)
- Unsubscribe link (manual)
- PDF content (verify real data)
- UI end-to-end (create schedule → email arrives)

---

## 📊 PROGRESS TRACKING

Update `CURSOR_MASTER_PLAN_27AB.md` after each task:

| Task | Status | Duration | Files Changed |
|------|--------|----------|---------------|
| 1. Suppression | ⏳ Pending | - | - |
| 2. PDF Fix | ⏳ Pending | - | - |
| 3. Logging Fix | ⏳ Pending | - | - |
| 4. Routing Fix | ⏳ Pending | - | - |
| 5. UI QA | ⏳ Pending | - | - |

---

## 🚨 ESCALATION RULES

If a task:
- Takes >2x estimated time → Stop, document blocker, ask for guidance
- Breaks existing functionality → Revert, analyze, try different approach
- Requires files not listed → Ask before modifying

---

## ✅ FINAL DELIVERABLE

After all tasks complete, update `PROJECT_STATUS-2.md` with:

```markdown
## ✅ Phase 27: Scheduled Reports Email MVP - COMPLETE

### Phase 27A: Email Delivery ✅
- ✅ Suppression filtering implemented
- ✅ Unsubscribe flow certified
- ✅ PDF content fix
- ✅ Email logging stabilized

### Phase 27B: Schedules UI ✅
- ✅ /app routing fixed
- ✅ Schedules CRUD via UI
- ✅ End-to-end flow certified
```

---

## 🚀 BEGIN EXECUTION

**Cursor, start with Task 1:**

1. Open `CURSOR_TASK_1_SUPPRESSION.md`
2. Read entire task file
3. Follow instructions exactly
4. Test locally
5. Commit with provided message
6. Move to Task 2

**DO NOT skip ahead. Execute sequentially.**

**Current working directory:** `C:\Users\gerar\Marketing Department Dropbox\Projects\Trendy\reportscompany`

**Let's lock down Phase 27A/B with zero landmines.** 🎯


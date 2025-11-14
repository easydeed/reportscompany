# Phase 29C Status - Industry Affiliates & Multi-Account

**Date:** November 14, 2025  
**Status:** 🏗️ **FOUNDATION COMPLETE** - Ready for API Implementation  
**Commit:** `e9fde0c` - Phase 29C foundation pushed to GitHub

---

## ✅ **COMPLETED WORK**

### **1. Phase 29A Migration Successfully Applied** ✅

```
======================================================================
✅ MIGRATION SUCCESSFUL!
======================================================================

📊 Database Changes:
   - Plans in database: 5
   - Accounts migrated: 1
   - Account users: 1

📋 Plans Seeded:
   - Free                 (free           ):   50 reports/month
   - Sponsored Free       (sponsored_free ):   75 reports/month
   - Pro                  (pro            ):  300 reports/month
   - Team                 (team           ): 1000 reports/month
   - Industry Affiliate   (affiliate      ): 5000 reports/month
```

**New Database Tables:**
- ✅ `plans` - Plan definitions with limits
- ✅ `account_users` - User-account memberships with roles
- ✅ `accounts` - Extended with `account_type`, `sponsor_account_id`, `monthly_report_limit_override`

---

### **2. Phase 29C Foundation (Commits)** ✅

**Commit:** `e9fde0c` - Foundation - RLS extension, account services

**Files Created:**
- ✅ `apps/api/src/api/services/accounts.py` (135 lines)
  - `get_user_accounts()` - List all accounts for a user
  - `get_default_account_for_user()` - Resolve default account
  - `verify_user_account_access()` - Check user access
  - `get_account_info()` - Get account details
- ✅ `PHASE_29C_EXECUTION_PLAN.md` - Full task breakdown
- ✅ `PHASE_29C_CURSOR_INSTRUCTIONS.md` - Complete implementation guide
- ✅ `run_phase_29a_migration.py` - Migration runner script

**Files Modified:**
- ✅ `apps/api/src/api/db.py` - Extended `set_rls()` function
  ```python
  def set_rls(cur, account_id: str, user_id: str | None = None, user_role: str | None = None):
  ```

---

## 📋 **REMAINING IMPLEMENTATION**

### **Backend API (Phase 29C.3A - 29C.6A)**

These are **fully specified** in `PHASE_29C_CURSOR_INSTRUCTIONS.md` - ready to copy-paste!

| Task | Endpoint | Status | File |
|------|----------|--------|------|
| 29C.3A | GET /v1/account/accounts | ⏳ Ready | `routes/account.py` |
| 29C.3A | POST /v1/account/use | ⏳ Ready | `routes/account.py` |
| 29C.4A | Affiliate services | ⏳ Ready | `services/affiliates.py` |
| 29C.4B | GET /v1/affiliate/overview | ⏳ Ready | `routes/affiliates.py` |
| 29C.6A | POST /v1/affiliate/invite-agent | ⏳ Ready | `routes/affiliates.py` |

**Estimated Implementation Time:** 30-45 minutes (copy-paste from instructions doc)

---

### **Frontend Components (Phase 29C.3B - 29C.7)**

| Task | Component | Status | File |
|------|-----------|--------|------|
| 29C.3B | Account Switcher | ⏳ Pending | `components/account-switcher.tsx` |
| 29C.3B | API Proxy Routes | ⏳ Pending | `app/api/proxy/v1/account/[...path]/route.ts` |
| 29C.5 | Affiliate Dashboard | ⏳ Pending | `app/affiliate/page.tsx` |
| 29C.6B | Invite Agent Modal | ⏳ Pending | `components/invite-agent-modal.tsx` |
| 29C.6C | Welcome/Onboarding Page | ⏳ Pending | `app/welcome/page.tsx` |
| 29C.7 | Regular User Polish | ⏳ Pending | Various files |

**Estimated Implementation Time:** 1-2 hours

---

## 🚀 **NEXT STEPS - OPTION A: Cursor Full Auto**

**Paste this into Cursor:**

```
PHASE 29C - IMPLEMENTATION REQUEST

Foundation is complete (commit e9fde0c). Please implement the remaining Phase 29C tasks:

1. Read PHASE_29C_CURSOR_INSTRUCTIONS.md
2. Implement all backend tasks (29C.3A, 29C.4A, 29C.4B, 29C.6A)
   - Copy the exact code from the instructions
   - Update main.py to include new routers
   - Test each endpoint after implementation
3. Implement all frontend tasks (29C.3B, 29C.5, 29C.6B, 29C.6C, 29C.7)
4. Create API proxy routes for new endpoints
5. Test the complete flow

Constraints:
- Do NOT break Phase 29A/29B functionality
- Keep backward compatibility for single-account users
- Follow existing patterns in the codebase
```

---

## 🚀 **NEXT STEPS - OPTION B: Manual Step-by-Step**

### **Step 1: Backend API Endpoints (30 min)**

1. Open `PHASE_29C_CURSOR_INSTRUCTIONS.md`
2. Copy code for Task 29C.3A into `apps/api/src/api/routes/account.py`
3. Create `apps/api/src/api/services/affiliates.py` (Task 29C.4A)
4. Create `apps/api/src/api/routes/affiliates.py` (Task 29C.4B + 29C.6A)
5. Update `apps/api/src/api/main.py` to include affiliate router
6. Test endpoints using curl or Postman

### **Step 2: Redeploy API (5 min)**

```bash
# Render will auto-deploy on push, or manual trigger:
# Render Dashboard → reportscompany → Deploy
```

### **Step 3: Frontend Components (1-2 hours)**

1. Create account switcher component
2. Create affiliate dashboard page
3. Create invite modal
4. Create welcome page
5. Add API proxy routes

### **Step 4: End-to-End Testing**

1. Set Demo Account to `INDUSTRY_AFFILIATE`
2. Test affiliate dashboard
3. Test invite flow
4. Verify regular users see no affiliate UI

---

## 🧪 **TESTING PLAN**

### **Backend API Tests**

```bash
# 1. List user accounts
curl -X GET "https://reportscompany.onrender.com/v1/account/accounts" \
  -H "Authorization: Bearer YOUR_TOKEN"

# 2. Get affiliate overview (requires INDUSTRY_AFFILIATE account)
curl -X GET "https://reportscompany.onrender.com/v1/affiliate/overview" \
  -H "Authorization: Bearer YOUR_TOKEN"

# 3. Invite agent
curl -X POST "https://reportscompany.onrender.com/v1/affiliate/invite-agent" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Test Agent",
    "email": "testagent@example.com",
    "default_city": "La Verne"
  }'
```

### **Database Verification**

```sql
-- Set Demo Account to affiliate
UPDATE accounts 
SET account_type = 'INDUSTRY_AFFILIATE', 
    plan_slug = 'affiliate'
WHERE id = '912014c3-6deb-4b40-a28d-489ef3923a3a';

-- Verify sponsored accounts
SELECT 
    a.name,
    a.account_type,
    a.plan_slug,
    sponsor.name AS sponsor_name
FROM accounts a
LEFT JOIN accounts sponsor ON a.sponsor_account_id = sponsor.id
WHERE a.sponsor_account_id IS NOT NULL;
```

---

## 📊 **PHASE 29 OVERALL PROGRESS**

| Phase | Status | Completion |
|-------|--------|------------|
| 29A - Schema & Plans | ✅ COMPLETE | 100% |
| 29B - Usage & Limits | ✅ COMPLETE | 100% |
| **29C - Affiliates & Multi-Account** | 🏗️ **IN PROGRESS** | **30%** |
| 29D - Stripe Integration | ⏳ Pending | 0% |
| 29E - UI Polish & Plan Pages | ⏳ Pending | 0% |

---

## 📁 **KEY FILES FOR REFERENCE**

- **Implementation Guide:** `PHASE_29C_CURSOR_INSTRUCTIONS.md` ⭐
- **Execution Plan:** `PHASE_29C_EXECUTION_PLAN.md`
- **Migration Script:** `run_phase_29a_migration.py`
- **Phase 29A+B Docs:** `PHASE_29AB_COMPLETE.md`
- **Account Services:** `apps/api/src/api/services/accounts.py`

---

## 💡 **RECOMMENDATIONS**

1. **For Speed:** Use Option A (Cursor Full Auto) - all code is ready
2. **For Control:** Use Option B (Manual Step-by-Step)
3. **Test Backend First:** Verify API endpoints before building frontend
4. **Use Demo Account:** Set it to INDUSTRY_AFFILIATE for testing

---

**Ready to proceed with Phase 29C implementation!** 🚀

Choose your path (Option A or B) and let's complete this phase!


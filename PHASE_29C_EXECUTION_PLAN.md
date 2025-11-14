# Phase 29C Execution Plan - Industry Affiliates & Multi-Account

**Date:** November 14, 2025  
**Status:** 🏗️ STARTING IMPLEMENTATION

---

## 🎯 **Goal**

Enable industry affiliates to sponsor agents and manage multiple accounts, while keeping the regular user experience simple.

---

## 📋 **Task Breakdown**

### **Backend - Session & RLS (29C.1-29C.2)**
- [ ] 29C.1: Extend `set_rls()` to accept user_id and user_role
- [ ] 29C.2: Create `get_user_accounts()` helper in services/accounts.py
- [ ] Update all `set_rls()` call sites to pass user info

### **Backend - Account Switching (29C.3A)**
- [ ] Create `GET /v1/account/accounts` - list user's accounts
- [ ] Create `POST /v1/account/use` - switch current account
- [ ] Implement account context storage (cookie/session)

### **Backend - Affiliate Services (29C.4A-29C.4B)**
- [ ] Create `services/affiliates.py` with:
  - `get_affiliate_overview()`
  - `get_sponsored_accounts()`
- [ ] Create `routes/affiliates.py` with:
  - `GET /v1/affiliate/overview`
  - Verify affiliate account type

### **Backend - Invite Flow (29C.6A)**
- [ ] Create `POST /v1/affiliate/invite-agent`
- [ ] Generate invite tokens
- [ ] Create `POST /v1/auth/accept-invite`
- [ ] Send invitation emails

### **Frontend - Account Switcher (29C.3B)**
- [ ] Create `AccountSwitcher` component
- [ ] Add to app shell in `/app/layout.tsx`
- [ ] API proxy for account endpoints

### **Frontend - Affiliate Dashboard (29C.5)**
- [ ] Create `/app/affiliate/page.tsx`
- [ ] Summary cards (sponsored count, reports)
- [ ] Sponsored accounts table
- [ ] Conditional nav item

### **Frontend - Invite UI (29C.6B-29C.6C)**
- [ ] Add "Invite Agent" button to affiliate dashboard
- [ ] Create invite modal/form
- [ ] Create `/app/welcome` onboarding page
- [ ] Handle invite token flow

### **Polish - Regular User Experience (29C.7)**
- [ ] Hide switcher for single-account users
- [ ] Hide affiliate nav for regular accounts
- [ ] 403 handler for non-affiliates accessing /app/affiliate

---

## 🔧 **Implementation Order**

1. **Session & RLS** (29C.1-29C.2) - Foundation
2. **Account Services** (29C.3A, 29C.4A-29C.4B) - Backend logic
3. **Invite Flow Backend** (29C.6A) - Core affiliate feature
4. **Account Switcher UI** (29C.3B) - Enable multi-account
5. **Affiliate Dashboard UI** (29C.5, 29C.6B) - Affiliate experience
6. **Onboarding Page** (29C.6C) - Agent experience
7. **Regular User Polish** (29C.7) - Backwards compatibility

---

## 📦 **Expected Deliverables**

### **New Backend Files:**
- `apps/api/src/api/services/accounts.py`
- `apps/api/src/api/services/affiliates.py`
- `apps/api/src/api/routes/affiliates.py`
- Modifications to `apps/api/src/api/db.py`
- Modifications to existing route files

### **New Frontend Files:**
- `apps/web/components/account-switcher.tsx`
- `apps/web/app/affiliate/page.tsx`
- `apps/web/app/welcome/page.tsx`
- `apps/web/app/api/proxy/v1/account/[...path]/route.ts`
- `apps/web/app/api/proxy/v1/affiliate/[...path]/route.ts`

### **Database Changes:**
- Optional: `signup_tokens` table for invite flow (if not exists)

---

## 🧪 **Testing Checklist**

### **Multi-Account User:**
- [ ] Can see account switcher
- [ ] Can switch between accounts
- [ ] RLS properly filters data per account

### **Industry Affiliate:**
- [ ] Can access /app/affiliate dashboard
- [ ] Sees sponsored accounts list
- [ ] Can invite new agents
- [ ] Invited agents receive email

### **Regular User:**
- [ ] No account switcher shown (single account)
- [ ] Cannot access /app/affiliate (403)
- [ ] Existing /app experience unchanged

### **Invited Agent:**
- [ ] Receives invitation email
- [ ] Can accept invite and set password
- [ ] Has `sponsored_free` plan
- [ ] `sponsor_account_id` correctly set

---

## 🚀 **Success Criteria**

✅ Multi-account users can switch between accounts seamlessly  
✅ Affiliates have a dedicated dashboard showing sponsored agents  
✅ Affiliates can invite agents who get `sponsored_free` plan  
✅ Regular users see no affiliate complexity  
✅ All RLS policies respect user + role context  
✅ Backwards compatible with Phase 29A/B  

---

**Status:** Ready to begin implementation! 🎯


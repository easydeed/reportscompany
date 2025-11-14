# Authentication Test Checklist

**Last Updated:** November 14, 2025  
**Purpose:** Ensure auth changes don't break existing functionality

---

## ✅ Required Tests Before Merging Auth Changes

When you modify **any** authentication logic (JWT signing, cookie setting, middleware, RLS), **all** tests in this checklist must pass.

---

## Backend Tests (pytest)

Run: `pytest apps/api/tests`

### Unit/Integration Tests

| Test Suite | Description | Status |
|------------|-------------|--------|
| `test_accept_invite_success` | Valid token sets password, marks used, returns JWT | Required ✅ |
| `test_accept_invite_invalid_token` | Non-existent token returns 400 | Required ✅ |
| `test_accept_invite_expired_token` | Expired token returns 400 | Required ✅ |
| `test_accept_invite_token_reuse` | Already-used token returns 400 | Required ✅ |
| `test_accept_invite_password_too_short` | Password < 8 chars returns 400 | Required ✅ |
| `test_accept_invite_sets_cookie` | Accept-invite sets `mr_token` cookie | Required ✅ |
| `test_plans_limits_*` | All plan limit tests (resolve, usage, evaluate) | Required ✅ |
| `test_affiliate_branding_*` | All branding resolution tests | Required ✅ |

**Pass Criteria:** All tests green, no errors or warnings

---

## Frontend Tests (Jest)

Run: `pnpm --filter web test`

### Component Tests

| Test Suite | Description | Status |
|------------|-------------|--------|
| `AccountSwitcher.test.tsx` | Account switching with cookie auth | Required ✅ |
| `PlanPage.test.tsx` | Plan page loads with authenticated user | Required ✅ |
| `AffiliatePage.test.tsx` | Affiliate dashboard with 403 handling | Required ✅ |

**Pass Criteria:** All component tests green

---

## E2E Tests (Playwright)

Run: `npx playwright test`

### Authentication Flow Tests

| Test | Description | Status |
|------|-------------|--------|
| `auth.spec.ts` – login works | User can log in and reach `/app` | Required ✅ |
| `auth.spec.ts` – cookie set | `mr_token` cookie is present after login | Required ✅ |
| `auth.spec.ts` – logout clears | Logout clears cookie and redirects | Required ✅ |

### Protected Page Tests

| Test | Description | Status |
|------|-------------|--------|
| `plan.spec.ts` – authenticated access | `/account/plan` works after login | Required ✅ |
| `plan.spec.ts` – plan name visible | Plan name displays correctly | Required ✅ |
| `plan.spec.ts` – usage meter | Usage meter shows current usage | Required ✅ |

### Affiliate Tests

| Test | Description | Status |
|------|-------------|--------|
| `affiliate.spec.ts` – affiliate login | Affiliate user can log in | Required ✅ |
| `affiliate.spec.ts` – dashboard loads | `/app/affiliate` loads with metrics | Required ✅ |
| `affiliate.spec.ts` – agents table | Agents table displays correctly | Required ✅ |

### Invite Flow Tests (Optional but Recommended)

| Test | Description | Status |
|------|-------------|--------|
| `invite.spec.ts` – accept invite | Agent can accept invite and set password | Recommended ⭐ |
| `invite.spec.ts` – redirect after accept | Redirects to `/app` after successful accept | Recommended ⭐ |
| `invite.spec.ts` – expired token | Shows error for expired invite link | Recommended ⭐ |

---

## Manual Verification Checklist

After automated tests pass, manually verify:

### Login Flow

- [ ] Navigate to `/login`
- [ ] Enter valid credentials
- [ ] Click "Sign In"
- [ ] **Verify:** Redirected to `/app`
- [ ] **Verify:** `mr_token` cookie is set (DevTools → Application → Cookies)
- [ ] **Verify:** Cookie has `HttpOnly`, `Secure`, `SameSite=Lax` attributes

### Protected Routes

- [ ] While logged in, visit `/account/plan`
- [ ] **Verify:** Page loads without error
- [ ] **Verify:** Plan name displays
- [ ] **Verify:** Usage meter shows current usage

- [ ] Visit `/app/affiliate` (as affiliate user)
- [ ] **Verify:** Dashboard loads
- [ ] **Verify:** Summary cards show metrics
- [ ] **Verify:** Agents table displays

### Logout

- [ ] Click "Logout" (or manually clear `mr_token` cookie)
- [ ] Try to visit `/account/plan`
- [ ] **Verify:** Redirected to `/login`

### Cross-Origin Behavior

- [ ] From Vercel frontend (`https://reportscompany-web.vercel.app`)
- [ ] Make authenticated request to API (`https://reportscompany.onrender.com`)
- [ ] **Verify:** Request succeeds (CORS configured correctly)
- [ ] **Verify:** Cookie is sent with request

---

## Regression Tests

These scenarios broke in Phase 29D and must never break again:

### 🔴 The `mr_token=undefined` Bug

**Scenario:**
1. Frontend login calls backend `/v1/auth/login`
2. Backend returns `{ access_token: <jwt> }`
3. Frontend tries to read `data.token` (typo: should be `data.access_token`)
4. Frontend sets `mr_token=undefined` in cookie
5. All authenticated requests fail with `DecodeError: Not enough segments`

**Prevention:**
- ✅ Backend sets cookie via `Set-Cookie` header (not frontend)
- ✅ Frontend uses proxy route (same-origin for cookie)
- ✅ Frontend NEVER manually manipulates `mr_token` cookie

**Tests:**
- `test_accept_invite_sets_cookie` (backend test)
- `auth.spec.ts` – verify cookie value is valid JWT (E2E test)

### 🔴 JWT Secret Mismatch

**Scenario:**
1. Backend signs JWT with `JWT_SECRET="dev-secret"`
2. Middleware verifies JWT with `JWT_SECRET="<different secret>"`
3. All requests fail with `401: Unauthorized`

**Prevention:**
- ✅ `JWT_SECRET` environment variable set on Render
- ✅ Diagnostic logging on app startup shows secret length
- ✅ Middleware logs JWT verification failures

**Tests:**
- Manual verification: Check Render logs for `JWT_SECRET` confirmation
- E2E test: Login and make authenticated request (would fail if mismatch)

### 🔴 Missing Cookie Fallback in Middleware

**Scenario:**
1. Login sets `mr_token` cookie
2. Middleware only checks `Authorization: Bearer` header
3. Cookie is ignored → all cookie-auth requests fail with 401

**Prevention:**
- ✅ Middleware checks `mr_token` cookie as fallback
- ✅ Order: Try `Authorization` header first, then cookie

**Tests:**
- `test_plan_usage_auth_cookie` (backend test)
- `plan.spec.ts` – page load after login (E2E test)

---

## Test Environments

### Local Development

```bash
# Backend
cd apps/api
pytest apps/api/tests

# Frontend
cd apps/web
pnpm test

# E2E (requires running services)
E2E_BASE_URL=http://localhost:3000 \
E2E_REGULAR_EMAIL=gerardoh@gmail.com \
E2E_REGULAR_PASSWORD=Test123456! \
npx playwright test
```

### CI (GitHub Actions)

Tests run automatically on:
- **Push** to `main` (E2E only)
- **Pull Request** (all tests)
- **Path changes:** `apps/api/**`, `apps/web/**`

**Workflows:**
- `.github/workflows/backend-tests.yml`
- `.github/workflows/frontend-tests.yml`
- `.github/workflows/e2e.yml`

### Staging (Render + Vercel)

Manual smoke test after deploy:
1. Visit `https://reportscompany-web.vercel.app/login`
2. Log in as test user
3. Navigate to `/account/plan`
4. Verify page loads

---

## Failure Investigation

If auth tests fail, check:

### Backend Failures

1. **Check logs:** Render → reportscompany-api → Logs
2. **Look for:** JWT verification errors, missing `JWT_SECRET`, RLS errors
3. **Verify:** `JWT_SECRET` environment variable is set correctly
4. **Check:** Database connection string is valid

### Frontend Failures

1. **Check console:** Browser DevTools → Console
2. **Look for:** Fetch errors, 401/403 responses, cookie issues
3. **Verify:** `NEXT_PUBLIC_API_BASE` is set on Vercel
4. **Check:** CORS `ALLOWED_ORIGINS` includes Vercel domain

### E2E Failures

1. **Check screenshots:** `playwright-report/` directory
2. **Look for:** Login failures, redirect issues, cookie problems
3. **Verify:** Test credentials are valid
4. **Check:** E2E secrets are set in GitHub Actions

---

## Quick Reference

### Test Commands

```bash
# All backend tests
pytest apps/api/tests

# Specific test file
pytest apps/api/tests/test_accept_invite.py

# All frontend tests
pnpm --filter web test

# Watch mode
pnpm --filter web test:watch

# E2E tests
npx playwright test

# E2E headed (see browser)
npx playwright test --headed

# E2E specific test
npx playwright test auth.spec.ts
```

### Test Credentials

See: `docs/TEST_CREDENTIALS.md`

### Coverage

```bash
# Backend coverage
pytest --cov=apps/api/src apps/api/tests

# Frontend coverage
pnpm --filter web test --coverage
```

---

**Status:** ✅ Active Checklist  
**Last Updated:** November 14, 2025


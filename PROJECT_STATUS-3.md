# Project Status - Phases 29D + T + A + W Complete

**Last Updated:** November 15, 2025  
**Current Phase:** All Testing, Auth Docs, and White-Label Phases ✅ COMPLETE

---

## 🎯 Current Status

### ✅ Completed Phases (November 15, 2025)

#### **Phase T: Testing Stack - 100% COMPLETE**
- **Status:** ✅ ALL DELIVERABLES COMPLETE
- **Features:**
  - **T1:** 95+ backend unit tests (pytest) - plans, limits, invites, branding
  - **T2:** 70+ frontend tests (Jest + RTL) - components and template mapping
  - **T3:** 17 E2E tests (Playwright) - auth, plan, affiliate, stripe flows
  - **T4:** 3 CI workflows (GitHub Actions) - automated testing on every push
  - **Total:** 180+ automated tests protecting core business logic

#### **Phase A: Auth Documentation - 100% COMPLETE**
- **Status:** ✅ ALL DELIVERABLES COMPLETE
- **Features:**
  - **A1:** `AUTH_ARCHITECTURE_V1.md` (425 lines) - complete auth contract
  - **A2:** `AUTH_TEST_CHECKLIST.md` (315 lines) - regression prevention guide
  - **Total:** 740+ lines of comprehensive authentication documentation

#### **Phase W: White-Label Branding - 100% COMPLETE**
- **Status:** ✅ ALL DELIVERABLES COMPLETE
- **Features:**
  - **W1:** Database schema + `get_brand_for_account` helper
  - **W2:** Branding API (GET/POST) + Management UI with live preview
  - **W3:** Email branding integration (templates + worker)
  - **W4:** PDF branding integration (API + templates + print page)
  - **Result:** Complete white-label system for affiliate accounts

---

### ✅ Previously Completed Phases

#### **Phase 29D: Stripe Integration (November 14, 2025)**
- **Status:** ✅ FULLY OPERATIONAL
- **Features:**
  - Stripe Checkout integration for Pro ($29/month) and Team ($99/month) plans
  - Stripe Customer Portal for subscription management
  - Webhook handler syncing subscription status to `accounts.plan_slug`
  - Plan & Usage page displaying current plan, limits, and usage
  - Cookie-based authentication working end-to-end

#### **Phase 30: Affiliate Branding Foundation**
- **Status:** ✅ COMPLETE (Enhanced by Phase W)
- **Features:**
  - Industry affiliates can upload custom logos
  - Branding appears on agent dashboards
  - Settings page for managing affiliate appearance

#### **Phase 29C: Frontend Dashboard**
- **Status:** ✅ COMPLETE
- **Features:**
  - React-based dashboard with metrics
  - Usage tracking and reporting
  - Plan limits display

#### **Phase 29A-B: Plan Enforcement & Affiliate System**
- **Status:** ✅ COMPLETE
- **Features:**
  - Plan-based usage limits (Free: 50, Pro: 100, Team: 200)
  - Affiliate invite system
  - Sponsored accounts

---

## 🏗️ Architecture Overview

### **Stack**
- **Backend:** FastAPI (Python) on Render
- **Frontend:** Next.js 14 (App Router) on Vercel
- **Database:** PostgreSQL on Render
- **Payments:** Stripe (Test Mode)
- **Auth:** JWT with HTTP-only cookies

### **Key Endpoints**
- **API Base:** `https://reportscompany.onrender.com`
- **Web Base:** `https://reportscompany-web.vercel.app`

### **Authentication Flow**
```
1. User logs in via /login
   ↓
2. Frontend → /api/proxy/v1/auth/login (Next.js proxy)
   ↓
3. Proxy → Backend /v1/auth/login
   ↓
4. Backend sets mr_token cookie (HTTP-only, secure)
   ↓
5. Cookie forwarded via proxy routes for authenticated requests
```

### **Stripe Integration Flow**
```
1. User clicks "Upgrade to Pro" on /account/plan
   ↓
2. Frontend → /api/proxy/v1/billing/checkout
   ↓
3. Backend creates Stripe Checkout Session
   ↓
4. User redirected to Stripe → completes payment
   ↓
5. Stripe webhook → /v1/webhooks/stripe
   ↓
6. Backend updates accounts.plan_slug = 'pro'
   ↓
7. Usage enforcement respects new plan limits
```

---

## 🔧 Configuration

### **Render (API) Environment Variables**
```bash
DATABASE_URL=<postgres connection string>
JWT_SECRET=mr-prod-jwt-secret-2024-reportscompany-secure
ALLOWED_ORIGINS=["http://localhost:3000","https://reportscompany-web.vercel.app","https://reportscompany-web-*.vercel.app"]
STRIPE_SECRET_KEY=sk_test_...
STRIPE_WEBHOOK_SECRET=whsec_...
STRIPE_PRICE_PRO_MONTH=price_1STMtBBKYbtiKxfswkmFEPeR
STRIPE_PRICE_TEAM_MONTH=price_1STMtfBKYbtiKxfsqQ4r29Cw
WEB_BASE=https://reportscompany-web.vercel.app
```

### **Vercel (Frontend) Environment Variables**
```bash
NEXT_PUBLIC_API_BASE=https://reportscompany.onrender.com
```

---

## 📊 Database Schema (Key Tables)

### **accounts**
```sql
- id (uuid, PK)
- name (text)
- account_type (enum: REGULAR, INDUSTRY_AFFILIATE)
- plan_slug (text: free, pro, team, sponsored_free)
- monthly_report_limit_override (int, nullable)
- stripe_customer_id (text, nullable)
- sponsor_account_id (uuid, nullable, FK to accounts)
- logo_url (text, nullable)
```

### **users**
```sql
- id (uuid, PK)
- email (text, unique)
- password_hash (text)
- is_active (boolean)
```

### **account_users**
```sql
- account_id (uuid, FK to accounts)
- user_id (uuid, FK to users)
- role (enum: OWNER, MEMBER)
```

### **plans**
```sql
- plan_slug (text, PK)
- plan_name (text)
- monthly_report_limit (int)
- allow_overage (boolean)
```

### **reports**
```sql
- id (uuid, PK)
- account_id (uuid, FK to accounts)
- created_at (timestamptz)
- report_data (jsonb)
```

---

## 🧪 Testing

### **Test Credentials**
See `docs/TEST_CREDENTIALS.md`

### **Test Matrix**
See `docs/TEST_MATRIX_V1.md` for comprehensive test cases covering:
- Authentication (AUTH-01 to AUTH-03)
- Schedules (SCHED-01 to SCHED-04)
- Data & Reports (DATA-01 to DATA-06)
- Plans & Usage (PLAN-01 to PLAN-04)
- Affiliates (AFF-01 to AFF-04)
- Branding (BRAND-01 to BRAND-03)
- Stripe (STR-01 to STR-05)

### **Latest Test Results (November 14, 2025)**
| Test | Status | Notes |
|------|--------|-------|
| AUTH-01: Login | ✅ PASS | Cookie-based auth working |
| PLAN-04: Plan & Usage UI | ✅ PASS | Displays correctly |
| STR-02: Stripe Checkout | ✅ PASS | Redirects to Stripe successfully |

---

## 🐛 Known Issues / Tech Debt

### **Minor Issues**
1. Stripe cancel URL has wrong path (`/app/account/plan` should be `/account/plan`)
   - **Impact:** Low - just a redirect URL
   - **Fix:** Update success/cancel URLs in `apps/api/src/api/routes/billing.py`

2. Diagnostic logging still active in production
   - **Impact:** Low - slightly verbose logs
   - **Fix:** Remove debug logging from `authn.py`, `auth.py`

### **Future Enhancements**
1. Add Stripe webhook signature verification test
2. Add test for subscription cancellation flow
3. Implement usage overage billing
4. Add metrics dashboard for affiliates

---

## 📁 Key Files

### **Backend (FastAPI)**
```
apps/api/src/api/
├── routes/
│   ├── auth.py              # Login, invite acceptance
│   ├── billing.py           # Stripe checkout, portal
│   ├── stripe_webhook.py    # Webhook handler
│   ├── account.py           # Account management, plan-usage
│   └── affiliate.py         # Affiliate management
├── middleware/
│   ├── authn.py            # Authentication (JWT + cookie)
│   └── rls.py              # Row-level security
├── config/
│   └── billing.py          # Stripe configuration
└── settings.py             # App settings
```

### **Frontend (Next.js)**
```
apps/web/
├── app/
│   ├── login/page.tsx                # Login page
│   ├── account/plan/page.tsx         # Plan & Usage page
│   ├── affiliate/page.tsx            # Affiliate dashboard
│   └── api/proxy/v1/                 # API proxy routes
│       ├── auth/login/route.ts       # Login proxy
│       ├── account/plan-usage/route.ts
│       ├── billing/checkout/route.ts
│       └── billing/portal/route.ts
└── components/
    ├── stripe-billing-actions.tsx    # Upgrade buttons
    └── checkout-status-banner.tsx    # Success/cancel banner
```

---

## 🚀 Next Steps

### **Immediate (Ready to Deploy)**
1. Remove diagnostic logging from production
2. Fix Stripe cancel URL path
3. Run full test suite from `TEST_MATRIX_V1.md`

### **Short-term (1-2 weeks)**
1. Test webhook flow end-to-end (subscription updates)
2. Add Stripe Customer Portal testing
3. Implement usage overage tracking
4. Add billing history page

### **UI V2 Strategy**
- Avoid Tailwind/monorepo trauma
- Consider shadcn/ui component library
- Maintain clean separation of concerns
- Focus on performance and DX

---

## 📚 Documentation

### **Essential Docs** (Keep)
- `docs/PHASE_29D_STRIPE_SETUP.md` - Stripe setup guide
- `docs/TEST_CREDENTIALS.md` - Test user credentials
- `docs/TEST_MATRIX_V1.md` - Comprehensive test matrix
- `RENDER_BUILD_CONFIGURATION.md` - Render build config

### **Reference**
- API docs: `/docs` endpoint on Render
- Stripe dashboard: https://dashboard.stripe.com/test
- Render dashboard: https://dashboard.render.com
- Vercel dashboard: https://vercel.com/dashboard

---

## 🎉 Achievements

### **Phase 29D - November 14, 2025**
After extensive debugging session:
- ✅ Identified root cause: Frontend was setting `mr_token=undefined` 
- ✅ Fixed by: Creating login proxy route + backend Set-Cookie
- ✅ Result: Full authentication flow working end-to-end
- ✅ Stripe integration verified working (checkout session creation)
- ✅ Plan & Usage page loading correctly

**Total debugging time:** ~6 hours  
**Key breakthrough:** Cookie value diagnostic logging revealed `"undefined"` string  
**Solution:** Login proxy route + backend Set-Cookie header

---

## 💡 Lessons Learned

1. **Cross-origin cookies are hard** - Always use same-origin proxy routes for `Set-Cookie` to work
2. **Debug with data, not assumptions** - Logging actual cookie values revealed the `"undefined"` bug
3. **Test incrementally** - Each fix was deployed and verified before moving on
4. **JWT secrets matter** - Ensure production secrets are set correctly on all services
5. **Proxy pattern works** - Using Next.js API routes as proxies solves CORS + cookie issues elegantly

---

**Status:** 🟢 Production Ready  
**Next Review:** After full test suite execution

---

# 🎯 NEXT PHASES: Testing Stack + Auth Contract + White-Label Branding

**Added:** November 14, 2025  
**Purpose:** Comprehensive specification for automated testing, auth documentation, and affiliate white-label branding

---

## 🌐 GLOBAL CONSTRAINTS (APPLY TO ALL PHASES)

### **Cursor – Read This First**

1. **Do not change business logic unless explicitly instructed:**
   - Auth flows, plan limits, affiliate relationships, invite flows, Stripe logic, templates are assumed correct and deployed

2. **Do not commit secrets:**
   - API keys, DB URLs, Stripe keys, passwords must use environment variables or local `.env` files (ignored by Git)

3. **Do not touch CORS, Render/Vercel env, or monorepo structure** unless spec says so

4. **All new code must:**
   - Live under appropriate app (`apps/api`, `apps/worker`, `apps/web`)
   - Be covered by tests where specified
   - Be wired into CI workflows for automatic testing

---

## PHASE T – TESTING STACK (BACKEND, FRONTEND, E2E, CI)

**Goal:** Fully automated tests that run in CI to detect regressions without manual clicking

### T1 – Backend Tests (pytest)

#### **T1.1 – Add pytest config & deps**

**Location:** Backend environment (covering `apps/api` and `apps/worker`)

**Tasks:**
1. Add dev dependencies:
   - `pytest`
   - `pytest-asyncio`
   - `httpx` (for ASGI TestClient)

2. Create `pytest.ini` at repo root:
```ini
[pytest]
asyncio_mode = auto
python_files = test_*.py
```

3. Ensure `PYTHONPATH` or `conftest.py` allows importing from `apps/api/src` and `apps/worker/src`

#### **T1.2 – Plan & limits tests**

**File:** `apps/api/tests/test_plans_limits.py`

**Import functions from Phase 29A/B:**
- `resolve_plan_for_account`
- `get_monthly_usage`
- `evaluate_report_limit`

**Test fixtures:**
- Free plan: limit 50, `allow_overage=False`
- Pro plan: limit 300, `allow_overage=True`

**Tests:**
- `test_resolve_plan_free_default_limit`
- `test_resolve_plan_with_override`
- `test_evaluate_report_limit_allow` (usage < 80%)
- `test_evaluate_report_limit_warn` (80% ≤ usage < 100%)
- `test_evaluate_report_limit_block` (usage ≥ 100%)

#### **T1.3 – Invite flow tests**

**File:** `apps/api/tests/test_accept_invite.py`

**Use:** FastAPI `TestClient` for `POST /v1/auth/accept-invite`

**Seed data:**
- Users row without password
- Accounts row
- `signup_tokens` row with valid token, future `expires_at`, null `used_at`

**Tests:**
- `test_accept_invite_success`:
  - POST valid `{ token, password }`
  - Assert: 200 OK, `signup_tokens.used_at` set, user password hash updated
- `test_accept_invite_invalid_token` (no matching row)
- `test_accept_invite_expired_token` (`expires_at < now`)
- `test_accept_invite_token_reuse` (`used_at` already set)

#### **T1.4 – Affiliate branding helper tests**

**File:** `apps/api/tests/test_affiliate_branding.py`

**Import:** `get_brand_for_account(db, account_id)` (to be implemented in Phase W1)

**Seed data:**
- REGULAR account with no sponsor
- INDUSTRY_AFFILIATE account with `affiliate_branding` row
- REGULAR account with `sponsor_account_id` pointing to affiliate

**Tests:**
- `test_regular_without_sponsor_uses_trendy_fallback`
- `test_affiliate_uses_own_branding`
- `test_sponsored_regular_uses_affiliate_brand`

---

### T2 – Frontend Unit Tests (Jest + React Testing Library)

#### **T2.1 – Jest setup**

**Location:** `apps/web`

**Tasks:**
1. Add dev dependencies:
```json
"jest", "ts-jest", "@types/jest", 
"@testing-library/react", "@testing-library/jest-dom"
```

2. Create `apps/web/jest.config.ts`:
```typescript
import type { Config } from "jest";

const config: Config = {
  testEnvironment: "jsdom",
  preset: "ts-jest",
  roots: ["<rootDir>/__tests__"],
  moduleNameMapper: {
    "^@/(.*)$": "<rootDir>/$1",
  },
  setupFilesAfterEnv: ["<rootDir>/jest.setup.ts"],
};

export default config;
```

3. Create `apps/web/jest.setup.ts`:
```typescript
import "@testing-library/jest-dom";
```

4. Add script to `apps/web/package.json`:
```json
"scripts": {
  "test": "jest"
}
```

#### **T2.2 – UI component tests**

**Directory:** `apps/web/__tests__/`

**AccountSwitcher.test.tsx:**
- Mock fetch for `/api/proxy/v1/account/accounts`
- Case 1: Single account → only label shown, no dropdown
- Case 2: Multiple accounts → dropdown appears, selecting calls `/api/proxy/v1/account/use`

**PlanPage.test.tsx:**
- Mock fetch for `/api/proxy/v1/account/plan-usage`:
  - `plan_slug="free"`, usage < 80% → green meter, no warning
  - `plan_slug="free"`, usage > 80% → yellow meter + warning
  - `plan_slug="sponsored_free"` → shows "sponsored" badge, no Stripe buttons

**AffiliatePage.test.tsx:**
- Mock `/api/proxy/v1/affiliate/overview`
- Assert summary cards and table render
- Mock 403 → assert "not affiliate" message

#### **T2.3 – Template mapping tests**

**File:** `apps/web/__tests__/TemplatesMapping.test.ts`

**Import:** Mapping functions from `apps/web/lib/templates.ts`

**Provide fake data:**
- `result_json` for each report type
- `brand` for affiliate and fallback

**For each builder, assert:**
- HTML contains correct brand name
- Contains expected metrics (e.g., "Median Price $850,000")
- Contains CSS overrides for brand colors (e.g., `--pct-blue: #123456`)

---

### T3 – E2E Tests (Playwright) Against Staging

#### **T3.1 – Install & configure Playwright**

**Location:** Repo root (or `apps/web`)

**Tasks:**
1. Run `npx playwright install`
2. Create `playwright.config.ts`:
```typescript
import { defineConfig } from "@playwright/test";

export default defineConfig({
  use: {
    baseURL: process.env.E2E_BASE_URL || "https://reportscompany-web.vercel.app",
    trace: "on-first-retry",
    headless: true,
  },
  reporter: [["list"], ["html", { outputFolder: "playwright-report" }]],
});
```

#### **T3.2 – E2E specs**

**Directory:** `e2e/` (at repo root)

**auth.spec.ts:**
- Uses `E2E_REGULAR_EMAIL`, `E2E_REGULAR_PASSWORD` from env
- Steps:
  1. Go to `/login`
  2. Fill login form
  3. Assert redirect to `/app` and see "Dashboard" text

**plan.spec.ts:**
- Log in as REGULAR user
- Go to `/account/plan`
- Assert plan name, usage meter, and upgrade button present

**affiliate.spec.ts:**
- Log in as `E2E_AFFILIATE_EMAIL`
- Go to `/app/affiliate`
- Assert summary cards and table present

**stripe.spec.ts:** (when Stripe fully ready)
- As free user, go to `/account/plan`
- Click "Upgrade to Pro"
- Assert navigation to Stripe checkout (URL contains `checkout.stripe.com`)

---

### T4 – CI Workflows

#### **T4.1 – Backend tests workflow**

**File:** `.github/workflows/backend-tests.yml`

```yaml
name: Backend Tests
on:
  push:
    paths:
      - "apps/api/**"
      - "apps/worker/**"
      - ".github/workflows/backend-tests.yml"
  pull_request:
    paths:
      - "apps/api/**"
      - "apps/worker/**"
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: "3.11"
      - name: Install dependencies
        run: pip install -r requirements.txt
      - name: Run API tests
        run: pytest apps/api/tests
      - name: Run Worker tests
        run: pytest apps/worker/tests
```

#### **T4.2 – Frontend tests workflow**

**File:** `.github/workflows/frontend-tests.yml`

```yaml
name: Frontend Tests
on:
  push:
    paths:
      - "apps/web/**"
      - ".github/workflows/frontend-tests.yml"
  pull_request:
    paths:
      - "apps/web/**"
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
        with:
          node-version: "20"
      - name: Install deps
        run: pnpm install
      - name: Run web tests
        run: pnpm --filter web test
```

#### **T4.3 – E2E workflow**

**File:** `.github/workflows/e2e.yml`

```yaml
name: E2E Tests
on:
  workflow_dispatch:
  push:
    branches: [ "main" ]
jobs:
  e2e:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
        with:
          node-version: "20"
      - name: Install deps
        run: pnpm install
      - name: Install Playwright
        run: npx playwright install --with-deps
      - name: Run E2E tests
        env:
          E2E_BASE_URL: ${{ secrets.E2E_BASE_URL }}
          E2E_REGULAR_EMAIL: ${{ secrets.E2E_REGULAR_EMAIL }}
          E2E_REGULAR_PASSWORD: ${{ secrets.E2E_REGULAR_PASSWORD }}
          E2E_AFFILIATE_EMAIL: ${{ secrets.E2E_AFFILIATE_EMAIL }}
          E2E_AFFILIATE_PASSWORD: ${{ secrets.E2E_AFFILIATE_PASSWORD }}
        run: npx playwright test
```

---

## PHASE A – LOCK THE AUTH CONTRACT (DOCS + TESTS)

**Goal:** Codify what we learned during Phase 29D debugging to prevent regressions

### A1 – AUTH_ARCHITECTURE_V1.md

**File:** `docs/AUTH_ARCHITECTURE_V1.md`

**Content:**

#### **Identity & Tokens**
- `mr_token` is the **only** auth token used by the web app
- It is a JWT issued by `/v1/auth/login` and stored as an **HttpOnly cookie**
- Expires after 1 hour (login) or 7 days (invite acceptance)

#### **Who Owns What**
- **Backend (API)** is the only place that sets or validates `mr_token`
- **Frontend never** writes/overwrites `document.cookie` for `mr_token`
- **Proxy routes** (`apps/web/app/api/proxy/**`) simply forward cookies or translate to `Authorization: Bearer`

#### **Authentication Flow**

**Login:**
```
/login → POST /api/proxy/v1/auth/login 
       → backend /v1/auth/login 
       → Set-Cookie mr_token=<jwt>
```

**Authenticated Requests:**
```
Browser sends mr_token automatically
→ Server-side or proxies read cookie
→ Call API with cookie or Authorization: Bearer
```

**Invite:**
```
Affiliate → invite-agent → signup token created
→ Invited user hits /welcome?token=...
→ POST /v1/auth/accept-invite
→ Sets password + mr_token cookie
```

#### **Verification**
- API uses `set_rls` with:
  - `app.current_account_id`
  - `app.current_user_id`
  - `app.current_user_role`
- Functions like `get_brand_for_account`, `evaluate_report_limit` assume these are set by middleware

### A2 – AUTH_TEST_CHECKLIST.md

**File:** `docs/AUTH_TEST_CHECKLIST.md`

**Content:** Short list of tests that must pass when auth changes:

#### **Unit/Integration:**
- `test_accept_invite_*` all green
- `test_plans_limits_*` all green
- `test_affiliate_branding_*` all green
- `test_result_builders_*` all green

#### **Web Unit:**
- `AccountSwitcher.test.tsx`
- `PlanPage.test.tsx`

#### **E2E:**
- `auth.spec.ts` – login to `/app` works
- `plan.spec.ts` – `/account/plan` works after login
- `affiliate.spec.ts` – `/app/affiliate` works for affiliate
- (Optional) Invite E2E: invite → welcome → `/app`

---

## PHASE W – AFFILIATE WHITE-LABEL BRANDING (EMAILS + PDFs + UI)

**Goal:** Affiliates look like the hero – their logo, colors, contact info. No obvious "TrendyReports" in client-facing surfaces

### W1 – affiliate_branding Table & Helper

#### **W1.1 – Create affiliate_branding table**

**Migration:** `00xx_create_affiliate_branding.sql`

```sql
CREATE TABLE IF NOT EXISTS affiliate_branding (
  account_id uuid PRIMARY KEY
    REFERENCES accounts(id) ON DELETE CASCADE,
  brand_display_name text NOT NULL,
  logo_url text,
  primary_color text,
  accent_color text,
  rep_photo_url text,
  contact_line1 text,
  contact_line2 text,
  website_url text,
  updated_at timestamptz NOT NULL DEFAULT now()
);
```

**Note:** This table is for accounts with `account_type='INDUSTRY_AFFILIATE'`

#### **W1.2 – get_brand_for_account helper**

**File:** `apps/api/src/api/services/branding.py`

**Implementation:**

```python
from typing import TypedDict, Optional

class Brand(TypedDict, total=False):
    display_name: str
    logo_url: Optional[str]
    primary_color: Optional[str]
    accent_color: Optional[str]
    rep_photo_url: Optional[str]
    contact_line1: Optional[str]
    contact_line2: Optional[str]
    website_url: Optional[str]

DEFAULT_PRIMARY = "#7C3AED"
DEFAULT_ACCENT = "#F26B2B"

def get_brand_for_account(db, account_id: str) -> Brand:
    """
    Returns branding for an account:
    - REGULAR with sponsor → use sponsor's branding
    - INDUSTRY_AFFILIATE → use own branding
    - Otherwise → Trendy fallback
    """
    # Load accounts row
    # If account_type='REGULAR' and sponsor_account_id present:
    #   branding_account_id = sponsor_account_id
    # Else:
    #   branding_account_id = account_id
    
    # Try to load affiliate_branding for branding_account_id
    # If found → return that
    # If not:
    #   If branding_account_id is affiliate/sponsor:
    #     Use display_name = accounts.name, no logo, default colors
    #   Else:
    #     Return Trendy fallback:
    #       display_name="TrendyReports"
    #       primary_color=DEFAULT_PRIMARY
    #       accent_color=DEFAULT_ACCENT
```

**Tests:** Covered in T1.4

---

### W2 – Branding API + UI for Affiliates

#### **W2.1 – Branding routes**

**File:** `apps/api/src/api/routes/affiliates.py`

**Add endpoints:**
- `GET /v1/affiliate/branding`
- `POST /v1/affiliate/branding`

**Guards:**
- Ensure current account is `INDUSTRY_AFFILIATE` or return 403

**GET:** Load from `affiliate_branding` or return fallback derived from account

**POST:** Validate payload, upsert into `affiliate_branding`, return updated branding

#### **W2.2 – Proxy route & UI**

**File:** `apps/web/app/api/proxy/v1/affiliate/branding/route.ts`
- Forward GET/POST to `/v1/affiliate/branding`

**File:** `apps/web/app/affiliate/branding/page.tsx`
- Load branding via proxy
- Render form with:
  - Display name
  - Logo URL
  - Primary/accent colors (color pickers)
  - Rep photo URL
  - Contact lines
  - Website URL
- Submit to proxy via POST
- Show live preview card with logo, name, and colored header

**Navigation:** Add "Branding" link under affiliate section (visible only when `account_type='INDUSTRY_AFFILIATE'`)

---

### W3 – Wire Brand into Emails

#### **W3.1 – Update email templates**

**File:** `apps/worker/src/email/templates.py`

**Update:** `build_schedule_email_html` to accept `brand: Optional[Brand]`

**Use brand in HTML:**
- **Header:**
  - If `brand.logo_url` → show logo
  - Use `brand.display_name` as sender/heading (not "TrendyReports")
- **Colors:**
  - Use `brand.primary_color`/`brand.accent_color` for header bar/CTA
- **Footer:**
  - Show `contact_line1`, `contact_line2`, `website_url`
  - Optional minimal "Powered by TrendyReports" in small muted font
- **Fallback:** If brand is Trendy default, keep current look

#### **W3.2 – Use brand in worker**

**File:** `apps/worker/src/worker/tasks.py`

**When schedule's report is created:**
1. You have `account_id` (owner of schedule)
2. Use DB connection to call `get_brand_for_account(db, account_id)`
3. Pass `brand` to `build_schedule_email_html`

**Note:** For REGULAR accounts with `sponsor_account_id`, this automatically picks sponsor brand

---

### W4 – Wire Brand into PDF Templates

#### **W4.1 – Add brand to report data API**

**File:** `apps/api/src/api/routes/reports.py`

**In:** `GET /v1/reports/{id}/data` or `GET /v1/report-runs/{id}`

**After loading report data:**
1. Call `get_brand_for_account(db, account_id)`
2. Add to response:
```json
{
  "brand": { ...Brand... },
  ...existing fields...
}
```

**Note:** Additive change – do not alter existing fields

#### **W4.2 – Use brand in templates.ts**

**File:** `apps/web/lib/templates.ts`

**Update all `buildXxxHtml(templateHtml, data)` functions:**
1. Read `const brand = data.brand || {}`
2. Derive: `brandName`, `logoUrl`, `primary`, `accent`
3. Inject overrides:
   - Add `<style>` block overriding CSS variables (`--pct-blue`, `--pct-accent`)
   - Replace header placeholders: `{{brand_name}}`, `{{brand_logo_url}}`, `{{brand_tagline}}`

**Update HTML templates** in `apps/web/templates/trendy-*.html`:
- Use placeholders instead of hard-coded values:
  - Header text: `{{brand_name}}`
  - Logo: `src="{{brand_logo_url}}"` with graceful fallback
  - Footer: `{{brand_tagline}}`

#### **W4.3 – Keep /print/[runId] simple**

**File:** `apps/web/app/print/[runId]/page.tsx`

**Ensure it:**
1. Fetches report data via proxy (including `brand`)
2. Passes data to mapping function to get full HTML
3. Renders that HTML as-is

---

## ✅ After These Phases Complete

### **You'll Have:**

1. **Full automated test stack:**
   - Backend tests (pytest)
   - Frontend tests (Jest + RTL)
   - E2E tests (Playwright)
   - CI workflows running on every push

2. **Auth behavior documented and protected:**
   - `docs/AUTH_ARCHITECTURE_V1.md` explains the contract
   - `docs/AUTH_TEST_CHECKLIST.md` lists required tests
   - Tests prevent "mr_token=undefined" saga from repeating

3. **Affiliates with proper white-label branding:**
   - Branding UI for affiliates to manage their appearance
   - Brand fully applied to emails and PDFs
   - Clients see affiliate as hero, not "TrendyReports"

### **Implementation Notes:**

- Give this entire spec to Cursor with: **"Execute the Testing + Auth Contract + White-Label spec exactly as described."**
- Phases are labeled (T1, T2, T3, T4, A1, A2, W1, W2, W3, W4) for tracking
- Each phase has clear deliverables and acceptance criteria
- Minimal room for "tripping" – maximum automation

---

**Status:** 📋 READY TO IMPLEMENT  
**Next Action:** Execute phases in order (T → A → W)


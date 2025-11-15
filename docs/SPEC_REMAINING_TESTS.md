# SPEC 2 – REMAINING TESTS (T2.3 + T3)

**Status:** 🔄 In Progress  
**Last Updated:** November 14, 2025

---

## 🌐 GLOBAL CONSTRAINTS FOR TESTS

### Testing Constraints:
- Do not change production logic to "make tests pass"
- Adjust tests to match correct behavior
- Only fix code if tests reveal real bugs
- Keep tests small, focused, and fast

---

## T2.3 – Template mapping Jest tests

**File:** `apps/web/__tests__/TemplatesMapping.test.ts`

### Implementation:

1. **Import** all `buildXxxHtml` functions from `apps/web/lib/templates.ts`

2. **Create fake data object** for each report type:
   - `result_json` with simple, deterministic metrics (city, counts, prices, bands)
   - `brand` with:
     - `display_name`: "ACME Title"
     - `logo_url`: "https://example.com/logo.png"
     - `primary_color`: "#123456"
     - `accent_color`: "#FF8800"

3. **For each builder:**
   - Call the function and get `html`
   - Assert:
     - html contains "ACME Title" (brand name)
     - html contains "https://example.com/logo.png" in img src
     - html contains "--pct-blue: #123456" and "--pct-accent: #FF8800" in `<style>`
     - html contains at least one known KPI string (e.g., "Closed Sales", "Median Price")

4. **Add one test with missing brand:**
   - Ensure fallback brand name is "TrendyReports" and default colors are used

---

## T3 – E2E Specs (Playwright)

**Assumption:** `playwright.config.ts` and `e2e.yml` exist from previous spec

**Directory:** `e2e/`

---

### T3.1 – Create E2E specs

#### **auth.spec.ts**

**Test: Login works**
- Read `E2E_REGULAR_EMAIL`, `E2E_REGULAR_PASSWORD`
- Navigate to `/login`
- Fill email/password
- Submit and wait for `/app`
- Assert an element in the dashboard (e.g., plan summary or nav link) is visible

---

#### **plan.spec.ts**

**Test: Plan page loads after login**
- Use same regular user
- After login (reuse helper), go to `/account/plan`
- Assert:
  - Text like "Plan & Usage" appears
  - A meter or usage text like "/" is present
  - If you know this user is on Free: "Free" appears

---

#### **affiliate.spec.ts**

**Test 1: Affiliate dashboard loads**
- Use `E2E_AFFILIATE_EMAIL` / `E2E_AFFILIATE_PASSWORD`
- After login, go to `/app/affiliate`
- Assert:
  - "Sponsored accounts" count visible
  - Table of sponsored accounts visible (at least header row)

**Test 2: Branding page renders**
- Go to `/app/affiliate/branding`
- Assert the form renders

---

#### **stripe.spec.ts** (Optional now, or later)

**Test: Stripe checkout redirect**
- As a Free user:
  - Go to `/account/plan`
  - Click "Upgrade to Pro"
  - Assert navigation to `https://checkout.stripe.com/` (test mode)
- This doesn't need to complete payment; just confirm checkout loads

---

## Benefits

Once these tests are in place and CI workflows are configured, any regression in:
- Branding
- Auth
- Plan usage
- Affiliate flows

Will be caught **automatically** — and you can stay in planner mode instead of "click-everything" mode.

---

**Status:** Ready to implement  
**Dependencies:** Playwright installed, test credentials configured


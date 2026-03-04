# TrendyReports — Enhancement Implementation Plan for Cursor

> **Date:** February 26, 2026
> **Target:** Cursor AI implementation
> **Strategy:** 6 isolated phases, each a standalone PR with zero cross-phase dependencies
> **Rule:** Every phase must pass existing tests before moving to the next

---

## ⚠️ CRITICAL RULES FOR CURSOR

1. **Read before writing.** Before touching ANY file, read the entire file first. Understand imports, patterns, and existing conventions.
2. **Follow existing patterns EXACTLY.** This codebase has specific conventions — use them. Don't introduce new patterns.
3. **Never modify test files until the code change is complete.** Tests are your validation — don't co-evolve them.
4. **Run tests after every file change:** `pytest tests/test_property_templates.py -v` (from repo root)
5. **Git commit after each sub-task within a phase.** Small, reversible commits.
6. **If a file import fails, STOP.** Read the file, understand the module structure, then try again. Don't guess.
7. **Every phase is a separate git branch** off `main`. Name: `enhance/phase-{N}-{short-name}`

---

## Phase 1: Connection Pooling (THE #1 PERFORMANCE WIN)

> **Branch:** `enhance/phase-1-connection-pool`
> **Risk:** HIGH — touches every DB call path
> **Estimated impact:** 60-80% reduction in API response times
> **Files changed:** 3 files modified, 0 files created

### Context

Currently, `db.py` opens a brand new TCP+TLS PostgreSQL connection on every call to `db_conn()`. On Render's infrastructure, each connection costs 100-300ms. The middleware alone opens 3-5 connections per request (JWT blacklist check, API key lookup, user info fetch, rate limit lookup). This means every single API request has 300-1500ms of pure connection overhead before any business logic runs.

### Step 1.1 — Install psycopg_pool

**File:** `apps/api/pyproject.toml`

Add `psycopg-pool` to dependencies. The version should be compatible with psycopg 3.2.1 (already installed).

```bash
cd apps/api
poetry add psycopg-pool
```

### Step 1.2 — Replace db_conn() with pooled connections

**File:** `apps/api/src/api/db.py`

**READ THE ENTIRE FILE FIRST.** Current implementation (approximately):

```python
# CURRENT (line ~8-15)
@contextmanager
def db_conn():
    with psycopg.connect(settings.DATABASE_URL, autocommit=False) as conn:
        with conn.cursor() as cur:
            yield conn, cur
        conn.commit()
```

**Replace with:**

```python
import psycopg_pool
from contextlib import contextmanager

# Module-level pool — initialized once at import time
_pool = None

def get_pool():
    """Lazy-initialize the connection pool."""
    global _pool
    if _pool is None:
        _pool = psycopg_pool.ConnectionPool(
            conninfo=settings.DATABASE_URL,
            min_size=2,       # Keep 2 connections warm
            max_size=10,      # Max 10 concurrent connections
            max_idle=300,     # Close idle connections after 5 min
            max_lifetime=3600, # Recycle connections after 1 hour
            timeout=10,       # Wait max 10s for a connection
        )
    return _pool

@contextmanager
def db_conn():
    """Get a connection from the pool. Commits on success, rolls back on exception."""
    pool = get_pool()
    with pool.connection() as conn:
        conn.autocommit = False
        with conn.cursor() as cur:
            yield conn, cur
        conn.commit()
```

**CRITICAL — Keep the exact same `yield conn, cur` signature.** Every caller in the codebase does `with db_conn() as (conn, cur):` — this must not change.

**Also keep `set_rls()` and `fetchone_dict()` / `fetchall_dicts()` completely untouched.** They don't interact with connection creation.

### Step 1.3 — Replace raw connections in middleware

**File:** `apps/api/src/api/middleware/authn.py`

**READ THE ENTIRE FILE FIRST.** This file has 3-5 places where it does `psycopg.connect(settings.DATABASE_URL)` directly, bypassing `db_conn()`.

**Search for all occurrences of:**
```python
psycopg.connect(settings.DATABASE_URL)
```

**Replace each one with:**
```python
from api.db import db_conn

# Instead of:
# conn = psycopg.connect(settings.DATABASE_URL)
# cur = conn.cursor()
# cur.execute(...)
# conn.close()

# Use:
with db_conn() as (conn, cur):
    cur.execute(...)
```

**There are approximately 5 places to fix (lines ~68, ~88, ~108, ~147, ~187).** Each one:
1. Opens a raw connection
2. Creates a cursor
3. Runs a query
4. Closes the connection

Replace each block with the `db_conn()` context manager. The query and result handling stay identical — only the connection acquisition changes.

**IMPORTANT:** The middleware currently does `conn.close()` in finally blocks. With the pool, the context manager handles this. Remove explicit `conn.close()` calls — they would return the connection to the pool prematurely.

### Step 1.4 — Add pool shutdown on app shutdown

**File:** `apps/api/src/api/main.py`

Add a shutdown event handler so the pool closes cleanly when the API process stops:

```python
from api.db import get_pool

@app.on_event("shutdown")
async def shutdown_pool():
    pool = get_pool()
    if pool:
        pool.close()
```

**Place this AFTER the existing middleware registration, BEFORE the router includes.** Read the file to find the right location.

### Step 1.5 — Verify

```bash
# Run existing tests
pytest tests/test_property_templates.py -v

# Start the API locally and hit health check
cd apps/api && uvicorn src.api.main:app --reload --port 10000
curl http://localhost:10000/health
```

### Ripple Effects & Warnings

- **DO NOT** change the `db_conn()` return signature. Every route in `routes/*.py` uses `with db_conn() as (conn, cur):`.
- **DO NOT** change `set_rls()`. It receives `cur` from the caller and that's fine.
- **DO NOT** touch the worker service. It has its own DB access patterns.
- The pool is process-local. Each Uvicorn worker gets its own pool. This is correct for Render.
- If `psycopg-pool` fails to install, check that `psycopg[binary]` is installed (it should be from psycopg 3.2.1).

---

## Phase 2: Redis Caching for Stripe + Rate Limiting

> **Branch:** `enhance/phase-2-redis-caching`
> **Risk:** LOW — additive changes, no existing behavior modified
> **Estimated impact:** Eliminates 800-2000ms Stripe overhead + 100-300ms rate limit overhead per request
> **Files changed:** 3 files modified, 1 file created

### Context

Every page load that checks plan usage triggers 4 live Stripe `Price.retrieve()` calls (one per plan). Stripe API calls take 200-500ms each. Additionally, the rate limiter opens a raw DB connection per request to look up the account's rate limit — another 100-300ms.

### Step 2.1 — Create a Redis cache utility for the API service

**File (NEW):** `apps/api/src/api/cache.py`

```python
"""
Redis cache utility for the API service.
Uses the same Redis instance as Celery (REDIS_URL env var).
"""
import json
import redis
from api.settings import Settings

settings = Settings()

_redis_client = None

def get_redis():
    """Lazy-initialize Redis client."""
    global _redis_client
    if _redis_client is None:
        _redis_client = redis.from_url(
            settings.REDIS_URL,
            decode_responses=True,
            socket_connect_timeout=2,
            socket_timeout=2,
        )
    return _redis_client

def cache_get(key: str):
    """Get a cached value. Returns None if missing or Redis is down."""
    try:
        val = get_redis().get(key)
        if val is not None:
            return json.loads(val)
    except Exception:
        pass  # Cache miss — not critical
    return None

def cache_set(key: str, value, ttl_seconds: int = 3600):
    """Set a cached value with TTL. Silently fails if Redis is down."""
    try:
        get_redis().setex(key, ttl_seconds, json.dumps(value, default=str))
    except Exception:
        pass  # Cache write failure — not critical
```

### Step 2.2 — Cache Stripe plan catalog

**File:** `apps/api/src/api/services/plans.py`

**READ THE ENTIRE FILE FIRST.** Find the `get_plan_catalog(cur)` function (around line 46-119). It:
1. Queries all plans from DB
2. For each plan with a `stripe_price_id`, calls `stripe.Price.retrieve()`
3. Returns a dict keyed by plan_slug

**Wrap the function with caching:**

```python
from api.cache import cache_get, cache_set

PLAN_CATALOG_CACHE_KEY = "api:plan_catalog"
PLAN_CATALOG_TTL = 86400  # 24 hours — Stripe prices rarely change

def get_plan_catalog(cur):
    # Try cache first
    cached = cache_get(PLAN_CATALOG_CACHE_KEY)
    if cached is not None:
        return cached

    # --- existing implementation unchanged ---
    # (all the DB queries and Stripe calls)
    # ...
    result = { ... }  # whatever the function currently returns

    # Cache the result
    cache_set(PLAN_CATALOG_CACHE_KEY, result, PLAN_CATALOG_TTL)
    return result
```

**DO NOT change the function signature.** It still takes `cur` and returns the same dict. Callers are unaffected.

**DO NOT change `get_plan_info(cur, plan_slug)`** — it calls `get_plan_catalog()` which will now be cached. It benefits automatically.

### Step 2.3 — Cache rate limit lookups

**File:** `apps/api/src/api/middleware/authn.py`

Find the `RateLimitMiddleware` class (around line 166-221). It currently opens a raw DB connection to fetch `api_rate_limit` from the accounts table on every request.

**Replace the DB lookup with a Redis-cached lookup:**

```python
from api.cache import cache_get, cache_set

# Inside RateLimitMiddleware, in the method that fetches rate limit:
# Find the block that does:
#   conn = psycopg.connect(...)
#   cur.execute("SELECT api_rate_limit FROM accounts WHERE id = %s", ...)
#   rate_limit = cur.fetchone()
#   conn.close()

# Replace with:
cache_key = f"api:rate_limit:{account_id}"
rate_limit = cache_get(cache_key)
if rate_limit is None:
    # Fall back to DB lookup (using the pool from Phase 1)
    with db_conn() as (conn, cur):
        cur.execute("SELECT api_rate_limit FROM accounts WHERE id = %s", (account_id,))
        row = cur.fetchone()
        rate_limit = row[0] if row else 60  # default 60 RPM
    cache_set(cache_key, rate_limit, 300)  # Cache for 5 minutes
```

### Step 2.4 — Verify

```bash
pytest tests/test_property_templates.py -v
cd apps/api && uvicorn src.api.main:app --reload --port 10000
# Hit plan-usage endpoint — first call should be slow, second should be <50ms
curl http://localhost:10000/v1/account/plan-usage -H "Authorization: Bearer $TOKEN"
```

### Ripple Effects & Warnings

- **Redis must be running.** The cache silently falls through on Redis failure — no breakage, just no caching.
- **DO NOT** modify the `get_plan_catalog` return structure. Callers depend on the exact dict shape.
- **Cache invalidation:** If someone changes Stripe prices, they need to wait up to 24h OR you can add a manual cache-clear admin endpoint later. This is fine for now.
- **The rate limit cache uses account_id as key.** If an account's rate limit is changed in the DB, it takes up to 5 minutes to take effect. This is acceptable.

---

## Phase 3: Fix Middleware Ordering + Deduplicate Calls

> **Branch:** `enhance/phase-3-middleware-fix`
> **Risk:** MEDIUM — changes request processing order
> **Estimated impact:** Enables rate limiting (currently disabled), eliminates duplicate DB queries
> **Files changed:** 3 files modified

### Context

Starlette processes middleware in LIFO order (last added = first executed). Currently:
1. `AuthContextMiddleware` is added FIRST (line 54) → runs LAST
2. `RateLimitMiddleware` is added SECOND (line 55) → runs SECOND
3. `RLSContextMiddleware` is added THIRD (line 58) → runs FIRST

This means `RateLimitMiddleware` runs BEFORE `AuthContextMiddleware` sets `account_id`, so rate limiting is a no-op. Also, `RLSContextMiddleware` is redundant — it only sets the demo header, which `AuthContextMiddleware` already handles.

### Step 3.1 — Fix middleware registration order

**File:** `apps/api/src/api/main.py`

**READ THE FILE.** Find the middleware registration block (around lines 54-58).

**Change the order to:**

```python
# Starlette processes middleware LIFO — last added runs first.
# Correct order: Auth first (outermost), then rate limit, then RLS.
app.add_middleware(RLSContextMiddleware)      # Runs LAST  (innermost)
app.add_middleware(RateLimitMiddleware)        # Runs SECOND
app.add_middleware(AuthContextMiddleware)      # Runs FIRST (outermost)
```

This ensures:
1. `AuthContextMiddleware` runs first → sets `request.state.account_id`
2. `RateLimitMiddleware` runs second → can now read `account_id` for rate limiting
3. `RLSContextMiddleware` runs last → sets DB context

### Step 3.2 — Remove redundant RLSContextMiddleware (optional, safe)

**File:** `apps/api/src/api/middleware/rls.py`

**READ IT.** The `RLSContextMiddleware` (line 6-19) only does ONE thing: sets `request.state.account_id` from the `X-Demo-Account` header. But `AuthContextMiddleware` already does this at lines 126-129.

**Option A (safer):** Leave it in place. It's redundant but harmless.
**Option B (cleaner):** Remove the `RLSContextMiddleware` class entirely and remove it from `main.py`. The demo header handling in `AuthContextMiddleware` covers the same functionality.

**If you choose Option B**, also remove the import in `main.py`:
```python
# Remove this line:
from api.middleware.rls import RLSContextMiddleware
# And remove:
app.add_middleware(RLSContextMiddleware)
```

### Step 3.3 — Fix duplicate plan/usage calls in account route

**File:** `apps/api/src/api/routes/account.py`

**READ THE FILE.** Find the `GET /v1/account/plan-usage` endpoint (around line 376-382). Currently it:
1. Calls `resolve_plan_for_account(cur, account_id)` — 1 query
2. Calls `get_monthly_usage(cur, account_id)` — 2 queries
3. Calls `evaluate_report_limit(cur, account_id)` — which internally calls BOTH of the above again

**Fix: Call `evaluate_report_limit()` ONCE and extract everything from its result:**

```python
@router.get("/v1/account/plan-usage")
async def get_plan_usage(request: Request):
    account_id = require_account_id(request)
    with db_conn() as (conn, cur):
        set_rls(cur, account_id)

        # Single call — evaluate_report_limit already computes plan + usage internally
        decision, info = evaluate_report_limit(cur, account_id)

        # Extract what we need from the info dict
        # (read evaluate_report_limit to see what info contains)
        plan = info.get("plan", {})
        usage = info.get("usage", {})

        # Get plan catalog (now cached via Phase 2)
        catalog = get_plan_catalog(cur)

        return {
            "plan": plan,
            "usage": usage,
            "limit_decision": decision.value if hasattr(decision, 'value') else str(decision),
            "catalog": catalog,
        }
```

**IMPORTANT:** Read `evaluate_report_limit()` in `services/usage.py` (around line 154-242) to understand the exact structure of the `info` dict it returns. Match the response structure to what the frontend currently expects. The frontend (`usePlanUsage` hook) depends on specific field names.

### Step 3.4 — Fix duplicate affiliate overview calls

**File:** `apps/api/src/api/routes/affiliates.py`

**READ THE FILE.** Find `GET /v1/affiliate/overview` (around line 30-74). It currently:
1. Calls `verify_affiliate_account(cur, account_id)` — 1 query
2. Calls `get_affiliate_overview(cur, account_id)` — which internally calls `get_sponsored_accounts()` — N+1 queries
3. Calls `get_sponsored_accounts(cur, account_id)` AGAIN — another N+1 queries
4. Queries account info — 1 more query

**Fix: Call `get_sponsored_accounts()` once and derive overview metrics locally:**

```python
@router.get("/v1/affiliate/overview")
async def get_affiliate_overview(request: Request):
    account_id = require_account_id(request)
    with db_conn() as (conn, cur):
        set_rls(cur, account_id)

        # Verify affiliate status (single query)
        verify_affiliate_account(cur, account_id)

        # Fetch sponsored accounts ONCE
        accounts = get_sponsored_accounts(cur, account_id)

        # Derive overview metrics locally (instead of calling get_affiliate_overview)
        overview = {
            "total_sponsored": len(accounts),
            "total_reports": sum(a.get("reports_this_month", 0) for a in accounts),
            "accounts": accounts,
        }

        # Account info (keep the existing query for this)
        cur.execute("SELECT name, account_type FROM accounts WHERE id = %s", (account_id,))
        acct = fetchone_dict(cur)

        return {
            "overview": overview,
            "account": acct,
        }
```

**READ `get_affiliate_overview()` in `services/affiliates.py` to verify the overview dict structure matches what it currently returns.** The frontend depends on specific field names.

### Step 3.5 — Fix N+1 in get_sponsored_accounts

**File:** `apps/api/src/api/services/affiliates.py`

**READ THE FILE.** Find `get_sponsored_accounts()` (around line 10-80). It:
1. Runs a main query to get all sponsored accounts
2. Then loops and runs a per-account query for group memberships

**Replace the loop with a batch query:**

```python
def get_sponsored_accounts(cur, affiliate_account_id):
    # Main query — get all sponsored accounts (KEEP THIS UNCHANGED)
    cur.execute("""
        SELECT ... FROM accounts ...
        WHERE sponsor_account_id = %s
    """, (affiliate_account_id,))
    accounts = fetchall_dicts(cur)

    if not accounts:
        return accounts

    # BATCH query for group memberships (replaces the N+1 loop)
    account_ids = [a["account_id"] for a in accounts]  # or whatever the key is
    cur.execute("""
        SELECT cgm.member_id, cg.id, cg.name
        FROM contact_group_members cgm
        JOIN contact_groups cg ON cgm.group_id = cg.id
        WHERE cgm.member_type = 'sponsored_agent'
        AND cgm.member_id = ANY(%s)
    """, (account_ids,))
    group_rows = fetchall_dicts(cur)

    # Build a lookup: member_id -> list of groups
    groups_by_member = {}
    for row in group_rows:
        mid = row["member_id"]  # adjust field name to match
        if mid not in groups_by_member:
            groups_by_member[mid] = []
        groups_by_member[mid].append({"id": row["id"], "name": row["name"]})

    # Attach groups to accounts
    for acct in accounts:
        acct["groups"] = groups_by_member.get(acct["account_id"], [])  # adjust key

    return accounts
```

**READ the existing function to get the exact column names and dict keys.** The above is a template — the actual column names may differ.

### Ripple Effects & Warnings

- **Middleware order change:** If any middleware depends on state set by another middleware, this could break. Read all 3 middleware classes to verify the dependency chain.
- **Account plan-usage response:** The frontend `usePlanUsage` hook (in `apps/web/lib/hooks/use-plan-usage.ts`) parses the response. **Read this hook** to make sure the response structure matches.
- **Affiliate overview response:** The affiliate dashboard component depends on the response shape. Read `apps/web/app/app/affiliate/page.tsx` to verify.
- **The N+1 fix uses `ANY(%s)` with psycopg.** psycopg 3 handles list-to-array conversion automatically, but verify it works with your driver version.

---

## Phase 4: PDF Engine Margin Normalization

> **Branch:** `enhance/phase-4-pdf-margins`
> **Risk:** MEDIUM — affects all generated PDFs
> **Estimated impact:** Identical PDF output between local dev and production
> **Files changed:** 2 files modified

### Context

Playwright (local dev) adds 0.5in margins via its API, which overrides CSS `@page` rules. PDFShift (production) uses 0 margins and lets CSS handle everything. This means templates look different locally vs production. The fix is to set both engines to 0 margins and let CSS handle all spacing.

### Step 4.1 — Change Playwright margins to 0

**File:** `apps/worker/src/worker/pdf_engine.py`

**READ THE ENTIRE FILE.** Find the Playwright render function (the one that calls `page.pdf()`). It currently has:

```python
page.pdf(
    format="Letter",
    print_background=True,
    margin={"top": "0.5in", "right": "0.5in", "bottom": "0.5in", "left": "0.5in"}
)
```

**Change to:**

```python
page.pdf(
    format="Letter",
    print_background=True,
    margin={"top": "0", "right": "0", "bottom": "0", "left": "0"}
)
```

### Step 4.2 — Standardize --pad across all themes

**File:** `apps/worker/src/worker/templates/property/_base/base.jinja2`

**READ THE ENTIRE FILE.** Find the CSS `:root` block where `--pad` is defined. It should be set to a single consistent value.

**Set:**
```css
:root {
    --page-w: 8.5in;
    --page-h: 11in;
    --pad: 0.5in;
}
```

**Then search ALL 5 theme files** for any override of `--pad`:
- `apps/worker/src/worker/templates/property/bold/bold.jinja2`
- `apps/worker/src/worker/templates/property/classic/classic.jinja2`
- `apps/worker/src/worker/templates/property/elegant/elegant.jinja2`
- `apps/worker/src/worker/templates/property/modern/modern.jinja2`
- `apps/worker/src/worker/templates/property/teal/teal.jinja2`

**If any theme overrides `--pad` to a different value (e.g., 0.6in), change it to 0.5in.** If themes don't override `--pad`, they inherit from base — no change needed.

**Also search for footer positioning.** Find `bottom:` values in footer CSS across all themes. Standardize to `bottom: 0.4in` everywhere.

### Step 4.3 — Add font loading safety

**File:** `apps/worker/src/worker/templates/property/_base/base.jinja2`

**In the `<head>` section**, add font preconnect hints (BEFORE the Google Fonts `<link>` tags):

```html
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
```

**At the end of the `<body>` (before `</body>`), add a font-loading trigger:**

```html
<!-- Force font load before PDF capture -->
<div style="position:absolute;left:-9999px;opacity:0;font-size:1px;">
  <span style="font-family:'Merriweather'">.</span>
  <span style="font-family:'Source Sans Pro'">.</span>
  <span style="font-family:'Space Grotesk'">.</span>
  <span style="font-family:'DM Sans'">.</span>
  <span style="font-family:'Playfair Display'">.</span>
  <span style="font-family:'Montserrat'">.</span>
  <span style="font-family:'Oswald'">.</span>
</div>
```

### Step 4.4 — Add font.ready wait in Playwright

**File:** `apps/worker/src/worker/pdf_engine.py`

In the Playwright render function, after `page.set_content(html)` or `page.goto(url)`, add:

```python
page.wait_for_load_state("networkidle")
page.evaluate("() => document.fonts.ready")
```

**Place this BEFORE the `page.pdf()` call.**

### Step 4.5 — Verify

```bash
pytest tests/test_property_templates.py -v

# If test harness exists:
cd apps/worker && python scripts/test_template.py --theme all

# Visual check: open the generated HTML in Chrome and compare with the PDF
```

### Ripple Effects & Warnings

- **ALL existing PDFs will look slightly different** after this change because the margin handling changes. This is intentional — the goal is to make them look the same across local and production.
- **The CSS `--pad` is used throughout templates** for content positioning. Changing it from 0.6in to 0.5in on affected themes will shift content slightly inward. Visually inspect all 7 pages.
- **The font loading div is tiny and invisible** — it won't affect layout.
- **`document.fonts.ready`** is a promise that resolves when all fonts are loaded. Playwright's `evaluate()` automatically awaits promises.

---

## Phase 5: Wire Up Live Preview in Property Wizard

> **Branch:** `enhance/phase-5-live-preview`
> **Risk:** LOW — uses existing built infrastructure, just wires it up
> **Estimated impact:** Major UX improvement — agents see real template output before generating
> **Files changed:** 2-3 files modified

### Context

The WIZARD_PREVIEW_AUDIT revealed that a complete live preview system is already built but not connected:
- **Backend:** `POST /v1/property/preview` endpoint exists and works
- **Frontend proxy:** `POST /api/proxy/v1/property/preview` exists and works
- **Component:** `ThemeSelector` in `apps/web/components/property/ThemeSelector.tsx` has full iframe preview with 500ms debounce, fullscreen mode, and per-page thumbnails
- **Active wizard:** `StepTheme` in `apps/web/components/property-wizard/` uses CSS gradient mockups only

The `ThemeSelector` component accepts props that are already available in the wizard state.

### Step 5.1 — Understand the current wizard architecture

**READ THESE FILES IN ORDER:**
1. `apps/web/components/property-wizard/property-wizard.tsx` — the orchestrator
2. `apps/web/components/property-wizard/step-theme.tsx` — the current Step 2 (themes)
3. `apps/web/components/property/ThemeSelector.tsx` — the dormant live preview component
4. `apps/web/lib/property-report-assets.ts` — theme definitions and R2 asset paths

**Understand:**
- What props does `StepTheme` receive from the wizard?
- What props does `ThemeSelector` expect?
- Are they compatible? (According to the audit: yes, they already match)

### Step 5.2 — Wire ThemeSelector into the wizard

**File:** `apps/web/components/property-wizard/step-theme.tsx` (or the wizard orchestrator)

**Option A (Safest — Enhance StepTheme):**

Keep `StepTheme` as the wrapper but add the live preview iframe from `ThemeSelector`:

```tsx
// In step-theme.tsx, import the preview functionality:
import { ThemeSelector } from '@/components/property/ThemeSelector'

// Replace the CSS gradient preview with the ThemeSelector component
// The ThemeSelector already handles:
// - Theme card selection
// - Accent color picker
// - Live iframe preview (calls POST /api/proxy/v1/property/preview)
// - 500ms debounce on theme/color changes
// - Fullscreen preview modal
```

**Option B (Cleaner — Replace StepTheme with ThemeSelector):**

In the wizard orchestrator (`property-wizard.tsx`), replace `<StepTheme>` with `<ThemeSelector>`:

```tsx
// In property-wizard.tsx, find where StepTheme is rendered
// Replace with ThemeSelector, passing the same props

<ThemeSelector
  propertyData={wizardState.propertyData}    // From Step 1
  comparables={wizardState.selectedComps}     // From Step 2
  selectedTheme={wizardState.theme}
  onThemeChange={(theme) => updateWizardState({ theme })}
  accentColor={wizardState.accentColor}
  onColorChange={(color) => updateWizardState({ accentColor: color })}
  selectedPages={wizardState.selectedPages}
  onPagesChange={(pages) => updateWizardState({ selectedPages: pages })}
/>
```

**READ `ThemeSelector.tsx` carefully to confirm the exact prop names and types.** The above is based on the audit's description — actual prop names may vary.

### Step 5.3 — Verify the preview API endpoint works

**Before testing in the browser, verify the backend endpoint:**

```bash
curl -X POST http://localhost:10000/v1/property/preview \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "theme": 4,
    "accent_color": "#34d1c3",
    "property_address": "714 Vine St, La Verne, CA 91750",
    "sitex_data": {"beds": 3, "baths": 2, "sqft": 1450},
    "comparables": []
  }'
```

This should return HTML. If it 404s, the route may not be mounted — check `main.py` router includes.

### Step 5.4 — Verify in browser

```bash
cd apps/web && npm run dev
# Navigate to /app/property/new
# Complete Step 1 (property search)
# Complete Step 2 (select comparables)
# On Step 3, the theme selector should now show a live preview iframe
```

### Ripple Effects & Warnings

- **The preview API call happens on every theme/color change** (debounced 500ms). This means the PropertyReportBuilder renders HTML on each change. It should be fast (<500ms) since it's just Jinja2 rendering, no PDF generation.
- **If the preview endpoint is slow**, it's likely because it renders all 7 pages. The `render_preview()` method on `PropertyReportBuilder` (which limits to cover + property + comparables) exists but isn't called by the API endpoint. Consider updating the API endpoint to use `render_preview()` instead of `render_html()` for better performance.
- **Page selection UI:** If `ThemeSelector` has a different page selection UI than `StepTheme`, the user experience may change. Read both components to compare.
- **The `ThemeSelector` references R2 screenshot URLs** via `getThemeCoverUrl()` and `getPagePreviewUrl()`. These URLs 404 unless screenshots are uploaded. The component has fallback gradients, so it won't break — just won't show screenshots.

---

## Phase 6: Structural Cleanup & Safety Fixes

> **Branch:** `enhance/phase-6-cleanup`
> **Risk:** LOW — isolated fixes with no cross-dependencies
> **Estimated impact:** Security improvement + code quality
> **Files changed:** 5 files modified

### Step 6.1 — Fix SQL injection in set_rls()

**File:** `apps/api/src/api/db.py`

**READ THE FILE.** Find `set_rls()` (around line 18-44). It currently uses f-string interpolation:

```python
cur.execute(f"SET app.current_account_id = '{account_id}'")
```

**Replace with parameterized queries:**

```python
from psycopg import sql

def set_rls(conn_or_cur, account_id, user_id=None, user_role=None):
    # Handle both cursor and (conn, cur) tuple
    if isinstance(conn_or_cur, tuple):
        _, cur = conn_or_cur
    else:
        cur = conn_or_cur

    # Use sql.Literal for safe parameterization of SET commands
    # (SET doesn't support %s placeholders in psycopg)
    cur.execute(
        sql.SQL("SET app.current_account_id = {}").format(sql.Literal(str(account_id)))
    )
    if user_id:
        cur.execute(
            sql.SQL("SET app.current_user_id = {}").format(sql.Literal(str(user_id)))
        )
    if user_role:
        cur.execute(
            sql.SQL("SET app.current_user_role = {}").format(sql.Literal(str(user_role)))
        )
```

**Note:** PostgreSQL's `SET` command doesn't support `%s` parameterized queries. `sql.Literal()` is the correct psycopg way to safely inject values into `SET` statements.

### Step 6.2 — Fix fail-open security in middleware

**File:** `apps/api/src/api/middleware/authn.py`

**Search for bare `except:` or `except Exception:` blocks** that silently swallow errors, especially around:
- JWT blacklist check (around line 77-78)
- API key lookup (around line 117-118)

**Replace silent passes with logged warnings:**

```python
import logging
logger = logging.getLogger(__name__)

# Instead of:
# except Exception:
#     pass

# Use:
except Exception as e:
    logger.warning(f"Auth check failed: {e}", exc_info=True)
    # For security checks, fail CLOSED (deny access):
    return JSONResponse(status_code=401, content={"detail": "Authentication error"})
```

**IMPORTANT:** For the JWT blacklist check specifically, failing closed is correct — if we can't verify a token isn't blacklisted, we should reject it. For non-security checks (like fetching user info for logging), failing open is acceptable.

### Step 6.3 — Remove duplicate route definitions in affiliates

**File:** `apps/api/src/api/routes/affiliates.py`

**READ THE ENTIRE FILE.** According to the audit, there are TWO sets of `GET /branding` and `POST /branding` definitions:
- Phase 30 version (around line 251)
- Phase W2 version (around line 502)

**Identify which version is newer/correct** (look at the code quality and completeness), then **delete the older duplicate**. Usually the later one is the most recent.

### Step 6.4 — Add structured logging

**File:** `apps/api/src/api/services/usage.py`

Find `log_limit_decision()` (around line 245-264). It currently uses `print()`.

**Replace with:**

```python
import logging
logger = logging.getLogger(__name__)

def log_limit_decision(account_id, decision, info):
    logger.info(
        "Plan limit check",
        extra={
            "account_id": str(account_id),
            "decision": str(decision),
            "ratio": info.get("ratio"),
            "usage": info.get("usage"),
        }
    )
```

### Step 6.5 — Remove JWT secret preview from startup

**File:** `apps/api/src/api/settings.py`

**Search for any line that prints/logs the JWT secret** (even partially). According to the audit, the first 10 characters are logged at startup.

**Remove or redact:**

```python
# Instead of:
# print(f"JWT_SECRET: {settings.JWT_SECRET[:10]}...")

# Use:
logger.info("JWT_SECRET configured: %s", "***" if settings.JWT_SECRET else "NOT SET")
```

### Step 6.6 — Add missing database indexes

**Create a migration file:** `db/migrations/043_add_performance_indexes.sql`

```sql
-- Performance indexes identified in architecture audit
-- These are all additive — no existing indexes are modified

-- Monthly usage count (reports.py, usage.py)
CREATE INDEX IF NOT EXISTS idx_report_generations_account_generated
    ON report_generations (account_id, generated_at);

-- Sponsored accounts lookup (affiliates.py)
CREATE INDEX IF NOT EXISTS idx_accounts_sponsor
    ON accounts (sponsor_account_id)
    WHERE sponsor_account_id IS NOT NULL;

-- Group membership batch lookup (affiliates.py)
CREATE INDEX IF NOT EXISTS idx_cgm_member
    ON contact_group_members (member_type, member_id);

-- JWT blacklist check (middleware/authn.py)
CREATE INDEX IF NOT EXISTS idx_jwt_blacklist_hash
    ON jwt_blacklist (token_hash);

-- Schedule usage count (usage.py)
CREATE INDEX IF NOT EXISTS idx_schedule_runs_schedule_created
    ON schedule_runs (schedule_id, created_at);

-- API key auth (middleware/authn.py)
CREATE INDEX IF NOT EXISTS idx_api_keys_hash
    ON api_keys (key_hash);
```

**Run with:**
```bash
python scripts/run_migrations.py
```

### Ripple Effects & Warnings

- **`set_rls()` change:** This function is called in virtually every route. The `sql.Literal()` approach is a drop-in replacement — same behavior, just safe. But TEST THOROUGHLY.
- **Fail-closed auth:** Returning 401 on blacklist check errors could cause false rejections if the DB is temporarily slow. Monitor after deployment.
- **Duplicate route removal:** Read BOTH versions carefully. If any frontend code references a specific response shape from one version, removing the wrong one would break the UI.
- **Indexes:** `CREATE INDEX IF NOT EXISTS` is safe — it won't fail if the index already exists. But large tables may take time to index. Run during low-traffic periods.

---

## Quick Reference — What Changes Where

| File | Phase | Change |
|------|-------|--------|
| `apps/api/pyproject.toml` | 1 | Add `psycopg-pool` dependency |
| `apps/api/src/api/db.py` | 1, 6 | Connection pool + `set_rls()` SQL injection fix |
| `apps/api/src/api/main.py` | 1, 3 | Pool shutdown + middleware order fix |
| `apps/api/src/api/middleware/authn.py` | 1, 2, 3, 6 | Pool connections + cached rate limit + reorder + fail-closed |
| `apps/api/src/api/middleware/rls.py` | 3 | (Optional) Remove redundant middleware |
| `apps/api/src/api/cache.py` | 2 | **NEW** — Redis cache utility |
| `apps/api/src/api/services/plans.py` | 2 | Cache Stripe plan catalog |
| `apps/api/src/api/services/usage.py` | 6 | Structured logging |
| `apps/api/src/api/services/affiliates.py` | 3 | Batch N+1 fix |
| `apps/api/src/api/routes/account.py` | 3 | Deduplicate plan/usage calls |
| `apps/api/src/api/routes/affiliates.py` | 3, 6 | Deduplicate overview + remove duplicate routes |
| `apps/api/src/api/settings.py` | 6 | Remove JWT secret preview |
| `apps/worker/src/worker/pdf_engine.py` | 4 | Playwright margins + font.ready wait |
| `apps/worker/src/worker/templates/property/_base/base.jinja2` | 4 | Standardize `--pad` + font preload |
| `apps/worker/src/worker/templates/property/*/` | 4 | Standardize `--pad` + footer position per theme |
| `apps/web/components/property-wizard/step-theme.tsx` | 5 | Wire live preview |
| `apps/web/components/property-wizard/property-wizard.tsx` | 5 | (Possibly) Import ThemeSelector |
| `db/migrations/043_*.sql` | 6 | **NEW** — Performance indexes |

---

## Execution Order

```
Phase 1 (Connection Pool)     ← Do this first. Highest impact.
    ↓
Phase 2 (Redis Caching)       ← Builds on Phase 1 (middleware uses pool)
    ↓
Phase 3 (Middleware + Dedup)   ← Builds on Phase 1 + 2
    ↓
Phase 4 (PDF Margins)          ← Independent of Phases 1-3
    ↓
Phase 5 (Live Preview)         ← Independent of Phases 1-4
    ↓
Phase 6 (Cleanup)              ← Independent, can run anytime
```

Phases 4, 5, and 6 are independent of each other and can be done in any order after Phase 3.

---

## Testing Checklist

After EACH phase, run:

```bash
# Unit tests
pytest tests/test_property_templates.py -v

# Start API and check health
cd apps/api && uvicorn src.api.main:app --reload --port 10000
curl http://localhost:10000/health

# Check a protected endpoint works
curl http://localhost:10000/v1/me -H "Authorization: Bearer $TOKEN"

# For Phase 4 specifically, generate test PDFs
cd apps/worker && python scripts/generate_all_property_pdfs.py

# For Phase 5, manually test the wizard in the browser
cd apps/web && npm run dev
# Navigate to /app/property/new and go through all 4 steps
```

---

## Rollback Plan

Each phase is a separate branch. If something breaks:

```bash
# Revert to main
git checkout main

# Or revert a specific phase
git revert --no-commit enhance/phase-{N}-{short-name}
```

Since each phase is isolated with its own branch, reverting one phase doesn't affect others.

# Backend Services

> `apps/api/src/api/services/` -- Business logic, SQL queries, integrations

---

## usage.py -- Usage Tracking & Plan Limits

### `get_monthly_usage(cur, account_id, now?)` (line 20-85)
Returns report count + schedule run count for current calendar month.

**Queries:**
- `SELECT COUNT(*) FROM report_generations WHERE account_id = %s AND generated_at >= %s`
- `SELECT COUNT(*) FROM schedule_runs WHERE schedule_id IN (SELECT id FROM schedules WHERE account_id = %s)` -- correlated subquery [M1]

**Returns:** `{ report_count, schedule_run_count, period_start, period_end }`

### `resolve_plan_for_account(cur, account_id)` (line 88-151)
Resolves effective plan with overrides.

**Query:** JOINs `accounts` with `plans` table. Falls back to 'free' plan if none assigned. Applies `monthly_report_limit_override` if set.

**Returns:** `{ plan_slug, plan_name, monthly_report_limit, allow_overage, overage_price_cents, has_override, account_type }`

### `evaluate_report_limit(cur, account_id, now?)` (line 154-242)
Central limit enforcement. Calls `get_monthly_usage()` and `resolve_plan_for_account()` internally.

**Decision logic:**
- `limit <= 0` or `>= 10000` -> `ALLOW` (unlimited)
- `ratio < 0.8` -> `ALLOW`
- `0.8 <= ratio < 1.1` -> `ALLOW_WITH_WARNING`
- `ratio >= 1.1` + no overage -> `BLOCK`
- `ratio >= 1.1` + overage allowed -> `ALLOW_WITH_WARNING`

**Returns:** `(LimitDecision, info_dict)` where info_dict contains usage, plan, ratio, message.

**Known issue:** When called from `/v1/account/plan-usage`, the route also calls `get_monthly_usage()` and `resolve_plan_for_account()` separately, duplicating all queries. See [H1].

### `log_limit_decision(account_id, decision, info)` (line 245-264)
Prints usage decision to stdout. Should use `logging` module.

---

## plans.py -- Plan Catalog & Stripe Pricing (cursor-wire-caching)

### `get_plan_catalog(cur)`

Fetches all active plans from DB, then calls `stripe.Price.retrieve()` for each plan with a `stripe_price_id`.

**Caching (cursor-wire-caching fix):** Wrapped with an in-memory TTL cache:

```python
_plan_cache: Dict | None = None
_plan_cache_time: float = 0
_CACHE_TTL_SECONDS = 3600  # 1 hour
```

- **First call:** DB query + Stripe API × N plans (~1–2 seconds)
- **Cached call:** Returns dict from memory (~0 ms)
- **Cache invalidation:** Call `invalidate_plan_cache()` — hooked into the Stripe webhook handler for `subscription.*`, `price.*`, and `product.*` events

**Returns:** `Dict[str, PlanCatalog]` keyed by `plan_slug`.

### `invalidate_plan_cache()`

Resets `_plan_cache = None` so the next call re-fetches from DB + Stripe. Called by:
- `routes/stripe_webhook.py` after any subscription change
- Admin plan management endpoints (future)

### `get_plan_info(cur, plan_slug)`

Convenience wrapper that calls `get_plan_catalog()` and returns one entry. Benefits from cache automatically.

---

## affiliates.py -- Affiliate Account Management (cursor-enhancement-plan)

### `get_sponsored_accounts(cur, affiliate_account_id)`

Runs exactly **2 queries** regardless of account count (was: 1 + N):
1. Main query: `accounts` JOIN `report_generations` aggregate
2. Batch query: ALL group memberships for all sponsored account IDs in one `ANY(%s::uuid[])` call

### `get_affiliate_overview(cur, affiliate_account_id)`

Lightweight aggregate query (1 query). The overview route calls this once and `get_sponsored_accounts()` once — no duplicate calls.

### `verify_affiliate_account(cur, account_id)`

Simple check: `SELECT account_type FROM accounts WHERE id = %s`, returns `True` if `INDUSTRY_AFFILIATE`.

---

## accounts.py -- Multi-Account Support

### `get_user_accounts(cur, user_id)` (line 10-64)
Returns all accounts for a user via `account_users` join. Ordered by role (OWNER first).

### `get_default_account_for_user(cur, user_id)` (line 67-93)
Returns first OWNER account, or first account in list.

### `verify_user_account_access(cur, user_id, account_id)` (line 96-115)
Checks `account_users` for membership.

### `get_account_info(cur, account_id)` (line 118-150)
Basic account lookup returning id, name, type, plan_slug, sponsor_account_id.

---

---

## simplyrets.py -- API-Layer SimplyRETS Client

> Full module doc: [modules/simplyrets-api-service.md](./modules/simplyrets-api-service.md)

Used by `routes/property.py` to fetch comparable listings during the property report wizard.

### `fetch_properties(params: dict) → list[dict]`

Async HTTP GET to `https://api.simplyrets.com/properties` with Basic Auth.
Returns raw listing objects normalised via `normalize_listing()`.

### `build_comparables_params(subject, options) → dict`

Constructs SimplyRETS query parameters from subject property attributes + user-specified options (`sqft_tolerance`, `radius`, `type`, `subtype`).

### `normalize_listing(raw) → dict`

Maps SimplyRETS API fields to the consistent `PropertyData` shape consumed by the property builder.

**Known behaviour:** No local rate limiter — relies on the 60 RPM SimplyRETS limit. Rapid frontend calls can trigger 429 responses.

---

## sitex.py -- SiteX Pro API Client

> Full module doc: [modules/sitex-api-service.md](./modules/sitex-api-service.md)

Provides subject-property lookup via the SiteX Pro REST API (OAuth2 client credentials). Used as Step 1 of the property report wizard.

### `SiteXClient` (class, singleton)

Manages OAuth2 token lifecycle (10-min TTL, auto-refreshed at 9 min). In-memory 24-hour cache for address and APN lookups.

### `SiteXClient.search_by_address(address, city, state, zip) → PropertyData | None`

Looks up property by street address. Returns `None` if not found; raises `MultiMatchError` if multiple results.

### `SiteXClient.search_by_apn(fips, apn) → PropertyData | None`

Higher-precision lookup using county FIPS + APN.

**Critical output field:** `property_type` (mapped from SiteX `UseCode`) is used by the comparables route to select the correct SimplyRETS `type` + `subtype`.

---

## Other Services

| File | Purpose | Key Functions |
|------|---------|---------------|
| `email.py` | Send emails via Resend | `send_invite_email()`, password reset, notifications |
| `branding.py` | White-label brand resolution | `get_brand_for_account()`, `validate_brand_input()` |
| `property_stats.py` | Property report statistics | Stats at agent/affiliate/admin levels |
| `qr_service.py` | QR code generation | Generate QR codes for report links |
| `twilio_sms.py` | SMS via Twilio | Send SMS notifications |
| `upload.py` | File upload handling | Process and store uploaded files |
| `agent_code.py` | Agent tracking codes | Generate/manage promotional codes |
| `billing_state.py` | Billing state management | Track subscription state |
| `plan_lookup.py` | Plan detail resolution | Resolve plan details from slugs |

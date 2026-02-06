All files have been read and analyzed. Here is the complete audit report.

TrendyReports API Performance Audit Report
CRITICAL (causes 1-5+ second delays per request)
[C1] No connection pooling — every db_conn() opens a new TCP connection
File: apps/api/src/api/db.py:11
Impact: psycopg.connect(settings.DATABASE_URL, autocommit=False) is called for every route handler invocation. On Render's cloud-hosted Postgres (network hop), each TCP + TLS handshake costs 100-300ms. Every single API call pays this cost, and it stacks with the middleware connections below.
Fix: Replace with psycopg_pool.ConnectionPool (from psycopg[pool]). Create a module-level pool on first use or at app startup. db_conn() becomes pool.connection(). The pool manages a warm set of pre-established connections, reducing per-request connection overhead to ~0ms.
[C2] Middleware opens 3-5 raw psycopg.connect() calls per authenticated request
File: apps/api/src/api/middleware/authn.py:68, 88, 108, 147, 187

Impact: Each of these is a separate psycopg.connect() — a brand new TCP+TLS connection to Postgres. A single JWT-authenticated request hits:

Line 68: Blacklist check (1 connection, ~100-300ms)
Line 147: User info/role fetch (1 connection, ~100-300ms)
Line 187: Rate limit — api_rate_limit fetch (1 connection, ~100-300ms)
If JWT fails and falls back to API key auth: line 88 adds another connection. If cookie auth is used instead: line 108 adds the cookie blacklist check.

Worst case: 4-5 connections × 100-300ms = 400-1500ms of pure connection overhead before any route code runs.

Fix: All middleware DB access should go through the same connection pool as db_conn(). Ideally, acquire a single pooled connection at the start of the middleware chain, use it for all lookups (blacklist, user info, rate limit), then release it. This collapses 3-5 connections to 1 pool checkout (~0-5ms).

[C3] get_plan_catalog() calls Stripe API live for every plan on every page load
File: apps/api/src/api/services/plans.py:91-103
Impact: The function queries all active plans, then calls stripe.Price.retrieve(stripe_price_id) per plan in a synchronous loop. With 4 plans, that's 4 sequential HTTP roundtrips to Stripe (each 200-500ms) = 800-2000ms. This function is called by GET /v1/account/plan-usage (apps/api/src/api/routes/account.py:385), which is fetched on every page load.
Additionally: These are synchronous calls. If any FastAPI handler in the app uses async def, Uvicorn runs sync handlers in a threadpool, but the Stripe calls still block that thread for the full duration.
Fix: Cache Stripe price data in Redis with a TTL of 1-24 hours. Stripe prices change extremely rarely. On cache miss, fetch from Stripe and store. Alternatively, store price info directly in the plans table during plan setup/webhook and never call Stripe at runtime.
[C4] Duplicate get_sponsored_accounts() calls — everything runs twice
File: apps/api/src/api/routes/affiliates.py:51-54 and apps/api/src/api/services/affiliates.py:94

Impact: The /v1/affiliate/overview endpoint calls:

get_affiliate_overview(cur, account_id) at line 51, which internally calls get_sponsored_accounts() at services/affiliates.py:94
Then immediately calls get_sponsored_accounts(cur, account_id) again at line 54
The entire sponsored accounts query + N+1 group membership queries (see C5) execute twice. With 20 sponsored accounts, that's 2 × (1 main query + 20 group queries) = 42 queries instead of 21.

Fix: Have get_affiliate_overview() return the sponsored list alongside metrics, or call get_sponsored_accounts() once in the route and derive overview metrics locally:

sponsored = get_sponsored_accounts(cur, account_id)
overview = {
    "sponsored_count": len(sponsored),
    "total_reports_this_month": sum(a["reports_this_month"] for a in sponsored),
}

[C5] N+1 query in get_sponsored_accounts() — per-account group membership loop
File: apps/api/src/api/services/affiliates.py:59-68
Impact: After the main query returns all sponsored accounts, a separate query per account fetches group memberships. With 20 accounts, that's 20 additional queries. Combined with issue C4 (double execution), that's 40 extra queries. Each query requires a DB roundtrip.
Fix: Replace the N+1 loop with a single batch query using WHERE cgm.member_id = ANY(%s) passing all account IDs, then group the results in Python. Or use a lateral join / subquery in the main query.
HIGH (causes 500ms-2 second delays)
[H1] evaluate_report_limit() redundantly re-fetches get_monthly_usage() and resolve_plan_for_account()
File: apps/api/src/api/routes/account.py:376-382 and apps/api/src/api/services/usage.py:182-183

Impact: The /v1/account/plan-usage endpoint at routes/account.py:376-382 calls:

resolve_plan_for_account(cur, account_id) — line 376
get_monthly_usage(cur, account_id) — line 379
evaluate_report_limit(cur, account_id) — line 382, which internally calls both get_monthly_usage() and resolve_plan_for_account() again at usage.py:182-183
Every sub-function runs twice. That's 4 redundant queries (2 for plan resolution, 2 for usage counting). Each query costs ~10-50ms on a cloud DB, so ~40-200ms wasted.

Fix: Call evaluate_report_limit() once, which returns both usage and plan in its info dict. Extract those from the result instead of calling the sub-functions separately. Or refactor evaluate_report_limit() to accept pre-fetched plan/usage data.

[H2] Rate limit middleware queries the database on every request
File: apps/api/src/api/middleware/authn.py:187-192
Impact: RateLimitMiddleware opens a raw psycopg.connect() to fetch api_rate_limit FROM accounts on every single request, including static assets, health checks that pass the account check, etc. This is a fresh TCP connection per request (100-300ms) for a value that essentially never changes during a session.
Fix: Cache the rate limit value in Redis (keyed by account_id) with a 5-minute TTL. Redis is already used by the rate limiter for counting. Alternatively, embed the rate limit in JWT claims so it's available without any DB hit. Fallback to the default (60) if not cached.
[H3] get_plan_info() calls get_plan_catalog() for a single plan — triggers ALL Stripe calls
File: apps/api/src/api/services/plans.py:122-128
Impact: get_plan_info(cur, plan_slug) fetches the entire catalog (all plans, all Stripe API calls) just to return one plan. This is O(n) Stripe calls when only 1 is needed. If there are 4 plans, a single get_plan_info('pro') triggers 4 Stripe roundtrips.
Fix: This becomes a non-issue if C3 is fixed with caching. Alternatively, query a single plan row and fetch only its Stripe price.
[H4] Middleware ordering is inverted — Starlette executes them bottom-to-top
File: apps/api/src/api/main.py:54-58

Impact: Starlette's add_middleware() uses a stack (LIFO). The registration order:

app.add_middleware(AuthContextMiddleware)   # Line 54 — added first
app.add_middleware(RateLimitMiddleware)      # Line 55 — added second
app.add_middleware(RLSContextMiddleware)     # Line 58 — added third

Execution order is reverse: RLSContextMiddleware → RateLimitMiddleware → AuthContextMiddleware.

This means RateLimitMiddleware runs before AuthContextMiddleware sets request.state.account_id. The rate limit middleware checks getattr(request.state, "account_id", None) (line 181), which will always be None at this point, so it skips rate limiting entirely and becomes a no-op pass-through (except it still opens a DB connection on line 187-192 if an account_id somehow exists). The RLSContextMiddleware also runs before auth, so it sets a demo header value that auth might override.

Fix: Reverse the registration order so auth runs first:

app.add_middleware(RLSContextMiddleware)     # runs last
app.add_middleware(RateLimitMiddleware)       # runs after auth
app.add_middleware(AuthContextMiddleware)     # runs first

MEDIUM (causes 100-500ms delays)
[M1] Correlated subquery in get_monthly_usage() schedule runs count
File: apps/api/src/api/services/usage.py:63-72
Impact: The query uses WHERE schedule_id IN (SELECT id FROM schedules WHERE account_id = %s) — a correlated subquery that scans the schedules table for each schedule run evaluation. With many schedules or runs, this degrades.
Fix: Rewrite as a JOIN:
SELECT COUNT(*) FROM schedule_runs sr
JOIN schedules s ON sr.schedule_id = s.id
WHERE s.account_id = %s AND sr.created_at >= %s AND ...

[M2] Error swallowing hides failures and may cause silent retry logic
Files:
apps/api/src/api/middleware/authn.py:77-78 — blacklist check failure silently continues (allows potentially blacklisted tokens through)
apps/api/src/api/middleware/authn.py:117-118 — same for cookie blacklist
apps/api/src/api/services/usage.py:76-78 — schedule_runs query failure silently returns 0
apps/api/src/api/routes/affiliates.py:306, 340, 556-558 — branding query failures silently fall through to legacy queries or defaults
apps/api/src/api/services/plans.py:69-75 — plan catalog query failure silently retries with different column names
Impact: Errors are swallowed with bare except Exception: pass. This masks real issues (connection failures, schema mismatches) and makes debugging extremely difficult. Some of these have security implications — e.g., if the blacklist check DB connection fails, the middleware silently allows the request through.
Fix: Log all exceptions at minimum. For security-critical paths (blacklist checks), fail closed (deny request) rather than fail open.
[M3] set_rls() uses f-string interpolation for SQL values
File: apps/api/src/api/db.py:38, 42, 44
Impact: cur.execute(f"SET LOCAL app.current_account_id TO '{account_id}'") uses f-string interpolation. While account_id comes from auth middleware (not direct user input), this is a SQL injection risk if the auth layer is ever bypassed or produces unexpected values. It also can't benefit from prepared statement caching.
Fix: Use parameterized queries. For SET LOCAL, psycopg3 supports cur.execute(sql.SQL("SET LOCAL app.current_account_id TO {}").format(sql.Literal(account_id))).
[M4] Sponsored account detail endpoint runs 4 separate queries that could be 1
File: apps/api/src/api/routes/affiliates.py:716-759
Impact: GET /affiliate/accounts/{id} runs 4 sequential queries: account info, reports this month, last report date, and total reports. These could all be a single query with subqueries or window functions, saving 3 roundtrips (~30-150ms).
Fix: Combine into one query:
SELECT a.*, 
  (SELECT COUNT(*) FROM reports WHERE account_id = a.id AND created_at >= date_trunc('month', CURRENT_DATE)) AS reports_this_month,
  (SELECT MAX(created_at) FROM reports WHERE account_id = a.id) AS last_report_at,
  (SELECT COUNT(*) FROM reports WHERE account_id = a.id) AS total_reports
FROM accounts a WHERE a.id = %s AND a.sponsor_account_id = %s

[M5] Duplicate route definitions — two GET /v1/affiliate/branding and two POST /v1/affiliate/branding
File: apps/api/src/api/routes/affiliates.py:251-363 (Phase 30) and apps/api/src/api/routes/affiliates.py:502-579 (Phase W2)
Impact: FastAPI will register both, but only one will match (last wins, or first wins depending on version). The dead code adds confusion and the duplicate verification + query logic is wasted effort if it were ever accidentally matched.
Fix: Remove the duplicate route definitions. Keep one version.
LOW (code quality / future risk)
[L1] RLSContextMiddleware is a no-op redundancy
File: apps/api/src/api/middleware/rls.py:1-20 and apps/api/src/api/main.py:58
Impact: This middleware only sets request.state.account_id from an X-Demo-Account header — but AuthContextMiddleware already does this (line 127-129 in authn.py). It adds an extra middleware layer in the ASGI stack for every request with zero value.
Fix: Remove RLSContextMiddleware and its registration in main.py.
[L2] JWT secret preview logged at startup
File: apps/api/src/api/settings.py:35-36
Impact: Logs the first 10 characters of JWT_SECRET on every startup. In cloud environments, these logs are often stored and accessible to operations teams. While partial, it narrows brute-force space.
Fix: Log only the length, or remove the logging entirely.
[L3] CREATE TABLE IF NOT EXISTS in a request handler
File: apps/api/src/api/routes/affiliates.py:162-172
Impact: The invite-agent endpoint runs CREATE TABLE IF NOT EXISTS signup_tokens on every invocation. DDL statements acquire locks and have no place in request handlers. The table should exist via migrations.
Fix: Move to a migration script. Remove the CREATE TABLE from the route handler.
[L4] get_plan_info() fetches entire catalog to return one plan
File: apps/api/src/api/services/plans.py:122-128
Impact: Fetches all plans and all Stripe prices to return a single plan entry. Wasteful but becomes irrelevant once C3 (caching) is fixed.
Fix: Addressed by C3.
[L5] Debug logging on every request for /reports/ paths
File: apps/api/src/api/middleware/authn.py:30-31
Impact: logger.info(f"AUTH_DEBUG: ...") fires on every request whose path contains /reports/. This is debug noise in production logs.
Fix: Remove or downgrade to logger.debug().
DATABASE
Missing Indexes (suspected — verify with \d tablename)
Table	Column(s)	Used By	Why
report_generations	account_id, generated_at	get_monthly_usage(), list reports, sponsored account metrics	Composite index needed for the WHERE account_id = X AND generated_at >= Y pattern used everywhere
report_generations	status	Multiple queries filter status IN ('completed', 'processing')	Partial index on active statuses would help
accounts	sponsor_account_id	get_sponsored_accounts() WHERE sponsor_account_id = X	FK index likely missing
contact_group_members	member_type, member_id	N+1 group membership query in get_sponsored_accounts()	Composite index for the lookup pattern
contact_group_members	account_id	Same query also filters by account_id	May need (member_type, member_id, account_id) composite
jwt_blacklist	token_hash	Middleware blacklist check on every request	Should be indexed; checked on every authenticated request
schedule_runs	schedule_id, created_at	get_monthly_usage() correlated subquery	Composite index for the range scan
schedules	account_id	Subquery in get_monthly_usage()	FK index
api_keys	key_hash	API key auth lookup	Should be unique index
Recommended Schema Changes
Add composite index: CREATE INDEX idx_report_gen_account_date ON report_generations (account_id, generated_at DESC);
Add index: CREATE INDEX idx_accounts_sponsor ON accounts (sponsor_account_id) WHERE sponsor_account_id IS NOT NULL;
Add composite index: CREATE INDEX idx_cgm_member ON contact_group_members (member_type, member_id, account_id);
Add index: CREATE INDEX idx_jwt_blacklist_hash ON jwt_blacklist (token_hash);
Add composite index: CREATE INDEX idx_schedule_runs_schedule_date ON schedule_runs (schedule_id, created_at);
SUMMARY
Overhead per authenticated affiliate page load (worst case):
Source	Overhead
C1: No connection pool (route)	100-300ms
C2: Middleware raw connections ×3	300-900ms
C3: Stripe API calls ×4 (plan-usage)	800-2000ms
C4: Duplicate get_sponsored_accounts()	200-500ms
C5: N+1 group queries ×20 (doubled)	400-1000ms
H1: Duplicate plan/usage calls	40-200ms
H2: Rate limit DB query	100-300ms
Total estimated overhead	~2-5.2 seconds
Expected after fixes:
Source	After Fix
Connection pool	~0-5ms (pool checkout)
Middleware: single pooled conn	~5-15ms (3 queries, 1 connection)
Stripe: cached in Redis	~1-5ms (cache hit)
Single get_sponsored_accounts() call	50% reduction
Batch group query (no N+1)	~10-30ms (1 query)
Single evaluate_report_limit() call	~10-30ms
Rate limit cached in Redis	~1-5ms
Expected total	~30-100ms
Expected improvement: 20-50× faster response times on core endpoints.

Update Todos
 Analyze db.py for connection pooling issues
 Analyze authn.py middleware for raw connections
 Analyze rls.py middleware
 Analyze routes (affiliates, account, reports)
 Analyze services (affiliates, usage, accounts, plans)
 Analyze settings.py and main.py
 Compile structured performance audit report
The report is complete. A few things worth highlighting beyond what you already suspected:

H4 (middleware ordering) is a significant finding — Starlette's LIFO middleware stack means RateLimitMiddleware currently runs before AuthContextMiddleware sets the account_id, so rate limiting is effectively disabled in production. The DB connection it opens on line 187 is entirely wasted.

M5 (duplicate route definitions) — there are two identical GET /branding and two POST /branding routes registered on the same prefix, from Phase 30 and Phase W2. One set is dead code.

M2 (fail-open security) — the blacklist check at lines 77-78 and 117-118 silently allows requests through if the DB connection fails, which means a database hiccup could let logged-out tokens back in.

The highest-impact fix is C1+C2 (connection pooling) because it affects every single request. C3 (Stripe caching) is the single biggest latency source for the plan-usage endpoint specifically.
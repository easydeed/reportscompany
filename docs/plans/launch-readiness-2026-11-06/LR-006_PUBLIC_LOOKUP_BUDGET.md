# LR-006: bound public property searches

Design rev 1, written for design review before code. Builder: Claude. Facts verified at `main` `1eedb22a`.
Jerry's decisions (2026-11-12) are marked **[Jerry]**. The 20-per-visitor amount was approved on November 9.

## 1. What is wrong today

- **The public search has no limit.** `POST /v1/cma/{agent_code}/search` (`routes/lead_pages.py:230`) calls SiteX (`services/sitex.py:826`, `lookup_property`) for anyone. The global limiter only applies to requests that carry an account: `RateLimitMiddleware.dispatch` returns early when `request.state.account_id` is empty (`middleware/authn.py:336`).
- **The API never sees the visitor's address.** The web proxies `app/api/proxy/v1/cma/[code]/search/route.ts` and `/request/route.ts` forward only `Content-Type`, so the API sees Vercel's server as the client. That causes two problems:
  - `/request`'s "5 per IP per hour" check (`lead_pages.py:326–337`) counts per Vercel egress address, so unrelated homeowners share one bucket.
  - `consumer_reports.ip_address`, stored with each consent, holds Vercel's address instead of the visitor's.
- **A spoofable client IP elsewhere.** `routes/leads.py:116–135` takes the *first* `X-Forwarded-For` entry, which any client can set.
- **The API is reachable directly** at `reportscompany.onrender.com`, so anything the web proxy enforces can be bypassed. The limit has to live in the API.
- **How the deployed API sees client addresses is not in the repository.** The deployed uvicorn command, and whether Render's load balancer appends or replaces `X-Forwarded-For`, must be established on the deployment, not assumed (§8, probes P1–P2).
- **The SiteX cache** is an in-process dictionary (`sitex.py:778`). A cached answer costs nothing, but each API process has its own cache.

## 2. Who a visitor is **[Jerry: signed cookie + IP ceiling]**

The visitor key never contains the agent code, so switching agent pages cannot reset a budget.

**Through the web (the normal path).**
1. The Next proxy reads the client address Vercel sets (`x-real-ip`, which Vercel overwrites and does not take from the client). It never reads an incoming `X-Forwarded-For` value as the client.
2. The proxy keeps a first-party `tr_v` cookie: 128 random bits, HMAC-signed with `VISITOR_COOKIE_SECRET`, `HttpOnly; Secure; SameSite=Lax`, 30 days. An absent or invalid cookie is replaced with a new one.
3. The proxy calls the API with:
   - `X-TR-Visitor-IP`: the address;
   - `X-TR-Visitor-Id`: the cookie's random value;
   - `X-TR-Proxy-Ts`: a Unix timestamp;
   - `X-TR-Proxy-Sig`: `HMAC_SHA256(PROXY_SHARED_SECRET, ts + "\n" + method + " " + path + "\n" + ip + "\n" + visitor_id)`.
4. The API trusts those headers only when the signature verifies (constant-time compare) and `ts` is within 60 seconds. Otherwise they are ignored, never trusted.

**Directly to the API (no valid signature).** There is no cookie. The visitor is the client address, taken as follows:
- **If** probe P2 shows Render's load balancer *appends* the connecting address: the last `X-Forwarded-For` hop.
- **Otherwise:** all unsigned callers share one strict `direct` bucket of 20 per hour in total. Attribution fails closed.

**The keys** are `HMAC_SHA256(VISITOR_KEY_SECRET, normalised value)`, truncated to 16 bytes, in hex.
- IPv4 addresses are used as is. IPv6 addresses are grouped by `/64`, which is how one subscriber's devices are usually addressed.
- No raw address or cookie value appears in Redis, logs or error bodies.

## 3. The budgets **[Jerry]**

All counted in Redis, shared across workers, checked before SiteX is called.

| Budget | Limit | Counts | Key |
|---|---|---|---|
| Per visitor | **20 per hour** (Nov 9) | every search request, cached or not ("20 lookups") | `lb:v:{visitor}` |
| Per address | **60 per hour** (the IP ceiling) | every search request from that address, across all cookies | `lb:ip:{address}` |
| Per page | **200 per hour** | SiteX calls only (cache misses) caused through that agent's page | `lb:p:{agent_id}` |
| Global | **1,000 per hour** | SiteX calls only, across all public pages | `lb:g` |

- **Window:** a rolling hour, kept as twelve 5-minute buckets per key with a TTL of 65 minutes. A fixed hour would allow 40 in two minutes across the boundary.
- **One atomic check.** A single Lua script checks the visitor and address budgets, and increments both only if both have room. Refused requests are not counted, so a refused visitor isn't pushed further back.
- **The vendor gate.** After a cache miss, and immediately before SiteX, a second Lua script does the same for the page and global budgets. A request refused there has already used one of its visitor lookups, which is honest: it searched.
- **Refusals:**
  - Visitor or address budget: `429` with `Retry-After` (seconds to the oldest bucket's expiry), `RateLimit-Limit`, `RateLimit-Remaining` and `RateLimit-Reset`. Body: `{"code": "lookup_limit", "detail": "Too many searches from this device. Try again in N minutes."}`.
  - Page or global budget: `429` with `Retry-After` and body `{"code": "lookup_busy", "detail": "Search is busy right now. Try again in a few minutes."}`. Neither body names an agent, an address or the budget.
  - The page shows these messages as they are. The `/cma` funnel already renders a server `detail`; I'll confirm in the render.
- **Admitted requests** carry the `RateLimit-*` headers too, so the remaining budget is visible.

## 4. `/request` gets the same attribution

- `/v1/cma/{agent_code}/request` reads the visitor address through the same function (§2) instead of `request.client.host`.
- Its existing rule (5 per address per hour from `consumer_reports`) is kept, now with the real address.
- `consumer_reports.ip_address` stores the attributed address, so new consent records carry the visitor's address. **Existing rows keep the proxy address they were stored with;** nothing is rewritten.
- `routes/leads.py`'s first-`X-Forwarded-For` reader moves to the same function in the same PR.

## 5. When Redis is down **[Jerry: bounded fallback]**

- If the limiter's Redis call fails, each API process falls back to in-memory limits until Redis answers again:
  - **20** per visitor per hour and **60** per address, per process;
  - **30 SiteX calls per hour per process**, in place of the page and global budgets.
- Spend therefore stays bounded at (number of API processes × 30) per hour, and homeowners keep searching.
- Every fallback decision is logged as `LOOKUP_LIMITER_DEGRADED`, with counts only. LR-027 alerts on it.
- **No unbounded path:** an error inside the fallback refuses the search (`lookup_busy`), never admits it.

## 6. Shared networks

- Two people behind one carrier or office address each have their own 20, until together they reach that address's 60. That covers ordinary carrier-grade NAT for a homeowner page.
- A visitor who clears cookies gets a new 20, but the address ceiling (60) and the page and global budgets still apply.
- A visitor with cookies blocked gets a new cookie on each request. Each call is then a "new" visitor, so the address ceiling is the effective limit for them.

## 7. Tests and proof

**Real Redis and the real routes.** SiteX is faked at `client.search_by_address`, with a counter.
- **Shared across processes:** 20 searches pass and the 21st is a 429. Run from two separate API processes against one Redis, the shared limit holds, and the fake SiteX counter equals the admitted cache misses.
- **The other limits:**
  - per-address 60 across many cookies;
  - per-page 200 and global 1,000, counting misses only, with cache hits not counted;
  - the rolling window;
  - the headers, `Retry-After`, and body codes with no PII.
- **Spoofing:**
  - forged `X-TR-*` headers without a valid signature;
  - a valid signature from the wrong path, or a stale timestamp;
  - a client-supplied `X-Forwarded-For` on the web path;
  - altered agent codes, which never reset the visitor budget.
- **Limiter outage:** Redis stopped mid-test gives the in-memory bounds, the `LOOKUP_LIMITER_DEGRADED` log line, and no unbounded path.
- **Nearby requests:** a normal visitor's three searches and one request all succeed. A refused search makes zero SiteX calls.
- **`/request`:** the real address is stored and the 5-per-hour rule applies per real address.
- **Web proxy (jest):**
  - it signs, and sets and renews the cookie;
  - it never forwards an incoming `X-Forwarded-For` as the client;
  - it passes a 429's body and `Retry-After` through.
- **Planted-bug checks** for each guard: signature ignored, agent code in the key, refused requests counted, misses not counted, the fallback unbounded, and the first XFF hop trusted.
- **Renders:** the `/cma` page at 390 and 1280 with both refusal messages.

## 8. Rollout

- **Secrets** (Jerry sets them; they never go in the repo):
  - `PROXY_SHARED_SECRET` in Vercel and on the API in Render;
  - `VISITOR_COOKIE_SECRET` in Vercel;
  - `VISITOR_KEY_SECRET` on the API.
- **Probes, before enforcing** (Jerry, or Codex with access):
  - **P1.** A preview deployment request with a forged `X-Forwarded-For` records Vercel's real client address, not the forged one.
  - **P2.** A direct API request with a forged `X-Forwarded-For` shows what Render presents (append or replace), and records the deployed uvicorn start command.
- **Observe first.** Ship with `LOOKUP_BUDGET_ENFORCE=0`: every decision is logged as allow or would-refuse, with counts only, and nothing is refused. After a day of logs and the probes, set it to `1`. Rollback is setting it back to `0`.
- **No migration.** Budgets live in Redis. The `/request` attribution change writes to an existing column.

## 9. Dependencies and coordination

- **LR-005 (Codex)** moves the middleware throttle ahead of route execution. This design does not use that middleware: the lookup budget is checked inside the route, before SiteX. It still needs LR-005's merge for a consistent Redis client and outage logging, so I'll build on LR-005's merged code.
- **LR-027** alerts on `LOOKUP_LIMITER_DEGRADED` and on sustained page or global refusals.
- **Not in scope:** the authenticated property search (`/v1/property/search`), which is already limited per account.

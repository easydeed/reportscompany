# LR-006: bound public property searches

Design rev 2, for design review before code. Facts verified at `main` `9af7fd85`. Jerry's decisions (2026-11-12) are marked **[Jerry]**. The 20-per-visitor amount was approved on November 9.

**Implementation:** Codex's #315 implements the observation stage (`LOOKUP_BUDGET_ENFORCE=0`). This design is the contract #315 must match. Section 10 lists where #315 must change to match it.

## 0. What changed from rev 1 (Codex AMEND at `55f9faef`)

| # | Codex | Rev 2 |
|---|---|---|
| 1 | Twelve 5-minute buckets are not a rolling hour: summing the current bucket and the previous eleven forgets a request after 55 minutes, allowing 40 in 60. Pin the boundaries, compute `Retry-After` for every exhausted budget, and keep the two admissions independently atomic. | An **exact sliding window**: a log of admitted timestamps per key, counted over exactly the last 3,600 s. It never admits more than the limit within any 3,600 s. `Retry-After` is the time until a slot frees in *every* exhausted budget. Boundary tests run at 3,599, 3,600 and 3,601 s. The request admission and the vendor gate are two separate atomic scripts. See section 3. |
| 2 | Bound the fallback's memory and concurrent admission; a full store must refuse, never evict; bound the Redis waits so the fallback is reachable. Test a distinct-visitor burst and a concurrent final-slot admission with Redis down. | The fallback holds **at most 4,096 keys per process**, with at most *limit* entries per key, and prunes expired entries on every admission. Admission runs under one lock. When full, it **refuses**; a live counter is never evicted. The limiter gets its own Redis client: 250 ms connect and read timeouts, and a 30 s breaker after a failure. See section 5. |
| 3 | Separate the limiter's synthetic `direct` key from a real attributed IP. Never store `direct`, a fabricated address or an unverified forwarded value as consent evidence. Specify `/request` and leads behaviour until P1/P2 are established, reconcile with #315, and do not call the transport verified before the probes pass. | **LR-006 changes no stored consent or lead attribution.** `/request` and `routes/leads.py` keep their current behaviour, as #315 already does. `direct` is a Redis key name only; it is never a value anywhere else. Consent-evidence attribution, with explicit provenance, becomes its own follow-up once P1/P2 pass. The transport is described as *signed*; it is called *verified* only after the probes. See sections 2 and 4. |

## 1. What is wrong today

- **The public search has no limit.**
  - `POST /v1/cma/{agent_code}/search` (`routes/lead_pages.py`) calls SiteX (`services/sitex.py`, `lookup_property`) for anyone.
  - The global limiter only applies to requests that carry an account: `RateLimitMiddleware` returns early without one.
- **The API never sees the visitor's address.** The web proxies forward only `Content-Type`, so the API sees Vercel's server as the client. As a result:
  - `/request`'s "5 per IP per hour" counts per Vercel egress address;
  - `consumer_reports.ip_address` holds that egress address, not the visitor's.
- **The API is reachable directly** at `reportscompany.onrender.com`, so the limit has to live in the API, not only in the web proxy.
- **How the deployed API sees client addresses is not in the repository.** The deployed uvicorn command, and whether Render appends or replaces `X-Forwarded-For`, are established by the probes (section 8), not assumed.
- **The SiteX cache** is in-process (`sitex.py`). A cached answer costs nothing, but each API process has its own cache.

## 2. Who a visitor is **[Jerry: signed cookie + IP ceiling]**

The visitor key never contains the agent code, so switching agent pages cannot reset a budget.

**Through the web, once attribution is turned on** (`LOOKUP_TRUST_VERIFIED_PROXY=1` on both services, set only after P1 and P2 pass):
1. The Next proxy reads `x-real-ip`, which Vercel sets. It never reads an incoming `X-Forwarded-For` as the client.
2. It keeps a first-party `tr_v` cookie: 128 random bits, HMAC-signed with `VISITOR_COOKIE_SECRET`, `HttpOnly; Secure; SameSite=Lax`, 30 days. An absent or invalid cookie is replaced.
3. It signs the call to the API:
   - `X-TR-Visitor-IP`, `X-TR-Visitor-Id`, `X-TR-Proxy-Ts`;
   - `X-TR-Proxy-Sig` = `HMAC_SHA256(PROXY_SHARED_SECRET, ts + "\n" + method + " " + raw_path + "\n" + ip + "\n" + visitor_id)`.
4. The API uses those headers only if the signature verifies (constant-time compare), `ts` is within 60 s, and every field is well-formed. Otherwise it ignores them.

**Signed is not the same as verified.** A valid signature proves the request came through our proxy. It does not prove `x-real-ip` is the visitor's real address; that is what P1 establishes on a real deployment. Until the probes pass, this document and the code call the transport *signed*, never *verified*.

**Every other request:** before attribution is turned on, or with no valid signature (direct API callers, forged headers), the caller is counted in **one shared Redis key, `lb:v:direct`, limit 20 per hour in total**. This fails closed.
- **`direct` is a key name, not an identity.** It never becomes an IP address, a visitor ID, a log field naming a person, a response header or a stored record. It exists only as that Redis key, and in the process-local fallback under the same name.

**Keys:** the limiter keys are `HMAC_SHA256(VISITOR_KEY_SECRET, value)`, truncated to 16 bytes, in hex.
- IPv4 addresses are used as they are; IPv4-mapped IPv6 addresses are first converted to IPv4. Other IPv6 addresses are grouped by `/64`.
- No raw address or cookie value appears in Redis, logs or error bodies.

## 3. The budgets **[Jerry]**

All are counted in Redis, shared across workers, and checked before SiteX is called.

| Budget | Limit | Counts | Key |
|---|---|---|---|
| Per visitor | **20 per hour** (November 9) | every search request, cached or not | `lb:v:{visitor}` |
| Per address | **60 per hour** (the IP ceiling) | every search request from that address, across all cookies | `lb:ip:{address}` |
| Unattributed | **20 per hour in total** | every search without a valid signature, or while attribution is off | `lb:v:direct` |
| Per page | **200 per hour** | outbound SiteX attempts (cache misses, including retries and token calls) caused through that agent's page | `lb:p:{agent_id}` |
| Global | **1,000 per hour** | outbound SiteX attempts across all public pages | `lb:g` |

### The window: an exact sliding hour

- **Each key is a sorted set of admitted timestamps**, in microseconds from the store's clock (`redis.call('TIME')`), so every worker uses one clock. A member is `<µs>-<sequence>` so two admissions in the same microsecond stay distinct.
- **Admission, in one Lua script per stage:**
  1. For each key, remove members with a score ≤ `now − 3,600,000,000` (`ZREMRANGEBYSCORE`).
  2. Count what remains (`ZCARD`).
  3. If **every** key is below its limit, `ZADD` `now` to every key and set `PEXPIRE 3,600,000` on each. Otherwise change nothing.
- **Guarantee:** an admitted request is counted until exactly 3,600 s after it was admitted. So no key ever holds more than its limit within any 3,600 s span, at any boundary. Memory per key is at most its limit (20, 60, 200 or 1,000 entries), because only admitted requests are added.
- **Refused requests are not counted**, so a refused visitor is not pushed further back.
- Rev 1's twelve 5-minute buckets are withdrawn. Section 10 lists them as a #315 correction.

### Two stages, each atomic on its own

1. **Request admission:** before the route does any work, one script covers the visitor and address keys, or the `direct` key.
2. **Vendor gate:** immediately before each outbound SiteX attempt, one script covers the page and global keys.

The stages are independent scripts and are never combined.
- A request admitted at stage 1 and refused at stage 2 keeps its stage-1 count. It did search, and the page reports `lookup_busy`.
- Two concurrent requests cannot both take the last slot at either stage, because each stage's check-and-add is one script.

### `Retry-After`, for every exhausted budget

- The script returns, for each key, `wait_i = (oldest_score_i + 3,600,000,000 − now) / 1,000,000` seconds, rounded **up**, with a minimum of 1. That is when that key's oldest admission leaves the window, and a slot frees there.
- `Retry-After` = **the maximum `wait_i` over every exhausted key**, so a retry at that moment finds room in all of them. If only one key is exhausted, it is that key's wait.
- Admitted responses carry `RateLimit-Limit`, `RateLimit-Remaining` and `RateLimit-Reset` for the tightest stage-1 key: the fewest remaining, with ties broken by the longest wait.

### Refusals

- **Visitor, address or `direct` budget:** `429`, with body `{"code":"lookup_limit","detail":"Too many searches from this device. Try again in N minutes."}`. N is `Retry-After`, rounded up to whole minutes.
- **Page or global budget, or the limiter unable to decide:** `429` with `Retry-After`, and body `{"code":"lookup_busy","detail":"Search is busy right now. Try again in a few minutes."}`.
- Neither body names an agent, an address or a budget.

## 4. `/request` and leads: unchanged in LR-006

LR-006 changes no stored attribution. That matches #315, which leaves both paths alone.

- **`/v1/cma/{agent_code}/request`:**
  - The 5-per-address-per-hour rule and the value written to `consumer_reports.ip_address` stay exactly as they are today: the API's peer address, which is Vercel's egress for web traffic.
  - The limiter's visitor, address or `direct` key is **never** written into a consent record.
  - Nothing fabricated is written: no `direct`, no placeholder, and no unverified forwarded value.
- **`routes/leads.py`:** unchanged in LR-006. Its `get_client_ip` trusts a client-supplied `CF-Connecting-IP` or the first `X-Forwarded-For` hop, and uses the result for the lead rate limit and the IP blocklist. A caller can bypass both by setting a header. That bug exists today and is filed separately (section 10).
- **Historical rows** are never rewritten.
- **The follow-up, after P1 and P2:** consent and lead attribution move to the signed transport, with **explicit provenance** stored next to the address. For example, `ip_source` ∈ {`signed_proxy`, `peer`, `unknown`}, set to `signed_proxy` only once P1/P2 have passed and the signature verifies. An address that can't be attributed is recorded as `unknown`, never guessed. That needs its own reviewed design and migration; it is not part of LR-006.

## 5. When Redis is down **[Jerry: bounded fallback]**

### Reaching the fallback quickly

- **A dedicated client:** the limiter does not use the shared client (2 s connect and 2 s read). It has its own Redis client with **250 ms connect and 250 ms read** timeouts and no retries, so one failed call costs at most about 0.5 s.
- **A breaker:** after a failed call, the process skips Redis for **30 s** and goes straight to the fallback, then tries Redis once. During an outage, searches are not delayed by repeated timeouts.
- **Logging:** each fallback decision is logged as `LOOKUP_LIMITER_DEGRADED`, with counts only. LR-027 alerts on it.

### Fallback limits, per process

- Stage 1: the same keys and limits (20 per visitor, 60 per address, 20 for `direct`), counted in process memory.
- Stage 2: **30 outbound SiteX attempts per hour per process**, in place of the page and global budgets. Spend is therefore bounded at (number of processes × 30) per hour.

### Bounded memory, atomic admission

- **The same sliding-window algorithm in memory:** for each key, a deque of admitted monotonic timestamps. A key holds at most *limit* entries.
- **A cardinality cap of 4,096 keys per process.** Keys are ordered by their last admission. Every admission first drops the keys whose newest entry has left the window, so expired keys never occupy the cap.
  - Memory is therefore bounded: 4,096 keys × at most 60 entries.
- **Full means refuse.** If admitting a request would need a key beyond 4,096 live keys, the request is refused (`lookup_busy`).
  - A live counter is **never evicted** to make room, since eviction would reset someone's allowance.
- **One lock per process:** prune, check and add run under one lock. Two concurrent requests cannot both take a key's last slot.
- **An error inside the fallback refuses the request**; it never admits it. In observation mode the decision is logged as `would-refuse` and the search proceeds, exactly as it does for any decision in that mode.

## 6. Shared networks

- **People behind one address:** two people behind one carrier or office address each have their own 20, until together they reach that address's 60.
- **Cleared cookies:** a visitor who clears cookies gets a new 20, but the address ceiling (60) and the page and global budgets still apply.
- **Blocked cookies:** a visitor with cookies blocked gets a new cookie on each request, so the address ceiling is their effective limit.
- **Before attribution is turned on:** every public search shares `direct` (20 per hour in total). That is why observation comes first: it measures real traffic against that rule before anything is refused.

## 7. Tests and proof

These use real Redis and the real routes, with SiteX faked at the client and counting every call.

**Window boundaries (Codex point 1).** Entries are seeded at scores relative to the store's own `TIME`, so the boundaries are exact.
- **Expiry boundary:** 20 admissions at `now − 3,599 s` mean the 21st is refused. At `now − 3,600 s` and at `now − 3,601 s` they have left the window, so it is admitted.
- **The burst rev 1 allowed** is refused: 20 at `now − 3,300 s` (minute 5), then a 21st now.
- **Retry-After** equals the oldest entry's remaining time, rounded up; a retry one second earlier is refused, and one at that time is admitted.
- **Two exhausted keys** (visitor and address): `Retry-After` is the larger wait, and a retry at the smaller wait is still refused.
- The same table runs against the in-memory fallback with an injected clock.

**Atomicity:**
- **Final slot:** 19 admitted, then 10 concurrent requests from two API processes against one Redis. Exactly one is admitted.
- **Per stage:** the same holds at the vendor gate.
- **Stage 2 refusal:** it leaves the stage-1 count in place.

**Fallback (Codex point 2), with Redis stopped:**
- **Distinct-visitor burst:** 5,000 distinct signed visitors. The first 4,096 live keys are admitted and the rest refused with `lookup_busy`. No earlier visitor's count is reset: visitor #1's 21st search is still refused.
- **Concurrent final slot in one process:** exactly one of 10 threads is admitted.
- **Fast fallback:** with Redis unreachable, a request reaches the fallback within the 250 ms budget, and the breaker skips Redis for 30 s.
- **Spend cap:** the stage-2 cap of 30 per process holds.

**Attribution (Codex point 3):**
- **No attribution on:** with `LOOKUP_TRUST_VERIFIED_PROXY` unset, all traffic counts in `direct`.
- **Signatures:** forged or stale signatures, the wrong path, and a client-supplied `X-Forwarded-For` all count in `direct`.
- **Agent codes:** altering the agent code never resets a visitor.
- **Consent records unchanged:** after searches in every attribution state, `/request` writes `consumer_reports.ip_address` exactly as main does. No row ever contains `direct`, a limiter key or a forwarded value.

**Elsewhere:**
- **Headers and bodies:** `RateLimit-*` and `Retry-After` are correct, and bodies contain no PII.
- **Web proxy (jest):**
  - it signs only when attribution is on;
  - it sets and renews the cookie;
  - it never forwards an incoming `X-Forwarded-For`;
  - it passes a 429's body and headers through.
- **Planted-bug checks:**
  - the window shortened to 55 minutes;
  - `Retry-After` taken from the wrong key;
  - the stages merged;
  - the fallback evicting;
  - the fallback unlocked;
  - the shared 2 s client used;
  - `direct` written to a consent row;
  - the signature ignored.
- **Renders:** `/cma` at 390 and 1280 with both refusal messages.

## 8. Rollout

1. **Secrets.** Jerry sets them; they never go in the repo:
   - `PROXY_SHARED_SECRET` on Vercel and the API;
   - `VISITOR_COOKIE_SECRET` on Vercel;
   - `VISITOR_KEY_SECRET` on the API.
2. **Probes,** run by Jerry, or by Codex with access:
   - **P1:** a preview request with a forged `X-Forwarded-For` records Vercel's real client address in `x-real-ip`, not the forged one.
   - **P2:** a direct API request with a forged `X-Forwarded-For` shows what Render presents, and records the deployed uvicorn start command.
3. **Observe** with `LOOKUP_BUDGET_ENFORCE=0` (#315's default). Decisions are logged as `allow` or `would-refuse`, with counts only.
   - Before attribution is on, every search counts in `direct`.
   - After P1/P2, `LOOKUP_TRUST_VERIFIED_PROXY=1` turns on the signed per-visitor keys, still in observation.
4. **Verify shared counting** across the deployed API processes, then **enforce** after a day of observation: set `LOOKUP_BUDGET_ENFORCE=1`. Enforcement requires the attribution opt-in. Rollback is setting it back to `0`.
5. **No migration.** Budgets live in Redis and process memory. No stored attribution changes in LR-006.

## 9. Dependencies

- **LR-005 (Codex) lands first,** as Codex noted. The lookup budget is checked inside the route and does not use the account middleware.
- **LR-027** alerts on `LOOKUP_LIMITER_DEGRADED` and on sustained `lookup_busy` refusals.
- **Not in scope:** the authenticated property search, which is already limited per account; consent and lead attribution (section 4's follow-up).

## 10. Reconciling with #315, and found while revising

**#315 must change to match this design** (this is a design note, not a code review of #315):
- **The window:** `lookup_windows._TAKE` counts buckets `> bucket − 12`, so an entry is forgotten 55 to 60 minutes after admission, the 40-in-60 case. `LocalWindow` has the same cutoff. Both move to the exact sliding window in section 3.
- **The Redis client:** `public_lookup_budget._check` calls `take_shared` through the shared client (2 s connect, 2 s read). It gets the dedicated 250 ms client and the breaker (section 5).
- **Already as specified:**
  - the fallback cap of 4,096, refusing rather than evicting, under one lock;
  - `direct` as a key only;
  - `/request` and leads unchanged;
  - observation as the default;
  - attribution opt-in only after the operator's evidence.

**Found, to file:**
- **Lead rate limit and blocklist can be bypassed by a header.** `routes/leads.py` `get_client_ip` trusts a client-supplied `CF-Connecting-IP` or the first `X-Forwarded-For` hop, and uses it for the lead rate limit and the IP blocklist. This is not caused by LR-006; it is fixed with the attribution follow-up (section 4).

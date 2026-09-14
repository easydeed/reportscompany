# FINDINGS — noticed during remediation, deliberately not fixed

Running log per Execution Plan §0.2. Each entry is out of the recording
ticket's scope and awaits its own ticket.

## From T0.2 (env-var reconstruction)

1. **Split email providers.** SendGrid is the primary sender
   (`apps/worker/src/worker/email/providers/sendgrid.py:10`), but the worker's
   failure-notification and consumer-report paths still send via Resend
   (`apps/worker/src/worker/tasks.py:668`, `:1894`), while
   `apps/api/src/api/settings.py` marks `RESEND_API_KEY` "Deprecated — kept for
   backwards compat, unused". If `RESEND_API_KEY` is unset in production, those
   two paths silently skip sending. Decide one provider.
2. **Two proxy routes use nonstandard API-base env vars with a wrong default
   port.** `apps/web/app/api/proxy/v1/affiliate/accounts/[accountId]/unsponsor/route.ts:4`
   reads `NEXT_PUBLIC_API_URL || "http://localhost:8000"`;
   `apps/web/app/api/proxy/v1/property/preview/route.ts:4` reads
   `API_URL || 'http://localhost:8000'`. Every other proxy route uses
   `NEXT_PUBLIC_API_BASE`; the API listens on 10000 (`settings.py` `PORT`), so
   the fallback is wrong locally. Both endpoints likely break in local dev.
3. **Dead Stripe price fields in Settings.**
   `STARTER_PRICE_ID` / `PRO_PRICE_ID` / `ENTERPRISE_PRICE_ID`
   (`apps/api/src/api/settings.py:20-22`) have zero consumers anywhere in
   `apps/`. The live mapping uses `STRIPE_PRICE_PRO_MONTH` /
   `STRIPE_PRICE_TEAM_MONTH` (`apps/api/src/api/config/billing.py:18-19`).
   Remove the dead fields or wire them up — relevant to Phase 2's plan-truth work.

## From Phase 2A (T2.1/T2.2)

4. **Phase 5 dead-code candidate: `_intake/*.zip`.** Binary archives at
   `_intake/real-estate-saa-s.zip` and `_intake/website-updates.zip` contain
   copies of files deleted in T1.1 (matched the `new-listings-gallery.html`
   verification grep). Prove-death rules apply before removal.
5. **`scripts/seed_production_demo_accounts.py:17-20` hardcodes a live Render
   Postgres connection string, password included**, as the default
   `DATABASE_URL`. Anyone running it without arguments writes to production.
   Same class as the `.env.example` leak fixed in T0.2 — belongs in a security
   ticket, not a cleanup one.

## From the Delivery Surfaces remediation (method, not code)

6. **"Merged" in a message is not repo state.** Three times this session — #58,
   #59 and #60 — a message stated a PR was merged while the GitHub API reported
   `state: open, merged: false`, and `main` was unchanged. Each time the branch
   I was told to build on did not exist yet. Verified via
   `pull_request_read` rather than working around an apparently stale checkout,
   which is what §0.6's "test the operation, don't read the summary" asks for
   applied to branch state. **Check the PR state before cutting a branch that
   depends on it**; the check is one call and the alternative is building on a
   base that is not there.

   Related, and worth knowing before the next CI-red alarm: **`main`'s Backend
   Tests job has `conclusion: failure` on every run for at least the last six
   merges**, including runs predating any of this remediation's branches. That
   is the deliberately-landed-red tickets (D-038, D-041, D-054) plus
   `test_simplyrets_query_builder.py`, `test_billing_checkout.py` and
   `test_me_endpoint.py`. A red PR check is therefore not evidence about the PR
   until the failing test names are compared against the files it touches.


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

## From P1-A (`fix/p1a-consumer-facing`, Delivery Surfaces Phase 1)

1. **Mailing address is still printed, and it is owner PII of the same class as
   the name.** A1 removed Primary/Secondary Owner but not **Mailing Address**,
   which still renders in bold, classic and elegant (`property.mailing_address`,
   defaulting to the site address). Where the two differ — an owner who does not
   live in the property — this discloses where the owner receives mail, to a
   consumer lead, on the page the name was just removed from. A1 is explicit that
   "it is the *name* and the *framing* that come out", so this was left rather
   than widened. It needs a decision, not an improvisation: the field is useful on
   an owner-facing seller report and wrong on a lead-facing one, and nothing
   currently distinguishes those audiences — see 2.

2. **There is no internal/agent-only variant of the property report.** A1 asked to
   check before removing the owner block and to gate rather than delete if one
   existed. It does not exist. The only "internal" concept is
   `_is_internal_render_caller()` (`apps/api/src/api/routes/report_data.py:18`),
   which authenticates the PDF renderer fetching its own data — not a report
   variant. Every property report is the lead-facing one. If an owner-facing
   variant is wanted, that is the seam it needs, and it also resolves 1.

3. **Five property templates are dead — 0 references.** `teal/teal.jinja2`,
   `bold/bold.jinja2`, `classic/classic.jinja2`, `modern/modern.jinja2`,
   `elegant/elegant.jinja2`. `THEME_TEMPLATES`
   (`apps/worker/src/worker/property_builder.py:179-184`) maps all five themes to
   the `*_report.jinja2` family only; searching each `<theme>/<theme>.jinja2` path
   repo-wide returns 0 references and nothing extends or includes them. They still
   contain the owner blocks and unguarded map containers this ticket fixed in the
   live family, so an audit grepping `owner_name` will find them and re-open a
   closed finding — the D-050/D-052 pattern. Belongs with issue #42
   (`chore/dead-code-round-2`), which should be extended to cover them.

4. **`[DIAGNOSTIC]` logging is live throughout the property pipeline.**
   `property_builder.py` contains **21** `logger.warning("[DIAGNOSTIC] …")` calls
   — `:36`, `:200-203`, `:503`, `:904`, `:906`, `:908`, `:937`, `:938`, `:961`
   among them — logging geocode results, API-key truthiness, image URLs and
   template paths. Same class as the startup noise removed from the API on
   `fix/env-var-name-drift` (D4). It logs at WARNING, so it is in production logs
   at default level, and `:961` logs the first 80 characters of a Google Maps URL
   (coordinates; stops short of the key). Wants a cleanup ticket.

5. **`teal_report.jinja2:1316` uses the cover photo as the aerial page
   background.** `hero` is the user-uploaded cover, or failing that a Google
   **Street View** of the address (`property_builder.py:941-949`). This is what
   made the audit describe "a stock drone photograph of a suburb" — in the
   reviewed renders `hero` was a fixture — but in production it is a *street-level*
   photograph behind a page titled "AERIAL VIEW". No other theme does this; the
   other four use `hero` only on the cover. Not changed: A2 scopes to the map, and
   removing a full-bleed page background is a design change. Flagged for
   Workstream E.

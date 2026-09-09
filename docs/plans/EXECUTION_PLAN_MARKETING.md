# Marketing & Funnel Remediation — Phase M

**Date:** 2026-08-27
**Source:** Chrome UX audit, 17 findings
**Base:** `main` at `b2efca2`
**Governs:** §0 Rules of Engagement from `EXECUTION_PLAN_2026-08-17.md` — unchanged

---

## Context Claude Code needs

This phase is different from Phases 0–5. Those were correctness work found by reading
code. These findings came from a browser session walking the public site as a first-time
visitor. Every one is something a real estate agent would see before deciding whether to
trust the product.

**These are not new discoveries.** The audit ran 2026-08-17 and was deliberately deferred
while stability work completed. Do not re-audit. The findings below are the spec.

**One thing today's production work changed:** the real plan data is now known, and the
pricing page contradicts it. From `mr-staging-db`:

| Slug | Display name | market_reports_limit |
|---|---|---|
| `free` | Free | 3 |
| `starter` | **Growth** | **15** |
| `pro` | Growth Plus | 99999 |
| `solo` | Solo Agent | 25 |
| `trial` | Trial | 3 |

The pricing page advertises Growth at **25/month**. Production enforces **15**. The 25
belongs to `solo`, which has no UI presence. This is D-035, severity WRONG, and 95
`skipped_limit` rows in `schedule_runs` are that cap firing on real users.

A `trial` plan row exists, but **no trial-expiry mechanism exists anywhere in the code** —
confirmed during Phase 2. So Free is permanent and Terms §4 describes behaviour the
product does not have.

---

## Decision gates — 4 of 17 need Jerry

Do not guess on these. Do not use a placeholder. If a gate is unanswered when you reach
its ticket, skip that ticket, note it in the PR, and continue.

| Gate | Blocks | Question |
|---|---|---|
| **G1** | M3-T1, M3-T2, M3-T6 | Growth = 15 or 25? And is Free permanent (delete trial copy) or a trial (delete the $0 tier)? |
| **G2** | M3-T3 | Real, verifiable social proof figure — or remove the claim entirely? |
| **G3** | M4-T3 | Real registered business address. Phone optional; omit rather than fake. |
| **G4** | M6 | What does a title company actually buy, and what's the conversion action? |

The other 13 tickets proceed now.

---

## M1 — Single fixture for all demo data

**Branch:** `fix/m1-demo-fixture`
**Findings:** #4, #5, #12, #13

The homepage prices Irvine at **$485,000** (hero: 1,247 active / 28 DOM) and **$1.2M**
("Live Preview": 847 active / 24 DOM). Same city, same page. For a product whose only
promise is accurate MLS data, contradicting itself about Irvine is disqualifying in a way
a broken link is not.

### M1-T1 — Create the fixture

`apps/web/lib/demo-data.ts` as the single source for every mock number, city, date, agent
name, and brokerage on the marketing site. Nothing inline anywhere else.

### M1-T2 — Reconcile Irvine, migrate all components

Pick one set of Irvine figures and use it everywhere. Every marketing component imports
from the fixture.

**Acceptance:** `grep -rn "485,000\|1.2M\|1,247\|847" apps/web/components/` returns hits
only inside the fixture file.

### M1-T3 — Relative dates

Demo reports are dated "January 2026" and "March 2026"; contacts "last sent Jan 2026."
Today is August. Generate all dates relative to `now` — "last month," "3 weeks ago."
Never hardcode.

**Acceptance:** no month-year string literals in marketing components.

### M1-T4 — Fictional brokerages

"Sarah Johnson" is credited to **"Compass Real Estate"** in one card and **"Compass
Realty"** in another — an invented person attached to a real brokerage, named two ways.
Trademark exposure, and any agent recognises Compass instantly.

Replace with clearly fictional names (Harbor Point Realty, Cypress & Vine Properties).
Verify the replacements aren't real firms.

```bash
grep -rn "Compass\|Coldwell\|Century 21\|Keller Williams\|RE/MAX\|Sotheby\|eXp\|Douglas Elliman" apps/web/ | grep -v node_modules
```

**Note:** `schedule_runs` contains a schedule named "Keller Williams North" — that's
production data, not marketing copy. Do not touch the database.

### M1-T5 — Avatar initials

The `/register` social-proof avatar row reads **SJ, MC, LP, DR, AW** — the exact initials
of the fake demo contacts on the homepage (Sarah Johnson, Michael Chen, Lisa Patel, David
Rodriguez, Amanda Wilson). The social proof is the seed data, and anyone who scrolled the
homepage sees it.

Once the fixture exists, assert they can't collide: either unlabeled generic shapes, or
initials drawn from a set with no overlap with fixture contacts.

**Acceptance:** no avatar initial pair matches any fixture contact.

**→ PR.**

---

## M2 — Shared layout

**Branch:** `fix/m2-shared-layout`
**Findings:** #9, #10, #16

### M2-T1 — One header, one footer

`/privacy`, `/terms`, and `/security` use a completely different header, nav, footer, and
tagline than the landing page.

- Landing nav: How It Works / Reports / Lead Capture / Contacts / Pricing / Log in
- Legal nav: Product / Pricing / Contact / Sign in

It reads as a different company's site, and there's no route back to the landing page's
sections. Extract shared header and footer components; apply to all three legal routes.

### M2-T2 — Title template

`<title>` renders "Privacy Policy | TrendyReports | TrendyReports" on all three legal
pages — the template appends the brand suffix twice.

**Acceptance:** brand appears once in every page title sitewide.

### M2-T3 — Branded 404

`apps/web/app/not-found.tsx` inherits the homepage title and offers no nav, no search, no
link home — a terminal dead end reachable from the footer. Add the shared header, a plain
message, and a primary CTA back to the landing page.

**Acceptance:** 404 renders shared nav; a visitor can leave without the back button.

**→ PR.**

---

## M3 — Copy truth

**Branch:** `fix/m3-copy-truth`
**Findings:** #1, #2, #3, #11, #14, #15
**Gates:** G1 (T1, T2, T6), G2 (T3)

### M3-T1 — Free vs. trial [G1]

**BLOCKER in the original audit.** Hero and `/register` say "14-day free trial, cancel
anytime." Pricing shows a permanent Free $0 plan at 3 reports/month. Terms §4 says "At the
end of the trial, you must subscribe to continue."

The code has effectively voted: `free` is a plan row with real limits, `sponsored_free` is
its sibling, and no expiry mechanism exists. But a `trial` plan row also exists, so confirm
with Jerry rather than inferring.

Per G1, make hero, pricing table, `/register`, and Terms §4 say the same thing.

```bash
grep -rn "14-day\|free trial\|14 day\|trial" apps/web/ | grep -v node_modules
```

**Acceptance:** grep for "trial" returns only consistent, intentional usage. Quote Terms §4
and the pricing table side by side in the review block.

### M3-T2 — Pricing numbers match production [G1]

Whatever G1 decides, the number on the pricing page must equal the number the system
enforces. If Jerry says 25, `starter.market_reports_limit` and `monthly_report_limit` both
need updating (the legacy column still feeds `evaluate_report_limit`) — that's a data
change, so write the migration but flag it for Jerry to apply. If Jerry says 15, the copy
changes.

Also fix the `/register` benefit list, which promises **"Unlimited market reports from live
MLS data"** while Free is capped at 3. Only `pro` is unlimited.

**Acceptance:** displayed limit == enforced limit for every tier shown.

### M3-T3 — One social proof figure, or none [G2]

`/register` says "4.9/5 from 500+ agents." `/login` says "TRUSTED BY 2,000+ AGENTS."
Neither cites a source. Two adjacent funnel pages, two different headcounts — once a
visitor notices, every other number on the site is suspect.

Per G2: one verified figure sitewide with a real source, or remove both. Do not invent a
smaller number.

### M3-T4 — Login stat tile

`/login` shows "Reliable / Uptime" where a number belongs, between "7 / Report types" and
"50K+ / Emails sent."

- **"7 / Report types" is correct** — 8 slugs exist, `open_houses` is disabled in the
  wizard, user-facing is 7. Leave it.
- "Reliable" as a metric is a non-claim. Remove the tile or publish a real figure.
- **Verify "50K+ emails sent" against `email_log`.** If it isn't real, remove it under the
  same rule as T3.

### M3-T5 — Explain the tier differentiators

"AI Market Insights," "Priority Generation," and "CMA Lead Page" appear as paid-tier
differentiators with no definition, tooltip, or anchor. Two of the three upgrade reasons
don't land.

Derive real definitions from the code rather than inventing marketing language — these are
implemented features. Add tooltips or short inline descriptions.

### M3-T6 — Drop the "with email" qualifier

"Register with email" / "Sign in with email" implies alternatives that don't exist. Drop
the qualifier until SSO ships.

**→ PR.**

---

## M4 — Navigation & identity

**Branch:** `fix/m4-nav-identity`
**Findings:** #7 (link only), #8
**Gate:** G3 (T3)

### M4-T1 — Kill mailto-as-navigation

"Partners," "Press," and "Support" are footer nav links that open a blank email client. A
Company section where every link is a mailto reads as a site with no company behind it.

Reduce the footer to links resolving to real pages. Move support to a single labelled
contact line rather than three nav entries. Do not build Partners/Press pages — deleting
the headings is the correct fix.

### M4-T2 — Title companies link

The footer's "For Title Companies" is `mailto:sales@trendyreports.io` and
`/for-title-companies` 404s. The page itself is M6, gated on G4.

**Until the page exists:** remove the footer link rather than leaving a mailto that fires a
blank email client with no context. A missing link is better than a dead end.

### M4-T3 — Real company identity [G3]

`/privacy`, `/terms`, and `/security` show "123 Market Street, San Francisco, CA 94103"
and "(415) 555-1234" — both placeholders, on the exact pages a title company reads during
vendor diligence.

Per G3, use the real registered address. If there's no business phone, **omit the field
entirely** — an omitted phone is neutral, a fake one is disqualifying.

Do not ship a substitute placeholder. If G3 is unanswered, leave this ticket open and note
it in the PR.

**→ PR.**

---

## M5 — Responsive

**Branch:** `fix/m5-responsive`
**Finding:** #17

At 1142px the `/app` dashboard clips horizontally — the "Bulk Import" button and the user
menu are cut off at the right edge. Any laptop at ~1280px or any split window loses
controls.

Audit the `/app` shell at 1024 / 1142 / 1280. The original observation came from an
authenticated **Title Rep** session, so it isn't evidence about other account types — check
at least `REGULAR` and `TITLE_COMPANY` too. The local stack from Phase 2A provisions all
five.

**Acceptance:** no horizontal clipping at any of the three widths, for at least three
account types.

**→ PR.**

---

## M6 — Title companies page [G4]

**Branch:** `feat/m6-title-companies`
**Finding:** #7

**Do not start without G4 answered.** This page cannot be written from the codebase.
Placeholder marketing copy here is worse than the 404 — a 404 makes no claim.

Once answered: build the route using M2's shared layout, with a real conversion action
(form or booking link) rather than a mailto. Restore the footer link removed in M4-T2.

---

## Confirmed clear — do not re-fix

The Chrome audit explicitly checked and cleared these:

- **No "Austin, TX" mock data.** All demo markets are Irvine / Newport Beach / Pasadena /
  Laguna Beach — correctly SoCal/CRMLS.
- **No `.com`/`.io` email mismatch.** Every address on every page is `@trendyreports.io`.
- **Homepage `<title>` is brand-first and specific**, not generic.
- **Password rules are stated inline** on `/register` ("at least 8 characters with a number
  and symbol").
- **`/security` is unusually honest** — it explicitly lists what the product does *not*
  have (no SOC 2, no MFA, no SSO, no pen test). **Keep that page exactly as is.** It's the
  most credible thing on the site.

---

## Verification

After M1–M5 merge, re-run a Chrome audit against the same route list with this document
attached as "already fixed — report only regressions and new findings." Do not send Chrome
in cold; it will re-find everything and burn its budget.

---

## Sequence

| | Branch | Gate | Can start |
|---|---|---|---|
| M1 | `fix/m1-demo-fixture` | — | now |
| M2 | `fix/m2-shared-layout` | — | now |
| M3 | `fix/m3-copy-truth` | G1, G2 | partially now |
| M4 | `fix/m4-nav-identity` | G3 | partially now |
| M5 | `fix/m5-responsive` | — | now |
| M6 | `feat/m6-title-companies` | G4 | blocked |

M1, M2, and M5 are independent and can run in any order. M3 and M4 have gated tickets that
can be skipped and picked up later. M2 must merge before M6.

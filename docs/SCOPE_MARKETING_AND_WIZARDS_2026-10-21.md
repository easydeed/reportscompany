# Scope — the marketing landing page and the wizards

**Date:** 2026-10-21
**Asked for:** scope, an order and a size. Not a build.
**Base:** `main` at `e2dc44f0`
**Governs:** §0 Rules of Engagement from `EXECUTION_PLAN_2026-08-17.md`

Everything below is read off the tree at `e2dc44f0` or measured today. Where a
number came from a run, the run is named. Where something is a question for
Jerry or for Design, it is marked and not answered here.

---

## 0 · Three premises in the ticket that the code does not support

Stated first because two of them change the order of the work.

### 0.1 "the two with no measurement at all"

There is a measurement. It is called **Frontend Tests**
(`.github/workflows/frontend-tests.yml`), it runs `tsc --noEmit` and the jest
suite on every push that touches `apps/web/**`, and:

```
gh run list --workflow=frontend-tests.yml --limit 100   ->  100 of 100 failure
gh run list --workflow=frontend-tests.yml --status success --limit 3  ->  (empty)
```

The oldest of those 100 runs is **2026-06-24**. There is no successful run of
this workflow on record at all. The most recent run on `main` (39491654740,
`Merge pull request #188`) ends:

```
Test Suites: 4 failed, 3 passed, 7 total
Tests:       13 failed, 41 passed, 54 total
```

and `npx jest` in `apps/web` today reproduces that figure exactly — same 13,
same 4 suites. So the surfaces are not unmeasured. They have a gate that has
been red for four months, which is worse: an unmeasured surface produces no
findings, while a permanently red gate produces 13 findings that everybody has
learned to scroll past. It also means **no web change in that period was gated
on anything**, including every B-phase restyle.

The four suites and their causes (measured, not guessed):

| Suite | Failing | Cause |
|---|---|---|
| `AccountSwitcher` | 6 | `No QueryClient set` — the component uses react-query; the test renders it with no provider |
| `NewSchedulePage` | 2 | same, plus it mocks `next/dynamic` and `ScheduleWizard`, neither of which the page has used since it moved to `UnifiedReportWizard` |
| `TemplatesMapping` | 4 | genuine drift — `buildNewListingsHtml` no longer contains `123 Main St`, price-band data, default colors, comma formatting |
| `PlanPage` | 1 | sponsored badge assertion |

`NewSchedulePage` is worth a second look on its own. Of its five tests, the
two that render anything fail, and the three that pass are of this shape:

```js
const expectedReportTypes = ['market_snapshot', ..., 'featured_listings'];
expectedReportTypes.forEach(type => { expect(expectedReportTypes).toContain(type); });
```

The array is asserted against itself. The product is not involved. That is the
only test in the repository whose name claims to cover a wizard.

### 0.2 "the M-phase found 17 issues and most were deferred"

Most were resolved, and several were resolved by **deleting the claim** rather
than sourcing it. All four gates were answered:

| Gate | Question | What happened |
|---|---|---|
| G1a | Growth 15 or 25? | Jerry changed the **data**, not the copy — `db/migrations/0054_growth_plan_report_limit.sql` sets both limit columns on `starter` to 25. The pricing page's "25 Market Reports / month" is now correct. |
| G1b | Free permanent, or a trial? | Permanent. Trial copy deleted — `hero.tsx:138`, `final-cta.tsx:41`, `faq.tsx:38`, `register/page.tsx:87,125`. |
| G1c | — | "Priority Generation" deleted from Growth Plus (`pricing.tsx:49`), with D-046's evidence in the comment. |
| G2 | A real social-proof figure, or none? | None. The `/about` stats card is deleted entire (`about/page.tsx:51`), "Trusted by 2,000+ agents" is gone from `/login`, the `/register` social-proof block is gone. |
| G3 | Real registered address | Supplied 2026-08-27 and live on both legal pages. |
| G4 | Title companies page | **Still unanswered.** `/for-title-companies` does not exist and the footer entry stays removed (`site-footer.tsx:14`). |

The fabricated testimonials were removed from the render in `11459e7c`. The
component file survives, orphaned, at
`apps/web/components/marketing/testimonials.tsx` — three invented people with
invented quotes and five stars each — and `marketing-home.tsx:23` carries the
comment saying why it is not imported. **A prospect does not see them.** One
import restores them.

So "a redesign that inherits the copy inherits the defects" is the right worry
pointed at the wrong copy: the live copy is largely clean, and it is **Design's
deck** that reintroduces three of the deleted claims (§2.2).

### 0.3 What the wizards actually are

Not three surfaces. Two live ones, one public funnel, and 2,882 lines of
orphaned wizard code:

| | Lines | Routes | Live? |
|---|---|---|---|
| `unified-wizard/` | 1,541 | `/app/reports/new`, `/app/schedules/new`, `/app/schedules/[id]/edit` | yes |
| `property-wizard/` | 3,425 | `/app/property/new` | yes |
| `schedule-builder/` | 1,562 | (sections, shared) | partly — only `recipients-section` is imported, by `unified-wizard/step-deliver.tsx` and `onboarding/guided-get-started.tsx` |
| `app/cma/[code]/cma-funnel.tsx` | 692 | `/cma/[code]` — **public** | yes |
| `components/Wizard.tsx` | 769 | — | **no importer** |
| `schedules/schedule-wizard.tsx` | 693 | — | **no importer** (exported from a barrel nobody imports) |
| `onboarding/setup-wizard.tsx` | 704 | — | **no importer** |
| `lead-pages/ConsumerLandingWizard.tsx` | 716 | — | **no importer** |

The **schedule builder is not a wizard** — it is step 4 of the unified wizard
(`step-deliver.tsx`: cadence weekly/monthly, day-of-week, day-of-month,
timezone, recipients, name), plus 1,562 lines of section components of which
one is reachable.

---

## 1 · What the marketing surface is

| | |
|---|---|
| Entry | `app/page.tsx` (5 lines) → `components/marketing-home.tsx` (42) |
| Sections | 13 rendered components, `components/marketing/` (2,522 lines across 14 files; `testimonials.tsx` is the unrendered 14th) |
| Chrome | `site-nav.tsx` (120) + `site-footer.tsx` (101), shared with every public page since M2 |
| Other public pages | `/about` `/blog` `/careers` `/docs` `/privacy` `/terms` `/security` `/register` `/login` `/welcome` |
| Demo data | `lib/demo-data.ts` — the M1 fixture. "Nothing here is real. Every figure is illustrative." |

**Total in scope for a landing restyle: ~2,785 lines.**

### 1.1 Can the render harness reach it? Yes — measured today

`scripts/render-routes.json` already carries `/`, and the eleven public routes
were probed directly against `next dev` on 3100 with **no cookie and no API**,
at 1440×900 and at 390×844:

```
all 11 routes: HTTP 200, no redirect, h1 present, 0 spinners, 0 skeletons
```

No API is needed — none of the marketing components or standalone pages reads
auth or calls the API (`grep` for `mr_token|useAuth|apiFetch|fetch(` over
`components/marketing/` and the seven content pages: zero hits). This really is
the easy half. Three limits of the harness as it stands, each small:

1. **It always mints a cookie.** `render_routes.mjs:437` calls
   `ctx.addCookies([{name:'mr_token', value: mintToken(...)}])` unconditionally,
   and an unknown token name falls back to `mintToken({})` — a *valid* default
   token, not no token. There is no way to express "render this the way a
   prospect sees it" today. (In practice the output is identical, because the
   marketing chrome is auth-blind — but that is a fact about today's nav, not a
   property of the harness.)
2. **One viewport**, 1440×900. The manifest has a single `viewport` key and
   `compare()` is keyed by `route + token`, so a second viewport needs the key
   widened. M5 audited `/app` at three widths; the public pages were never
   checked at any.
3. **The probe's text capture is tuned to app chrome.** `landmarks` keeps
   strings of 2–60 characters, which excludes nearly every sentence on a
   marketing page. A copy change — the thing most likely to regress here —
   would diff as nothing.

### 1.2 Found in that first probe

- **`/docs` overflows horizontally by 70px at 390px.** The culprit is the
  `curl` example block (`bg-slate-900 rounded-lg p-4 font-mono text-sm`) with
  no `overflow-x-auto` and no wrapping; it forces its parent card to 444px and
  takes 8 elements past the viewport edge with it. First measurement of these
  pages, first finding.
- **`/welcome` renders no `<h1>`** without a `?token=` parameter (175 characters
  of body text). It is the invited-user password page and its no-token state is
  a card, not a page heading. A manifest row for it needs a different marker or
  a token in the path, or the harness will call it BROKEN.

---

## 2 · Design's package, against the live files

`docs/design-claude/new_package/design_handoff_product/` — `Landing v4.dc.html`
(37KB) and `Wizards v3.dc.html` (67KB), plus `ADOPTION.md`, which already
sequences them: Landing is item 8, *"independent of everything above; can be
done any time by whoever owns marketing"*; Wizards is item 10, *"after your
end-to-end measurement"*.

### 2.1 Did they design from live files this time? Partly

**The feature set: yes.** Landing v4 says "Seven reports. Pick what your sphere
hears about" — seven is the live count after `3164cbb4` disabled `open_houses`.
The wizard deck's market flow is the four steps we have, under our names
(story / audience / where-and-when / deliver). The property deck says *"Owner
names never print"* and *"Text stays dark where your color is light. We never
shift your color to fix contrast"* — both are current, and the second is
exactly the `ink_on` rule D-208 landed last week. Somebody read the code.

**The data: no.** The decks are templated (`{{ p.price }}`, `{{ previewArea }}`,
`{{ c.address }}`) around a demo agent called **Jennifer Martinez of Jennifer
Realty**, `jennifer@jenniferrealty.com`. The live fixture's agent is **Sarah
Johnson** (`demo-data.ts:100`), her brokerage comes from `BROKERAGES`, and rule
2 of that file is "No demo value is written inline in a component." Adopting
either deck literally reintroduces exactly what M1 removed, and "Jennifer
Realty" has not been through M1-T4's check that a fictional brokerage is not a
real firm.

### 2.2 Does the landing resolve, reproduce or ignore the 17?

Mostly it **sidesteps** them — the deck has no testimonials, no stat tiles, no
trial copy, no uptime or SOC claim, and its prices are placeholders rather than
numbers, so G1a is deferred to data rather than re-decided. But it reintroduces
three deleted things:

1. **"Open Houses"** in the footer's Reports column. Deliberately removed from
   user-facing copy in `3164cbb4`; still `disabled: true` in
   `unified-wizard/types.ts:97` because SimplyRETS open-house data is not
   reliable. The deck advertises a report the product refuses to build.
2. **"Status"** in the footer. `/status` was **deleted** in `725802a7` for
   carrying fabricated uptime numbers with no monitoring behind them. There is
   no such route (`apps/web/app/status` does not exist).
3. **"350+ Southern California cities."** An unsourced quantitative claim —
   precisely the family G2 answered by deleting both figures, with "Do not
   invent a smaller number" written next to it. Either it has a source or it
   goes. **[JERRY]**

And one gated thing: **"Title company or lender? Sponsor TrendyReports for your
agents… Talk to us →"**, plus a "Sponsors" footer column. That is M6, gated on
**G4**, which is still unanswered. Build the slot, leave the destination unset
with a TODO; do not invent a conversion action.

One to check rather than assert: the deck's footer says *"Data from CRMLS and
partner MLSs"*, where `help-content.ts` was corrected to CRMLS / Southern
California only. Whether "partner MLSs" is true is a question for Jerry, not a
copy edit.

### 2.3 The wizard deck is a product change, and ADOPTION says so

ADOPTION is explicit that the one-page-per-kind idea *"is not load-bearing…
Both fit a four-step wizard."* Read against the deck, what it actually commits
to is bigger than a restyle in four places:

| Deck | Live | What it is |
|---|---|---|
| "Who's reading it? Sellers get the value story. Buyers get the neighborhood story. Same data, different first page." | property wizard has 4 steps: Property, Comparables, Theme & Pages, Generate | **a new step and a new report variant** |
| "Public page + QR code — homeowner scans, enters their phone, gets the PDF" | `/cma/[code]` exists as its own funnel | a step that wires an existing public surface into the wizard |
| "Uses 1 of your 1 remaining property reports this month." | the property wizard shows the limit **nowhere**; it discovers it as a generic error after submit (§3.2) | plan usage plumbed into the wizard **before** the work |
| "This one's free and doesn't count toward your 3 a month." | no such exemption exists in `services/usage.py` | **a billing rule that does not exist — [JERRY]** |
| "Pages {{ pageCount }} of 6" | `COMPACT_PAGES` and `FULL_PAGES` are 9 pages | a count mismatch to resolve |
| the onboarding flow ("Two minutes… Send it to yourself first… Keep it going every month") | `onboarding/guided-get-started.tsx`, 553 lines, live at `/app/get-started` | overlaps a surface that already exists |

The market-report half of the deck is genuinely a restyle. The property half is
a feature.

---

## 3 · What the wizards carry

Enumerated before judging, as asked.

### 3.1 Unified wizard — `/app/reports/new`, `/app/schedules/new`, `/app/schedules/[id]/edit`

- **Step count is conditional, not four.** `effectiveSteps = needsAudience ? [0,1,2,3] : [0,2,3]`
  (`index.tsx:97`) — the audience step appears only for report types with
  `hasAudienceStep: true`. Five of eight types skip it. *The product has a
  three-or-four-step wizard, not a four-step one*, and any proposal measured
  against "our four-step flow" is measured against something we do not quite have.
- **One component, three intents**: send-now, create-schedule, edit-schedule,
  switched by `defaultMode` and `scheduleId`.
- **Report type** — eight entries in `types.ts`, one `disabled: true`.
- **Audience** — presets from `AUDIENCE_FILTER_PRESETS`.
- **Area** — city (combobox) or up to N ZIPs, five-digit validated.
- **Lookback window** — per-type `defaultLookback`.
- **Cadence** — weekly (day-of-week) or monthly (day-of-month), timezone,
  schedule name, recipients.
- **Branding and profile**, fetched from three endpoints and used for the live
  email and PDF previews.
- **Theme** — *not chosen here.* `themeId` is seeded from the account's
  `default_theme_id` (`index.tsx:135`) and never offered to the reader. Theme
  selection lives in the property wizard and in Settings → Branding.
- **Plan limits** — a dedicated `limit_reached` state, with used/limit read off
  the 403 and an upgrade line. **Discovered at the end**, after all four steps.
- **Verification** — a distinct `verification_required` state (D-019), because
  "Try Again" is the one action that cannot help.
- **No account-type branching anywhere in it.** `account_type` does not appear
  in either wizard; role gating is `middleware.ts` plus the separate
  `/app/company` and `/app/affiliate` trees.

### 3.2 Property wizard — `/app/property/new`

Four steps: Property, Comparables, Theme & Pages, Generate.

- **Address lookup** against SiteX, with the full record forwarded to the worker
  so the wizard path and the lookup path agree (D-118's comment at
  `step-generate.tsx:128`).
- **Comparables** — status filter, sqft tolerance, radius, fallback level,
  per-comp include/exclude, map modal.
- **Theme** — three themes, accent colour with live contrast metrics, page
  selection.
- **Pages** — `theme.compact ? COMPACT_PAGES : FULL_PAGES` (`property-wizard.tsx:271`).
  **The two lists are byte-identical** (9 pages each). A branch that selects
  between two identical things, on a flag (`compact`) that differs per theme.
- **Plan limits: nothing.** `step-generate.tsx:162` turns every non-OK response,
  403 included, into `new Error(errData.detail || "Failed to create report")`.
  A Free account that has used its one property report this month gets a generic
  red card at the end of a four-step flow. No `limit_reached` state, no upgrade
  line, and **no verification state either** — D-019's remedy exists on one
  wizard and not the other.
- **Two seeds of a retired theme.** `useState(4)` (`:61`) and
  `useRef({themeId: 4})` (`:68`) are both `teal`, retired 2026-10-05. The fix at
  `:80` only covers the *successful* branch of the account fetch; `if (!res.ok) return;`
  and the `catch` leave 4 in place. With `selectedThemeId === 4`, `THEMES` (ids
  2, 3, 5) matches nothing, so **no theme card shows as selected** and
  `handleReset()` restores that state. What is submitted is safe — the
  `selectedTheme` memo falls back to `DEFAULT_THEME_ID` — so the reader picks
  nothing, sees nothing selected, and gets atlas.

### 3.3 Nobody has walked either flow, and that is confirmed

- `/app/property/new` **is not in the render manifest** at all. `/app/reports/new`
  and `/app/schedules/new` are, at `h1` depth and one viewport.
- No e2e spec touches a wizard (`e2e/` is auth, plan, stripe, affiliate).
- The one jest file naming a wizard is §0.1's.
- The three decisions that make a wizard a wizard — the conditional audience
  step, the end-of-flow limit refusal, the theme seed — are each invisible to
  every gate we have.

---

## 4 · Order and size

**Marketing first**, and the scope agrees with the ticket's instinct, with one
item hoisted in front of it.

### Step 0 — Frontend Tests back to green · 1 PR, small

Before either surface, because it is the thing that would catch a regression in
either, it has been red for four months, and nothing else can be said to be
"verified" on the web side until it is. Four suites, three causes, none deep:
wrap two tests in a `QueryClientProvider`, retarget `NewSchedulePage` at the
component the page actually renders (and delete the three self-asserting tests
or make them read `types.ts`), and reconcile `TemplatesMapping` against the
builders as they are now. Each failure seen to fail before and after.

### Step 1 — the harness reaches the public pages · 1 PR, small

Manifest rows for the ten public routes, an optional-token mode so a prospect's
view is expressible, a second viewport at 390px with `compare()` keyed on it,
and a text probe that does not drop sentences. Then a before-run, so the
redesign has a baseline. **This is cheap and it is what makes everything after
it reviewable.** `/docs`'s 70px overflow is the first thing it will report.

### Step 2 — the landing adoption · 2 PRs, medium

Paint and reversible, as you said. Split because the two halves have different
risk:

- **2a, copy and claims** — resolve the three reintroductions (Open Houses,
  Status, "350+ cities"), map the deck's Jennifer Martinez onto `demo-data.ts`
  rather than inlining a second demo identity, and build the sponsor slot with
  its destination unset and a TODO pending **G4**.
- **2b, the restyle** — section by section against the Step 1 baseline.

### Step 3 — the wizards, measurement before anything moves · 1 PR, medium

The walk-through you asked for, as an artefact rather than a diff: both flows
end to end, every step, at both viewports, on at least a Free account and an
unlimited one — so that the limit refusal, the conditional audience step and
the theme seed are all on the record *before*. `/app/property/new` joins the
manifest. This is the "end-to-end measurement" ADOPTION's item 10 is waiting on,
and it is the before-half of before-and-after.

### Step 4 — the wizard restyle · size unknown until Step 3

The market half is a restyle and could be sized now. The property half is a
feature — a new audience step, a new report variant, usage plumbed into the UI,
and a free-first-report billing rule that does not exist. **Not sizeable until
Steps 3 and the [JERRY] answers land**, and not to be started as if it were
paint.

**Gated, not to be guessed:** G4 (what a title company buys, and the sponsor
CTA's destination); the free-first-property-report exemption; whether "350+
Southern California cities" and "partner MLSs" have sources.

---

## 5 · Findings to file from this scoping

Filed on the board, not worked, per the ticket. Board after this scoping:
**218 entries, open 79, fixed 132** — BROKEN 6 · WRONG 22 · FRAGILE 22 · ROUGH 29,
re-derived with `scripts/derive.py`.

| # | Severity | What |
|---|---|---|
| **D-211** | **BROKEN** | Frontend Tests has never passed; 13 of 54 fail identically in CI and locally; every `apps/web` change for four months merged with its gate red |
| **D-212** | WRONG | `NewSchedulePage.test.tsx` asserts a literal against itself in three tests and mocks a component the page stopped using |
| **D-213** | WRONG | the property wizard turns a 403 limit refusal into a generic error — no limit state, no upgrade line, no verification state, at the end of a four-step flow |
| **D-214** | FRAGILE | the property wizard seeds `themeId = 4` (retired `teal`) in two places; on a failed account fetch no theme reads as selected and `handleReset` restores it. **D-174 in TypeScript** — the gate written for D-174 parses `.py` only |
| **D-215** | ROUGH | `COMPACT_PAGES` and `FULL_PAGES` are byte-identical; the `theme.compact` branch selects between two identical lists |
| **D-216** | ROUGH | `/docs` overflows 70px at 390px on an unwrapped `curl` block |
| **D-217** | ROUGH | 2,882 lines of orphaned wizard components with no importer, two of them exported from barrels |
| **D-218** | ROUGH | `testimonials.tsx` survives as dead code — three fabricated people, one import from being live again |

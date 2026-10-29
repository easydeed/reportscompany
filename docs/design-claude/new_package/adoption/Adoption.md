# Adoption guide — getting the new look onto the existing `apps/web` components

Answers the 2026-10-15 engineering review, in its order. Companion: `tokens.css` (drop-in `:root`).

## First, a measurement note

The package in `design_handoff_product/` has **9 files, no Tailwind config, no Button, no Card**. The `.dc.html` files are design references rendered by `support.js`; they are not a frontend and were never meant to be mounted. The "96 files / parallel application" reviewed is not this folder — same situation as the market package on 10-06. Please confirm the path before planning against it; the sizing below assumes you adopt the look onto your 174 components, which is also what we intended.

That said, your framing is the right one. Here's the honest split.

## 1 · Token set

`tokens.css` in this folder is a replacement for the `:root` block in `app/globals.css`, variable names preserved (plus ~25 `NEW` names you can ignore until something uses them). Beyond the variables, three base rules change:

```css
body { font-size: 15px; line-height: 1.5; }                 /* was 14 / 1.6 */
h1   { font-size: 34px; font-weight: 800; letter-spacing: -0.03em; line-height: 1.1; }
a    { color: var(--link); } a:hover { color: var(--link-hover); }
```

**What tokens alone buy you (≈70% of the visual distance):**
- Light warm sidebar instead of dark — one variable group (`--sidebar-*`).
- Ink primary buttons instead of indigo (`--primary`). Indigo becomes link-only.
- Warm neutrals (`#E4E2DA / #ECEAE3 / #FAFAF7`) instead of cool slate greys — the thing people describe as "it looks calmer".
- Flat cards (`--shadow-card: none`, border `#E4E2DA`, radius 16).
- 15px body, heavier/tighter headings.

**What tokens can't buy:** page structure (what's on the dashboard, groups-as-filters on Contacts, wizard right column), and the embedded live report. Those are section 2.

## 2 · Which components differ structurally

Audited against `components/ui/*` and the page files listed in `README.md`. Three buckets.

### A · Restyle only — same markup, same behaviour (your component, new clothes)
| yours | change |
|---|---|
| `ui/button` | `default`: `bg-primary` now resolves to ink — no code change. `rounded-md` → `rounded-[10px]`; height `h-9` → `h-11` (44px) for primary, keep `h-9` for row actions; `font-medium` → `font-semibold`; `outline`: white bg + `--border`, no shadow-xs; add `disabled` style text `#94A3B8` on white with border (instead of opacity 50) |
| `ui/card` | `rounded-xl` → `rounded-2xl`, `shadow-sm` → none, `py-6/px-6` → `p-5` or `p-6`; `CardTitle` 17px/700 |
| `ui/input` | `rounded-lg` → `rounded-[10px]`, `h-11` keep, `text-base` keep (15–16px), border `--border`, focus ring `0 0 0 3px var(--ring-alpha)` + border `--ring` |
| `ui/badge` | becomes the status pill: `rounded-md` → `rounded-full`, `px-2 py-0.5` → `px-[9px] py-[3px]`, `font-medium` → `font-semibold`, text 12px. Add variants for the semantic pairs in `tokens.css` (`opened / sent / bounced / running / hot / new / clicked`) — `clicked` reads the agent accent |
| `ui/switch` | 36×20, track `--success` on / `--disabled` off (not `--primary`) |
| `ui/table` | row rule `--border-subtle`, head 11–12px uppercase `--muted-foreground` 700 tracking 0.08em, cell `py-3` not `p-2`, tabular-nums on numeric columns, hover bg `--surface-cream` |
| `ui/tabs` | the pill-row look: on = ink bg / white text; off = white / `#475569` / `--border`. Markup unchanged |
| `ui/dialog`, `ui/select` | radius 16 / 10, `--shadow-elevated`, border `--border`. Nothing else |
| `site-nav.tsx` | colours + heights only; the link set is the same (Reports, Pricing, Log in, Start free) |
| `components/branding-form.tsx` | form unchanged; wrap in the two-column grid and mount the existing report preview in the right column |
| `settings/profile`, `settings/security` | fields unchanged; they merge onto one page (that's a routing/layout change, not a component one) |
| `app/app/help/*`, `app/app/admin/page.tsx` | tokens + card radius only |

**Count: 14 components / pages, zero structural work.**

### B · Same component, one structural change (keep the file, edit it)
| yours | what actually changes |
|---|---|
| `app/app-layout.tsx` (sidebar) | Light theme is tokens. Structural: **"New report" primary button at the top of the rail**; three group labels (Reports / Engage / Account); usage block (three bars) above the account row; Help moves to the rail bottom. Nav item markup itself is the same `<a>` + icon + label |
| `dashboard/dashboard-content.tsx` | Replace the stat tiles with: sentence title, "Latest report" card (embeds the report preview you already have in `shared/pdf-preview`), "Next send" row, "Call these first" list. Data sources already exist; it's a re-composition of existing pieces |
| `app/app/reports/page.tsx`, `property/page.tsx`, `schedules/schedule-table.tsx` | Tables keep `ui/table`. Add a filter-pill row above (reuse `ui/tabs` restyled) and the kind thumbnail cell (56px `pdf-preview` at scale). Schedules: switch moves into column 1 |
| `app/app/people/page.tsx` (Contacts) | Groups become filter pills over the same list (drop the Groups tab). Add a **detail drawer** (new, see C) and move "Add contact" from modal to inline panel — the form fields are the same |
| `settings/billing/page.tsx` | Plan cards + inline confirm panel replace the dialog; usage/payment/invoices blocks exist already |
| `lead-page-client.tsx` | Settings fold inline under "Customize" instead of a separate panel; leads table gains the state pill + filter pills |
| `cma/[code]/cma-funnel.tsx` | Keep your step machine (address → confirm → contact → success). Change: one question per screen, the cover artifact on every step, consent checkbox, Call/Text buttons on success. The data flow is yours |

**Count: 7 files with bounded edits.**

### C · Genuinely new structures
1. **Contact detail drawer** (340px sticky column ≥1100px / overlay below). New component; small.
2. **Embedded live artifact column** in the wizard shell (right column, scaled 816×1056 page that updates per step). You have `shared/pdf-preview/layouts/*` — this is a mount + the scaling rule in `README.md`, but the wizard shell itself is restructured. **Deferred per your note** until the four-step flow is measured; nothing in A or B depends on it.
3. **Comps map** (Leaflet, subject + toggleable comp pins). New; only needed by the property wizard, so deferred with it.
4. **Progress checklist** ("working" state with real stage names). New, ~40 lines; used by the wizards, Home Value Page processing step, and CSV import.
5. **Madlib summary** (choice slots that jump back a step). Wizard-only; deferred.
6. **Brand swatch picker** (diagonal primary/accent swatch, 4 or 6 options). New, tiny; used by Branding, onboarding, landing hero.

**Count: 6, of which 3 are wizard-bound and deferred.** Live now: drawer, progress checklist, swatch picker.

So: 14 restyles, 7 bounded edits, 3 small new components, 3 deferred. Not 73 routes.

## 3 · Order of adoption

Your guess is right with one amendment: tokens before shell.

1. **Tokens** (`tokens.css` + the three base rules). Half a day. Every route changes at once and nothing breaks structurally — but see §4 for the one thing that looks wrong immediately.
2. **`ui/*` restyles** (bucket A). One day. Button / Card / Badge / Input / Table / Tabs / Switch.
3. **Shell**: `app-layout.tsx` sidebar structure (New-report button, groups, usage, Help). One day. After this the product reads as the new design on every route even where page content is old.
4. **Dashboard**. Highest-value single page; the first thing every session sees.
5. **Reports / Property / Schedules lists** (filter pills + thumbnails). Mechanical once Tabs and Badge are done.
6. **Contacts** (pills, inline add, drawer, CSV steps).
7. **Billing, Settings merge, Lead page.**
8. **Landing** — independent of everything above; can be done any time by whoever owns marketing. Token-wise it shares everything.
9. **Home Value Page** — independent too; worth doing early if lead volume matters, since it's the only surface a non-customer sees.
10. **Wizards + comps map** — after your end-to-end measurement.

## 4 · What breaks under partial adoption

Mostly nothing — the old and new share the same font and ink colour, so mixed pages look unfinished rather than broken. Three real conflicts:

- **Dark sidebar next to new content** (or new sidebar next to old content) is the only combination that looks like two products. Ship tokens step 1 and the sidebar step 3 within the same release window; don't leave a dark rail over cream/flat cards for weeks.
- **Indigo primary buttons next to ink ones.** `--primary` flips globally in step 1, so this can only happen where a component hard-codes `bg-indigo-*` or `#4F46E5`. Grep for both before step 1; anything found is either a link (keep indigo) or a button (use `--primary`).
- **Old shadowed cards (`shadow-sm`) inside a new flat page** read as floating. Card restyle is in step 2 for that reason — do it with tokens if you can.
- **Old `Badge` (rounded-md, indigo fill) next to new status pills** on the same table. Harmless but visible; Badge is a ten-minute change, do it in step 2.
- Cool slate (`#F8FAFC`, `#E2E8F0`) backgrounds hard-coded in page files will look blue-grey against the warm tokens. Grep for `slate-` and `#F8FAFC`/`#E2E8F0`/`#F1F5F9`; replace with the `--muted` / `--border` tokens.

Combinations that are fine indefinitely: new shell + old page content; new tables + old dialogs; old wizard behind the new shell; old landing with the new app.

## Two findings

- **Sidebar contrast.** Yours is `--sidebar-muted #475569` on `#0F172A` (3.4:1). `tokens.css` sets it to `#64748B` on `#FAFAF7` (4.6:1). The package had a parallel miss — the 11px group labels were `#94A3B8` on cream (2.5:1); fixed in `App v3.dc.html` to `#64748B` as of this note. Rule going forward: `#94A3B8` is for placeholders and decorative icons, never text. `#64748B` is the lightest text colour.
- **Index keys.** The `.dc.html` files' list repeater keys by index by design (it's a preview runtime, not shipped code), so nothing from the package will carry that into your build. In the spec, every row that holds in-flight input (Contacts drawer, schedule switches, comps checkboxes, group pills) must be keyed by record id — added to `README.md` under "Build notes". Your admin table finding is in your code, not the package; agree it should be fixed there.

## Constraints that aren't free choices (what you asked for last)

The app surface has fewer of these than the PDFs, but they exist:

1. **Agent brand never touches chrome.** `--agent-primary / --agent-accent` are read only by the embedded report, the brand swatch picker, the account initials circle and the `clicked` pill. If a route needs a saturated colour on UI it uses ink or `--link`, never the agent's. Reason: the same screen shows the agent's brand inside the artifact; brand on chrome makes the artifact disappear.
2. **The embedded report is a fixed 816×1056 page, scaled — never reflowed.** Any thumbnail or preview is `transform: scale()` of the real page. A responsive re-layout of the report is a different document and would diverge from the PDF the client receives.
3. **Status pills are semantic pairs, fixed** (`tokens.css`). `opened/done/called` green, `sent` grey, `bounced/failed` red, `hot` amber, `new/lead` ink. Don't derive them from brand or theme.
4. **Numbers in copy are derived.** "3 reports left on Free", "64 opened", "resets Nov 1", "goes out Oct 1 to 107 contacts" — every number in a title or lead sentence is computed from plan limits, usage and schedule state. No sentence should ship with a literal number in it. Absence rules follow the PDF packages: show "—" or "Nothing scheduled", never 0 as a fake value.
5. **Disabled is a colour, not an opacity.** `disabled:opacity-50` on top of cream drops below 3:1. Disabled buttons: `#94A3B8` text, white bg, `--border` border.
6. **Sentence titles replace page names** where state exists (dashboard, done states). If the state can't be computed, fall back to the page name — don't ship a sentence with blanks.
7. **The light sidebar makes the page white and the rail cream**, not the reverse. If a route forces a grey page background the rail disappears into it.
8. **Home Value Page carries no product branding.** No logo, no "powered by", no product colour — only the agent's `brand_hex` and name. Consent copy is legal's, not ours; the layout holds three lines at 12px.

## Wizards

Agreed on sequencing. For when you measure: the one-page-per-kind idea is not load-bearing. What the redesign actually commits to is (a) the real report on screen from step 1 and (b) one sentence per step. Both fit a four-step wizard. If end-to-end testing says four steps work, keep them and adopt (a) and (b); the madlib and the kind cards are optional on top.

# App v3 — implementation drop-ins

Written 2026-10-22 against `main` as of 18:22Z. These are real TSX files on your paths, using your hooks, your Radix primitives, your `cn`, your route table and your tier logic. Copy them over the existing files (paths under `code/apps/web/…` mirror the repo). They compile against what's in the repo today; the only new dependency is nothing — `lucide-react`, `@radix-ui/react-switch`, `next/navigation` are all already there.

## Why the last pass missed

Tokens landed (`globals.css` is correct), `ui/button`, `ui/card`, `ui/badge` landed. What didn't:

1. **The shell is still the shadcn Sidebar + a 56px topbar.** App v3 has no topbar. The account menu is a row at the bottom of the rail; the "New report" button is the first thing in the rail; the nav is three flat groups with no collapsibles (Settings / Admin accordions are gone); Help sits above the usage block at the bottom; the content column is `max-width 1120px`, `padding 44px 48px 80px`. The rail is 236px, not 256. Nav items are 14px / 38px rows, group labels 11px / 0.1em. None of that is a token.
2. **`PageHeader` is still 20px / 600.** Every page title in the design is 34px / 800 / -0.03em with a 16px sub-line. One file, every route.
3. **Lists are still boxed `ui/table` cards** with a tinted header row, outer border, radius and a "Showing N" footer. The design's lists are open: a 1.5px ink rule on top, an 11px uppercase header, hairlines between rows, cream hover, no box, no footer. Reports rows carry a 72px page thumbnail.
4. **Dashboard** was re-composed into three `Card`s with a stacked "Latest report" preview at natural width. The design is: sentence title + 17px lead, then a two-column grid — left: the report as a tilted physical object (360px, −2°, page shadow) with "PDF / Share" under it; right: Next send (cream row with a green dot), Call these first (avatar rows), Recent (text rows). The limit alerts, onboarding checklist and `PageHeader` action button are not on it; the limit lives in the lead sentence.
5. **`StatusBadge`** still uses `emerald-50 / slate-50 / amber-50` Tailwind pairs for most states, with a border. The design pairs are the `--success-muted` etc. tokens, 12px / 700, no border.
6. **Switch** is the default 32×18 primary-coloured one; design is 40×24, green on.

## Files in this folder

| path | replaces | status |
|---|---|---|
| `app/app-layout.tsx` | same | full rewrite. Same exports (`default`, `isBuilderRoute`), same props, same tier matrix, same builder-route logic. `ui/sidebar.tsx` is no longer imported by it (leave the file; nothing else breaks). `AccountSwitcher` moves into the rail above the account row. `useBranding` is read for the avatar colour. |
| `components/page-header.tsx` | same | full rewrite, same props (`title` now accepts a ReactNode). Every page that passes `description` as a marketing line ("Manage and generate your market reports") should pass a derived count or nothing — see Reports for the pattern. |
| `components/status-badge.tsx` | same | full rewrite, same props + optional `accent` for the `clicked` state. Labels change: `completed → Done`, `processing → Running`, `inactive → Paused`. |
| `components/ui/list.tsx` | new | `SectionLabel`, `RuleList`, `ListHeader`, `ListRow`, `Cell`, `Text`, `IconButton`, `FilterPills`, `ListEmpty`. The list vocabulary for every table in the app. |
| `components/ui/switch.tsx` | same | sizes/colours only. |
| `components/shared/report-thumb.tsx` | new | `SharedPDFPreview` pinned at 480 and transform-scaled to any width (constraint #2). Used at 360 (dashboard) and 72 (list rows). |
| `components/dashboard/dashboard-content.tsx` | same | full rewrite. Reads `?from=onboarding&city=&autopilot=` for the first-run state. Drops `MetricCard`, `Alert`, `DashboardOnboarding` imports; if `DashboardOnboarding` must survive for sponsored accounts, mount it under the grid. |
| `app/app/reports/page.tsx` | same | full rewrite on `list.tsx`. Assumes `Report.schedule_name` may exist (used for the Sent/Manual filter and row sub-line); if the API doesn't return it the filter still works, every row just reads "Manual" — add the field to `/v1/reports`. |
| `components/schedules/schedule-table.tsx` | same | full rewrite, same props. The page wrapping it should use `PageHeader` with `description={`${active} active · next send ${date}`}` and the "New schedule" button as action; the table now owns the footnote. |
| `components/auth/auth-frame.tsx` | new | `AuthFrame`, `AuthError`, `AuthSubmit` + three class strings. One-column auth layout on the cream ground, white 420px card, app h1. Replaces the dark `#1E293B` split panel on both auth pages. `forgot-password`, `reset-password` and `verify-email` should move onto it too (same move, not included). |
| `app/login/page.tsx` | same | full rewrite, same endpoint/cookie/redirect. Drops the unread "Keep me signed in" checkbox and the `console.log` timing lines. `Checkbox` import gone. |
| `app/register/page.tsx` | same | full rewrite, same endpoint/payload/redirect. Benefits list and dark panel gone; terms checkbox (never enforced) becomes a sentence under the button; password hint now matches the one rule the code checks (8+). `Checkbox`/`Check` imports gone. |

## Then, the same move on the pages not included here

Each is the identical transformation — `PageHeader` + `FilterPills` + `RuleList` rows — and the full content spec is in `../README.md`:

- **Property reports** (`app/app/property/page.tsx`): header "Property reports" / "{n} this month · {views} page views · {leads} leads"; address input (50px, 1.5px `--border-strong`, map-pin glyph) as the primary way in; columns `minmax(0,1.8fr) auto minmax(0,1fr) auto auto 112px` — Property (address / city · value), For (Seller `#EEF2FF/#3730A3` · Buyer `#F1F5F9/#334155` tag), Created, Views, Leads (bold when > 0), actions (Download · QR tone=link · Delete tone=danger).
- **Home-value page** (`lead-page-client.tsx`): README §Home-value page. Left column: Your link row (cream URL box + ink Copy + outline open) · QR + "Download PNG" · "Customize" toggles an inline cream settings card (headline, subheadline, colour swatches, Save) · lead filter pills `All · n / Hot · n / Called · n` · lead rows (address / phone · views · when, state pill, 38px ink Call button `tel:`). Right column: the phone mockup of the page.
- **Contacts** (`people/page.tsx`): README §Contacts. Groups as filter pills (not a tab); search right-aligned 260px; inline Add contact card; inline 3-step CSV import card; detail drawer 340px sticky ≥1100px. Rows `44px minmax(0,1.4fr) minmax(0,1.4fr) minmax(0,1fr) auto`.
- **Branding** (`branding-form.tsx`): wrap in `grid-cols-[minmax(0,1fr)_minmax(0,1fr)]`, the form left, `<ReportThumb width={420} …/>` right, fed by the form's live values. No separate preview button.
- **Plan & billing** (`settings/billing/page.tsx`): README §Plan & billing — three plan cards (current = 1.5px ink border, white; CTA disabled "Current plan"), inline confirm card, usage rows (same `UsageRow` as the rail), payment, invoices list, cancel line.
- **Settings**: merge profile + security + notifications into one `max-w-[720px]` page per README §Settings; inline email / password editors.
- **Help / Admin**: `PageHeader` + `RuleList` rows; admin metrics as 6 plain cells (`text-[28px] font-extrabold tabular-nums` + label), not `MetricCard`.

## Things to delete once these are in

- `components/metric-card.tsx` usages on dashboard/admin (the design has no count tiles outside Admin, and Admin's are plain).
- The topbar tier badges ("ADMIN", "TITLE REP"…). Role is the 12px line under the name in the rail.
- Any `bg-muted/40` table header rows, `rounded-xl border` table wrappers, "Showing N …" footers.
- `.gradient-trendy`, `.shimmer` in `globals.css` — nothing in the design uses them. The `[data-sidebar]` dark scrollbar block should flip to `#CBD5E1 / #94A3B8` (the rail is light now).

## Checks before you call it done

Open `App v3.dc.html` (in `../`) beside the running app at 1280px and compare the Dashboard, Market reports and Schedules routes. Specifically: rail width 236 and cream; no topbar; h1 34px; list rows with the 1.5px top rule and no outer box; report rows have a page thumbnail; status pills with no border; "Nothing scheduled" never "0".

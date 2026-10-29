# Handoff: Product surfaces — Landing, App shell, Wizards, Home Value Page

Repo: `easydeed/reportscompany` · Surface: `apps/web` (Next.js) · Design date: 2026-10-06
Companion packages: `design_handoff_market_reports/` (7 PDF market report types) and `design_handoff_property_report/` (6-page property report / consumer CMA). Read `../DESIGN_HANDOFF.md` for the index across all three.

## Principle

The artifact does the talking. Every screen in this package puts the real report (market page or property cover) on screen, live, and cuts the words around it to one orienting sentence per step. If a screen needs a paragraph to explain itself, the design is wrong — fix the artifact or the control, not the copy.

Concretely:
- Every wizard step renders the actual report on the right, updating as the user picks. There is no "preview" step.
- Dashboard leads with the last report sent and who opened it, not four count tiles.
- Landing page sections are a headline + one sentence + a real report. No feature-icon grids.
- Home Value Page shows the cover of the homeowner's own report un-veiling as they answer.

## About the design files

`.dc.html` files are design references built in HTML. Open any of them in a browser with `support.js` beside it (no build step). They are not React components to copy; they show intended layout, copy, states and behaviour. Each has a Tweaks panel (top-right in the preview) to switch states — those switches are listed per file below. Sample data (Jennifer Martinez / Jennifer Realty, Irvine, the contact list, numbers) is invented; the structure is not.

The product files embed the report designs from the companion packages: `Report Page.dc.html` (market) and `Property Report Cover.dc.html` → `Property Report.dc.html` (property). Keep all files in one folder — `Wizards v3`, `App v3`, `Landing v4` and `Home Value Page` import them by relative name.

| file | what it is | repo files it replaces / informs |
|---|---|---|
| `Landing v4.dc.html` | Marketing home, full page | `components/marketing-home.tsx`, `site-nav.tsx`, `marketing/hero.tsx`, `how-it-works.tsx`, `pricing.tsx` |
| `App v3.dc.html` | Authenticated app shell + 11 pages | `app/app-layout.tsx`, `components/dashboard/dashboard-content.tsx`, `app/app/reports/page.tsx`, `app/app/property/page.tsx`, `components/schedules/schedule-table.tsx`, `app/app/lead-page/lead-page-client.tsx`, `app/app/leads/page.tsx`, `app/app/people/page.tsx`, `components/branding-form.tsx`, `app/app/settings/billing/page.tsx`, `settings/profile/page.tsx`, `settings/security/page.tsx`, `app/app/help/help-content.ts`, `app/app/admin/page.tsx` |
| `Wizards v3.dc.html` | Four flows in one shell: onboarding, new report, new schedule, property report | `components/unified-wizard/*` (types, step-story, step-audience, step-where-when, step-deliver), `components/property-wizard/types.ts`, `components/onboarding/guided-get-started.tsx`, `setup-wizard.tsx` |
| `Home Value Page.dc.html` | Public homeowner funnel (`/cma/[code]`) | `app/cma/[code]/cma-funnel.tsx`, `app/cma/[code]/page.tsx` |
| `comps-map.html` | Leaflet / OpenStreetMap comps picker, iframed by the property wizard | new; no equivalent today |
| `Report Page.dc.html` | Market report page (dependency) | see `design_handoff_market_reports/README.md` |
| `Property Report.dc.html`, `Property Report Cover.dc.html` | Property report (dependency) | see `design_handoff_property_report/README.md` |

## Fidelity

High-fidelity for layout, type, colour, copy, states and interaction. Responsive behaviour is designed down to ~360px on Landing and Home Value Page; App and Wizards are designed for ≥1100px with a documented collapse below (see each section). Nothing in this package is a wireframe.

---

## Shared system (all four product files)

### Type
One family: **Plus Jakarta Sans** 400 / 500 / 600 / 700 / 800 (Google Fonts). Body 15px / 1.5 in the app and wizards, 16px / 1.6 on Landing and Home Value Page. Page titles 34px / 800 / `letter-spacing: -0.03em` / `line-height: 1.1`. Section labels 11–12px / 700 uppercase `letter-spacing: 0.08em`. Mono is not used on product surfaces — it belongs to the PDFs.

### Colour
Neutrals (fixed):
- Ink `#0F172A` · body `#334155` · secondary `#475569` · muted `#64748B` · placeholder `#94A3B8` · disabled `#CBD5E1`
- Cream page `#FAFAF7` (Landing, Home Value Page, open drawer row) · app page `#FFFFFF` · panel `#ECEAE3` (active nav, inactive step dot) · band `#EEEDE7` (landing footer) · rules `#E4E2DA` (borders, pills off) and `#ECEAE3` (section rules) · dark band `#0F172A`
- Links `#4F46E5`, hover `#3730A3`. Define on `a` globally — users will add links.

Product accent (the app's own UI, not the agent's brand): indigo `#4F46E5` for the primary CTA on Landing and the current-step marker in the madlib summary. Inside the app, primary buttons are **ink** `#0F172A` on white, not indigo — the agent's brand colour is the only saturated colour on authenticated pages, and it lives in the artifact.

Agent brand themes (App, Wizards, Landing picker) — `[primary, accent]`, applied only to the embedded report and the brand swatch picker:
- navy `#18235c` / `#0d9488`
- indigo `#4F46E5` / `#D97706` (default)
- green `#14532D` / `#CA8A04`
- wine `#7F1D1D` / `#DB2777`

Property brand set (Wizards property flow, Home Value Page) — from `tests/golden/themes.json`: red `#DC2626`, teal `#0D9488`, cyan `#0E7490`, amber `#F59E0B`, lime `#84CC16`, violet `#7C3AED`. Themes elegant / bold / modern per the property package.

Status pills (text / background), semantic and fixed:
- Opened / Done / Called `#065F46` on `#D1FAE5`
- Clicked: white on agent `accent`
- Sent `#64748B` on `#F1F5F9`
- New lead / New: white on `#0F172A`
- Bounced / Failed `#991B1B` on `#FEE2E2`
- Running `#1E40AF` on `#DBEAFE`
- Hot `#92400E` on `#FEF3C7`
- Seller / Buyer type tag `#3730A3` on `#EEF2FF` / `#334155` on `#F1F5F9`
- Pill: 11.5–12px / 600, `padding: 3px 9px`, `border-radius: 999px`.

Usage bars: `primary` fill; `#D97706` at ≥80%; `#B91C1C` at 100%.

### Controls
- Filter pill (toggle): on = `#0F172A` bg / white text / `#0F172A` border; off = white / `#475569` / `#E4E2DA`. 13px / 600, `padding: 7px 12px`, 999px.
- Radio: 18px circle, selected = `6px solid #0F172A` ring; unselected `1.5px solid #CBD5E1`. Label 700 when selected.
- Switch: 36×20, track `#059669` on / `#CBD5E1` off, white 14px knob at `left: 19px` / `3px`.
- Primary button: `#0F172A` bg, white, 14px / 700, `padding: 12px 18px`, radius 10px. Disabled: `#94A3B8` text on white with `#E4E2DA` border. Secondary: white, `#0F172A`, `1px solid #E4E2DA`.
- Text input: 15px, `padding: 12px 14px`, `1px solid #E4E2DA`, radius 10px, focus ring `0 0 0 3px rgba(79,70,229,0.18)` + border `#4F46E5`.
- Cards: white, `1px solid #E4E2DA`, radius 16px, `padding: 20–24px`. No shadows on cards. Shadow only on floating things (drawer overlay, map pins).
- Step dots (wizards, CSV import): 22px circle; current `#0F172A` / white; done `#D1FAE5` / `#047857` with "✓"; upcoming `#ECEAE3` / `#64748B`.
- Progress checklist (every "working" state): rows with a 20px circle — done `#047857` filled with white check; active `2px dashed #0F172A` ring spinning (`@keyframes tr-spin` / `hv-spin`, 1.4s linear); upcoming `1.5px solid #CBD5E1`. Each line is a real stage name, ticked at 1s intervals in the design; wire to actual job stages.
- Icons: Lucide (`lucide-static@0.460.0`), 16–18px, rendered via CSS mask so they take `currentColor`. No other icon set, no emoji.

### Embedded artifact scaling
The report is rendered at its true 816×1056 size and scaled with `transform: scale(s); transform-origin: top left`, where `s = clamp(0.2, min(520/816, (w − 64)/816, (h − 116)/1056))` against the available right-column box. Re-measure on resize. Never re-flow the report at a smaller width — it's a fixed-page document.

---

## Landing v4 (`Landing v4.dc.html`)

Max content width 1120px, `padding: 0 24px`. Cream `#FAFAF7` page; alternating sections sit on white with a `1px solid #ECEAE3` top rule. Nav: logo left; "Reports", "Pricing", "Log in", "Start free" (ink button) right; collapses to logo + "Start free" under 720px.

Tweaks: none (interactive state is in-page: city input, theme swatch, report carousel).

### Sections, in order
1. **Hero** — h1 "Market reports your clients actually open." (56px / 800 / −0.04em, 40px under 720px) · one sentence: "Live MLS data. Your brand. Sent to your sphere every month, on autopilot." · city input + CTA ("Get my free report" → "Get my {city} report" once typed) · four brand swatches (diagonal split primary/accent, 28px, ring on selected). Right: the **real Closed Sales page** for the typed city, rendered from `Report Page` with the chosen theme, inside a soft brand glow (`radial-gradient` of `primary` at 18% opacity, 600px, behind the page; no gradient on the page itself). Typing a city and submitting flips the page to that city's name — this is the first "it's real" moment.
2. **Reports** (`#reports`) — "Seven reports. Pick what your sphere hears about." · carousel of the seven kinds at 340px card width, 28px gap, active card at scale 1 / opacity 1, others 0.94 / 0.45; prev/next arrows and dot-pick; label under the active card "{Kind} — {one-line note}" (notes in `Component.KINDS`). Cards are live `Report Page` renders, not screenshots.
3. **Schedules** — "Set it once. It goes out every month." · one sentence · phone mockup showing the email with the report, on a **dot grid** background (`radial-gradient(#D6D3CB 1px, transparent 1px)` at 18px). Phone is a plain rounded rect (28px radius, `#0F172A` 10px bezel), no device brand.
4. **Property report** — "Type an address. Walk in with a seller report." · property-cover artifact + four comp rows (address, specs, distance, price).
5. **Home-value page** — "A home-value page with your name on it." · phone mockup of the Home Value Page address step on the dot grid.
6. **Contacts** — "See who opened. Call them first." · six-row contact list with status pills.
7. **Pricing** (`#pricing`) — "Free for one city. Pay when you want more." · three plan cards: Free $0 forever "1 city, monthly / 3 reports a month" · Growth $19/mo "Up to 3 cities, weekly / 25 reports a month, CSV import" (recommended — indigo CTA, others ink-on-white) · Growth Plus $29/mo "Any number of cities / Unlimited reports and schedules". All CTAs "Start free". Footnote: "Every plan includes property reports, your lead-capture page and contacts. No credit card to start." The pricing unit is **reports sent per month**; cities and cadence are the plan gates.
8. **CTA band** — "Your first report is two minutes away." on `linear-gradient(135deg, #0F172A, color-mix(in oklch, #0F172A 55%, primary))` — the only gradient on the site, tinted to the picked brand. White text ≥ 7:1 on both ends. City input + CTA repeated.
9. **Footer** on `#EEEDE7`, 4 columns ≥ 900px (brand blurb + support email · Product · Reports · Company), stacks to 2 then 1. Legal line "© 2026 TrendyReports · Data from CRMLS and partner MLSs" + Privacy / Terms / Status.

### Build notes
- Hero report and carousel cards are the same `MarketReportBuilder` output as production — render a cached sample PDF page per kind per theme as PNG/SVG at build time (4 themes × 7 kinds = 28 images) rather than running the builder client-side. The design's live render is to show what it should look like, not how to ship it.
- The city input is not a form post; it only changes the rendered area label until "Start free" is clicked, which carries `?city=` into signup.
- Brand glow and dot grid are decoration behind artifacts only. Page backgrounds stay flat cream/white.

---

## App v3 (`App v3.dc.html`)

Tweaks: `theme` (navy · indigo · green · wine — agent brand), `firstRun` (dashboard straight out of onboarding), `showAdmin` (adds Admin to nav), `showUsage` (usage block in sidebar).

### Shell
Left sidebar 248px, white, `border-right: 1px solid #ECEAE3`, sticky, full height. Logo top (28px). Three nav groups with 11px uppercase labels:
- **Reports**: Dashboard · Market reports · Property reports · Schedules
- **Engage**: Home-value page · Contacts
- **Account**: Branding · Plan & billing · Settings · (Admin, role-gated)
Item: 14px / 500, `padding: 8px 10px`, radius 8px, Lucide icon 16px; active = `#ECEAE3` bg / 700 / ink. Bottom: usage block (three bars: Market reports, Schedules, Property reports with "x / limit" and reset note; "Upgrade" link on Free), then Help and the account row (initials circle in `primary`, name, brand).
Content: `padding: 36px 40px 80px`, `max-width: 1180px`. Under 1100px the sidebar becomes a top bar with a menu button and the contact drawer becomes a fixed right overlay (`min(380px, 92vw)`).

### Pages
**Dashboard** — `dashTitle` is a sentence, not "Dashboard": normal state "Good morning, Jennifer." + one line "Your **Monthly Irvine Snapshot** goes out Oct 1 to 107 contacts. 3 reports left this month on Free." Below, two columns `minmax(0,1fr) 380px`:
- Left: **Latest report** card — the real Snapshot page at ~0.42 scale with "Sent Sep 1 to 107 contacts · 64 opened" and "All reports →"; **Next send** row (green dot, name → recipients, date, "Edit"); **Recent activity** list (4 rows: title / sub / when).
- Right: **Call these first** — the contacts who opened, clicked or became a lead (max 4) with pills and "All contacts →".
First-run state (`firstRun` or `?from=onboarding&city=&theme=&autopilot=`): a small pill "First report sent" above the title; title "Your {city} Snapshot is in your inbox."; lead sentence changes with autopilot on/off; "Latest report" shows the report just sent to them; "Next send" is either the Nov 1 run with "0 contacts so far" or "Nothing scheduled" with a "Turn on" action; right column becomes **First steps** (Import your contacts → Contacts · Set up your home-value page → Home-value page · Add your logo → Branding); activity shows the two events that just happened. Query params are how onboarding hands off — the wizard's finish button navigates to `/app?from=onboarding&city=Irvine&theme=1&autopilot=1`.

**Market reports** — title + "12 this month · 3 left on Free" · "New report" button → wizard `flow=report`. Filter pills: All · Sent to contacts · Downloaded only · Snapshot · Closed · Listings. Table rows `kind thumbnail (scaled Report Page, 56px wide) · name + area · date · via (Schedule · name / Manual) · opens (64 / 107 or —)`. Row click opens the report.

**Property reports** — title + "4 this month · 211 page views · 9 leads" · "New property report" → wizard `flow=property`. Rows: address + city · estimated value · Seller/Buyer tag · date · page views · leads (bold when > 0).

**Schedules** — title + "2 active · next send Oct 1, 9:00 AM" · "New schedule" → wizard `flow=schedule`. Rows: switch · name · kind · area · cadence ("Monthly · 1st, 9:00 AM") · recipients · next run ("Paused" when off, row at 0.7 opacity). Note under the table: "Each send uses one report from your monthly allowance. Weekly cadence needs Growth."

**Home-value page** (lead page) — title "Home-value page" + "38 visits · 9 leads · 4 called you back". Left: the agent's public URL with copy button, QR, and a scaled render of the Home Value Page address step; "Customize" toggles an inline settings panel (headline, brand, phone/text preference) — no separate settings page. Right: **Leads** with filter pills All · 9 / Hot · 3 / Called · 4; rows address · phone · views · when · state pill (Hot / New / Called).

**Contacts** — title + "107 people · 4 groups · 64 opened September". Toolbar: search, "Import CSV", "Add contact", "Manage groups". **Groups are filter pills**, not a separate tab: All · 107 / My Sphere · 107 / Past clients · 64 / Leads · 9 / Tustin owners · 41 / Opened Sept · 64. Rows: initials circle (per-contact colour) · name + email · group names · last-send state pill. Clicking a row opens a **detail drawer** (340px sticky right column ≥1100px; fixed overlay below): name, email, phone, "Added {date}", group membership as toggle pills (changes persist in-page), notes, and send history (Sep/Aug/Jul Snapshot with state pills); "Send them something" primary, "Remove" text button.
- **Add contact** is inline (expands under the toolbar): name, email, phone, group pills, "Add contact" / "Cancel".
- **CSV import** is a 3-step inline panel with step dots: 1 Choose file (drop zone + "use the sample `public/sample-contacts.csv`") → 2 Match columns (from → to with a sample value; `type` column shown as "(ignored)") → 3 Done ("Import 5 contacts" → success line and "Done").
- **Manage groups** swaps the list for a groups view: rows name · description · count · "used by {schedule}" · View / Rename; "New group" input + Create; "← Back to people".
- Empty state (first run): "No contacts yet. Import a CSV or add a few by hand." with the two buttons inline.

**Branding** — title + "What goes on every report, email and page." Left: form — logo upload ("Add photo"), brand name, four theme swatches, agent name, DRE #, phone, email, website; "Save changes". Right: live Closed Sales page with the current values — the form is the control, the report is the preview, no separate preview button.

**Plan & billing** — title + sub "You're on Free. Resets Nov 1." / "You're on Growth · $19/mo · renews Nov 6." A "Plan changed" pill appears after a switch. **Plan cards inline** (Free / Growth / Growth Plus, same copy as Landing; current card's CTA reads "Current plan" disabled, higher plans "Upgrade" ink button, lower "Downgrade" outline). Clicking opens an inline confirm card with title, one-paragraph body, a fine-print line and the CTA:
- Upgrade to Growth: "25 reports a month, 3 schedules, weekly cadence, CSV import. Takes effect now." fine: "Card collected on the next screen. Cancel any time." (from Free) / "Prorated — you only pay the difference this month." (from paid)
- Upgrade to Plus: "Unlimited reports and schedules, 25 property reports a month. Takes effect now."
- Drop to Free: "You keep Growth until Nov 6. After that: 3 reports a month, 1 schedule. Schedules over the limit pause, nothing is deleted." fine: "You can come back any time."
Below: **Usage** (same three bars as sidebar, with notes) · **Payment** (card on file or "No card on file") · **Invoices** (date · amount · PDF) · footer line "Cancelling keeps your plan until Nov 6, then drops to Free. Reports and contacts stay." + "Cancel plan" text button. Limits: Free 3 / 1 / 1, Growth 25 / 3 / 5, Plus ∞ / ∞ / 25 (market reports / schedules / property reports).

**Settings** — single page, `max-width: 720px`, replaces profile + security + notifications pages. Sections: **Profile** (photo, name, title, DRE #, phone — "Save changes"); **Sign in**: email row with "Change" → inline editor (new email + password + "Update email" / "Cancel"); password row with "Change" → inline editor (current, new, confirm + "Update password"); **Notifications**: three switches — "When someone opens a report / One email per send, the morning after", "New lead / Email and text, immediately", "Product updates / Once a month at most"; **Account**: export data, delete account (text buttons, confirm on click).

**Help** — "How can we help?" + search; eight topic cards with article counts (Getting started 6 · Creating reports 8 · Scheduling 5 · Contacts 5 · Lead capture 6 · Branding 4 · Plan & billing 5 · For title companies 4); six FAQ rows; support email.

**Admin** (role-gated) — "Platform". Health row (API · Database · Redis · Worker, green/red dot); six metric cards (Accounts 1,284 · Active users 612 · Reports 4,318 · Error rate 1.2% · Avg render 6.4s / p95 14.1s · Schedules 891 of 1,040); recent report runs table (account · type · state pill · duration · when); 12 admin links with counts (Companies, Title reps, Accounts, Users, Market reports, Schedules, Property reports, Lead pages, Emails, Plans, Security, System).

---

## Wizards v3 (`Wizards v3.dc.html`)

Tweaks: `flow` (onboarding · report · schedule · property). The flow switcher at the top of the design file is for review only — production routes are separate.

### Shell (all four flows)
Full-screen, white. Top bar: "← {Back label}" (TrendyReports / Market reports / Schedules / Property reports) · step list (dot + label, clickable backwards only) · "Finish later" (onboarding) / "Save draft" (others). Two columns: **left 480px** controls, `padding: 40px 48px`; **right** the artifact on `#FAFAF7`, centred, scaled (see Embedded artifact scaling). Footer nav fixed to the left column bottom: "← Back" text button and the primary CTA ("Continue" until the last step, then the verb — see below). CTA disabled until the step's requirement is met.

**Madlib summary** (report, schedule, property flows — not onboarding): one sentence above the controls built from the choices, where each choice is an underlined slot (`border-bottom: 2px solid #D6D3CB`, 700; current step's slot in `#4F46E5`) that jumps back to that step. E.g. "A **Market Snapshot** for **Irvine** over **30 days**, **sent monthly on the 1st** to **107 contacts**." This replaces a review step.

Each step has exactly one h2 (24px / 800) and one explanatory sentence (14px `#475569`). No more.

**Working state** (replaces the left column on submit): title ("Building your report…" / "Building and sending…" / "Building your first report…" / "Building the report…"), "Usually under a minute. You can leave — we'll email you.", then the progress checklist with real stage names (see per-flow lists). Artifact stays on the right and **fills in** as stages complete (design simulates; wire to builder stage events).

**Done state**: title + one line + 2–3 action rows (icon · label · sub), e.g. "Download PDF · 1 page · 640 KB", "Share to social · 1080×1920 story image", "Send it to contacts instead · Pick who, from your list".

### Flow: Onboarding (`flow=onboarding`) — steps: Your area · Your look · Send it to you · Autopilot
Copy and order were settled in the Sep 23 round: area → brand → real report → send to me → autopilot.
1. **Where do your people live?** — city input (required). Right: the Snapshot page for that city appears as they type. Sentence: "We'll build this month's Market Snapshot for that city from live MLS data. Watch it fill in on the right."
2. **Make it yours.** — four brand swatches; name, brand, phone, email prefilled from signup, editable. "Pick your colors. Everything else is already filled from your signup; fix anything that's off."
3. **Send it to yourself first.** — shows the recipient (their email) and the button "Send me this report". Working stages: "Pulling 30 days of {city} sales from CRMLS" · "Applying your colors and contact block" · "Rendering the PDF" · "Sending to {email}".
4. **Keep it going every month.** — one switch, default on: "Monthly {city} Snapshot → My Sphere, the 1st at 9:00 AM". CTA "Turn on autopilot" / "Finish" when off.
Done: "Your sphere is on autopilot." / "The {city} Snapshot is in your inbox now. The next one goes out Nov 1 at 9:00 AM." (or "Your first report is in your inbox." / "Turn on monthly sending whenever you're ready, from Schedules."). Actions: Open the email · Import contacts · Set up your home-value page. Finish → `/app?from=onboarding&city=…&theme=…&autopilot=…` (see Dashboard first-run).

### Flow: New report (`flow=report`) — steps: Report · (Audience) · Area & window · Deliver
1. **What should your sphere hear about?** — seven kind cards (name + one line + default window; Open Houses marked "Paused — open-house data isn't reliable yet." and not selectable). Right: that kind's page. "Snapshot is the one most agents send monthly. Pick another to see it on the right."
   Kinds: Snapshot 30d · Closed Sales 30d (audience) · New Listings 14d (audience) · Active Inventory 30d (audience) · Price Bands 30d · Featured Listings 90d · Open Houses 7d.
2. **Who is it for?** — only for Closed / Listings / Inventory. Radios: Everyone (no filter) · First-time buyers (under 70% of median · 2+ bed, 2+ bath) · Luxury (above 150% of median, single-family) · Families (3+ bed, 2+ bath, single-family) · Condo watch · Investors (under 50% of median). "Filters which homes make the page. 'All' is right for a general sphere."
3. **Where, and how far back?** — segmented City / ZIPs; city input or up to five ZIP chips (input + "Add"); lookback pills (7 · 14 · 30 · 90 days, default from the kind). "One city or up to five ZIPs. The window sets which sales count."
4. **Deliver** — radios: **Download PDF** · **Send to contacts** (group checkboxes My Sphere · 107 / Past clients / Leads · 9, CTA "Send to {n} contacts") · **Make it a schedule** (jumps into the schedule variant below). CTA "Generate PDF" / "Send to n contacts".
Working: "Pulling {n} days of {area} data from CRMLS" · "Checking 118 closed · 94 active listings" · "Writing the headline from the numbers" · "Rendering the PDF" / "Sending to n contacts". Done: "Your {Kind} is ready." or "Sent to n contacts." + "We'll tell you who opens it the morning after."

### Flow: New schedule (`flow=schedule`)
Same steps as New report; step 4 is **Schedule**: recipient groups, cadence Monthly (day-of-month picker 1–28) / Weekly (day-of-week; weekly is a Growth gate — show the upgrade line on Free), send time 9:00 AM fixed, optional name (default "Monthly {Area} {Kind}"). CTA "Turn on schedule". Done: "{name} is on." / "First send the 1st at 9:00 AM. You'll see who opens it the morning after." Actions: View schedule · Send one now too.

### Flow: Property report (`flow=property`) — steps: Address · Comparables · Look · Generate
1. **Which home?** — address input + "Look up". After lookup, the public-record fields appear as an editable summary (beds, baths, sq ft, year, lot, APN) — "We pull the public record so you don't type it. Correct anything the county has wrong." Right: the cover (`Property Report Cover`, elegant, default brand) un-veils with the address and stats.
2. **Which sales count?** — the **comps map** (`comps-map.html` in an iframe, `#`-hash protocol below) with the subject pinned (house icon in brand colour, white ring) and up to ten comps as price pins: selected = ink pill white text, dropped = white pill grey text; tap toggles. Under the map: the list with checkboxes (address · specs · sold date · distance · price), "Auto-pick" resets to the six closest. Minimum 3 selected to continue. Estimate on the right = mean $/sq ft of selected × subject sq ft, rounded to $10K, shown in the madlib and the "working" sub. "We picked the six closest in size and distance. The estimate on the right follows your checks."
3. **How should it feel?** — three theme tiles (Elegant · Bold · Modern) each rendering the cover live via `Property Report Cover`, plus six brand swatches. "Three typefaces, one brand color. The cover on the right updates."
4. **Who's reading it?** — radios Seller / Buyer ("Sellers get the value story. Buyers get the neighborhood story. Same data, different first page."); page checklist (cover, your home, comparable sales, what the comps support, your market, next steps); switch "Public page & QR code" (default on). CTA "Generate report".
Working: "Reading the county record" · "Scoring n comparable sales" · "Laying out n pages in {theme}" · "Building the public page and QR code" / "Rendering the PDF". Done: "Your seller report is ready." / "n comps · estimate $1.41M · 6 pages." Actions: Download PDF (6 pages · 2.1 MB) · Public page & QR (`trendyreports.io/p/…`) · Email it to the homeowner.

### `comps-map.html` protocol
Standalone page, Leaflet 1.9.4 + OpenStreetMap tiles (greyscale filter `grayscale(1) contrast(0.92) brightness(1.04)`, background `#F4F3EE`). State is passed in the URL hash as JSON: `{ subject: [lat, lng], brand: "#hex", comps: [{ lat, lng, price, on }] }`; a 0.75-mile radius circle is drawn around the subject (`.radius`, non-interactive). Pin click posts `{ type: "comp-toggle", index }` to the parent, which re-renders the hash. In production, replace with the same Leaflet component mounted directly (no iframe) and keep the three visual states (subject, on, off) and the greyscale tiles — colour on the map must come only from the subject pin and the brand.

---

## Home Value Page (`Home Value Page.dc.html`)

Public, mobile-first (designed at 390px, scales to desktop with the artifact beside the controls at ≥ 820px). Cream page. Tweaks: `brand` (red · teal · cyan · amber · lime · violet) — the agent's property-report brand; the page carries no product branding at all, only the agent's.

Steps, one question per screen, three progress dots (address / confirm / contact) in the brand colour:
1. **Address** — h1 "What's your Irvine home worth today?" (34px / 800) · "Based on this month's closed sales near you. Free, from Jennifer — no sign-up." · address input with typeahead (three suggestions from ≥2 characters) · "Find my home". The artifact is a real cover (`Property Report Cover`, elegant, agent's brand) at 260px tall, desaturated 0.6, under a veil reading "Your report starts with your address" with caption "A real report, like this one, for your home".
2. **Looking up** (auto, ~3s) — "Finding your home…" + three-stage checklist: "Matching your address" · "Reading the county record" · "Checking the MLS for your street". Veil text "Pulling your home's record…".
3. **Confirm** — "Is this your home?" · record card (address, beds · baths · sq ft · built, APN) · "Yes, that's it" / "Not my home" (returns to address with the field focused). The cover is now **un-veiled, full colour, with the homeowner's street and stats** — this is the moment the page proves it's real. Caption "Your report · {address}".
4. **Contact** — "Where should it go?" · "It's a PDF with your estimate and the sales behind it. We'll send the link." · segmented Text / Email · phone (auto-formats `(949) 555-0123`, needs 10 digits) or email · first name (optional; cover "Prepared for" updates live) · consent checkbox "Jennifer can contact me about my home" (required; copy must include the brokerage's TCPA text in production) · "Send my report". CTA disabled until contact valid + consent.
5. **Processing** (auto, ~4s) — "Building your report…" · "About 20 seconds. You can close this — the link still arrives." · stages: "Finding your home in county records" · "Pulling nearby sales from the MLS" · "Writing your estimate and range" · "Texting the link to (949) ••• 0123" / "Emailing the link to …".
6. **Success** — title "It's on its way to (949) ••• 0123." · cover tilted −2° as a finished object · **Jennifer's card**: photo/initials, name, brand · DRE, one line "Questions about the number? I'm happy to walk through it." · two buttons **Call** (`tel:`) and **Text** (`sms:`) in the brand colour · "Check another address" text link.

Rules: no estimate number is shown on the page — it's in the PDF, which is the reason to give a contact. No sign-up, no password, no product logo. Everything the homeowner sees is in the agent's name.

---

## States and edge cases carried across files
- **Empty**: dashboard first-run, contacts empty, schedules "Nothing scheduled". Each has one sentence and the next action inline; no illustrations.
- **Limits**: usage bars turn amber at 80% and red at 100%; the "New report" button stays enabled at the limit and the wizard's Deliver step shows the upgrade line instead of blocking earlier.
- **Paused kinds**: Open Houses is shown but not selectable, with the reason in its card.
- **Narrow widths**: sidebar → top bar < 1100px; contact drawer → overlay; wizard columns stack (artifact above controls, capped at 50vh) < 900px; landing sections stack < 720px.
- **Absence** in any report thumbnail follows the PDF packages' rules (dash, "New", "flat"); the product never invents a number.

## Assets
- Font: Plus Jakarta Sans (Google Fonts). Icons: Lucide 0.460.0. Map: Leaflet 1.9.4 + OSM tiles (attribution required). Photos: Unsplash placeholders in the embedded reports; production uses MLS/Street View per the companion packages.
- No SVG illustrations, no stock imagery, no emoji anywhere.

## Open items
1. Landing hero/carousel: decide build-time rendered images vs. a server component that renders the real builder output. The design assumes it looks identical to the PDF.
2. Home Value Page consent copy needs legal's TCPA text; layout accommodates up to 3 lines at 12px.
3. Schedule weekly cadence on Free: design shows the upgrade line inline; confirm whether the option should be disabled or allowed-then-gated at save.
4. Comps map in production: direct Leaflet mount recommended over the iframe; confirm tile provider / usage policy.
5. Admin page is a layout only — metrics and links map 1:1 to `app/app/admin/page.tsx` as read on 2026-10-06; verify nothing moved.

## Change log
- 2026-10-06 · App v3: Contacts (groups as filters, detail drawer, inline add, 3-step CSV import, groups view), Plan & billing (inline plan change + confirm, usage, payment, invoices), Settings (single page, inline email/password editors, notifications). Wizards v3: onboarding, report, schedule, property + comps map; first-run handoff to dashboard. Home Value Page: six steps, un-veiling cover, Jennifer's card. Landing v4: bigger footer, brand glow behind artifacts, dot grid on phone mockups, CTA band tinted to brand.
- 2026-10-06 (earlier) · App v3 shell + 11 pages; Landing v4 footer.
- 2026-09-30 · Landing v4 + Report Page (7 kinds); property report redesign (3 themes × 6 brands, 6 pages).
- 2026-09-23 · Onboarding reordered (area → brand → real report → send to me → autopilot); dashboard empty state as a status line; landing cut to the core loop with the pricing unit defined; report preview labelled sample vs. live.

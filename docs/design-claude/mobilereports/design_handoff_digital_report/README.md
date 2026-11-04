# Design handoff — the digital report (/p/[code] and /r/[id])

Date: 2026-11-04 · Repo `easydeed/reportscompany`, **main** as read 2026-11-04T18:10Z (tree `d70f6df2f744`; the GitHub tree hash — no commit sha was exposed to me, so none is claimed).

Three live files, 49 touches, templates and styles only:

- `apps/web/app/p/[code]/page.tsx` — P1–P10
- `apps/web/app/p/[code]/lead-capture-form.tsx` — F1–F9 (the form is part of /p; it reads the page's CSS variables, so its props are unchanged)
- `apps/web/components/mobile-report/MobileReportViewer.tsx` — R1–R30 (confirmed: that is where the viewer lives on main; `app/r/[id]/page.tsx` only mounts it)

## Files

| file | what |
|---|---|
| `EDITS.md` | every touch: page, why, exact before, exact after — generated from `touches.json` |
| `touches.json` | the single source; `apply_touches.py` reads it |
| `apply_touches.py` | `--check` simulates in order and refuses if any anchor is not found exactly `count` times; without `--check` it applies or refuses, never half-applies |
| `screenshots/` | before/after at 390 and 1280 for both pages, atlas + linen + harbor at 390; the four other /r tabs at 390 (`r-390-{details,comps,market,agent}-*`) |

`docs/DESIGN_HANDOFF_RULES.md` is not on main at this reading; this package follows the seven rules as recorded in the project's standing instructions (2026-11-04).

## What the design does

Both pages become the PDF seen on a phone, in the report's own theme:

- **Theme**: faces, display weight/tracking/case and corner radius come from the three PDF entry files (`templates/property/<theme>/<theme>_report.jinja2`) — Barlow Condensed/Barlow · 4px (atlas), Cormorant Garamond/Geist · 0 (linen), Manrope · 14px (harbor). Loaded through `next/font/google`, self-hosted, so the page paints in the theme face without a Google Fonts round trip. The id→name lookup is `themeName` from `lib/themes.generated.ts` (the single-sourced registry, D-163).
- **Colour**: the brand colour is the only fill. Text on it is `on_primary`; display lines on it are `display_ink`; brand-coloured text on white is `primary_ink`; the one dark panel is `#0f172a` with its label in `primary_on_dark`. The accent is never a background. No gradient anywhere. Neutrals are the PDF's (`#14161A` ink, `#2A2D33` body, `#5E636B` muted, `#ECECE8` rule, `#F6F6F3` strip).
- **/p**: the accent gradient hero becomes the cover band — kind label, logo as supplied (no `brightness-0 invert`), street in the display face, city line, four cover stats with dashes for missing values. Below it a white 880px sheet: the lead form first on a phone, the PDF page-6 agent panel (brand fill, white phone pill in `primary_ink`, tel:/mailto: stripped for dialling) second; two columns from `md`. Page foot as the PDF's.
- **/r**: header becomes the masthead (kind label, street in the display face). The value box becomes the PDF range panel: *Range supported by N closed sales*, the range, *Range of the comparable sales shown.* — no "most likely", no confidence pill. Stat tiles, address and agent cards lose every indigo/violet site counted in `REPORT_VIEWER_TINTS_FOR_DESIGN_2026-10-19.md` (all fourteen are covered: l.232, 254/258/271, 299/300, 337/339, 498, 536/537, 566/569/570, 648). Comp photo plate is the PDF tint plate with the distance tile when there is no photo; the price sits on a solid white plate, not over the photo. Active tab: `primary_ink` + a 2px brand bar, no alpha wash. Content and tab bar hold a 560px column on desktop.

## The one dependency (rule 5 — yours)

Neither response carries what the PDF has:

- `/v1/property/public/{code}` has `theme` and `accent_color` but no derived inks.
- `/v1/r/{id}/data` has `branding.primary_color/accent_color` and no theme at all.

The edits read **`theme_tokens`** (the `derive_theme()` dict: `primary, primary_dark, primary_ink, on_primary, tint, primary_on_dark, display_ink`) and, on /r, **`theme`** from the response. Until those fields exist, both pages render on `NEUTRAL_TOKENS` — the fixed dark neutral `#0f172a`, white on it — and /r resolves to the registry default theme (atlas). Readable everywhere, visibly unbranded, so it cannot be mistaken for done. The web app never computes a colour; that stays in `themes.py`.

Which colour to derive from is also yours to confirm, because the two PDF paths disagree today:
- agent property report: `property_builder._get_theme_color` → `accent_color` first (so on /p, `data.accent_color` *is* the PDF's brand colour, name notwithstanding);
- consumer report: `consumer_report_data.py:100` → `secondary_color or primary_color`. For a navy-primary / amber-secondary account that PDF is **amber**. If the intent is "the PDF is navy", that line is where it is decided, not in the viewer.

## Fixed-rule flags (rule 6)

- Brand colour / derived inks / text on gradients: P5, P6, P8, F8, R8, R9, R14, R19, R25, R26.
- Missing-data dashes: P6 (cover stats), R10 (`'--'` → `'—'`, 12 sites).
- Estimate panel: R9 — the PDF's panel, label + range + method line, nothing else.
- Page count, text on photos: no edit touches a PDF; R17 moves the comp price off the photo onto a white plate.

## Structural questions (rule 7 — asked, not edited)

1. **/r tabs.** Details duplicates Overview (stats, address) and Market has four rows. A homeowner on a phone would be better served by four tabs — Overview folds Details, or Details becomes a disclosure on Overview. Your call; no edit here changes the tab set.
2. **Form-first vs agent-first on /p.** The edits put the form first on a phone with CSS order only (agent panel first from `md`). If you want agent-first on phones too, drop the `order-*` classes in P8/P9.
3. **StatusPage** (expired / inactive / locked / error) is untouched — still slate + Tailwind indigo/amber icons, outside the theme. Separate edit if wanted.
4. **Consent validation**: F7 adds `required` and the asterisk; the `handleSubmit` guard and the server check are yours.
5. **Market tab copy**: R22 stops asserting "2 miles / 12 months". When the radius is on the response, print it there.

## Checks worth running after apply

- `tsc`: `fontWeight: "var(--display-weight)"` and `textWrap` are cast through `React.CSSProperties`; if your `@types/react` predates `textWrap`, the cast covers it.
- Lint: `accentColor` is still passed to the form and destructured there but no longer read (unused-var warning, not an error); `MapPin` and `Home` imports in the viewer become unused after R12/R16.
- `next/font/google`: `Geist` requires Next ≥ 14.2.

## Left on the table

- /p and /r share no code with each other or the PDF; a `theme_tokens` → CSS-variables helper would be the first shared piece once three surfaces read it (asked, not done).
- The /r Details tab and Comps carousel keep their layout; only colour/corner/face changed (R29–R30 added for the details card after the tab review).

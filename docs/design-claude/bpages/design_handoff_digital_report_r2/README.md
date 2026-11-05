# Design handoff — the digital report, round 2 (/p/[code] and /r/[id])

Date: 2026-11-05 · Repo `easydeed/reportscompany`, **main** as read 2026-11-05T17:18Z (tree `15b80ddd9d46`). Rule 1: the request named `401f5ba6` or later; `github compare 401f5ba6...main` lists ten changed files and **none of the three live files is among them**, so every anchor here is cut against the files exactly as they stand at `401f5ba6` and at main as read. (The compare exposes no head commit sha to me, so none beyond `401f5ba6` is claimed.)

Three live files, **21 anchored touches making 7 edits**, templates and styles only:

- `apps/web/app/p/[code]/page.tsx` — F7d, F7e, B2, B3a–B3g
- `apps/web/app/p/[code]/lead-capture-form.tsx` — F7a–F7c
- `apps/web/components/mobile-report/MobileReportViewer.tsx` — R9, R22, B1a–B1f

`python3 docs/design-claude/design_handoff_digital_report_r2/apply_touches.py --check` from the repo root. All 21 anchors were verified to occur exactly once, in order, against the three files as read; the script refuses and writes nothing if any has moved.

## Files

| file | what |
|---|---|
| `EDITS.md` | every touch: page, why, exact before, exact after — generated from `touches.json` |
| `touches.json` | the single source; `apply_touches.py` reads it |
| `apply_touches.py` | `--check` simulates in order and refuses if any anchor is not found exactly once; without `--check` it applies or refuses, never half-applies |
| `screenshots/B1-*.png` | /r Overview before (5 tabs, gradient card), the Details tab being removed, Overview after on atlas/linen/harbor at 390, R22 strip before→after |
| `screenshots/B2-*.png` | /p at 390 before and after (three themes), F7 consent row before→after |
| `screenshots/B3-*.png` | status page before (slate + amber) and after: expired/atlas, inactive/linen, locked/harbor, error/NEUTRAL at 390; locked at 1280 |

## A — the re-cuts

- **F7** (F7a–F7e). Checkbox 20px, `border-slate-400`, `accentColor: "var(--primary)"`. The label's only child is `{P_CONSENT_COPY}` — unchanged, one string; the asterisk is an `aria-hidden` sibling span *outside* the label, so the label text still equals `leads.consent_text` byte for byte and the consent tests that read the label see the constant alone. The `accentColor` prop is removed end to end (props type, destructure, `accentColor={accentColor}`, `const accentColor`). After F7e `/p` reads no raw colour; `accent_color` stays on the response *type* only, as a description of the API.
- **R9.** The gradient card becomes the PDF `.rangepanel` on the fixed dark neutral `#0f172a`: `RANGE_HEADING` in `primary_on_dark`, low – high in the display face, `comps_range.method`, `rangeBasis(...)`, `NO_RANGE` when there's no range — those five and nothing else. **FLAG rule 6: estimate panel** (also derived inks, text on gradient removed). It is the last `report.branding` read in the file.
- **R21.** Dropped — "Median Price per Sqft" on main is fine.
- **R22.** The indigo/violet panel becomes the PDF strip `#F6F6F3` with the hairline and muted `#5E636B` text; `{compsSentence(stats)}` untouched. After R9 + R22 the file names zero Tailwind indigo/violet classes (checked on the simulated result), so the relay test's count can go to zero.

## B — the structural changes

- **B1 — four tabs.** `details` leaves `TabId`, the `tabs` array, the switch; `DetailsTab` and the `Building2` import go. Nothing is lost: address/city/state/ZIP were already on the address card, beds/baths/sqft on the three tiles; **lot size and year built** join the address card as a two-up facts row under a hairline (display-face value, muted label, same voice as the tiles). Same formatting Details used; missing prints `—`, never 0. Fields already on the response.
- **B2 — phone agent line.** Inside the form column, above "About this home", `md:hidden`: name in ink, ` · company_name` when present, `agent_phone` as tap-to-call in `primary_ink` — the footer's own pattern, no new copy, no photo. Renders only when `agent_name` is set. The agent panel and the `order-*` classes are untouched.
- **B3 — themed status page.** `StatusPage` takes optional `theme` and `tokens`; faces via `themeName(theme)` from `THEME_FACES`, colours from the tokens, `NEUTRAL_TOKENS` + default faces when absent (not-found, error, and expired/inactive until your 410 body carries `theme`/`theme_tokens` — B3b reads them with a null fallback, so it builds and renders today). Strip page, white sheet with the theme corner and hairline, an 8px brand bar across the top (a surface with no text on it — so no derived-ink question arises), icon in `primary_ink`, title in the display face, message muted, PDF foot. No Tailwind hue class remains. Every case's text is unchanged. **FLAG rule 6: brand colour as a surface.** Locked passes the tokens it already receives; the error mount is untouched.

## Rule-5 dependency (yours)

The 410 body carrying `theme` and `theme_tokens`, as stated in the request. Nothing else.

## Checks worth running after apply

- `tsc`: `FetchResult` gains optional `theme`/`theme_tokens` on three variants; `StatusPage` props are optional, so the error mount compiles unchanged. `textWrap` is cast through `React.CSSProperties` as before.
- `tests/test_report_viewer_relay_is_current.py`: set the indigo/violet expectation to 0.
- `tests/test_digital_report_faces_match_the_pdf.py`: StatusPage now also resolves faces through `THEME_FACES[themeName(theme)]`.
- Consent tests: the label's text is `P_CONSENT_COPY` exactly; the asterisk is outside the `<label>`.
- Analytics: `tab_change` can no longer emit `details`.

## Left on the table

- Harbor's Manrope 800 range line wraps to two lines at 390 (`text-wrap: balance`); the PDF forces one line at 60px. Fine on a phone, mentioned so nobody files it.
- The success and rate-limited states in `lead-capture-form.tsx` still use slate/amber Tailwind classes. Not part of this request.

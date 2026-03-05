# Branding Section — Honest Audit

> Route: `/app/settings/branding` — `apps/web/app/app/settings/branding/page.tsx`

---

## What We Built

### Property Reports
Five fully designed Jinja2 themes — Classic, Modern, Elegant, Teal, Bold — each with its own typography, layout personality, color palette, and page structure. A smart color system that derives WCAG-safe variants from a single accent color. Theme selection lives in the property wizard (`step-theme.tsx`) with visual preview cards and a per-report accent color override.

### Email Reports
A V16 modular architecture in `template.py` with 9 shared component helpers, 6 photo card builders, 7 layout body builders, adaptive gallery routing, and full color parameterization. Every `background-color`, every `border`, every gradient reads from `{primary_color}` and `{accent_color}` f-string variables. We tested it across three completely different brand palettes (navy/gold, forest/copper, purple/teal) and it works.

### What the Branding Page Actually Lets You Control

Three tabs. That's it.

---

## Tab 1: Colors

| Control | What It Does |
|---|---|
| Primary Color picker + hex input | Sets `primary_color` |
| Accent Color picker + hex input | Sets `accent_color` (stored as `secondary_color` in DB) |
| 6 preset pairs | One-click color combos (Indigo, Ocean, Crimson, Forest, Midnight, Royal) |
| Gradient preview bar | Shows the primary-to-accent gradient |

## Tab 2: Logos

| Control | What It Does |
|---|---|
| PDF Header Logo upload | White/light logo for gradient headers |
| PDF Footer Logo upload | Dark/colored logo for light footers |
| Email Header Logo upload | Falls back to PDF header if empty |
| Email Footer Logo upload | Falls back to PDF footer if empty |

## Tab 3: Preview & Test

| Control | What It Does |
|---|---|
| Report type dropdown | Picks which type to sample |
| Download Sample PDF button | Generates a real branded PDF via API |
| Download Social Image button | Generates a branded JPG via API |
| Send Test Email button | Sends a real branded email via API |
| PDF preview mockup | Static wireframe with gradient header and logos |
| Email preview mockup | Static wireframe with gradient header and logos |

---

## What's Missing — The Uncomfortable Part

### 1. No Property Report Theme Selection

We built 5 themes. Each one has a distinct visual identity — different fonts, different layouts, different personality. The theme selector exists... buried inside the property wizard (`step-theme.tsx`), chosen per-report, forgotten per-report.

**There is no way to set a default theme in branding.**

Every single time an agent creates a property report, they start at Teal (hardcoded default, id 4). If they want Bold, they pick it. Next report? Back to Teal. There is no "my brand uses the Elegant theme" setting anywhere in the system.

The branding page — the one place where an agent goes to define "this is what my brand looks like" — has zero awareness that themes exist.

### 2. No Email Theme/Layout Selection

The email system is single-layout. Colors come from branding (good). But there is no concept of email visual themes, no layout variants, no style presets. Every account gets the same structure. The only differentiation is the two colors and the logos.

We parameterized every color in `template.py`. We built the infrastructure for theming. We never built the UI to use it.

### 3. No Font Selection

Property report themes each use curated font pairings:
- **Classic**: Merriweather + system sans
- **Modern**: DM Sans
- **Elegant**: Playfair Display
- **Teal**: Montserrat
- **Bold**: Clash Display + DM Sans

None of this is exposed. An agent can't pick a font. They can't even see which fonts their chosen theme uses. The branding page acts like typography doesn't exist.

Email templates hardcode Georgia for serif elements and system fonts for everything else. No font control whatsoever.

### 4. The "Preview" Is a Lie

The Preview & Test tab shows two mockups:

**PDF Preview**: A static wireframe — gradient header, gray placeholder bars, three empty boxes. It doesn't reflect the actual theme. It doesn't show real content structure. It doesn't show what Classic looks like vs. Bold. It's the same wireframe regardless of what theme the agent has been using.

**Email Preview**: Same problem. A gradient header, "Your market report is ready!", a gray bar, a button. This bears no resemblance to the actual V16 email templates we just built — no hero metrics, no photo galleries, no AI narratives, no sales tables. The agent has no idea what their emails actually look like until they send one.

The schedule builder has a better email preview than the branding page does. That's backwards.

### 5. No Account-Level Defaults

Nothing persists as an account preference beyond colors and logos:

| Setting | Persisted? | Where? |
|---|---|---|
| Primary color | Yes | `accounts.primary_color` |
| Accent color | Yes | `accounts.secondary_color` |
| 4 logo URLs | Yes | `accounts` table |
| Default property theme | **No** | Hardcoded to Teal in wizard |
| Default report type | **No** | — |
| Default lookback period | **No** | Hardcoded to 30 days |
| Font preference | **No** | — |
| Display/brand name | **No** | Uses `accounts.name`, not editable in branding |

### 6. Property Accent Color vs. Branding Accent Color — Disconnected

The property wizard has its own accent color picker in `step-theme.tsx`. It defaults to the theme's built-in accent, not the branding accent. A user can set `#F59E0B` as their accent in branding, then their property reports come out with `#B8860B` because that's what Teal defaults to, and they never noticed.

The two color systems don't talk to each other. Branding sets email colors. The property wizard sets property report colors. An agent who carefully picks colors in branding and expects consistency across all outputs will be disappointed.

### 7. Brand Name Is Invisible

There is no "Brand Name" or "Display Name" field on the branding page. The system uses `accounts.name` (set during signup or account settings, not here). The email templates render `brand["display_name"]` — pulled from the account name. The agent can't control this from branding.

If their account is named "John Smith's Account" because that's what they typed during onboarding, that's what shows up in emails.

---

## The Core Problem

We built a theming system that nobody can use from the place where theming belongs.

- Property reports have 5 themes — the branding page shows 0.
- Email templates are fully color-parameterized — the branding page shows a fake wireframe preview.
- We have curated font pairings per theme — the branding page doesn't mention fonts.
- We have a smart color system with WCAG-safe derivation — the branding page offers a color picker and 6 presets.

The branding page is a logo uploader with a color picker attached. It was adequate when we had one template style and hardcoded colors. It has not kept up with anything we've built in the last two iterations.

---

## What Needs to Happen

### Must-Have (the branding page is incomplete without these)

| Feature | What It Does | Effort |
|---|---|---|
| **Default Property Theme selector** | 5 theme cards with visual preview, sets account-level default, wizard pre-selects it | Medium — needs DB column `accounts.default_theme`, API PATCH, wizard reads it |
| **Accent color sync** | Branding accent feeds into property wizard as the default accent, instead of theme hardcoded value | Low — wire `accent_color` from account into wizard initial state |
| **Real email preview** | Replace the static wireframe with the actual `email-preview.tsx` component from the schedule builder (or better) | Low — component already exists, just mount it |
| **Brand/display name field** | Editable text field, saved to `accounts.name` or a new `display_name` column | Low |

### Should-Have (differentiation)

| Feature | What It Does | Effort |
|---|---|---|
| **Live theme preview** | Show a real mini-PDF preview that updates when you switch themes | Medium — needs thumbnail generation or pre-rendered previews |
| **Font preview** | At minimum, show which fonts the selected theme uses. Ideally let users pick from curated pairs | Low for display, Medium for selection |
| **Email layout variants** | If we ever build multiple email layouts, this is where users pick | Future |

### Nice-to-Have

| Feature | What It Does |
|---|---|
| Extended palette (tertiary, neutral) | More color control for power users |
| Custom CSS/override zone | For white-label accounts |
| Brand guidelines export | Download a brand kit PDF with colors, fonts, logos |

---

## File Map

```
apps/web/app/app/settings/branding/page.tsx    ← The branding page (this audit)
apps/web/components/schedule-builder/
  └── email-preview.tsx                         ← Better email preview (not used here)
apps/web/components/property-wizard/
  ├── step-theme.tsx                            ← Theme selector (per-report only)
  └── types.ts                                  ← THEMES array, font definitions
apps/worker/src/worker/email/template.py        ← V16 email templates (color-parameterized)
apps/worker/src/worker/templates/property/      ← 5 Jinja2 theme folders
apps/api/src/api/routes/account.py              ← Branding PATCH endpoint
```

---

## Summary

The branding page is where agents go to say "this is my brand." Right now it lets them set two colors and upload four logos. Meanwhile, we've built a theming engine with 5 visual identities, curated typography, smart color derivation, and fully parameterized email templates — and none of it is accessible from the one page that should be the command center for all of it.

We didn't ship the steering wheel with the car.

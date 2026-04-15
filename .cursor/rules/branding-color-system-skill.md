# Skill: Branding & Color System

> Place this file at `.cursor/rules/branding-color-system.md`
> This skill applies when working on any email template, PDF template, or branded component.

---

## The Problem This Solves

Brand colors chosen by agents range from dark navy (#18235c) to bright coral (#FF6B54) to pale gold (#D4A853). Templates must look premium with ANY brand color — not just the one we tested with. When a color is applied to a background, border, or text, it must harmonize with the surrounding content, not fight for attention.

---

## The Color Pipeline

Every branded template (PDF and email) receives two colors from the agent's settings:
- `primary_color` — the dominant brand color (often dark: navy, charcoal, forest green)
- `accent_color` — the secondary brand color (often brighter: teal, coral, gold, indigo)

These are processed through `compute_color_roles()` which produces 6 WCAG-safe variants:

| Variant | What It Is | Use For |
|---------|-----------|---------|
| `theme_color` | Raw accent hex as-is | Borders, small icons, pills where the accent appears at full strength |
| `theme_color_light` | 35% lightened toward white | Subtle background tints — callout boxes, section highlights. NOT for large backgrounds. |
| `theme_color_dark` | 25% darkened toward black | Hover states, borders on colored elements |
| `theme_color_on_dark` | Guaranteed readable on dark bg (WCAG ≥ 3.0) | Text that sits on the dark header gradient, text on primary_color backgrounds |
| `theme_color_on_light` | Guaranteed readable on white bg (WCAG ≥ 3.0) | Text on white backgrounds — labels, prices, links |
| `theme_color_text` | Pure white or dark (#1a1a1a) | Text overlaid directly on accent-colored fills (buttons, badges) |

---

## Rules for Applying Colors

### Rule 1: The email/PDF body should FLOW, not fight

Content sections (AI narrative, stats, quick take) should feel like natural parts of the page, not competing colored blocks. Apply color with restraint:

**WRONG — high contrast callout that fights for attention:**
```css
background-color: #0d9488;  /* Full accent as background */
color: white;
border: 2px solid #0d9488;
```

**RIGHT — subtle tint that harmonizes:**
```css
background-color: rgba(13, 148, 136, 0.06);  /* 6% opacity — barely there */
border-left: 3px solid rgba(13, 148, 136, 0.4);  /* 40% opacity border */
color: #1f2937;  /* Dark text, always readable */
```

**The opacity scale for accent-colored backgrounds:**
| Opacity | Effect | Use For |
|---------|--------|---------|
| 3-6% | Barely visible tint, harmonizes with any brand color | Section backgrounds (narrative, stats) |
| 8-12% | Noticeable but soft | Hover states, selected items |
| 15-20% | Clearly tinted | Badges, pills, count indicators |
| 30-40% | Strong tint | Borders, dividers |
| 100% | Full color | Buttons, header gradient, small accent elements only |

### Rule 2: Labels on tinted backgrounds

When placing a label (like "MARKET INSIGHT") on a tinted background:
- If the tint is very light (3-8% opacity): use `accent_on_light` for the label text — it's guaranteed readable on light backgrounds
- If the tint is medium (15-30%): use white text with a small accent-colored pill behind it
- NEVER use the raw accent color as text on an accent-tinted background — same-color-on-same-color is unreadable

### Rule 3: The header is the ONE place for full-strength color

The header gradient is where brand colors get to be bold:
```
background: linear-gradient(135deg, {primary_color} 0%, {primary_color} 60%, {accent_color} 100%);
```
- Primary color dominates (0-60%)
- Accent color appears at the end as a subtle wash
- All text in the header is WHITE — never primary or accent colored text on the gradient
- Logo appears in the header against the gradient — it should be a light/white version

### Rule 4: The footer is neutral

Agent footer background should be neutral, not brand-tinted:
- Background: `#f9fafb` (gray-50) or `#f3f4f6` (gray-100)
- Agent name: dark text, serif font
- Contact links: `accent_on_light` for link color (guaranteed readable)
- Company logo: rendered as-is (the agent uploaded it, we don't tint it)

### Rule 5: Status colors are NEVER brand colors

Status badges use semantic colors that don't change with branding:
- Sold/Closed: red (#dc2626 on #fee2e2)
- Active: green (#059669 on #d1fae5)
- Pending: amber (#d97706 on #fef3c7)
- Featured: gold (#f59e0b on #fef3c7)

These are fixed. They communicate meaning, not brand.

### Rule 6: Dark mode outer chrome

For email dark mode (`@media (prefers-color-scheme: dark)`):
- Outer background: `#232323` — universal neutral dark that complements ANY brand
- Content cards: stay white (`#ffffff`) — we use `color-scheme: light only` to prevent dark mode from inverting content
- The dark outer chrome frames the email without competing with brand colors

---

## Applying Colors in Email Templates (Python f-strings)

Emails use inline styles. CSS variables don't work. Use the computed variants directly:

```python
# Header gradient — full strength brand colors
f'background-color: {primary_color};'

# AI Narrative background — 6% opacity tint
f'background-color: rgba({r}, {g}, {b}, 0.06);'
# Where r,g,b are the accent_color converted to RGB components

# Narrative border — 40% opacity
f'border-left: 3px solid rgba({r}, {g}, {b}, 0.4);'

# Section label on tinted background — use computed on_light variant
f'color: {accent_on_light};'

# CTA button — full accent (one of the few places)
f'background-color: {accent_color}; color: {accent_text};'
```

### Helper: Convert hex to rgba

```python
def hex_to_rgba(hex_color: str, opacity: float) -> str:
    """Convert #RRGGBB to rgba(R, G, B, opacity)"""
    hex_color = hex_color.lstrip('#')
    r, g, b = int(hex_color[0:2], 16), int(hex_color[2:4], 16), int(hex_color[4:6], 16)
    return f'rgba({r}, {g}, {b}, {opacity})'
```

Use this instead of manual hex-alpha suffixes ({color}0D, {color}33, etc.) which are less readable and don't work in all email clients.

---

## Applying Colors in PDF Templates (Jinja2 + CSS Variables)

PDFs use CSS custom properties. The builder injects computed variants:

```css
:root {
  --primary-color: {{ primary_color }};
  --accent-color: {{ accent_color }};
  --accent-light: {{ accent_light }};         /* For section backgrounds */
  --accent-on-dark: {{ accent_on_dark }};     /* Text on header */
  --accent-on-light: {{ accent_on_light }};   /* Text on white */
}

.ai-narrative {
  background-color: color-mix(in srgb, var(--accent-color) 6%, white);
  border-left: 3px solid color-mix(in srgb, var(--accent-color) 40%, transparent);
}
```

---

## Testing Brand Colors

Always test with at least these 4 brand combos:
1. **Dark navy + teal** (#18235c + #0d9488) — the default, always looks good
2. **Bright coral + midnight** (#FF6B54 + #0f172a) — tests light accent on dark primary
3. **Light gold + charcoal** (#D4A853 + #1a1a1a) — tests warm accent
4. **Indigo + indigo** (#4F46E5 + #818CF8) — tests same-family colors where tints might blend

If the template looks good with all 4, it works with anything.

---

## Common Mistakes

| Mistake | Why It Fails | Fix |
|---------|-------------|-----|
| Using raw accent as large background | Overwhelming, fights with content | Use 3-6% opacity tint |
| Same color text on same color background | Invisible | Use computed on_light/on_dark variants |
| Accent-colored text on accent-tinted background | Low contrast, unreadable | Use dark text (#1f2937) on tints, white text on full-color fills |
| Hardcoding hex-alpha ({color}0D) | Unreliable across email clients, unreadable code | Use hex_to_rgba() helper |
| Brand-tinting the footer | Competes with the header, makes footer feel heavy | Use neutral gray (#f9fafb) |
| Different dark mode colors per brand | Inconsistent experience | Use universal #232323 |
| Using accent for status badges | Confuses meaning (is it a brand element or a status?) | Status colors are semantic, never brand |

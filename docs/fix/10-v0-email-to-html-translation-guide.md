# V0 → Email HTML Translation Guide

## How to Use This Document

This guide translates the 4 V0 React designs into changes for `apps/worker/src/worker/email/template.py`. The V0 designs use React/Tailwind (flexbox, CSS grid, Lucide icons) — none of which work in HTML emails. This guide maps every visual decision to **email-safe table HTML** that Cursor can implement.

**V0 source files** (for visual reference):
- `components/email/email-header.tsx` — Shared header (all 4 layouts)
- `components/email/email-footer.tsx` — Agent footer + disclaimer
- `components/email/market-snapshot.tsx` — Layout 1: Market Snapshot
- `components/email/listings-gallery.tsx` — Layout 2: Listings Gallery
- `components/email/table-view.tsx` — Layout 3: Table View (Closed Sales)
- `components/email/market-analytics.tsx` — Layout 4: Analytics Dashboard

---

## Design System (Shared Across All 4 Layouts)

The V0 designs establish a consistent visual language. These are the **universal patterns** to implement:

### Color Usage
| Element | V0 Uses | Email Translation |
|---------|---------|-------------------|
| Header gradient | `#1e3a5f → #b8860b` | Already exists — replace with `{primary_color} → {accent_color}` |
| Accent bar | `gradient 90deg same colors` | `background: linear-gradient(90deg, {primary_color}, {accent_color})` |
| Hero metric number | `text-[#1e3a5f]` (brand color) | `color: {primary_color}` |
| Hero metric background | `from-[#1e3a5f]/[0.06] to-transparent` | `background-color: {primary_color}08` |
| Section label text | `text-[#1e3a5f]` | `color: {primary_color}` |
| Section label bar | `h-0.5 w-5 bg-[#1e3a5f]` | 20×2px div with `background-color: {primary_color}` |
| Metric icons | `text-[#b8860b]` (gold/accent) | Replace with Unicode symbols or omit (icons don't work in email) |
| Quick Take border | `border-[#b8860b]/20, bg-[#b8860b]/[0.06]` | `border: 1px solid {accent_color}33; background-color: {accent_color}0F` |
| CTA button | `bg-[#1e3a5f]` | `background-color: {primary_color}` (already exists) |
| CTA area background | `bg-[#1e3a5f]/[0.04]` | `background-color: {primary_color}0A` |
| Agent footer bg | `bg-[#1e3a5f]/[0.03]` | `background-color: {primary_color}08` |
| Contact pill borders | `border-[#1e3a5f]/15` | `border: 1px solid {primary_color}26` |
| Gallery card badges | `bg-[#1e3a5f]/[0.07]` | `background-color: {primary_color}12` |
| Table header row | `bg-[#1e3a5f]` with white text | `background-color: {primary_color}; color: #ffffff` |

### Typography
| Element | V0 Style | Email Translation |
|---------|----------|-------------------|
| Hero metric | `font-serif text-5xl font-bold` | `font-family: Georgia, serif; font-size: 48px; font-weight: 700` |
| Section labels | `text-xs uppercase tracking-widest` | `font-size: 11px; text-transform: uppercase; letter-spacing: 2px` |
| Metric values | `font-serif text-2xl font-bold` | `font-family: Georgia, serif; font-size: 24px; font-weight: 700` |
| Metric labels | `text-[10px] uppercase tracking-wider` | `font-size: 10px; text-transform: uppercase; letter-spacing: 0.5px` |
| Body text | `text-sm leading-relaxed` | `font-size: 14px; line-height: 1.6` |
| Table stats | `font-serif text-lg font-bold text-[#1e3a5f]` | `font-family: Georgia, serif; font-size: 18px; font-weight: 700; color: {primary_color}` |

**Key typography change:** V0 uses `font-serif` (Georgia) for hero metrics and key numbers. The current template uses system font for everything. Adding serif for headline numbers creates visual distinction and a real estate "premium" feel.

---

## Changes to Implement

### Change 1: Accent Transition Bar (NEW)

**V0 reference:** `email-header.tsx` line 23-28
```jsx
<div className="h-1" style={{ background: "linear-gradient(90deg, #1e3a5f 0%, #b8860b 100%)" }} />
```

**What it does:** 4px gradient strip between header and white content area. Creates a visual "seal."

**Email HTML — insert immediately after the header `</table>` and VML closing tags:**
```python
# Add this after the header gradient section closes
f'''
          <!-- Accent Transition Strip -->
          <tr>
            <td style="height: 4px; background: linear-gradient(90deg, {primary_color} 0%, {accent_color} 100%); font-size: 0; line-height: 0;">&nbsp;</td>
          </tr>
'''
```

**Outlook fallback:** Linear gradients don't work in Outlook. It will render as a solid bar in the first color, which is fine.

---

### Change 2: AI Insight Paragraph Restyle

**V0 reference:** All 4 templates use the same pattern (market-snapshot.tsx line 30-36)
```jsx
<div className="rounded-lg border-l-4 border-[#1e3a5f] bg-[#1e3a5f]/[0.04] px-5 py-4">
  <p className="text-sm leading-relaxed text-foreground/80">...</p>
</div>
```

**What changed from current:** 
- Current: `background-color: #fafaf9; border-radius: 6px; border: 1px solid #e7e5e4` (gray box)
- V0: Left border in brand color + very subtle brand-tinted background. No full border.

**Email HTML — replace the insight_html block:**
```python
insight_html = f'''
              <!-- AI Insight -->
              <table role="presentation" cellpadding="0" cellspacing="0" width="100%" style="margin-bottom: 28px;">
                <tr>
                  <td style="padding: 16px 20px; background-color: {primary_color}0A; border-left: 4px solid {primary_color}; border-radius: 8px;">
                    <p style="margin: 0; font-size: 14px; line-height: 1.6; color: #44403c; font-weight: 400;">
                      {insight_text}
                    </p>
                  </td>
                </tr>
              </table>
'''
```

---

### Change 3: Hero Metric Card

**V0 reference:** market-snapshot.tsx lines 38-47
```jsx
<div className="rounded-xl border border-[#1e3a5f]/10 bg-gradient-to-br from-[#1e3a5f]/[0.06] to-transparent p-6 text-center">
  <p className="mb-1 text-xs font-semibold uppercase tracking-widest text-[#1e3a5f]/70">Median Sale Price</p>
  <p className="font-serif text-5xl font-bold tracking-tight text-[#1e3a5f]">$875K</p>
  <div className="mx-auto mt-3 h-1 w-12 rounded-full bg-[#b8860b]" />
</div>
```

**What changed from current:**
- Current: Label in gray, 48px number in black, on white background. No visual container.
- V0: Branded tinted card with border. Number in brand color. Serif font. Gold accent bar underneath.

**Email HTML — replace the headline metric section in hero_4_html:**
```python
f'''
              <!-- HERO METRIC -->
              <table role="presentation" cellpadding="0" cellspacing="0" width="100%" style="margin-bottom: 28px;">
                <tr>
                  <td align="center" style="padding: 24px 20px; background-color: {primary_color}0F; border-radius: 12px; border: 1px solid {primary_color}1A;">
                    <p style="margin: 0 0 6px 0; font-size: 11px; font-weight: 600; color: {primary_color}B3; text-transform: uppercase; letter-spacing: 2px;">
                      {h1_label}
                    </p>
                    <p style="margin: 0; font-family: Georgia, 'Times New Roman', serif; font-size: 48px; font-weight: 700; color: {primary_color}; letter-spacing: -1px; line-height: 1;">
                      {h1_value}
                    </p>
                    <!--[if !mso]><!-->
                    <div style="margin: 12px auto 0; width: 48px; height: 4px; border-radius: 4px; background-color: {accent_color};"></div>
                    <!--<![endif]-->
                  </td>
                </tr>
              </table>
'''
```

**Notes:** 
- `{primary_color}0F` = ~6% opacity. Safe in all email clients.
- Gold accent bar hidden from Outlook (divs are unreliable in MSO).
- Georgia serif creates the "premium real estate" feel from V0.

---

### Change 4: Key Metrics Row

**V0 reference:** market-snapshot.tsx lines 50-71
```jsx
<div className="grid grid-cols-3 gap-3">
  {metrics.map(m => (
    <div className="rounded-lg border border-border bg-card p-4 text-center">
      <Icon className="h-4 w-4 text-[#b8860b]" />  {/* Gold icon */}
      <p className="font-serif text-2xl font-bold">{m.value}</p>
      <p className="text-[10px] uppercase tracking-wider">{m.label}</p>
    </div>
  ))}
</div>
```

**What changed from current:**
- Current: Single bordered box with 3 cells divided by 1px borders. Numbers in #1c1917.
- V0: 3 separate cards with gap. Each has an icon (gold). Numbers in serif font. Individual card borders.

**Email HTML — replace the key metrics row:**
```python
f'''
              <!-- KEY METRICS ROW -->
              <table role="presentation" cellpadding="0" cellspacing="0" width="100%" style="margin-bottom: 28px;">
                <tr>
                  <td width="33%" style="padding-right: 6px;">
                    <table role="presentation" cellpadding="0" cellspacing="0" width="100%" style="border: 1px solid #e7e5e4; border-radius: 8px; background-color: #ffffff;">
                      <tr>
                        <td align="center" style="padding: 18px 8px;">
                          <p style="margin: 0 0 6px 0; font-size: 14px; color: {accent_color};">&#9679;</p>
                          <p style="margin: 0 0 4px 0; font-family: Georgia, 'Times New Roman', serif; font-size: 24px; font-weight: 700; color: #1c1917;">
                            {h2_value}
                          </p>
                          <p style="margin: 0; font-size: 10px; font-weight: 600; color: #78716c; text-transform: uppercase; letter-spacing: 0.5px;">
                            {h2_label}
                          </p>
                        </td>
                      </tr>
                    </table>
                  </td>
                  <td width="34%" style="padding: 0 3px;">
                    <table role="presentation" cellpadding="0" cellspacing="0" width="100%" style="border: 1px solid #e7e5e4; border-radius: 8px; background-color: #ffffff;">
                      <tr>
                        <td align="center" style="padding: 18px 8px;">
                          <p style="margin: 0 0 6px 0; font-size: 14px; color: {accent_color};">&#9679;</p>
                          <p style="margin: 0 0 4px 0; font-family: Georgia, 'Times New Roman', serif; font-size: 24px; font-weight: 700; color: #1c1917;">
                            {h3_value}
                          </p>
                          <p style="margin: 0; font-size: 10px; font-weight: 600; color: #78716c; text-transform: uppercase; letter-spacing: 0.5px;">
                            {h3_label}
                          </p>
                        </td>
                      </tr>
                    </table>
                  </td>
                  <td width="33%" style="padding-left: 6px;">
                    <table role="presentation" cellpadding="0" cellspacing="0" width="100%" style="border: 1px solid #e7e5e4; border-radius: 8px; background-color: #ffffff;">
                      <tr>
                        <td align="center" style="padding: 18px 8px;">
                          <p style="margin: 0 0 6px 0; font-size: 14px; color: {accent_color};">&#9679;</p>
                          <p style="margin: 0 0 4px 0; font-family: Georgia, 'Times New Roman', serif; font-size: 24px; font-weight: 700; color: #1c1917;">
                            {h4_value}
                          </p>
                          <p style="margin: 0; font-size: 10px; font-weight: 600; color: #78716c; text-transform: uppercase; letter-spacing: 0.5px;">
                            {h4_label}
                          </p>
                        </td>
                      </tr>
                    </table>
                  </td>
                </tr>
              </table>
'''
```

**Notes:** 
- `&#9679;` (●) replaces Lucide icons. Gold accent color. Simple and email-safe.
- Separate `<table>` per card creates the gap/spacing V0 shows.
- Serif font on numbers only (Georgia) matches V0.

---

### Change 5: Section Labels

**V0 reference:** market-snapshot.tsx lines 15-24 (SectionLabel component)
```jsx
<div className="mb-4 flex items-center gap-2">
  <div className="h-0.5 w-5 rounded-full bg-[#1e3a5f]" />
  <span className="text-xs font-semibold uppercase tracking-widest text-[#1e3a5f]">{children}</span>
</div>
```

**What changed from current:**
- Current: Gray uppercase text (#57534e), no accent bar
- V0: Brand-colored text + small accent bar to the left

**Email HTML — create a reusable pattern for all section headers:**
```python
def _section_label_html(label: str, primary_color: str) -> str:
    return f'''
                    <table role="presentation" cellpadding="0" cellspacing="0" style="margin-bottom: 14px;">
                      <tr>
                        <td style="width: 20px; padding-right: 8px; vertical-align: middle;">
                          <div style="width: 20px; height: 2px; background-color: {primary_color}; border-radius: 2px;"></div>
                        </td>
                        <td style="vertical-align: middle;">
                          <p style="margin: 0; font-size: 11px; font-weight: 700; color: {primary_color}; text-transform: uppercase; letter-spacing: 2px;">
                            {label}
                          </p>
                        </td>
                      </tr>
                    </table>'''
```

**Apply to:** "Market Activity", "By Property Type", "By Price Range", "Price Tiers", all listings section headers. Replace every instance of the current gray uppercase section label.

---

### Change 6: Market Activity (Core Indicators)

**V0 reference:** market-snapshot.tsx lines 73-97

**What changed from current:**
- Current: Bordered card with section header + 3 inline stats with left/right borders
- V0: Same layout but with small icons above each stat (in muted brand color). Uses the new SectionLabel.

**Email HTML — update core_indicators_html:**

Main changes:
1. Replace the gray "Market Activity" label with `_section_label_html("Market Activity", primary_color)` 
2. Add a small `&#8226;` or `&#9679;` dot above each stat value in `color: {primary_color}80`
3. Keep the 3-column layout with dividers — it's already close to V0

---

### Change 7: Property Types + Price Tiers (Side by Side)

**V0 reference:** market-snapshot.tsx lines 99-167 — 2-column grid

**What changed from current:**
- Current: Two separate full-width cards stacked vertically
- V0: Side by side in a 2-column layout. Property types has icons + count. Price tiers has progress bars.

**Email HTML:**
```python
f'''
              <!-- PROPERTY TYPES + PRICE TIERS (Side by Side) -->
              <table role="presentation" cellpadding="0" cellspacing="0" width="100%" style="margin-bottom: 28px;">
                <tr>
                  <!-- Property Types -->
                  <td width="48%" style="vertical-align: top; padding-right: 8px;">
                    <table role="presentation" cellpadding="0" cellspacing="0" width="100%" style="border: 1px solid #e7e5e4; border-radius: 8px; background-color: #ffffff;">
                      <tr>
                        <td style="padding: 16px;">
                          {_section_label_html("By Property Type", primary_color)}
                          {property_type_rows}
                        </td>
                      </tr>
                    </table>
                  </td>
                  <!-- Price Tiers -->
                  <td width="52%" style="vertical-align: top; padding-left: 8px;">
                    <table role="presentation" cellpadding="0" cellspacing="0" width="100%" style="border: 1px solid #e7e5e4; border-radius: 8px; background-color: #ffffff;">
                      <tr>
                        <td style="padding: 16px;">
                          {_section_label_html("By Price Range", primary_color)}
                          {price_tier_rows_with_bars}
                        </td>
                      </tr>
                    </table>
                  </td>
                </tr>
              </table>
'''
```

**Price tier progress bars (V0 feature):**
```python
# For each tier, add a mini progress bar below the label
f'''<table role="presentation" cellpadding="0" cellspacing="0" width="100%" style="margin-top: 4px;">
  <tr>
    <td style="padding-right: 8px;">
      <div style="height: 6px; background-color: #f0f0f0; border-radius: 4px; overflow: hidden;">
        <div style="width: {width_pct}%; height: 6px; background-color: {primary_color}; border-radius: 4px;"></div>
      </div>
    </td>
    <td width="60" style="text-align: right;">
      <span style="font-size: 10px; color: #78716c;">{tier["range"]}</span>
    </td>
  </tr>
</table>'''
```

---

### Change 8: Quick Take Callout

**V0 reference:** All 4 templates — market-snapshot.tsx lines 169-178
```jsx
<div className="rounded-lg border border-[#b8860b]/20 bg-[#b8860b]/[0.06] p-5">
  <DollarSign className="text-[#b8860b]" />
  <p className="text-sm font-medium leading-relaxed">{text}</p>
</div>
```

**What changed from current:**
- Current: Centered italic gray text at 14px. Invisible.
- V0: Accent-colored callout card with icon. Border in accent color. Background tinted. Bold text.

**Email HTML — replace the quick_take section:**
```python
f'''
              <!-- QUICK TAKE CALLOUT -->
              <table role="presentation" cellpadding="0" cellspacing="0" width="100%" style="margin-bottom: 28px;">
                <tr>
                  <td style="padding: 18px 20px; background-color: {accent_color}0F; border: 1px solid {accent_color}33; border-radius: 8px;">
                    <table role="presentation" cellpadding="0" cellspacing="0" width="100%">
                      <tr>
                        <td width="28" style="vertical-align: top; padding-right: 12px;">
                          <span style="font-size: 20px; color: {accent_color};">&#36;</span>
                        </td>
                        <td style="vertical-align: top;">
                          <p style="margin: 0; font-size: 14px; font-weight: 500; line-height: 1.6; color: #1c1917;">
                            {quick_take}
                          </p>
                        </td>
                      </tr>
                    </table>
                  </td>
                </tr>
              </table>
'''
```

**Notes:** `&#36;` is the $ sign used as a visual icon (like V0's DollarSign Lucide icon). For Analytics layout, use `&#9670;` (diamond) or `&#9650;` (triangle).

---

### Change 9: CTA Button Area

**V0 reference:** All 4 templates
```jsx
<div className="rounded-lg bg-[#1e3a5f]/[0.04] px-6 py-6 text-center">
  <a className="rounded-lg bg-[#1e3a5f] px-8 py-3.5 text-sm font-semibold text-white">View Full Report</a>
</div>
```

**What changed from current:**
- Current: Button floating on white background
- V0: Button sits in a lightly tinted area

**Email HTML — wrap the existing CTA in a tinted container:**
```python
f'''
              <!-- CTA AREA -->
              <table role="presentation" cellpadding="0" cellspacing="0" width="100%" style="margin-bottom: 28px;">
                <tr>
                  <td align="center" style="padding: 24px; background-color: {primary_color}0A; border-radius: 8px;">
                    <!--[if mso]>
                    <v:roundrect xmlns:v="urn:schemas-microsoft-com:vml" href="{pdf_url}" style="height:48px;v-text-anchor:middle;width:220px;" arcsize="8%" stroke="f" fillcolor="{primary_color}">
                      <w:anchorlock/>
                      <center style="color:#ffffff;font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,Arial,sans-serif;font-size:14px;font-weight:600;">View Full Report</center>
                    </v:roundrect>
                    <![endif]-->
                    <!--[if !mso]><!-->
                    <a href="{pdf_url}" target="_blank" style="display: inline-block; background-color: {primary_color}; color: #ffffff; font-size: 14px; font-weight: 600; text-decoration: none; padding: 14px 36px; border-radius: 8px; letter-spacing: 0.3px;">
                      View Full Report
                    </a>
                    <!--<![endif]-->
                  </td>
                </tr>
              </table>
'''
```

---

### Change 10: Agent Footer

**V0 reference:** email-footer.tsx lines 4-45
```jsx
<div className="bg-[#1e3a5f]/[0.03] px-8 py-8">
  <img className="h-20 w-20 rounded-full border-2 border-[#1e3a5f]/20" />
  <p className="font-serif text-lg font-bold">Sarah Chen</p>
  <p className="text-xs text-muted">Senior Realtor, DRE#01234567</p>
  <a className="rounded-md border border-[#1e3a5f]/15 px-3 py-1.5 text-xs text-[#1e3a5f]">📞 (310) 555-0142</a>
  <a className="rounded-md border border-[#1e3a5f]/15 px-3 py-1.5 text-xs text-[#1e3a5f]">✉ sarah@acme.com</a>
</div>
```

**What changed from current:**
- Current: White background, plain text links for phone/email
- V0: Branded tinted background. Agent name in serif. Contact info in pill/badge buttons with brand-colored borders.

**Email HTML — replace agent_footer_html (full photo version):**
```python
agent_footer_html = f'''
              <!-- AGENT FOOTER -->
              <table role="presentation" cellpadding="0" cellspacing="0" width="100%" style="margin-top: 4px;">
                <tr>
                  <td style="padding: 28px 0; border-top: 1px solid {primary_color}15;">
                    <table role="presentation" cellpadding="0" cellspacing="0" width="100%" style="background-color: {primary_color}08; border-radius: 10px; padding: 24px;">
                      <tr>
                        <td style="padding: 24px;">
                          <table role="presentation" cellpadding="0" cellspacing="0">
                            <tr>
                              <!-- Agent Photo -->
                              <td style="vertical-align: top; padding-right: 20px;">
                                <!--[if mso]>
                                <v:oval xmlns:v="urn:schemas-microsoft-com:vml" style="width:80px;height:80px;" stroke="f">
                                  <v:fill type="frame" src="{rep_photo_url}"/>
                                </v:oval>
                                <![endif]-->
                                <!--[if !mso]><!-->
                                <img src="{rep_photo_url}" alt="{contact_line1 or rep_name}" width="80" height="80" style="display: block; width: 80px; height: 80px; border-radius: 50%; object-fit: cover; border: 2px solid {primary_color}33;">
                                <!--<![endif]-->
                              </td>
                              <!-- Agent Info -->
                              <td style="vertical-align: middle;">
                                <p style="margin: 0 0 2px 0; font-family: Georgia, 'Times New Roman', serif; font-size: 18px; font-weight: 700; color: #1c1917;">
                                  {contact_line1 or rep_name}
                                </p>
                                {f'<p style="margin: 0 0 12px 0; font-size: 12px; color: #78716c;">{contact_line2 or rep_title}</p>' if (contact_line2 or rep_title) else '<div style="margin-bottom: 12px;"></div>'}
                                <table role="presentation" cellpadding="0" cellspacing="0">
                                  <tr>
                                    {f"""<td style="padding-right: 8px;">
                                      <a href="tel:{rep_phone}" style="display: inline-block; padding: 6px 14px; border: 1px solid {primary_color}26; border-radius: 6px; color: {primary_color}; text-decoration: none; font-size: 12px; font-weight: 500;">
                                        {rep_phone}
                                      </a>
                                    </td>""" if rep_phone else ""}
                                    {f"""<td>
                                      <a href="mailto:{rep_email}" style="display: inline-block; padding: 6px 14px; border: 1px solid {primary_color}26; border-radius: 6px; color: {primary_color}; text-decoration: none; font-size: 12px; font-weight: 500;">
                                        {rep_email}
                                      </a>
                                    </td>""" if rep_email else ""}
                                  </tr>
                                </table>
                              </td>
                            </tr>
                          </table>
                        </td>
                      </tr>
                    </table>
                  </td>
                </tr>
              </table>'''
```

---

### Change 11: Gallery Property Cards

**V0 reference:** listings-gallery.tsx lines 67-109

**Key V0 design decisions:**
1. **Price overlay on photo** — gradient from transparent → black/70% at bottom, white price text
2. **Detail badges** — "3 Bed" / "2 Bath" / "1,850 SF" as small rounded pills in brand tint
3. **Card shadow** — `shadow-sm` (subtle depth)

**Email HTML — replace the card builder in `_build_gallery_grid_html`:**
```python
# Photo with price overlay (simplified for email)
# Note: position:absolute is unreliable in email. Use stacked approach.
photo_html = f'''<table role="presentation" cellpadding="0" cellspacing="0" width="100%" style="background-color: #f0f0f0;">
  <tr>
    <td style="padding: 0;">
      <img src="{photo_url}" alt="{address}" width="100%" height="{img_height}" style="display: block; width: 100%; height: {img_height}px; object-fit: cover;">
    </td>
  </tr>
</table>'''

# Details with brand-tinted badges
badges_html = ""
if beds:
    badges_html += f'<span style="display: inline-block; padding: 3px 8px; background-color: {primary_color}12; border-radius: 4px; font-size: 10px; font-weight: 500; color: {primary_color}; margin-right: 4px;">{beds} Bed</span>'
if baths:
    badges_html += f'<span style="display: inline-block; padding: 3px 8px; background-color: {primary_color}12; border-radius: 4px; font-size: 10px; font-weight: 500; color: {primary_color}; margin-right: 4px;">{baths} Bath</span>'
if sqft:
    badges_html += f'<span style="display: inline-block; padding: 3px 8px; background-color: {primary_color}12; border-radius: 4px; font-size: 10px; font-weight: 500; color: {primary_color};">{sqft:,} SF</span>'

# Price in brand color, bold serif
price_html = f'''<p style="margin: 0 0 6px 0; font-family: Georgia, 'Times New Roman', serif; font-size: 16px; font-weight: 700; color: {primary_color};">
  {price_str}
</p>'''
```

**Gallery count badge (V0 feature):**
```python
# Before the card grid, add the count badge
gallery_header = f'''
              <table role="presentation" cellpadding="0" cellspacing="0" width="100%" style="margin-bottom: 20px;">
                <tr>
                  <td width="auto" style="vertical-align: middle;">
                    <span style="display: inline-block; background-color: {primary_color}; color: #ffffff; font-size: 14px; font-weight: 700; padding: 6px 16px; border-radius: 20px;">
                      {count}
                    </span>
                  </td>
                  <td style="padding-left: 10px; vertical-align: middle;">
                    <span style="font-size: 14px; font-weight: 600; color: #1c1917;">{section_title}</span>
                  </td>
                  <td style="vertical-align: middle; padding-left: 12px;">
                    <div style="height: 1px; background-color: #e7e5e4;"></div>
                  </td>
                </tr>
              </table>'''
```

---

### Change 12: Table View (Closed Sales / Inventory)

**V0 reference:** table-view.tsx — full component

**Key V0 design decisions:**
1. **Summary stats row** — 4 compact cards at top with brand-colored serif numbers
2. **Table header** — Solid brand color background with white text (not #f5f5f4 gray)
3. **Sale-to-list ratio badges** — Green for ≥100%, red for <97%, gray for neutral
4. **Strikethrough list price** — Shows both list and sale price with list crossed out

**Email HTML — update `_build_listings_table_html` header row:**
```python
# Table header - brand colored
f'''<tr style="background-color: {primary_color};">
  <td style="padding: 10px 12px; font-size: 10px; font-weight: 700; color: #ffffff; text-transform: uppercase; letter-spacing: 0.5px;">
    Address
  </td>
  <td align="center" style="padding: 10px 8px; font-size: 10px; font-weight: 700; color: #ffffff; text-transform: uppercase; letter-spacing: 0.5px; width: 50px;">
    Bd/Ba
  </td>
  <td align="right" style="padding: 10px 12px; font-size: 10px; font-weight: 700; color: #ffffff; text-transform: uppercase; letter-spacing: 0.5px; width: 100px;">
    Price
  </td>
  <td align="center" style="padding: 10px 8px; font-size: 10px; font-weight: 700; color: #ffffff; text-transform: uppercase; letter-spacing: 0.5px; width: 50px;">
    DOM
  </td>
</tr>'''
```

**Summary stats row (NEW — from V0 table-view.tsx lines 142-161):**
```python
# Add above the table, 4 compact stat cards
f'''<table role="presentation" cellpadding="0" cellspacing="0" width="100%" style="margin-bottom: 20px;">
  <tr>
    <td width="25%" style="padding-right: 4px;">
      <table role="presentation" cellpadding="0" cellspacing="0" width="100%" style="border: 1px solid #e7e5e4; border-radius: 8px;">
        <tr>
          <td align="center" style="padding: 12px 6px;">
            <p style="margin: 0; font-family: Georgia, serif; font-size: 18px; font-weight: 700; color: {primary_color};">{stat1_value}</p>
            <p style="margin: 4px 0 0; font-size: 9px; font-weight: 600; color: #78716c; text-transform: uppercase; letter-spacing: 0.5px;">{stat1_label}</p>
          </td>
        </tr>
      </table>
    </td>
    <!-- ... repeat for 3 more stats ... -->
  </tr>
</table>'''
```

---

### Change 13: Analytics Layout (NEW)

**V0 reference:** market-analytics.tsx — full component

**Reality check:** The V0 Analytics design uses Recharts (AreaChart, BarChart) which **cannot be rendered in email**. Charts are interactive SVG/Canvas.

**Email-safe alternatives:**
1. **KPI stat cards with trend indicators** — Implement the 2×2 grid of StatCards (doable)
2. **Year-over-Year comparison table** — Implement the branded-header table (doable)
3. **Charts** — Replace with a simple text summary or a pre-rendered chart image (if you generate PNG server-side)

**For now, implement from V0:**
- The 2×2 KPI grid with `+8.0%` / `-10.5%` change indicators (green up / red down)
- The YoY comparison table with brand-colored header
- Skip the charts — add as a future phase when server-side chart rendering is available

**KPI card with trend (from V0 StatCard component):**
```python
f'''<td width="50%" style="padding: {"0 4px 8px 0" if i % 2 == 0 else "0 0 8px 4px"};">
  <table role="presentation" cellpadding="0" cellspacing="0" width="100%" style="border: 1px solid #e7e5e4; border-radius: 8px;">
    <tr>
      <td style="padding: 16px;">
        <p style="margin: 0 0 6px; font-size: 10px; font-weight: 600; color: #78716c; text-transform: uppercase; letter-spacing: 0.5px;">{label}</p>
        <p style="margin: 0 0 8px; font-family: Georgia, serif; font-size: 24px; font-weight: 700; color: #1c1917;">{value}</p>
        <p style="margin: 0; font-size: 11px;">
          <span style="color: {"#059669" if positive else "#dc2626"}; font-weight: 600;">{"▲" if positive else "▼"} {change}</span>
          <span style="color: #78716c;"> vs last yr</span>
        </p>
      </td>
    </tr>
  </table>
</td>'''
```

---

## Implementation Order

| Priority | Change | Impact | Difficulty |
|----------|--------|--------|------------|
| 1 | **Change 1** — Accent bar | High (first visual upgrade users see) | Trivial |
| 2 | **Change 3** — Hero metric card | High (visual anchor of email) | Easy |
| 3 | **Change 2** — AI insight restyle | Medium (brand integration) | Easy |
| 4 | **Change 5** — Section labels | High (used everywhere) | Easy |
| 5 | **Change 8** — Quick Take callout | Medium (drives clicks) | Easy |
| 6 | **Change 9** — CTA area | Medium (conversion) | Trivial |
| 7 | **Change 4** — Metrics row | Medium (visual polish) | Medium |
| 8 | **Change 10** — Agent footer | Medium (personal touch) | Medium |
| 9 | **Change 11** — Gallery cards | High (gallery report users) | Medium |
| 10 | **Change 7** — Side-by-side types/tiers | Medium (Market Snapshot only) | Medium |
| 11 | **Change 12** — Table view header | Medium (Closed/Inventory) | Easy |
| 12 | **Change 6** — Core indicators | Low (polish) | Easy |
| 13 | **Change 13** — Analytics layout | Low (new feature) | Hard |

---

## What NOT to Change

1. **HTML email table architecture** — All layout must remain `<table role="presentation">`
2. **VML/MSO Outlook conditionals** — Keep all `<!--[if mso]>` blocks
3. **Dark mode CSS** — Keep `@media (prefers-color-scheme: dark)` 
4. **Mobile `@media` queries** — Keep stacking behavior
5. **Helper functions** — `_format_price`, `_get_hero_4_metrics`, etc. are clean
6. **AI insights logic** — Only change the display, not the generation
7. **f-string architecture** — Not switching to Jinja2 for emails

## Email Client Compatibility Notes

| Feature | Gmail | Apple Mail | Outlook | Yahoo |
|---------|-------|------------|---------|-------|
| `border-radius` | ✅ | ✅ | ❌ (ignored) | ✅ |
| `background-color` with hex+alpha (`#1e3a5f0A`) | ✅ | ✅ | ❌ | ✅ |
| `linear-gradient` | ✅ | ✅ | ❌ (solid fallback) | ✅ |
| `border-left: 4px solid` | ✅ | ✅ | ✅ | ✅ |
| `font-family: Georgia, serif` | ✅ | ✅ | ✅ | ✅ |
| `<div>` for accent bars | ✅ | ✅ | ⚠️ (unreliable) | ✅ |
| VML `<v:roundrect>` | N/A | N/A | ✅ | N/A |

**Outlook workaround for hex+alpha colors:** Use full `rgba()` or a close solid hex equivalent:
- `{primary_color}0A` → In Outlook, falls back to transparent (which is fine — white bg shows through)
- The brand tinting is a progressive enhancement; Outlook users get clean white sections

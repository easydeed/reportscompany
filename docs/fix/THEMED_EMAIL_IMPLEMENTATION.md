# THEMED_EMAIL_IMPLEMENTATION.md
# V0 → template.py Translation Guide — Complete Rewrite

> **This replaces the previous 13-change approach.** The old plan tried to polish a flat layout. This guide implements 7 distinct editorial layouts from V0, each as its own builder function. The result: emails that look like luxury real estate marketing, not data exports.

---

## Table of Contents

1. Architecture Overview
2. Shared Components (All Layouts)
3. Layout 1: Market Narrative
4. Layout 2: Gallery 2×2
5. Layout 3: Gallery 3×2
6. Layout 4: Single Stacked
7. Layout 5: Large List
8. Layout 6: Closed Sales Table
9. Layout 7: Market Analytics
10. Report Type → Layout Mapping
11. AI Narrative Prompt Upgrade
12. Email Client Compatibility
13. Implementation Order
14. Testing Checklist

---

## 1. Architecture Overview

### Current State (What Exists)

`apps/worker/src/worker/email/template.py` — One ~2,020-line function (`schedule_email_html()`) that uses `REPORT_CONFIG` flags to toggle sections on/off. All 8 report types share the same rendering path with conditionals.

### Target State (What We're Building)

Replace the monolithic function with **7 layout builder functions** + **shared component helpers**. Each layout maps 1:1 to a V0 React component.

```
schedule_email_html()
├── _build_header()                    ← shared
├── _build_ai_narrative()              ← shared
├── _build_quick_take()                ← shared
├── _build_cta()                       ← shared
├── _build_agent_footer()              ← shared
├── _build_footer()                    ← shared
│
├── _build_market_narrative_body()     ← Layout 1
├── _build_gallery_2x2_body()         ← Layout 2
├── _build_gallery_3x2_body()         ← Layout 3
├── _build_single_stacked_body()      ← Layout 4
├── _build_large_list_body()          ← Layout 5
├── _build_closed_sales_body()        ← Layout 6
└── _build_analytics_body()           ← Layout 7
```

### Key Variables (All Layouts)

These already exist in the current template — keep them:

```python
primary_color    # e.g., "#1B365D" — agent's brand color
accent_color     # e.g., "#B8860B" — agent's secondary color
rep_name         # Agent name
rep_phone        # Agent phone
rep_email        # Agent email
rep_photo_url    # Agent headshot URL
logo_url         # Brand logo URL
pdf_url          # Link to full PDF report
report_type      # e.g., "market_snapshot", "featured_listings"
report_title     # e.g., "Market Snapshot – Silver Lake"
period_label     # e.g., "Last 30 Days"
insight_text     # AI-generated narrative (4-6 sentences)
quick_take       # One-liner market summary
```

---

## 2. Shared Components (All Layouts)

### 2A. Email Header

**V0 reference:** `email-header.tsx`

Already implemented and looking good. Keep the existing gradient header with these elements:
- Gradient background: `linear-gradient(135deg, {primary_color}, {accent_color})`
- Logo centered
- Report type badge pill (semi-transparent white)
- Title: "Report Type – Area"
- Period subtitle
- 4px accent transition strip below

**No changes needed** to the header. It's solid.

### 2B. AI Narrative (NEW — Prominent Treatment)

**V0 reference:** All layouts use this pattern:

```python
def _build_ai_narrative(insight_text: str) -> str:
    """Full-width narrative paragraph — the newsletter hook."""
    if not insight_text:
        return ''
    return f'''
    <table role="presentation" cellpadding="0" cellspacing="0" width="100%"
           style="margin-bottom: 32px;">
      <tr>
        <td style="padding: 0;">
          <p style="margin: 0; font-size: 16px; line-height: 1.8; color: #1c1917;
             font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto,
             'Helvetica Neue', Arial, sans-serif;">
            {insight_text}
          </p>
        </td>
      </tr>
    </table>'''
```

**Critical change from current:** This is 16px on white with 1.8 line-height — NOT a small 14px gray box with a border. The narrative is the opening paragraph of the email. No background color, no border. Just clean text on white.

### 2C. Gallery Count Badge

**V0 reference:** Used in gallery and list layouts:

```python
def _build_gallery_count(count: int, label: str, primary_color: str) -> str:
    """Branded count badge with horizontal rule."""
    return f'''
    <table role="presentation" cellpadding="0" cellspacing="0" width="100%"
           style="margin-bottom: 20px;">
      <tr>
        <td width="auto" style="vertical-align: middle;">
          <span style="display: inline-block; background-color: {primary_color};
                color: #ffffff; font-size: 14px; font-weight: 700;
                padding: 6px 16px; border-radius: 20px;">
            {count}
          </span>
        </td>
        <td style="padding-left: 10px; vertical-align: middle;">
          <span style="font-size: 14px; font-weight: 600; color: #1c1917;">
            {label}
          </span>
        </td>
        <td style="vertical-align: middle; padding-left: 12px;">
          <div style="height: 1px; background-color: #e7e5e4;"></div>
        </td>
      </tr>
    </table>'''
```

### 2D. Quick Take Callout

**V0 reference:** All layouts — accent-colored callout:

```python
def _build_quick_take(quick_take: str, accent_color: str) -> str:
    """Accent-colored insight callout."""
    if not quick_take:
        return ''
    return f'''
    <table role="presentation" cellpadding="0" cellspacing="0" width="100%"
           style="margin-bottom: 28px;">
      <tr>
        <td style="padding: 18px 20px; background-color: {accent_color}0F;
            border: 1px solid {accent_color}33; border-radius: 8px;">
          <table role="presentation" cellpadding="0" cellspacing="0" width="100%">
            <tr>
              <td width="28" style="vertical-align: top; padding-right: 12px;">
                <span style="font-size: 20px; color: {accent_color};">&#36;</span>
              </td>
              <td style="vertical-align: top;">
                <p style="margin: 0; font-size: 14px; font-weight: 500;
                   line-height: 1.6; color: #1c1917;">
                  {quick_take}
                </p>
              </td>
            </tr>
          </table>
        </td>
      </tr>
    </table>'''
```

### 2E. CTA Button Area

**V0 reference:** All layouts — tinted container with branded button:

```python
def _build_cta(pdf_url: str, primary_color: str, cta_text: str = "View Full Report") -> str:
    """Branded CTA button in tinted container."""
    return f'''
    <table role="presentation" cellpadding="0" cellspacing="0" width="100%"
           style="margin-bottom: 28px;">
      <tr>
        <td align="center" style="padding: 24px; background-color: {primary_color}0A;
            border-radius: 8px;">
          <!--[if mso]>
          <v:roundrect xmlns:v="urn:schemas-microsoft-com:vml"
            xmlns:w="urn:schemas-microsoft-com:office:word"
            href="{pdf_url}"
            style="height:48px;v-text-anchor:middle;width:240px;"
            arcsize="8%" stroke="f" fillcolor="{primary_color}">
            <w:anchorlock/>
            <center style="color:#ffffff;font-family:-apple-system,BlinkMacSystemFont,
              'Segoe UI',Roboto,Arial,sans-serif;font-size:14px;font-weight:600;">
              {cta_text}
            </center>
          </v:roundrect>
          <![endif]-->
          <!--[if !mso]><!-->
          <a href="{pdf_url}" target="_blank"
             style="display: inline-block; background-color: {primary_color};
             color: #ffffff; font-size: 14px; font-weight: 600;
             text-decoration: none; padding: 14px 40px; border-radius: 8px;
             letter-spacing: 0.3px;">
            {cta_text}
          </a>
          <!--<![endif]-->
        </td>
      </tr>
    </table>'''
```

### 2F. Agent Footer

**V0 reference:** `email-footer.tsx` — already looking good. Keep existing implementation with:
- Tinted background: `{primary_color}08`
- Agent photo: 80×80 circular with brand border
- Name in Georgia serif, 18px bold
- Title/license in 12px gray
- Phone + Email as pill buttons with `{primary_color}26` borders
- VML oval fallback for Outlook

### 2G. Section Label

**V0 reference:** Used in Closed Sales and other section headers:

```python
def _build_section_label(label: str, primary_color: str) -> str:
    """Branded section label with accent bar."""
    return f'''
    <table role="presentation" cellpadding="0" cellspacing="0"
           style="margin-bottom: 14px;">
      <tr>
        <td style="width: 20px; padding-right: 8px; vertical-align: middle;">
          <div style="width: 20px; height: 2px; background-color: {primary_color};
               border-radius: 2px;"></div>
        </td>
        <td style="vertical-align: middle;">
          <p style="margin: 0; font-size: 11px; font-weight: 700;
             color: {primary_color}; text-transform: uppercase;
             letter-spacing: 2px;">
            {label}
          </p>
        </td>
      </tr>
    </table>'''
```

### 2H. Filter Description Blurb (Optional)

Shows audience criteria when a report has filter presets:

```python
def _build_filter_blurb(filter_text: str, primary_color: str) -> str:
    """Optional report criteria callout."""
    if not filter_text:
        return ''
    return f'''
    <table role="presentation" cellpadding="0" cellspacing="0" width="100%"
           style="margin-bottom: 20px;">
      <tr>
        <td style="padding: 12px 16px; background-color: {primary_color}08;
            border-radius: 8px; border-left: 3px solid {primary_color};">
          <p style="margin: 0; font-size: 13px; line-height: 1.5; color: #44403c;">
            <span style="font-weight: 600; color: {primary_color};">Report Criteria:</span>
            {filter_text}
          </p>
        </td>
      </tr>
    </table>'''
```

---

## 3. Layout 1: Market Narrative

**V0 reference:** `market-narrative.tsx`
**Used for:** Market Snapshot, New Listings, Price Bands

### Structure

```
[HEADER]
[AI NARRATIVE — 4-6 sentences, 16px, on white]
[HERO STAT — one 56px number, centered, on subtle bg]
[2×2 PHOTO GRID — 4 properties]
[STACKED VERTICAL STATS — label left, big number right]
[QUICK TAKE]
[CTA]
[AGENT FOOTER]
[FOOTER]
```

### Hero Stat

```python
def _build_hero_stat(value: str, label: str, trend: str, trend_positive: bool,
                     primary_color: str) -> str:
    """Single massive stat — the visual anchor of the email."""
    trend_color = "#059669" if trend_positive else "#dc2626"
    trend_arrow = "&#9650;" if trend_positive else "&#9660;"
    trend_html = ''
    if trend:
        trend_html = f'''
        <p style="margin: 8px 0 0; font-size: 13px; font-weight: 600;
           color: {trend_color};">
          <span style="display: inline-block; margin-right: 3px;">{trend_arrow}</span>
          {trend}
        </p>'''

    return f'''
    <table role="presentation" cellpadding="0" cellspacing="0" width="100%"
           style="margin-bottom: 32px;">
      <tr>
        <td align="center" style="padding: 32px 20px;">
          <p style="margin: 0; font-family: Georgia, 'Times New Roman', serif;
             font-size: 56px; font-weight: 700; color: {primary_color};
             line-height: 1; letter-spacing: -1px;">
            {value}
          </p>
          <p style="margin: 8px 0 0; font-size: 11px; font-weight: 600;
             color: #78716c; text-transform: uppercase; letter-spacing: 2px;">
            {label}
          </p>
          {trend_html}
        </td>
      </tr>
    </table>'''
```

### 2×2 Photo Grid Card

```python
def _build_photo_card_2x2(listing: dict, primary_color: str) -> str:
    """Single property card for 2×2 grid."""
    photo_url = listing.get('photo_url', '')
    price = listing.get('price', '')
    address = listing.get('address', '')
    location = listing.get('location', '')
    beds = listing.get('beds', '')
    baths = listing.get('baths', '')
    sqft = listing.get('sqft', '')

    return f'''
    <table role="presentation" cellpadding="0" cellspacing="0" width="100%"
           style="background-color: #ffffff; border-radius: 8px;
           border: 1px solid #e7e5e4; overflow: hidden;">
      <tr>
        <td style="padding: 0;">
          <img src="{photo_url}" alt="{address}" width="100%" height="160"
               style="display: block; width: 100%; height: 160px;
               object-fit: cover; background: #f5f5f4;">
        </td>
      </tr>
      <tr>
        <td style="padding: 12px 14px;">
          <p style="margin: 0 0 4px; font-family: Georgia, 'Times New Roman', serif;
             font-size: 18px; font-weight: 700; color: {primary_color};">
            {price}
          </p>
          <p style="margin: 0 0 2px; font-size: 13px; font-weight: 600;
             color: #1c1917;">
            {address}
          </p>
          <p style="margin: 0 0 8px; font-size: 11px; color: #78716c;">
            {location}
          </p>
          <p style="margin: 0;">
            <span style="display: inline-block; padding: 2px 8px;
              background-color: {primary_color}0D; border-radius: 4px;
              font-size: 10px; font-weight: 500; color: {primary_color};
              margin-right: 4px;">
              {beds} Bed
            </span>
            <span style="display: inline-block; padding: 2px 8px;
              background-color: {primary_color}0D; border-radius: 4px;
              font-size: 10px; font-weight: 500; color: {primary_color};
              margin-right: 4px;">
              {baths} Bath
            </span>
            <span style="display: inline-block; padding: 2px 8px;
              background-color: {primary_color}0D; border-radius: 4px;
              font-size: 10px; font-weight: 500; color: {primary_color};">
              {sqft} SF
            </span>
          </p>
        </td>
      </tr>
    </table>'''
```

### 2×2 Grid Assembly

```python
def _build_photo_grid_2x2(listings: list, primary_color: str) -> str:
    """Assemble 4 listings into a 2×2 grid."""
    # Take first 4 listings
    items = listings[:4]
    rows_html = ''
    for i in range(0, len(items), 2):
        left = _build_photo_card_2x2(items[i], primary_color)
        right = _build_photo_card_2x2(items[i+1], primary_color) if i+1 < len(items) else ''
        rows_html += f'''
        <tr>
          <td width="50%" style="padding: 4px; vertical-align: top;">
            {left}
          </td>
          <td width="50%" style="padding: 4px; vertical-align: top;">
            {right}
          </td>
        </tr>'''

    return f'''
    <table role="presentation" cellpadding="0" cellspacing="0" width="100%"
           style="margin-bottom: 32px;">
      {rows_html}
    </table>'''
```

### Stacked Vertical Stats

```python
def _build_stacked_stats(stats: list) -> str:
    """Stacked vertical stat rows — label left, big number right.
    stats: list of dicts with 'label' and 'value' keys.
    """
    rows_html = ''
    for i, stat in enumerate(stats):
        border = 'border-bottom: 1px solid #f0efed;' if i < len(stats) - 1 else ''
        rows_html += f'''
        <tr>
          <td style="padding: 16px 0; {border}">
            <table role="presentation" cellpadding="0" cellspacing="0" width="100%">
              <tr>
                <td style="font-size: 14px; color: #57534e;">
                  {stat['label']}
                </td>
                <td align="right" style="font-family: Georgia, 'Times New Roman', serif;
                    font-size: 24px; font-weight: 700; color: #1c1917;">
                  {stat['value']}
                </td>
              </tr>
            </table>
          </td>
        </tr>'''

    return f'''
    <table role="presentation" cellpadding="0" cellspacing="0" width="100%"
           style="margin-bottom: 32px; border-top: 1px solid #e7e5e4;">
      {rows_html}
    </table>'''
```

### Full Layout Assembly

```python
def _build_market_narrative_body(data: dict, primary_color: str,
                                  accent_color: str) -> str:
    """Layout 1: Market Narrative — for data-heavy reports."""
    parts = []

    # AI Narrative
    parts.append(_build_ai_narrative(data.get('insight_text', '')))

    # Hero Stat
    hero = data.get('hero_metric', {})
    parts.append(_build_hero_stat(
        value=hero.get('value', ''),
        label=hero.get('label', ''),
        trend=hero.get('trend', ''),
        trend_positive=hero.get('trend_positive', True),
        primary_color=primary_color
    ))

    # 2×2 Photo Grid (if listings available)
    listings = data.get('listings', [])
    if listings:
        parts.append(_build_gallery_count(
            min(4, len(listings)),
            data.get('listings_label', 'Notable Properties'),
            primary_color
        ))
        parts.append(_build_photo_grid_2x2(listings, primary_color))

    # Stacked Stats
    stats = data.get('secondary_stats', [])
    if stats:
        parts.append(_build_stacked_stats(stats))

    # Quick Take
    parts.append(_build_quick_take(data.get('quick_take', ''), accent_color))

    # CTA
    parts.append(_build_cta(data.get('pdf_url', ''), primary_color))

    return '\n'.join(parts)
```

---

## 4. Layout 2: Gallery 2×2

**V0 reference:** `gallery-2x2.tsx`
**Used for:** Featured Listings (4 properties)

### Structure

```
[HEADER]
[AI NARRATIVE — 2-3 sentences]
[GALLERY COUNT — "4 Featured Listings in Silver Lake"]
[2×2 GRID — large 180px photos, 20px serif pricing]
[QUICK TAKE]
[CTA]
[AGENT FOOTER]
[FOOTER]
```

### Photo Card (Larger Version)

Same as 2×2 card from Layout 1 but with 180px photo height and 20px price:

```python
def _build_gallery_card_large(listing: dict, primary_color: str) -> str:
    """Gallery card with 180px photo and prominent pricing."""
    photo_url = listing.get('photo_url', '')
    price = listing.get('price', '')
    address = listing.get('address', '')
    location = listing.get('location', '')
    beds = listing.get('beds', '')
    baths = listing.get('baths', '')
    sqft = listing.get('sqft', '')

    return f'''
    <table role="presentation" cellpadding="0" cellspacing="0" width="100%"
           style="background-color: #ffffff; border-radius: 8px;
           border: 1px solid #e7e5e4; overflow: hidden;">
      <tr>
        <td style="padding: 0;">
          <img src="{photo_url}" alt="{address}" width="100%" height="180"
               style="display: block; width: 100%; height: 180px;
               object-fit: cover; background: #f5f5f4;">
        </td>
      </tr>
      <tr>
        <td style="padding: 14px 16px;">
          <p style="margin: 0 0 4px; font-family: Georgia, 'Times New Roman', serif;
             font-size: 20px; font-weight: 700; color: {primary_color};">
            {price}
          </p>
          <p style="margin: 0 0 2px; font-size: 14px; font-weight: 600;
             color: #1c1917;">
            {address}
          </p>
          <p style="margin: 0 0 10px; font-size: 12px; color: #78716c;">
            {location}
          </p>
          <p style="margin: 0; font-size: 12px; color: #57534e;">
            {beds} Bed &bull; {baths} Bath &bull; {sqft} SF
          </p>
        </td>
      </tr>
    </table>'''
```

### Layout Assembly

```python
def _build_gallery_2x2_body(data: dict, primary_color: str,
                             accent_color: str) -> str:
    """Layout 2: Gallery 2×2 — 4 featured properties."""
    parts = []
    parts.append(_build_ai_narrative(data.get('insight_text', '')))

    listings = data.get('listings', [])[:4]
    parts.append(_build_gallery_count(
        len(listings),
        data.get('listings_label', 'Featured Listings'),
        primary_color
    ))

    # 2×2 grid with large cards
    rows_html = ''
    for i in range(0, len(listings), 2):
        left = _build_gallery_card_large(listings[i], primary_color)
        right = _build_gallery_card_large(listings[i+1], primary_color) if i+1 < len(listings) else ''
        rows_html += f'''
        <tr>
          <td width="50%" style="padding: 4px; vertical-align: top;">{left}</td>
          <td width="50%" style="padding: 4px; vertical-align: top;">{right}</td>
        </tr>'''
    parts.append(f'''
    <table role="presentation" cellpadding="0" cellspacing="0" width="100%"
           style="margin-bottom: 32px;">{rows_html}</table>''')

    parts.append(_build_quick_take(data.get('quick_take', ''), accent_color))
    parts.append(_build_cta(data.get('pdf_url', ''), primary_color, "View All Listings"))
    return '\n'.join(parts)
```

---

## 5. Layout 3: Gallery 3×2

**V0 reference:** `gallery-3x2.tsx`
**Used for:** New Listings Gallery (6 properties, compact)

### Photo Card (Compact)

```python
def _build_gallery_card_compact(listing: dict, primary_color: str) -> str:
    """Compact gallery card — 110px photo, tight padding."""
    photo_url = listing.get('photo_url', '')
    price = listing.get('price', '')
    address = listing.get('address', '')
    beds = listing.get('beds', '')
    baths = listing.get('baths', '')

    return f'''
    <table role="presentation" cellpadding="0" cellspacing="0" width="100%"
           style="background-color: #ffffff; border-radius: 8px;
           border: 1px solid #e7e5e4; overflow: hidden;">
      <tr>
        <td style="padding: 0;">
          <img src="{photo_url}" alt="{address}" width="100%" height="110"
               style="display: block; width: 100%; height: 110px;
               object-fit: cover; background: #f5f5f4;">
        </td>
      </tr>
      <tr>
        <td style="padding: 10px 10px;">
          <p style="margin: 0 0 2px; font-family: Georgia, 'Times New Roman', serif;
             font-size: 15px; font-weight: 700; color: {primary_color};">
            {price}
          </p>
          <p style="margin: 0 0 4px; font-size: 11px; font-weight: 600;
             color: #1c1917;">
            {address}
          </p>
          <p style="margin: 0; font-size: 10px; color: #78716c;">
            {beds}bd / {baths}ba
          </p>
        </td>
      </tr>
    </table>'''
```

### 3-Column Grid Assembly

```python
def _build_gallery_3x2_body(data: dict, primary_color: str,
                             accent_color: str) -> str:
    """Layout 3: Gallery 3×2 — 6 properties compact."""
    parts = []
    parts.append(_build_ai_narrative(data.get('insight_text', '')))

    listings = data.get('listings', [])[:6]
    parts.append(_build_gallery_count(
        len(listings),
        data.get('listings_label', 'New Listings'),
        primary_color
    ))

    # 3-column grid
    rows_html = ''
    for i in range(0, len(listings), 3):
        cells = ''
        for j in range(3):
            if i + j < len(listings):
                card = _build_gallery_card_compact(listings[i+j], primary_color)
                cells += f'<td width="33%" style="padding: 3px; vertical-align: top;">{card}</td>'
            else:
                cells += '<td width="33%" style="padding: 3px;"></td>'
        rows_html += f'<tr>{cells}</tr>'

    parts.append(f'''
    <table role="presentation" cellpadding="0" cellspacing="0" width="100%"
           style="margin-bottom: 32px;">{rows_html}</table>''')

    parts.append(_build_quick_take(data.get('quick_take', ''), accent_color))
    parts.append(_build_cta(data.get('pdf_url', ''), primary_color, "View All Listings"))
    return '\n'.join(parts)
```

---

## 6. Layout 4: Single Stacked

**V0 reference:** `single-stacked.tsx`
**Used for:** Featured Listings (luxury), Just Sold highlights, Open Houses

### Full-Width Property Card

```python
def _build_stacked_property_card(listing: dict, primary_color: str,
                                  accent_color: str) -> str:
    """Luxury full-width property card — magazine style."""
    photo_url = listing.get('photo_url', '')
    price = listing.get('price', '')
    address = listing.get('address', '')
    location = listing.get('location', '')
    beds = listing.get('beds', '')
    baths = listing.get('baths', '')
    sqft = listing.get('sqft', '')
    year = listing.get('year_built', '')
    description = listing.get('description', '')

    year_badge = ''
    if year:
        year_badge = f'''
        <span style="display: inline-block; padding: 4px 12px;
          background-color: {primary_color}0D; border-radius: 6px;
          font-size: 11px; font-weight: 500; color: {primary_color};
          margin-right: 6px;">
          Built {year}
        </span>'''

    desc_html = ''
    if description:
        desc_html = f'''
        <p style="margin: 12px 0 0; font-size: 13px; color: #57534e;
           line-height: 1.5; font-style: italic;">
          &ldquo;{description}&rdquo;
        </p>'''

    return f'''
    <table role="presentation" cellpadding="0" cellspacing="0" width="100%"
           style="border-radius: 12px; border: 1px solid #e7e5e4;
           overflow: hidden; margin-bottom: 8px;">
      <tr>
        <td style="padding: 0;">
          <img src="{photo_url}" alt="{address}" width="520" height="240"
               style="display: block; width: 100%; height: 240px;
               object-fit: cover; background: #f5f5f4;">
        </td>
      </tr>
      <tr>
        <td style="padding: 20px;">
          <p style="margin: 0 0 4px; font-family: Georgia, 'Times New Roman', serif;
             font-size: 22px; font-weight: 700; color: {primary_color};">
            {price}
          </p>
          <p style="margin: 0 0 2px; font-size: 15px; font-weight: 600;
             color: #1c1917;">
            {address}
          </p>
          <p style="margin: 0 0 12px; font-size: 12px; color: #78716c;">
            {location}
          </p>
          <p style="margin: 0;">
            <span style="display: inline-block; padding: 4px 12px;
              background-color: {primary_color}0D; border-radius: 6px;
              font-size: 11px; font-weight: 500; color: {primary_color};
              margin-right: 6px;">
              {beds} Bed
            </span>
            <span style="display: inline-block; padding: 4px 12px;
              background-color: {primary_color}0D; border-radius: 6px;
              font-size: 11px; font-weight: 500; color: {primary_color};
              margin-right: 6px;">
              {baths} Bath
            </span>
            <span style="display: inline-block; padding: 4px 12px;
              background-color: {primary_color}0D; border-radius: 6px;
              font-size: 11px; font-weight: 500; color: {primary_color};
              margin-right: 6px;">
              {sqft} SF
            </span>
            {year_badge}
          </p>
          {desc_html}
        </td>
      </tr>
    </table>'''
```

### Branded Divider Between Cards

```python
def _build_branded_divider(primary_color: str, accent_color: str) -> str:
    """Thin gradient divider between stacked cards."""
    return f'''
    <table role="presentation" cellpadding="0" cellspacing="0" width="100%">
      <tr>
        <td align="center" style="padding: 12px 0;">
          <!--[if !mso]><!-->
          <div style="width: 64px; height: 2px; border-radius: 2px;
               background: linear-gradient(90deg, {primary_color}, {accent_color});">
          </div>
          <!--<![endif]-->
          <!--[if mso]>
          <div style="width: 64px; height: 2px; background-color: {primary_color};"></div>
          <![endif]-->
        </td>
      </tr>
    </table>'''
```

### Layout Assembly

```python
def _build_single_stacked_body(data: dict, primary_color: str,
                                accent_color: str) -> str:
    """Layout 4: Single Stacked — luxury magazine layout."""
    parts = []
    parts.append(_build_ai_narrative(data.get('insight_text', '')))

    listings = data.get('listings', [])[:5]  # Max 5 for this layout
    for i, listing in enumerate(listings):
        parts.append(_build_stacked_property_card(listing, primary_color, accent_color))
        if i < len(listings) - 1:
            parts.append(_build_branded_divider(primary_color, accent_color))

    parts.append(_build_cta(data.get('pdf_url', ''), primary_color,
                            "Schedule a Private Showing"))
    return '\n'.join(parts)
```

---

## 7. Layout 5: Large List

**V0 reference:** `large-list.tsx`
**Used for:** 10+ property lists (New Listings, Inventory)

### Property Row (Photo Left, Details Right)

```python
def _build_property_row(listing: dict, primary_color: str,
                        is_last: bool = False) -> str:
    """List row: 160×120 photo left, details right."""
    photo_url = listing.get('photo_url', '')
    price = listing.get('price', '')
    address = listing.get('address', '')
    location = listing.get('location', '')
    beds = listing.get('beds', '')
    baths = listing.get('baths', '')
    sqft = listing.get('sqft', '')
    border = '' if is_last else 'border-bottom: 1px solid #f0efed;'

    return f'''
    <tr>
      <td style="{border}">
        <table role="presentation" cellpadding="0" cellspacing="0" width="100%">
          <tr>
            <td width="160" style="vertical-align: top;">
              <img src="{photo_url}" alt="{address}" width="160" height="120"
                   style="display: block; width: 160px; height: 120px;
                   object-fit: cover; background: #f5f5f4;">
            </td>
            <td style="vertical-align: middle; padding: 14px 16px;">
              <p style="margin: 0 0 4px; font-family: Georgia, 'Times New Roman', serif;
                 font-size: 18px; font-weight: 700; color: {primary_color};">
                {price}
              </p>
              <p style="margin: 0 0 2px; font-size: 14px; font-weight: 600;
                 color: #1c1917;">
                {address}
              </p>
              <p style="margin: 0 0 8px; font-size: 12px; color: #78716c;">
                {location}
              </p>
              <p style="margin: 0; font-size: 11px; color: #57534e;">
                {beds} Bed &bull; {baths} Bath &bull; {sqft} SF
              </p>
            </td>
          </tr>
        </table>
      </td>
    </tr>'''
```

### Layout Assembly

```python
def _build_large_list_body(data: dict, primary_color: str,
                            accent_color: str) -> str:
    """Layout 5: Large List — 10+ properties with photo rows."""
    parts = []
    parts.append(_build_ai_narrative(data.get('insight_text', '')))

    listings = data.get('listings', [])
    parts.append(_build_gallery_count(
        len(listings),
        data.get('listings_label', 'New Listings'),
        primary_color
    ))

    # Build property rows inside a bordered container
    rows_html = ''
    for i, listing in enumerate(listings):
        rows_html += _build_property_row(
            listing, primary_color, is_last=(i == len(listings) - 1))

    parts.append(f'''
    <table role="presentation" cellpadding="0" cellspacing="0" width="100%"
           style="border: 1px solid #e7e5e4; border-radius: 12px;
           overflow: hidden; margin-bottom: 32px;">
      {rows_html}
    </table>''')

    parts.append(_build_quick_take(data.get('quick_take', ''), accent_color))
    parts.append(_build_cta(data.get('pdf_url', ''), primary_color))
    return '\n'.join(parts)
```

---

## 8. Layout 6: Closed Sales Table

**V0 reference:** `closed-sales-table.tsx`
**Used for:** Closed Sales, Inventory

### Structure

```
[HEADER]
[AI NARRATIVE — 3-4 sentences]
[HERO STAT — "8 Homes Sold" or "$875K Median"]
[2×2 PHOTO GRID — 4 notable sales with SOLD badge]
[DATA TABLE — brand header, alternating rows]
[QUICK TAKE]
[CTA]
[AGENT FOOTER]
[FOOTER]
```

### Photo Card With Badge (SOLD overlay)

```python
def _build_photo_card_with_badge(listing: dict, primary_color: str,
                                  accent_color: str,
                                  badge_text: str = "Sold") -> str:
    """2×2 card with a badge overlay on the photo."""
    photo_url = listing.get('photo_url', '')
    price = listing.get('price', '')
    address = listing.get('address', '')
    beds = listing.get('beds', '')
    baths = listing.get('baths', '')

    return f'''
    <table role="presentation" cellpadding="0" cellspacing="0" width="100%"
           style="background-color: #ffffff; border-radius: 8px;
           border: 1px solid #e7e5e4; overflow: hidden;">
      <tr>
        <td style="padding: 0; position: relative;">
          <img src="{photo_url}" alt="{address}" width="100%" height="130"
               style="display: block; width: 100%; height: 130px;
               object-fit: cover; background: #f5f5f4;">
        </td>
      </tr>
      <tr>
        <td style="padding: 10px 12px;">
          <p style="margin: 0;">
            <span style="display: inline-block; padding: 2px 8px;
              background-color: {accent_color}; color: #ffffff;
              font-size: 9px; font-weight: 700; text-transform: uppercase;
              letter-spacing: 1px; border-radius: 3px; margin-bottom: 6px;">
              {badge_text}
            </span>
          </p>
          <p style="margin: 4px 0 2px; font-family: Georgia, 'Times New Roman', serif;
             font-size: 16px; font-weight: 700; color: {primary_color};">
            {price}
          </p>
          <p style="margin: 0 0 2px; font-size: 12px; font-weight: 500;
             color: #1c1917;">
            {address}
          </p>
          <p style="margin: 0; font-size: 10px; color: #78716c;">
            {beds}bd / {baths}ba
          </p>
        </td>
      </tr>
    </table>'''
```

### Data Table

```python
def _build_sales_table(rows: list, primary_color: str) -> str:
    """Clean data table with branded header and alternating rows."""
    header = f'''
    <tr style="background-color: {primary_color};">
      <td style="padding: 10px 12px; font-size: 11px; font-weight: 700;
          color: #ffffff; text-transform: uppercase; letter-spacing: 0.5px;">
        Address
      </td>
      <td align="center" style="padding: 10px 8px; font-size: 11px;
          font-weight: 700; color: #ffffff; text-transform: uppercase;
          letter-spacing: 0.5px; width: 55px;">
        Bd/Ba
      </td>
      <td align="right" style="padding: 10px 12px; font-size: 11px;
          font-weight: 700; color: #ffffff; text-transform: uppercase;
          letter-spacing: 0.5px; width: 110px;">
        Sale Price
      </td>
      <td align="right" style="padding: 10px 12px; font-size: 11px;
          font-weight: 700; color: #ffffff; text-transform: uppercase;
          letter-spacing: 0.5px; width: 50px;">
        DOM
      </td>
    </tr>'''

    body_rows = ''
    for i, row in enumerate(rows):
        bg = '#ffffff' if i % 2 == 0 else '#fafaf9'
        body_rows += f'''
    <tr style="background-color: {bg};">
      <td style="padding: 10px 12px; border-bottom: 1px solid #f0efed;">
        <span style="font-size: 13px; font-weight: 600; color: #1c1917;">
          {row.get('address', '')}
        </span>
      </td>
      <td align="center" style="padding: 10px 8px; border-bottom: 1px solid #f0efed;
          font-size: 13px; color: #57534e;">
        {row.get('bed_bath', '')}
      </td>
      <td align="right" style="padding: 10px 12px; border-bottom: 1px solid #f0efed;">
        <span style="font-family: Georgia, 'Times New Roman', serif;
          font-size: 14px; font-weight: 700; color: {primary_color};">
          {row.get('price', '')}
        </span>
      </td>
      <td align="right" style="padding: 10px 12px; border-bottom: 1px solid #f0efed;
          font-size: 13px; color: #57534e;">
        {row.get('dom', '')}
      </td>
    </tr>'''

    return f'''
    <table role="presentation" cellpadding="0" cellspacing="0" width="100%"
           style="border: 1px solid #e7e5e4; border-radius: 12px;
           overflow: hidden; margin-bottom: 32px;">
      {header}
      {body_rows}
    </table>'''
```

### Layout Assembly

```python
def _build_closed_sales_body(data: dict, primary_color: str,
                              accent_color: str) -> str:
    """Layout 6: Closed Sales — photos + data table."""
    parts = []
    parts.append(_build_ai_narrative(data.get('insight_text', '')))

    # Hero stat
    hero = data.get('hero_metric', {})
    parts.append(_build_hero_stat(
        value=hero.get('value', ''),
        label=hero.get('label', ''),
        trend=hero.get('trend', ''),
        trend_positive=hero.get('trend_positive', True),
        primary_color=primary_color
    ))

    # Notable sales photo grid (top 4 with SOLD badge)
    notable = data.get('notable_sales', data.get('listings', []))[:4]
    if notable:
        parts.append(_build_gallery_count(len(notable), "Notable Sales", primary_color))
        rows_html = ''
        for i in range(0, len(notable), 2):
            left = _build_photo_card_with_badge(notable[i], primary_color, accent_color)
            right = _build_photo_card_with_badge(notable[i+1], primary_color, accent_color) if i+1 < len(notable) else ''
            rows_html += f'''
            <tr>
              <td width="50%" style="padding: 4px; vertical-align: top;">{left}</td>
              <td width="50%" style="padding: 4px; vertical-align: top;">{right}</td>
            </tr>'''
        parts.append(f'''
        <table role="presentation" cellpadding="0" cellspacing="0" width="100%"
               style="margin-bottom: 24px;">{rows_html}</table>''')

    # Data table
    table_rows = data.get('table_rows', [])
    if table_rows:
        parts.append(_build_section_label("Recent Sales", primary_color))
        parts.append(_build_sales_table(table_rows, primary_color))

    parts.append(_build_quick_take(data.get('quick_take', ''), accent_color))
    parts.append(_build_cta(data.get('pdf_url', ''), primary_color,
                            "Get Your Home's Value"))
    return '\n'.join(parts)
```

---

## 9. Layout 7: Market Analytics

**V0 reference:** `market-analytics.tsx`
**Used for:** Market Trends, Year-over-Year analysis

### Stacked Stats With Trends

```python
def _build_trend_stats(stats: list) -> str:
    """Stacked stat rows with trend indicators — alternating backgrounds.
    stats: list of dicts with 'label', 'value', 'trend', 'trend_positive', 'trend_label'.
    """
    rows_html = ''
    for i, stat in enumerate(stats):
        bg = '#ffffff' if i % 2 == 0 else '#fafaf9'
        color = '#059669' if stat.get('trend_positive', True) else '#dc2626'
        arrow = '&#9650;' if stat.get('trend_positive', True) else '&#9660;'

        # Special case for neutral indicators
        trend_label = stat.get('trend_label', stat.get('trend', ''))
        if stat.get('trend_neutral'):
            color = '#B8860B'
            arrow = '&rarr;'

        rows_html += f'''
        <tr>
          <td style="padding: 16px 20px; background-color: {bg};">
            <table role="presentation" cellpadding="0" cellspacing="0" width="100%">
              <tr>
                <td style="font-size: 14px; color: #57534e; vertical-align: middle;">
                  {stat['label']}
                </td>
                <td align="right" style="vertical-align: middle;">
                  <span style="font-family: Georgia, 'Times New Roman', serif;
                    font-size: 24px; font-weight: 700; color: #1c1917;
                    margin-right: 12px;">
                    {stat['value']}
                  </span>
                  <span style="font-size: 12px; font-weight: 600; color: {color};">
                    <span style="margin-right: 2px;">{arrow}</span>{trend_label}
                  </span>
                </td>
              </tr>
            </table>
          </td>
        </tr>'''

    return f'''
    <table role="presentation" cellpadding="0" cellspacing="0" width="100%"
           style="border: 1px solid #e7e5e4; border-radius: 12px;
           overflow: hidden; margin-bottom: 32px;">
      {rows_html}
    </table>'''
```

### Year-over-Year Comparison Card

```python
def _build_yoy_comparison(last_year: list, this_year: list,
                           primary_color: str) -> str:
    """Side-by-side Year-over-Year comparison.
    Each list: [{'label': 'Median Price', 'value': '$855K'}, ...]
    """
    left_rows = ''
    for item in last_year:
        left_rows += f'''
        <tr>
          <td style="padding: 0 0 12px;">
            <p style="margin: 0; font-family: Georgia, 'Times New Roman', serif;
               font-size: 20px; font-weight: 700; color: #78716c;">
              {item['value']}
            </p>
            <p style="margin: 2px 0 0; font-size: 11px; color: #a8a29e;">
              {item['label']}
            </p>
          </td>
        </tr>'''

    right_rows = ''
    for item in this_year:
        right_rows += f'''
        <tr>
          <td style="padding: 0 0 12px;">
            <p style="margin: 0; font-family: Georgia, 'Times New Roman', serif;
               font-size: 20px; font-weight: 700; color: {primary_color};">
              {item['value']}
            </p>
            <p style="margin: 2px 0 0; font-size: 11px; color: #78716c;">
              {item['label']}
            </p>
          </td>
        </tr>'''

    return f'''
    <table role="presentation" cellpadding="0" cellspacing="0" width="100%"
           style="margin-bottom: 32px;">
      <tr>
        <td style="padding-bottom: 10px;">
          <p style="margin: 0; font-size: 11px; font-weight: 700;
             color: #78716c; text-transform: uppercase; letter-spacing: 2px;">
            Year-Over-Year Comparison
          </p>
        </td>
      </tr>
      <tr>
        <td>
          <table role="presentation" cellpadding="0" cellspacing="0" width="100%"
                 style="border: 1px solid #e7e5e4; border-radius: 12px;
                 overflow: hidden;">
            <tr>
              <td width="50%" style="padding: 20px; background-color: #f5f5f4;
                  border-right: 1px solid #e7e5e4; vertical-align: top;">
                <p style="margin: 0 0 14px; font-size: 11px; font-weight: 700;
                   color: #78716c; text-transform: uppercase; letter-spacing: 2px;">
                  Last Year
                </p>
                <table role="presentation" cellpadding="0" cellspacing="0">
                  {left_rows}
                </table>
              </td>
              <td width="50%" style="padding: 20px; background-color: #ffffff;
                  vertical-align: top;">
                <p style="margin: 0 0 14px; font-size: 11px; font-weight: 700;
                   color: {primary_color}; text-transform: uppercase;
                   letter-spacing: 2px;">
                  This Year
                </p>
                <table role="presentation" cellpadding="0" cellspacing="0">
                  {right_rows}
                </table>
              </td>
            </tr>
          </table>
        </td>
      </tr>
    </table>'''
```

### Layout Assembly

```python
def _build_analytics_body(data: dict, primary_color: str,
                           accent_color: str) -> str:
    """Layout 7: Market Analytics — trends and year-over-year."""
    parts = []
    parts.append(_build_ai_narrative(data.get('insight_text', '')))

    # Hero stat with trend
    hero = data.get('hero_metric', {})
    parts.append(_build_hero_stat(
        value=hero.get('value', ''),
        label=hero.get('label', ''),
        trend=hero.get('trend', ''),
        trend_positive=hero.get('trend_positive', True),
        primary_color=primary_color
    ))

    # Trend stats
    trend_stats = data.get('trend_stats', [])
    if trend_stats:
        parts.append(_build_trend_stats(trend_stats))

    # YoY comparison
    last_year = data.get('last_year_stats', [])
    this_year = data.get('this_year_stats', [])
    if last_year and this_year:
        parts.append(_build_yoy_comparison(last_year, this_year, primary_color))

    parts.append(_build_quick_take(data.get('quick_take', ''), accent_color))
    parts.append(_build_cta(data.get('pdf_url', ''), primary_color,
                            "Get Your Free Home Valuation"))
    return '\n'.join(parts)
```

---

## 10. Report Type → Layout Mapping

Update `schedule_email_html()` to route each report type to the correct layout builder:

```python
LAYOUT_MAP = {
    'market_snapshot':        '_build_market_narrative_body',
    'new_listings':           '_build_market_narrative_body',
    'price_bands':            '_build_market_narrative_body',
    'featured_listings':      '_build_gallery_2x2_body',       # or single_stacked
    'new_listings_gallery':   '_build_gallery_3x2_body',       # or gallery_2x2
    'open_houses':            '_build_single_stacked_body',
    'closed_sales':           '_build_closed_sales_body',
    'inventory':              '_build_closed_sales_body',
}

# Gallery layout selection based on listing count:
def _select_gallery_layout(report_type: str, listing_count: int) -> str:
    """Auto-select the best gallery layout based on listing count."""
    if listing_count <= 3:
        return '_build_single_stacked_body'
    elif listing_count <= 4:
        return '_build_gallery_2x2_body'
    elif listing_count <= 6:
        return '_build_gallery_3x2_body'
    else:
        return '_build_large_list_body'
```

This means gallery-type reports auto-select the best layout for the number of listings. 1-3 properties get the luxury single-stacked treatment, 4 get the 2×2 grid, 5-6 get the 3×2, and 7+ get the large list.

---

## 11. AI Narrative Prompt Upgrade

The current AI insight prompt generates 2 weak sentences. Upgrade it to produce 4-6 engaging sentences.

### Updated System Prompt for AI Insights

```python
AI_INSIGHT_PROMPT = """You are a real estate market analyst writing the opening
paragraph of a premium market newsletter for homeowners. Write 4-6 sentences
that are conversational, data-driven, and action-oriented.

Your tone: authoritative but approachable. Like a trusted advisor writing a
personal note, not a robot generating a summary.

Requirements:
- Lead with the most interesting or surprising data point
- Reference specific streets or neighborhoods when possible
- Include at least one actionable insight ("If you're considering listing...")
- End with a forward-looking statement about what this means
- Use the agent's area name naturally
- Never use bullet points or formatting — just flowing prose
- Never start with "The market" or "This month" — start with the area name
  or a specific data point

DO NOT write generic filler. Every sentence should contain specific data or
a concrete insight that would make a homeowner pick up the phone.

Example: "Silver Lake's housing market heated up this month with a 12% jump
in median sale prices, fueled by razor-thin inventory below the $1M mark.
Three homes on Hyperion Avenue alone sold above asking in the last 30 days
— a signal that buyer competition is intensifying heading into spring."
"""
```

---

## 12. Email Client Compatibility

| Feature | Gmail | Apple Mail | Outlook | Yahoo |
|---------|:-----:|:----------:|:-------:|:-----:|
| `border-radius` | Yes | Yes | No (ignored) | Yes |
| `hex+alpha` bg colors | Yes | Yes | No | Yes |
| `linear-gradient` | Yes | Yes | No (solid fallback) | Yes |
| `border-left: 4px` | Yes | Yes | Yes | Yes |
| `Georgia, serif` | Yes | Yes | Yes | Yes |
| `object-fit: cover` | Yes | Yes | No | Yes |
| VML `<v:roundrect>` | N/A | N/A | Yes | N/A |

**Outlook strategy:** Progressive enhancement. Outlook users get:
- Rectangular cards (no border-radius) — fine
- Solid `{primary_color}` instead of gradients — fine
- No tinted backgrounds (hex+alpha ignored) — white shows through, still clean
- VML CTA button — already handled

---

## 13. Implementation Order

### Phase 1: Shared Components (Do First)

1. Create `_build_ai_narrative()` — the new 16px white treatment
2. Create `_build_gallery_count()` — branded count badge
3. Create `_build_quick_take()` — accent callout
4. Create `_build_cta()` — tinted CTA area
5. Create `_build_section_label()` — branded section headers
6. Create `_build_filter_blurb()` — optional filter criteria
7. Update `_build_hero_stat()` — new 56px serif treatment
8. Update agent footer — keep existing, ensure pill buttons

### Phase 2: Layout Builders (One at a Time)

9. `_build_market_narrative_body()` — Layout 1 (most report types use this)
10. `_build_gallery_2x2_body()` — Layout 2
11. `_build_single_stacked_body()` — Layout 4 (luxury)
12. `_build_large_list_body()` — Layout 5
13. `_build_closed_sales_body()` — Layout 6
14. `_build_gallery_3x2_body()` — Layout 3
15. `_build_analytics_body()` — Layout 7

### Phase 3: Routing & Integration

16. Update `schedule_email_html()` to use `LAYOUT_MAP`
17. Implement `_select_gallery_layout()` for auto-selection
18. Update AI insight prompt (longer, more engaging)
19. Test all 8 report types render correctly

### Phase 4: Polish

20. Verify dark mode CSS still works
21. Verify mobile stacking on all layouts
22. Check Outlook VML rendering
23. Test with 3-4 different brand color combinations

---

## 14. Testing Checklist

After implementation, verify each layout:

### Market Narrative (Layout 1)
- [ ] AI narrative is 16px on white — no gray box, no border
- [ ] Hero stat is 56px Georgia serif in `{primary_color}`
- [ ] 2×2 photo grid shows 4 properties with 160px photos
- [ ] Stacked stats are full-width rows, label left, number right
- [ ] Quick Take has accent-colored callout styling

### Gallery 2×2 (Layout 2)
- [ ] 4 cards with 180px photos
- [ ] Price is 20px Georgia serif in `{primary_color}`
- [ ] Gallery count badge shows correct number

### Gallery 3×2 (Layout 3)
- [ ] 6 cards in 3-column layout
- [ ] 110px photos, compact but readable
- [ ] Cards don't break on mobile (should stack)

### Single Stacked (Layout 4)
- [ ] Full-width 240px hero photos
- [ ] Price is 22px Georgia serif
- [ ] Branded gradient dividers between cards
- [ ] Optional description renders in italic

### Large List (Layout 5)
- [ ] 160×120 photos in each row
- [ ] 18px serif pricing
- [ ] Clean dividers between rows
- [ ] Handles 10+ listings without breaking

### Closed Sales (Layout 6)
- [ ] Hero stat renders (e.g., "8 Homes Sold")
- [ ] 2×2 notable sales grid with SOLD badges
- [ ] Data table has brand-colored header
- [ ] Alternating row backgrounds
- [ ] Sale prices in serif font

### Market Analytics (Layout 7)
- [ ] Hero stat has trend arrow (green ▲ or red ▼)
- [ ] Stacked stats have trend indicators
- [ ] YoY comparison card shows Last Year vs This Year
- [ ] "This Year" column uses `{primary_color}`

### Cross-Layout Checks
- [ ] All 8 report types route to correct layout
- [ ] Gallery auto-selection works (1-3 → stacked, 4 → 2×2, etc.)
- [ ] All layouts render on white background (not gray)
- [ ] Agent footer consistent across all layouts
- [ ] Header gradient uses `{primary_color}` → `{accent_color}`
- [ ] Dark mode CSS preserved
- [ ] Mobile media queries preserved
- [ ] Outlook VML conditionals preserved

### Browser Rendering Test

```python
# Quick test: render each layout and open in browser
for report_type in ['market_snapshot', 'featured_listings',
                    'new_listings_gallery', 'closed_sales']:
    html = schedule_email_html(report_type=report_type, ...)
    with open(f"/tmp/email_test_{report_type}.html", "w") as f:
        f.write(html)
```

---

## Cursor Prompt

```
Read THEMED_EMAIL_IMPLEMENTATION.md for the complete spec.

TASK: Rewrite the email template system in apps/worker/src/worker/email/template.py.

Replace the monolithic schedule_email_html() function with a modular architecture:
- 8 shared component helper functions (_build_ai_narrative, _build_hero_stat, etc.)
- 7 layout builder functions, one per layout type
- A LAYOUT_MAP dict routing report_type → layout builder
- Auto-selection logic for gallery layouts based on listing count

RULES:
- Keep ALL email-safe table layout (no flexbox, no CSS grid, no CSS variables)
- Keep ALL VML/MSO Outlook conditionals for header gradient, agent photo, CTA button
- Keep ALL dark mode and mobile @media CSS
- Keep the existing helper functions (_format_price, _get_hero_4_metrics, etc.)
- Keep the REPORT_CONFIG dict for section toggles
- All colors must use {primary_color} and {accent_color} f-string variables
- Background is WHITE (#ffffff) — not gray. Brand colors on elements only.
- AI narrative: 16px, line-height 1.8, on white. No gray box.
- Hero stats: Georgia serif, 56px, {primary_color}
- Photo heights: 240px (stacked), 180px (2×2 gallery), 160px (market narrative),
  130px (closed sales), 120px (large list), 110px (3×2 compact)
- Price font: Georgia serif in {primary_color} — 22px stacked, 20px gallery,
  18px list rows, 16px compact

IMPLEMENTATION ORDER:
Phase 1: Build shared component helpers first
Phase 2: Build layout builders one at a time (start with market_narrative)
Phase 3: Update schedule_email_html() routing
Phase 4: Update AI insight prompt

Test each layout by rendering to HTML and opening in a browser.
```

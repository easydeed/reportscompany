# Skill: Email HTML Design & Layout

> Place this file at `.cursor/rules/email-html-design.md`
> This skill applies when working on `apps/worker/src/worker/email/template.py` or any email HTML

---

## Email HTML Is Not Web HTML

Email rendering engines are 15+ years behind browsers. Gmail strips `<style>` tags from non-Google senders. Outlook uses Microsoft Word's rendering engine. Yahoo ignores half of CSS. Every style must be inline. Every layout must be table-based.

**If it doesn't work in a `<table>`, it doesn't work in email.**

---

## The Rendering Engine Reality

| Client | Rendering Engine | What Breaks |
|--------|-----------------|-------------|
| Gmail (web) | Google's sanitizer | Strips `<style>` blocks, rewrites class names |
| Gmail (app) | WebView | Better CSS support, still strips `<style>` |
| Outlook 2016+ | Microsoft Word | No CSS Grid, no Flexbox, no background-image on divs, no border-radius |
| Apple Mail | WebKit | Most CSS works — the "good" client |
| Yahoo Mail | Custom sanitizer | Strips `<style>` from some senders |

**Design for Outlook first.** If it looks good in Word's renderer, it looks good everywhere.

---

## Layout Rules

### Everything is a table
```html
<!-- CORRECT: table-based layout -->
<table role="presentation" width="100%" cellpadding="0" cellspacing="0" border="0">
  <tr>
    <td style="padding: 20px;">Content here</td>
  </tr>
</table>

<!-- WRONG: div-based layout -->
<div style="display: flex; gap: 20px;">
  <div>Content here</div>
</div>
```

### Multi-column layouts use table cells
```html
<!-- 2-column: 60/40 split -->
<table role="presentation" width="100%" cellpadding="0" cellspacing="0">
  <tr>
    <td width="60%" valign="top" style="padding-right: 10px;">Left content</td>
    <td width="40%" valign="top" style="padding-left: 10px;">Right content</td>
  </tr>
</table>

<!-- 3-column equal -->
<table role="presentation" width="100%" cellpadding="0" cellspacing="0">
  <tr>
    <td width="33.33%" valign="top">Col 1</td>
    <td width="33.33%" valign="top">Col 2</td>
    <td width="33.33%" valign="top">Col 3</td>
  </tr>
</table>
```

### Centering
```html
<!-- Center a block element -->
<table role="presentation" width="600" align="center" cellpadding="0" cellspacing="0">
  <tr>
    <td align="center">Centered content</td>
  </tr>
</table>

<!-- Center an image -->
<img src="..." width="160" height="40" alt="" style="display: block; margin: 0 auto;">
```

### Spacing
- Use `padding` on `<td>` elements — this is the most reliable spacing method
- `margin` is unreliable in email — Outlook ignores it on many elements
- For vertical spacing between sections: use an empty `<tr>` with a `<td>` with height
```html
<!-- Spacer row -->
<tr><td style="height: 20px; font-size: 0; line-height: 0;">&nbsp;</td></tr>
```

---

## Typography

### Safe fonts only
```
font-family: Georgia, 'Times New Roman', Times, serif;     /* Serif (prices, metrics) */
font-family: -apple-system, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif;  /* Sans (body) */
```

Custom fonts (Google Fonts, Adobe Fonts) are stripped by Gmail and ignored by Outlook. Never rely on them. Georgia is the premium serif fallback for email.

### Font sizing
| Element | Size | Weight | Font |
|---------|------|--------|------|
| Header title | 24px | 700 | Georgia |
| Header metric value | 28-32px | 700 | Georgia |
| Header meta line | 11px | 400 | sans-serif |
| Hero stat | 48-56px | 700 | Georgia |
| Section label ("MARKET INSIGHT") | 10-11px | 600 | sans-serif, uppercase |
| Body text | 14-16px | 400 | sans-serif |
| Property price | 18-22px | 700 | Georgia |
| Property address | 13-14px | 600 | sans-serif |
| Property specs | 11px | 400 | sans-serif |
| Table header | 10px | 600 | sans-serif, uppercase |
| Table data | 12px | 400 | sans-serif |
| Footer agent name | 16-18px | 700 | Georgia |
| Footer text | 11-12px | 400 | sans-serif |
| Powered by | 10px | 400 | sans-serif |

---

## Image Handling

### Always set width AND height
```html
<!-- CORRECT -->
<img src="photo.jpg" width="260" height="160" alt="Property" 
     style="display: block; border-radius: 6px; object-fit: cover;">

<!-- WRONG — Outlook will display at natural size -->
<img src="photo.jpg" style="max-width: 100%; height: auto;">
```

### Logo best practices
```html
<!-- Centered logo with padding -->
<td align="center" style="padding: 15px 0;">
  <img src="logo.png" width="160" alt="Company" 
       style="display: block; max-width: 160px; max-height: 45px; width: auto; height: auto;">
</td>
```
- `display: block` prevents the inline gap below images
- Set `max-width` and `max-height` to constrain — logos come in all shapes
- Use `width: auto; height: auto;` with max constraints so the logo maintains aspect ratio
- Center with `align="center"` on the parent `<td>`
- Add generous padding around logos — they need breathing room

### Circular photos (agent headshot)
```html
<!-- Modern clients -->
<img src="headshot.jpg" width="80" height="80" 
     style="border-radius: 50%; display: block; object-fit: cover;">

<!-- Outlook fallback (VML) -->
<!--[if mso]>
<v:oval xmlns:v="urn:schemas-microsoft-com:vml" style="width:80px;height:80px;" 
        strokecolor="#ffffff" strokeweight="2px">
  <v:fill type="frame" src="headshot.jpg"/>
</v:oval>
<![endif]-->
```

---

## Header Design Pattern

The email header is the brand showcase. It should be:
- Substantial height (not a thin strip)
- Gradient or solid dark background
- Logo centered or right-aligned with generous padding
- Title and metric clearly readable in white

### 3-row header structure (most reliable)
```html
<table role="presentation" width="100%" cellpadding="0" cellspacing="0" 
       style="background-color: #18235c;">
  
  <!-- Row 1: Logo, centered with padding -->
  <tr>
    <td align="center" style="padding: 18px 24px 10px;">
      <img src="logo.png" width="140" alt="" 
           style="display: block; max-height: 40px; width: auto; height: auto;">
    </td>
  </tr>
  
  <!-- Row 2: Title + metric -->
  <tr>
    <td style="padding: 0 24px;">
      <table role="presentation" width="100%" cellpadding="0" cellspacing="0">
        <tr>
          <td width="65%" style="font-family: Georgia, serif; font-size: 24px; 
                                  font-weight: 700; color: #ffffff;">
            Report Title — City
            <div style="font-size: 11px; font-weight: 400; opacity: 0.7; margin-top: 4px;">
              March 2026 • Data via MLS
            </div>
          </td>
          <td width="35%" align="right" valign="bottom" 
              style="font-family: Georgia, serif; font-size: 28px; 
                     font-weight: 700; color: #ffffff;">
            42
            <div style="font-size: 10px; font-weight: 400; text-transform: uppercase; 
                        letter-spacing: 0.5px; opacity: 0.8;">
              Homes Sold
            </div>
          </td>
        </tr>
      </table>
    </td>
  </tr>
  
  <!-- Row 3: Bottom padding -->
  <tr>
    <td style="height: 18px; font-size: 0;">&nbsp;</td>
  </tr>
</table>
```

This 3-row pattern gives the header substance:
- Logo on its own row, centered, with top padding — works regardless of logo orientation (wide or tall)
- Title + metric on the second row, 65/35 split
- Bottom padding row for breathing room

Total height: approximately 110-130px — substantial but not excessive.

### VML gradient for Outlook
```html
<!--[if gte mso 9]>
<v:rect xmlns:v="urn:schemas-microsoft-com:vml" fill="true" stroke="false" 
        style="width:600px;height:130px;">
  <v:fill type="gradient" color="#18235c" color2="#0d9488" angle="135"/>
  <v:textbox inset="0,0,0,0">
<![endif]-->
  <!-- Header content here -->
<!--[if gte mso 9]>
  </v:textbox>
</v:rect>
<![endif]-->
```

---

## Section Design Patterns

### Subtle callout box (AI narrative, quick take)
```html
<td style="padding: 16px 20px; 
           background-color: rgba(13, 148, 136, 0.06);
           border-left: 3px solid rgba(13, 148, 136, 0.4);
           border-radius: 0 8px 8px 0;">
  <div style="font-size: 10px; font-weight: 600; text-transform: uppercase;
              letter-spacing: 0.8px; color: #0f766e; margin-bottom: 6px;">
    MARKET INSIGHT
  </div>
  <div style="font-size: 14px; line-height: 1.6; color: #1f2937;">
    Narrative text here...
  </div>
</td>
```

### Stats row (2 or 4 metrics)
```html
<table role="presentation" width="100%" cellpadding="0" cellspacing="0">
  <tr>
    <td width="25%" align="center" style="padding: 12px 8px; 
        background-color: #f9fafb; border: 1px solid #e5e7eb;">
      <div style="font-family: Georgia, serif; font-size: 22px; font-weight: 700; 
                  color: #18235c;">28</div>
      <div style="font-size: 10px; color: #6b7280; text-transform: uppercase;">
        Homes Sold</div>
    </td>
    <!-- Repeat for each metric -->
  </tr>
</table>
```

---

## Dark Mode

```css
@media (prefers-color-scheme: dark) {
  .email-outer { background-color: #232323 !important; }
}
```

- Outer chrome: `#232323` — universal, never brand-colored
- Content area: stays white — `color-scheme: light only` prevents inversion
- Never adapt content colors for dark mode — it breaks brand consistency

---

## Mobile Responsive

```css
@media screen and (max-width: 600px) {
  .email-container { width: 100% !important; }
  .stack-on-mobile { display: block !important; width: 100% !important; }
  .hide-on-mobile { display: none !important; }
}
```

- 3-column grids → stack to 1 column
- Stats rows → stack or go to 2 columns
- Photo grids → stack to full width
- Header metric → can move below title

---

## Testing Checklist

Before shipping any email template change:
1. Open in browser — does it look right at 600px?
2. Litmus or Email on Acid test (if available)
3. Send a test to Gmail, Outlook, Apple Mail
4. Check with 4 different brand color combos (dark+teal, coral+midnight, gold+charcoal, indigo+indigo)
5. Check dark mode (Gmail app, Apple Mail dark mode)

---

## Common Email Mistakes

| Mistake | Why It Fails | Fix |
|---------|-------------|-----|
| Using `<div>` for layout | Outlook ignores div dimensions | Use `<table>` |
| Using `display: flex` | Zero email client support | Use table cells |
| Using CSS Grid | Zero email client support | Use table cells |
| Using `<style>` classes | Gmail strips them | All styles inline |
| Using `margin` for spacing | Outlook ignores on many elements | Use `padding` on `<td>` |
| Using `background-image` on `<td>` | Outlook ignores it | Use `<img>` or VML |
| Setting only `max-width` on images | Outlook uses natural image size | Set explicit `width` AND `height` |
| Using custom web fonts | Gmail strips `@import` and `<link>` | Use Georgia + system sans-serif |
| Using `position: absolute` | Unreliable across clients | Use table cell positioning |
| Forgetting `display: block` on images | Creates a gap below images in some clients | Always add it |
| Using `rgba()` on backgrounds | Outlook doesn't support rgba | Provide a hex fallback: `background-color: #hex; background-color: rgba(...);` |

---

## File Map

| File | Purpose |
|------|---------|
| `apps/worker/src/worker/email/template.py` | The ONLY file that produces email HTML — all 7 layout builders |
| `scripts/gen_email_templates.py` | Dev script to generate all email types as HTML for QA |
| `output/email_reports/` | Generated HTML outputs for visual testing |
| `apps/web/components/shared/email-preview/` | React preview component (mirrors V16 layouts) |

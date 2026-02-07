# V0 Design Prompt — Market Report Email Template

## What to Build

Design a **premium real estate market report email template** as a React component. This will be used as a visual reference for an HTML email — focus on layout, typography, color hierarchy, and visual polish rather than interactivity.

Build **two complete email mockups** side-by-side (or as tabs):
1. **Market Snapshot** — The data-heavy version with all sections
2. **New Listings Gallery** — The photo-heavy version with property cards

Both share the same header, footer, and base structure but have different content sections.

---

## Brand System

The template must be **white-label** — all brand colors come from variables:

```
Primary Color: #2563eb (blue — this is a placeholder, agent chooses their own)
Accent Color: #7c3aed (purple — secondary brand color)
```

**Critical design requirement:** Brand colors must appear throughout the email body, not just in the header. The current design has brand colors only in the header gradient — everything below is gray. Fix this by threading the primary color through section accents, metric highlights, card borders, CTA areas, and the agent footer.

---

## Email Structure — Market Snapshot

Design these sections in order, top to bottom:

### 1. Header (Gradient Band)
- Background: gradient from primary_color → accent_color (135°)
- Logo centered (placeholder: white text "Acme Realty" or a white rectangle)
- Small badge pill: brand name in semi-transparent white bubble
- Title: "Market Snapshot – Los Angeles" (large, white, clean)
- Subtitle: "Period: Last 30 Days • Source: Live MLS Data" (small, white, 90% opacity)
- **Design goal:** Premium, confident, branded. This is the first thing recipients see.

### 2. Accent Transition
- A thin branded strip (3-4px) that bridges the colorful header to the white content area
- Creates a visual "seal" effect

### 3. AI Insight Paragraph
- A short paragraph of market commentary (1-3 sentences)
- Example: "Healthy activity in Los Angeles this month—142 families found their new home at a median price of $875K. With homes averaging 34 days on market, there's time to explore without missing out."
- **Design goal:** Should feel like expert commentary, not just another data box. Subtle branded accent (left border? light tint? icon?). Readable, warm, authoritative.

### 4. Headline Metric (Hero Number)
- One dominant number: "$875K" with label "Median Sale Price" above it
- This is THE most important data point
- **Design goal:** This should be the visual anchor of the email. Big, bold, unmissable. Use brand color as an accent (background tint, underline, side bar — your call). It should NOT look like the other metric cards.

### 5. Key Metrics Row (3 cards)
- Three supporting metrics in a horizontal row:
  - "142" / Closed Sales
  - "34" / Avg Days on Market  
  - "2.8" / Months of Inventory
- **Design goal:** Clean data cards that feel like a dashboard strip. Numbers should be prominent. Use brand color as a subtle accent (top border? number color? icon dots?). Must look different from the headline metric above.

### 6. Core Indicators (Market Activity)
- Section header: "Market Activity"
- Three inline stats:
  - "89" / New Listings
  - "67" / Pending Sales
  - "96.2%" / Sale-to-List Ratio
- **Design goal:** Secondary data tier. Should clearly look like "supporting detail" vs the hero metrics above. Could be a bordered card, a subtle strip, or compact inline layout.

### 7. Property Type Breakdown
- Section header: "By Property Type"
- Horizontal layout:
  - Single Family: 98
  - Condos: 31
  - Townhomes: 13
- **Design goal:** Clean, compact. Not a chart — just labeled numbers. Visually grouped with Price Tiers below.

### 8. Price Tier Breakdown
- Section header: "By Price Range"
- Three tiers:
  - Entry Level: 42 (Under $500K)
  - Move-Up: 67 ($500K - $1M)
  - Luxury: 33 ($1M+)
- **Design goal:** Should pair visually with Property Types above (same container or visual family). Could use progress bars, colored dots, or tier badges.

### 9. Quick Take / Market Callout
- A punchy one-liner summary:
  - "Seller's market conditions: 2.8 months of inventory indicates strong demand in Los Angeles."
- **Design goal:** This is the hook that drives clicks to the full report. Give it visual presence — not buried italic text. Could be a callout card, a highlighted quote, or a branded accent strip.

### 10. CTA Button
- "View Full Report" — single primary CTA
- Brand primary_color background, white text
- **Design goal:** Clear, confident, not cramped. Give it breathing room. Consider a light branded background area around it (not just a floating button on white).

### 11. Agent Footer
- Circular agent photo (80px)
- Agent name: "Sarah Chen" (bold)
- Title: "Senior Realtor, DRE#01234567"
- Phone: (310) 555-0142
- Email: sarah@acmerealty.com
- **Design goal:** This should feel like a personal touch, not an afterthought. The agent is the sender — make their footer feel like a warm "I'm here for you" moment. Consider making phone/email into small tappable button-style elements. Light branded background.

### 12. Email Footer
- "Powered by TrendyReports" (or branded name)
- Unsubscribe link
- Small, muted, professional

---

## Email Structure — New Listings Gallery

Same header (#1) and footer (#11, #12). Different body:

### 3. AI Insight Paragraph
- "Fresh opportunities in Los Angeles—24 new properties just hit the market. With a median asking price of $725K, there's something for every buyer."

### 4. Gallery Header
- Badge: "24" + "New Listings" (count + label)
- Like a section marker showing what's below

### 5. Property Cards (6 cards in 3x2 grid)
Each card:
- **Photo** (top, 16:10 aspect ratio, fills card width)
- **Price overlay** on the photo (bottom-left or bottom, semi-transparent dark gradient with white price text — like Zillow/Redfin)
- **Address** (bold, below photo)
- **City, ZIP** (gray, smaller)
- **Details**: "3 Bed • 2 Bath • 1,850 SF" (small, gray)

Sample data for 6 cards:
1. 742 Sunset Blvd — $1,250,000 — 4 Bed / 3 Bath / 2,800 SF — Los Angeles, 90028
2. 1831 Echo Park Ave — $689,000 — 2 Bed / 2 Bath / 1,200 SF — Los Angeles, 90026
3. 4521 Franklin Ave — $925,000 — 3 Bed / 2 Bath / 1,650 SF — Los Angeles, 90027
4. 2200 Beachwood Dr — $1,475,000 — 5 Bed / 4 Bath / 3,200 SF — Los Angeles, 90068
5. 915 Hyperion Ave — $599,000 — 2 Bed / 1 Bath / 950 SF — Los Angeles, 90029
6. 3340 Waverly Dr — $1,100,000 — 4 Bed / 3 Bath / 2,400 SF — Los Angeles, 90027

**Design goal:** These cards are the star of this email. They should look like professional real estate marketing — not a database table with thumbnails. The price on the photo is key (gives it that Zillow/Redfin feel). Cards should have subtle depth (shadow, border treatment). Photos should be prominent.

### 6. Quick Take + CTA
Same as Market Snapshot version.

---

## Design Constraints & Goals

### Must-Haves
- **600px max width** (email standard)
- **Brand color threading** — primary_color appears in at least 5 places in the body, not just the header
- **Clear visual hierarchy** — someone scanning for 3 seconds should absorb: headline number → key metrics → action button
- **Professional real estate aesthetic** — think Compass market reports, not generic SaaS dashboards
- **Mobile-friendly layout** — metrics should stack cleanly at narrow widths
- **Light background** (#f5f5f4 or similar) behind the email card for depth

### Nice-to-Haves
- Subtle texture or pattern in the header (not required)
- Micro-iconography for metrics (small icons or geometric accents)
- Visual "breathing room" between sections — not wall-to-wall boxes

### Avoid
- Emojis anywhere
- Overly colorful / rainbow palette — monochromatic brand usage
- Heavy drop shadows (keep it subtle)
- Dark/moody themes — this is a professional real estate email
- Overly complex layouts that won't translate to email tables

---

## Technical Notes

This design will be **translated to HTML email tables** (not used as-is). So:
- Use visual layout as inspiration, not as implementation
- Flexbox/grid will become `<table>` in the real version
- CSS variables will become Python f-string interpolation
- Complex effects (position: absolute overlays) may need simplification for Outlook
- Focus on making the design LOOK right — we'll handle email compatibility separately

Use placeholder images from picsum.photos or similar for the property photos. Use solid color rectangles if images don't load.

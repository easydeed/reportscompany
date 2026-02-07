# V0 Prompt — TrendyReports Property Report PDF Redesign

## IMPORTANT: Read This First

I need you to design **all 7 pages** of a real estate property report PDF, rendered as a **single React component** that displays all pages stacked vertically. This is for a **print PDF** (8.5" × 11" per page), NOT a web app. Everything must work with pure HTML/CSS — no JavaScript interactivity needed.

I need **5 theme variants**. Please create them as separate tabs/views I can switch between. Each theme has a radically different visual personality but the same data and page structure.

---

## Context

This is a **Seller Property Report** — a document a real estate agent gives to a homeowner showing their property details, comparable sales, and market analysis. **Realtors are all about image.** These reports represent the agent's personal brand. They need to look like they came from a high-end design agency, not a data export.

Think: luxury real estate brochure meets data-rich market analysis. Every page should feel intentional, polished, and visually striking — even the data-heavy pages.

---

## The 5 Themes

### 1. BOLD
- **Personality:** Confident, powerful, high-impact. Think Wall Street meets luxury real estate.
- **Fonts:** Oswald (display/headers) + Inter (body)
- **Colors:** Deep navy `#0F1629` (primary) + Gold `#C9A227` (accent)
- **Design language:** Sharp geometric shapes, strong borders, uppercase text, high contrast. Gold accent bar at top. Corner triangle accent on cover. Alternating row stripes on tables.
- **Radius:** 2-4px (sharp, minimal)

### 2. CLASSIC
- **Personality:** Timeless, trustworthy, traditional luxury. Think old-money estate.
- **Fonts:** Playfair Display (display) + Source Sans Pro (body)
- **Colors:** Navy `#1B365D` (primary) + Warm tan `#8B7355` (accent)
- **Design language:** Refined serif typography, dotted dividers, subtle shadows, warm surface tones `#FDFBF7`. Feels like a printed book.
- **Radius:** 4-6px (soft, refined)

### 3. ELEGANT
- **Personality:** Boutique luxury, sophisticated, understated. Think Chanel meets real estate.
- **Fonts:** Cormorant Garamond (display, italic) + Montserrat (body)
- **Colors:** Charcoal `#1A1A1A` (primary) + Champagne `#B8977E` (accent)
- **Design language:** Delicate corner flourishes (thin L-shaped borders), italic display type, zero border radius (all sharp edges), minimal shadows, lots of whitespace. Surface tone `#FAF8F5`.
- **Radius:** 0px (deliberately sharp)

### 4. MODERN
- **Personality:** Fresh, tech-forward, energetic. Think Silicon Valley startup meets real estate.
- **Fonts:** Space Grotesk (display) + DM Sans (body)
- **Colors:** Coral `#FF6B5B` (primary) + Midnight `#1A1F36` (accent)
- **Design language:** Large border radius (12-20px), pill-shaped badges, gradient accents, decorative circles, playful geometry. Surface tone `#F1F5F9`.
- **Radius:** 12-20px (round, friendly)

### 5. TEAL
- **Personality:** Vibrant, coastal, contemporary. Think Miami luxury meets data dashboard.
- **Fonts:** Montserrat (display + body, heavy weights 700-900)
- **Colors:** Teal `#34D1C3` (primary) + Deep navy `#18235C` (accent)
- **Design language:** Bold weights, alternating colored rows (mint `#DFF6F3` + lavender `#ECEAF7`), diagonal stripe accents, mini decorative bars. High energy.
- **Radius:** 6-10px (medium, clean)

---

## Page Structure (7 Pages)

### PAGE 1: COVER
**This is the most important page. It sells the agent's brand.**

- **Full-bleed hero image** as background (use a beautiful luxury home photo from Unsplash)
- Dark gradient overlay from top to bottom so white text is readable
- **Top bar:** Thin colored accent bar spanning full width (each theme styles differently)
- **Top section:** Agent company logo (right side) + "Property Report" badge
- **Center-bottom content area (over the hero image):**
  - Property type label ("Single Family Residence") in small caps
  - **Large property address** as the headline: "1847 Hillcrest Drive"
  - City/State/ZIP below: "Beverly Hills, CA 90210"
  - Colored accent line
  - **Stats row:** 4 Beds | 3.5 Baths | 3,240 Sq Ft | 1985 Built — displayed horizontally with large numbers
- **Bottom agent bar** (white background, spanning full width):
  - Left: Agent circular headshot photo + Name "Alexandra Reynolds" + Title "Realtor® · DRE# 01234567" + Contact info
  - Right: Company logo or company name
- **Theme-specific decorative elements:**
  - Bold: Gold corner triangle (bottom-right)
  - Classic: (subtle, minimal decoration)
  - Elegant: Corner flourish brackets (thin L-shaped lines, top-left and bottom-right)
  - Modern: Decorative translucent circles (3 different sizes, scattered)
  - Teal: Diagonal stripe accent + mini vertical bars

### PAGE 2: TABLE OF CONTENTS
**Should NOT be a boring list. Make it feel designed.**

- Page header with title "Contents" and subtitle "Property Report Overview"
- 7 items listed, each with:
  - Section number (styled per theme — some use badges, some use large serif numbers)
  - Section title
  - Section subtitle/description
- **DESIGN REQUIREMENT:** Each theme should style these items uniquely:
  - Bold: Thick borders, uppercase titles, gold numbers
  - Classic: Dotted dividers, large Playfair numbers, elegant spacing
  - Elegant: Minimal lines, italic titles, large Garamond numbers, generous whitespace
  - Modern: Rounded cards for each item, coral number badges, no borders
  - Teal: Teal number badges, bold uppercase titles, thick borders
- **ADD:** A subtle sidebar accent or decorative element on this page to prevent it from feeling empty. Consider a thin vertical accent line, a decorative page number, or a muted background section.
- Footer: Agent photo (small circle) + name + phone on left, company logo on right

### PAGE 3: AERIAL VIEW
**Full visual page — the map should dominate.**

- Page header: "Aerial View" with property address as subtitle
- **Large satellite/aerial map image** filling most of the page (at least 70% of content area)
- Use a Google Maps satellite screenshot as placeholder
- **ADD:** Property pin/marker overlay or address label on the map
- **ADD:** A small info bar below the map showing: Latitude/Longitude, or Neighborhood name, or ZIP code — something to fill the space below the map with useful context
- Footer

### PAGE 4: PROPERTY DETAILS
**Data page — but make the data beautiful.**

- Page header: "Property Details"
- **Two-column layout:**
  - Left column: Property details table (Property Type, Bedrooms, Bathrooms, Sq Ft, Lot Size, Year Built, Garage, Pool, Zoning)
  - Right column: Tax Information table (APN, Assessed Value, Land Value, Improvement Value, Annual Taxes, Tax Year) + Location table (Address, City, State, ZIP, County)
- **DESIGN REQUIREMENT:** Tables should feel rich, not like spreadsheets:
  - Bold: Dark header rows, alternating gray stripes, thick borders
  - Classic: Warm cream background, thin borders, serif headers
  - Elegant: Minimal — no borders on rows, just bottom accent line under section titles
  - Modern: Rounded containers for each table, colored header bars, no visible row borders
  - Teal: Alternating mint/lavender rows, navy header bars
- **ADD:** Consider a small property summary card or key stats highlight at the top of this page before the tables. Something visual like: a horizontal bar showing key metrics (Beds/Baths/SqFt/Year) with icons.
- Footer

### PAGE 5: AREA SALES ANALYSIS ⭐ (Needs most improvement)
**This page currently looks empty. It needs visual weight and storytelling.**

- Page header: "Area Sales Analysis"
- **Price Range Display (hero element):** A visually prominent section showing:
  - LOW: $1,975,000
  - MEDIAN: $2,100,000 (highlighted/emphasized)
  - HIGH: $2,280,000
  - This should NOT be three plain text items. Design it as a visual element — a large card, a horizontal bar chart, colored blocks, or a gradient strip with markers.
- **Market Statistics Grid:** 4 stats in a 2×2 or 4-column layout:
  - 4 Comparables found
  - 3,183 Avg Sq Ft
  - 4.25 Avg Beds
  - 3.38 Avg Baths
- **ADD A COMPARISON TABLE:** This is crucial — show a table comparing the subject property vs the comparable averages:

  | Metric | Subject Property | Comp Average | Difference |
  |--------|-----------------|--------------|------------|
  | Price | $2,100,000 | $2,113,750 | -$13,750 |
  | Sq Ft | 3,240 | 3,183 | +57 |
  | Beds | 4 | 4.25 | -0.25 |
  | Baths | 3.5 | 3.38 | +0.12 |
  | $/Sq Ft | $648 | $665 | -$17 |

  Style the "Difference" column with green (positive) / red (negative) indicators.

- **ADD:** A simple horizontal bar chart or visual indicator showing where the subject property sits in the price range relative to comps
- Footer

### PAGE 6: SALES COMPARABLES ⭐ (Needs most improvement)
**This is where agents prove their value. Each comp needs to look like a mini property listing.**

- Page header: "Sales Comparables"
- **2×2 grid of comparable property cards** (4 cards total)
- **Each card must include:**
  - **PROPERTY PHOTO** (180-200px tall) — Use different Unsplash luxury home photos for each card. This is critical — the current design uses tiny 100px Google Maps satellite thumbnails. We need actual property photos.
  - Card header bar with: Comp number (#1, #2, etc.) + Sale price ($2,150,000)
  - Property address
  - Quick stats: 4 bd · 3 ba · 3,100 sqft
  - Detail stats row: $/sqft, Sold date, Distance from subject
- **Card design should feel premium:**
  - Bold: Sharp borders, dark headers, gold accents
  - Classic: Subtle shadows, refined serif typography
  - Elegant: No border radius, thin borders, italic addresses
  - Modern: Large rounded corners, gradient headers, pill-shaped badges
  - Teal: Navy headers, teal number badges, bold typography
- **PHOTO IS THE #1 PRIORITY ON THIS PAGE.** The photos make or break whether an agent uses this report. If the cards don't have prominent, beautiful photos, the agent won't use the product.
- Footer

### PAGE 7: RANGE OF SALES ⭐ (Needs significant improvement)
**Price positioning page — show where this property sits in the market.**

- Page header: "Range of Sales"
- **Visual Price Range Bar:**
  - A prominent horizontal gradient bar showing the price range from LOW to HIGH
  - A marker/pin showing where the subject property's estimated value sits
  - The marker should have a label showing the estimated price
  - Make this bar at least 40px tall with clear visual styling per theme
- **Comparable Properties List:**
  - Each comp in a styled row showing: Address + Sale Price
  - Rows should clearly show the progression from lowest to highest price
  - Consider adding a visual indicator (colored dot or bar) showing each comp's position relative to the range
- **ADD: Summary Statistics Block:**
  - Average price per sq ft across comps
  - Average days on market (use "12 days" as placeholder)
  - Price per sq ft trend indicator
  - Number of active listings in area (use "8" as placeholder)
- **ADD:** A brief text area for "Market Insight" — a 2-3 sentence summary. Use placeholder text like: "Based on 4 comparable sales within 0.6 miles, the estimated market value for this property falls between $1,975,000 and $2,280,000. The median comparable sold at $2,100,000, suggesting strong market positioning."
- Footer

---

## Sample Data (Use This Exactly)

**Property:**
- Address: 1847 Hillcrest Drive, Beverly Hills, CA 90210
- 4 beds, 3.5 baths, 3,240 sqft, lot 8,500 sqft
- Year built: 1985
- APN: 4328-015-023
- Owner: Sarah & Michael Chen
- Assessed value: $1,850,000
- Annual taxes: $21,500
- Property type: Single Family Residence

**Agent:**
- Name: Alexandra Reynolds
- Title: Realtor® · DRE# 01234567
- Phone: (310) 555-0147
- Email: alexandra@luxuryestates.com
- Company: Luxury Estates Group
- Use a professional headshot photo from Unsplash

**4 Comparables:**

| # | Address | Price | Sq Ft | Beds | Baths | Year | $/SqFt | Sold | Distance |
|---|---------|-------|-------|------|-------|------|--------|------|----------|
| 1 | 1923 Sunset Ridge | $2,150,000 | 3,100 | 4 | 3 | 1992 | $694 | 01/15/2024 | 0.3 mi |
| 2 | 2045 Canyon View | $1,975,000 | 2,980 | 4 | 3.5 | 1988 | $663 | 02/08/2024 | 0.5 mi |
| 3 | 1756 Laurel Heights | $2,280,000 | 3,450 | 5 | 4 | 1995 | $661 | 01/28/2024 | 0.4 mi |
| 4 | 2112 Oak Terrace | $2,050,000 | 3,200 | 4 | 3 | 1990 | $641 | 02/20/2024 | 0.6 mi |

**Stats:**
- Price range: $1,975,000 - $2,280,000
- Median: $2,100,000
- Avg sqft: 3,183
- Avg beds: 4.25
- Avg baths: 3.38

---

## Technical Requirements

1. **Page size:** Each page must be exactly 8.5in × 11in (612px × 792px at 72dpi, or use CSS `width: 8.5in; height: 11in`)
2. **Pages stack vertically** with a gap between them (simulating a PDF preview)
3. **Use real images** from Unsplash for:
   - Cover hero: A luxury home exterior (different per theme)
   - Agent headshot: Professional portrait
   - Comp photos: 4 different luxury homes
   - Aerial map: Use a Google Maps satellite-style image or a map placeholder
4. **Print CSS:** Include `@page { size: Letter; margin: 0; }` and `@media print` rules that remove shadows and gaps
5. **Colors as CSS variables** in `:root` so they can be overridden
6. **Each page has a consistent footer:** Agent photo (small circle) + name + phone on left, company logo/name on right, separated by a thin top border
7. **No JavaScript interactivity** inside the pages — this renders to a static PDF
8. **Use the theme's font pairing** — load from Google Fonts via link tags

---

## What Makes This Outstanding

- **The cover should make a realtor proud to put their name on it.** Full hero photo, elegant typography, professional branding.
- **The comparables page should make homeowners say "wow."** Large property photos, clean data, premium card design.
- **The analysis page should tell a visual story** — not just display numbers. Show where the property sits, how it compares, what the market looks like.
- **Every page should feel intentional** — even the data tables should look designed, not generated.
- **White space is your friend** — don't cram data. Let things breathe. This is luxury real estate, not a spreadsheet.

---

## Deliverable

A single React component with a theme switcher that lets me view all 7 pages for each of the 5 themes. Each theme should feel like it came from a completely different design studio while maintaining the same data structure and page flow.

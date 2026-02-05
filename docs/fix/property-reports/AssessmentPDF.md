Property Report PDF System — Complete Audit Report
A. Current State Summary
Theme Comparison Matrix
Attribute	Bold	Classic	Elegant	Modern	Teal
--pad (internal margin)	0.5in	0.6in	0.6in	0.55in	0.55in
Page size	Letter (8.5x11)	Letter	Letter	Letter	Letter
@page margin	0	0	0	0	0
Footer bottom	0.4in	0.4in	0.4in	0.4in	0.3in
Page count	7 pages	7 pages	7 pages	7 pages	7 pages
Primary font	Oswald	Merriweather	Playfair Display	Space Grotesk	Montserrat
Body font	Montserrat	Source Sans Pro	Montserrat	DM Sans	Montserrat
Primary color var	--navy (#15216E)	--navy (#1B365D)	--burgundy (#1a1a1a)	--coral (#FF6B5B)	--teal (#34d1c3)
Accent color var	--gold (#D69649)	--sky (#4A90A4)	--gold (#C9A962)	gradient coral	--navy (#18235c)
Cover layout	Full-bleed navy bg	Header + centered title	Full-bleed burgundy	Split 50/50 grid	Full-bleed navy
Contents layout	Full-page with header	Full-page standard	Decorative flourishes	Split 2-column	Split panel overlay
Table styling	Striped odd rows	Striped even rows	Striped even rows	Ghost bg cards	Custom colorful rows
Border radius	10-12px	8-10px	8-14px	20px	10-14px
Inconsistencies Found
1. Padding/Margin Inconsistencies
--pad varies: 0.5in (Bold), 0.55in (Modern, Teal), 0.6in (Classic, Elegant)
Footer bottom position varies: 0.3in (Teal) vs 0.4in (all others)
Cover page insets vary wildly between themes
2. Font Loading
All use Google Fonts (good)
Fonts loaded differently per theme (inconsistent preconnect patterns)
Font fallbacks vary (some use system-ui, others use serif)
3. CSS Variable Naming
Primary color: --navy, --burgundy, --coral, --teal (should be --primary)
No shared variable naming convention
Some themes duplicate color definitions
4. Print Media Handling
All have @page { size: Letter; margin: 0; } ✅
All have page-break-after: always ✅
Print background colors: consistent ✅
But page break handling varies slightly
5. Layout Approaches
Teal: Uses absolute positioning heavily (.abs, .cover-content inset:)
Modern: Uses CSS Grid for cover (split layout)
Classic/Bold/Elegant: Use flexbox primarily
Contents page: 5 completely different approaches
6. Table Striping
Bold: odd rows colored
Classic/Elegant: even rows colored
Modern: no striping, card-based
Teal: alternating custom colors (--rowA, --rowB)
What IS Consistent
✅ Page structure: All themes have exactly 7 pages in same order
Cover → Contents → Aerial → Property → Analysis → Comparables → Range
✅ Page dimensions: All use Letter (8.5in × 11in)
✅ @page CSS rule: All set margin: 0 in CSS
✅ Data contract: All templates use identical Jinja2 variables
✅ Page break handling: All use page-break-after: always
✅ Color accuracy: All use -webkit-print-color-adjust: exact
B. Template Deep Dive (Per Theme)
1. BOLD Theme
CSS Variables:

--navy: {{ theme_color | default('#15216E') }};
--navy-light: #1E2D8F;
--gold: #D69649;
--gold-light: #E5AB5E;
--cream: #FDF8F3;
--warm-white: #FFFFFF;
--charcoal: #1A1A1A;
--slate: #4A4A4A;
--border: #E8E4DF;
--page-w: 8.5in;
--page-h: 11in;
--pad: 0.5in;
--shadow: 0 8px 30px rgba(21, 33, 110, 0.15);

Typography Scale:

Element	Font	Size	Weight
Cover title	Oswald	72px	700
Cover address	Oswald	32px	600
Page title	Oswald	42px	600
Section header	Oswald	14px	600
Body text	Montserrat	12-15px	400-600
Table header	-	11px	600
Footer brand	-	10px	600
Spacing System:

--pad: 0.5in (page padding)
Cover header: 0.35in var(--pad)
Cover main: 0 1in
Cover bottom: 0.4in var(--pad)
Page header: 20px 25px
Aerial header: 0.4in var(--pad)
Footer bottom: 0.4in
Color Tokens:

Primary: --navy (#15216E)
Accent: --gold (#D69649)
Background: --cream (#FDF8F3)
Text: --charcoal (#1A1A1A)
Muted: --slate (#4A4A4A)
Border: --border (#E8E4DF)
Unique Features:

Hero background image with 15% opacity overlay on cover
Accent line with gold/navy split (accent-line::after 60% width)
Bold uppercase typography throughout
Gradient bars in charts (gold → navy)
Top-left price badge on comp cards
2. CLASSIC Theme
CSS Variables:

--navy: {{ theme_color | default('#1B365D') }};
--navy-light: #2C4A7C;
--sky: #4A90A4;
--sand: #C4B7A6;
--cream: #FDFBF7;
--warm-white: #FFFFFF;
--charcoal: #333333;
--slate: #5C6670;
--border: #E0DCD4;
--page-w: 8.5in;
--page-h: 11in;
--pad: 0.6in;
--shadow: 0 4px 20px rgba(27, 54, 93, 0.1);

Typography Scale:

Element	Font	Size	Weight
Cover title	Merriweather	58px	900
Cover address	Merriweather	28px	700
Page title	Merriweather	36px	900
Contents number	Merriweather	24px	900
Body text	Source Sans Pro	13-16px	400-600
Agent name	Merriweather	22px	700
Spacing System:

--pad: 0.6in (page padding)
Cover top: 0.5in var(--pad)
Cover main: 0.5in 1in
Cover bottom: 0.4in var(--pad)
Page header: padding-bottom: 15px, margin-bottom: 30px
Footer bottom: 0.4in
Color Tokens:

Primary: --navy (#1B365D)
Accent: --sky (#4A90A4)
Warm accent: --sand (#C4B7A6)
Background: --cream (#FDFBF7)
Text: --charcoal (#333333)
Muted: --slate (#5C6670)
Unique Features:

Two-tone divider (navy + sky ::after 40% width)
Agent photo in cover bottom section
Contents with dotted leaders
Traditional serif typography
Page header with border-bottom accent
3. ELEGANT Theme
CSS Variables:

--burgundy: {{ theme_color | default('#1a1a1a') }};
--burgundy-dark: #0d0d0d;
--gold: #C9A962;
--gold-light: #E8D5A3;
--cream: #FAF7F2;
--cream-dark: #F0EBE3;
--charcoal: #2D2D2D;
--slate: #5A5A5A;
--page-w: 8.5in;
--page-h: 11in;
--pad: 0.6in;
--shadow: 0 15px 50px rgba(114,47,55,0.15);

Typography Scale:

Element	Font	Size	Weight
Cover title	Playfair Display	72px	400
Cover subtitle	Playfair Display (italic)	64px	400
Page title	Playfair Display	48px	400
Section title	Playfair Display	18px	500
Body text	Montserrat	11-15px	300-500
Agent name	Playfair Display	22px	-
Spacing System:

--pad: 0.6in
Cover header: 0.5in 0.6in
Cover main: 0 1in
Cover footer: 0.5in 0.6in
Contents header: 0.3in 0 0.5in, border-bottom margin 0.4in
Footer bottom: 0.4in
Color Tokens:

Primary: --burgundy (#1a1a1a) - Note: defaults to dark, not burgundy!
Accent: --gold (#C9A962)
Light accent: --gold-light (#E8D5A3)
Background: --cream (#FAF7F2)
Text: --charcoal (#2D2D2D)
Unique Features:

Corner flourishes (corner-flourish with L-shaped gold lines)
Diamond decorative elements (.diamond)
Gold rule dividers with gradient fade
Circular agent photo with gold border
Luxury serif aesthetic
4. MODERN Theme
CSS Variables:

--coral: {{ theme_color | default('#FF6B5B') }};
--coral-light: #FF8A7D;
--coral-dark: #E55A4B;
--midnight: #1A1F36;
--slate: #4A5568;
--silver: #94A3B8;
--ghost: #F1F5F9;
--pure: #FFFFFF;
--gradient-coral: linear-gradient(135deg, var(--coral), #FF8A7D, #FFB199);
--gradient-dark: linear-gradient(135deg, #1A1F36, #2D3348);
--page-w: 8.5in;
--page-h: 11in;
--pad: 0.55in;
--radius: 20px;
--shadow: 0 20px 60px rgba(26,31,54,0.15);

Typography Scale:

Element	Font	Size	Weight
Cover title	Space Grotesk	56px	700
Cover address	Space Grotesk	22px	600
Page title	Space Grotesk	30-52px	700
Contents number	Space Grotesk	14px	700
Body text	DM Sans	11-15px	400-600
Agent name	Space Grotesk	18px	700
Spacing System:

--pad: 0.55in
Cover left/right: 0.6in padding
Cover photo area: 0.6in inset from top/sides, 3in from bottom
Contents left: width: 45%, padding-right: 40px
Contents right: padding: 40px
Footer bottom: 0.4in
Color Tokens:

Primary: --coral (#FF6B5B)
Dark: --midnight (#1A1F36)
Muted: --slate (#4A5568)
Light muted: --silver (#94A3B8)
Background: --ghost (#F1F5F9)
Surface: --pure (#FFFFFF)
Unique Features:

Split 50/50 cover layout (dark left, light right)
Decorative coral circles with pseudo-elements
Glassmorphism address box (backdrop-filter: blur)
Pill-shaped labels (.pill)
Gradient backgrounds
Large border-radius (20px)
Card-based property items
5. TEAL Theme
CSS Variables:

--teal: {{ theme_color | default('#34d1c3') }};
--teal-2: {{ theme_color | default('#21c7b7') }};
--navy: #18235c;
--navy-2: #0f1a45;
--ink: #0b0f1a;
--muted: #6b7280;
--paper: #ffffff;
--bg: #f4f6fb;
--line: #e6e9f2;
--soft: #eef2ff;
--rowA: #dff6f3;
--rowB: #eceaf7;
--page-w: 8.5in;
--page-h: 11in;
--pad: 0.55in;
--radius: 14px;
--shadow: 0 10px 30px rgba(0,0,0,.12);

Typography Scale:

Element	Font	Size	Weight
Cover title	Montserrat	64px	900
Cover subtitle	Montserrat	58px	300
Section title	Montserrat	28-38px	900
Cover address	Montserrat	32px	800
Body text	Montserrat	11-14px	400-700
Agent name	Montserrat	15px	900
Spacing System:

--pad: 0.55in
Cover content: inset: 0.8in 0.7in 2.5in
Cover footer: height: 2.4in, padding: 0.4in 0.6in
Cover stripe: bottom: 2.4in
Contents panel: right: 0.6in, top: 0.7in, bottom: 0.7in
Map card: bottom: 0.85in, height: 5.2in
Footer bottom: 0.3in (different from others!)
Color Tokens:

Primary: --teal (#34d1c3)
Secondary: --navy (#18235c)
Dark: --navy-2 (#0f1a45)
Text: --ink (#0b0f1a)
Muted: --muted (#6b7280)
Background: --bg (#f4f6fb)
Table row A: --rowA (#dff6f3)
Table row B: --rowB (#eceaf7)
Unique Features:

Overlay-based cover (gradient + stripe)
Contents page with floating panel over dark background
Mini decorative bars (.mini-bars)
Pin markers with concentric circles
Colorful alternating table rows (teal/purple tint)
Slider with caret indicators
Most detailed/complex template
C. Data Flow
Pipeline: API → Worker → Template → PDF
┌─────────────────────────────────────────────────────────────────────────┐
│                             API Layer                                    │
├─────────────────────────────────────────────────────────────────────────┤
│  1. POST /property-reports                                              │
│     • Validates input (PropertyReportContext schema)                    │
│     • Creates DB record with status='pending'                           │
│     • Enqueues Celery task: generate_property_report.delay(report_id)   │
└───────────────────────────────────┬─────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                           Worker Layer                                   │
├─────────────────────────────────────────────────────────────────────────┤
│  2. Celery Task: generate_property_report()                             │
│     a. fetch_report_with_joins(report_id)                               │
│        • Queries property_reports + users + accounts + affiliate_branding│
│        • Returns structured dict with agent{}, branding{}               │
│                                                                         │
│     b. PropertyReportBuilder(report_data)                               │
│        • Resolves theme (number → name)                                 │
│        • Sets up Jinja2 environment with custom filters                 │
│        • Registers filters: format_currency, format_number, truncate    │
│                                                                         │
│     c. builder.render_html()                                            │
│        • Builds unified context (property, agent, comparables, stats)   │
│        • Selects template: THEME_TEMPLATES[theme_name]                  │
│        • Renders Jinja2 template with context                           │
│                                                                         │
│     d. render_pdf(run_id, account_id, html_content)                     │
│        • Playwright (local): margins 0.5in, format Letter               │
│        • PDFShift (prod): margins 0, format Letter, CSS handles margins │
│                                                                         │
│     e. upload_to_r2(local_path, s3_key)                                 │
│        • Uploads to Cloudflare R2                                       │
│        • Returns public URL                                             │
│                                                                         │
│     f. update_report_status(report_id, 'complete', pdf_url)             │
└─────────────────────────────────────────────────────────────────────────┘

Data Fields Available to Templates
property object:

property.street_address    # "123 Main St"
property.city              # "Los Angeles"
property.state             # "CA"
property.zip_code          # "90210"
property.full_address      # "123 Main St, Los Angeles, CA 90210"
property.owner_name        # "John Doe"
property.secondary_owner   # "Jane Doe"
property.county            # "Los Angeles"
property.apn               # "1234-567-890"
property.bedrooms          # 4
property.bathrooms         # 2.5
property.sqft              # 2200
property.lot_size          # 7500
property.year_built        # 1985
property.garage            # 2
property.pool              # "Yes" or None
property.zoning            # "R1"
property.property_type     # "Single Family"
property.assessed_value    # 650000
property.land_value        # 200000
property.improvement_value # 450000
property.tax_amount        # 8500
property.tax_year          # 2024
property.legal_description # "LOT 1 BLK 2..."
property.census_tract      # "1234.01"

agent object:

agent.name           # "Jane Agent"
agent.title          # "Realtor®"
agent.license        # "CA BRE#01234567"
agent.phone          # "(555) 123-4567"
agent.email          # "jane@example.com"
agent.company_name   # "Acme Realty"
agent.photo_url      # "https://..."
agent.logo_url       # "https://..."
agent.company_short  # "TR" (for logo text)
agent.company_tagline # "Real Estate Excellence"

comparables list (each item):

comp.address         # "456 Oak Ave"
comp.sale_price      # 725000 (raw number)
comp.sold_date       # "01/15/2024"
comp.sqft            # 2100
comp.bedrooms        # 4
comp.bathrooms       # 2
comp.year_built      # 1990
comp.lot_size        # 6500
comp.price_per_sqft  # 345
comp.distance_miles  # 0.3
comp.map_image_url   # Google Static Maps URL
comp.pool            # True/False

stats object:

stats.total_comps    # 4
stats.avg_sqft       # 2050
stats.avg_beds       # 3.5
stats.avg_baths      # 2.25
stats.price_low      # 650000
stats.price_high     # 800000
stats.piq.sqft       # Subject property sqft
stats.piq.bedrooms   # Subject property beds
stats.low.price      # Lowest comp price
stats.medium.price   # Median comp price
stats.high.price     # Highest comp price

images object:

images.hero          # Cover background image URL
images.aerial_map    # Google Static Maps aerial URL

theme_color: Custom primary color override (hex)

Conditional Logic Examples
{% if images.hero %}...{% endif %}                    # Show hero if exists
{% if agent.photo_url %}...{% endif %}                # Show agent photo
{% for comp in comparables[:4] %}...{% endfor %}      # Max 4 comps
{{ property.pool | default('None') }}                 # Default values
{{ comp.sale_price | format_currency }}               # Custom filters

D. Recommendations
1. Proposed Standardized Base System
Create a shared CSS variables file that all themes inherit:

/* base_variables.css - Shared across all themes */
:root {
  /* Page dimensions (immutable) */
  --page-width: 8.5in;
  --page-height: 11in;
  
  /* Standardized margins (CRITICAL FOR PDF CONSISTENCY) */
  --page-margin: 0.5in;           /* Internal content margin */
  --footer-bottom: 0.4in;         /* Footer position from bottom */
  --header-margin-bottom: 0.3in;  /* Space below page headers */
  
  /* Theme-specific (override in each theme) */
  --color-primary: inherit;
  --color-accent: inherit;
  --color-background: inherit;
  --color-surface: inherit;
  --color-text: inherit;
  --color-text-muted: inherit;
  --color-border: inherit;
  
  /* Typography (theme-specific) */
  --font-display: inherit;
  --font-body: inherit;
  
  /* Shared spacing scale */
  --space-xs: 4px;
  --space-sm: 8px;
  --space-md: 16px;
  --space-lg: 24px;
  --space-xl: 40px;
  
  /* Shared border radius */
  --radius-sm: 6px;
  --radius-md: 10px;
  --radius-lg: 16px;
}

2. What Should Be Theme-Specific vs Shared
SHARED (in base template/CSS):

Page dimensions and @page rules
Print media queries
Page footer structure and positioning
.sheet and .page base classes
Page break handling
Color accuracy settings
Custom Jinja2 filters
THEME-SPECIFIC:

Color palette (primary, accent, background)
Font families (display + body)
Cover page layout/design
Contents page layout
Table styling (borders, striping)
Card/section styling
Decorative elements (flourishes, dividers)
Border radius values
Shadow definitions
3. Bugs and Issues Found
Issue	Severity	Location	Description
Margin mismatch	HIGH	pdf_engine.py	Playwright uses 0.5in margins, PDFShift uses 0 (CSS handles it). This causes different output!
Footer position	MEDIUM	Teal theme	Uses 0.3in bottom vs 0.4in in others - footer will be in different position
Elegant burgundy default	LOW	elegant_report.jinja2	--burgundy defaults to #1a1a1a (black), not burgundy
Missing fallback fonts	LOW	All themes	Some themes lack proper font-family fallbacks
Hardcoded strings	LOW	All themes	"TrendyReports" hardcoded in footers instead of using agent.company_name
Chart height variance	LOW	Templates	Teal: 2.8in, others vary. Should be standardized
Analysis table rows	LOW	Modern/Teal	Modern missing "Lot Size" row, Teal has "Stories" and "Pools" extras
4. Migration Strategy
Phase 1: Create Base Infrastructure (Non-Breaking)

Create base.css with shared variables
Create base_print.css with print rules
Create shared Jinja2 macros for:
Page footer
Page header
Comp card
Stats table
Test alongside existing templates
Phase 2: Standardize PDF Engine

Remove Playwright margins (set to 0 like PDFShift)
Update all templates to use CSS margins via --page-margin
Test PDF output consistency between engines
Phase 3: Refactor Themes Incrementally

Start with Teal (most complex) - extract to base + theme overrides
Update Classic next (simplest)
Continue with Bold, Elegant, Modern
Create base_property_report.jinja2 with {% block %} structure
Phase 4: Template Inheritance

{# base_property_report.jinja2 #}
<!doctype html>
<html>
<head>
  {% include "shared/base_styles.css" %}
  {% block theme_styles %}{% endblock %}
</head>
<body>
  <div class="sheet">
    {% block cover %}{% endblock %}
    {% block contents %}{% endblock %}
    {% block aerial %}{% endblock %}
    {% block property %}{% endblock %}
    {% block analysis %}{% endblock %}
    {% block comparables %}{% endblock %}
    {% block range %}{% endblock %}
  </div>
</body>
</html>

{# teal_report.jinja2 #}
{% extends "base_property_report.jinja2" %}

{% block theme_styles %}
  <style>
    :root {
      --color-primary: var(--teal);
      --color-accent: var(--navy);
      --font-display: 'Montserrat', sans-serif;
    }
    /* Theme-specific overrides */
  </style>
{% endblock %}

{% block cover %}
  {# Teal-specific cover design #}
{% endblock %}

E. Answers to Specific Questions
1. Can we create a single base_property_report.jinja2 that all themes extend?
Yes, using Jinja2 template inheritance with {% extends %} and {% block %}. However, the cover and contents pages are so different across themes that they'd need to be fully overridden in each theme. Shared blocks would work well for: aerial, property, analysis, comparables, and range pages.

2. What's the minimum set of CSS variables needed for consistent theming?
--color-primary
--color-accent  
--color-background
--color-surface
--color-text
--color-text-muted
--color-border
--font-display
--font-body
--page-margin (currently --pad)
--footer-bottom
--radius-md
--shadow-md

3. Are there any hardcoded values that should be variables?
Footer bottom position (0.3in vs 0.4in)
"TrendyReports" brand name in footers
Chart heights (2.8in, 3.8in, 4in, etc.)
Map heights (5.1in, 5.2in, 6.5in)
Cover content insets
Table cell padding
4. Is the page structure identical across themes?
Yes, all 7 pages are identical in order and purpose:

Cover
Contents
Aerial View
Property Details
Area Sales Analysis
Sales Comparables
Range of Sales
5. What would break if we standardized margins to exactly 0.5" on all sides?
Teal theme: Cover content positioned via inset: 0.8in 0.7in 2.5in would need adjustment
Classic theme: Content using 0.6in padding would compress slightly
Elegant theme: Same as Classic
Contents pages: Panel/overlay positioning would shift
Minimal visual impact on inner content pages (property, analysis, comps, range)
6. Are fonts loaded consistently?
No. Each theme has its own <link> tags. Font fallbacks vary:

Bold: sans-serif
Classic: serif
Elegant: system-ui, sans-serif
Modern: system-ui, sans-serif
Teal: system-ui, -apple-system, Segoe UI, Roboto, Arial, sans-serif
Recommendation: Standardize fallback to system-ui, -apple-system, sans-serif for all.

7. Is print CSS properly separated from screen CSS?
Partially. All themes have @media print blocks, but print rules are interspersed with screen rules. A cleaner approach would be:

All shared print rules in @media print { } block at end
Screen-only rules in @media screen { }
8. Any z-index issues or overlapping elements?
Teal cover: Multiple overlays with z-index:2 - works but fragile
Modern cover: Pseudo-elements with circles could overlap content on different viewport sizes
Elegant: Corner flourishes with opacity: 0.12 - safe
9. Are images/photos handled consistently?
Mostly yes:

All use object-fit: cover
All have placeholder backgrounds
Aspect ratios vary:
Comp card images: 130-140px height
Map cards: 4-6.5in height
Agent photos: 70-90px circles
Inconsistency: Some use <img> tags, others use background-image CSS.

10. Is there proper error handling for missing data?
Yes, handled well via Jinja2:

{{ property.pool | default('None') }}
{% if agent.photo_url %}...{% endif %}
{{ stats.piq.price | format_currency }}  # Filter handles None

The PropertyReportBuilder class also provides fallbacks in context building.

Summary
The current system is functional but has significant inconsistencies that will cause maintenance headaches and PDF rendering differences between environments. The top priorities for standardization are:

Fix PDF engine margin mismatch (Playwright vs PDFShift)
Standardize --pad to 0.5in across all themes
Standardize footer position to 0.4in
Create shared base CSS with common variables
Extract reusable Jinja2 macros for common components
# Cursor Prompt: Generate Page Preview JPGs for Theme Selector

## Task

Generate JPG preview images for each page of each property report theme. These replace the decorative line placeholders in the property wizard's theme selector (`step-theme.tsx`).

We already generate cover page JPGs (`/previews/1-5.jpg`) using Playwright/PDFShift. Extend that same approach to generate per-page previews.

---

## What to Generate

For each of the 5 themes (Classic=1, Modern=2, Elegant=3, Teal=4, Bold=5), generate a JPG preview of each report page:

| Page Key | Page Name | Content Description |
|---|---|---|
| `cover` | Cover Page | Theme cover with gradient/photo, property address, agent branding |
| `details` | Property Details | Key stats bar, property details table, features |
| `aerial` | Aerial View | Map image with address overlay, neighborhood context |
| `comparables` | Comparables | Comp cards with photos, price, specs |
| `range` | Range of Sales | Price range visualization, comp dots on gradient bar |
| `market` | Market Trends | Market metrics — median price, DOM, inventory |
| `overview` | Executive Summary | AI-generated narrative text page |

**5 themes × 7 pages = 35 JPG files**

---

## Output Location

Store generated previews at:

```
apps/web/public/previews/pages/{themeId}/{pageKey}.jpg
```

Example file tree:
```
apps/web/public/previews/pages/
├── 1/                    # Classic
│   ├── cover.jpg
│   ├── details.jpg
│   ├── aerial.jpg
│   ├── comparables.jpg
│   ├── range.jpg
│   ├── market.jpg
│   └── overview.jpg
├── 2/                    # Modern
│   ├── cover.jpg
│   ├── details.jpg
│   └── ...
├── 3/                    # Elegant
├── 4/                    # Teal
└── 5/                    # Bold
```

---

## Generation Approach

### Option A: Script Using Existing PDF Pipeline (Recommended)

Create a script that:
1. Renders each theme's full report HTML using the existing Jinja2 templates with sample data
2. Uses Playwright to render each page as a screenshot (JPG)
3. Saves to the public previews directory

**Script location:** `apps/worker/scripts/generate_page_previews.py`

```python
"""
Generate JPG previews for each page of each property report theme.

Usage:
  python -m scripts.generate_page_previews

Outputs to: apps/web/public/previews/pages/{theme_id}/{page_key}.jpg
"""

import asyncio
import os
from pathlib import Path
from playwright.async_api import async_playwright

# Import the existing property builder and template system
from worker.property_builder import PropertyReportBuilder
from worker.templates.property import THEME_TEMPLATES

# Sample data that produces a complete report with all pages
SAMPLE_DATA = {
    "property": {
        "street_address": "2847 Waverly Drive",
        "city": "Silver Lake",
        "state": "CA",
        "zip_code": "90039",
        "bedrooms": 3,
        "bathrooms": 2,
        "sqft": 1850,
        "lot_size": 5200,
        "year_built": 1928,
        "list_price": 1295000,
        "property_type": "Single Family",
        "latitude": 34.0870,
        "longitude": -118.2700,
    },
    "comparables": [
        # 5-6 sample comps with realistic data
        {
            "street_address": "1420 Micheltorena St",
            "city": "Silver Lake",
            "state": "CA",
            "zip_code": "90026",
            "sale_price": 875000,
            "sold_date": "2025-01-15",
            "sqft": 1200,
            "bedrooms": 2,
            "bathrooms": 2,
            "year_built": 2019,
            "distance_miles": 0.4,
            "photo_url": "https://images.unsplash.com/photo-1600585154340-be6161a56a0c?w=400&h=300&fit=crop",
            "map_image_url": None,
        },
        {
            "street_address": "3021 Sunset Blvd",
            "city": "Silver Lake",
            "state": "CA",
            "zip_code": "90039",
            "sale_price": 2150000,
            "sold_date": "2025-02-01",
            "sqft": 2800,
            "bedrooms": 4,
            "bathrooms": 3.5,
            "year_built": 2024,
            "distance_miles": 0.6,
            "photo_url": "https://images.unsplash.com/photo-1600596542815-ffad4c1539a9?w=400&h=300&fit=crop",
            "map_image_url": None,
        },
        {
            "street_address": "915 Hyperion Ave",
            "city": "Silver Lake",
            "state": "CA",
            "zip_code": "90027",
            "sale_price": 599000,
            "sold_date": "2024-12-20",
            "sqft": 950,
            "bedrooms": 2,
            "bathrooms": 1,
            "year_built": 1965,
            "distance_miles": 0.8,
            "photo_url": "https://images.unsplash.com/photo-1600607687939-ce8a6c25118c?w=400&h=300&fit=crop",
            "map_image_url": None,
        },
        {
            "street_address": "3340 Silver Lake Blvd",
            "city": "Silver Lake",
            "state": "CA",
            "zip_code": "90039",
            "sale_price": 1100000,
            "sold_date": "2025-01-28",
            "sqft": 2400,
            "bedrooms": 4,
            "bathrooms": 3,
            "year_built": 1942,
            "distance_miles": 0.5,
            "photo_url": "https://images.unsplash.com/photo-1600566753190-17f0baa2a6c3?w=400&h=300&fit=crop",
            "map_image_url": None,
        },
    ],
    "market_trends": {
        "median_sale_price": 925000,
        "avg_dom": 24,
        "active_listings": 42,
        "months_of_inventory": 2.1,
        "sale_to_list_ratio": 101.3,
        "price_per_sqft": 687,
    },
    "overview_text": "This beautifully maintained 1928 Craftsman in the heart of Silver Lake offers an exceptional blend of period charm and modern updates. The property's location on Waverly Drive provides easy access to Sunset Junction's vibrant dining and shopping scene while maintaining a quiet, tree-lined residential feel. Recent comparable sales in the immediate area suggest strong demand, with homes in this condition and location commanding premium prices. The current market dynamics — low inventory at 2.1 months and a sale-to-list ratio above 100% — favor sellers, making this an opportune time to position the property competitively.",
    "agent": {
        "name": "Sarah Chen",
        "title": "Senior Realtor",
        "phone": "(310) 555-1234",
        "email": "sarah@acmerealty.com",
        "license": "DRE #01234567",
        "photo_url": "https://randomuser.me/api/portraits/women/44.jpg",
        "brokerage": "Acme Realty",
    },
}

THEMES = {
    1: "classic",
    2: "modern",
    3: "elegant",
    4: "teal",
    5: "bold",
}

PAGE_KEYS = ["cover", "details", "aerial", "comparables", "range", "market", "overview"]

# Map page keys to the page identifiers used in the template system
PAGE_KEY_TO_TEMPLATE_PAGE = {
    "cover": "cover",
    "details": "details",
    "aerial": "aerial",
    "comparables": "comparables",
    "range": "range",
    "market": "market_trends",
    "overview": "overview",
}

OUTPUT_BASE = Path(__file__).resolve().parents[2] / "apps" / "web" / "public" / "previews" / "pages"
# Adjust this path based on your actual project structure — it should resolve to
# apps/web/public/previews/pages/


async def generate_previews():
    """Generate JPG previews for all themes and pages."""

    async with async_playwright() as p:
        browser = await p.chromium.launch()

        for theme_id, theme_name in THEMES.items():
            print(f"\n--- Generating previews for theme {theme_id} ({theme_name}) ---")

            output_dir = OUTPUT_BASE / str(theme_id)
            output_dir.mkdir(parents=True, exist_ok=True)

            # Build the full report HTML using the existing template system
            # You'll need to adapt this to match your actual PropertyReportBuilder API
            builder = PropertyReportBuilder(
                theme_id=theme_id,
                accent_color=None,  # Use theme default
                property_data=SAMPLE_DATA["property"],
                comparables=SAMPLE_DATA["comparables"],
                market_trends=SAMPLE_DATA["market_trends"],
                overview_text=SAMPLE_DATA["overview_text"],
                agent=SAMPLE_DATA["agent"],
                branding={},  # Use defaults
            )

            html = builder.render_html()

            # Load the HTML in Playwright
            page = await browser.new_page()
            await page.set_viewport_size({"width": 816, "height": 1056})  # US Letter at 96dpi
            await page.set_content(html, wait_until="networkidle")

            # Wait for fonts and images to load
            await page.wait_for_timeout(2000)

            # Each page in the PDF is a separate element — find them
            # The template uses CSS page-break-before/after to separate pages
            # We need to screenshot each page section individually

            # Strategy: The report HTML has page-sized divs or sections.
            # Find each page element and screenshot it.

            # Method 1: If pages have identifiable classes/IDs
            for page_key in PAGE_KEYS:
                template_page = PAGE_KEY_TO_TEMPLATE_PAGE[page_key]

                # Try to find the page element by common selectors
                # Adapt these selectors to match your actual template structure
                selectors_to_try = [
                    f'[data-page="{template_page}"]',
                    f'.page-{template_page}',
                    f'#page-{template_page}',
                    f'.page[data-type="{template_page}"]',
                ]

                element = None
                for selector in selectors_to_try:
                    try:
                        element = await page.query_selector(selector)
                        if element:
                            break
                    except:
                        continue

                if element:
                    output_path = output_dir / f"{page_key}.jpg"
                    await element.screenshot(
                        path=str(output_path),
                        type="jpeg",
                        quality=85,
                    )
                    print(f"  ✓ {page_key}.jpg")
                else:
                    print(f"  ✗ {page_key} — could not find page element")
                    # Fallback: screenshot by scroll position
                    # Each page is ~1056px tall (US Letter at 96dpi)
                    page_index = PAGE_KEYS.index(page_key)
                    output_path = output_dir / f"{page_key}.jpg"
                    await page.screenshot(
                        path=str(output_path),
                        type="jpeg",
                        quality=85,
                        clip={
                            "x": 0,
                            "y": page_index * 1056,
                            "width": 816,
                            "height": 1056,
                        }
                    )
                    print(f"  ✓ {page_key}.jpg (via scroll position)")

            await page.close()

        await browser.close()
        print(f"\n✅ All previews generated in {OUTPUT_BASE}")


if __name__ == "__main__":
    asyncio.run(generate_previews())
```

**IMPORTANT:** The script above is a scaffold. You will need to adapt:
1. The `PropertyReportBuilder` instantiation to match the actual constructor signature
2. The page element selectors to match the actual template DOM structure
3. The output path to resolve correctly from where the script runs
4. The sample data fields to match what the builder actually expects

**Check the existing cover preview generation code** (wherever the `/previews/1-5.jpg` files are generated) and follow that same pattern. If those are generated differently (e.g., via PDFShift API), use that approach instead of Playwright.

---

### Option B: PDFShift API (If That's How Covers Are Generated)

If the existing cover previews use PDFShift's image rendering:

1. Generate the full PDF for each theme (using sample data)
2. Use PDFShift's PDF-to-image conversion to extract each page as a JPG
3. Save to the same output directory

Check how the existing cover previews are generated and mirror that approach.

---

## Wire Into the Theme Selector

### Update `step-theme.tsx`

**File:** `apps/web/components/property-wizard/step-theme.tsx` (or wherever the theme page grid lives)

Replace the decorative line placeholders with actual page preview images:

```typescript
// Helper to get page preview URL
function getPagePreviewUrl(themeId: number, pageKey: string): string {
  return `/previews/pages/${themeId}/${pageKey}.jpg`;
}

// In the page grid rendering:
const REPORT_PAGES = [
  { key: 'cover', label: 'Cover' },
  { key: 'details', label: 'Details' },
  { key: 'aerial', label: 'Aerial' },
  { key: 'comparables', label: 'Comparables' },
  { key: 'range', label: 'Range of Sales' },
  { key: 'market', label: 'Market Trends' },
  { key: 'overview', label: 'Executive Summary' },
];

// Render each page as a thumbnail:
{REPORT_PAGES.map((page) => (
  <div key={page.key} className="flex flex-col items-center gap-1.5">
    <div className="w-full aspect-[8.5/11] rounded-lg border border-stone-200 
                    overflow-hidden bg-stone-50 shadow-sm hover:shadow-md 
                    hover:border-stone-300 transition-all cursor-pointer">
      <img
        src={getPagePreviewUrl(selectedThemeId, page.key)}
        alt={`${page.label} page preview`}
        className="w-full h-full object-cover"
        loading="lazy"
        onError={(e) => {
          // Fallback to placeholder if image doesn't exist yet
          (e.target as HTMLImageElement).style.display = 'none';
          (e.target as HTMLImageElement).parentElement!.classList.add(
            'flex', 'items-center', 'justify-center'
          );
          (e.target as HTMLImageElement).parentElement!.innerHTML = `
            <div class="flex flex-col items-center gap-1 text-stone-400">
              <div class="w-6 h-8 border border-stone-300 rounded-sm"></div>
              <span class="text-[9px]">${page.label}</span>
            </div>
          `;
        }}
      />
    </div>
    <span className="text-[10px] text-stone-500 font-medium text-center">
      {page.label}
    </span>
  </div>
))}
```

**Key behaviors:**
- Thumbnails are aspect-ratio `8.5/11` (US Letter proportions)
- `loading="lazy"` since there are 7 images per theme
- `onError` fallback renders the old placeholder if the JPG doesn't exist
- When the agent switches themes, the `selectedThemeId` changes and all thumbnails update to show the new theme's pages
- Subtle hover effect (shadow + border darken) for visual polish

### Update Preview on Theme Change

When the agent selects a different theme, the page grid should update immediately. Since the images are static files served from `/public/`, this is instant — just changing the `src` URL triggers the browser to load the new theme's images.

```typescript
// The grid already re-renders when selectedThemeId changes
// because getPagePreviewUrl(selectedThemeId, page.key) produces a new URL
```

If you want to add a loading state while new theme images load:

```typescript
const [imagesLoaded, setImagesLoaded] = useState(false);

useEffect(() => {
  setImagesLoaded(false);
  // Preload all images for the selected theme
  const promises = REPORT_PAGES.map(page => {
    return new Promise<void>((resolve) => {
      const img = new Image();
      img.onload = () => resolve();
      img.onerror = () => resolve(); // Don't block on missing images
      img.src = getPagePreviewUrl(selectedThemeId, page.key);
    });
  });
  Promise.all(promises).then(() => setImagesLoaded(true));
}, [selectedThemeId]);
```

---

## Image Specifications

| Property | Value |
|---|---|
| Format | JPEG |
| Quality | 85% |
| Dimensions | 816 × 1056 px (US Letter at 96dpi) |
| Thumbnail display size | ~120 × 155 px (CSS scaled, actual file is full resolution for crisp display on retina) |
| Total file size estimate | ~50-150KB per image, ~2-5MB total for all 35 |

---

## Verification

After generating:

1. Check all 35 files exist: `ls -la apps/web/public/previews/pages/*/`
2. Open a few in a browser to verify they look correct and match their theme
3. Open the property wizard → theme selector → verify page thumbnails load
4. Switch between themes → thumbnails update to show correct theme
5. Each page should be visually distinct and recognizable at thumbnail size
6. Cover page thumbnails should match the existing cover preview JPGs (just generated differently)

# Social Media Sharing

> Branded, share-ready market reports for Instagram, TikTok, and LinkedIn Stories

---

## What It Does

TrendyReports generates **1080×1920 pixel images** optimized for social media stories. Agents can share stunning, branded market insights directly to Instagram Stories, TikTok, LinkedIn, and Facebook—in seconds.

| Feature | Details |
|---------|---------|
| **Format** | 1080×1920 JPEG (9:16 aspect ratio) |
| **Platforms** | Instagram Stories, TikTok, LinkedIn Stories, Facebook Stories |
| **Branding** | Full white-label (logo, colors, headshot, contact info) |
| **Report Types** | All 8 report types supported |
| **User Action** | One-click from Reports dashboard |

---

## User Experience

### How Agents Use It

1. **Generate any report** in TrendyReports
2. **Click the Share button** (pink icon) in the Reports table
3. **Screenshot or save** the social-optimized preview
4. **Post directly** to Instagram, TikTok, or LinkedIn

The entire workflow takes under 30 seconds.

### Example Output

```
┌──────────────────────────────┐
│    ▓▓▓ YOUR LOGO ▓▓▓         │
│    MARKET SNAPSHOT           │
│    Los Angeles, CA           │
├──────────────────────────────┤
│                              │
│         $1.2M                │
│    Median Sale Price         │
│                              │
│    ┌────────┐ ┌────────┐     │
│    │   47   │ │   28   │     │
│    │  Sold  │ │  Days  │     │
│    └────────┘ └────────┘     │
│                              │
│    ┌────────┐ ┌────────┐     │
│    │  2.1   │ │  98%   │     │
│    │  MOI   │ │ SP/LP  │     │
│    └────────┘ └────────┘     │
│                              │
│       Last 30 days           │
├──────────────────────────────┤
│  [Photo] Jane Smith          │
│          (555) 123-4567      │
│          jane@realty.com     │
│               [COMPANY LOGO] │
└──────────────────────────────┘
```

---

## Supported Report Types

| Report | Hero Metric | Additional Metrics |
|--------|-------------|-------------------|
| **Market Snapshot** | Median Price | Homes Sold, Avg DOM, MOI, SP/LP |
| **New Listings** | New Listings Count | Median Price, Avg DOM |
| **Closed Sales** | Homes Sold | Median Price, Avg DOM, SP/LP |
| **Inventory** | Active Listings | Median Price, Avg DOM, MOI |
| **Price Bands** | Total Listings | Top 3 bands with distribution |
| **Gallery** | Featured Photo | Price, Address, Beds/Baths/SqFt |
| **Featured Listings** | Featured Photo | Price, Address, Details |
| **Open Houses** | Active Listings | Date/Time, Locations |

---

## Branding Integration

Every social image automatically includes the agent's branding:

| Element | Source |
|---------|--------|
| **Header Logo** | Account branding settings |
| **Brand Colors** | Primary + accent from settings |
| **Agent Headshot** | Circular photo in footer |
| **Contact Info** | Name, phone, email |
| **Footer Logo** | Company/brokerage logo |

Colors are injected via CSS variables for perfect consistency:

```css
:root {
  --pct-blue: #7C3AED;    /* Primary */
  --pct-accent: #F26B2B;  /* Accent */
}
```

---

## Technical Architecture

### Route Structure

```
/api/social/[runId]     → Raw HTML (for screenshots)
/social/[runId]         → Redirects to API route
```

### Data Flow

```
┌─────────────────────────────────────────────────────────────┐
│  1. User clicks Share on completed report                   │
│                          ↓                                  │
│  2. Opens /social/{runId} → redirects to /api/social/{id}   │
│                          ↓                                  │
│  3. API route fetches report data from backend              │
│                          ↓                                  │
│  4. Template builder injects metrics + branding             │
│                          ↓                                  │
│  5. Returns clean 1080×1920 HTML page                       │
│                          ↓                                  │
│  6. User screenshots or saves image                         │
└─────────────────────────────────────────────────────────────┘
```

### Files

| Path | Purpose |
|------|---------|
| `apps/web/app/api/social/[runId]/route.ts` | API route serving clean HTML |
| `apps/web/app/social/[runId]/page.tsx` | Redirect to API route |
| `apps/web/lib/social-templates.ts` | Template builder functions |
| `apps/web/templates/social/*.html` | HTML templates (6 files) |
| `apps/worker/src/worker/social_engine.py` | Automated screenshot engine |

---

## Automated Screenshot Generation

For pre-generated images (future feature), the worker uses Playwright:

```python
from worker.social_engine import render_social_image

jpg_path, url = render_social_image(
    run_id="abc123",
    account_id="uuid",
    print_base="https://app.trendyreports.com"
)
# Returns: ("/tmp/mr_social/abc123_social.jpg", "https://...")
```

### Requirements

```bash
pip install playwright
playwright install chromium
```

### Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `PRINT_BASE` | `http://localhost:3000` | Base URL for social pages |
| `SOCIAL_DIR` | `/tmp/mr_social` | Output directory for JPEGs |

---

## Security

All templates implement XSS protection:

- **Text values**: Escaped via `escapeHtml()`
- **URLs**: Validated (http/https only) via `sanitizeUrl()`
- **Colors**: Hex validation only
- **Report IDs**: UUID v4 format validation

---

## Selling Points

### For Real Estate Agents

- **Stand out on social media** with professional, branded market updates
- **Save hours** vs. manually creating graphics
- **Consistent branding** across all reports and channels
- **Mobile-optimized** format for Stories and Reels

### For Brokerages & Affiliates

- **Co-branded exposure** on every agent post
- **Track engagement** via report generation metrics
- **Empower agents** with marketing tools that actually get used

---

## Future Roadmap

| Feature | Status | Description |
|---------|--------|-------------|
| Pre-generated JPEGs | Planned | Auto-generate at report creation, store in R2 |
| Multiple sizes | Planned | 1200×630 for feed posts, 1080×1080 for grid |
| Web Share API | Planned | One-tap share on mobile |
| Video export | Planned | Animated metrics for Reels/TikTok |
| Custom captions | Planned | User-added text overlays |

---

## Related Documentation

- [PDF Reports](./PDF_REPORTS.md) — PDF generation system
- [Branding](./BRANDING.md) — White-label configuration
- [Email System](./EMAIL_SYSTEM.md) — Email delivery with branding

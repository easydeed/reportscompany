# Glossary

> Platform-specific terms, status codes, role definitions, and report types.

## Report Types (Market Reports)

| Type | Key | Description |
|------|-----|-------------|
| Market Snapshot | `market_snapshot` | Complete market overview (active + pending + sold) |
| New Listings | `new_listings` | Recently listed properties (text format) |
| New Listings Gallery | `new_listings_gallery` | Photo-rich listing gallery |
| Closed Sales | `closed` | Recently sold properties |
| Inventory | `inventory` | Available supply analysis |
| Price Bands | `price_bands` | Market segmentation by price tier |
| Open Houses | `open_houses` | Upcoming open house schedule |
| Featured Listings | `featured_listings` | Agent's curated listings |

## Report Types (Property/CMA)

| Type | Key | Description |
|------|-----|-------------|
| Property Report (Seller) | `seller` | CMA for listing appointments |
| Property Report (Buyer) | `buyer` | CMA for buyer presentations |
| Consumer Report | mobile CMA | SMS-delivered home value estimate |

## Property Report Themes

| Theme | ID | Colors | Fonts |
|-------|-----|--------|-------|
| Classic | 1 | Navy + Sky Blue | Merriweather / Source Sans Pro |
| Modern | 2 | Coral + Midnight | Space Grotesk / DM Sans |
| Elegant | 3 | Burgundy + Gold | Playfair Display / Montserrat |
| Teal | 4 (DEFAULT) | Teal + Navy | Montserrat / Montserrat |
| Bold | 5 | Navy + Gold | Oswald / Montserrat |

## Audience Presets (Market Reports)

| Preset | Key | Filter Logic |
|--------|-----|-------------|
| All Listings | `all` | No additional filters |
| First-Time Buyers | `first_time` | 2+ beds, 2+ baths, SFR, <=70% median |
| Luxury | `luxury` | SFR, >=150% median |
| Families | `families` | 3+ beds, 2+ baths, SFR |
| Condo Buyers | `condo` | Condos only |
| Investors | `investors` | <=50% median |

## Status Codes

| Entity | Statuses |
|--------|----------|
| Report Generation | `pending` -> `processing` -> `completed` / `failed` |
| Property Report | `pending` -> `processing` -> `completed` / `failed` |
| Consumer Report | `pending` -> `ready` / `failed` |
| Schedule | `active` / `paused` (via `active` boolean) |
| Lead | `new` -> `contacted` -> `converted` |

## Account Types

| Type | Description | Dashboard |
|------|-------------|-----------|
| `REGULAR` | Individual real estate agent | `/app` |
| `INDUSTRY_AFFILIATE` | Title company sponsoring agents | `/app/affiliate` |

## User Roles

| Role | Scope | Access |
|------|-------|--------|
| `OWNER` | Account | Full account management |
| `MEMBER` | Account | Standard user access |
| `AFFILIATE` | Account | Affiliate agent access |
| `ADMIN` | Account | Account admin |
| `is_platform_admin` | Platform | System-wide admin, bypasses RLS |

## Subscription Plans

| Plan | Slug | Reports/Month | Overage | Property Reports | SMS |
|------|------|--------------|---------|-----------------|-----|
| Free | `free` | 50 | No | 5 | 10 |
| Pro | `pro` | 300 | $1.50/report | 25 | 50 |
| Team | `team` | 1,000 | $1.00/report | 100 | 200 |
| Affiliate | `affiliate` | 5,000 | No charge | 500 | 1,000 |
| Sponsored Free | `sponsored_free` | 75 | No | 10 | 20 |

## Key Terms

| Term | Meaning |
|------|---------|
| RLS | Row-Level Security -- PostgreSQL filters data by `account_id` automatically |
| RLS Context | `SET app.current_account_id = '<uuid>'` executed before every query |
| Print Page | Server-rendered HTML at `/print/[runId]` used as source for PDF generation |
| Social Image | 1080x1920 image at `/social/[runId]` for social media sharing |
| Short Code | Unique 8-char code for property report public URLs (`/p/{code}`) |
| Agent Code | Unique 6-char code for CMA landing pages (`/cma/{code}`) |
| Billable Unit | One report generation event tracked for plan limits |
| Sponsor | An INDUSTRY_AFFILIATE account that pays for agent subscriptions |
| Elastic Widening | Auto-expanding search filters when too few results are returned |
| Market-Adaptive Filters | Converting percentage-based intent filters to dollar amounts using market medians |
| Consecutive Failures | Counter on schedules; auto-pauses after 3 failures |
| Print Pipeline | Frontend renders HTML -> Worker converts to PDF via Playwright/PDFShift |

# Frontend Components

> `apps/web/components/` -- All React components organized by domain

---

## Layout & Navigation

| Component | File | Purpose |
|-----------|------|---------|
| Navbar | `navbar.tsx` | Main app navigation bar |
| Footer | `footer.tsx` | App footer |
| NavAuth | `NavAuth.tsx` | Auth-aware navigation (login/logout) |
| Logo | `logo.tsx` | Logo component |
| AccountSwitcher | `account-switcher.tsx` | Multi-account dropdown switcher |
| PageHeader | `page-header.tsx` | Reusable page header template |
| PageSkeleton | `page-skeleton.tsx` | Full-page loading skeleton |

---

## Dashboard

| Component | File | Purpose |
|-----------|------|---------|
| DashboardContent | `dashboard/dashboard-content.tsx` | Main dashboard layout with metrics |

---

## Unified Report Wizard (`unified-wizard/`) — NEW

Story-first 4-step wizard that replaces both the old Report Builder and Schedule Builder. One flow, two delivery modes (Send Now / Schedule). Both `/app/reports/new` and `/app/schedules/new` mount this component.

| Component | File | Purpose |
|-----------|------|---------|
| UnifiedReportWizard | `unified-wizard/index.tsx` | Main shell: step nav, sidebar preview, submit logic |
| StepStory | `unified-wizard/step-story.tsx` | 5 story cards (What Just Listed, What Just Sold, Market Update, What's Available, Showcase) |
| StepAudience | `unified-wizard/step-audience.tsx` | 6 audience cards (conditional — only for "What Just Listed") |
| StepWhereWhen | `unified-wizard/step-where-when.tsx` | Area (CityCombobox/ZIP) + timeframe (7/14/30/60/90 days) combined |
| StepDeliver | `unified-wizard/step-deliver.tsx` | Send Now (browser/PDF/email) or Schedule (cadence/day/time/timezone) |
| types | `unified-wizard/types.ts` | Story→report_type mapping, audience presets, state interfaces |

**Key features:**
- 5 stories map to 5 `report_type` values internally — agent never sees `new_listings_gallery` or `market_snapshot`
- Audience step auto-skips for non-gallery stories
- Smart lookback defaults per story (14d for listings, 30d for market, 90d for showcase)
- City selection uses `CityCombobox` (searchable dropdown from `crmls-cities.ts`) — eliminates free-text spelling errors
- Right sidebar shows SharedEmailPreview with real branding, updating live as the user configures
- Zero backend changes — same POST payloads to `/api/proxy/v1/reports` and `/api/proxy/v1/schedules`

---

## Shared Email Preview (`shared/email-preview/`) — NEW

Single preview component used in both the Unified Wizard and the Branding page. Renders a React interpretation of the V16 email template layouts with real agent branding and sample data.

| Component | File | Purpose |
|-----------|------|---------|
| SharedEmailPreview | `shared/email-preview/index.tsx` | Main component, routes to layout per report type |
| PreviewHeader | `shared/email-preview/preview-header.tsx` | Gradient header with logo, title, period |
| PreviewNarrative | `shared/email-preview/preview-narrative.tsx` | AI insight placeholder |
| PreviewHeroStat | `shared/email-preview/preview-hero-stat.tsx` | Big serif number (56px Georgia) |
| PreviewPhotoGrid | `shared/email-preview/preview-photo-grid.tsx` | 2×2, 3×2, stacked, large-cards layouts |
| PreviewStackedStats | `shared/email-preview/preview-stacked-stats.tsx` | Horizontal stat bar or vertical rows |
| PreviewDataTable | `shared/email-preview/preview-data-table.tsx` | Sales/inventory table with branded header |
| PreviewQuickTake | `shared/email-preview/preview-quick-take.tsx` | Accent callout box |
| PreviewCta | `shared/email-preview/preview-cta.tsx` | Branded CTA button |
| PreviewAgentFooter | `shared/email-preview/preview-agent-footer.tsx` | Agent photo, name, contact pills |
| PreviewGalleryCount | `shared/email-preview/preview-gallery-count.tsx` | Count badge |
| sample-data | `shared/email-preview/sample-data.ts` | Per-type placeholder content (stats, listings, narrative text) |

**What's real vs. sample:**
- Real: gradient colors, logo, agent info, report title, period line, CTA color
- Sample: metric values, property photos (Unsplash), AI narrative, listing details

---

## Report Builder (`report-builder/`) — LEGACY

> Superseded by Unified Wizard. Kept as fallback.

| Component | File | Purpose |
|-----------|------|---------|
| ReportBuilder | `report-builder/index.tsx` | Main wizard container |
| ReportPreview | `report-builder/report-preview.tsx` | Live report preview |

---

## Schedule Builder (`schedule-builder/`) — LEGACY

> Superseded by Unified Wizard. Kept as fallback.

| Component | File | Purpose |
|-----------|------|---------|
| ScheduleBuilder | `schedule-builder/index.tsx` | Main wizard container |
| EmailPreview | `schedule-builder/email-preview.tsx` | Email preview (React mockup, sample data) |

---

## Schedules (`schedules/`)

| Component | File | Purpose |
|-----------|------|---------|
| ScheduleTable | `schedules/schedule-table.tsx` | Schedules list table |
| ScheduleDetail | `schedules/schedule-detail.tsx` | Schedule detail view |
| ScheduleWizard | `schedules/schedule-wizard.tsx` | Schedule creation wizard |

---

## Property (`property/`)

| Component | File | Purpose |
|-----------|------|---------|
| PropertySearchForm | `property/PropertySearchForm.tsx` | Property address search |
| ComparablesPicker | `property/ComparablesPicker.tsx` | Select comparable properties |
| ComparablesMapModal | `property/ComparablesMapModal.tsx` | Map view for comparables |
| ThemeSelector | `property/ThemeSelector.tsx` | Report theme/style picker |

---

## Property Report Wizard (`property-wizard/`)

Multi-step wizard for creating property reports.

| Component | File | Purpose |
|-----------|------|---------|
| PropertyWizard | `property-wizard/property-wizard.tsx` | Main wizard container (4 steps) |
| StepTheme | `property-wizard/step-theme.tsx` | Theme selection, accent color picker with Smart Color System, page checklist |
| types | `property-wizard/types.ts` | Theme definitions, page lists (FULL_PAGES, COMPACT_PAGES), accent presets |

**StepTheme features:**
- 5-theme gallery with preview images (`/previews/1-5.jpg`)
- Accent color picker with per-theme suggested palettes and shared `ACCENT_PRESETS` (16 colors)
- **Live Contrast Preview** — shows accent color on dark (#1B365D), light (#ffffff), and as fill, with real-time WCAG contrast ratios
- **Smart Color System badge** — explains auto-adjustment for readability
- Report page checklist with 9 pages including Executive Summary (`overview`); required pages (`property`, `comparables`) locked

**Branding sync (NEW):**
- On mount, `property-wizard.tsx` fetches `/api/proxy/v1/account` to read `default_theme_id` and `secondary_color`
- If the account has a default theme set (1-5), the wizard pre-selects it instead of hardcoded Teal (4)
- If the account has an accent color, the wizard uses it as the initial accent instead of the theme's `accentDefault`
- Agent can still override both per-report in the theme step

---

## Branding Page (`app/settings/branding/`) — REBUILT

Single-page layout with controls (left) and persistent live preview (right). Replaces the old 3-tab layout.

**Sections:**
1. **Brand Identity** — display name, tagline (NEW)
2. **Colors** — primary/accent pickers, 6 presets, gradient preview
3. **Default Property Theme** — 5 theme cards with font info, sets account default (NEW)
4. **Logos** — 2 uploads (header light + footer dark), simplified from 4
5. **Agent Info** — name, title, phone, email, photo (NEW, consolidated from profile)

**Right panel:**
- Email/PDF toggle
- SharedEmailPreview (real V16 layouts, live-updating as user edits branding)
- PropertyPreviewMini (cover page thumbnail with selected theme)
- Test actions: Download Sample PDF, Send Test Email

**Accent sync:** When accent color changes on branding page, it also becomes the default accent for property reports (property wizard reads `account.secondary_color` on mount).

**Theme sync:** When default theme changes on branding page, it is persisted to `accounts.default_theme_id` via `PATCH /v1/account/branding`. The property wizard reads this on mount via `GET /v1/account` and pre-selects it instead of hardcoded Teal. (Backend support added: migration `0043_add_default_theme_id`, `AccountOut` + `BrandingPatch` models updated.)

---

## Branding Components (`branding/`) — LEGACY

| Component | File | Purpose |
|-----------|------|---------|
| DownloadTools | `branding/download-tools.tsx` | Download branded assets |
| ReportPreview | `branding/report-preview.tsx` | Report with branding preview (legacy) |

---

## Admin (`admin/`)

| Component | File | Purpose |
|-----------|------|---------|
| AdminOverview | `admin/admin-overview.tsx` | Admin dashboard overview cards |
| EmailLogTable | `admin/email-log-table.tsx` | Email log table |
| RecentReportsTable | `admin/recent-reports-table.tsx` | Recent reports table |
| SchedulesTable | `admin/schedules-table.tsx` | Schedules table (server) |
| SchedulesTableClient | `admin/schedules-table-client.tsx` | Schedules table (client) |

---

## Marketing (`marketing/`)

Landing page sections.

| Component | File | Purpose |
|-----------|------|---------|
| MarketingHome | `marketing-home.tsx` | Marketing homepage container |
| Hero | `marketing/hero.tsx` | Hero section |
| MarketingNav | `marketing/marketing-nav.tsx` | Marketing navigation |
| MarketingFooter | `marketing/marketing-footer.tsx` | Marketing footer |
| ReportTypesGrid | `marketing/report-types-grid.tsx` | Report types showcase |
| PdfReports | `marketing/pdf-reports.tsx` | PDF reports showcase |
| EmailReports | `marketing/email-reports.tsx` | Email reports showcase |
| HowItWorks | `marketing/how-it-works.tsx` | How it works section |
| AudienceCards | `marketing/audience-cards.tsx` | Audience feature cards |
| Pricing | `marketing/pricing.tsx` | Pricing table |
| FinalCta | `marketing/final-cta.tsx` | Final call-to-action |

---

## Onboarding (`onboarding/`)

| Component | File | Purpose |
|-----------|------|---------|
| SetupWizard | `onboarding/setup-wizard.tsx` | Initial setup wizard |
| OnboardingChecklist | `onboarding/onboarding-checklist.tsx` | Progress checklist |
| DashboardOnboarding | `onboarding/dashboard-onboarding.tsx` | Dashboard onboarding prompt |
| AffiliateOnboarding | `onboarding/affiliate-onboarding.tsx` | Affiliate-specific onboarding |
| EmptyState | `onboarding/empty-state.tsx` | Onboarding empty state |

---

## Lead Pages (`lead-pages/`)

| Component | File | Purpose |
|-----------|------|---------|
| ConsumerLandingWizard | `lead-pages/ConsumerLandingWizard.tsx` | Consumer landing page wizard |

---

## Mobile Report (`mobile-report/`)

| Component | File | Purpose |
|-----------|------|---------|
| MobileReportViewer | `mobile-report/MobileReportViewer.tsx` | Mobile-optimized report viewer |

---

## Shared Components

| Component | File | Purpose |
|-----------|------|---------|
| SharedEmailPreview | `shared/email-preview/index.tsx` | Unified email preview (V16 layouts, real branding) — used in wizard + branding |
| CityCombobox | `shared/city-combobox.tsx` | Searchable city dropdown (CRMLS 6-county list, grouped by county) — used in wizard + schedule builder |
| Wizard | `Wizard.tsx` | Generic wizard/stepper container |
| Stepper | `stepper.tsx` | Step progress indicator |
| StatusBadge | `status-badge.tsx` | Status indicator badge |
| MetricCard | `metric-card.tsx` | Metric/stat display card |
| EmptyState | `empty-state.tsx` | Empty state placeholder |
| DataTable | `data-table.tsx` | Generic sortable data table |
| GoogleMapsLoader | `google-maps-loader.tsx` | Google Maps API loader |
| InviteAgentModal | `invite-agent-modal.tsx` | Modal for inviting agents |
| CheckoutStatusBanner | `checkout-status-banner.tsx` | Checkout status notification |
| StripeBillingActions | `stripe-billing-actions.tsx` | Stripe billing UI |

---

## UI Primitives (`ui/`)

50+ Radix UI / shadcn/ui components. Key ones:

`accordion` `alert` `alert-dialog` `avatar` `badge` `breadcrumb` `button` `button-group` `calendar` `card` `chart` `checkbox` `command` `dialog` `drawer` `dropdown-menu` `form` `image-upload` `input` `input-group` `label` `navigation-menu` `pagination` `popover` `progress` `radio-group` `scroll-area` `select` `separator` `sheet` `sidebar` `skeleton` `slider` `sonner` `spinner` `switch` `table` `tabs` `textarea` `toast` `toaster` `toggle` `tooltip`

Custom hooks in ui/:
- `use-mobile.tsx` -- Mobile viewport detection
- `use-toast.ts` -- Toast notification hook

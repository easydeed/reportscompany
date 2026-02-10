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

## Report Builder (`report-builder/`)

Multi-step wizard for creating reports.

| Component | File | Purpose |
|-----------|------|---------|
| ReportBuilder | `report-builder/index.tsx` | Main wizard container |
| ReportPreview | `report-builder/report-preview.tsx` | Live report preview |
| ReportTypeSection | `report-builder/sections/report-type-section.tsx` | Report type selection step |
| AreaSection | `report-builder/sections/area-section.tsx` | Area/location selection step |
| LookbackSection | `report-builder/sections/lookback-section.tsx` | Date range selection step |
| DeliverySection | `report-builder/sections/delivery-section.tsx` | Delivery method selection step |

---

## Schedule Builder (`schedule-builder/`)

Multi-step wizard for creating scheduled reports.

| Component | File | Purpose |
|-----------|------|---------|
| ScheduleBuilder | `schedule-builder/index.tsx` | Main wizard container |
| EmailPreview | `schedule-builder/email-preview.tsx` | Email preview |
| ReportTypeSection | `schedule-builder/sections/report-type-section.tsx` | Report type step |
| AreaSection | `schedule-builder/sections/area-section.tsx` | Area selection step |
| LookbackSection | `schedule-builder/sections/lookback-section.tsx` | Lookback step |
| CadenceSection | `schedule-builder/sections/cadence-section.tsx` | Frequency selection step |
| RecipientsSection | `schedule-builder/sections/recipients-section.tsx` | Recipient selection step |

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

## Branding (`branding/`)

| Component | File | Purpose |
|-----------|------|---------|
| BrandingForm | `branding-form.tsx` | Brand settings form (logos, colors, contact) |
| BrandingPreview | `branding-preview.tsx` | Live branding preview |
| DownloadTools | `branding/download-tools.tsx` | Download branded assets |
| ReportPreview | `branding/report-preview.tsx` | Report with branding preview |

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

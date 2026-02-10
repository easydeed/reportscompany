# UI Component Library

> `apps/web/components/ui/` -- 57 shadcn/ui + Radix UI components
> `apps/web/components/` -- Custom application components

## shadcn/ui Primitives (components/ui/)

All standard shadcn/ui components built on Radix UI primitives:

accordion, alert, alert-dialog, aspect-ratio, avatar, badge, breadcrumb, button, button-group, calendar, card, carousel, chart, checkbox, collapsible, command, context-menu, dialog, drawer, dropdown-menu, empty, field, form, hover-card, image-upload, input, input-group, input-otp, item, kbd, label, menubar, navigation-menu, pagination, popover, progress, radio-group, resizable, scroll-area, select, separator, sheet, sidebar, skeleton, slider, sonner, spinner, switch, table, tabs, textarea, toast, toaster, toggle, toggle-group, tooltip, use-mobile

## Key Custom Components

### DataTable (`components/data-table.tsx`)
Generic data table wrapper with sorting, filtering, and pagination support.

### MetricCard (`components/metric-card.tsx`)
Dashboard metric display with label, value, icon, and index-based animation delay.

### StatusBadge (`components/status-badge.tsx`)
Colored badge for status values (completed, processing, pending, failed, etc.).

### EmptyState (`components/empty-state.tsx`)
Empty state placeholder with icon, title, description, and optional CTA action.

### PageHeader (`components/page-header.tsx`)
Consistent page header with title, description, and optional action button.

### PageSkeleton (`components/page-skeleton.tsx`)
Full-page loading skeleton.

### Wizard (`components/Wizard.tsx`)
Multi-step wizard container with step navigation.

### Stepper (`components/stepper.tsx`)
Step indicator component for wizards.

### Navbar (`components/navbar.tsx`)
App navigation bar with user menu.

### AccountSwitcher (`components/account-switcher.tsx`)
Account switching dropdown for users with multiple accounts.

### Logo (`components/logo.tsx`)
App logo component.

### Footer (`components/footer.tsx`)
App footer.

### CheckoutStatusBanner (`components/checkout-status-banner.tsx`)
Banner showing Stripe checkout success/cancel status.

### GoogleMapsLoader (`components/google-maps-loader.tsx`)
Script loader for Google Maps API.

### ImageUpload (`components/ui/image-upload.tsx`)
Image upload component with preview, supports different aspect ratios and asset types (headshot, logo).

### use-mobile (`components/ui/use-mobile.tsx`)
Hook for detecting mobile viewport. Returns boolean.

## Component Locations

```
components/
  ui/                     # 57 shadcn/ui primitives
  admin/                  # Admin-specific (overview, tables)
  branding/               # Branding form/preview
  dashboard/              # Dashboard content
  lead-pages/             # Lead page editor
  marketing/              # Landing page sections (hero, pricing, etc.)
  mobile-report/          # Consumer report viewer
  onboarding/             # Setup wizard, checklist
  property/               # Property wizard components
  providers/              # React Query provider
  report-builder/         # Market report wizard
  schedule-builder/       # Schedule wizard
  schedules/              # Schedule list/detail
```

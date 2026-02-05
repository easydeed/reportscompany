# TrendyReports — UI Modernization Blueprint

> Extracted from the wizard design language. Every page and component should feel like it belongs in the same product as the Report Builder.

---

## 1. The Wizard Design Language (What We're Matching)

The Report Builder, Schedule Builder, and Property Report wizards establish a clear, consistent visual identity. Here's what makes them work:

### Visual DNA

| Trait | Pattern | Code Reference |
|-------|---------|----------------|
| **Surface** | Pure white cards on light gray background | `bg-white border border-gray-200 rounded-lg` on `bg-gray-50` |
| **Primary action** | Violet 600 | `bg-violet-600 hover:bg-violet-700 text-white` |
| **Section cards** | Rounded-lg with 1px border, p-4 padding | `bg-white border border-gray-200 rounded-lg p-4` |
| **Section headers** | Small, medium-weight, gray-900 | `text-sm font-medium text-gray-900` |
| **Body text** | Small, gray-500 or gray-700 | `text-sm text-gray-500` / `text-sm text-gray-700` |
| **Completion** | Green checkmark in green-50 circle | `w-5 h-5 rounded-full bg-green-50` + `w-3 h-3 text-green-500` |
| **Selection state** | Violet-50 bg + violet-600 2px border | `bg-violet-50 border-2 border-violet-600` |
| **Unselected** | White bg + gray-200 border, hover gray-300 | `bg-white border-gray-200 hover:border-gray-300` |
| **Pills/tags** | Rounded-full, small padding | `px-3 py-1.5 text-sm rounded-full` |
| **Sticky header** | White bg, bottom border, z-10 | `sticky top-0 z-10 bg-white border-b border-gray-200` |
| **Page padding** | Consistent 8-unit horizontal, 6-unit vertical | `px-8 py-6` |
| **Spacing** | 4-unit between sections | `space-y-4` |

### What's Wrong With the Rest of the UI

The audit reveals these inconsistencies outside the wizards:

1. **Mixed token systems** — `--app-*` CSS variables, oklch colors, and hardcoded Tailwind classes all used interchangeably
2. **Glass cards vs solid cards** — `.glass` class (`bg-white/90 backdrop-blur-lg`) used alongside plain `bg-card` and `bg-white`
3. **Inconsistent page headers** — Dashboard uses `text-3xl font-bold`, settings uses `text-xl font-semibold`, wizards use sticky headers
4. **Sidebar footer** — Hardcoded "Professional Plan" text that doesn't reflect actual plan
5. **CSS variable bloat** — Two parallel systems: semantic oklch tokens (`--primary`, `--card`) AND `--app-*` hex tokens
6. **No loading skeletons** — Pages jump from blank to loaded
7. **Empty states** — Inconsistent or missing

---

## 2. Design Tokens — Simplified & Unified

### Problem: Two Token Systems

The current `globals.css` has BOTH:
```css
/* System 1: oklch semantic tokens (shadcn default) */
--primary: oklch(0.55 0.25 290);
--card: oklch(1 0 0);

/* System 2: --app-* hex tokens (manually added) */
--app-bg: #f5f5f7;
--app-surface: #ffffff;
--app-primary: #7c3aed;
```

Components use a mix of both, creating confusion.

### Solution: Consolidate to One System

Keep shadcn's semantic tokens as the source of truth, but map them to simple, predictable values. Remove `--app-*` entirely.

```css
/* globals.css — Unified token set */
:root {
  /* ── Backgrounds ── */
  --background: #f5f5f7;        /* Page background (light gray) */
  --card: #ffffff;               /* Card/surface background */
  --muted: #f3f4f6;             /* Muted/secondary background */

  /* ── Text ── */
  --foreground: #111827;         /* Primary text (gray-900) */
  --muted-foreground: #6b7280;   /* Secondary text (gray-500) */
  --card-foreground: #111827;    /* Card text */

  /* ── Brand ── */
  --primary: #7c3aed;            /* Violet-600 */
  --primary-foreground: #ffffff;
  --accent: #f26b2b;             /* Coral (keep for special moments) */
  --accent-foreground: #ffffff;

  /* ── Interactive ── */
  --ring: #7c3aed;               /* Focus ring = primary */
  --border: #e5e7eb;             /* Default border (gray-200) */
  --input: #e5e7eb;              /* Input border */

  /* ── Status ── */
  --destructive: #ef4444;
  --success: #22c55e;
  --warning: #f59e0b;

  /* ── Radius ── */
  --radius: 0.5rem;              /* Default (8px) — matches rounded-lg */

  /* ── Sidebar ── */
  --sidebar-background: #ffffff;
  --sidebar-foreground: #374151;
  --sidebar-border: #e5e7eb;
  --sidebar-accent: #f3f4f6;
  --sidebar-accent-foreground: #111827;
  --sidebar-primary: #7c3aed;
  --sidebar-primary-foreground: #ffffff;
}
```

### Migration Checklist

| Replace This | With This |
|-------------|-----------|
| `bg-[var(--app-bg)]` | `bg-background` |
| `bg-[var(--app-surface)]` | `bg-card` |
| `text-[var(--app-text)]` | `text-foreground` |
| `text-[var(--app-muted)]` | `text-muted-foreground` |
| `border-[var(--app-border)]` | `border-border` |
| `bg-violet-600` | `bg-primary` |
| `hover:bg-violet-700` | `hover:bg-primary/90` |
| `.glass` class | `bg-card border border-border rounded-xl shadow-sm` |

---

## 3. Typography System

### Current (Keep)

Plus Jakarta Sans is a great choice — it matches the wizard aesthetic perfectly. No change needed on the font itself.

### Scale to Standardize

| Use Case | Class | Example |
|----------|-------|---------|
| **Page title** | `text-2xl font-bold tracking-tight` | "Market Reports", "Dashboard" |
| **Section title** | `text-lg font-semibold` | Card header, settings section |
| **Card label** | `text-sm font-medium text-foreground` | "Report Type", "Area" |
| **Body** | `text-sm text-foreground` | Descriptions, table cells |
| **Muted** | `text-sm text-muted-foreground` | Helper text, timestamps |
| **Tiny** | `text-xs text-muted-foreground` | Badges, metadata |
| **Overline** | `text-xs font-medium text-muted-foreground uppercase tracking-wider` | Section labels in settings |

### Changes from Current

- Dashboard title: `text-3xl` → `text-2xl` (matches wizard scale)
- Settings title: `text-xl` → `text-lg` (consistent hierarchy)
- Stop using `tracking-tight` on everything — only on page titles

---

## 4. Component Patterns

### 4.1 Page Shell

Every authenticated page should follow this structure:

```tsx
// Consistent page layout
<div className="space-y-6">
  {/* Page Header */}
  <div className="flex items-center justify-between">
    <div>
      <h1 className="text-2xl font-bold tracking-tight">Page Title</h1>
      <p className="text-sm text-muted-foreground mt-1">
        Brief description of this page
      </p>
    </div>
    <div className="flex items-center gap-3">
      {/* Primary action button */}
      <Button>
        <Plus className="w-4 h-4 mr-2" />
        New Item
      </Button>
    </div>
  </div>

  {/* Content */}
  {children}
</div>
```

### 4.2 Card Pattern (Unified)

Kill the `.glass` class. One card pattern everywhere:

```tsx
// Standard card
<div className="bg-card border border-border rounded-xl p-6 shadow-sm">
  {children}
</div>

// With section header (settings-style)
<div className="bg-card border border-border rounded-xl p-6 shadow-sm">
  <h3 className="text-xs font-medium text-muted-foreground uppercase tracking-wider mb-4">
    Section Label
  </h3>
  {content}
</div>

// Compact card (wizard sections)
<div className="bg-card border border-border rounded-lg p-4">
  <div className="flex items-center justify-between mb-4">
    <h3 className="text-sm font-medium text-foreground">Section Title</h3>
    {isComplete && <CompletionBadge />}
  </div>
  {content}
</div>
```

### 4.3 Selection Card Pattern

Extracted from the wizard's report type selector:

```tsx
// Reusable selection card
<button
  onClick={() => onSelect(id)}
  className={cn(
    "flex flex-col items-center p-4 rounded-lg border-2 transition-all",
    isSelected
      ? "bg-primary/5 border-primary shadow-sm"
      : "bg-card border-border hover:border-gray-300 hover:shadow-sm"
  )}
>
  <Icon className={cn(
    "w-6 h-6 mb-2",
    isSelected ? "text-primary" : "text-muted-foreground"
  )} />
  <span className={cn(
    "text-sm font-medium",
    isSelected ? "text-foreground" : "text-muted-foreground"
  )}>
    {label}
  </span>
</button>
```

### 4.4 Data Table Pattern

Replace the current glass-wrapped table with something cleaner:

```tsx
<div className="bg-card border border-border rounded-xl overflow-hidden shadow-sm">
  {/* Table toolbar */}
  <div className="flex items-center justify-between px-4 py-3 border-b border-border">
    <div className="flex items-center gap-2">
      <Input
        placeholder="Search..."
        className="w-64 h-8 text-sm"
      />
      {/* Filter pills */}
    </div>
    <div className="flex items-center gap-2 text-xs text-muted-foreground">
      {count} results
    </div>
  </div>

  {/* Table */}
  <Table>
    <TableHeader>
      <TableRow className="bg-muted/50 hover:bg-muted/50">
        <TableHead className="text-xs font-medium text-muted-foreground uppercase tracking-wider">
          Column
        </TableHead>
      </TableRow>
    </TableHeader>
    <TableBody>
      <TableRow className="hover:bg-muted/30 transition-colors">
        <TableCell className="text-sm">{data}</TableCell>
      </TableRow>
    </TableBody>
  </Table>

  {/* Pagination footer */}
  <div className="flex items-center justify-between px-4 py-3 border-t border-border">
    <p className="text-xs text-muted-foreground">Showing 1-10 of 42</p>
    <Pagination />
  </div>
</div>
```

### 4.5 Empty State Pattern

```tsx
<div className="bg-card border border-border rounded-xl p-12 text-center shadow-sm">
  <div className="w-12 h-12 rounded-full bg-primary/10 flex items-center justify-center mx-auto mb-4">
    <Icon className="w-6 h-6 text-primary" />
  </div>
  <h3 className="text-lg font-semibold text-foreground mb-1">
    No reports yet
  </h3>
  <p className="text-sm text-muted-foreground mb-6 max-w-sm mx-auto">
    Create your first market report to get started with data-driven insights.
  </p>
  <Button>
    <Plus className="w-4 h-4 mr-2" />
    Create Report
  </Button>
</div>
```

### 4.6 Metric Card Pattern (Dashboard)

```tsx
<div className="bg-card border border-border rounded-xl p-5 shadow-sm">
  <div className="flex items-center justify-between mb-3">
    <span className="text-xs font-medium text-muted-foreground uppercase tracking-wider">
      {label}
    </span>
    <div className="w-8 h-8 rounded-lg bg-primary/10 flex items-center justify-center">
      <Icon className="w-4 h-4 text-primary" />
    </div>
  </div>
  <div className="text-2xl font-bold text-foreground">{value}</div>
  {trend && (
    <div className="flex items-center gap-1 mt-1">
      <TrendIcon className={cn("w-3 h-3", isPositive ? "text-success" : "text-destructive")} />
      <span className={cn("text-xs font-medium", isPositive ? "text-success" : "text-destructive")}>
        {trend}%
      </span>
      <span className="text-xs text-muted-foreground">vs last period</span>
    </div>
  )}
</div>
```

### 4.7 Loading Skeleton Pattern

```tsx
// Page skeleton
<div className="space-y-6">
  <div className="flex items-center justify-between">
    <div>
      <Skeleton className="h-7 w-48" />
      <Skeleton className="h-4 w-72 mt-2" />
    </div>
    <Skeleton className="h-9 w-32" />
  </div>

  {/* Metric cards skeleton */}
  <div className="grid grid-cols-4 gap-4">
    {Array.from({ length: 4 }).map((_, i) => (
      <div key={i} className="bg-card border border-border rounded-xl p-5 shadow-sm">
        <Skeleton className="h-4 w-24 mb-3" />
        <Skeleton className="h-7 w-16" />
      </div>
    ))}
  </div>

  {/* Table skeleton */}
  <div className="bg-card border border-border rounded-xl overflow-hidden shadow-sm">
    <div className="px-4 py-3 border-b border-border">
      <Skeleton className="h-8 w-64" />
    </div>
    {Array.from({ length: 5 }).map((_, i) => (
      <div key={i} className="px-4 py-3 border-b border-border last:border-0">
        <Skeleton className="h-4 w-full" />
      </div>
    ))}
  </div>
</div>
```

### 4.8 Status Badge Pattern

```tsx
const STATUS_STYLES = {
  completed: "bg-emerald-50 text-emerald-700 border-emerald-200",
  processing: "bg-blue-50 text-blue-700 border-blue-200",
  pending: "bg-amber-50 text-amber-700 border-amber-200",
  failed: "bg-red-50 text-red-700 border-red-200",
  active: "bg-emerald-50 text-emerald-700 border-emerald-200",
  inactive: "bg-gray-50 text-gray-500 border-gray-200",
}

<span className={cn(
  "inline-flex items-center px-2 py-0.5 rounded-full text-xs font-medium border",
  STATUS_STYLES[status]
)}>
  {label}
</span>
```

---

## 5. Sidebar Modernization

### Current Issues

1. Sidebar footer has hardcoded "Professional Plan" — should reflect actual plan
2. Uses a mix of `SidebarMenuButton` props and manual active detection
3. No visual hierarchy between primary nav and secondary sections
4. Missing micro-interactions

### Proposed Changes

```tsx
// Sidebar structure — cleaner visual hierarchy
<Sidebar className="border-r border-border">
  <SidebarHeader className="px-4 py-4">
    <Link href="/app" className="flex items-center gap-2">
      <Logo className="h-7" />
    </Link>
  </SidebarHeader>

  <SidebarContent className="px-2">
    {/* Primary navigation — no group label */}
    <SidebarMenu>
      {primaryNav.map(item => (
        <SidebarMenuItem key={item.name}>
          <SidebarMenuButton asChild isActive={isActive(item.href)}>
            <Link href={item.href}>
              <item.icon className="w-4 h-4" />
              <span>{item.name}</span>
            </Link>
          </SidebarMenuButton>
        </SidebarMenuItem>
      ))}
    </SidebarMenu>

    {/* Divider */}
    <Separator className="my-2" />

    {/* Settings & Admin — with group labels */}
    <SidebarGroup>
      <SidebarGroupLabel className="text-xs font-medium text-muted-foreground uppercase tracking-wider px-2">
        Account
      </SidebarGroupLabel>
      <SidebarMenu>
        {accountNav.map(item => (/* ... */))}
      </SidebarMenu>
    </SidebarGroup>
  </SidebarContent>

  <SidebarFooter className="px-3 py-3">
    {/* Dynamic plan badge + CTA */}
    <div className="bg-muted rounded-lg p-3">
      <div className="flex items-center gap-2 mb-2">
        <Badge variant="secondary" className="text-xs">
          {planName} Plan
        </Badge>
        <span className="text-xs text-muted-foreground">
          {usageCount}/{limit} reports
        </span>
      </div>
      <Progress value={(usageCount / limit) * 100} className="h-1.5 mb-2" />
      <Button size="sm" className="w-full" asChild>
        <Link href="/app/reports/new">
          <Plus className="w-3.5 h-3.5 mr-1.5" />
          New Report
        </Link>
      </Button>
    </div>
  </SidebarFooter>
</Sidebar>
```

### Topbar Simplification

```tsx
<header className="flex h-12 items-center gap-4 border-b border-border bg-card px-4">
  <SidebarTrigger className="text-muted-foreground" />
  <div className="flex-1" />

  {/* Account switcher (if multi-account) */}
  {showAccountSwitcher && <AccountSwitcher />}

  {/* User menu */}
  <DropdownMenu>
    <DropdownMenuTrigger asChild>
      <Button variant="ghost" size="sm" className="gap-2">
        <Avatar className="w-6 h-6">
          <AvatarImage src={user.photo_url} />
          <AvatarFallback className="text-xs">{initials}</AvatarFallback>
        </Avatar>
        <span className="text-sm font-medium hidden sm:inline">{user.name}</span>
      </Button>
    </DropdownMenuTrigger>
    {/* Dropdown content */}
  </DropdownMenu>
</header>
```

---

## 6. Page-by-Page Modernization

### 6.1 Dashboard (`app/app/page.tsx`)

**Current:** Uses external `DashboardOverview` from `@repo/ui` — opaque, can't easily style.

**Target:**

```
┌──────────────────────────────────────────────────┐
│  Overview                          [New Report ▸] │
│  Your account activity and key metrics           │
├──────────────────────────────────────────────────┤
│                                                   │
│  ┌─────────┐ ┌─────────┐ ┌─────────┐ ┌─────────┐│
│  │Reports  │ │Emails   │ │Leads    │ │Schedules││
│  │  24     │ │  156    │ │  8      │ │  3      ││
│  │↑ 12%   │ │↑ 8%    │ │↓ 2%    │ │─       ││
│  └─────────┘ └─────────┘ └─────────┘ └─────────┘│
│                                                   │
│  ┌──────────────────────┐ ┌──────────────────────┐│
│  │ Recent Reports       │ │ Report Activity      ││
│  │ ┌──────────────────┐ │ │ ┌──────────────────┐ ││
│  │ │ Closed Sales     │ │ │ │     Bar Chart    │ ││
│  │ │ LA · 2h ago  ✓   │ │ │ │     (Recharts)   │ ││
│  │ ├──────────────────┤ │ │ └──────────────────┘ ││
│  │ │ New Listings     │ │ │                      ││
│  │ │ OC · 1d ago  ✓   │ │ │                      ││
│  │ └──────────────────┘ │ │                      ││
│  └──────────────────────┘ └──────────────────────┘│
│                                                   │
│  ┌──────────────────────────────────────────────┐│
│  │ Onboarding Checklist (dismissible)           ││
│  │ ☑ Create profile  ☑ Add branding  ☐ Report  ││
│  └──────────────────────────────────────────────┘│
└──────────────────────────────────────────────────┘
```

**Key changes:**
- Inline the metric cards (replace `@repo/ui` import with local components)
- Use the MetricCard pattern from section 4.6
- Recent reports as a simple list with status badges
- Activity chart in a clean card wrapper
- Move onboarding below the fold (it's not the primary focus)

### 6.2 Reports List (`app/app/reports/page.tsx`)

**Target:**

```
┌──────────────────────────────────────────────────┐
│  Market Reports                    [New Report ▸] │
│  View and manage your generated reports          │
├──────────────────────────────────────────────────┤
│                                                   │
│  ┌──────────────────────────────────────────────┐│
│  │ [Search...        ] [Type ▾] [Status ▾]      ││
│  │──────────────────────────────────────────────││
│  │  Report        Area       Date     Status    ││
│  │──────────────────────────────────────────────││
│  │  Closed Sales  LA 90210   2h ago   ✓ Done    ││
│  │  New Listings  Orange Co  1d ago   ✓ Done    ││
│  │  Inventory     SD 92101   3d ago   ⚠ Failed  ││
│  │──────────────────────────────────────────────││
│  │  Showing 1-10 of 42            [< 1 2 3 >]  ││
│  └──────────────────────────────────────────────┘│
└──────────────────────────────────────────────────┘
```

**Key changes:**
- Unified table pattern (section 4.4)
- Search + filter pills in table toolbar
- Status badges (section 4.8)
- Row click → detail view or PDF download
- Empty state when no reports exist

### 6.3 Property Reports List (`app/app/property/page.tsx`)

Same table pattern as Market Reports, with:
- Theme preview thumbnail (small color swatch)
- Property address as primary column
- Quick actions: View PDF, Copy QR Link, Delete

### 6.4 Schedules List (`app/app/schedules/page.tsx`)

Same table pattern, with:
- Cadence badge (Weekly/Monthly pill)
- Next run time column
- Active/Paused toggle in row
- Recipient count

### 6.5 Leads Page (`app/app/lead-page/page.tsx`)

Same table pattern, with:
- Status column (New/Contacted/Converted)
- Source badge (QR Scan / Direct Link)
- Quick contact actions (email, SMS)

### 6.6 Contacts Page (`app/app/people/page.tsx`)

Same table pattern, with:
- Type filter (Client/Agent/Group)
- Group membership tags
- Quick add contact button

### 6.7 Settings Pages

**Layout:** Keep the collapsible sidebar sub-menu for settings. Each settings page follows this pattern:

```tsx
<div className="space-y-8 max-w-2xl">
  {/* Page header */}
  <div>
    <h2 className="text-lg font-semibold">Profile</h2>
    <p className="text-sm text-muted-foreground mt-1">
      Your personal information shown on reports and emails.
    </p>
  </div>

  {/* Section cards */}
  <div className="bg-card border border-border rounded-xl p-6 shadow-sm">
    <h3 className="text-xs font-medium text-muted-foreground uppercase tracking-wider mb-4">
      Photo
    </h3>
    {/* Content */}
  </div>

  <div className="bg-card border border-border rounded-xl p-6 shadow-sm">
    <h3 className="text-xs font-medium text-muted-foreground uppercase tracking-wider mb-4">
      Personal Information
    </h3>
    {/* Form fields with consistent spacing */}
    <div className="grid grid-cols-2 gap-4">
      <div className="space-y-2">
        <Label className="text-sm font-medium">First Name</Label>
        <Input />
      </div>
      {/* ... */}
    </div>
  </div>

  {/* Sticky save bar */}
  <div className="flex justify-end sticky bottom-4">
    <Button disabled={!hasChanges}>
      <Save className="w-4 h-4 mr-2" />
      Save Changes
    </Button>
  </div>
</div>
```

**Settings sub-pages:**
- **Profile** — Photo, name, title, license, contact info
- **Security** — Password change, sessions
- **Branding** — Logo upload, color picker, company info
- **Billing** — Current plan, usage, payment method, invoices

---

## 7. Implementation Phases

### Phase 1: Foundation (Do First)

**Files to change:**
- `globals.css` — Consolidate tokens, remove `--app-*` variables
- Kill `.glass` class everywhere

**Why first:** Every other change builds on consistent tokens. This is a find-and-replace pass with no visual regressions if mapped correctly.

**Estimated scope:** ~20 files with `--app-*` references

### Phase 2: Shared Components

**Create or update:**
- `components/page-header.tsx` — Reusable page header (title + description + actions)
- `components/status-badge.tsx` — Unified status badges
- `components/metric-card.tsx` — Updated metric card (replace current)
- `components/empty-state.tsx` — Updated empty state (replace current)
- `components/data-table.tsx` — Updated table wrapper with toolbar + pagination
- `components/page-skeleton.tsx` — Loading skeleton compositions

**Why second:** These are the building blocks that every page needs.

### Phase 3: Sidebar & Topbar

**Files to change:**
- `app/app-layout.tsx` — Sidebar and topbar updates
- `components/account-switcher.tsx` — Clean up styling

**Why third:** These are globally visible but self-contained. One change affects every page.

### Phase 4: Dashboard

**Files to change:**
- `app/app/page.tsx` — Rebuild with local components
- Remove/reduce dependency on `@repo/ui` `DashboardOverview`

**Why fourth:** Highest-visibility page. With foundation + shared components done, this becomes assembly.

### Phase 5: List Pages

**Files to change:**
- `app/app/reports/page.tsx`
- `app/app/property/page.tsx`
- `app/app/schedules/page.tsx`
- `app/app/lead-page/page.tsx`
- `app/app/people/page.tsx`

**Why fifth:** These all follow the same pattern. Once the data table component is solid, these are quick.

### Phase 6: Settings Pages

**Files to change:**
- `app/app/settings/profile/page.tsx`
- `app/app/settings/security/page.tsx`
- `app/app/settings/branding/page.tsx`
- `app/app/settings/billing/page.tsx`

**Why last:** Already the closest to the target. Mostly cleanup.

---

## 8. Files NOT to Touch

These are already good — don't regress them:

- `components/report-builder/*` — Design reference, leave as-is
- `components/schedule-builder/*` — Design reference, leave as-is
- `components/property/*` — Design reference, leave as-is
- `app/app/reports/new/page.tsx` — Wizard page, leave as-is
- `app/app/schedules/new/page.tsx` — Wizard page, leave as-is
- `app/app/property/new/page.tsx` — Wizard page, leave as-is

---

## 9. Quick Reference: Class Cheat Sheet

Use this as a copy-paste reference when building pages:

```
PAGE BACKGROUND:      bg-background
CARD:                 bg-card border border-border rounded-xl p-6 shadow-sm
COMPACT CARD:         bg-card border border-border rounded-lg p-4
PAGE TITLE:           text-2xl font-bold tracking-tight
SECTION TITLE:        text-lg font-semibold
CARD LABEL:           text-sm font-medium text-foreground
OVERLINE:             text-xs font-medium text-muted-foreground uppercase tracking-wider
BODY:                 text-sm text-foreground
MUTED:                text-sm text-muted-foreground
TINY:                 text-xs text-muted-foreground

SELECTED:             bg-primary/5 border-2 border-primary
UNSELECTED:           bg-card border border-border hover:border-gray-300
SELECTED TEXT:        text-primary
UNSELECTED TEXT:      text-muted-foreground

BUTTON PRIMARY:       (use shadcn Button default — maps to bg-primary)
BUTTON SECONDARY:     variant="outline"
BUTTON GHOST:         variant="ghost"

PILL SELECTED:        bg-primary/10 text-primary border border-primary/20 rounded-full px-3 py-1
PILL UNSELECTED:      bg-card text-muted-foreground border border-border rounded-full px-3 py-1

TABLE HEADER:         bg-muted/50 text-xs font-medium text-muted-foreground uppercase tracking-wider
TABLE ROW:            hover:bg-muted/30 transition-colors
TABLE CELL:           text-sm py-3

SPACING:              space-y-6 (page sections), space-y-4 (within cards), gap-4 (grids)
PAGE PADDING:         p-6 (set by layout, don't override)
```

---

## 10. Summary

The modernization is essentially: **make everything look like it was built by the same person who built the wizards.**

The wizards use a clean, systematic approach:
- White on light gray
- Violet as the single action color
- Small, precise typography
- Consistent card treatment
- Clear visual hierarchy

Everything else in the app is *close* but has accumulated inconsistencies. This blueprint provides the specific patterns, token values, and implementation order to bring it all into alignment.

Total estimated pages to modify: ~15-20 files
Complexity: Mostly styling/markup changes, minimal logic changes
Risk: Low — visual-only changes, no API or data flow modifications

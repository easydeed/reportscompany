# Skill: Admin Panel Design

> Place this file at `.cursor/rules/admin-panel-design.md`
> This skill applies when working on any file in `apps/web/app/app/admin/`

---

## What This Is

TrendyReports has a platform admin panel at `/app/admin`. It's used by Jerry (founder) and future operations staff to manage every aspect of the platform: accounts, affiliates, agents, reports, schedules, emails, billing, leads, SMS, CMA pages, and system health.

The admin panel is NOT a developer tool. It's an operations dashboard. It should feel like Stripe Dashboard, Linear, or Vercel — clean, data-dense, fast, and beautiful.

---

## Design Philosophy

### 1. Data density over whitespace
Admins process hundreds of records. Every pixel should carry information. Compact rows, visible metadata, inline actions. But dense ≠ cluttered — use clear typography hierarchy, subtle borders, and color-coded badges to organize the density.

### 2. Drill-down navigation
Every entity links to every related entity. Account → their reports → their schedules → their leads → their agent → back to account. The admin should never have to "go back and search" — everything is a click away.

### 3. Actionable, not read-only
Every page should have clear actions: pause/resume, retry, delete, edit, export. Actions live in context (row dropdown, detail page header) not hidden behind menus.

### 4. Real-time operational awareness
The dashboard should immediately answer: "Is anything broken right now?" Failed reports, failed emails, failed schedules, unhealthy services — these surface at the top, not buried in logs.

---

## Page Types

### Dashboard (the home)
The admin dashboard answers 5 questions at a glance:
1. **Is anything broken?** → System health indicators + failed counts
2. **What's happening now?** → Live activity feed (recent reports, emails, signups)
3. **How are we growing?** → Key metrics (accounts, MRR, reports this month)
4. **What needs attention?** → Failed reports, stuck schedules, unverified users
5. **Quick actions** → Most common admin tasks as shortcut buttons

### List Pages (accounts, users, reports, schedules, emails, leads)
Every list page follows the same pattern:
```
┌─ PageHeader: title + action buttons (export, create) ─────────┐
├─ Metric Cards: 3-4 KPIs with trend indicators ────────────────┤
├─ Filter Bar: search + dropdowns + date range + clear button ───┤
├─ Data Table: sortable columns, inline badges, row actions ─────┤
├─ Pagination: page numbers or infinite scroll ──────────────────┤
└─────────────────────────────────────────────────────────────────┘
```

### Detail Pages (account detail, affiliate detail, user detail)
Every detail page follows:
```
┌─ Back link + PageHeader: entity name + status badge + actions ─┐
├─ Summary Cards: key metrics for this entity ───────────────────┤
├─ Tabs: Overview | Reports | Schedules | Leads | Settings ──────┤
├─ Tab Content: contextual data tables + cards ──────────────────┤
└─────────────────────────────────────────────────────────────────┘
```

### Settings/Config Pages (plans, blocked IPs, system health)
Simple form-based or card-based layouts for configuration.

---

## Color Coding

Status badges are the admin's visual language. Use them consistently:

| Status | Color | Background | Text |
|--------|-------|-----------|------|
| Active / Complete / Delivered / Healthy | Green | #d1fae5 | #059669 |
| Pending / Generating / Processing / Warning | Yellow | #fef3c7 | #d97706 |
| Failed / Error / Down / Blocked | Red | #fee2e2 | #dc2626 |
| Inactive / Paused / Disabled | Gray | #f3f4f6 | #6b7280 |
| Queued / Scheduled / New | Blue | #dbeafe | #2563eb |
| Sponsored / Affiliate | Purple | #ede9fe | #7c3aed |

### Trend indicators
- ↑ 12% (green) — improving
- ↓ 5% (red) — declining
- → 0% (gray) — flat

---

## Table Design Standards

```css
/* Header row */
.admin-table th {
  font-size: 11px;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.05em;
  color: var(--color-text-secondary);
  background: var(--color-background-secondary); /* bg-muted/40 */
  padding: 10px 16px;
  white-space: nowrap;
}

/* Data rows */
.admin-table td {
  font-size: 13px;
  padding: 12px 16px;
  border-bottom: 1px solid var(--color-border-tertiary);
}

/* Row hover */
.admin-table tr:hover {
  background: var(--color-background-secondary); /* bg-muted/30 */
}
```

- First column (name/title) is always `font-weight: 500` and links to the detail page
- Status column uses StatusBadge component
- Actions column: DropdownMenu with MoreHorizontal trigger (8×8 ghost button)
- Timestamps: relative ("2 hours ago") with full date on hover tooltip
- Counts: right-aligned, tabular-nums
- Empty state: centered icon + text + CTA button

---

## Admin Sidebar Navigation

Group pages logically:

```
OVERVIEW
  Dashboard

MANAGEMENT
  Accounts
  Users
  Affiliates

CONTENT
  Reports
  Schedules
  Property Reports

DELIVERY
  Emails
  SMS
  Lead Pages

ANALYTICS
  Overview Metrics
  CMA Analytics

CONFIGURATION
  Plans
  Security (Blocked IPs)
  System Health
```

Each item: Lucide icon (16px) + label (13px). Active state: indigo left border + light indigo background.

---

## Metric Cards

Admin metric cards show:
- Label (11px uppercase, muted)
- Value (24px, font-weight 700, Outfit or sans-serif)
- Trend badge (optional): "↑ 12% vs last month" in green/red

Layout: 4 cards per row on desktop, 2 on tablet, 1 on mobile.

```jsx
<div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
  <MetricCard label="Total Accounts" value="412" trend="+12%" trendUp />
  <MetricCard label="Active (30d)" value="87" trend="-3%" trendUp={false} />
  <MetricCard label="Reports (30d)" value="1,243" trend="+18%" trendUp />
  <MetricCard label="Failed" value="3" variant="danger" />
</div>
```

---

## Filter Bar Pattern

```jsx
<div className="flex items-center gap-3 p-3 bg-muted/20 rounded-lg border">
  <Input placeholder="Search..." className="w-[240px] h-9" />
  <Select placeholder="Status">
    <SelectItem>All</SelectItem>
    <SelectItem>Active</SelectItem>
    <SelectItem>Inactive</SelectItem>
  </Select>
  <Select placeholder="Type">...</Select>
  <DateRangePicker />
  <Button variant="ghost" size="sm">Clear</Button>
  <div className="ml-auto text-xs text-muted-foreground">
    Showing 47 of 412
  </div>
</div>
```

- Filters apply immediately (no "Apply" button needed)
- Show result count on the right
- "Clear" resets all filters
- Filters sync to URL query params (shareable filtered views)

---

## Action Patterns

### Row-level actions (in table)
```jsx
<DropdownMenu>
  <DropdownMenuTrigger asChild>
    <Button variant="ghost" size="icon" className="h-8 w-8">
      <MoreHorizontal className="h-4 w-4" />
    </Button>
  </DropdownMenuTrigger>
  <DropdownMenuContent align="end">
    <DropdownMenuItem>View Details</DropdownMenuItem>
    <DropdownMenuItem>Edit</DropdownMenuItem>
    <DropdownMenuSeparator />
    <DropdownMenuItem className="text-destructive">Delete</DropdownMenuItem>
  </DropdownMenuContent>
</DropdownMenu>
```

### Page-level actions (in header)
Primary action: `Button size="sm"` (e.g., "Create Affiliate", "Export CSV")
Secondary actions: `Button variant="outline" size="sm"`
Destructive: `Button variant="destructive" size="sm"` with confirmation dialog

### Confirmation dialogs
All destructive actions (delete, deactivate, unsponsor) require a confirmation dialog:
```
"Are you sure you want to deactivate {name}?"
"This will prevent them from generating reports."
[Cancel] [Deactivate]
```

---

## Charts (for analytics pages)

Use Recharts (already in the project):
- Line charts: daily/weekly trends
- Bar charts: distribution, comparison
- Pie/donut: breakdown by category

Chart styling:
- Colors: use the indigo brand ramp (#818CF8, #6366F1, #4F46E5) as primary series
- Gray (#9ca3af) for secondary/comparison series
- Axis labels: 11px, muted color
- Grid lines: very subtle (#f3f4f6)
- Tooltip: white card with shadow, 13px text

---

## Responsive Behavior

- Desktop (1024px+): full sidebar + content
- Tablet (768-1023px): collapsible sidebar, 2-column metric cards
- Mobile (< 768px): sidebar as drawer, 1-column cards, horizontal-scroll tables

Tables should NOT stack on mobile — use horizontal scroll with the first column (name) pinned.

---

## Performance

- Use React Query for all data fetching (staleTime: 2 min for lists, 5 min for metrics)
- Paginate tables (50 rows per page max)
- Skeleton loaders for every page (not spinners)
- Optimistic updates for toggle actions (pause/resume, activate/deactivate)

---

## Common Admin Mistakes

| Mistake | Why It Fails | Fix |
|---------|-------------|-----|
| Read-only dashboards | Admin sees problems but can't fix them | Every metric should link to the actionable page |
| Separate admin auth | Friction — admin has to log in twice | Use the same session, check is_platform_admin |
| Hardcoded colors | Doesn't match the app design system | Use design tokens (text-foreground, bg-muted, etc.) |
| Missing drill-down | Admin has to "go back and search" constantly | Every entity links to related entities |
| No empty states | Blank pages confuse new admins | Show "No X yet" with guidance |
| No export | Admin needs data for reporting/meetings | Add CSV export on every list page |
| Giant tables without filters | Unusable at 500+ rows | Filters + search + pagination on every list |
| Inline editing without confirmation | Accidental changes | Destructive actions always get a dialog |

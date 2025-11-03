# Vercel v0 Prompt: Market Reports SaaS Dashboard Enhancement

## Context

I need to upgrade a working Next.js 16 SaaS application dashboard from basic wireframe styling to a modern, professional UI. The application is a **Market Reports Generator** for real estate professionals that creates automated MLS reports with PDF export.

**Current Tech Stack:**
- Next.js 16.0.1 (App Router)
- React 19.2.0 with React Compiler
- TypeScript 5.9.3
- Tailwind CSS v4.1.16
- No UI library currently integrated

**Current State:** All dashboard pages are functional but use minimal styling - basic borders, simple buttons, plain tables. No icons, no sophisticated layouts, no visual hierarchy.

---

## Design Requirements

### Overall Design Language
- **Style:** Modern SaaS dashboard, professional but approachable
- **Color Palette:** 
  - Primary: Blue (#2563EB / blue-600)
  - Secondary: Orange (#F26B2B)
  - Neutrals: Slate scale (slate-50 through slate-900)
  - Success: Green for completed states
  - Warning: Amber for alerts
  - Danger: Red for errors/deletions
- **Typography:** System font stack (ui-sans-serif, system-ui), clear hierarchy
- **Spacing:** Generous whitespace, consistent 4px grid system
- **Components:** Use shadcn/ui patterns (you can inline the components or suggest installation)

### Key Design Principles
1. **Data Visualization:** Charts should be clean, readable, with subtle animations
2. **Status Indicators:** Clear visual feedback (badges, progress bars, icons)
3. **Actions:** Primary actions should stand out, destructive actions should be clearly marked
4. **Responsive:** Mobile-first, works perfectly on all screen sizes
5. **Loading States:** Skeleton loaders or spinners for async operations
6. **Empty States:** Friendly, actionable empty states with illustrations or icons

---

## Pages to Enhance

### 1. App Layout (Header/Navigation)
**Current File:** `apps/web/app/app-layout.tsx`

**Requirements:**
- Sticky header with subtle shadow on scroll
- Logo on left (currently just text "Market Reports")
- Horizontal navigation with active state indicators
- User menu dropdown on right (avatar, account name, logout)
- Mobile: Hamburger menu that slides in from left
- Breadcrumb navigation below header on inner pages
- Consider adding a sidebar for better navigation on desktop

**Navigation Links:**
- Overview (dashboard home)
- Reports (list view)
- New Report (primary CTA)
- Branding (settings)
- Billing (subscription)

### 2. Overview Dashboard (Analytics)
**Current File:** `apps/web/app/app/page.tsx`

**Current Elements:**
- 4 stat cards: Reports (period), Billable Reports, Monthly Limit, API Rate
- Reports by Type chart (horizontal bars)
- Daily Activity timeline (bar chart)

**Enhanced Design Needs:**
- **Stat Cards:** 
  - Add icons (FileText, CheckCircle, Zap, Activity)
  - Show trend indicators (↑ 12% from last period)
  - Add subtle hover effects
  - Consider gradient backgrounds or colored left borders
  
- **Charts:**
  - Reports by Type: Use recharts or similar, add colors per type, make interactive
  - Daily Activity: Line or area chart instead of bars, show hover tooltips
  - Add a date range picker in top right
  - Consider adding more charts: Status breakdown (pie), Top cities, Recent activity feed

- **Layout:**
  - Better grid system (maybe 3 columns on large screens)
  - Add a "Quick Actions" card (Generate Report, View Last Report, etc.)
  - Recent reports preview (last 5) with mini status badges

### 3. Reports List Page
**Current File:** `apps/web/app/app/reports/page.tsx`

**Current Elements:**
- Simple table: Created, Type, Status, Files (HTML/JSON/PDF links)
- "New Report" button in header
- Offline alert banner

**Enhanced Design Needs:**
- **Header:**
  - Add search/filter input
  - Status filter dropdown (All, Completed, Processing, Failed)
  - Report type filter
  - Sort options
  - Export all button

- **Table:**
  - Status badges with colors (green for completed, blue for processing, red for failed, yellow for pending)
  - Report type icons
  - Thumbnail preview on hover (if available)
  - More actions dropdown per row (Download, Share, Delete, Re-generate)
  - Pagination controls
  - Alternating row colors for readability
  - Empty state: Friendly illustration + "Create your first report" button

- **Files Column:**
  - Icon buttons instead of text links
  - Download icon for PDF
  - Eye icon for HTML
  - Code icon for JSON
  - Tooltips on hover

### 4. New Report Wizard
**Current File:** `apps/web/app/app/reports/new/page.tsx`

**Current Elements:**
- Multi-step wizard with Stepper component
- Form fields: Report Type, City/ZIPs, Lookback Days, Filters
- Status polling after submission

**Enhanced Design Needs:**
- **Wizard Steps:**
  - Visual progress indicator at top (step 1 of 4)
  - Each step in a card with clear title and description
  - Step icons for each stage
  - Smooth transitions between steps

- **Form Fields:**
  - Better form controls (shadcn Select, Input, RadioGroup)
  - Report type selector: Cards with icons instead of dropdown
  - City input with autocomplete suggestions
  - ZIP codes: Tag input (add/remove chips)
  - Lookback days: Slider with preset options (7, 14, 30, 60, 90 days)
  - Filters: Collapsible advanced options section

- **Status Screen:**
  - Large spinner or animated icon while processing
  - Progress steps: "Fetching data → Analyzing → Generating PDF → Complete"
  - Estimated time remaining
  - Success state: Checkmark animation + preview card with download buttons
  - Error state: Clear error message + "Try again" button

### 5. Branding Page
**Current File:** `apps/web/app/app/branding/page.tsx`

**Current Elements:**
- Logo URL input
- Primary & Secondary color pickers
- Preview section with logo and color swatches
- Save button

**Enhanced Design Needs:**
- **Layout:**
  - Two-column layout: Form on left, Live Preview on right
  - Form in a card with sections

- **Form Enhancements:**
  - Logo upload button (drag & drop zone) in addition to URL
  - Native color pickers with hex input
  - Add disclaimer text editor (rich text)
  - Font family selector (dropdown with preview)
  - Logo size slider
  - Reset to defaults button

- **Live Preview:**
  - Show full report header mock-up
  - Show sample business card
  - Show sample footer
  - Toggle between light/dark mode preview
  - "Apply to all reports" confirmation modal

### 6. Billing Page
**Current File:** `apps/web/app/app/billing/page.tsx`

**Current Elements:**
- Current plan & status text
- 3 plan cards (Starter, Professional, Enterprise)
- "Open Billing Portal" button

**Enhanced Design Needs:**
- **Current Plan Section:**
  - Large card showing current plan with badge
  - Progress bar for usage (47 of 100 reports used this month)
  - Renewal date
  - "Upgrade" or "Manage Plan" CTA

- **Pricing Cards:**
  - Feature comparison table
  - Highlighted "Most Popular" badge on recommended plan
  - Toggle between Monthly/Annual billing (show savings)
  - Icons for each feature
  - Tooltip explanations on hover
  - Clear pricing: $XX/mo (billed annually)
  - "Current Plan" vs "Upgrade" button states

- **Billing Portal:**
  - Section with invoice history preview
  - Payment method card (last 4 digits, expiry)
  - "Update payment method" button

- **Usage Metrics:**
  - Current period usage breakdown
  - API calls remaining
  - Report generation metrics
  - Mini chart showing usage over time

---

## Additional Components Needed

### Common Components to Create/Use

1. **Badge Component:**
   - Status badges (success, warning, error, info)
   - Sizing variants (sm, md, lg)
   - Pill and square variants

2. **Card Component:**
   - Header, body, footer sections
   - Optional border, shadow, hover effects
   - Clickable card variant

3. **Button Component:**
   - Variants: primary, secondary, outline, ghost, destructive
   - Sizes: sm, md, lg
   - Loading state with spinner
   - Icon support (left, right, icon-only)

4. **Select/Dropdown:**
   - Native-looking select with better styling
   - Multi-select option
   - Search/filter capability

5. **Modal/Dialog:**
   - Confirmation dialogs
   - Form modals
   - Close on backdrop click, ESC key

6. **Toast/Notification:**
   - Success, error, warning, info variants
   - Auto-dismiss after 3-5 seconds
   - Dismiss button

7. **Skeleton Loader:**
   - For loading states on cards, tables
   - Pulse animation

8. **Empty State:**
   - Icon or illustration
   - Heading and description
   - Primary action button

---

## Technical Specifications

### File Structure
```
apps/web/
├── app/
│   ├── app/
│   │   ├── page.tsx                    # Overview dashboard
│   │   ├── reports/
│   │   │   ├── page.tsx                # Reports list
│   │   │   └── new/
│   │   │       └── page.tsx            # Report wizard
│   │   ├── branding/
│   │   │   └── page.tsx                # Branding settings
│   │   ├── billing/
│   │   │   └── page.tsx                # Billing/subscription
│   │   └── app-layout.tsx              # Shared layout
│   └── globals.css                      # Global styles
├── components/
│   ├── ui/                              # shadcn/ui components
│   │   ├── badge.tsx
│   │   ├── button.tsx
│   │   ├── card.tsx
│   │   ├── dialog.tsx
│   │   ├── input.tsx
│   │   └── ...
│   └── dashboard/                       # Custom dashboard components
│       ├── stat-card.tsx
│       ├── report-table.tsx
│       ├── chart-wrapper.tsx
│       └── ...
└── lib/
    ├── api.ts                           # API helpers (existing)
    └── utils.ts                         # Utilities (existing)
```

### Data Flow (Existing - Don't Change)
- API calls via `apiFetch()` from `@/lib/api`
- Authentication via `X-Demo-Account` header (temporary)
- Base URL: `http://localhost:10000` (from env)

### Styling Approach
- Tailwind CSS v4 (already configured)
- CSS variables for theme colors (define in globals.css)
- Dark mode support (optional but recommended)
- Responsive breakpoints: sm (640px), md (768px), lg (1024px), xl (1280px)

### Icons
- Use Lucide React for icons
- Consistent 20px size for inline icons
- 24px for feature icons

### Animation
- Subtle transitions (150-300ms)
- Framer Motion for complex animations (optional)
- Hover effects on interactive elements
- Loading spinners for async operations

---

## Example: Stat Card Enhancement

**Current Code:**
```tsx
<div className="rounded-lg border bg-white p-4">
  <p className="text-sm text-slate-500">Reports (period)</p>
  <p className="mt-1 text-2xl font-semibold">{summary.total_reports ?? 0}</p>
</div>
```

**Enhanced Version:**
```tsx
<Card className="group transition-all hover:shadow-md">
  <CardContent className="flex items-start justify-between p-6">
    <div className="space-y-1">
      <p className="text-sm font-medium text-slate-600">Reports Generated</p>
      <p className="text-3xl font-bold tracking-tight">{summary.total_reports ?? 0}</p>
      <p className="flex items-center text-xs text-green-600">
        <TrendingUp className="mr-1 h-3 w-3" />
        <span>+12% from last period</span>
      </p>
    </div>
    <div className="rounded-full bg-blue-50 p-3 text-blue-600 transition-colors group-hover:bg-blue-100">
      <FileText className="h-5 w-5" />
    </div>
  </CardContent>
</Card>
```

---

## Deliverables Requested

Please provide v0-generated code for:

1. **Enhanced App Layout** with improved header/navigation
2. **Overview Dashboard** with beautiful stat cards and charts
3. **Reports List Page** with advanced table, filters, and actions
4. **New Report Wizard** with step-by-step form improvements
5. **Branding Page** with better form controls and live preview
6. **Billing Page** with pricing cards and usage metrics
7. **Common UI Components** (Badge, Card, Button, Select, Modal, Toast, Skeleton)

For each component/page:
- Use TypeScript
- Include proper types
- Use Tailwind CSS v4
- Add loading and error states
- Make fully responsive
- Include accessibility attributes (aria-labels, keyboard nav)
- Add comments for complex logic

---

## Notes for v0

- Keep existing data fetching logic (don't modify API calls)
- Maintain existing routing structure
- Don't add new dependencies unless necessary (prefer Tailwind + Lucide)
- If suggesting shadcn/ui, provide inline component code
- Prioritize visual polish over functionality changes
- Focus on professional SaaS aesthetics

---

## Success Criteria

✅ Dashboard looks modern and professional  
✅ Clear visual hierarchy and information architecture  
✅ Smooth transitions and micro-interactions  
✅ Responsive across all device sizes  
✅ Accessible (WCAG 2.1 AA compliance)  
✅ Fast (no heavy dependencies that slow down React Compiler)  
✅ Consistent design system across all pages  
✅ Easy to scan and understand at a glance  
✅ Delightful user experience with attention to detail

---

**Ready to paste into v0.dev!** 🚀


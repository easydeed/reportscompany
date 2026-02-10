# Dashboard Page

> `apps/web/app/app/page.tsx` + `components/dashboard/dashboard-content.tsx`

## Route: `/app`

### Server Component (page.tsx)

Thin shell that does one thing: checks the JWT `account_type` claim. If `INDUSTRY_AFFILIATE`, redirects to `/app/affiliate`. Otherwise renders `<DashboardContent />`.

Uses `force-dynamic` export to disable caching.

### Client Component: DashboardContent

Fetches all data client-side in parallel on mount via `useEffect`:

| API Call | Purpose |
|----------|---------|
| `GET /v1/usage` | Report count, avg render time, recent reports/emails |
| `GET /v1/account/plan-usage` | Plan limits, usage warnings |
| `GET /v1/onboarding` | Onboarding checklist status |

### UI Sections

1. **PageHeader** - "Overview" title with "New Report" button
2. **Usage Warning Banners** - Shows amber alert for `ALLOW_WITH_WARNING`, red alert for `BLOCK` plan decisions
3. **Metric Cards** (4-column grid) - Reports count, Emails Sent, Active Schedules, Avg Render time
4. **Two-Column Layout**:
   - Left (2/3): Recent Activity list (reports + emails merged, sorted by timestamp, max 8 items)
   - Right (1/3): Onboarding Checklist (`DashboardOnboarding` component)

All sections show skeleton loading states while data loads.

## Onboarding Flow

### SetupWizard (`components/onboarding/setup-wizard.tsx`)

Modal dialog with 4 steps:
1. **Welcome** - Greeting with user name (extracted from JWT/profile), overview of steps
2. **Profile** - First name, last name, company, phone, headshot upload
3. **Branding** - Logo upload, primary color, accent color with live preview
4. **Complete** - Success message, CTA button

API calls:
- `GET /v1/users/me` - Load existing profile
- `GET /v1/account` - Load existing branding + account type
- `PATCH /v1/users/me` - Save profile
- `PATCH /v1/account/branding` - Save branding
- `POST /v1/onboarding/complete-step` - Mark steps complete (`profile_complete`, `branding_setup`)

Affiliate accounts see different copy ("Invite your first agent" vs "Create your first report") and route to `/app/affiliate` on completion.

### OnboardingChecklist (`components/onboarding/onboarding-checklist.tsx`)

Persistent sidebar checklist showing progress on setup tasks. Dismissible via `POST /v1/onboarding/dismiss`.

## Key Files

- `apps/web/app/app/page.tsx` - Server component shell
- `apps/web/components/dashboard/dashboard-content.tsx` - Main dashboard UI
- `apps/web/components/onboarding/setup-wizard.tsx` - Setup wizard modal
- `apps/web/components/onboarding/onboarding-checklist.tsx` - Checklist sidebar
- `apps/web/components/onboarding/dashboard-onboarding.tsx` - Orchestrator for onboarding display
- `apps/web/components/onboarding/affiliate-onboarding.tsx` - Affiliate-specific onboarding

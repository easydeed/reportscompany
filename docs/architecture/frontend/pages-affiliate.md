# Affiliate Dashboard Pages

Affiliate pages are for `INDUSTRY_AFFILIATE` account types. Users with this account type are automatically redirected from `/app` to `/app/affiliate`.

## Route: `/app/affiliate` -- Affiliate Overview

> `apps/web/app/app/affiliate/page.tsx`

Client component that fetches data in parallel on mount.

### API Calls

| Endpoint | Purpose |
|----------|---------|
| `GET /v1/affiliate/overview` | Sponsored count, total reports, sponsored accounts list |
| `GET /v1/account/plan-usage` | Plan name, report count, limits |
| `GET /v1/onboarding` | Onboarding checklist status |

Returns 403 for non-affiliate accounts (shows "Not an Affiliate Account" message).

### UI Sections

1. **AffiliateOnboarding** - Setup wizard + checklist for new affiliates
2. **AffiliateDashboardShell** - Overview metrics, plan summary, sponsored accounts table

Sponsored accounts show: name, plan, reports this month, last report date.

## Route: `/app/affiliate/accounts/[accountId]` -- Sponsored Account Detail

> `apps/web/app/app/affiliate/accounts/[accountId]/page.tsx`

Detail view for a single sponsored account.

### API Calls

| Endpoint | Purpose |
|----------|---------|
| `GET /v1/affiliate/accounts/{accountId}` | Account details |
| `POST /v1/affiliate/accounts/{accountId}/deactivate` | Deactivate account |
| `POST /v1/affiliate/accounts/{accountId}/reactivate` | Reactivate account |
| `POST /v1/affiliate/accounts/{accountId}/unsponsor` | Remove sponsorship |

## Route: `/app/affiliate/branding` -- Affiliate Branding

> `apps/web/app/app/affiliate/branding/page.tsx`

White-label branding editor for the affiliate's brand. This branding is applied to all sponsored agents' reports.

API: `GET/PATCH /v1/affiliate/branding`

## Route: `/app/affiliate/property-reports` -- Affiliate Property Reports

> `apps/web/app/app/affiliate/property-reports/page.tsx`

View property reports across all sponsored accounts.

## InviteAgentModal

> `apps/web/components/invite-agent-modal.tsx`

Modal dialog for inviting new agents to be sponsored. Sends invite via `POST /v1/affiliate/invite-agent`.

## Key Files

- `apps/web/app/app/affiliate/page.tsx` - Main affiliate dashboard
- `apps/web/app/app/affiliate/accounts/[accountId]/page.tsx` - Sponsored account detail
- `apps/web/app/app/affiliate/branding/page.tsx` - Branding editor
- `apps/web/app/app/affiliate/property-reports/page.tsx` - Property reports
- `apps/web/components/invite-agent-modal.tsx` - Agent invite modal
- `apps/web/components/onboarding/affiliate-onboarding.tsx` - Affiliate onboarding flow

# Settings Pages

All settings pages live under `/app/settings/` and use client-side data fetching.

## Route: `/app/settings` -- Settings Overview

> `apps/web/app/app/settings/page.tsx`

Landing page with links to all settings sections.

## Route: `/app/settings/profile` -- Profile Settings

> `apps/web/app/app/settings/profile/page.tsx`

Edit user profile information.

| API Call | Purpose |
|----------|---------|
| `GET /v1/users/me` | Load current profile |
| `PATCH /v1/users/me` | Save profile changes |

Fields: First name, last name, email, phone, company name, job title, website, avatar/headshot.

## Route: `/app/settings/security` -- Security Settings

> `apps/web/app/app/settings/security/page.tsx`

Password change form.

| API Call | Purpose |
|----------|---------|
| `PATCH /v1/auth/change-password` | Change password (current + new) |

## Route: `/app/settings/billing` -- Billing Settings

> `apps/web/app/app/settings/billing/page.tsx`

Stripe subscription management.

| API Call | Purpose |
|----------|---------|
| `GET /v1/account/plan-usage` | Current plan + usage |
| `POST /v1/billing/checkout` | Create Stripe checkout session |
| `POST /v1/billing/portal` | Create Stripe customer portal session |

Uses `components/stripe-billing-actions.tsx` for Stripe redirect buttons.

See also: `/app/billing/page.tsx` -- alternate billing page.

## Route: `/app/settings/branding` -- Branding Settings

> `apps/web/app/app/settings/branding/page.tsx`

White-label branding editor. Also accessible at `/app/branding/page.tsx`.

| API Call | Purpose |
|----------|---------|
| `GET /v1/account` | Load current branding |
| `PATCH /v1/account/branding` | Save branding changes |
| `POST /v1/branding/test-email` | Send test branded email |
| `POST /v1/branding/sample-pdf` | Generate sample branded PDF |
| `POST /v1/branding/sample-jpg` | Generate sample branded social image |

Uses `components/branding-form.tsx` and `components/branding-preview.tsx`.

Fields: Display name, logo URL, footer logo URL, rep photo URL, primary color, accent color, contact line 1 & 2, website URL.

## Other Settings-Related Pages

- `/app/account/settings/page.tsx` -- Account-level settings
- `/account/plan/page.tsx` -- Plan selection page

## Key Files

- `apps/web/app/app/settings/page.tsx`
- `apps/web/app/app/settings/profile/page.tsx`
- `apps/web/app/app/settings/security/page.tsx`
- `apps/web/app/app/settings/billing/page.tsx`
- `apps/web/app/app/settings/branding/page.tsx`
- `apps/web/components/branding-form.tsx`
- `apps/web/components/branding-preview.tsx`
- `apps/web/components/stripe-billing-actions.tsx`

# Frontend Pages

> `apps/web/app/` -- All Next.js App Router pages

---

## Public Pages (no auth required)

| Path | File | Purpose |
|------|------|---------|
| `/` | `app/page.tsx` | Marketing landing page |
| `/login` | `app/login/page.tsx` | Login form |
| `/register` | `app/register/page.tsx` | User registration |
| `/forgot-password` | `app/forgot-password/page.tsx` | Request password reset |
| `/reset-password` | `app/reset-password/page.tsx` | Reset password form |
| `/verify-email` | `app/verify-email/page.tsx` | Email verification |
| `/welcome` | `app/welcome/page.tsx` | Welcome / invite acceptance |
| `/about` | `app/about/page.tsx` | About page |
| `/blog` | `app/blog/page.tsx` | Blog listing |
| `/careers` | `app/careers/page.tsx` | Careers page |
| `/help` | `app/help/page.tsx` | Help / documentation |
| `/privacy` | `app/privacy/page.tsx` | Privacy policy |
| `/terms` | `app/terms/page.tsx` | Terms of service |
| `/security` | `app/security/page.tsx` | Security info |
| `/docs` | `app/docs/page.tsx` | API documentation |
| `/access-denied` | `app/access-denied/page.tsx` | 403 page |

---

## Public Dynamic Pages

| Path | File | Purpose |
|------|------|---------|
| `/p/[code]` | `app/p/[code]/page.tsx` | Lead capture landing page |
| `/cma/[code]` | `app/cma/[code]/page.tsx` | Consumer CMA page |
| `/r/[id]` | `app/r/[id]/page.tsx` | Public report viewer (mobile) |
| `/print/[runId]` | `app/print/[runId]/page.tsx` | Print-optimized report |
| `/social/[runId]` | `app/social/[runId]/page.tsx` | Social media share view |
| `/branding-preview/[reportType]` | `app/branding-preview/...` | Branding preview |
| `/branding-preview/social/[reportType]` | `app/branding-preview/social/...` | Social branding preview |

---

## Protected Pages (`/app/*` -- requires auth)

### Dashboard
| Path | File | Purpose |
|------|------|---------|
| `/app` | `app/app/page.tsx` | Main dashboard |
| `/app/layout.tsx` | Layout wrapper | Sidebar + nav via AppLayoutClient |

### Reports
| Path | File | Purpose |
|------|------|---------|
| `/app/reports` | `app/app/reports/page.tsx` | Reports list |
| `/app/reports/new` | `app/app/reports/new/page.tsx` | Create new report (wizard) |

### Property Reports
| Path | File | Purpose |
|------|------|---------|
| `/app/property` | `app/app/property/page.tsx` | Property list |
| `/app/property/new` | `app/app/property/new/page.tsx` | Create property report |
| `/app/property/[id]` | `app/app/property/[id]/page.tsx` | Property detail |
| `/app/property/[id]/settings` | `app/app/property/[id]/settings/page.tsx` | Property settings |

### Schedules
| Path | File | Purpose |
|------|------|---------|
| `/app/schedules` | `app/app/schedules/page.tsx` | Schedules list |
| `/app/schedules/new` | `app/app/schedules/new/page.tsx` | Create schedule (wizard) |
| `/app/schedules/[id]` | `app/app/schedules/[id]/page.tsx` | Schedule detail |
| `/app/schedules/[id]/edit` | `app/app/schedules/[id]/edit/page.tsx` | Edit schedule |

### People & Leads
| Path | File | Purpose |
|------|------|---------|
| `/app/people` | `app/app/people/page.tsx` | Contacts list |
| `/app/leads` | `app/app/leads/page.tsx` | Leads list |
| `/app/lead-page` | `app/app/lead-page/page.tsx` | Lead page editor |

### Settings
| Path | File | Purpose |
|------|------|---------|
| `/app/settings` | `app/app/settings/page.tsx` | Settings overview |
| `/app/settings/profile` | `app/app/settings/profile/page.tsx` | Profile settings |
| `/app/settings/billing` | `app/app/settings/billing/page.tsx` | Billing settings |
| `/app/settings/security` | `app/app/settings/security/page.tsx` | Security settings |
| `/app/settings/branding` | `app/app/settings/branding/page.tsx` | Branding settings |

### Billing & Branding
| Path | File | Purpose |
|------|------|---------|
| `/app/billing` | `app/app/billing/page.tsx` | Billing page |
| `/app/branding` | `app/app/branding/page.tsx` | Branding editor |

### Affiliate
| Path | File | Purpose |
|------|------|---------|
| `/app/affiliate` | `app/app/affiliate/page.tsx` | Affiliate dashboard |
| `/app/affiliate/accounts/[accountId]` | `...page.tsx` | Sponsored account detail |
| `/app/affiliate/branding` | `...page.tsx` | Affiliate branding |
| `/app/affiliate/property-reports` | `...page.tsx` | Affiliate property reports |

---

## Admin Pages (`/app/admin/*` -- requires admin role)

| Path | File | Purpose |
|------|------|---------|
| `/app/admin` | `app/app/admin/page.tsx` | Admin dashboard |
| `/app/admin/accounts` | `...page.tsx` | Manage all accounts |
| `/app/admin/accounts/[id]` | `...page.tsx` | Account detail |
| `/app/admin/affiliates` | `...page.tsx` | Manage affiliates |
| `/app/admin/affiliates/new` | `...page.tsx` | Create affiliate |
| `/app/admin/affiliates/[id]` | `...page.tsx` | Affiliate detail |
| `/app/admin/users` | `...page.tsx` | Manage users |
| `/app/admin/leads` | `...page.tsx` | Manage leads |
| `/app/admin/property-reports` | `...page.tsx` | Property reports |
| `/app/admin/property-reports/[id]` | `...page.tsx` | Property report detail |
| `/app/admin/sms` | `...page.tsx` | SMS management |

---

## Account
| Path | File | Purpose |
|------|------|---------|
| `/account/plan` | `app/account/plan/page.tsx` | Plan selection |
| `/app/account/settings` | `...page.tsx` | Account settings |

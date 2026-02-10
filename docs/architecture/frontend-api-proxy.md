# Frontend API Proxy Routes

> `apps/web/app/api/` -- Next.js API routes that proxy requests to the FastAPI backend

---

## How the Proxy Works

Client components call `lib/api.ts` which sends requests to `/api/proxy/v1/...`. These Next.js API routes forward the request to the backend with the `mr_token` cookie for authentication, avoiding CORS issues.

```
Browser -> /api/proxy/v1/reports -> FastAPI backend /v1/reports
```

---

## Auth Routes (`/api/auth/`)

| Route | Method | Backend Endpoint | Purpose |
|-------|--------|------------------|---------|
| `/api/auth/me` | GET | `/v1/me` | Get current user |

---

## Proxy Routes (`/api/proxy/v1/...`)

### Authentication
| Route | Methods | Purpose |
|-------|---------|---------|
| `/api/proxy/v1/auth/login` | POST | Login |
| `/api/proxy/v1/auth/logout` | POST | Logout |
| `/api/proxy/v1/auth/register` | POST | Register |
| `/api/proxy/v1/auth/verify-email` | POST | Verify email |
| `/api/proxy/v1/auth/resend-verification` | POST | Resend verification |
| `/api/proxy/v1/auth/forgot-password` | POST | Request password reset |
| `/api/proxy/v1/auth/reset-password` | POST | Reset password |
| `/api/proxy/v1/auth/accept-invite` | POST | Accept invite |

### Reports
| Route | Methods | Purpose |
|-------|---------|---------|
| `/api/proxy/v1/reports` | GET, POST | List / create reports |
| `/api/proxy/v1/reports/[id]` | GET | Get report detail |

### Schedules
| Route | Methods | Purpose |
|-------|---------|---------|
| `/api/proxy/v1/schedules` | GET, POST | List / create schedules |
| `/api/proxy/v1/schedules/[id]` | GET, PUT, DELETE | Schedule CRUD |

### Account
| Route | Methods | Purpose |
|-------|---------|---------|
| `/api/proxy/v1/account/plan-usage` | GET | Plan usage data |
| `/api/proxy/v1/accounts/[id]` | GET | Account info |

### Contacts
| Route | Methods | Purpose |
|-------|---------|---------|
| `/api/proxy/v1/contacts` | GET, POST | List / create contacts |
| `/api/proxy/v1/contacts/import` | POST | Bulk import contacts |
| `/api/proxy/v1/contact-groups` | GET, POST | List / create groups |

### Leads
| Route | Methods | Purpose |
|-------|---------|---------|
| `/api/proxy/v1/leads` | GET, POST | List / create leads |
| `/api/proxy/v1/leads/export` | GET | Export leads to CSV |

### Affiliate
| Route | Methods | Purpose |
|-------|---------|---------|
| `/api/proxy/v1/affiliate/overview` | GET | Affiliate dashboard data |
| `/api/proxy/v1/affiliate/accounts` | GET | Sponsored accounts |
| `/api/proxy/v1/affiliate/branding` | GET, POST | Branding CRUD |
| `/api/proxy/v1/affiliate/invite-agent` | POST | Invite agent |

### Billing
| Route | Methods | Purpose |
|-------|---------|---------|
| `/api/proxy/v1/billing/checkout` | POST | Start Stripe checkout |
| `/api/proxy/v1/billing/customer-portal` | POST | Open Stripe portal |

### Property
| Route | Methods | Purpose |
|-------|---------|---------|
| `/api/proxy/v1/property/search` | GET | Property search |
| `/api/proxy/v1/property/preview` | POST | Property preview |
| `/api/proxy/v1/property/comparables` | GET | Get comparables |
| `/api/proxy/v1/property/stats` | GET | Property stats |
| `/api/proxy/v1/property/reports` | GET, POST | Property report CRUD |
| `/api/proxy/v1/property/reports/[id]` | GET, PUT, DELETE | Property report detail |

### Admin
| Route | Methods | Purpose |
|-------|---------|---------|
| `/api/proxy/v1/admin/accounts` | GET | All accounts |
| `/api/proxy/v1/admin/affiliates` | GET, POST | Affiliate management |
| `/api/proxy/v1/admin/agents` | GET | Agent management |
| `/api/proxy/v1/admin/users` | GET | User management |
| `/api/proxy/v1/admin/leads` | GET | Lead management |
| `/api/proxy/v1/admin/reports` | GET | Report management |
| `/api/proxy/v1/admin/schedules` | GET | Schedule management |
| `/api/proxy/v1/admin/metrics` | GET | Platform metrics |
| `/api/proxy/v1/admin/emails` | GET | Email logs |
| `/api/proxy/v1/admin/stats` | GET | Platform stats |
| `/api/proxy/v1/admin/sms` | GET, POST | SMS management |
| `/api/proxy/v1/admin/property-reports` | GET | Property reports |

### User / Me
| Route | Methods | Purpose |
|-------|---------|---------|
| `/api/proxy/v1/me` | GET | Current user profile |
| `/api/proxy/v1/me/leads` | GET | User's leads |
| `/api/proxy/v1/me/lead-page` | GET, PUT | User's lead page |
| `/api/proxy/v1/users/me/email` | PUT | Update email |
| `/api/proxy/v1/users/me/password` | PUT | Update password |

### Branding Tools
| Route | Methods | Purpose |
|-------|---------|---------|
| `/api/proxy/v1/branding/sample-jpg` | POST | Generate sample JPG |
| `/api/proxy/v1/branding/sample-pdf` | POST | Generate sample PDF |
| `/api/proxy/v1/branding/test-email` | POST | Send test email |

### Onboarding
| Route | Methods | Purpose |
|-------|---------|---------|
| `/api/proxy/v1/onboarding/status` | GET | Onboarding progress |
| `/api/proxy/v1/onboarding/complete-step` | POST | Complete a step |
| `/api/proxy/v1/onboarding/dismiss` | POST | Dismiss onboarding |

### Upload
| Route | Methods | Purpose |
|-------|---------|---------|
| `/api/proxy/v1/upload/branding` | POST | Upload branding assets |

### Usage
| Route | Methods | Purpose |
|-------|---------|---------|
| `/api/proxy/v1/usage` | GET | Usage tracking |

### CMA
| Route | Methods | Purpose |
|-------|---------|---------|
| `/api/proxy/v1/cma/search` | GET | CMA property search |
| `/api/proxy/v1/cma/request` | POST | Request CMA |

---

## Direct API Routes (`/api/v1/admin/`)

Some admin routes go directly to the backend without the proxy pattern.

## Social Route

| Route | Methods | Purpose |
|-------|---------|---------|
| `/api/social/[runId]` | GET | Social content for sharing |

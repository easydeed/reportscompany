# TrendyReports File Tree

> Single source of truth for locating files across all 3 services.

## API Service (`apps/api/src/api/`)

```
apps/api/src/api/
├── main.py                          # FastAPI app init, middleware + 26 routers
├── settings.py                      # Pydantic env settings (DB, Redis, Stripe, JWT)
├── db.py                            # Connection helper, RLS setter, dict helpers
├── auth.py                          # JWT sign/verify, bcrypt, API key hash
├── worker_client.py                 # Enqueue tasks to Redis/Celery
│
├── config/
│   └── billing.py                   # Stripe price-ID mapping + validation
│
├── deps/
│   └── admin.py                     # FastAPI dependency: require platform admin
│
├── schemas/
│   ├── __init__.py
│   └── property.py                  # ComparableProperty, PropertyStats, normalization
│
├── middleware/
│   ├── authn.py                     # AuthContextMiddleware + RateLimitMiddleware
│   └── rls.py                       # RLSContextMiddleware (legacy placeholder)
│
├── routes/
│   ├── health.py                    # GET /health
│   ├── auth.py                      # /v1/auth/* (login, register, password reset, verify)
│   ├── reports.py                   # /v1/reports (CRUD + limit enforcement)
│   ├── report_data.py               # /v1/reports/{id}/data (public for PDF gen)
│   ├── property.py                  # /v1/property/* (search, comps, CMA reports)
│   ├── schedules.py                 # /v1/schedules/* (CRUD, pause, resume)
│   ├── contacts.py                  # /v1/contacts/* (CRUD, import)
│   ├── contact_groups.py            # /v1/contact-groups/* (CRUD)
│   ├── leads.py                     # /v1/leads/* (capture, list, export)
│   ├── lead_pages.py                # /v1/lead-pages/* (landing page management)
│   ├── account.py                   # /v1/account/* (settings, branding, plan-usage)
│   ├── billing.py                   # /v1/billing/* (Stripe checkout, portal)
│   ├── stripe_webhook.py            # /v1/webhooks/stripe (subscription events)
│   ├── webhooks.py                  # /v1/webhooks (generic webhook management)
│   ├── admin.py                     # /v1/admin/* (platform admin functions)
│   ├── admin_metrics.py             # /v1/admin/metrics/* (analytics)
│   ├── affiliates.py                # /v1/affiliate/* (overview, invite, branding)
│   ├── me.py                        # /v1/me (current user profile, leads, lead-page)
│   ├── users.py                     # /v1/users/* (user management within accounts)
│   ├── apikeys.py                   # /v1/api-keys (CRUD)
│   ├── usage.py                     # /v1/usage (tracking endpoints)
│   ├── onboarding.py                # /v1/onboarding/* (steps, dismiss)
│   ├── upload.py                    # /v1/upload/* (file uploads)
│   ├── branding_tools.py            # /v1/branding/* (sample PDF/JPG, test email)
│   ├── mobile_reports.py            # /v1/r/* (mobile report viewer)
│   ├── unsubscribe.py               # /v1/email/unsubscribe
│   ├── devfiles.py                  # /dev-files/* (development only)
│   └── dev_stripe_prices.py         # /v1/dev/* (development only)
│
└── services/
    ├── accounts.py                  # Multi-account: user accounts, access verification
    ├── affiliates.py                # Sponsored accounts, overview metrics
    ├── usage.py                     # Monthly usage, plan resolution, limit enforcement
    ├── plans.py                     # Plan catalog with Stripe pricing
    ├── plan_lookup.py               # Plan slug/price lookups
    ├── billing_state.py             # Stripe subscription state sync
    ├── branding.py                  # White-label brand resolution chain
    ├── email.py                     # Resend email service (verification, reset, etc.)
    ├── simplyrets.py                # SimplyRETS MLS API client
    ├── sitex.py                     # SiteX Pro API client (OAuth2, property lookup)
    ├── twilio_sms.py                # Twilio SMS delivery
    ├── property_stats.py            # Property report statistics
    ├── qr_service.py                # QR code generation
    ├── agent_code.py                # Agent tracking codes
    ├── upload.py                    # File upload to S3/R2
    └── __init__.py                  # Exports LimitDecision, evaluate_report_limit, etc.
```

## Worker Service (`apps/worker/src/worker/`)

```
apps/worker/src/worker/
├── app.py                           # Celery app config (Redis broker, SSL, beat schedule)
├── tasks.py                         # Core tasks: generate_report, process_consumer_report (1465 lines)
├── pdf_engine.py                    # Dual PDF: Playwright (local) + PDFShift (cloud) (286 lines)
├── property_builder.py              # PropertyReportBuilder class with 5 themes (800 lines)
├── report_builders.py               # Market report JSON builders (8 report types) (904 lines)
├── filter_resolver.py               # Market-adaptive filter resolution (254 lines)
├── query_builders.py                # SimplyRETS API query construction (363 lines)
├── ai_insights.py                   # OpenAI market insights with sender-aware tone (329 lines)
├── schedules_tick.py                # Background scheduler: finds due schedules, enqueues (448 lines)
├── limit_checker.py                 # Monthly report limit enforcement (151 lines)
├── cache.py                         # Redis caching (15-min TTL)
├── redis_utils.py                   # Redis connection factory with SSL
│
├── property_tasks/
│   └── property_report.py           # Celery task for property PDF generation (394 lines)
│
├── compute/
│   ├── extract.py                   # PropertyDataExtractor (SimplyRETS -> clean objects) (130 lines)
│   └── validate.py                  # Property data validation and filtering
│
├── email/
│   ├── send.py                      # Schedule email orchestrator with branding (165 lines)
│   ├── template.py                  # Jinja2 HTML email templates (2019 lines)
│   └── providers/
│       └── sendgrid.py              # SendGrid v3 API with retry logic (127 lines)
│
├── sms/
│   └── send.py                      # Twilio SMS: consumer + agent notifications (148 lines)
│
├── vendors/
│   └── simplyrets.py                # SimplyRETS MLS API with rate limiting (131 lines)
│
├── utils/
│   ├── photo_proxy.py               # MLS photo -> R2 proxy (291 lines)
│   └── image_proxy.py               # General image -> R2 proxy (213 lines)
│
└── templates/property/
    ├── _base/
    │   ├── base.jinja2              # Base template with inheritance
    │   └── _macros.jinja2           # Shared Jinja2 macros
    ├── teal/teal.jinja2             # Theme 4: Teal + Navy (DEFAULT)
    ├── bold/bold.jinja2             # Theme 5: Navy + Gold
    ├── classic/classic.jinja2       # Theme 1: Navy + Sky Blue
    ├── modern/modern.jinja2         # Theme 2: Coral + Midnight
    └── elegant/elegant.jinja2       # Theme 3: Burgundy + Gold
```

## Frontend (`apps/web/`)

```
apps/web/
├── middleware.ts                     # JWT auth guard for /app/* routes
├── next.config.ts                   # React Compiler, Turbopack, external dir
├── package.json                     # Next.js 16, React 19, Radix UI, React Query
│
├── lib/
│   ├── api.ts                       # Client-side fetch (routes through /api/proxy)
│   ├── api-server.ts                # Server-side fetch (direct to backend + cookies)
│   ├── get-api-base.ts              # API base URL resolution
│   ├── utils.ts                     # cn(), formatters, helpers
│   ├── templates.ts                 # Report template definitions
│   ├── social-templates.ts          # Social media post templates
│   ├── sample-report-data.ts        # Sample data for previews
│   ├── property-report-assets.ts    # Property report asset references
│   ├── wizard-types.ts              # TypeScript types for wizard flows
│   └── hooks/
│       ├── use-user.ts              # React Query user hook
│       └── use-plan-usage.ts        # Plan usage data hook
│
├── hooks/
│   ├── use-toast.ts                 # Toast notification hook
│   └── useGooglePlaces.ts           # Google Places autocomplete hook
│
├── components/
│   ├── ui/                          # 50+ Radix/shadcn primitives
│   ├── report-builder/              # Market report wizard (index + 4 sections)
│   ├── schedule-builder/            # Schedule wizard (index + 5 sections)
│   ├── property/                    # PropertySearchForm, ComparablesPicker, MapModal, ThemeSelector
│   ├── admin/                       # AdminOverview, EmailLogTable, ReportsTable, SchedulesTable
│   ├── marketing/                   # Hero, Pricing, HowItWorks, ReportTypesGrid, etc.
│   ├── onboarding/                  # SetupWizard, OnboardingChecklist, DashboardOnboarding
│   ├── branding/                    # DownloadTools, ReportPreview
│   ├── mobile-report/               # MobileReportViewer
│   ├── lead-pages/                  # ConsumerLandingWizard
│   ├── schedules/                   # ScheduleTable, ScheduleDetail, ScheduleWizard
│   ├── dashboard/                   # DashboardContent
│   ├── providers/                   # QueryProvider (React Query setup)
│   └── [shared components]          # Navbar, Footer, AccountSwitcher, DataTable, etc.
│
├── app/
│   ├── layout.tsx                   # Root layout
│   ├── page.tsx                     # Landing page (marketing)
│   ├── app-layout.tsx               # Client wrapper with QueryProvider
│   │
│   ├── login/page.tsx               # Login
│   ├── register/page.tsx            # Register
│   ├── forgot-password/page.tsx     # Forgot password
│   ├── reset-password/page.tsx      # Reset password
│   ├── verify-email/page.tsx        # Email verification
│   ├── welcome/page.tsx             # Invite acceptance
│   │
│   ├── app/                         # Protected routes (auth required)
│   │   ├── page.tsx                 # Dashboard
│   │   ├── layout.tsx               # App layout with sidebar
│   │   ├── reports/                 # Report list + new report wizard
│   │   ├── property/               # Property list + new + detail + settings
│   │   ├── schedules/              # Schedule list + new + detail + edit
│   │   ├── people/                 # Contacts
│   │   ├── leads/                  # Lead management
│   │   ├── lead-page/              # Lead page editor
│   │   ├── settings/               # Profile, billing, security, branding
│   │   ├── billing/                # Billing page
│   │   ├── branding/               # Branding editor
│   │   ├── affiliate/              # Affiliate dashboard + accounts + branding
│   │   ├── admin/                  # Admin: accounts, users, affiliates, leads, reports, SMS
│   │   └── account/               # Account settings
│   │
│   ├── r/[id]/page.tsx              # Public mobile report viewer
│   ├── p/[code]/page.tsx            # Property landing page + lead form
│   ├── cma/[code]/page.tsx          # Consumer CMA wizard
│   ├── print/[runId]/page.tsx       # Print-optimized report (PDF source)
│   ├── social/[runId]/page.tsx      # Social image (1080x1920)
│   │
│   └── api/                         # Next.js API routes
│       ├── auth/me/route.ts         # Get current user
│       ├── proxy/v1/                # ~60 proxy routes to backend
│       └── social/[runId]/route.ts  # Social content endpoint
│
├── [static pages: about, blog, careers, help, privacy, terms, security, docs, access-denied]
└── branding-preview/                # Branding preview routes
```

## Database (`db/`)

```
db/
└── migrations/
    ├── 0001_init.sql                # Core tables: accounts, users, report_generations, api_keys, usage_tracking + RLS
    ├── 0002_webhooks.sql            # webhooks + webhook_deliveries + RLS
    ├── 0003_plans.sql               # plans table + seed (free, pro, team, affiliate, sponsored_free)
    ├── 0004_account_users.sql       # account_users M2M + roles
    ├── 0005_auth_tables.sql         # password_reset_tokens, email_verification_tokens, login_attempts
    ├── 0006_schedules.sql           # schedules, schedule_runs, email_log, email_suppressions + RLS
    ├── 0007_contacts.sql            # contacts table
    ├── 0008_jwt_blacklist.sql       # JWT revocation table
    ├── 0009_contacts_rls.sql        # contacts RLS policies
    ├── 0010-0033                    # Various schema additions, indexes, columns
    ├── 0034_property_reports.sql    # property_reports + leads + RLS + indexes
    ├── 0035-0037                    # Lead rate limits, blocked IPs, lead enhancements
    ├── 0038_consumer_reports.sql    # consumer_reports + report_analytics + RLS
    ├── 0039-0041                    # Agent codes, SMS logs, lead page features
    ├── seed_demo_accounts.sql       # Development seed data
    └── seed_demo_accounts_v2.sql    # Updated seed data
```

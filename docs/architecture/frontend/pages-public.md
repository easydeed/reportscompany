# Public Pages (No Auth Required)

These pages are accessible without authentication. They are consumer-facing or used as render targets.

## Route: `/r/[id]` -- Mobile Report Viewer

> `apps/web/app/r/[id]/page.tsx` -> `components/mobile-report/MobileReportViewer.tsx`

Consumer-facing report view. Renders the market report in a mobile-friendly format. This is what recipients see when they click a report link in an email.

## Route: `/p/[code]` -- Property Landing Page + Lead Capture

> `apps/web/app/p/[code]/page.tsx`

Public landing page for a property report. Accessed via QR code on printed property reports.

Displays property details and a lead capture form (name, email, phone, message). On submission, creates a lead in the backend and notifies the agent via SMS + email.

API calls (public, no auth):
- `GET /v1/cma/{code}/search` - Load property data for display
- `POST /v1/cma/{code}/request` - Submit lead capture form

## Route: `/cma/[code]` -- Consumer CMA Wizard

> `apps/web/app/cma/[code]/page.tsx`

Public page where consumers can request a CMA report for their property. Multi-step wizard that collects property address and contact info.

## Route: `/print/[runId]` -- Print-Optimized Report

> `apps/web/app/print/[runId]/page.tsx`

Full-page HTML report optimized for PDF rendering. This is the page that the backend's headless browser captures to generate PDF files.

Not meant for direct user viewing -- used as the PDF source URL by the report generation worker.

## Route: `/social/[runId]` -- Social Media Image

> `apps/web/app/social/[runId]/page.tsx`

1080x1920 HTML page designed for social media sharing (Instagram Stories, TikTok, etc.). Rendered by the backend to produce a JPG/PNG image.

Includes agent branding, key metrics, and contact info. The backend captures this as a screenshot.

## Route: `/branding-preview/[reportType]` -- Branding Preview

> `apps/web/app/branding-preview/[reportType]/page.tsx`

Preview of how branding looks on a specific report type. Used by the branding editor to show a live preview.

Also: `/branding-preview/social/[reportType]/page.tsx` for social media template preview.

## Other Public Pages

| Route | File | Purpose |
|-------|------|---------|
| `/` | `app/page.tsx` | Marketing homepage |
| `/login` | `app/login/page.tsx` | Login form |
| `/register` | `app/register/page.tsx` | Registration form |
| `/forgot-password` | `app/forgot-password/page.tsx` | Password reset request |
| `/reset-password` | `app/reset-password/page.tsx` | Password reset form |
| `/verify-email` | `app/verify-email/page.tsx` | Email verification |
| `/welcome` | `app/welcome/page.tsx` | Post-registration welcome |
| `/about` | `app/about/page.tsx` | About page |
| `/blog` | `app/blog/page.tsx` | Blog |
| `/docs` | `app/docs/page.tsx` | Documentation |
| `/help` | `app/help/page.tsx` | Help center |
| `/careers` | `app/careers/page.tsx` | Careers page |
| `/terms` | `app/terms/page.tsx` | Terms of service |
| `/privacy` | `app/privacy/page.tsx` | Privacy policy |
| `/security` | `app/security/page.tsx` | Security page |
| `/status` | `app/status/page.tsx` | Service status |
| `/access-denied` | `app/access-denied/page.tsx` | Access denied |
| `/unsubscribed` | `app/unsubscribed/page.tsx` | Email unsubscribe confirmation |

## Key Files

- `apps/web/app/r/[id]/page.tsx` + `components/mobile-report/MobileReportViewer.tsx`
- `apps/web/app/p/[code]/page.tsx`
- `apps/web/app/cma/[code]/page.tsx`
- `apps/web/app/print/[runId]/page.tsx`
- `apps/web/app/social/[runId]/page.tsx`
- `apps/web/app/branding-preview/[reportType]/page.tsx`
- `apps/web/components/marketing-home.tsx` + `components/marketing/` - Landing page components

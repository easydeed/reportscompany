# TrendyReports — Forbidden Changes (Read First)

These changes BREAK PRODUCTION. Never make them without explicit user approval.

## Database

- **NEVER** change plan_slug values in the `plans` table. Code throughout references `'starter'` and `'pro'`. Renaming the DB values breaks dozens of conditionals.
- **NEVER** drop or rename existing columns. Always add new columns and migrate gradually.
- **NEVER** delete rows from `accounts`, `users`, `report_generations`, `email_log` without explicit user approval. These have FK dependencies and historical value.
- **NEVER** run UPDATE/DELETE without a WHERE clause.
- **NEVER** modify Row-Level Security policies without understanding tenant isolation impact.

## Code Conditionals

- **NEVER** rename TypeScript types like `StarterPlan`, `ProPlan`. They're tied to slugs.
- **NEVER** change conditions like `planSlug === 'starter'` to `planSlug === 'growth'`. The slug stays `'starter'`.
- **NEVER** change `account_type` enum values (`REGULAR`, `INDUSTRY_AFFILIATE`, `TITLE_COMPANY`).
- **NEVER** change the role hierarchy assumptions in middleware without coordinated frontend changes.

## Stripe

- **NEVER** modify Stripe price IDs in code without confirming the Stripe Dashboard match.
- **NEVER** test against production Stripe keys.
- **NEVER** create new products/prices without Jerry's approval.

## API

- **NEVER** change API response shapes without coordinating frontend updates.
- **NEVER** remove fields from response models — add new ones instead.
- **NEVER** change endpoint paths (e.g., `/v1/reports`) without updating Next.js proxy routes.

## Frontend

- **NEVER** put `QueryProvider` inside conditional layout branches. It must always be present under `/app`.
- **NEVER** add routes to `BUILDER_ROUTES` without testing the React Query implication.
- **NEVER** hardcode brand colors in components. Use props from `branding` object.
- **NEVER** assume an agent's branding falls back to their sponsor's. Agents ALWAYS use their own branding.

## PDF Generation

- **NEVER** suggest WeasyPrint, wkhtmltopdf, ReportLab, pdfkit, fpdf, xhtml2pdf, or Puppeteer.
- **NEVER** suggest Poetry as a PDF tool — Poetry is a Python package manager, not a renderer.
- Production PDFs are rendered by **PDFShift** via HTTPS API.
- Local dev fallback is Playwright. That's the ONLY other path.

## Secrets

- **NEVER** commit secrets to the repo. `.env` is gitignored; `.env.example` should NOT contain real keys.
- **NEVER** log API keys, tokens, or passwords.
- **NEVER** share JWTs in chat or commits.

## Deployment

- **NEVER** force-push to main.
- **NEVER** deploy directly without going through the Vercel/Render auto-deploy pipeline.
- **NEVER** skip CI checks.

## Demo Accounts

These accounts are archived and should NEVER be modified or deleted:
- Demo Account: `912014c3-6deb-4b40-a28d-489ef3923a3a`
- Demo Title Company: `6588ca4a-9509-4118-9359-d1cbf72dcd52`
- Demo Sponsored Agent: `d84a771e-1add-408b-bd82-7feb198121d4`
- Demo Free Agent: `cf7d8fde-4bb4-4603-88f0-39459053117b`
- Demo Pro Agent: `c059d968-e171-4549-9667-70eb7f3735cc`

## Real Customer (PCT)

These accounts are LIVE customer data. Never modify without explicit user approval:
- Pacific Coast Title Company: `494f23ee-e8be-4fa2-9d7e-c18c1fb24a5b`
- All 6 PCT reps parented under it (Jerry Hernandez, Angeline Ahn, Hugo Lopez, Jorge Mesa, Izzy Lopez, Jesse Lopez)

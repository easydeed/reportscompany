# Affiliate / title-rep view — inventory

Read from `easydeed/reportscompany@main` 2026-10-23. Purpose: name the real routes before asking Design what the sponsor-side views should be.

## 1. Who the tiers are (as the code sees them)

Resolved server-side in `app/app/layout.tsx` from the JWT, passed to `app-layout.tsx` as four booleans:

| Flag | JWT condition | Role label in rail | Home |
|---|---|---|---|
| `isAdmin` | `is_platform_admin` | Platform admin | `/app/admin` |
| `isCompanyAdmin` | `is_company_admin` or `account_type === 'TITLE_COMPANY'` | Company admin | `/app/company` |
| `isAffiliate` | `is_affiliate` or `account_type === 'INDUSTRY_AFFILIATE'` | Title rep | `/app/affiliate` |
| `isSponsored` | `is_sponsored` | Trial agent | `/app` |

Two sub-cases the booleans don't carry but pages branch on:
- **Company rep** = `INDUSTRY_AFFILIATE` with a `parent_account_id` (a rep inside a TITLE_COMPANY). Detected per-page (`affiliate/page.tsx`, `settings/branding/page.tsx`). Copy changes ("My agents" vs "Affiliate dashboard", "Remove from book" vs "Remove sponsorship") and branding becomes read-only.
- **Independent affiliate** = `INDUSTRY_AFFILIATE` with no parent. Sets own branding; agents are "trial agents".

`app/app/page.tsx` redirects `/app` → `/app/company` or `/app/affiliate` by tier, so neither ever sees the agent dashboard.

## 2. Title rep (`INDUSTRY_AFFILIATE`) — what's distinct

**Routes (all `/app/affiliate/*`):**
- `/app/affiliate` — `AffiliateDashboardShell` (`components/v0-styling/AffiliateDashboardShell.tsx`, 26 KB) + `AffiliateOnboarding` card above it. Contents: PageHeader with Bulk-invite + Invite-agent buttons; a 3-tile metrics card (Agents · Reports · Active 30d) + "N agents at limit" amber alert; a "Your reports" usage card (the rep's own plan usage); the sponsored-agents table (Agent · Plan · Reports · Status · Last invited · Last activity · Created · ⋯). Row actions: resend invite / cancel invitation (pending), view reports & schedules / deactivate (active), reactivate / remove sponsorship (deactivated). Two confirm dialogs.
- `/app/affiliate/agents/[agentId]` — per-agent detail: usage header + Tabs (Reports | Schedules), lazy-loaded.
- `/app/affiliate/accounts/[accountId]` — `SponsoredAccountDetailPage` (older detail view; likely superseded by agents/[agentId]).
- `/app/affiliate/reports`, `/schedules`, `/property-reports` — cross-agent lists ("all-reports", "all-schedules" endpoints).
- `/app/affiliate/branding` → redirects to `/app/branding` → redirects to `/app/settings/branding`.

**Shared surfaces that change for them:**
- `/app/people` — Contacts merges `sponsored_accounts` in as `kind: "sponsored_agent"` rows with a "Trial Agents" filter, an "Edit sponsored agent" dialog (phone, notes, sponsorship toggle → unsponsor), and group membership for agents.
- `/app/settings/branding` — company reps get a read-only "inherited from {company}" view; independent affiliates edit normally. Their branding flows to every sponsored agent's reports (the onboarding tip says so in words; the mechanism is server-side).
- `/app/settings/billing` — an `INDUSTRY_AFFILIATE` block at line ~381.
- Rail (`app-layout.tsx`, already in our drop-in): "My book" group (My agents · Agent reports · Agent schedules), then "My work" (their own reports + Contacts), then Account. A "My agents" 3-row stat block replaces the usage bars at the bottom.
- Onboarding: `components/onboarding/affiliate-onboarding.tsx` — its own step list (profile → branding → first agent invited → …), with "Pro tip" callouts.

**Modals/components only they use:** `components/invite-agent-modal.tsx` (single invite, `isCompanyRep` copy switch), `components/affiliate/bulk-invite-modal.tsx` (CSV, `public/sample-agent-invite.csv`).

## 3. Title company admin (`TITLE_COMPANY`) — what's distinct

**Routes (all `/app/company/*`):**
- `/app/company` — company dashboard (`app/app/company/page.tsx`, 23 KB, no shell component). Company header (initials tile + plan badge + "Edit branding"); 3 usage bars; 4 metric cards (Title reps · Total agents · Reports this month · Active agents 30d, each with a delta); "agents at limit" alert; Title reps table (Rep · Office/area · Agents · Reports 30d · Last active · Status · ⋯ with View agents / Resend invite / Deactivate); Recent activity feed + Quick actions card (Invite rep · Edit branding · View all agents · Download activity report).
- `/app/company/reps` (25 KB) — rep management + invite-rep.
- `/app/company/agents` (18 KB) — all agents across reps, `?rep=` filter.
- `/app/company/reports`, `/app/company/schedules` — cross-company lists.
- `/app/company/branding` (33 KB) — the company brand that flows down to reps (read-only for them) and onto their agents' reports.

No "New report" button in the rail for this tier (they don't make reports). Rail: Company group (Dashboard · Title reps · All agents · All reports · All schedules) + Account (Branding · Plan & billing · Settings).

## 4. Sponsored / trial agent (`is_sponsored`) — what's distinct

Minor. Same agent app with: Branding hidden from the rail (sponsor's brand wins), "Trial agent" role label, a "Trial" badge on Plan & billing when `plan_slug === 'sponsored_free'` AND `sponsor_account_id` set, an info note on `/app/settings/branding`. Can self-upgrade.

## 5. The hierarchy, in one line

Platform → **Title company** (brand, plan, seats) → **Title reps** (each a "book" of agents; inherit company brand) → **Sponsored agents** (`sponsored_free`, carry the sponsor's logo next to theirs). An independent **affiliate** is a rep without a company above it.

## 6. What Design's packages cover

| Surface | Covered? |
|---|---|
| Agent app (Dashboard, Reports, Schedules, Property, Home-value, Contacts, Billing, Settings, Help) | Yes — App v3 |
| Admin (platform) | Yes — App v3, one page + link list |
| Rail variants for admin / company / affiliate | **Nav only** — our `app-layout.tsx` drop-in derives them from the existing route table; Design never drew these rails |
| `/app/affiliate` dashboard + agent table | **No** |
| `/app/affiliate/agents/[id]` detail | **No** |
| `/app/affiliate/reports`, `/schedules`, `/property-reports` | **No** (the agent Reports/Schedules list vocabulary would transfer, with an added "Agent" column) |
| Contacts with sponsored-agent rows + "Trial agents" filter | **No** — App v3 Contacts is agent-only |
| `/app/company` dashboard | **No** |
| `/app/company/reps`, `/agents`, `/reports`, `/schedules` | **No** |
| `/app/company/branding` + read-only inherited branding for reps | **No** — App v3 Branding is the agent form only |
| Affiliate onboarding (`affiliate-onboarding.tsx`) | **No** — Wizards v3 onboarding is agent onboarding |
| Invite agent / bulk invite modals | **No** |
| Sponsor's logo "next to theirs" on reports | **Partly** — Landing v4 sponsor band promises it; PDF Reports v2 / Property Report packages show one agent brand, no sponsor co-brand slot |
| Sponsored-agent app differences (Trial badge, hidden Branding, branding note) | Implicit — rail drop-in hides Branding; nothing drawn |

Net: every drop-in is the agent view. The sponsor side is ~12 routes, two dashboards, two tables with row-action menus, one branding-inheritance state, one onboarding, two invite modals, and one co-brand slot on the report itself.

## 6b. Findings from the API + worker (2026-10-23) and the product calls made on them

**The co-brand is not implemented.** `apps/api/src/api/services/branding.py` and `apps/worker/src/worker/tasks.py::_resolve_email_brand` both state: *REGULAR accounts (sponsored or not) → their OWN branding. No sponsor/affiliate fallback.* Migration `0008` originally specified sponsored agents → sponsor's brand; that rule was later removed. The landing page's "Your logo goes next to theirs" and `_intake`'s "Co-branded PDFs" describe behaviour the render path does not have.
→ **Call: agent-only is intended.** The sponsor's value is the free seat and the relationship. No co-brand slot on agent reports; the landing-page line needs rewording.

**Rep branding was contradictory** — company page: "reps can override"; rep page: "managed by your company"; worker honours `affiliate_branding.branding_override`.
→ **Call: company sets logo, colours, name. Rep contributes photo + two contact lines only.** `branding_override` should be dropped or ignored.

**Where the company brand actually appears:** on reports the rep runs themselves (and the rep's emails). Not on agents' reports. Reps run reports occasionally, so this matters less than it looked.

**Other calls:** invite by email only (API currently requires `name` — change `/v1/affiliate/invite-agent`); hitting the 10-report trial limit needs no rep action (the limit is the point); independent affiliates exist only as demo accounts, so the rep view can assume a parent company; desktop only.

**Company admin's three questions:** are my reps using it, are agents sending reports, invite a rep. Nothing else on the dashboard.

Design: `Sponsor v3.dc.html` (rep: My agents / Agent / Reports / Branding; company: Reps & agents / Branding).

## 7. Suggested shape of the ask to Design

Name these, in priority order:
1. `/app/affiliate` — the rep's "My agents" page (table + invite). Highest traffic on the sponsor side.
2. `/app/company` — the company dashboard, and whether it's a separate layout or the same PageHeader + RuleList vocabulary with a reps table.
3. Branding inheritance: company → rep (read-only view) → agent reports (co-brand slot). This touches the PDF package too.
4. Contacts when sponsored agents are mixed in — a filter pill, or a separate "Agents" page?
5. `/app/affiliate/agents/[id]` — tabs or two rule-topped lists?
6. Affiliate onboarding steps vs the agent onboarding flow.

Things to tell Design so they don't re-derive them: the tier booleans and the company-rep sub-case above; the full row-action menus (section 2); that the company tier has no "New report"; that the rail drop-in already handles nav for all four tiers.

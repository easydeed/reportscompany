# Design handoff — Sponsor views (title company + title rep)

Repo: `easydeed/reportscompany` · Prepared 2026-10-23 · Surfaces: `/app/company/*` and `/app/affiliate/*` · Grounded in `AFFILIATE_INVENTORY.md` (code read 2026-10-23) and the API routes in `apps/api/src/api/routes/{company,affiliates}.py`.

Companion to `design_handoff_product/` — same shell, same tokens, same list vocabulary (`components/ui/list.tsx`, `page-header.tsx`). Read that package's `README.md` §Shared system first; nothing here redefines it.

## What's in the folder

| file | what |
|---|---|
| `Sponsor v4.dc.html` | the design. Rail toggle (top-right pill) flips rep ↔ company. Tweaks: `tier` (rep · company), `leads` (on/off — see Decisions) |
| `Report Page.dc.html`, `support.js`, `indigo.png` | dependencies; open the design with these beside it |
| `AFFILIATE_INVENTORY.md` | the code inventory the design was corrected against |
| `DECISIONS.md` | the five calls for Jerry, with the recommendation on each |
| `code/apps/web/…` | TSX drop-ins on repo paths (table below) |

## The surface in one paragraph

Two tiers on the App v3 shell. **Company** (`/app/company`): Dashboard · Reps & agents · Branding · Plan · Settings — sets the brand, owns the rep seats, watches whether the network is working. **Rep** (`/app/affiliate`): My agents · Reports · Schedules · Settings — manages one book of agents, sees activity never content, touches no billing or branding. Neither tier has "New report" in the rail. Every list is the App v3 rule-list; every status is a sentence with a dot, not a badge; every destructive action states its consequence before it runs.

## Rail (patch to `app-layout.tsx`)

The App v3 `app-layout.tsx` drop-in already derives nav per tier; change only the two sponsor branches of `getNavGroups` and let a group omit its label:

```ts
if (isCompanyAdmin) return [{ label: "", items: [
  { name: "Dashboard",     href: "/app/company",          icon: LayoutDashboard, exact: true },
  { name: "Reps & agents", href: "/app/company/reps",     icon: Users },
  { name: "Branding",      href: "/app/company/branding", icon: Palette },
  { name: "Plan",          href: "/app/settings/billing", icon: CreditCard },
  { name: "Settings",      href: "/app/settings/profile", icon: Settings },
] }]
if (isAffiliate) return [{ label: "", items: [
  { name: "My agents", href: "/app/affiliate",           icon: Users,    exact: false },  // owns /app/affiliate/agents/*
  { name: "Reports",   href: "/app/affiliate/reports",   icon: FileText },
  { name: "Schedules", href: "/app/affiliate/schedules", icon: Calendar },
  { name: "Settings",  href: "/app/settings/profile",    icon: Settings },
] }]
```
Render: `{g.label && <span …>{g.label}</span>}`. `isActivePath` needs "My agents" active on `/app/affiliate/agents/*` but not on `/app/affiliate/reports|schedules` — exact-match the three sub-routes first. The `showNewReport` flag already excludes company; add `&& !tier.isAffiliate`. Drop the "My agents" 3-row stat block at the bottom of the rail for affiliates (the numbers moved into the page sentence). Rep's own `/app/reports`, `/app/people`, `/app/settings/branding`, `/app/settings/billing` stay reachable by URL but leave the rail — see Decisions #5.

## Drop-ins

| path | replaces | notes |
|---|---|---|
| `components/sponsor/shared.tsx` | new | `Avatar`, `Sentence`, `SeatBadge`, `RowButton`, `ConsequenceMenu`, `ActivityRow`, `StatCell`, `H2`, `EmailInvite`, `post`, date/label helpers. The sponsor vocabulary on top of `ui/list.tsx`. |
| `app/app/affiliate/page.tsx` | same | My agents. Drops `AffiliateDashboardShell`, `AffiliateOnboarding`, the metrics card, the "Your reports" card, the bulk/invite modals. Merges `sponsored_accounts` + `/v1/contacts` into one book. Row actions wired to the real endpoints (below). |
| `app/app/affiliate/agents/[agentId]/page.tsx` | same | Person. Drops Tabs, usage bars, PDF links, status badges. Reports → activity sentences; schedules → "Going out on its own". |
| `app/app/affiliate/reports/page.tsx` | same | Read-only feed on `/v1/affiliate/all-reports`. Drops metric tiles, search, selects, PDF column, pagination, the CMA pitch card. |
| `app/app/affiliate/schedules/page.tsx` | same | Read-only feed on `/v1/affiliate/all-schedules`, agents' schedules only. |
| `app/app/company/page.tsx` | same | Dashboard on `useCompanyOverview` + `useCompanyBranding`. Drops usage bars, 4 metric cards, quick actions, the reps dropdown menu. Exports `repSentence`. |
| `app/app/company/reps/page.tsx` | same | Reps & agents: expandable rep → agents from `useCompanyAgents`. Drops stat tiles, search/selects, export, pagination, the invite dialog (inline email instead). |

Not included as TSX (spec below, same transformation): company Branding, Plan, Settings; rep Settings; `/app/company/agents` (keep as the "All N agents →" overflow, restyle as a rule-list).

## Pages — what each one is

### Company · Dashboard (`/app/company`)
Header: the brand that flows down — logo tile (or initials on `primary_color`) + company name + "N reps · N agents · N reports this month". Three `StatCell`s: **Reps** (and how many haven't joined), **Agents sending** `x of y` with "n haven't sent anything in a month" in amber, **Reports this month** with the change on last month. Then **Your reps** as sentence rows (`repSentence`), then **This week** — activity as sentences ("Jennifer Martinez sent an Irvine market snapshot · Today"). If leads is yes: a cream-green line above the reps — "Your agents' reports brought in N homeowner leads this month — up from M in September."

### Company · Reps & agents (`/app/company/reps`)
Inline invite (email → ink "Send invite"); one line under it. Rule-list of reps: chevron · avatar · name / "office · n agents" · sentence · action (pending → "Resend invite"). Open → agent rows indented under a 2px rule: avatar · name / email · status word (Active green · Invited grey · Lapsed amber) · "Last sent Monday". More than 6 → "All 19 of Ben's agents →" to `/app/company/agents?rep=`.

### Company · Branding (`/app/company/branding`, 33 KB today)
Rule-list of three rows: Logo (chip) · Replace; Colour (swatch + hex) · Change; Name · Edit. Right column, sticky: `<ReportThumb width={300}>` of a rep's report cover carrying the company brand — "Live · a rep's report cover" label above, "Download a sample PDF" under. Below the form, **What each rep adds**: a card with the rep photo + "Name · Title Rep" + two contact lines, then the sentence: *"Photo and contact line only. Your colour is never changed to fix contrast — if text wouldn't read on it, the report picks a readable ink on its own."* Keep the `PATCH /v1/company/branding` cascade; stop sending `rep_photo_url`/`contact_line*` from this page (those are the rep's). Drop the email-logo / footer-logo / website fields from the first screen — four logo slots is a builder concern; one logo, derived variants.

### Company · Plan (`/app/settings/billing`, company tier)
Title "Plan" · "N rep seats, M in use. You pay for seats; agents pay for themselves." **Rep seats**: one row per seat — "Seat 1" · avatar + rep name / "office · n agents"; an empty seat reads "Open" with "Invite a rep". "Add seats" link right of the heading. **Agents** paragraph: agents don't take seats, trial seat = 10 reports a month, agents who want more upgrade and pay themselves, "Right now N agents are on trial seats and M have upgraded." Then Billing row + Card row. **Blocked on Decisions #1** — there is no seat count in the API.

### Company · Settings (`/app/settings/profile`, company tier)
App v3 settings treatment: Company / Address / Website rows · **Admins** list (Owner marker, Remove on others, "Add an admin") · **Email me** toggles (rep joins or leaves · a rep's agents go quiet · monthly summary) · Sign out. No admin-management endpoint exists today — draw it, wire later.

### Rep · My agents (`/app/affiliate`)
Title + sentence: "13 people in your book. 7 have a seat; 5 sent something this month." Inline invite (email → "Invite") with one line: "A seat is the agent's own account with 10 reports a month, paid by {company}. Whole office? Paste a list." Filter pills: Everyone · **Trial agents** · No seat yet · Gone quiet · Waiting. Rows: avatar · name (+ seat badge) / brokerage or email · sentence · primary action + ⋯. Sentences: "Offered a seat Monday" · "Offered a seat 2 weeks ago, hasn't taken it" (amber) · "Has a seat · 7 reports this month" · "Has a seat · used all 10 this month" · "Has a seat · nothing sent in 5 weeks" (amber) · "Seat paused since September" (grey) · contacts: "In your book · gets what you send".

Row actions — exactly the five in code, each with what it does on the server:

| status | primary | ⋯ item | server | consequence copy |
|---|---|---|---|---|
| pending | Resend invite | **Cancel the offer** | `POST …/accounts/{id}/deactivate` (`is_active=FALSE`) | "The invite link stops working. They stay in your book and keep getting your reports." |
| active / limit / quiet | Check in (quiet only, `mailto:`) | **Pause their seat** | `…/deactivate` | "They're locked out of their account until you turn it back on. Nothing is deleted." |
| deactivated | Turn back on → `…/reactivate` | **Take the seat back** | `…/unsponsor` (`sponsor_account_id=NULL`, `sponsored_free→free`) | "They keep their account and reports, on the Free plan (3 a month), on their own. You can't undo this from here." |
| contact | Give a seat → `POST /v1/affiliate/invite-agent` | — | | |

These replaced the v3 guesses ("they keep their account but can't send") after reading the routes: deactivate is a lockout, not a send-block; unsponsor has no reverse endpoint.

### Rep · Person (`/app/affiliate/agents/[id]`)
Back link · avatar · name / email · "Email Tom" + status-specific action + ⋯ (same menu). Cream status sentence at 17px. Three `StatCell`s (not for pending): Sent this month `7` "of 10 on the seat" · Last sent `Monday` · Seat `Paid` "by Pacific Coast Title". **What Tom has been doing**: activity rows from `/agents/{id}/reports` — "Sent an Irvine market snapshot" / "Their schedule sent a Tustin closed sales" · when; "Took the seat" at the bottom. Footnote: "You see that reports went out. The reports themselves belong to Tom." **Going out on its own** (if any schedules): area · type / cadence · to n people · Next Nov 1 / Paused.

### Rep · Reports (`/app/affiliate/reports`)
Pills My agents' · Mine · Everything (from `source`). Rows: avatar + name (links to the person) · "Irvine · market snapshot" · when. Footnote as above. If leads is yes, a second line under the report in green: "1 homeowner lead".

### Rep · Schedules (`/app/affiliate/schedules`)
Rows: avatar + name · "Costa Mesa · new listings" / "Every other week" · Next Oct 31 / Paused (amber). No toggles, no New schedule. Footnote: "These are the agents' schedules — you can see them, not change them."

### Rep · Settings (`/app/settings/profile`, affiliate tier)
Photo / Name / Phone / Email / Password rows (editable) · **Your brand**: Logo and Colour rows marked "Set by the company", with "Reports you run carry {company}'s logo and colour with your photo and contact line. For changes, ask {admin}." · **Email me** toggles (an agent takes a seat · goes quiet for a month · [brings in a lead] · weekly digest) · Sign out. No billing, no plan. The two contact lines + photo post to `POST /v1/affiliate/branding` with the company's fields echoed back unchanged; `branding_override` should stop being set (inventory §6b).

## What the API doesn't return (and the design assumes)

1. **Open counts.** No endpoint on either tier returns opens per report; `report_generations` has none. The v3 "6 of 10 opened" rows are gone from v4 on the rep feed; "whether it landed" is wording only until there's a number. If opens exist in the email layer, add `opened_count` / `recipient_count` to `all-reports` and `/agents/{id}/reports` and the rows take them without layout change.
2. **Leads.** Captured by agents' reports, stored, not exposed above the agent. Two reads needed if Decisions #2 is yes: a company count (`/v1/company/overview` → `metrics.leads_this_month`, `leads_last_month`) and a rep feed (`/v1/affiliate/all-reports` rows → `lead_count`; `/agents/{id}/reports` → same). No lead contact details on the rep side.
3. **Seats.** No concept in the API. Reps are counted, not seated. See Decisions #1.
4. **Contacts have no send history.** `/v1/contacts` carries no last-sent / opened per contact, so contact rows in the book read "In your book · gets what you send" rather than "Got your Newport snapshot Monday · opened it" (v4 design shows the intended form).
5. **`rep.office` is always `""`**; the design falls back to email. `/v1/company/agents` keys agents by `rep_name`, not `rep_id` — the expandable view joins on name; add `rep_id`.
6. **Email-only invite.** `/v1/affiliate/invite-agent` requires `name`; `/v1/company/invite-rep` requires `name`, `first_name`, `last_name`. Both drop-ins derive a display name from the address until the API relaxes.
7. **Company rep actions.** The current reps-table menu offers Deactivate / Remove for reps with no handler and no endpoint. Not drawn. "Reassign agents" (a rep leaves, agents need a new rep) is in the design as an intent; there's no endpoint.

## Decisions already made (do not reopen without the owner)
- No co-brand on agents' reports; the sponsor's value is the seat and the relationship (inventory §6b).
- Company sets logo, colour, name. Rep contributes photo and two contact lines only, read-only otherwise.
- Rep rail is four items; company rail is five; neither has New report.
- The rep sees activity, never content: no PDF links, no report thumbnails, no report browser on the rep side.
- Reps do not author schedules. Rep broadcasting is net-new product, out of this build.
- Status is a sentence with a dot, never a tinted chip. Destructive items are red and say their consequence.

## Change log
- 2026-10-23 · v4: company Dashboard / Plan / Settings added; Reps & agents made expandable; Branding preview is the live cover; rep Reports and Schedules made read-only (thumbnails, Run a report, New schedule removed); row ⋯ menus with consequence copy; leads behind a tweak. Consequence copy corrected to server behaviour after reading the routes.
- 2026-10-23 · v3: product calls applied (no co-brand, company owns brand, email-only invite, one book).

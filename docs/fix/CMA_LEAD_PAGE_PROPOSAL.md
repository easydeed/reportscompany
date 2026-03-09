# Agent Lead Page — Self-Serve CMA Funnel Redesign

> One URL per agent. Branded. Self-serve. Lead captured at the moment of highest intent.

---

## The Concept

Every agent gets a permanent, branded URL:

```
trendyreports.io/cma/{agent_code}
```

A homeowner lands on this page — from a business card, yard sign, email signature, social media bio, QR code on a flyer — and walks through a guided flow:

1. **See the agent's brand** (establishes trust)
2. **Enter their address** (they're curious about their home's value)
3. **See property details confirmed** (builds confidence in the data)
4. **Enter phone or email to receive the report** (lead captured at peak intent)
5. **Report generated and delivered via SMS** (instant gratification)
6. **Agent notified immediately** (lead is hot)

The homeowner never creates an account. Never logs in. Never sees our platform name prominently. This is the **agent's page** with the agent's branding.

---

## Why Capture Contact at Step 4, Not Step 1

The old system asked for a phone number before showing anything. That's a gate that kills conversion. Modern users bounce when they hit a form before seeing value.

The new flow gives them value first:
- Step 1: They see a polished, professional page (free)
- Step 2: They search their address (free, interactive)
- Step 3: They see their property details (free, personalized)
- Step 4: They're invested. They WANT the report. NOW you ask for contact info.

By Step 4, they've spent 60-90 seconds engaging with the page. The report is the payoff. Giving their phone number or email to receive it feels like a fair exchange, not a gate.

---

## The Flow (Detailed)

### URL Structure

```
trendyreports.io/cma/{agent_code}
```

The `agent_code` is a short, memorable code the agent chooses or is auto-generated:
- `SARAH2025`
- `JCHEN`
- `ACMEREALTY`

It maps to the agent's account. The backend looks up `accounts.agent_code` → loads branding, agent info, logos, colors.

---

### Step 1: Agent Brand + Welcome

The homeowner lands and immediately sees a **branded, trustworthy page**.

```
┌─────────────────────────────────────────────┐
│                                             │
│  ┌─────────────────────────────────────┐    │
│  │  ██████ GRADIENT HEADER ██████████  │    │
│  │                                     │    │
│  │        [Agent Logo]                 │    │
│  │                                     │    │
│  │    What's Your Home Worth?          │    │
│  │                                     │    │
│  │    Get a free, professional         │    │
│  │    property report in seconds.      │    │
│  │                                     │    │
│  └─────────────────────────────────────┘    │
│                                             │
│  ┌───────────────────────────────────────┐  │
│  │                                       │  │
│  │  [Agent Photo]  Sarah Chen            │  │
│  │                 Senior Realtor         │  │
│  │                 Acme Realty            │  │
│  │                 DRE #01234567         │  │
│  │                                       │  │
│  └───────────────────────────────────────┘  │
│                                             │
│  ┌───────────────────────────────────────┐  │
│  │  🔍 Enter your property address...    │  │
│  └───────────────────────────────────────┘  │
│                                             │
│  Uses your actual branding colors,          │
│  logo, and agent photo from your account.   │
│                                             │
└─────────────────────────────────────────────┘
```

**Key elements:**
- Header gradient: `primary_color → accent_color` (same as email reports)
- Agent logo centered in header
- Headline: "What's Your Home Worth?" (or customizable)
- Subheadline: "Get a free, professional property report in seconds."
- Agent card: photo, name, title, brokerage, license
- Address search input with Google Places autocomplete
- **No forms, no gates, no phone number required yet**

The agent card builds trust — "this isn't a random website, it's MY agent's page." The address input is the single call-to-action.

---

### Step 2: Address Search + Property Confirmation

After typing and selecting an address from Google Places autocomplete:

```
┌─────────────────────────────────────────────┐
│                                             │
│  ✓ 2847 Waverly Drive                      │
│    Silver Lake, CA 90039                    │
│                                             │
│  ┌───────────────────────────────────────┐  │
│  │                                       │  │
│  │  We found your property:              │  │
│  │                                       │  │
│  │  2847 Waverly Drive                   │  │
│  │  Silver Lake, CA 90039                │  │
│  │                                       │  │
│  │  ┌─────────┬─────────┬──────────┐     │  │
│  │  │  3 Bed  │  2 Bath │ 1,850 SF │     │  │
│  │  └─────────┴─────────┴──────────┘     │  │
│  │                                       │  │
│  │  Year Built: 1928                     │  │
│  │  Lot Size: 5,200 SF                   │  │
│  │  Property Type: Single Family         │  │
│  │  APN: 5432-001-020                    │  │
│  │                                       │  │
│  └───────────────────────────────────────┘  │
│                                             │
│  Is this your property?                     │
│                                             │
│  [ Yes, Get My Report → ]                   │
│                                             │
│  Not your property? [Search again]          │
│                                             │
└─────────────────────────────────────────────┘
```

**What happens behind the scenes:**
1. Google Places returns the structured address
2. Backend calls SiteX/Black Knight API to fetch property details (beds, baths, sqft, year built, lot size, APN, owner name)
3. Property details displayed for confirmation
4. If multiple properties match (condos, multi-unit), show a selection table

**The homeowner sees their own property data.** This is the "wow" moment — it feels personalized and data-rich. They're now invested.

---

### Step 3: Report Preview + Contact Capture

They clicked "Yes, Get My Report." Now we show what they'll receive and ask for delivery info:

```
┌─────────────────────────────────────────────┐
│                                             │
│  Your Report Is Almost Ready                │
│                                             │
│  ┌───────────────────────────────────────┐  │
│  │                                       │  │
│  │  📋 Your report will include:         │  │
│  │                                       │  │
│  │  ✓ Estimated home value               │  │
│  │  ✓ Recent comparable sales            │  │
│  │  ✓ Neighborhood market trends         │  │
│  │  ✓ Professional PDF report            │  │
│  │                                       │  │
│  │  ┌──────────────────────────────────┐ │  │
│  │  │  [Mini preview of PDF cover      │ │  │
│  │  │   page with agent's branding]    │ │  │
│  │  └──────────────────────────────────┘ │  │
│  │                                       │  │
│  └───────────────────────────────────────┘  │
│                                             │
│  Where should we send your report?          │
│                                             │
│  ┌────────────────────────┐                 │
│  │  📱  Send via Text     │  ← default      │
│  │  (recommended — instant │                 │
│  │   delivery)             │                 │
│  └────────────────────────┘                 │
│  ┌────────────────────────┐                 │
│  │  📧  Send via Email    │                 │
│  └────────────────────────┘                 │
│                                             │
│  [Phone/Email input based on selection]     │
│                                             │
│  ┌──────────────────────────────────────┐   │
│  │  (310) 555-____                      │   │
│  └──────────────────────────────────────┘   │
│                                             │
│  □ I agree to receive this report and       │
│    be contacted by Sarah Chen               │
│                                             │
│  [ Generate My Free Report → ]              │
│                                             │
└─────────────────────────────────────────────┘
```

**Key design decisions:**
- **SMS is default and recommended** — highlighted, pre-selected, labeled "instant delivery"
- **Email is the alternative** — available but secondary
- Only ONE field: phone OR email (not both — reduce friction)
- Consent checkbox (TCPA/GDPR compliance)
- Mini preview of the actual PDF cover page (using their branding) shows the homeowner what they're getting — tangible, professional
- "Generate My Free Report" is the CTA — action-oriented, emphasizes "free"

---

### Step 4: Report Generation + Delivery

After submitting:

```
┌─────────────────────────────────────────────┐
│                                             │
│           Generating Your Report...         │
│                                             │
│  ┌───────────────────────────────────────┐  │
│  │                                       │  │
│  │  ████████████░░░░░░░░  65%            │  │
│  │                                       │  │
│  │  ✓ Property data loaded               │  │
│  │  ✓ Finding comparable sales...        │  │
│  │  ○ Analyzing market trends            │  │
│  │  ○ Building your report               │  │
│  │                                       │  │
│  └───────────────────────────────────────┘  │
│                                             │
│         Takes about 15-30 seconds           │
│                                             │
└─────────────────────────────────────────────┘
```

Then success:

```
┌─────────────────────────────────────────────┐
│                                             │
│           ✓ Your Report Is Ready!           │
│                                             │
│  ┌───────────────────────────────────────┐  │
│  │                                       │  │
│  │  We just sent your report to:         │  │
│  │  📱 (310) 555-1234                    │  │
│  │                                       │  │
│  │  Check your text messages for          │  │
│  │  a link to download your free          │  │
│  │  property report.                      │  │
│  │                                       │  │
│  └───────────────────────────────────────┘  │
│                                             │
│  ┌───────────────────────────────────────┐  │
│  │                                       │  │
│  │  Questions about your home's value?   │  │
│  │                                       │  │
│  │  [Agent Photo]  Sarah Chen            │  │
│  │                 (310) 555-1234        │  │
│  │                 sarah@acme.com        │  │
│  │                                       │  │
│  │  [ Call Sarah ] [ Email Sarah ]       │  │
│  │                                       │  │
│  └───────────────────────────────────────┘  │
│                                             │
└─────────────────────────────────────────────┘
```

**What happens behind the scenes:**
1. Lead created in `leads` table (or `consumer_reports` — see architecture below)
2. Property report generated via Celery worker (same pipeline as property reports)
3. If SMS: Twilio sends text to homeowner with report download link
4. If Email: Resend sends email with report link
5. Agent notified via SMS: "New lead! {name} at {address} just requested a CMA."
6. `sms_credits` decremented
7. Lead appears on agent's dashboard at `/app/leads`

---

## Architecture Decisions

### Unify Lead Storage

Currently leads from `/p/{short_code}` go to `leads` table and leads from `/cma/{agent_code}` go to `consumer_reports` table. This should be unified.

All leads go to the **`leads` table** with a `source` field:

| Source | Meaning |
|---|---|
| `qr_scan` | From property report QR code landing page |
| `direct_link` | From property report direct URL |
| `cma_page` | From agent's self-serve CMA page |
| `widget` | From embeddable widget (future) |
| `manual` | Agent-entered lead |

The `consumer_reports` table stays for tracking the generated report (PDF path, property data), but the lead itself lives in `leads`.

### Agent Code

Store `agent_code` on the `accounts` table:

```sql
ALTER TABLE accounts ADD COLUMN agent_code VARCHAR(20) UNIQUE;
```

Auto-generate on account creation: first name + last initial + year, e.g., `SARAHC2025`. Agent can customize it in settings (with uniqueness validation).

### URL Structure

```
/cma/{agent_code}              → Self-serve CMA funnel
/cma/{agent_code}?address=...  → Pre-filled address (for QR codes on specific properties)
/p/{short_code}                → Property report landing page (keep as-is)
```

The `/cma` route is the agent's permanent lead gen page. The `/p` route stays for property-specific QR codes. They share the same lead table but different flows.

### Report Generation

Use the **existing property report pipeline**:
1. SiteX lookup for property data
2. SimplyRETS for comparable sales
3. Jinja2 templates with agent's selected theme and branding
4. Playwright (local) or PDFShift (production) for PDF rendering
5. Upload PDF to R2
6. Generate short link for SMS delivery

The consumer CMA report is essentially a property report minus the wizard — the system auto-selects comps, auto-generates the executive summary, and uses the agent's default theme.

### Anti-Spam (Same Pipeline)

Reuse the existing anti-spam from the property QR flow:
1. Honeypot field (hidden)
2. Rate limit: 5 submissions per IP per hour
3. Duplicate: same phone/email + same address = silent success (don't re-generate)
4. IP blocklist
5. CAPTCHA (consider adding — high-traffic public page)

---

## What the Agent Controls

In their dashboard settings (or branding page):

| Setting | Default | Where |
|---|---|---|
| Agent code | Auto-generated | Account settings |
| Page headline | "What's Your Home Worth?" | Lead page settings |
| Page subheadline | "Get a free, professional property report in seconds." | Lead page settings |
| Preferred delivery | SMS | Lead page settings |
| Report theme | Account default | From branding |
| Colors/logo/photo | Account branding | From branding |
| SMS credits | Per plan | Billing |
| Active/inactive toggle | Active | Lead page settings |
| Custom thank-you message | Default | Lead page settings |

### Lead Page Settings UI (New Section)

Add a "Lead Page" section to the agent's settings:

```
┌────────────────────────────────────────────┐
│  Lead Capture Page                         │
│                                            │
│  Your URL:                                 │
│  trendyreports.io/cma/SARAHC2025  [Copy]  │
│                                            │
│  QR Code: [Download PNG] [Download SVG]    │
│                                            │
│  ┌──────────────────────────────────────┐  │
│  │ Active  ○─────●                      │  │
│  └──────────────────────────────────────┘  │
│                                            │
│  Headline:                                 │
│  [ What's Your Home Worth?            ]    │
│                                            │
│  Subheadline:                              │
│  [ Get a free property report...      ]    │
│                                            │
│  Agent Code:                               │
│  [ SARAHC2025 ] [Check Availability]       │
│                                            │
│  Preferred Delivery:                       │
│  ( ● ) Text Message  ( ○ ) Email           │
│                                            │
│  [ Save Changes ]                          │
│                                            │
└────────────────────────────────────────────┘
```

---

## Mobile Experience

This page will be accessed primarily on phones (QR scans from yard signs, business cards). The design must be **mobile-first**.

- Full-width, single column
- Large touch targets (48px minimum)
- Phone number input uses `type="tel"` for numeric keyboard
- Address autocomplete works well on mobile (Google Places handles this)
- Progress bar during generation prevents impatient back-button taps
- Success state has large, tappable "Call Agent" / "Email Agent" buttons

---

## SMS Messages

### To the Homeowner (via Twilio)

```
Your property report for 2847 Waverly Dr is ready!

View your free report:
https://trendyreports.io/r/{short_link}

Prepared by Sarah Chen, Acme Realty
(310) 555-1234
```

### To the Agent (via Twilio)

```
🏠 New CMA Lead!

Someone just requested a report for:
2847 Waverly Dr, Silver Lake CA 90039

📱 (310) 555-9876
📧 jane@example.com

Respond quickly — they're actively evaluating!
- TrendyReports
```

---

## Embeddable Widget (Future Phase)

The same flow packaged as an `<iframe>` that agents can embed on their own websites:

```html
<iframe 
  src="https://trendyreports.io/cma/{agent_code}?embed=true" 
  width="100%" 
  height="600"
  frameborder="0">
</iframe>
```

When `?embed=true` is present:
- Remove the outer page chrome (no TrendyReports header/footer)
- Compact layout optimized for iframe dimensions
- Cross-origin message passing for height adjustment
- Same lead pipeline, same branding

This is a powerful upsell feature — agents get a "home value estimator" widget for their website that captures leads automatically.

---

## Implementation Phases

### Phase 1: Core CMA Funnel
1. Create `/cma/[code]/page.tsx` — the 4-step flow
2. Add `agent_code` to accounts table + settings UI
3. Wire address search (Google Places → SiteX property lookup)
4. Wire report generation (reuse property report pipeline)
5. Wire SMS delivery (Twilio, reuse existing)
6. Wire lead capture (write to `leads` table with source `cma_page`)
7. Wire agent SMS notification
8. Mobile-responsive design

### Phase 2: Agent Controls
9. Lead Page settings section in dashboard
10. QR code generation for the CMA URL
11. Custom headline/subheadline
12. Active/inactive toggle
13. Agent code customization with uniqueness check

### Phase 3: Polish
14. Report preview thumbnail on Step 3
15. Email delivery option (Resend)
16. Analytics: views, submissions, conversion rate
17. Lead deduplication (same phone + same address = don't regenerate)

### Phase 4: Widget (Future)
18. Embeddable iframe mode
19. Cross-origin session handling
20. Widget-specific compact layout

---

## File Map

```
NEW FILES:
apps/web/app/cma/[code]/page.tsx              ← Server component: fetch agent data
apps/web/app/cma/[code]/cma-funnel.tsx         ← Client component: 4-step flow
apps/web/app/cma/[code]/property-search.tsx    ← Address search + property confirmation
apps/web/app/cma/[code]/contact-capture.tsx    ← Phone/email input + consent
apps/web/app/cma/[code]/report-progress.tsx    ← Generation progress + success
apps/web/app/app/settings/lead-page/page.tsx   ← Agent lead page settings

MODIFIED FILES:
apps/api/src/api/routes/leads.py               ← Add CMA lead capture endpoint
apps/api/src/api/routes/account.py             ← Add agent_code field
apps/worker/src/worker/tasks.py                ← Add consumer CMA report task
DB migration                                    ← accounts.agent_code column
```

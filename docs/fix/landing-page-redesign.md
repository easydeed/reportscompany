# TrendyReports Landing Page Redesign

## Context

The current landing page at `www.trendyreports.io` needs a redesign. The product is a real estate market report SaaS — agents and brokerages use it to generate branded market reports and deliver them to clients via email and PDF.

**Vibe:** Clean and approachable — think Mailchimp, Canva, Notion marketing pages. Friendly, confident, not corporate. Light backgrounds, generous whitespace, clear hierarchy, subtle animations on scroll.

## What to KEEP (Do Not Remove)

These two sections are the strongest parts of the current page. Keep their content, images, and carousel functionality intact. You may restyle them to match the new design language, but preserve the structure and all image assets:

1. **"Email reports clients actually open"** section — the email report carousel with 4 screenshots
2. **"Print-ready PDFs that look expensive"** section — the PDF report carousel with 4 screenshots

## What to REMOVE Entirely

- **Fake testimonials** — Jessica Martinez, Robert Chen, Sarah Patel. All fabricated. Delete the entire testimonials section.
- **"Enterprise-grade security" section** — SOC 2 badge, 99.9% uptime SLA, 256-bit encryption claims are not verified. Remove completely.
- **Fake address/phone in footer** — "123 Market Street, San Francisco" and "(415) 555-1234" are placeholder. Remove.
- **Brokerage logo ticker** — "Keller Williams, RE/MAX, Coldwell Banker..." Remove unless these are confirmed partnerships. Replace with a subtle note like "Used by agents across the country" without specific brand names.
- **Fake stat counters** — "1,200+ agents", "50K+ reports" — remove unless these numbers are verified.

---

## New Page Structure

### 1. Navigation Bar

Minimal, sticky on scroll with backdrop blur.

```
[Logo]                                    [Pricing] [Login] [Start Free →]
```

- Kill the Product/Solutions/Company dropdowns — this is a single-page site
- "Start Free" is primary CTA (pill-shaped button, warm color)
- "Login" is a text link
- Mobile: hamburger menu
- On scroll: `backdrop-blur-md bg-white/80 border-b`

### 2. Hero Section

**Kill the generic SaaS hero.** Lead with the OUTCOME agents care about.

**Layout:** Text-centered or text-left with product visual.

**Headline direction (pick the best or riff):**
- "Market reports your clients actually want to read"
- "Look like a top producer. Every single week."
- "Your brand. Your market. Delivered automatically."

**Subhead:** One human sentence.
- "Create beautiful, branded market reports from live MLS data. Schedule them once — they deliver themselves."

**CTA:**
- Primary: "Try it free" (pill button, friendly, low pressure)
- Secondary: "See sample reports →" (text link, scrolls to email/PDF sections)

**Social proof line (subtle, below CTA):**
- "Free for 14 days · No credit card · Takes 2 minutes"

**Visual:** Show an ACTUAL email report or PDF at a slight angle with a soft shadow. The product is the hero visual — not a generic dashboard screenshot.

### 3. "How It Works" — Three Visual Cards

Replace the current numbered-circles-with-bullet-lists approach with three clean cards.

```
┌──────────────────┐  ┌──────────────────┐  ┌──────────────────┐
│  📍               │  │  🎨               │  │  📬               │
│  Pick your market │  │  Add your brand   │  │  Hit send         │
│                   │  │                   │  │                   │
│  Choose ZIP codes │  │  Upload your logo │  │  Reports deliver  │
│  or cities. 8     │  │  and colors.      │  │  on your schedule.│
│  report types.    │  │  Every report     │  │  Weekly, monthly, │
│                   │  │  looks like yours.│  │  or one-time.     │
└──────────────────┘  └──────────────────┘  └──────────────────┘
```

- Use Lucide icons (MapPin, Palette, Send) — consistent style
- One short description per card, no bullets
- Subtle cards: rounded-2xl, light border, soft shadow on hover

### 4. Email Reports Section (KEEP — restyle wrapper only)

Keep the existing carousel, images, and feature callouts. Restyle the section background, heading typography, and badge styling to match the new design language.

### 5. PDF Reports Section (KEEP — restyle wrapper only)

Same as above — keep everything, restyle to match.

### 6. Report Types Grid (NEW)

Show the breadth — 8 report types is a real differentiator.

Section heading: **"8 report types. One click each."**

Layout: 4×2 grid (desktop), 2×4 (mobile). Clean cards with icon + title + one-line description.

| Icon | Title | Description |
|------|-------|-------------|
| BarChart3 | Market Snapshot | Full market overview with stats and trends |
| Home | New Listings | Fresh listings for any area |
| TrendingUp | Inventory Report | Supply and demand analysis |
| DollarSign | Closed Sales | Recent sales and price trends |
| Layers | Price Bands | Market segmented by price range |
| Image | Listings Gallery | Photo-rich visual grid |
| MapPin | Open Houses | Weekend open house schedule |
| Star | Featured Listings | Showcase your best properties |

Style: Light cards, subtle borders, small Lucide icons. Informational — no CTAs per card.

### 7. For Agents / For Affiliates (Two Cards)

Two cards side by side. Clean and direct.

**For Agents:**
"Impress clients with branded market reports on autopilot. Generate from live MLS data, customize with your branding, and deliver by email on a schedule."
→ [Start free trial]

**For Title & Lending Teams:**
"Sponsor agents, strengthen relationships, and track engagement — all under one plan with co-branded reports."
→ [Talk to us] (mailto:sales@trendyreports.com)

Keep it to a short paragraph each. No bullet lists.

### 8. Pricing Section

Keep the 3-tier structure, make it cleaner.

**Starter ($0/mo)** — "Get started for free"
- 50 reports/month
- Core report types
- Email & PDF delivery
- Basic branding

**Pro ($29/mo)** — "For individual agents" — MOST POPULAR
- 300 reports/month
- All 8 report types
- Automated scheduling
- Full white-label branding

**Team ($99/mo)** — "For teams & affiliates"
- Unlimited reports
- Sponsor agents
- Admin dashboard
- Dedicated support

Style: Rounded-2xl cards, soft shadows, indigo highlight border on "Most Popular" card. Pill-shaped CTA buttons. Bottom note: "All plans include 14-day free trial · No credit card required"

### 9. Final CTA

Simple and warm. Centered.

**"Ready to try it?"**
"Set up takes 2 minutes. Your first report is free."
[Start free trial]   [See sample reports]

Subtle gradient or tinted background. Inviting, not aggressive.

### 10. Footer (Honest)

```
[Logo]
Turn MLS data into beautiful market reports.

Product           Support            Legal
For Agents        Help Center        Privacy Policy  
For Affiliates    Contact Us         Terms of Service
Pricing           

© 2025 TrendyReports. All rights reserved.
```

- NO fake address or phone
- NO social media links unless they're active real accounts
- NO links to pages that don't exist (Blog, Careers, Press, API Docs, Status — remove if these are dead links)
- Keep only: real email (hello@trendyreports.com or support@trendyreports.com)

---

## Design Language

### Color Palette

```css
/* Primary — friendly, trustworthy */
--primary: #6366F1;         /* Indigo-500 */
--primary-hover: #4F46E5;   /* Indigo-600 */
--primary-light: #EEF2FF;   /* Indigo-50: section backgrounds */

/* Accent — warm highlight */
--accent: #F59E0B;          /* Amber-500: badges, highlights only */

/* Neutrals — warm, not cold */
--text: #1E293B;            /* Slate-800 */
--text-muted: #64748B;      /* Slate-500 */
--bg: #FFFFFF;
--bg-alt: #F8FAFC;          /* Slate-50: alternating sections */
--border: #E2E8F0;          /* Slate-200 */
```

### Typography

Continue with `Plus Jakarta Sans` (already loaded) or switch to `Inter`.
- Hero headline: 48-56px, font-bold, tight tracking (-0.02em)
- Section headlines: 32-40px, font-bold  
- Body: 16-18px, relaxed line-height (1.6-1.7)
- Small/captions: 14px, text-muted

Use **sentence case** for all headings. No ALL CAPS.

### Spacing
- Section padding: `py-20` to `py-24`
- Max width: `max-w-6xl` (1152px)
- Card padding: `p-8`
- Generous gaps between sections — let it breathe

### Buttons
```
Primary:  bg-indigo-500 text-white rounded-full px-6 py-3 hover:bg-indigo-600
Secondary: border border-slate-200 rounded-full px-6 py-3 hover:bg-slate-50
```
Pill-shaped (`rounded-full`) for all CTAs — this is the Mailchimp/Canva friendly pattern.

### Cards
```
bg-white rounded-2xl border border-slate-200/50 p-8 hover:shadow-md transition-shadow
```
Rounded corners, barely-there borders, soft hover shadows.

### Animations (Framer Motion)

Subtle scroll-triggered entrance. Every section fades up on scroll:

```tsx
<motion.div
  initial={{ opacity: 0, y: 16 }}
  whileInView={{ opacity: 1, y: 0 }}
  transition={{ duration: 0.4, ease: 'easeOut' }}
  viewport={{ once: true, margin: '-50px' }}
>
```

- Cards within a section: stagger 50-80ms between each
- NO parallax, NO scroll hijacking, NO heavy effects
- Keep it calm and professional

---

## File Structure

Extract sections into components for clarity:

```
components/marketing/
  marketing-nav.tsx
  hero.tsx
  how-it-works.tsx
  email-reports.tsx      ← existing carousel, restyled
  pdf-reports.tsx        ← existing carousel, restyled
  report-types-grid.tsx  ← new
  audience-cards.tsx     ← agents/affiliates
  pricing.tsx
  final-cta.tsx
  marketing-footer.tsx
```

The page file assembles them in order.

---

## Checklist

- [ ] New nav bar (sticky, blur, minimal, mobile hamburger)
- [ ] New hero (outcome headline, product visual, pill CTA)
- [ ] New "How it works" (3 clean cards with icons)
- [ ] Email reports section restyled (KEEP content + images)
- [ ] PDF reports section restyled (KEEP content + images)
- [ ] Report types grid (8 types, Lucide icons)
- [ ] Agents/Affiliates dual cards
- [ ] Pricing cleaned up (3 tiers, verified info)
- [ ] Final CTA (centered, warm)
- [ ] Honest footer (no fake info, only real links)
- [ ] REMOVED: fake testimonials, fake security badges, fake address, fake stats
- [ ] Scroll animations (subtle Framer Motion fade-up)
- [ ] Fully responsive (desktop → tablet → mobile)
- [ ] Pill-shaped buttons throughout
- [ ] Sentence case headings (not ALL CAPS)

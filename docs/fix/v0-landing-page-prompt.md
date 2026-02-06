Create a complete landing page for TrendyReports, a real estate market report SaaS platform. Agents and brokerages use it to generate branded market reports and deliver them to clients via email and PDF.

## Design Direction

Clean and approachable — like Mailchimp, Canva, or Notion's marketing pages. Friendly, warm, confident but not corporate. Generous whitespace, soft rounded corners (rounded-2xl), pill-shaped CTA buttons (rounded-full), subtle scroll animations. Warm neutral palette with indigo primary (#6366F1) and amber accent (#F59E0B) used sparingly.

Use Plus Jakarta Sans for all typography. Sentence case for all headings — never ALL CAPS.

## Page Sections (in this exact order)

### 1. Sticky Navigation
- Left: Logo text "TrendyReports" in indigo-600 font-bold
- Right: "Pricing" text link, "Log in" text link, "Start free trial" pill button (indigo-500 bg, white text)
- Sticky on scroll with backdrop-blur-md bg-white/80 border-b effect
- Mobile: hamburger menu

### 2. Hero Section
- Centered layout
- Headline: "Market reports your clients actually want to read" (text-5xl font-bold tracking-tight on desktop)
- Subhead: "Create beautiful, branded market reports from live MLS data. Schedule them once — they deliver themselves." (text-lg text-slate-500, max-w-2xl mx-auto)
- Two buttons: "Start free trial" (indigo pill, large) and "See sample reports ↓" (outline pill)
- Below buttons: "Free for 14 days · No credit card · Takes 2 minutes" in text-sm text-slate-400
- Below that: a mockup showing a sample email report at a slight 3D angle with a soft shadow. Use a placeholder card that looks like a real estate email report with a purple gradient header, property stats, and agent info. Make this look like an actual product screenshot — not abstract.

### 3. How It Works — Three Cards
- Section heading: "From MLS to inbox in three clicks" (text-3xl font-bold text-center)
- Three cards in a row (stack on mobile), each with:
  - A Lucide icon in an indigo-50 circle (MapPin, Palette, Send)
  - Title: "Pick your market" / "Add your brand" / "Hit send"
  - One short sentence description
- Cards: bg-white rounded-2xl border border-slate-100 p-8 hover:shadow-md transition-shadow

### 4. Email Reports Showcase
- Section heading: "Email reports clients actually open"
- Subhead: "Mobile-optimized HTML emails with your brand front and center"
- Left side: Two rows of feature badges in pills:
  - "Your logo & colors" / "Mobile-first design" / "Key market metrics" / "Your contact info"
- Right side: A carousel/slideshow of 4 email report mockups. Create realistic-looking email report cards:
  1. Market Snapshot — purple gradient header, stats grid showing median price/inventory/DOM, agent photo footer
  2. New Listings Gallery — purple header, 2x2 grid of property photos with prices
  3. Featured Listings — blue gradient header, featured property cards
  4. Market Analysis — orange gradient header, chart area, trend data
- Each mockup should be a card (rounded-2xl shadow-xl) roughly phone-shaped (tall aspect ratio)
- Auto-rotating carousel with dot indicators and prev/next arrows

### 5. PDF Reports Showcase
- Section heading: "Print-ready PDFs that look expensive"
- Subhead: "8.5×11 formatted for perfect printing and digital sharing"
- Same layout as email section but mirrored (carousel on left, features on right)
- Feature badges: "Professional header" / "Property galleries" / "Charts & visualizations" / "Agent footer"
- 4 PDF mockups as cards (landscape aspect ratio, like a printed page):
  1. Market Snapshot PDF — gradient header with logo, stats section, property grid
  2. New Listings Gallery PDF — header, 3x2 property photo grid with details
  3. Featured Listings PDF — header, 2x2 featured property cards
  4. Price Trends PDF — header, line chart area, comparison table
- Same carousel behavior

### 6. Report Types Grid
- Section heading: "8 report types. One click each." (text-3xl font-bold text-center)
- 4x2 grid (2x4 on mobile) of small cards, each with:
  - Lucide icon (BarChart3, Home, TrendingUp, DollarSign, Layers, Image, MapPin, Star)
  - Title: Market Snapshot / New Listings / Inventory Report / Closed Sales / Price Bands / Listings Gallery / Open Houses / Featured Listings
  - One line description in text-sm text-slate-500
- Cards: bg-white rounded-xl border border-slate-100 p-6 text-center

### 7. Who It's For — Two Cards
- Two cards side by side (stack on mobile)
- Card 1 — "For agents": "Impress clients with branded market reports on autopilot. Generate from live MLS data, customize with your branding, and deliver by email on a schedule." → "Start free trial" button
- Card 2 — "For title & lending teams": "Sponsor agents, strengthen relationships, and track engagement — all under one plan with co-branded reports." → "Talk to us" button (outline style)
- Cards: rounded-2xl, card 1 has bg-indigo-50, card 2 has bg-amber-50

### 8. Pricing Section
- Section heading: "Simple, transparent pricing"
- Subhead: "Choose the plan that fits your business"
- Three pricing cards side by side:
  - **Starter** ($0/month): "Get started for free" — 50 reports/month, Core report types, Email & PDF delivery, Basic branding → "Start free trial" outline button
  - **Pro** ($29/month): "For individual agents" — 300 reports/month, All 8 report types, Automated scheduling, Full white-label branding → "Start free trial" indigo button — has "Most popular" badge (amber-500 bg, small pill above the card)
  - **Team** ($99/month): "For teams & affiliates" — Unlimited reports, Sponsor agents, Admin dashboard, Dedicated support → "Start free trial" outline button
- Cards: rounded-2xl, Pro card has ring-2 ring-indigo-500 to highlight it
- Below all cards: "All plans include 14-day free trial · No credit card required" in text-sm text-slate-400 text-center

### 9. Final CTA
- Subtle indigo-50 background section
- "Ready to try it?" (text-3xl font-bold text-center)
- "Set up takes 2 minutes. Your first report is free." (text-slate-500)
- "Start free trial" large indigo pill button
- "Free for 14 days · No credit card · Cancel anytime" below

### 10. Footer
- bg-slate-900 text-white
- Left: "TrendyReports" logo text + tagline "Turn MLS data into beautiful market reports."
- Three columns: Product (For Agents, For Affiliates, Pricing) / Support (Help Center, Contact Us) / Legal (Privacy Policy, Terms of Service)
- Bottom: "© 2025 TrendyReports. All rights reserved."
- NO fake address, NO fake phone number, NO social media links

## Technical Requirements
- Use React with TypeScript
- Use Tailwind CSS for all styling
- Use Lucide React for icons
- Use Framer Motion for subtle scroll-triggered fade-up animations on each section (opacity 0→1, y 16→0, duration 0.4s, viewport once)
- Carousel sections: auto-rotate every 4 seconds, with manual prev/next and dot indicators
- Fully responsive: desktop → tablet → mobile
- All CTA buttons are pill-shaped (rounded-full)
- Alternating section backgrounds: white → slate-50 → white → slate-50
- No fake data, no placeholder testimonials, no unverified claims

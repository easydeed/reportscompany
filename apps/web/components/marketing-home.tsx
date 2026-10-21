"use client"

/**
 * The landing page — Design's `Landing v4.dc.html`, section for section:
 * hero, the report carousel, autopilot, property reports, lead capture,
 * contacts, pricing, the closing band, the sponsor band.
 *
 * The city box and the "Your colors" swatches are page state, shared through
 * `LandingTheme`, because in the deck they restyle every mock on the page at
 * once rather than only the hero.
 */
import { useState } from "react"
import { SiteNav } from "@/components/site-nav"
import { SiteFooter } from "@/components/site-footer"
import { DEMO_MARKET } from "@/lib/demo-data"
import { LANDING_THEMES, LandingTheme } from "@/components/marketing/landing-primitives"
import { Hero } from "@/components/marketing/hero"
import { ReportKinds } from "@/components/marketing/report-kinds"
import { Autopilot } from "@/components/marketing/autopilot"
import { PropertyReports } from "@/components/marketing/property-reports"
import { LeadCapture } from "@/components/marketing/lead-capture"
import { ContactManagement } from "@/components/marketing/contact-management"
import { Pricing } from "@/components/marketing/pricing"
import { FinalCta } from "@/components/marketing/final-cta"
import { SponsorBand } from "@/components/marketing/sponsor-band"

export function MarketingHome() {
  const [city, setCity] = useState("")
  const [theme, setTheme] = useState(0)
  const [primary, accent] = LANDING_THEMES[theme]
  const area = city.trim() || DEMO_MARKET.city

  return (
    <LandingTheme.Provider value={{ primary, accent, city, area }}>
      <div className="flex min-h-screen flex-col overflow-x-clip bg-[#FAFAF7] text-[#0F172A]">
        <SiteNav />
        <main>
          <Hero onCity={setCity} theme={theme} onTheme={setTheme} />
          <ReportKinds />
          <Autopilot />
          <PropertyReports />
          <LeadCapture />
          <ContactManagement />
          <Pricing />
          <FinalCta onCity={setCity} />
          <SponsorBand />
        </main>
        <SiteFooter />
      </div>
    </LandingTheme.Provider>
  )
}

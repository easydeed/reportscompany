"use client"

import { MarketingNav } from "@/components/marketing/marketing-nav"
import { Hero } from "@/components/marketing/hero"
import { HowItWorks } from "@/components/marketing/how-it-works"
import { EmailReports } from "@/components/marketing/email-reports"
import { PdfReports } from "@/components/marketing/pdf-reports"
import { ReportTypesGrid } from "@/components/marketing/report-types-grid"
import { AudienceCards } from "@/components/marketing/audience-cards"
import { Pricing } from "@/components/marketing/pricing"
import { FinalCta } from "@/components/marketing/final-cta"
import { MarketingFooter } from "@/components/marketing/marketing-footer"

export function MarketingHome() {
  return (
    <div className="min-h-screen bg-white">
      <MarketingNav />
      <Hero />
      <HowItWorks />
      <EmailReports />
      <PdfReports />
      <ReportTypesGrid />
      <AudienceCards />
      <Pricing />
      <FinalCta />
      <MarketingFooter />
    </div>
  )
}

"use client"

import { MarketingNav } from "@/components/marketing/marketing-nav"
import { Hero } from "@/components/marketing/hero"
import { HowItWorks } from "@/components/marketing/how-it-works"
import { EmailReports } from "@/components/marketing/email-reports"
import { PdfReports } from "@/components/marketing/pdf-reports"
import { ReportTypes } from "@/components/marketing/report-types"
import { PropertyReports } from "@/components/marketing/property-reports"
import { LeadCapture } from "@/components/marketing/lead-capture"
import { ContactManagement } from "@/components/marketing/contact-management"
import { WhoItsFor } from "@/components/marketing/who-its-for"
import { Pricing } from "@/components/marketing/pricing"
import { FinalCta } from "@/components/marketing/final-cta"
import { MarketingFooter } from "@/components/marketing/marketing-footer"

export function MarketingHome() {
  return (
    <>
      <MarketingNav />
      <main>
        <Hero />
        <HowItWorks />
        <EmailReports />
        <PdfReports />
        <ReportTypes />
        <PropertyReports />
        <LeadCapture />
        <ContactManagement />
        <WhoItsFor />
        <Pricing />
        <FinalCta />
      </main>
      <MarketingFooter />
    </>
  )
}

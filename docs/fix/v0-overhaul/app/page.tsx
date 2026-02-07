import { Navbar } from "@/components/navbar";
import { Hero } from "@/components/hero";
import { HowItWorks } from "@/components/how-it-works";
import { EmailReports } from "@/components/email-reports";
import { PdfReports } from "@/components/pdf-reports";
import { ReportTypes } from "@/components/report-types";
import { PropertyReports } from "@/components/property-reports";
import { LeadCapture } from "@/components/lead-capture";
import { ContactManagement } from "@/components/contact-management";
import { WhoItsFor } from "@/components/who-its-for";
import { Pricing } from "@/components/pricing";
import { FinalCTA } from "@/components/final-cta";
import { Footer } from "@/components/footer";

export default function Page() {
  return (
    <>
      <Navbar />
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
        <FinalCTA />
      </main>
      <Footer />
    </>
  );
}

import { Navbar } from "@/components/navbar"
import { Footer } from "@/components/footer"

export const metadata = {
  title: "Terms of Service | TrendyReports",
  description: "TrendyReports Terms of Service - The agreement governing your use of our platform.",
}

export default function TermsPage() {
  return (
    <div className="min-h-screen bg-white">
      <Navbar />

      <section className="pt-32 pb-16 px-4 sm:px-6 lg:px-8">
        <div className="max-w-[800px] mx-auto">
          <h1 className="font-display font-semibold text-4xl text-slate-900 mb-4">Terms of Service</h1>
          <p className="text-slate-600 mb-8">Last updated: December 1, 2025</p>

          <div className="prose prose-slate max-w-none">
            <p className="lead text-lg text-slate-600 mb-8">
              Welcome to TrendyReports. By using our service, you agree to these terms. Please read them
              carefully.
            </p>

            <h2 className="font-display font-semibold text-2xl text-slate-900 mt-12 mb-4">
              1. Acceptance of Terms
            </h2>
            <p className="text-slate-600 mb-6">
              By accessing or using TrendyReports ("Service"), you agree to be bound by these Terms of
              Service ("Terms") and our Privacy Policy. If you do not agree to these Terms, you may not
              use the Service. These Terms apply to all users, including individual real estate agents,
              title companies (affiliates), and their employees.
            </p>

            <h2 className="font-display font-semibold text-2xl text-slate-900 mt-12 mb-4">
              2. Description of Service
            </h2>
            <p className="text-slate-600 mb-6">
              TrendyReports provides a platform for generating automated real estate market reports using
              MLS data. The Service includes report generation, scheduling, email delivery, and white-label
              branding capabilities. We reserve the right to modify, suspend, or discontinue any aspect of
              the Service at any time.
            </p>

            <h2 className="font-display font-semibold text-2xl text-slate-900 mt-12 mb-4">
              3. Account Registration
            </h2>
            <p className="text-slate-600 mb-4">To use the Service, you must:</p>
            <ul className="list-disc pl-6 text-slate-600 space-y-2 mb-6">
              <li>Be at least 18 years old</li>
              <li>Provide accurate and complete registration information</li>
              <li>Maintain the security of your account credentials</li>
              <li>Notify us immediately of any unauthorized account access</li>
              <li>Be responsible for all activities under your account</li>
            </ul>
            <p className="text-slate-600 mb-6">
              We reserve the right to suspend or terminate accounts that violate these Terms or engage in
              fraudulent activity.
            </p>

            <h2 className="font-display font-semibold text-2xl text-slate-900 mt-12 mb-4">
              4. Subscription and Payment
            </h2>
            <h3 className="font-display font-semibold text-xl text-slate-900 mt-8 mb-3">Billing</h3>
            <p className="text-slate-600 mb-4">
              Paid subscriptions are billed in advance on a monthly or annual basis. By subscribing, you
              authorize us to charge your payment method for the applicable fees. All fees are
              non-refundable except as expressly stated in these Terms.
            </p>

            <h3 className="font-display font-semibold text-xl text-slate-900 mt-8 mb-3">Free Trial</h3>
            <p className="text-slate-600 mb-4">
              We offer a 14-day free trial for new users. No credit card is required during the trial
              period. At the end of the trial, you must subscribe to continue using the Service.
            </p>

            <h3 className="font-display font-semibold text-xl text-slate-900 mt-8 mb-3">Cancellation</h3>
            <p className="text-slate-600 mb-6">
              You may cancel your subscription at any time through your account settings. Cancellation
              takes effect at the end of the current billing period. You will continue to have access to
              the Service until then.
            </p>

            <h2 className="font-display font-semibold text-2xl text-slate-900 mt-12 mb-4">
              5. Acceptable Use
            </h2>
            <p className="text-slate-600 mb-4">You agree not to:</p>
            <ul className="list-disc pl-6 text-slate-600 space-y-2 mb-6">
              <li>Use the Service for any unlawful purpose</li>
              <li>Violate any applicable laws or regulations</li>
              <li>Infringe upon intellectual property rights of others</li>
              <li>Transmit malware, viruses, or harmful code</li>
              <li>Attempt to gain unauthorized access to the Service</li>
              <li>Interfere with the proper functioning of the Service</li>
              <li>Scrape, harvest, or collect data without authorization</li>
              <li>Resell or redistribute the Service without permission</li>
              <li>Use the Service to send spam or unsolicited communications</li>
            </ul>

            <h2 className="font-display font-semibold text-2xl text-slate-900 mt-12 mb-4">
              6. MLS Data Usage
            </h2>
            <p className="text-slate-600 mb-6">
              The Service uses MLS data from authorized sources. You agree to comply with all applicable
              MLS rules and regulations. Reports generated through the Service are for your legitimate
              business use in real estate. You may not use MLS data for purposes unrelated to real estate
              transactions or marketing.
            </p>

            <h2 className="font-display font-semibold text-2xl text-slate-900 mt-12 mb-4">
              7. Intellectual Property
            </h2>
            <p className="text-slate-600 mb-6">
              The Service, including all content, features, and functionality, is owned by TrendyReports
              and protected by intellectual property laws. You retain ownership of your content (logos,
              branding) that you upload to the Service. By uploading content, you grant us a license to use
              it solely for providing the Service.
            </p>

            <h2 className="font-display font-semibold text-2xl text-slate-900 mt-12 mb-4">
              8. Disclaimer of Warranties
            </h2>
            <p className="text-slate-600 mb-6">
              THE SERVICE IS PROVIDED "AS IS" WITHOUT WARRANTIES OF ANY KIND, EXPRESS OR IMPLIED. WE DO NOT
              WARRANT THAT THE SERVICE WILL BE UNINTERRUPTED, ERROR-FREE, OR SECURE. WE MAKE NO WARRANTIES
              REGARDING THE ACCURACY OR COMPLETENESS OF MLS DATA OR GENERATED REPORTS. YOU USE THE SERVICE
              AT YOUR OWN RISK.
            </p>

            <h2 className="font-display font-semibold text-2xl text-slate-900 mt-12 mb-4">
              9. Limitation of Liability
            </h2>
            <p className="text-slate-600 mb-6">
              TO THE MAXIMUM EXTENT PERMITTED BY LAW, TRENDYREPORTS SHALL NOT BE LIABLE FOR ANY INDIRECT,
              INCIDENTAL, SPECIAL, CONSEQUENTIAL, OR PUNITIVE DAMAGES ARISING FROM YOUR USE OF THE SERVICE.
              OUR TOTAL LIABILITY SHALL NOT EXCEED THE AMOUNT YOU PAID US IN THE TWELVE MONTHS PRECEDING
              THE CLAIM.
            </p>

            <h2 className="font-display font-semibold text-2xl text-slate-900 mt-12 mb-4">
              10. Indemnification
            </h2>
            <p className="text-slate-600 mb-6">
              You agree to indemnify and hold harmless TrendyReports and its officers, directors,
              employees, and agents from any claims, damages, or expenses arising from your use of the
              Service or violation of these Terms.
            </p>

            <h2 className="font-display font-semibold text-2xl text-slate-900 mt-12 mb-4">
              11. Termination
            </h2>
            <p className="text-slate-600 mb-6">
              We may terminate or suspend your account immediately, without prior notice, if you breach
              these Terms. Upon termination, your right to use the Service ceases immediately. Provisions
              that by their nature should survive termination shall survive.
            </p>

            <h2 className="font-display font-semibold text-2xl text-slate-900 mt-12 mb-4">
              12. Governing Law
            </h2>
            <p className="text-slate-600 mb-6">
              These Terms are governed by the laws of the State of California, without regard to conflict
              of law principles. Any disputes shall be resolved in the courts located in San Francisco
              County, California.
            </p>

            <h2 className="font-display font-semibold text-2xl text-slate-900 mt-12 mb-4">
              13. Changes to Terms
            </h2>
            <p className="text-slate-600 mb-6">
              We reserve the right to modify these Terms at any time. We will notify you of material
              changes by posting an update on our website or sending an email. Your continued use of the
              Service after changes constitutes acceptance of the modified Terms.
            </p>

            <h2 className="font-display font-semibold text-2xl text-slate-900 mt-12 mb-4">
              14. Contact Information
            </h2>
            <p className="text-slate-600 mb-6">
              For questions about these Terms, please contact us:
            </p>
            <div className="bg-slate-50 rounded-xl p-6">
              <p className="text-slate-700 mb-2">
                <strong>TrendyReports, Inc.</strong>
              </p>
              <p className="text-slate-600">
                Email:{" "}
                <a href="mailto:legal@trendyreports.com" className="text-indigo-600 hover:underline">
                  legal@trendyreports.com
                </a>
              </p>
              <p className="text-slate-600">Address: 123 Market Street, San Francisco, CA 94103</p>
            </div>
          </div>
        </div>
      </section>

      <Footer />
    </div>
  )
}

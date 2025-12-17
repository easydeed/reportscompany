import { Navbar } from "@/components/navbar"
import { Footer } from "@/components/footer"

export const metadata = {
  title: "Privacy Policy | TrendyReports",
  description: "TrendyReports Privacy Policy - How we collect, use, and protect your data.",
}

export default function PrivacyPage() {
  return (
    <div className="min-h-screen bg-white">
      <Navbar />

      <section className="pt-32 pb-16 px-4 sm:px-6 lg:px-8">
        <div className="max-w-[800px] mx-auto">
          <h1 className="font-display font-semibold text-4xl text-slate-900 mb-4">Privacy Policy</h1>
          <p className="text-slate-600 mb-8">Last updated: December 1, 2025</p>

          <div className="prose prose-slate max-w-none">
            <p className="lead text-lg text-slate-600 mb-8">
              At TrendyReports, we take your privacy seriously. This Privacy Policy explains how we collect,
              use, disclose, and safeguard your information when you use our service.
            </p>

            <h2 className="font-display font-semibold text-2xl text-slate-900 mt-12 mb-4">
              Information We Collect
            </h2>

            <h3 className="font-display font-semibold text-xl text-slate-900 mt-8 mb-3">
              Personal Information
            </h3>
            <p className="text-slate-600 mb-4">
              When you create an account, we collect information you provide directly, including:
            </p>
            <ul className="list-disc pl-6 text-slate-600 space-y-2 mb-6">
              <li>Name and email address</li>
              <li>Company name and job title</li>
              <li>Phone number (optional)</li>
              <li>Billing information (processed securely by Stripe)</li>
              <li>Profile photo (optional)</li>
            </ul>

            <h3 className="font-display font-semibold text-xl text-slate-900 mt-8 mb-3">
              Usage Information
            </h3>
            <p className="text-slate-600 mb-4">
              We automatically collect certain information when you use our service:
            </p>
            <ul className="list-disc pl-6 text-slate-600 space-y-2 mb-6">
              <li>Log data (IP address, browser type, pages visited)</li>
              <li>Device information (device type, operating system)</li>
              <li>Usage patterns (features used, reports generated)</li>
              <li>Performance data (load times, errors encountered)</li>
            </ul>

            <h3 className="font-display font-semibold text-xl text-slate-900 mt-8 mb-3">
              MLS Data
            </h3>
            <p className="text-slate-600 mb-6">
              To generate market reports, we access MLS data through authorized data providers. This data
              is used solely to create your reports and is not stored longer than necessary for report
              generation.
            </p>

            <h2 className="font-display font-semibold text-2xl text-slate-900 mt-12 mb-4">
              How We Use Your Information
            </h2>
            <p className="text-slate-600 mb-4">We use the information we collect to:</p>
            <ul className="list-disc pl-6 text-slate-600 space-y-2 mb-6">
              <li>Provide, maintain, and improve our services</li>
              <li>Generate market reports on your behalf</li>
              <li>Send scheduled reports to your specified recipients</li>
              <li>Process transactions and send billing information</li>
              <li>Send product updates and marketing communications (with your consent)</li>
              <li>Respond to your comments, questions, and support requests</li>
              <li>Monitor and analyze usage trends to improve user experience</li>
              <li>Detect, prevent, and address technical issues and fraud</li>
            </ul>

            <h2 className="font-display font-semibold text-2xl text-slate-900 mt-12 mb-4">
              Information Sharing
            </h2>
            <p className="text-slate-600 mb-4">
              We do not sell your personal information. We may share your information only in these circumstances:
            </p>
            <ul className="list-disc pl-6 text-slate-600 space-y-2 mb-6">
              <li>
                <strong>Service Providers:</strong> With third-party vendors who assist in providing our
                services (e.g., email delivery, payment processing, cloud hosting)
              </li>
              <li>
                <strong>Business Transfers:</strong> In connection with a merger, acquisition, or sale of
                assets
              </li>
              <li>
                <strong>Legal Requirements:</strong> When required by law or to protect our rights and
                safety
              </li>
              <li>
                <strong>With Your Consent:</strong> When you explicitly authorize us to share information
              </li>
            </ul>

            <h2 className="font-display font-semibold text-2xl text-slate-900 mt-12 mb-4">
              Data Security
            </h2>
            <p className="text-slate-600 mb-6">
              We implement industry-standard security measures to protect your data, including:
            </p>
            <ul className="list-disc pl-6 text-slate-600 space-y-2 mb-6">
              <li>Encryption of data in transit (TLS 1.3) and at rest (AES-256)</li>
              <li>Regular security audits and penetration testing</li>
              <li>Access controls and authentication requirements</li>
              <li>Secure data centers with SOC 2 Type II compliance</li>
              <li>Regular employee security training</li>
            </ul>

            <h2 className="font-display font-semibold text-2xl text-slate-900 mt-12 mb-4">
              Data Retention
            </h2>
            <p className="text-slate-600 mb-6">
              We retain your personal information for as long as your account is active or as needed to
              provide services. Generated reports are stored for 90 days unless you delete them earlier.
              You can request deletion of your account and associated data at any time.
            </p>

            <h2 className="font-display font-semibold text-2xl text-slate-900 mt-12 mb-4">
              Your Rights
            </h2>
            <p className="text-slate-600 mb-4">Depending on your location, you may have the right to:</p>
            <ul className="list-disc pl-6 text-slate-600 space-y-2 mb-6">
              <li>Access the personal information we hold about you</li>
              <li>Correct inaccurate or incomplete information</li>
              <li>Delete your personal information</li>
              <li>Export your data in a portable format</li>
              <li>Opt out of marketing communications</li>
              <li>Restrict or object to certain processing activities</li>
            </ul>
            <p className="text-slate-600 mb-6">
              To exercise these rights, please contact us at{" "}
              <a href="mailto:privacy@trendyreports.com" className="text-purple-600 hover:underline">
                privacy@trendyreports.com
              </a>
              .
            </p>

            <h2 className="font-display font-semibold text-2xl text-slate-900 mt-12 mb-4">
              Cookies and Tracking
            </h2>
            <p className="text-slate-600 mb-6">
              We use cookies and similar technologies to provide and improve our services. You can control
              cookie preferences through your browser settings. Essential cookies required for the service
              to function cannot be disabled.
            </p>

            <h2 className="font-display font-semibold text-2xl text-slate-900 mt-12 mb-4">
              Children's Privacy
            </h2>
            <p className="text-slate-600 mb-6">
              Our service is not intended for children under 18 years of age. We do not knowingly collect
              personal information from children.
            </p>

            <h2 className="font-display font-semibold text-2xl text-slate-900 mt-12 mb-4">
              Changes to This Policy
            </h2>
            <p className="text-slate-600 mb-6">
              We may update this Privacy Policy from time to time. We will notify you of any material
              changes by posting the new policy on this page and updating the "Last updated" date.
              Continued use of the service after changes constitutes acceptance of the updated policy.
            </p>

            <h2 className="font-display font-semibold text-2xl text-slate-900 mt-12 mb-4">Contact Us</h2>
            <p className="text-slate-600 mb-6">
              If you have questions about this Privacy Policy or our data practices, please contact us:
            </p>
            <div className="bg-slate-50 rounded-xl p-6">
              <p className="text-slate-700 mb-2">
                <strong>TrendyReports, Inc.</strong>
              </p>
              <p className="text-slate-600">
                Email:{" "}
                <a href="mailto:privacy@trendyreports.com" className="text-purple-600 hover:underline">
                  privacy@trendyreports.com
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

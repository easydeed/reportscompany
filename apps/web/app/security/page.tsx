import { Navbar } from "@/components/navbar"
import { Footer } from "@/components/footer"
import { Shield, CheckCircle, Server, XCircle, Trash2, Mail } from "lucide-react"

export const metadata = {
  title: "Security | TrendyReports",
  description: "How TrendyReports protects your data — our current security practices, the providers we use, and what we don't claim.",
}

const whatWeHave = [
  "Passwords are hashed with bcrypt before storage",
  "PostgreSQL row-level security separates tenant data",
  "Sessions use HTTP-only secure cookies",
  "Stripe webhooks are signature-verified",
  "Rate limiting on authentication endpoints",
  "Role-based access controls for platform admins, title company admins, affiliates, and agents",
  "Encrypted storage at rest (PostgreSQL on Render, file storage on Cloudflare R2)",
  "HTTPS/TLS in transit",
]

const whatWeDontClaim = [
  "We are not SOC 2 certified",
  "We don't offer multi-factor authentication",
  "We don't support SSO (Google, Microsoft, SAML)",
  "We have not undergone external penetration testing",
]

export default function SecurityPage() {
  return (
    <div className="min-h-screen bg-white">
      <Navbar />

      {/* Hero */}
      <section className="pt-32 pb-16 px-4 sm:px-6 lg:px-8">
        <div className="max-w-[800px] mx-auto text-center">
          <div className="w-16 h-16 bg-indigo-100 rounded-2xl flex items-center justify-center mx-auto mb-6">
            <Shield className="w-8 h-8 text-indigo-600" />
          </div>
          <h1 className="font-display font-semibold text-4xl sm:text-5xl text-slate-900 mb-6">
            Security at TrendyReports
          </h1>
          <p className="text-xl text-slate-600 leading-relaxed">
            TrendyReports runs on managed cloud infrastructure provided by Vercel,
            Render, and Cloudflare — vendors that handle HTTPS at the edge,
            encrypted storage at rest, and TLS for database connections by default.
          </p>
        </div>
      </section>

      {/* What we have today */}
      <section className="py-16 px-4 sm:px-6 lg:px-8 bg-slate-50">
        <div className="max-w-[1000px] mx-auto">
          <h2 className="font-display font-semibold text-3xl text-slate-900 mb-12 text-center">
            What we have today
          </h2>

          <div className="grid md:grid-cols-2 gap-4">
            {whatWeHave.map((item) => (
              <div key={item} className="flex items-start gap-3 bg-white rounded-xl p-5 border border-slate-200">
                <CheckCircle className="w-5 h-5 text-green-500 mt-0.5 shrink-0" />
                <span className="text-slate-700">{item}</span>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Providers we use */}
      <section className="py-16 px-4 sm:px-6 lg:px-8">
        <div className="max-w-[800px] mx-auto">
          <div className="flex items-center justify-center w-12 h-12 bg-indigo-100 rounded-xl mx-auto mb-6">
            <Server className="w-6 h-6 text-indigo-600" />
          </div>
          <h2 className="font-display font-semibold text-3xl text-slate-900 mb-6 text-center">
            Providers we use
          </h2>
          <p className="text-lg text-slate-600 leading-relaxed text-center">
            We rely on reputable managed providers for infrastructure and operations:
            Vercel (web hosting), Render (API and database hosting), Cloudflare R2
            (file storage), Stripe (payments), SendGrid (transactional email), and
            Twilio (SMS notifications).
          </p>
        </div>
      </section>

      {/* What we don't claim */}
      <section className="py-16 px-4 sm:px-6 lg:px-8 bg-slate-50">
        <div className="max-w-[800px] mx-auto">
          <h2 className="font-display font-semibold text-3xl text-slate-900 mb-8 text-center">
            What we don't claim
          </h2>
          <p className="text-slate-600 mb-8 text-center">
            We're explicit about what we don't offer today:
          </p>
          <div className="space-y-3">
            {whatWeDontClaim.map((item) => (
              <div key={item} className="flex items-start gap-3 bg-white rounded-xl p-5 border border-slate-200">
                <XCircle className="w-5 h-5 text-slate-400 mt-0.5 shrink-0" />
                <span className="text-slate-700">{item}</span>
              </div>
            ))}
          </div>
          <p className="text-slate-600 mt-8 text-center">
            We continue to invest in our security program as the product matures.
          </p>
        </div>
      </section>

      {/* Account and data deletion */}
      <section className="py-16 px-4 sm:px-6 lg:px-8">
        <div className="max-w-[800px] mx-auto">
          <div className="flex items-center justify-center w-12 h-12 bg-indigo-100 rounded-xl mx-auto mb-6">
            <Trash2 className="w-6 h-6 text-indigo-600" />
          </div>
          <h2 className="font-display font-semibold text-3xl text-slate-900 mb-6 text-center">
            Account and data deletion
          </h2>
          <p className="text-lg text-slate-600 leading-relaxed text-center">
            To delete your account and associated data, contact us at{" "}
            <a href="mailto:support@trendyreports.io" className="text-indigo-600 hover:text-indigo-700 font-medium">
              support@trendyreports.io
            </a>
            . We'll process your request as quickly as possible.
          </p>
        </div>
      </section>

      {/* Questions */}
      <section className="py-16 px-4 sm:px-6 lg:px-8">
        <div className="max-w-[800px] mx-auto">
          <div className="bg-slate-900 rounded-2xl p-8 md:p-12 text-white text-center">
            <Mail className="w-12 h-12 mx-auto mb-6 text-indigo-400" />
            <h2 className="font-display font-semibold text-2xl mb-4">Questions</h2>
            <p className="text-slate-300 mb-6">
              Contact us for security questions, vulnerability reports, or
              compliance documentation.
            </p>
            <a
              href="mailto:support@trendyreports.io"
              className="inline-flex items-center justify-center bg-white text-slate-900 font-medium px-6 py-3 rounded-lg hover:bg-slate-100 transition-colors"
            >
              support@trendyreports.io
            </a>
          </div>
        </div>
      </section>

      <Footer />
    </div>
  )
}

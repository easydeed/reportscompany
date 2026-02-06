import { Navbar } from "@/components/navbar"
import { Footer } from "@/components/footer"
import { Shield, Lock, Server, Eye, Users, FileCheck, AlertTriangle, CheckCircle } from "lucide-react"

export const metadata = {
  title: "Security | TrendyReports",
  description: "Learn about TrendyReports security practices - how we protect your data and maintain platform security.",
}

const securityFeatures = [
  {
    icon: Lock,
    title: "Encryption Everywhere",
    description: "All data is encrypted in transit using TLS 1.3 and at rest using AES-256 encryption. Your information is protected at every step.",
  },
  {
    icon: Server,
    title: "SOC 2 Type II Compliant Infrastructure",
    description: "Our cloud infrastructure is hosted on AWS with SOC 2 Type II certification, ensuring the highest standards of security and availability.",
  },
  {
    icon: Eye,
    title: "Access Controls",
    description: "Role-based access control, multi-factor authentication, and audit logging ensure only authorized users can access your data.",
  },
  {
    icon: Users,
    title: "Employee Security",
    description: "All employees undergo background checks and receive regular security training. Access to production systems is strictly limited.",
  },
  {
    icon: FileCheck,
    title: "Regular Audits",
    description: "We conduct regular security audits, penetration testing, and vulnerability assessments by third-party security firms.",
  },
  {
    icon: AlertTriangle,
    title: "Incident Response",
    description: "We have a documented incident response plan and dedicated security team ready to respond to any security concerns 24/7.",
  },
]

const certifications = [
  { name: "SOC 2 Type II", description: "Service Organization Controls compliance" },
  { name: "GDPR", description: "General Data Protection Regulation compliance" },
  { name: "CCPA", description: "California Consumer Privacy Act compliance" },
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
            Your data security is our top priority. We implement industry-leading security practices
            to protect your information and maintain your trust.
          </p>
        </div>
      </section>

      {/* Security Features */}
      <section className="py-16 px-4 sm:px-6 lg:px-8 bg-slate-50">
        <div className="max-w-[1000px] mx-auto">
          <h2 className="font-display font-semibold text-3xl text-slate-900 mb-12 text-center">
            How We Protect Your Data
          </h2>

          <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-8">
            {securityFeatures.map((feature) => (
              <div key={feature.title} className="bg-white rounded-xl p-6 border border-slate-200">
                <div className="w-12 h-12 bg-indigo-100 rounded-xl flex items-center justify-center mb-4">
                  <feature.icon className="w-6 h-6 text-indigo-600" />
                </div>
                <h3 className="font-display font-semibold text-lg text-slate-900 mb-2">
                  {feature.title}
                </h3>
                <p className="text-slate-600 text-sm">{feature.description}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Data Protection */}
      <section className="py-16 px-4 sm:px-6 lg:px-8">
        <div className="max-w-[1000px] mx-auto">
          <div className="grid md:grid-cols-2 gap-12 items-center">
            <div>
              <h2 className="font-display font-semibold text-3xl text-slate-900 mb-6">
                Data Protection Practices
              </h2>
              <div className="space-y-4">
                <div className="flex items-start gap-3">
                  <CheckCircle className="w-5 h-5 text-green-500 mt-0.5 shrink-0" />
                  <div>
                    <h4 className="font-semibold text-slate-900">Data Minimization</h4>
                    <p className="text-slate-600 text-sm">
                      We only collect data necessary to provide our service. MLS data is processed
                      and not stored longer than needed.
                    </p>
                  </div>
                </div>
                <div className="flex items-start gap-3">
                  <CheckCircle className="w-5 h-5 text-green-500 mt-0.5 shrink-0" />
                  <div>
                    <h4 className="font-semibold text-slate-900">Data Retention</h4>
                    <p className="text-slate-600 text-sm">
                      Generated reports are retained for 90 days. You can delete your data at any
                      time through your account settings.
                    </p>
                  </div>
                </div>
                <div className="flex items-start gap-3">
                  <CheckCircle className="w-5 h-5 text-green-500 mt-0.5 shrink-0" />
                  <div>
                    <h4 className="font-semibold text-slate-900">Secure Deletion</h4>
                    <p className="text-slate-600 text-sm">
                      When you delete data or close your account, it is permanently removed from
                      all systems and backups within 30 days.
                    </p>
                  </div>
                </div>
                <div className="flex items-start gap-3">
                  <CheckCircle className="w-5 h-5 text-green-500 mt-0.5 shrink-0" />
                  <div>
                    <h4 className="font-semibold text-slate-900">No Data Selling</h4>
                    <p className="text-slate-600 text-sm">
                      We never sell your personal information or share it with third parties for
                      marketing purposes.
                    </p>
                  </div>
                </div>
              </div>
            </div>
            <div className="bg-gradient-to-br from-indigo-600 to-indigo-800 rounded-2xl p-8 text-white">
              <h3 className="font-display font-semibold text-xl mb-6">Compliance & Certifications</h3>
              <div className="space-y-4">
                {certifications.map((cert) => (
                  <div key={cert.name} className="flex items-center gap-3">
                    <div className="w-10 h-10 bg-white/20 rounded-lg flex items-center justify-center">
                      <CheckCircle className="w-5 h-5" />
                    </div>
                    <div>
                      <div className="font-semibold">{cert.name}</div>
                      <div className="text-indigo-200 text-sm">{cert.description}</div>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* Infrastructure */}
      <section className="py-16 px-4 sm:px-6 lg:px-8 bg-slate-50">
        <div className="max-w-[1000px] mx-auto">
          <h2 className="font-display font-semibold text-3xl text-slate-900 mb-8 text-center">
            Infrastructure Security
          </h2>

          <div className="grid md:grid-cols-2 gap-8">
            <div className="bg-white rounded-xl p-6 border border-slate-200">
              <h3 className="font-display font-semibold text-lg text-slate-900 mb-4">
                Cloud Infrastructure
              </h3>
              <ul className="space-y-3 text-slate-600">
                <li className="flex items-start gap-2">
                  <CheckCircle className="w-4 h-4 text-green-500 mt-1 shrink-0" />
                  <span>Hosted on AWS with multi-AZ deployment</span>
                </li>
                <li className="flex items-start gap-2">
                  <CheckCircle className="w-4 h-4 text-green-500 mt-1 shrink-0" />
                  <span>Automated backups with point-in-time recovery</span>
                </li>
                <li className="flex items-start gap-2">
                  <CheckCircle className="w-4 h-4 text-green-500 mt-1 shrink-0" />
                  <span>DDoS protection and WAF (Web Application Firewall)</span>
                </li>
                <li className="flex items-start gap-2">
                  <CheckCircle className="w-4 h-4 text-green-500 mt-1 shrink-0" />
                  <span>99.9% uptime SLA</span>
                </li>
              </ul>
            </div>
            <div className="bg-white rounded-xl p-6 border border-slate-200">
              <h3 className="font-display font-semibold text-lg text-slate-900 mb-4">
                Application Security
              </h3>
              <ul className="space-y-3 text-slate-600">
                <li className="flex items-start gap-2">
                  <CheckCircle className="w-4 h-4 text-green-500 mt-1 shrink-0" />
                  <span>OWASP Top 10 vulnerability protection</span>
                </li>
                <li className="flex items-start gap-2">
                  <CheckCircle className="w-4 h-4 text-green-500 mt-1 shrink-0" />
                  <span>Secure coding practices and code review</span>
                </li>
                <li className="flex items-start gap-2">
                  <CheckCircle className="w-4 h-4 text-green-500 mt-1 shrink-0" />
                  <span>Dependency scanning and automated updates</span>
                </li>
                <li className="flex items-start gap-2">
                  <CheckCircle className="w-4 h-4 text-green-500 mt-1 shrink-0" />
                  <span>Rate limiting and abuse prevention</span>
                </li>
              </ul>
            </div>
          </div>
        </div>
      </section>

      {/* Report a Vulnerability */}
      <section className="py-16 px-4 sm:px-6 lg:px-8">
        <div className="max-w-[800px] mx-auto">
          <div className="bg-slate-900 rounded-2xl p-8 md:p-12 text-white text-center">
            <AlertTriangle className="w-12 h-12 mx-auto mb-6 text-yellow-400" />
            <h2 className="font-display font-semibold text-2xl mb-4">Report a Security Vulnerability</h2>
            <p className="text-slate-300 mb-6">
              We take security seriously. If you discover a vulnerability, please report it responsibly.
              We have a bug bounty program for valid security findings.
            </p>
            <a
              href="mailto:security@trendyreports.com"
              className="inline-flex items-center justify-center bg-white text-slate-900 font-medium px-6 py-3 rounded-lg hover:bg-slate-100 transition-colors"
            >
              security@trendyreports.com
            </a>
          </div>
        </div>
      </section>

      {/* FAQ */}
      <section className="py-16 px-4 sm:px-6 lg:px-8 bg-slate-50">
        <div className="max-w-[800px] mx-auto">
          <h2 className="font-display font-semibold text-2xl text-slate-900 mb-8 text-center">
            Security FAQ
          </h2>

          <div className="space-y-4">
            <div className="bg-white rounded-xl p-6 border border-slate-200">
              <h3 className="font-semibold text-slate-900 mb-2">
                Where is my data stored?
              </h3>
              <p className="text-slate-600">
                Your data is stored in secure AWS data centers located in the United States. All data
                is encrypted at rest using AES-256 encryption.
              </p>
            </div>
            <div className="bg-white rounded-xl p-6 border border-slate-200">
              <h3 className="font-semibold text-slate-900 mb-2">
                Do you share my data with third parties?
              </h3>
              <p className="text-slate-600">
                We only share data with service providers necessary to operate our service (e.g., email
                delivery, payment processing). We never sell your data.
              </p>
            </div>
            <div className="bg-white rounded-xl p-6 border border-slate-200">
              <h3 className="font-semibold text-slate-900 mb-2">
                How can I delete my data?
              </h3>
              <p className="text-slate-600">
                You can delete your reports and account data at any time from your account settings.
                For complete account deletion, contact support@trendyreports.com.
              </p>
            </div>
            <div className="bg-white rounded-xl p-6 border border-slate-200">
              <h3 className="font-semibold text-slate-900 mb-2">
                Is my payment information secure?
              </h3>
              <p className="text-slate-600">
                Yes. We use Stripe for payment processing. Your payment details are never stored on our
                servers. Stripe is PCI DSS Level 1 certified.
              </p>
            </div>
          </div>
        </div>
      </section>

      <Footer />
    </div>
  )
}

import { Navbar } from "@/components/navbar"
import { Footer } from "@/components/footer"
import { Code, Book, Key, Zap, FileJson, Mail, Calendar, Shield, ArrowRight, ExternalLink } from "lucide-react"
import Link from "next/link"

export const metadata = {
  title: "API Documentation | TrendyReports",
  description: "TrendyReports API documentation - Integrate automated market reports into your applications.",
}

const endpoints = [
  {
    method: "POST",
    path: "/v1/reports/generate",
    description: "Generate a new market report",
    tag: "Reports",
  },
  {
    method: "GET",
    path: "/v1/reports/{id}",
    description: "Get report details and PDF URL",
    tag: "Reports",
  },
  {
    method: "GET",
    path: "/v1/reports",
    description: "List all reports for your account",
    tag: "Reports",
  },
  {
    method: "POST",
    path: "/v1/schedules",
    description: "Create an automated report schedule",
    tag: "Schedules",
  },
  {
    method: "GET",
    path: "/v1/schedules",
    description: "List all schedules",
    tag: "Schedules",
  },
  {
    method: "PATCH",
    path: "/v1/schedules/{id}",
    description: "Update or pause a schedule",
    tag: "Schedules",
  },
  {
    method: "GET",
    path: "/v1/account",
    description: "Get account information and usage",
    tag: "Account",
  },
]

const features = [
  {
    icon: FileJson,
    title: "RESTful API",
    description: "Clean, predictable resource-oriented endpoints with JSON responses.",
  },
  {
    icon: Key,
    title: "API Key Auth",
    description: "Simple API key authentication. Generate keys from your dashboard.",
  },
  {
    icon: Zap,
    title: "Webhooks",
    description: "Get notified when reports are ready or schedules run.",
  },
  {
    icon: Shield,
    title: "Rate Limiting",
    description: "Fair rate limits with clear headers. Pro plans get higher limits.",
  },
]

const methodColors: Record<string, string> = {
  GET: "bg-green-100 text-green-700",
  POST: "bg-blue-100 text-blue-700",
  PATCH: "bg-yellow-100 text-yellow-700",
  DELETE: "bg-red-100 text-red-700",
}

export default function DocsPage() {
  return (
    <div className="min-h-screen bg-white">
      <Navbar />

      {/* Hero */}
      <section className="pt-32 pb-16 px-4 sm:px-6 lg:px-8">
        <div className="max-w-[800px] mx-auto text-center">
          <div className="inline-flex items-center gap-2 bg-purple-100 text-purple-700 px-4 py-2 rounded-full mb-6 text-sm font-medium">
            <Code className="w-4 h-4" />
            Developer Documentation
          </div>
          <h1 className="font-display font-semibold text-4xl sm:text-5xl text-slate-900 mb-6">
            TrendyReports API
          </h1>
          <p className="text-xl text-slate-600 leading-relaxed mb-8">
            Integrate automated market reports directly into your CRM, website, or application.
            Generate reports programmatically and automate your market intelligence workflow.
          </p>
          <div className="flex flex-col sm:flex-row gap-4 justify-center">
            <a
              href="#quickstart"
              className="inline-flex items-center justify-center bg-purple-600 hover:bg-purple-700 text-white font-medium px-6 py-3 rounded-lg transition-colors"
            >
              Get Started
              <ArrowRight className="w-4 h-4 ml-2" />
            </a>
            <a
              href="mailto:api@trendyreports.com?subject=API Access Request"
              className="inline-flex items-center justify-center border border-slate-300 hover:border-purple-300 hover:bg-purple-50 text-slate-700 font-medium px-6 py-3 rounded-lg transition-colors"
            >
              Request API Access
            </a>
          </div>
        </div>
      </section>

      {/* Features */}
      <section className="py-16 px-4 sm:px-6 lg:px-8 bg-slate-50">
        <div className="max-w-[1000px] mx-auto">
          <div className="grid md:grid-cols-2 lg:grid-cols-4 gap-6">
            {features.map((feature) => (
              <div key={feature.title} className="bg-white rounded-xl p-6 border border-slate-200">
                <div className="w-10 h-10 bg-purple-100 rounded-lg flex items-center justify-center mb-4">
                  <feature.icon className="w-5 h-5 text-purple-600" />
                </div>
                <h3 className="font-semibold text-slate-900 mb-2">{feature.title}</h3>
                <p className="text-slate-600 text-sm">{feature.description}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Quick Start */}
      <section id="quickstart" className="py-16 px-4 sm:px-6 lg:px-8">
        <div className="max-w-[1000px] mx-auto">
          <h2 className="font-display font-semibold text-3xl text-slate-900 mb-8 text-center">
            Quick Start
          </h2>

          <div className="grid md:grid-cols-2 gap-8">
            <div>
              <h3 className="font-semibold text-lg text-slate-900 mb-4">1. Get Your API Key</h3>
              <p className="text-slate-600 mb-4">
                Generate an API key from your dashboard under Settings &rarr; API. Keep this key
                secure and never expose it in client-side code.
              </p>
              <div className="bg-slate-900 rounded-lg p-4 font-mono text-sm text-slate-300 overflow-x-auto">
                <span className="text-slate-500"># Include in request headers</span>
                <br />
                Authorization: Bearer tr_live_xxxxxxxxxxxx
              </div>
            </div>

            <div>
              <h3 className="font-semibold text-lg text-slate-900 mb-4">2. Make Your First Request</h3>
              <p className="text-slate-600 mb-4">
                Generate a market report with a simple POST request. The API will return a report
                ID that you can use to retrieve the PDF.
              </p>
              <div className="bg-slate-900 rounded-lg p-4 font-mono text-sm text-slate-300 overflow-x-auto">
                <span className="text-purple-400">curl</span> -X POST \<br />
                {"  "}https://api.trendyreports.com/v1/reports/generate \<br />
                {"  "}-H{" "}
                <span className="text-green-400">"Authorization: Bearer tr_live_xxx"</span> \<br />
                {"  "}-H{" "}
                <span className="text-green-400">"Content-Type: application/json"</span> \<br />
                {"  "}-d <span className="text-green-400">'{"{"}"report_type": "market_snapshot", "zip_codes": ["94103"]{"}"}'</span>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* Endpoints */}
      <section className="py-16 px-4 sm:px-6 lg:px-8 bg-slate-50">
        <div className="max-w-[1000px] mx-auto">
          <h2 className="font-display font-semibold text-3xl text-slate-900 mb-8 text-center">
            API Endpoints
          </h2>

          <div className="bg-white rounded-xl border border-slate-200 overflow-hidden">
            <div className="divide-y divide-slate-100">
              {endpoints.map((endpoint) => (
                <div
                  key={endpoint.path}
                  className="flex items-center justify-between p-4 hover:bg-slate-50 transition-colors"
                >
                  <div className="flex items-center gap-4">
                    <span
                      className={`px-2 py-1 rounded text-xs font-mono font-bold ${
                        methodColors[endpoint.method]
                      }`}
                    >
                      {endpoint.method}
                    </span>
                    <code className="text-sm text-slate-700">{endpoint.path}</code>
                  </div>
                  <div className="flex items-center gap-4">
                    <span className="text-sm text-slate-600 hidden md:block">
                      {endpoint.description}
                    </span>
                    <span className="text-xs bg-slate-100 text-slate-600 px-2 py-1 rounded">
                      {endpoint.tag}
                    </span>
                  </div>
                </div>
              ))}
            </div>
          </div>

          <p className="text-center text-slate-600 mt-6">
            Full API reference documentation coming soon.{" "}
            <a href="mailto:api@trendyreports.com" className="text-purple-600 hover:underline">
              Contact us
            </a>{" "}
            for early access.
          </p>
        </div>
      </section>

      {/* Report Types */}
      <section className="py-16 px-4 sm:px-6 lg:px-8">
        <div className="max-w-[1000px] mx-auto">
          <h2 className="font-display font-semibold text-3xl text-slate-900 mb-8 text-center">
            Available Report Types
          </h2>

          <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-6">
            {[
              {
                name: "market_snapshot",
                title: "Market Snapshot",
                description: "Area-wide market trends with charts and statistics",
              },
              {
                name: "new_listings",
                title: "New Listings Gallery",
                description: "Photo-rich showcase of recent listings",
              },
              {
                name: "featured_listings",
                title: "Featured Listings",
                description: "Curated property highlights",
              },
              {
                name: "neighborhood",
                title: "Neighborhood Analysis",
                description: "Hyperlocal market intelligence",
              },
              {
                name: "price_trends",
                title: "Price Trends",
                description: "Historical price data visualization",
              },
              {
                name: "custom",
                title: "Custom Report",
                description: "Build your own with our report builder",
              },
            ].map((type) => (
              <div key={type.name} className="bg-white rounded-xl p-6 border border-slate-200">
                <code className="text-xs bg-purple-100 text-purple-700 px-2 py-1 rounded mb-3 inline-block">
                  {type.name}
                </code>
                <h3 className="font-semibold text-slate-900 mb-2">{type.title}</h3>
                <p className="text-slate-600 text-sm">{type.description}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Webhooks */}
      <section className="py-16 px-4 sm:px-6 lg:px-8 bg-slate-50">
        <div className="max-w-[1000px] mx-auto">
          <div className="grid md:grid-cols-2 gap-12 items-center">
            <div>
              <h2 className="font-display font-semibold text-3xl text-slate-900 mb-6">Webhooks</h2>
              <p className="text-slate-600 mb-6">
                Subscribe to events and get notified when important things happen. Perfect for
                building automated workflows.
              </p>
              <div className="space-y-3">
                <div className="flex items-center gap-3">
                  <code className="text-xs bg-slate-200 text-slate-700 px-2 py-1 rounded">
                    report.completed
                  </code>
                  <span className="text-slate-600 text-sm">Report is ready for download</span>
                </div>
                <div className="flex items-center gap-3">
                  <code className="text-xs bg-slate-200 text-slate-700 px-2 py-1 rounded">
                    report.failed
                  </code>
                  <span className="text-slate-600 text-sm">Report generation failed</span>
                </div>
                <div className="flex items-center gap-3">
                  <code className="text-xs bg-slate-200 text-slate-700 px-2 py-1 rounded">
                    schedule.executed
                  </code>
                  <span className="text-slate-600 text-sm">Scheduled report was sent</span>
                </div>
              </div>
            </div>
            <div className="bg-slate-900 rounded-xl p-6">
              <div className="text-sm font-mono text-slate-300">
                <span className="text-slate-500">// Webhook payload example</span>
                <br />
                {"{"}
                <br />
                {"  "}<span className="text-purple-400">"event"</span>:{" "}
                <span className="text-green-400">"report.completed"</span>,
                <br />
                {"  "}<span className="text-purple-400">"data"</span>: {"{"}
                <br />
                {"    "}<span className="text-purple-400">"report_id"</span>:{" "}
                <span className="text-green-400">"rpt_abc123"</span>,
                <br />
                {"    "}<span className="text-purple-400">"pdf_url"</span>:{" "}
                <span className="text-green-400">"https://..."</span>,
                <br />
                {"    "}<span className="text-purple-400">"created_at"</span>:{" "}
                <span className="text-green-400">"2025-12-17T..."</span>
                <br />
                {"  }"}
                <br />
                {"}"}
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* CTA */}
      <section className="py-16 px-4 sm:px-6 lg:px-8">
        <div className="max-w-[800px] mx-auto text-center">
          <h2 className="font-display font-semibold text-3xl text-slate-900 mb-4">
            Ready to integrate?
          </h2>
          <p className="text-xl text-slate-600 mb-8">
            API access is available on Pro and Enterprise plans. Contact us to get started.
          </p>
          <div className="flex flex-col sm:flex-row gap-4 justify-center">
            <a
              href="mailto:api@trendyreports.com?subject=API Access Request"
              className="inline-flex items-center justify-center bg-purple-600 hover:bg-purple-700 text-white font-medium px-6 py-3 rounded-lg transition-colors"
            >
              <Mail className="w-5 h-5 mr-2" />
              Request API Access
            </a>
            <Link
              href="/login"
              className="inline-flex items-center justify-center border border-slate-300 hover:border-purple-300 hover:bg-purple-50 text-slate-700 font-medium px-6 py-3 rounded-lg transition-colors"
            >
              Start Free Trial
            </Link>
          </div>
        </div>
      </section>

      <Footer />
    </div>
  )
}

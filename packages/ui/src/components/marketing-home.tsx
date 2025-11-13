"use client"

import { Button } from "./ui/button"
import { Navbar } from "./navbar"
import { CodeTabs } from "./code-tabs"
import { motion } from "framer-motion"
import { TrendingUp, FileText, Zap, BarChart3, Sparkles, Code, ArrowRight, Check } from "lucide-react"
import { useState } from "react"

export function MarketingHome() {
  const [currentSample, setCurrentSample] = useState(0)

  const samples = [
    { title: "Market Snapshot", image: "/real-estate-market-report.png" },
    { title: "New Listings", image: "/neighborhood-comparison-chart.jpg" },
    { title: "Closed Sales", image: "/luxury-real-estate-data.jpg" },
    { title: "Inventory Trends", image: "/investment-property-metrics.jpg" },
    { title: "Price Analysis", image: "/real-estate-market-report.png" },
    { title: "Neighborhood Stats", image: "/neighborhood-comparison-chart.jpg" },
    { title: "Buyer Activity", image: "/luxury-real-estate-data.jpg" },
    { title: "Market Forecast", image: "/investment-property-metrics.jpg" },
  ]

  const pythonCode = `import requests

response = requests.post(
    "https://api.trendyreports.com/v1/reports",
    headers={"Authorization": "Bearer YOUR_API_KEY"},
    json={
        "type": "market_snapshot",
        "area": {"city": "San Francisco"},
        "lookback": 30
    }
)

report = response.json()
print(f"Report ID: {report['id']}")`

  const javascriptCode = `const response = await fetch(
  'https://api.trendyreports.com/v1/reports',
  {
    method: 'POST',
    headers: {
      'Authorization': 'Bearer YOUR_API_KEY',
      'Content-Type': 'application/json'
    },
    body: JSON.stringify({
      type: 'market_snapshot',
      area: { city: 'San Francisco' },
      lookback: 30
    })
  }
);

const report = await response.json();
console.log('Report ID:', report.id);`

  const pythonCodeGet = `response = requests.get(
    f"https://api.trendyreports.com/v1/reports/{report_id}",
    headers={"Authorization": "Bearer YOUR_API_KEY"}
)

data = response.json()
print(f"PDF: {data['pdf_url']}")`

  const javascriptCodeGet = `const response = await fetch(
  \`https://api.trendyreports.com/v1/reports/\${reportId}\`,
  {
    headers: {
      'Authorization': 'Bearer YOUR_API_KEY'
    }
  }
);

const data = await response.json();
console.log('PDF:', data.pdf_url);`

  return (
    <div className="min-h-screen bg-gradient-to-b from-white via-purple-50/30 to-white">
      <Navbar />

      {/* Hero */}
      <section className="relative pt-32 pb-20 px-4 sm:px-6 lg:px-8 overflow-hidden">
        <div className="absolute inset-0 opacity-30 pointer-events-none">
          <div className="absolute top-0 right-1/4 w-[600px] h-[600px] bg-purple-400 rounded-full blur-[140px]" />
          <div className="absolute bottom-0 left-1/4 w-[500px] h-[500px] bg-orange-300 rounded-full blur-[140px]" />
        </div>

        <div className="max-w-[1200px] mx-auto relative z-10">
          <div className="grid lg:grid-cols-2 gap-16 items-center">
            <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.2 }}>
              <div className="inline-flex items-center gap-2 px-3 py-1.5 rounded-full bg-purple-100 border border-purple-200 mb-6">
                <TrendingUp className="w-4 h-4 text-purple-600" />
                <span className="text-sm font-medium text-purple-700">Data that ships itself</span>
              </div>
              <h1 className="font-display font-bold text-5xl sm:text-6xl lg:text-7xl mb-6 text-balance bg-gradient-to-r from-purple-600 via-purple-500 to-orange-500 bg-clip-text text-transparent">
                MLS data.
                <br />
                Beautiful reports.
                <br />
                Zero effort.
              </h1>
              <p className="text-xl text-slate-600 mb-8 text-pretty leading-relaxed">
                Turn live housing data into stunning branded market reports in seconds.
              </p>
              <div className="flex flex-col sm:flex-row gap-4">
                <Button
                  size="lg"
                  className="bg-gradient-to-r from-purple-600 to-purple-700 hover:from-purple-700 hover:to-purple-800 text-white text-lg px-8 shadow-lg shadow-purple-500/25"
                >
                  Start Free Trial
                </Button>
                <Button
                  size="lg"
                  variant="outline"
                  className="text-lg px-8 border-slate-300 hover:bg-slate-50 bg-transparent"
                >
                  View Sample Reports
                </Button>
              </div>
              <p className="text-sm text-slate-500 mt-4">14 days free • No credit card • Cancel anytime</p>
            </motion.div>

            <motion.div
              initial={{ opacity: 0, scale: 0.95 }}
              animate={{ opacity: 1, scale: 1 }}
              transition={{ duration: 0.22, delay: 0.1 }}
              className="relative h-[600px] hidden lg:block"
            >
              {/* Main report card with visible chart content */}
              <div className="absolute top-0 right-0 w-80 aspect-[8.5/11] bg-white rounded-2xl shadow-2xl border border-slate-200 p-4 rotate-[2deg] z-20">
                <div className="w-full h-full bg-gradient-to-br from-purple-50 to-transparent rounded-xl overflow-hidden p-4 space-y-3">
                  <div className="space-y-2">
                    <div className="h-3 bg-purple-200 rounded w-1/2" />
                    <div className="h-6 bg-purple-600 rounded w-3/4" />
                  </div>
                  <div className="h-40 bg-gradient-to-t from-purple-100 to-transparent rounded-lg relative overflow-hidden">
                    <div className="absolute bottom-0 left-0 right-0 flex items-end justify-around gap-1 p-2">
                      <div className="w-8 h-16 bg-purple-400 rounded" />
                      <div className="w-8 h-24 bg-purple-500 rounded" />
                      <div className="w-8 h-20 bg-purple-400 rounded" />
                      <div className="w-8 h-32 bg-purple-600 rounded" />
                      <div className="w-8 h-28 bg-purple-500 rounded" />
                    </div>
                  </div>
                  <div className="space-y-2">
                    <div className="h-2 bg-slate-200 rounded w-full" />
                    <div className="h-2 bg-slate-200 rounded w-5/6" />
                    <div className="h-2 bg-slate-200 rounded w-4/6" />
                  </div>
                </div>
              </div>
              {/* Second card behind */}
              <div className="absolute top-12 left-0 w-80 aspect-[8.5/11] bg-white rounded-2xl shadow-xl border border-slate-200 p-4 rotate-[-4deg] z-10 opacity-90">
                <div className="w-full h-full bg-gradient-to-br from-orange-50 to-transparent rounded-xl" />
              </div>
              {/* Third card further behind */}
              <div className="absolute top-24 right-8 w-80 aspect-[8.5/11] bg-white rounded-2xl shadow-lg border border-slate-200 p-4 rotate-[6deg] opacity-70">
                <div className="w-full h-full bg-gradient-to-br from-blue-50 to-transparent rounded-xl" />
              </div>
            </motion.div>
          </div>
        </div>
      </section>

      {/* Value Props */}
      <section className="py-20 px-4 sm:px-6 lg:px-8 bg-white">
        <div className="max-w-[1200px] mx-auto">
          <div className="grid md:grid-cols-3 gap-8">
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              whileInView={{ opacity: 1, y: 0 }}
              viewport={{ once: true }}
              transition={{ duration: 0.2 }}
              className="relative group"
            >
              <div className="absolute inset-0 bg-gradient-to-br from-purple-100 to-purple-50 rounded-2xl transform group-hover:scale-105 transition-transform" />
              <div className="relative p-8 space-y-4">
                <div className="w-12 h-12 rounded-xl bg-purple-600 flex items-center justify-center">
                  <TrendingUp className="w-6 h-6 text-white" />
                </div>
                <h3 className="font-display font-bold text-2xl">Accurate MLS data</h3>
                <p className="text-slate-600 leading-relaxed">
                  Real-time market insights from verified MLS sources. Always current, always accurate.
                </p>
              </div>
            </motion.div>

            <motion.div
              initial={{ opacity: 0, y: 20 }}
              whileInView={{ opacity: 1, y: 0 }}
              viewport={{ once: true }}
              transition={{ duration: 0.2, delay: 0.1 }}
              className="relative group"
            >
              <div className="absolute inset-0 bg-gradient-to-br from-orange-100 to-orange-50 rounded-2xl transform group-hover:scale-105 transition-transform" />
              <div className="relative p-8 space-y-4">
                <div className="w-12 h-12 rounded-xl bg-orange-500 flex items-center justify-center">
                  <Sparkles className="w-6 h-6 text-white" />
                </div>
                <h3 className="font-display font-bold text-2xl">Branded for you</h3>
                <p className="text-slate-600 leading-relaxed">
                  Add your logo, colors, and style. Every report reinforces your professional brand.
                </p>
              </div>
            </motion.div>

            <motion.div
              initial={{ opacity: 0, y: 20 }}
              whileInView={{ opacity: 1, y: 0 }}
              viewport={{ once: true }}
              transition={{ duration: 0.2, delay: 0.2 }}
              className="relative group"
            >
              <div className="absolute inset-0 bg-gradient-to-br from-blue-100 to-blue-50 rounded-2xl transform group-hover:scale-105 transition-transform" />
              <div className="relative p-8 space-y-4">
                <div className="w-12 h-12 rounded-xl bg-blue-500 flex items-center justify-center">
                  <FileText className="w-6 h-6 text-white" />
                </div>
                <h3 className="font-display font-bold text-2xl">Print-perfect PDFs</h3>
                <p className="text-slate-600 leading-relaxed">
                  Letter-sized, pixel-crisp reports. Perfect for email or print. Client-ready in seconds.
                </p>
              </div>
            </motion.div>
          </div>
        </div>
      </section>

      {/* How it works - 4 steps */}
      <section className="py-20 px-4 sm:px-6 lg:px-8">
        <div className="max-w-[1200px] mx-auto">
          <div className="text-center mb-16">
            <h2 className="font-display font-bold text-4xl sm:text-5xl mb-4 text-white">How it works</h2>
          </div>

          <div className="grid md:grid-cols-4 gap-6">
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              whileInView={{ opacity: 1, y: 0 }}
              viewport={{ once: true }}
              transition={{ duration: 0.2 }}
              className="text-center"
            >
              <div className="w-16 h-16 rounded-full bg-cyan-500/10 border border-cyan-500/30 flex items-center justify-center mx-auto mb-4">
                <TrendingUp className="w-8 h-8 text-cyan-400" />
              </div>
              <h3 className="font-display font-semibold text-lg mb-2 text-white">Connect</h3>
              <p className="text-sm text-slate-400">Link your MLS credentials</p>
            </motion.div>

            <motion.div
              initial={{ opacity: 0, y: 20 }}
              whileInView={{ opacity: 1, y: 0 }}
              viewport={{ once: true }}
              transition={{ duration: 0.2, delay: 0.05 }}
              className="text-center"
            >
              <div className="w-16 h-16 rounded-full bg-cyan-500/10 border border-cyan-500/30 flex items-center justify-center mx-auto mb-4">
                <BarChart3 className="w-8 h-8 text-cyan-400" />
              </div>
              <h3 className="font-display font-semibold text-lg mb-2 text-white">Choose Area</h3>
              <p className="text-sm text-slate-400">Select city or ZIP codes</p>
            </motion.div>

            <motion.div
              initial={{ opacity: 0, y: 20 }}
              whileInView={{ opacity: 1, y: 0 }}
              viewport={{ once: true }}
              transition={{ duration: 0.2, delay: 0.1 }}
              className="text-center"
            >
              <div className="w-16 h-16 rounded-full bg-cyan-500/10 border border-cyan-500/30 flex items-center justify-center mx-auto mb-4">
                <Sparkles className="w-8 h-8 text-cyan-400" />
              </div>
              <h3 className="font-display font-semibold text-lg mb-2 text-white">Generate</h3>
              <p className="text-sm text-slate-400">Reports in 30 seconds</p>
            </motion.div>

            <motion.div
              initial={{ opacity: 0, y: 20 }}
              whileInView={{ opacity: 1, y: 0 }}
              viewport={{ once: true }}
              transition={{ duration: 0.2, delay: 0.15 }}
              className="text-center"
            >
              <div className="w-16 h-16 rounded-full bg-cyan-500/10 border border-cyan-500/30 flex items-center justify-center mx-auto mb-4">
                <Zap className="w-8 h-8 text-cyan-400" />
              </div>
              <h3 className="font-display font-semibold text-lg mb-2 text-white">Auto-Send</h3>
              <p className="text-sm text-slate-400">Schedule and deliver</p>
            </motion.div>
          </div>
        </div>
      </section>

      {/* Samples carousel */}
      <section className="py-20 px-4 sm:px-6 lg:px-8 bg-gradient-to-b from-purple-50/50 to-white">
        <div className="max-w-[1200px] mx-auto">
          <div className="text-center mb-12">
            <h2 className="font-display font-bold text-4xl sm:text-5xl mb-4">Sample Reports</h2>
            <p className="text-lg text-slate-600">See what your clients will receive</p>
          </div>

          <div className="grid grid-cols-2 md:grid-cols-4 gap-6">
            {samples.map((sample, idx) => (
              <motion.div
                key={idx}
                initial={{ opacity: 0, y: 20 }}
                whileInView={{ opacity: 1, y: 0 }}
                viewport={{ once: true }}
                transition={{ duration: 0.2, delay: idx * 0.05 }}
                onClick={() => setCurrentSample(idx)}
                className={`cursor-pointer bg-white rounded-xl border-2 transition-all hover:shadow-lg p-3 ${
                  currentSample === idx
                    ? "border-purple-500 shadow-lg shadow-purple-500/20"
                    : "border-slate-200 hover:border-purple-300"
                }`}
              >
                <div className="aspect-[8.5/11] bg-slate-100 rounded-lg overflow-hidden mb-3">
                  <img
                    src={sample.image || "/placeholder.svg"}
                    alt={sample.title}
                    className="w-full h-full object-cover"
                  />
                </div>
                <p className="text-sm font-medium text-slate-900 text-center">{sample.title}</p>
              </motion.div>
            ))}
          </div>
        </div>
      </section>

      {/* Developers strip */}
      <section className="py-20 px-4 sm:px-6 lg:px-8">
        <div className="max-w-[1200px] mx-auto">
          <div className="text-center mb-12">
            <h2 className="font-display font-bold text-4xl sm:text-5xl mb-4 text-white">Open API</h2>
            <p className="text-lg text-slate-400">Honest rate limits. Webhooks.</p>
          </div>

          <div className="space-y-8 max-w-4xl mx-auto">
            <div>
              <div className="flex items-center gap-2 mb-3">
                <Code className="w-5 h-5 text-cyan-400" />
                <h3 className="font-mono text-sm text-cyan-400">POST /v1/reports</h3>
              </div>
              <CodeTabs pythonCode={pythonCode} javascriptCode={javascriptCode} />
            </div>

            <div>
              <div className="flex items-center gap-2 mb-3">
                <Code className="w-5 h-5 text-cyan-400" />
                <h3 className="font-mono text-sm text-cyan-400">GET /v1/reports/:id</h3>
              </div>
              <CodeTabs pythonCode={pythonCodeGet} javascriptCode={javascriptCodeGet} />
            </div>
          </div>
        </div>
      </section>

      {/* Pricing */}
      <section className="relative py-32 px-4 sm:px-6 lg:px-8 overflow-hidden">
        {/* Grayscale data/tech background */}
        <div className="absolute inset-0 z-0">
          <img
            src="/abstract-data-visualization-network-nodes-connecti.jpg"
            alt=""
            className="w-full h-full object-cover grayscale opacity-[0.08]"
          />
          <div className="absolute inset-0 bg-gradient-to-b from-white/90 via-white/70 to-white/90" />
        </div>

        <div className="max-w-[1200px] mx-auto relative z-10">
          <div className="text-center mb-16">
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              whileInView={{ opacity: 1, y: 0 }}
              viewport={{ once: true }}
              transition={{ duration: 0.2 }}
            >
              <div className="inline-flex items-center gap-2 px-4 py-2 rounded-full bg-purple-100 border border-purple-200 mb-4">
                <Sparkles className="w-4 h-4 text-purple-600" />
                <span className="text-sm font-medium text-purple-700">Transparent pricing, no surprises</span>
              </div>
              <h2 className="font-pricing font-bold text-5xl sm:text-6xl mb-6 text-slate-900">Pick your plan</h2>
              <p className="text-xl text-slate-600 max-w-2xl mx-auto">Start free. Scale as you grow. Cancel anytime.</p>
            </motion.div>
          </div>

          <div className="grid md:grid-cols-4 gap-8">
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              whileInView={{ opacity: 1, y: 0 }}
              viewport={{ once: true }}
              transition={{ duration: 0.2 }}
              className="bg-white rounded-2xl border-2 border-slate-200 p-8 hover:border-purple-300 hover:shadow-xl transition-all"
            >
              <div className="mb-6">
                <h3 className="font-pricing font-bold text-xl mb-2 text-slate-900">Starter</h3>
                <p className="text-sm text-slate-600">Perfect for solo agents</p>
              </div>
              <div className="mb-6">
                <span className="font-pricing font-bold text-5xl text-slate-900">$99</span>
                <span className="text-slate-600">/mo</span>
              </div>
              <ul className="space-y-3 mb-8">
                <li className="flex items-start gap-2 text-sm text-slate-700">
                  <Check className="w-5 h-5 text-purple-600 shrink-0 mt-0.5" />
                  <span>50 reports per month</span>
                </li>
                <li className="flex items-start gap-2 text-sm text-slate-700">
                  <Check className="w-5 h-5 text-purple-600 shrink-0 mt-0.5" />
                  <span>3 scheduled reports</span>
                </li>
                <li className="flex items-start gap-2 text-sm text-slate-700">
                  <Check className="w-5 h-5 text-purple-600 shrink-0 mt-0.5" />
                  <span>Your logo & branding</span>
                </li>
                <li className="flex items-start gap-2 text-sm text-slate-700">
                  <Check className="w-5 h-5 text-purple-600 shrink-0 mt-0.5" />
                  <span>Email delivery</span>
                </li>
              </ul>
              <Button className="w-full bg-slate-900 hover:bg-slate-800 text-white font-pricing">
                Start Free Trial
              </Button>
            </motion.div>

            <motion.div
              initial={{ opacity: 0, y: 20 }}
              whileInView={{ opacity: 1, y: 0 }}
              viewport={{ once: true }}
              transition={{ duration: 0.2, delay: 0.05 }}
              className="bg-gradient-to-br from-purple-600 to-purple-700 rounded-2xl border-2 border-purple-500 p-8 relative overflow-hidden shadow-2xl shadow-purple-500/25 transform md:scale-105"
            >
              <div className="absolute top-4 right-4 bg-orange-500 text-white text-xs font-bold px-3 py-1 rounded-full">
                POPULAR
              </div>
              <div className="mb-6">
                <h3 className="font-pricing font-bold text-xl mb-2 text-white">Professional</h3>
                <p className="text-sm text-purple-100">For growing teams</p>
              </div>
              <div className="mb-6">
                <span className="font-pricing font-bold text-5xl text-white">$299</span>
                <span className="text-purple-100">/mo</span>
              </div>
              <ul className="space-y-3 mb-8">
                <li className="flex items-start gap-2 text-sm text-white">
                  <Check className="w-5 h-5 text-orange-400 shrink-0 mt-0.5" />
                  <span>200 reports per month</span>
                </li>
                <li className="flex items-start gap-2 text-sm text-white">
                  <Check className="w-5 h-5 text-orange-400 shrink-0 mt-0.5" />
                  <span>Unlimited schedules</span>
                </li>
                <li className="flex items-start gap-2 text-sm text-white">
                  <Check className="w-5 h-5 text-orange-400 shrink-0 mt-0.5" />
                  <span>Priority support</span>
                </li>
                <li className="flex items-start gap-2 text-sm text-white">
                  <Check className="w-5 h-5 text-orange-400 shrink-0 mt-0.5" />
                  <span>API access</span>
                </li>
                <li className="flex items-start gap-2 text-sm text-white">
                  <Check className="w-5 h-5 text-orange-400 shrink-0 mt-0.5" />
                  <span>Webhook integrations</span>
                </li>
              </ul>
              <Button className="w-full bg-white hover:bg-purple-50 text-purple-700 font-pricing font-bold">
                Start Free Trial
              </Button>
            </motion.div>

            <motion.div
              initial={{ opacity: 0, y: 20 }}
              whileInView={{ opacity: 1, y: 0 }}
              viewport={{ once: true }}
              transition={{ duration: 0.2, delay: 0.1 }}
              className="bg-white rounded-2xl border-2 border-slate-200 p-8 hover:border-purple-300 hover:shadow-xl transition-all"
            >
              <div className="mb-6">
                <h3 className="font-pricing font-bold text-xl mb-2 text-slate-900">Enterprise</h3>
                <p className="text-sm text-slate-600">For large brokerages</p>
              </div>
              <div className="mb-6">
                <span className="font-pricing font-bold text-5xl text-slate-900">$999</span>
                <span className="text-slate-600">/mo</span>
              </div>
              <ul className="space-y-3 mb-8">
                <li className="flex items-start gap-2 text-sm text-slate-700">
                  <Check className="w-5 h-5 text-purple-600 shrink-0 mt-0.5" />
                  <span>Unlimited reports</span>
                </li>
                <li className="flex items-start gap-2 text-sm text-slate-700">
                  <Check className="w-5 h-5 text-purple-600 shrink-0 mt-0.5" />
                  <span>Team management</span>
                </li>
                <li className="flex items-start gap-2 text-sm text-slate-700">
                  <Check className="w-5 h-5 text-purple-600 shrink-0 mt-0.5" />
                  <span>Advanced analytics</span>
                </li>
                <li className="flex items-start gap-2 text-sm text-slate-700">
                  <Check className="w-5 h-5 text-purple-600 shrink-0 mt-0.5" />
                  <span>Dedicated support</span>
                </li>
                <li className="flex items-start gap-2 text-sm text-slate-700">
                  <Check className="w-5 h-5 text-purple-600 shrink-0 mt-0.5" />
                  <span>Custom integrations</span>
                </li>
              </ul>
              <Button className="w-full bg-slate-900 hover:bg-slate-800 text-white font-pricing">
                Start Free Trial
              </Button>
            </motion.div>

            <motion.div
              initial={{ opacity: 0, y: 20 }}
              whileInView={{ opacity: 1, y: 0 }}
              viewport={{ once: true }}
              transition={{ duration: 0.2, delay: 0.15 }}
              className="bg-gradient-to-br from-slate-900 to-slate-800 rounded-2xl border-2 border-slate-700 p-8 relative overflow-hidden"
            >
              <div className="absolute top-0 right-0 w-32 h-32 bg-orange-500/10 rounded-full blur-3xl" />
              <div className="mb-6 relative">
                <h3 className="font-pricing font-bold text-xl mb-2 text-white">Title Partner</h3>
                <p className="text-sm text-slate-400">Co-branded solution</p>
              </div>
              <div className="mb-6 relative">
                <span className="font-pricing font-bold text-4xl text-white">Custom</span>
              </div>
              <ul className="space-y-3 mb-8 relative">
                <li className="flex items-start gap-2 text-sm text-slate-300">
                  <Check className="w-5 h-5 text-orange-400 shrink-0 mt-0.5" />
                  <span>Co-branded PDFs</span>
                </li>
                <li className="flex items-start gap-2 text-sm text-slate-300">
                  <Check className="w-5 h-5 text-orange-400 shrink-0 mt-0.5" />
                  <span>Credits & ledger</span>
                </li>
                <li className="flex items-start gap-2 text-sm text-slate-300">
                  <Check className="w-5 h-5 text-orange-400 shrink-0 mt-0.5" />
                  <span>Admin console</span>
                </li>
                <li className="flex items-start gap-2 text-sm text-slate-300">
                  <Check className="w-5 h-5 text-orange-400 shrink-0 mt-0.5" />
                  <span>White-label option</span>
                </li>
              </ul>
              <Button className="w-full bg-orange-500 hover:bg-orange-600 text-white font-pricing font-bold">
                Contact Sales
              </Button>
            </motion.div>
          </div>

          <motion.div
            initial={{ opacity: 0, y: 20 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true }}
            transition={{ duration: 0.2, delay: 0.2 }}
            className="mt-12 text-center"
          >
            <p className="text-sm text-slate-600">
              All plans include 14-day free trial • No credit card required • Cancel anytime
            </p>
          </motion.div>
        </div>
      </section>

      {/* Security/Compliance */}
      <section className="py-20 px-4 sm:px-6 lg:px-8">
        <div className="max-w-[1200px] mx-auto">
          <div className="bg-white/5 backdrop-blur-sm rounded-xl border border-white/10 p-8">
            <div className="flex flex-col md:flex-row items-center justify-between gap-8">
              <div className="flex items-center gap-4">
                <div className="w-12 h-12 rounded-xl bg-cyan-500/10 flex items-center justify-center shrink-0">
                  <Check className="w-6 h-6 text-cyan-400" />
                </div>
                <div>
                  <h3 className="font-display font-bold text-xl mb-1 text-white">Security & Compliance</h3>
                  <p className="text-sm text-slate-400">
                    SOC-ready practices, RLS per tenant, unsubscribe & suppression
                  </p>
                </div>
              </div>
              <div className="flex items-center gap-8 shrink-0">
                <div className="text-center">
                  <div className="font-display font-bold text-2xl text-white font-mono">99.9%</div>
                  <div className="text-xs text-slate-400">Uptime</div>
                </div>
                <div className="text-center">
                  <div className="font-display font-bold text-2xl text-white font-mono">256</div>
                  <div className="text-xs text-slate-400">Encryption</div>
                </div>
                <div className="text-center">
                  <div className="font-display font-bold text-2xl text-white">SOC 2</div>
                  <div className="text-xs text-slate-400">Ready</div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* CTA Footer */}
      <section className="py-24 px-4 sm:px-6 lg:px-8 bg-gradient-to-br from-purple-600 via-purple-700 to-orange-600 relative overflow-hidden">
        <div className="absolute inset-0 opacity-10">
          <div className="absolute top-0 left-1/4 w-96 h-96 bg-white rounded-full blur-[120px]" />
          <div className="absolute bottom-0 right-1/4 w-96 h-96 bg-orange-300 rounded-full blur-[120px]" />
        </div>

        <div className="max-w-[1200px] mx-auto text-center relative z-10">
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true }}
            transition={{ duration: 0.2 }}
          >
            <h2 className="font-display font-bold text-4xl sm:text-5xl lg:text-6xl mb-6 text-balance text-white">
              Report once. Repeat forever.
            </h2>
            <p className="text-xl text-purple-100 mb-8 text-pretty max-w-3xl mx-auto">
              Your brand. Every report. Schedules that never forget. From MLS to inbox in one tap.
            </p>
            <div className="flex flex-col sm:flex-row items-center justify-center gap-4">
              <Button size="lg" className="bg-white text-purple-700 hover:bg-purple-50 text-lg px-8 shadow-xl">
                Start Free Trial
                <ArrowRight className="w-5 h-5 ml-2" />
              </Button>
              <Button
                size="lg"
                variant="ghost"
                className="text-lg px-8 text-white hover:bg-white/10 border-2 border-white/30"
              >
                Schedule Demo
              </Button>
            </div>
            <p className="text-sm text-purple-100 mt-6">Agents love it. Title teams scale it.</p>
          </motion.div>
        </div>
      </section>

      {/* Footer */}
      <footer className="border-t border-white/10 bg-[#0B1220]">
        <div className="max-w-[1200px] mx-auto px-4 sm:px-6 lg:px-8 py-12">
          <div className="flex flex-col sm:flex-row justify-between items-center gap-6 text-center sm:text-left">
            <div className="flex items-center gap-2">
              <div className="w-6 h-6 rounded-lg bg-gradient-to-br from-cyan-500 to-violet-500 flex items-center justify-center">
                <span className="text-white font-display font-bold text-sm">R</span>
              </div>
              <span className="text-sm text-slate-400">© 2025 TrendyReports</span>
            </div>
            <div className="flex items-center gap-6 text-sm text-slate-400">
              <a href="#docs" className="hover:text-white transition-colors">
                Docs
              </a>
              <a href="#status" className="hover:text-white transition-colors">
                Status
              </a>
              <a href="#security" className="hover:text-white transition-colors">
                Security
              </a>
              <a href="#privacy" className="hover:text-white transition-colors">
                Privacy
              </a>
              <a href="#terms" className="hover:text-white transition-colors">
                Terms
              </a>
            </div>
          </div>
        </div>
      </footer>
    </div>
  )
}

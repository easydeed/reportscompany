"use client"

import { Button } from "@/components/ui/button"
import { Navbar } from "@/components/navbar"
import { Footer } from "@/components/footer"
import { motion } from "framer-motion"
import { ArrowRight, Check, Shield, FileCheck, TrendingUp, Star, Quote, ChevronRight, Play } from 'lucide-react'
import { useState } from "react"
import Link from "next/link"

export function MarketingHome() {
  const [currentSample, setCurrentSample] = useState(0)

  const samples = [
    { title: "Market Snapshot", desc: "Area-wide trends with charts" },
    { title: "New Listings Gallery", desc: "Photo-rich property showcase" },
    { title: "Featured Listings", desc: "Curated property highlights" },
    { title: "Neighborhood Analysis", desc: "Localized market intelligence" },
    { title: "Price Trends", desc: "Historical data visualization" },
  ]

  return (
    <div className="min-h-screen bg-white">
      <Navbar />

      {/* Hero - Professional and direct */}
      <section className="relative pt-32 pb-24 px-4 sm:px-6 lg:px-8">
        <div className="max-w-[1200px] mx-auto">
          <div className="grid lg:grid-cols-2 gap-16 items-center">
            <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.3 }}>
              <div className="inline-flex items-center gap-2 bg-purple-50 border border-purple-200 rounded-full px-4 py-2 mb-6">
                <div className="w-2 h-2 bg-purple-600 rounded-full animate-pulse" />
                <span className="text-sm font-semibold text-purple-900">Trusted by 1,200+ real estate professionals</span>
              </div>
              <h1 className="font-display font-semibold text-5xl sm:text-6xl lg:text-7xl mb-6 text-slate-900 leading-[1.05]">
                Stop wasting time on market reports
              </h1>
              <p className="text-xl text-slate-600 mb-8 leading-relaxed max-w-xl">
                Generate beautiful, branded market reports in 30 seconds. Automate delivery. Recover 3+ hours every week to focus on what actually closes deals.
              </p>
              <div className="flex flex-col sm:flex-row gap-4 mb-8">
                <Button
                  size="lg"
                  className="bg-gradient-to-r from-purple-600 to-purple-700 hover:from-purple-700 hover:to-purple-800 text-white text-lg px-8 h-14 shadow-lg hover:shadow-xl transition-all"
                  asChild
                >
                  <Link href="/login">
                    Start Free Trial — No Credit Card
                    <ArrowRight className="w-5 h-5 ml-2" />
                  </Link>
                </Button>
                <Button
                  size="lg"
                  variant="outline"
                  className="text-lg px-8 h-14 border-slate-300 hover:bg-slate-50"
                  asChild
                >
                  <Link href="#demo">
                    <Play className="w-5 h-5 mr-2" />
                    Watch 60-Second Demo
                  </Link>
                </Button>
              </div>
              <div className="flex flex-wrap items-center gap-x-6 gap-y-2 text-sm text-slate-600">
                <div className="flex items-center gap-2">
                  <Check className="w-4 h-4 text-green-600" />
                  <span>14-day free trial</span>
                </div>
                <div className="flex items-center gap-2">
                  <Check className="w-4 h-4 text-green-600" />
                  <span>Setup in 5 minutes</span>
                </div>
                <div className="flex items-center gap-2">
                  <Check className="w-4 h-4 text-green-600" />
                  <span>Cancel anytime</span>
                </div>
              </div>
            </motion.div>

            <motion.div
              initial={{ opacity: 0, scale: 0.95 }}
              animate={{ opacity: 1, scale: 1 }}
              transition={{ duration: 0.4, delay: 0.1 }}
              className="relative"
            >
              {/* Product screenshot - actual report interface */}
              <div className="bg-white rounded-xl shadow-2xl border border-slate-200 overflow-hidden">
                <img
                  src="/placeholder.svg?height=600&width=800&text=Product+Dashboard+Screenshot"
                  alt="TrendyReports Dashboard showing automated report scheduling"
                  className="w-full"
                />
              </div>
            </motion.div>
          </div>
        </div>
      </section>

      {/* Trust Bar */}
      <section className="py-12 px-4 sm:px-6 lg:px-8 border-y border-slate-200 bg-slate-50">
        <div className="max-w-[1200px] mx-auto">
          <div className="grid grid-cols-2 md:grid-cols-4 gap-8 text-center">
            <div>
              <div className="font-display font-bold text-4xl text-slate-900 mb-1">1,200+</div>
              <div className="text-sm text-slate-600">Active agents & brokers</div>
            </div>
            <div>
              <div className="font-display font-bold text-4xl text-slate-900 mb-1">50K+</div>
              <div className="text-sm text-slate-600">Reports generated monthly</div>
            </div>
            <div>
              <div className="font-display font-bold text-4xl text-slate-900 mb-1">30s</div>
              <div className="text-sm text-slate-600">Average generation time</div>
            </div>
            <div>
              <div className="font-display font-bold text-4xl text-slate-900 mb-1">98%</div>
              <div className="text-sm text-slate-600">Customer satisfaction</div>
            </div>
          </div>
        </div>
      </section>

      <section className="py-24 px-4 sm:px-6 lg:px-8 bg-gradient-to-br from-purple-50 via-white to-orange-50">
        <div className="max-w-[1200px] mx-auto">
          <div className="text-center mb-16">
            <h2 className="font-display font-semibold text-4xl sm:text-5xl mb-4 text-slate-900">
              The real cost of manual reports
            </h2>
            <p className="text-xl text-slate-600 max-w-3xl mx-auto">Stop trading your time for repetitive work. Automate reports and focus on what actually grows your business.</p>
          </div>

          <div className="grid lg:grid-cols-2 gap-12 items-center">
            {/* Visual comparison */}
            <div className="space-y-6">
              <div className="bg-white rounded-2xl border-2 border-red-200 p-8 relative">
                <div className="absolute -top-3 left-6 bg-red-100 text-red-700 text-xs font-bold px-3 py-1 rounded-full">
                  OLD WAY
                </div>
                <div className="space-y-4 mt-2">
                  <div className="flex items-center gap-3">
                    <div className="text-2xl">⏱️</div>
                    <div>
                      <div className="font-semibold text-slate-900">3+ hours per week</div>
                      <div className="text-sm text-slate-600">Export, format, send — manually</div>
                    </div>
                  </div>
                  <div className="flex items-center gap-3">
                    <div className="text-2xl">😓</div>
                    <div>
                      <div className="font-semibold text-slate-900">Inconsistent branding</div>
                      <div className="text-sm text-slate-600">Looks different every time</div>
                    </div>
                  </div>
                  <div className="flex items-center gap-3">
                    <div className="text-2xl">📅</div>
                    <div>
                      <div className="font-semibold text-slate-900">Missed schedules</div>
                      <div className="text-sm text-slate-600">Forget to send, lose credibility</div>
                    </div>
                  </div>
                </div>
              </div>

              <div className="bg-white rounded-2xl border-2 border-green-300 p-8 relative shadow-lg">
                <div className="absolute -top-3 left-6 bg-gradient-to-r from-purple-600 to-purple-700 text-white text-xs font-bold px-3 py-1 rounded-full">
                  WITH TRENDYREPORTS
                </div>
                <div className="space-y-4 mt-2">
                  <div className="flex items-center gap-3">
                    <div className="text-2xl">⚡</div>
                    <div>
                      <div className="font-semibold text-slate-900">30 seconds per report</div>
                      <div className="text-sm text-slate-600">Automated data, instant generation</div>
                    </div>
                  </div>
                  <div className="flex items-center gap-3">
                    <div className="text-2xl">✨</div>
                    <div>
                      <div className="font-semibold text-slate-900">Perfect every time</div>
                      <div className="text-sm text-slate-600">Your brand, professional layout</div>
                    </div>
                  </div>
                  <div className="flex items-center gap-3">
                    <div className="text-2xl">🔄</div>
                    <div>
                      <div className="font-semibold text-slate-900">Never miss a send</div>
                      <div className="text-sm text-slate-600">Set once, runs automatically</div>
                    </div>
                  </div>
                </div>
              </div>
            </div>

            {/* ROI Calculator */}
            <div className="bg-gradient-to-br from-slate-900 to-slate-800 rounded-3xl p-10 text-white relative overflow-hidden">
              <div className="absolute top-0 right-0 w-64 h-64 bg-purple-500/10 rounded-full blur-3xl" />
              <div className="relative z-10">
                <div className="text-purple-300 font-medium mb-2">Time Recovered Annually</div>
                <div className="font-display font-bold text-6xl mb-8">150 hours</div>
                
                <div className="space-y-6 mb-8">
                  <div className="flex justify-between items-center pb-4 border-b border-white/10">
                    <span className="text-slate-300">Hours saved per week</span>
                    <span className="font-bold text-xl">3 hours</span>
                  </div>
                  <div className="flex justify-between items-center pb-4 border-b border-white/10">
                    <span className="text-slate-300">Weeks per year</span>
                    <span className="font-bold text-xl">× 50</span>
                  </div>
                  <div className="flex justify-between items-center pb-4 border-b border-white/10">
                    <span className="text-slate-300">Your hourly rate</span>
                    <span className="font-bold text-xl">$150</span>
                  </div>
                </div>

                <div className="bg-white/10 backdrop-blur-sm rounded-2xl p-6 border border-white/20">
                  <div className="text-purple-300 text-sm font-medium mb-1">Recovered Value</div>
                  <div className="font-display font-bold text-5xl text-transparent bg-clip-text bg-gradient-to-r from-green-400 to-emerald-400">
                    $22,050
                  </div>
                  <div className="text-slate-400 text-sm mt-2">That's 62x more than your annual subscription</div>
                </div>

                <div className="mt-8 pt-6 border-t border-white/10">
                  <div className="text-sm text-slate-400">
                    Based on 3 hours/week @ $150/hour. Your actual ROI may be higher.
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* Product Screenshots Section - Actual interface */}
      <section id="demo" className="py-24 px-4 sm:px-6 lg:px-8 bg-slate-50">
        <div className="max-w-[1200px] mx-auto">
          <div className="text-center mb-16">
            <h2 className="font-display font-semibold text-4xl sm:text-5xl mb-4 text-slate-900">
              See how it works
            </h2>
            <p className="text-xl text-slate-600">Three steps. Fully automated. Always professional.</p>
          </div>

          {/* Video Demo */}
          <div className="mb-20">
            <div className="max-w-4xl mx-auto bg-white rounded-2xl shadow-2xl border border-slate-200 overflow-hidden">
              <div className="aspect-video bg-slate-100 relative">
                <div className="absolute inset-0 flex items-center justify-center">
                  <button className="w-20 h-20 rounded-full bg-purple-600 hover:bg-purple-700 flex items-center justify-center shadow-2xl hover:scale-110 transition-transform">
                    <Play className="w-8 h-8 text-white ml-1" />
                  </button>
                </div>
                <img
                  src="/placeholder.svg?height=720&width=1280&text=Demo+Video:+Create+Report+in+60+Seconds"
                  alt="Product demo video"
                  className="w-full h-full object-cover"
                />
              </div>
            </div>
            <p className="text-center mt-4 text-slate-600">Watch a real agent create a market report in under 60 seconds</p>
          </div>

          {/* Product Screenshots */}
          <div className="grid md:grid-cols-3 gap-8">
            <div className="bg-white rounded-2xl border border-slate-200 overflow-hidden shadow-lg hover:shadow-xl transition-shadow">
              <img
                src="/placeholder.svg?height=400&width=600&text=Screenshot:+Select+Area+%26+Type"
                alt="Select market area and report type"
                className="w-full"
              />
              <div className="p-6">
                <div className="w-10 h-10 rounded-xl bg-purple-100 flex items-center justify-center mb-4">
                  <span className="font-bold text-purple-600">1</span>
                </div>
                <h3 className="font-display font-semibold text-xl text-slate-900 mb-2">Choose data source</h3>
                <p className="text-slate-600">Select city, ZIP codes, or custom polygons. Pick report type. We handle the MLS connection.</p>
              </div>
            </div>

            <div className="bg-white rounded-2xl border border-slate-200 overflow-hidden shadow-lg hover:shadow-xl transition-shadow">
              <img
                src="/placeholder.svg?height=400&width=600&text=Screenshot:+Set+Schedule"
                alt="Configure automated schedule"
                className="w-full"
              />
              <div className="p-6">
                <div className="w-10 h-10 rounded-xl bg-purple-100 flex items-center justify-center mb-4">
                  <span className="font-bold text-purple-600">2</span>
                </div>
                <h3 className="font-display font-semibold text-xl text-slate-900 mb-2">Set schedule</h3>
                <p className="text-slate-600">Weekly, monthly, or custom cadence. Add your branding. Configure delivery settings.</p>
              </div>
            </div>

            <div className="bg-white rounded-2xl border border-slate-200 overflow-hidden shadow-lg hover:shadow-xl transition-shadow">
              <img
                src="/placeholder.svg?height=400&width=600&text=Screenshot:+Beautiful+Report+Output"
                alt="Generated professional report"
                className="w-full"
              />
              <div className="p-6">
                <div className="w-10 h-10 rounded-xl bg-purple-100 flex items-center justify-center mb-4">
                  <span className="font-bold text-purple-600">3</span>
                </div>
                <h3 className="font-display font-semibold text-xl text-slate-900 mb-2">Deliver automatically</h3>
                <p className="text-slate-600">Reports generate and send on schedule. PDF links, email campaigns, or direct download.</p>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* For Brokerages/Title Companies */}
      <section id="for-affiliates" className="py-24 px-4 sm:px-6 lg:px-8">
        <div className="max-w-[1200px] mx-auto">
          <div className="grid lg:grid-cols-2 gap-16 items-center">
            <div>
              <div className="inline-flex items-center gap-2 bg-purple-50 border border-purple-200 rounded-full px-4 py-2 mb-6">
                <span className="text-sm font-semibold text-purple-900">FOR BROKERAGES & TITLE COMPANIES</span>
              </div>
              <h2 className="font-display font-semibold text-4xl sm:text-5xl mb-6 text-slate-900">
                Sponsor agents. Scale touchpoints. Track ROI.
              </h2>
              <p className="text-xl text-slate-600 mb-8 leading-relaxed">
                Provide unlimited report access to your entire agent roster under your brand. One flat rate. No per-seat fees. Full usage analytics.
              </p>

              <div className="space-y-6 mb-8">
                <div className="flex items-start gap-4">
                  <div className="w-12 h-12 rounded-xl bg-purple-100 flex items-center justify-center shrink-0">
                    <Check className="w-6 h-6 text-purple-600" />
                  </div>
                  <div>
                    <div className="font-semibold text-lg text-slate-900 mb-1">Co-branded reports</div>
                    <div className="text-slate-600">Your logo, colors, and contact info on every report. TrendyReports stays invisible.</div>
                  </div>
                </div>
                <div className="flex items-start gap-4">
                  <div className="w-12 h-12 rounded-xl bg-purple-100 flex items-center justify-center shrink-0">
                    <Check className="w-6 h-6 text-purple-600" />
                  </div>
                  <div>
                    <div className="font-semibold text-lg text-slate-900 mb-1">Unlimited agent seats</div>
                    <div className="text-slate-600">Sponsor 10 agents or 1,000. Same price. No per-user charges.</div>
                  </div>
                </div>
                <div className="flex items-start gap-4">
                  <div className="w-12 h-12 rounded-xl bg-purple-100 flex items-center justify-center shrink-0">
                    <Check className="w-6 h-6 text-purple-600" />
                  </div>
                  <div>
                    <div className="font-semibold text-lg text-slate-900 mb-1">Usage dashboard</div>
                    <div className="text-slate-600">See which agents are active, reports generated, and engagement metrics.</div>
                  </div>
                </div>
              </div>

              <Button size="lg" className="bg-purple-600 hover:bg-purple-700 text-white h-14 px-8" asChild>
                <a href="mailto:enterprise@trendyreports.com">
                  Request Enterprise Demo
                  <ChevronRight className="w-5 h-5 ml-2" />
                </a>
              </Button>
            </div>

            <div className="bg-white rounded-2xl border border-slate-200 overflow-hidden shadow-2xl">
              <img
                src="/placeholder.svg?height=600&width=800&text=Admin+Dashboard+Screenshot"
                alt="Enterprise admin dashboard showing agent activity and report analytics"
                className="w-full"
              />
            </div>
          </div>
        </div>
      </section>

      {/* Social Proof - Testimonials */}
      <section className="py-24 px-4 sm:px-6 lg:px-8 bg-slate-50">
        <div className="max-w-[1200px] mx-auto">
          <div className="text-center mb-16">
            <h2 className="font-display font-semibold text-4xl sm:text-5xl mb-4 text-slate-900">
              Trusted by top-producing agents
            </h2>
            <p className="text-xl text-slate-600">Real results from real estate professionals</p>
          </div>

          <div className="grid md:grid-cols-3 gap-8">
            <div className="bg-white rounded-2xl border border-slate-200 p-8">
              <div className="flex gap-1 mb-6">
                {[...Array(5)].map((_, i) => (
                  <Star key={i} className="w-5 h-5 fill-orange-400 text-orange-400" />
                ))}
              </div>
              <p className="text-slate-700 text-lg leading-relaxed mb-6">
                "TrendyReports recovered 3+ hours every week. That's billable time I now spend on client meetings and prospecting. ROI is 20x my subscription cost."
              </p>
              <div className="flex items-center gap-3">
                <div className="w-12 h-12 rounded-full bg-purple-600 flex items-center justify-center text-white font-bold">
                  JM
                </div>
                <div>
                  <div className="font-semibold text-slate-900">Jessica Martinez</div>
                  <div className="text-sm text-slate-600">Keller Williams, Austin TX</div>
                </div>
              </div>
            </div>

            <div className="bg-white rounded-2xl border border-slate-200 p-8">
              <div className="flex gap-1 mb-6">
                {[...Array(5)].map((_, i) => (
                  <Star key={i} className="w-5 h-5 fill-orange-400 text-orange-400" />
                ))}
              </div>
              <p className="text-slate-700 text-lg leading-relaxed mb-6">
                "We sponsor 40 agents under one plan. Every report carries our brand. The usage analytics show clear engagement. Best marketing investment we've made."
              </p>
              <div className="flex items-center gap-3">
                <div className="w-12 h-12 rounded-full bg-purple-600 flex items-center justify-center text-white font-bold">
                  RC
                </div>
                <div>
                  <div className="font-semibold text-slate-900">Robert Chen</div>
                  <div className="text-sm text-slate-600">Broker/Owner, Pacific Realty</div>
                </div>
              </div>
            </div>

            <div className="bg-white rounded-2xl border border-slate-200 p-8">
              <div className="flex gap-1 mb-6">
                {[...Array(5)].map((_, i) => (
                  <Star key={i} className="w-5 h-5 fill-orange-400 text-orange-400" />
                ))}
              </div>
              <p className="text-slate-700 text-lg leading-relaxed mb-6">
                "My clients forward the reports to their friends. The design is clean and the data is current. I close more referrals now than ever before."
              </p>
              <div className="flex items-center gap-3">
                <div className="w-12 h-12 rounded-full bg-purple-600 flex items-center justify-center text-white font-bold">
                  SP
                </div>
                <div>
                  <div className="font-semibold text-slate-900">Sarah Patel</div>
                  <div className="text-sm text-slate-600">RE/MAX, Denver CO</div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* Sample Reports */}
      <section id="sample-report" className="py-24 px-4 sm:px-6 lg:px-8">
        <div className="max-w-[1200px] mx-auto">
          <div className="text-center mb-16">
            <h2 className="font-display font-semibold text-4xl sm:text-5xl mb-4 text-slate-900">
              Professional reports. Every time.
            </h2>
            <p className="text-xl text-slate-600">8.5×11 print-ready PDFs with your branding</p>
          </div>

          <div className="grid md:grid-cols-5 gap-6">
            {samples.map((sample, idx) => (
              <button
                key={idx}
                onClick={() => setCurrentSample(idx)}
                className={`group bg-white rounded-xl border-2 transition-all hover:shadow-xl ${
                  currentSample === idx ? "border-purple-500 shadow-xl" : "border-slate-200"
                }`}
              >
                <div className="aspect-[8.5/11] bg-slate-50 rounded-t-xl overflow-hidden">
                  <img
                    src={`/ceholder-svg-key-su72x-height-1100-width-850-text-.jpg?key=su72x&height=1100&width=850&text=${encodeURIComponent(sample.title + ' Report')}`}
                    alt={sample.title}
                    className="w-full h-full object-cover group-hover:scale-105 transition-transform duration-300"
                  />
                </div>
                <div className="p-4 text-left">
                  <div className="font-semibold text-sm text-slate-900 mb-1">{sample.title}</div>
                  <div className="text-xs text-slate-600">{sample.desc}</div>
                </div>
              </button>
            ))}
          </div>

          <div className="mt-12 text-center">
            <Button size="lg" variant="outline" className="border-purple-300 text-purple-700 hover:bg-purple-50" asChild>
              <a href="/samples" target="_blank">
                View Full Sample Reports
                <ChevronRight className="w-5 h-5 ml-2" />
              </a>
            </Button>
          </div>
        </div>
      </section>

      {/* Integrations */}
      <section className="py-24 px-4 sm:px-6 lg:px-8 bg-slate-50">
        <div className="max-w-[1200px] mx-auto">
          <div className="text-center mb-16">
            <h2 className="font-display font-semibold text-4xl sm:text-5xl mb-4 text-slate-900">
              Integrates with your MLS
            </h2>
            <p className="text-xl text-slate-600">Connects to the data sources you already use</p>
          </div>

          <div className="grid grid-cols-2 md:grid-cols-4 gap-6">
            {["MLS Grid", "Zillow", "Realtor.com", "ListHub", "Zapier", "Mailchimp", "Salesforce", "HubSpot"].map((integration, idx) => (
              <div key={idx} className="bg-white rounded-xl border border-slate-200 p-6 text-center hover:border-purple-300 hover:shadow-lg transition-all">
                <div className="font-semibold text-slate-900">{integration}</div>
              </div>
            ))}
          </div>

          <div className="mt-12 text-center">
            <p className="text-slate-600">
              Need a custom integration?{" "}
              <a href="mailto:integrations@trendyreports.com" className="text-purple-600 hover:text-purple-700 font-semibold underline">
                Contact our team
              </a>
            </p>
          </div>
        </div>
      </section>

      {/* Pricing */}
      <section id="pricing" className="py-24 px-4 sm:px-6 lg:px-8">
        <div className="max-w-[1200px] mx-auto">
          <div className="text-center mb-16">
            <h2 className="font-display font-semibold text-4xl sm:text-5xl mb-4 text-slate-900">
              Simple, transparent pricing
            </h2>
            <p className="text-xl text-slate-600">Choose the plan that fits your business. Upgrade or downgrade anytime.</p>
          </div>

          <div className="grid md:grid-cols-3 gap-8 max-w-5xl mx-auto">
            {/* Starter */}
            <div className="bg-white rounded-3xl border border-slate-200 p-8 hover:border-purple-200 hover:shadow-lg transition-all">
              <div className="mb-6">
                <h3 className="font-display font-semibold text-2xl mb-2 text-slate-900">Starter</h3>
                <p className="text-slate-600">Try TrendyReports risk-free</p>
              </div>
              <div className="mb-6">
                <span className="font-display font-bold text-5xl text-slate-900">$0</span>
                <span className="text-slate-600 text-lg">/month</span>
              </div>
              <ul className="space-y-3 mb-8">
                <li className="flex items-start gap-3 text-sm">
                  <Check className="w-5 h-5 text-purple-600 shrink-0 mt-0.5" />
                  <span className="text-slate-700"><strong>50 reports</strong> per month</span>
                </li>
                <li className="flex items-start gap-3 text-sm">
                  <Check className="w-5 h-5 text-purple-600 shrink-0 mt-0.5" />
                  <span className="text-slate-700">Market snapshot templates</span>
                </li>
                <li className="flex items-start gap-3 text-sm">
                  <Check className="w-5 h-5 text-purple-600 shrink-0 mt-0.5" />
                  <span className="text-slate-700">Email & PDF delivery</span>
                </li>
                <li className="flex items-start gap-3 text-sm">
                  <Check className="w-5 h-5 text-purple-600 shrink-0 mt-0.5" />
                  <span className="text-slate-700">Basic branding options</span>
                </li>
              </ul>
              <Button className="w-full h-12" variant="outline" asChild>
                <Link href="/login">Get Started Free</Link>
              </Button>
            </div>

            {/* Pro - Most Popular */}
            <div className="bg-gradient-to-br from-purple-50 via-white to-white rounded-3xl border-2 border-purple-300 p-8 relative shadow-lg hover:shadow-xl transition-all transform hover:scale-105">
              <div className="absolute -top-4 left-1/2 -translate-x-1/2 bg-gradient-to-r from-purple-600 to-purple-700 text-white text-xs font-bold px-4 py-1.5 rounded-full shadow-lg">
                MOST POPULAR
              </div>
              <div className="mb-6">
                <h3 className="font-display font-semibold text-2xl mb-2 text-slate-900">Pro</h3>
                <p className="text-slate-700">For active agents and teams</p>
              </div>
              <div className="mb-6">
                <span className="font-display font-bold text-5xl text-slate-900">$299</span>
                <span className="text-slate-600 text-lg">/month</span>
              </div>
              <ul className="space-y-3 mb-8">
                <li className="flex items-start gap-3 text-sm">
                  <Check className="w-5 h-5 text-purple-600 shrink-0 mt-0.5" />
                  <span className="text-slate-700"><strong>300 reports</strong> per month</span>
                </li>
                <li className="flex items-start gap-3 text-sm">
                  <Check className="w-5 h-5 text-purple-600 shrink-0 mt-0.5" />
                  <span className="text-slate-700">All report types + galleries</span>
                </li>
                <li className="flex items-start gap-3 text-sm">
                  <Check className="w-5 h-5 text-purple-600 shrink-0 mt-0.5" />
                  <span className="text-slate-700">Automated scheduling</span>
                </li>
                <li className="flex items-start gap-3 text-sm">
                  <Check className="w-5 h-5 text-purple-600 shrink-0 mt-0.5" />
                  <span className="text-slate-700">Full white-label branding</span>
                </li>
                <li className="flex items-start gap-3 text-sm">
                  <Check className="w-5 h-5 text-purple-600 shrink-0 mt-0.5" />
                  <span className="text-slate-700">Priority support</span>
                </li>
              </ul>
              <Button className="w-full h-12 bg-gradient-to-r from-purple-600 to-purple-700 hover:from-purple-700 hover:to-purple-800 text-white shadow-lg" asChild>
                <Link href="/login">Start 14-Day Free Trial</Link>
              </Button>
            </div>

            {/* Team */}
            <div className="bg-white rounded-3xl border border-slate-200 p-8 hover:border-purple-200 hover:shadow-lg transition-all">
              <div className="mb-6">
                <h3 className="font-display font-semibold text-2xl mb-2 text-slate-900">Team</h3>
                <p className="text-slate-600">For brokerages & title companies</p>
              </div>
              <div className="mb-6">
                <span className="font-display font-bold text-5xl text-slate-900">$999</span>
                <span className="text-slate-600 text-lg">/month</span>
              </div>
              <ul className="space-y-3 mb-8">
                <li className="flex items-start gap-3 text-sm">
                  <Check className="w-5 h-5 text-purple-600 shrink-0 mt-0.5" />
                  <span className="text-slate-700"><strong>Unlimited reports</strong></span>
                </li>
                <li className="flex items-start gap-3 text-sm">
                  <Check className="w-5 h-5 text-purple-600 shrink-0 mt-0.5" />
                  <span className="text-slate-700">Unlimited agent seats</span>
                </li>
                <li className="flex items-start gap-3 text-sm">
                  <Check className="w-5 h-5 text-purple-600 shrink-0 mt-0.5" />
                  <span className="text-slate-700">Admin dashboard & analytics</span>
                </li>
                <li className="flex items-start gap-3 text-sm">
                  <Check className="w-5 h-5 text-purple-600 shrink-0 mt-0.5" />
                  <span className="text-slate-700">Co-branded reports</span>
                </li>
                <li className="flex items-start gap-3 text-sm">
                  <Check className="w-5 h-5 text-purple-600 shrink-0 mt-0.5" />
                  <span className="text-slate-700">Dedicated support manager</span>
                </li>
              </ul>
              <Button className="w-full h-12" variant="outline" asChild>
                <Link href="/login">Start 14-Day Free Trial</Link>
              </Button>
            </div>
          </div>

          <div className="mt-16 max-w-3xl mx-auto">
            <div className="grid md:grid-cols-2 gap-8 text-sm">
              <div>
                <h4 className="font-semibold text-slate-900 mb-2">All plans include:</h4>
                <ul className="space-y-1 text-slate-600">
                  <li>• 14-day free trial, no credit card</li>
                  <li>• Cancel or change plans anytime</li>
                  <li>• 99.9% uptime SLA</li>
                  <li>• SOC 2 Type II compliant</li>
                </ul>
              </div>
              <div>
                <h4 className="font-semibold text-slate-900 mb-2">Need something custom?</h4>
                <p className="text-slate-600 mb-2">Enterprise plans available with custom integrations, dedicated infrastructure, and volume pricing.</p>
                <a href="mailto:enterprise@trendyreports.com" className="text-purple-600 hover:text-purple-700 font-semibold underline">
                  Contact sales →
                </a>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* Security */}
      <section className="py-24 px-4 sm:px-6 lg:px-8 bg-slate-50">
        <div className="max-w-[1200px] mx-auto">
          <div className="text-center mb-16">
            <h2 className="font-display font-semibold text-4xl sm:text-5xl mb-4 text-slate-900">
              Enterprise-grade security
            </h2>
            <p className="text-xl text-slate-600">Bank-level protection for your data</p>
          </div>

          <div className="grid md:grid-cols-3 gap-8">
            <div className="bg-white rounded-2xl border border-slate-200 p-10 text-center">
              <div className="w-16 h-16 rounded-2xl bg-green-100 flex items-center justify-center mx-auto mb-6">
                <Shield className="w-8 h-8 text-green-600" />
              </div>
              <div className="font-display font-bold text-4xl text-slate-900 mb-2">SOC 2</div>
              <div className="text-slate-600">Type II compliant</div>
            </div>

            <div className="bg-white rounded-2xl border border-slate-200 p-10 text-center">
              <div className="w-16 h-16 rounded-2xl bg-blue-100 flex items-center justify-center mx-auto mb-6">
                <TrendingUp className="w-8 h-8 text-blue-600" />
              </div>
              <div className="font-display font-bold text-4xl text-slate-900 mb-2">99.9%</div>
              <div className="text-slate-600">Uptime SLA</div>
            </div>

            <div className="bg-white rounded-2xl border border-slate-200 p-10 text-center">
              <div className="w-16 h-16 rounded-2xl bg-purple-100 flex items-center justify-center mx-auto mb-6">
                <FileCheck className="w-8 h-8 text-purple-600" />
              </div>
              <div className="font-display font-bold text-4xl text-slate-900 mb-2">256-bit</div>
              <div className="text-slate-600">AES encryption</div>
            </div>
          </div>

          <div className="mt-12 text-center text-slate-600">
            <p>GDPR compliant • Row-level security • Automatic backups • Unsubscribe management</p>
          </div>
        </div>
      </section>

      {/* CTA */}
      <section className="py-24 px-4 sm:px-6 lg:px-8 bg-gradient-to-br from-purple-600 via-purple-700 to-purple-800 relative overflow-hidden">
        <div className="absolute inset-0 opacity-10">
          <div className="absolute inset-0" style={{ backgroundImage: 'radial-gradient(circle at 2px 2px, white 1px, transparent 0)', backgroundSize: '40px 40px' }} />
        </div>
        <div className="max-w-[1200px] mx-auto text-center relative z-10">
          <h2 className="font-display font-semibold text-4xl sm:text-5xl lg:text-6xl mb-6 text-white leading-tight">
            Ready to automate your market reports?
          </h2>
          <p className="text-xl text-purple-100 mb-8 max-w-3xl mx-auto leading-relaxed">
            Join 1,200+ agents who recovered 150+ hours per year. Start your 14-day free trial today — no credit card required.
          </p>
          <div className="flex flex-col sm:flex-row items-center justify-center gap-4">
            <Button size="lg" className="bg-white text-purple-700 hover:bg-purple-50 h-14 px-10 text-lg shadow-xl hover:shadow-2xl hover:scale-105 transition-all font-semibold" asChild>
              <Link href="/login">
                Start Free Trial
                <ArrowRight className="w-5 h-5 ml-2" />
              </Link>
            </Button>
            <Button
              size="lg"
              variant="ghost"
              className="text-white hover:bg-white/10 border-2 border-white/40 hover:border-white/60 h-14 px-10 text-lg transition-all"
              asChild
            >
              <a href="mailto:sales@trendyreports.com">Talk to Sales</a>
            </Button>
          </div>
          <div className="flex flex-wrap items-center justify-center gap-6 mt-8 text-sm text-purple-100">
            <div className="flex items-center gap-2">
              <Check className="w-4 h-4" />
              <span>No credit card required</span>
            </div>
            <div className="flex items-center gap-2">
              <Check className="w-4 h-4" />
              <span>Setup in 5 minutes</span>
            </div>
            <div className="flex items-center gap-2">
              <Check className="w-4 h-4" />
              <span>Cancel anytime</span>
            </div>
          </div>
        </div>
      </section>

      <Footer />
    </div>
  )
}

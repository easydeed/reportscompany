"use client"

import { Button } from "@/components/ui/button"
import { Navbar } from "@/components/navbar"
import { Footer } from "@/components/footer"
import { motion } from "framer-motion"
import {
  ArrowRight,
  Check,
  Shield,
  FileCheck,
  TrendingUp,
  Star,
  ChevronRight,
  Play,
  Clock,
  Palette,
  User,
  Building2,
} from "lucide-react"
import { useState } from "react"
import Link from "next/link"
import Image from "next/image"

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

      {/* 1. HERO - Who we are, what we do */}
      <section className="relative pt-32 pb-24 px-4 sm:px-6 lg:px-8">
        <div className="max-w-[1200px] mx-auto">
          <div className="grid lg:grid-cols-2 gap-16 items-center">
            <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.3 }}>
              <div className="inline-flex items-center gap-2 bg-purple-50 border border-purple-200 rounded-full px-4 py-2 mb-6">
                <div className="w-2 h-2 bg-purple-600 rounded-full animate-pulse" />
                <span className="text-sm font-semibold text-purple-900">
                  Trusted by 1,200+ real estate professionals
                </span>
              </div>
              <h1 className="font-display font-semibold text-5xl sm:text-6xl lg:text-7xl mb-6 text-slate-900 leading-[1.05]">
                Stop wasting time on market reports
              </h1>
              <p className="text-xl text-slate-600 mb-8 leading-relaxed max-w-xl">
                Generate beautiful, branded market reports in 30 seconds. Automate delivery. Recover 3+ hours every week
                to focus on what actually closes deals.
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
                  className="text-lg px-8 h-14 border-slate-300 hover:bg-slate-50 bg-transparent"
                  asChild
                >
                  <Link href="#demo">
                    <Play className="w-5 h-5 mr-2" />
                    Watch Demo
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
              <div className="bg-white rounded-xl shadow-2xl border border-slate-200 overflow-hidden">
                <img
                  src="/placeholder.svg?height=600&width=800&text=TrendyReports+Dashboard"
                  alt="TrendyReports Dashboard"
                  className="w-full"
                />
              </div>
            </motion.div>
          </div>
        </div>
      </section>

      {/* 2. TRUST BAR - Social proof numbers */}
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

      {/* 3. WHY CHOOSE US - Benefits with visual impact */}
      <section className="py-24 px-4 sm:px-6 lg:px-8 text-white overflow-hidden relative">
        <div className="absolute inset-0">
          <Image src="/modern-luxury-real-estate-office-interior-with-gla.jpg" alt="" fill className="object-cover" />
          <div className="absolute inset-0 bg-gradient-to-br from-purple-900/95 via-slate-900/90 to-slate-900/95" />
        </div>
        <div className="absolute inset-0 overflow-hidden">
          <div className="absolute top-0 left-1/4 w-96 h-96 bg-purple-500/20 rounded-full blur-3xl" />
          <div className="absolute bottom-0 right-1/4 w-96 h-96 bg-orange-500/10 rounded-full blur-3xl" />
        </div>

        <div className="max-w-[1200px] mx-auto relative z-10">
          <div className="text-center mb-16">
            <p className="text-purple-400 font-medium uppercase tracking-wider text-sm mb-4">
              Built for top performers
            </p>
            <h2 className="font-display font-semibold text-4xl sm:text-5xl mb-4">Why top producers choose us</h2>
            <p className="text-xl text-slate-400 max-w-2xl mx-auto">
              The tools you need to stay top-of-mind with every client, every week.
            </p>
          </div>

          <div className="grid md:grid-cols-3 gap-6">
            <div className="group relative bg-gradient-to-br from-purple-500/10 to-purple-600/5 backdrop-blur-sm rounded-3xl border border-purple-500/20 p-8 hover:border-purple-500/40 transition-all duration-300 hover:-translate-y-1">
              <div className="absolute inset-0 bg-gradient-to-br from-purple-500/5 to-transparent rounded-3xl opacity-0 group-hover:opacity-100 transition-opacity" />
              <div className="relative">
                <div className="w-16 h-16 rounded-2xl bg-gradient-to-br from-purple-500 to-purple-600 flex items-center justify-center mb-6 shadow-lg shadow-purple-500/25">
                  <Clock className="w-8 h-8 text-white" />
                </div>
                <h3 className="font-display font-semibold text-2xl text-white mb-3">Set it and forget it</h3>
                <p className="text-slate-400 leading-relaxed text-lg">
                  Configure once. Reports generate and deliver automatically every week, month, or on your custom
                  schedule.
                </p>
                <div className="mt-6 pt-6 border-t border-purple-500/20">
                  <div className="flex items-center gap-2 text-purple-400">
                    <Check className="w-5 h-5" />
                    <span className="text-sm">Automated delivery</span>
                  </div>
                </div>
              </div>
            </div>

            <div className="group relative bg-gradient-to-br from-orange-500/10 to-orange-600/5 backdrop-blur-sm rounded-3xl border border-orange-500/20 p-8 hover:border-orange-500/40 transition-all duration-300 hover:-translate-y-1">
              <div className="absolute inset-0 bg-gradient-to-br from-orange-500/5 to-transparent rounded-3xl opacity-0 group-hover:opacity-100 transition-opacity" />
              <div className="relative">
                <div className="w-16 h-16 rounded-2xl bg-gradient-to-br from-orange-500 to-orange-600 flex items-center justify-center mb-6 shadow-lg shadow-orange-500/25">
                  <Palette className="w-8 h-8 text-white" />
                </div>
                <h3 className="font-display font-semibold text-2xl text-white mb-3">Your brand, everywhere</h3>
                <p className="text-slate-400 leading-relaxed text-lg">
                  Logo, colors, contact info — every report looks like it came from your design team.
                </p>
                <div className="mt-6 pt-6 border-t border-orange-500/20">
                  <div className="flex items-center gap-2 text-orange-400">
                    <Check className="w-5 h-5" />
                    <span className="text-sm">Full white-label</span>
                  </div>
                </div>
              </div>
            </div>

            <div className="group relative bg-gradient-to-br from-emerald-500/10 to-emerald-600/5 backdrop-blur-sm rounded-3xl border border-emerald-500/20 p-8 hover:border-emerald-500/40 transition-all duration-300 hover:-translate-y-1">
              <div className="absolute inset-0 bg-gradient-to-br from-emerald-500/5 to-transparent rounded-3xl opacity-0 group-hover:opacity-100 transition-opacity" />
              <div className="relative">
                <div className="w-16 h-16 rounded-2xl bg-gradient-to-br from-emerald-500 to-emerald-600 flex items-center justify-center mb-6 shadow-lg shadow-emerald-500/25">
                  <TrendingUp className="w-8 h-8 text-white" />
                </div>
                <h3 className="font-display font-semibold text-2xl text-white mb-3">Always fresh data</h3>
                <p className="text-slate-400 leading-relaxed text-lg">
                  Direct MLS integration means your reports show real-time listings, sales, and market stats.
                </p>
                <div className="mt-6 pt-6 border-t border-emerald-500/20">
                  <div className="flex items-center gap-2 text-emerald-400">
                    <Check className="w-5 h-5" />
                    <span className="text-sm">Real-time MLS data</span>
                  </div>
                </div>
              </div>
            </div>
          </div>

          <div className="mt-20 text-center">
            <p className="text-slate-500 mb-8 uppercase tracking-wider text-sm">Trusted by agents at</p>
            <div className="flex flex-wrap justify-center items-center gap-x-16 gap-y-6">
              <span className="text-2xl font-semibold text-slate-500 hover:text-slate-400 transition-colors">
                Keller Williams
              </span>
              <span className="text-2xl font-semibold text-slate-500 hover:text-slate-400 transition-colors">
                RE/MAX
              </span>
              <span className="text-2xl font-semibold text-slate-500 hover:text-slate-400 transition-colors">
                Coldwell Banker
              </span>
              <span className="text-2xl font-semibold text-slate-500 hover:text-slate-400 transition-colors">
                Century 21
              </span>
              <span className="text-2xl font-semibold text-slate-500 hover:text-slate-400 transition-colors">
                eXp Realty
              </span>
            </div>
          </div>
        </div>
      </section>

      {/* WHITE SEPARATOR - Two Audiences */}
      <section className="relative py-20 px-4 sm:px-6 lg:px-8 overflow-hidden">
        {/* Split background */}
        <div className="absolute inset-0 flex">
          <div className="w-1/2 bg-gradient-to-br from-purple-50 via-white to-purple-50/30" />
          <div className="w-1/2 bg-gradient-to-bl from-orange-50 via-white to-orange-50/30" />
        </div>

        {/* Diagonal divider line */}
        <div className="absolute inset-0 flex items-center justify-center">
          <div className="h-full w-px bg-gradient-to-b from-transparent via-slate-200 to-transparent" />
        </div>

        <div className="relative max-w-[1200px] mx-auto">
          <div className="grid md:grid-cols-2 gap-8 items-center">
            {/* For Agents - Left side */}
            <div className="group">
              <div className="relative p-8 rounded-3xl bg-white shadow-lg border border-purple-100 hover:shadow-2xl hover:scale-[1.02] transition-all duration-300">
                {/* Decorative corner accent */}
                <div className="absolute -top-3 -right-3 w-24 h-24 bg-gradient-to-br from-purple-500 to-purple-600 rounded-2xl opacity-10 blur-2xl group-hover:opacity-20 transition-opacity" />

                <div className="relative">
                  <div className="inline-flex p-4 rounded-2xl bg-gradient-to-br from-purple-500 to-purple-600 mb-6 shadow-lg shadow-purple-500/20">
                    <User className="w-8 h-8 text-white" />
                  </div>

                  <h3 className="font-display font-semibold text-2xl text-slate-900 mb-3">For Agents</h3>
                  <p className="text-slate-600 text-lg leading-relaxed mb-6">
                    Grow your business and impress clients with stunning, branded market reports
                  </p>

                  {/* Key features mini-list */}
                  <div className="space-y-2">
                    <div className="flex items-center gap-2 text-sm text-slate-700">
                      <div className="w-1.5 h-1.5 rounded-full bg-purple-500" />
                      <span>Automated MLS data pulls</span>
                    </div>
                    <div className="flex items-center gap-2 text-sm text-slate-700">
                      <div className="w-1.5 h-1.5 rounded-full bg-purple-500" />
                      <span>Custom branding & logos</span>
                    </div>
                    <div className="flex items-center gap-2 text-sm text-slate-700">
                      <div className="w-1.5 h-1.5 rounded-full bg-purple-500" />
                      <span>Share in seconds</span>
                    </div>
                  </div>
                </div>
              </div>
            </div>

            {/* For Affiliates - Right side */}
            <div className="group">
              <div className="relative p-8 rounded-3xl bg-white shadow-lg border border-orange-100 hover:shadow-2xl hover:scale-[1.02] transition-all duration-300">
                {/* Decorative corner accent */}
                <div className="absolute -top-3 -left-3 w-24 h-24 bg-gradient-to-br from-orange-500 to-orange-600 rounded-2xl opacity-10 blur-2xl group-hover:opacity-20 transition-opacity" />

                <div className="relative">
                  <div className="inline-flex p-4 rounded-2xl bg-gradient-to-br from-orange-500 to-orange-600 mb-6 shadow-lg shadow-orange-500/20">
                    <Building2 className="w-8 h-8 text-white" />
                  </div>

                  <h3 className="font-display font-semibold text-2xl text-slate-900 mb-3">For Affiliates</h3>
                  <p className="text-slate-600 text-base leading-relaxed mb-2">
                    (Title Companies, Lenders & Brokerages)
                  </p>
                  <p className="text-slate-600 text-lg leading-relaxed mb-6">
                    Sponsor agents and strengthen relationships with co-branded reports
                  </p>

                  {/* Key features mini-list */}
                  <div className="space-y-2">
                    <div className="flex items-center gap-2 text-sm text-slate-700">
                      <div className="w-1.5 h-1.5 rounded-full bg-orange-500" />
                      <span>Co-branded reports with your logo</span>
                    </div>
                    <div className="flex items-center gap-2 text-sm text-slate-700">
                      <div className="w-1.5 h-1.5 rounded-full bg-orange-500" />
                      <span>Sponsor unlimited agents</span>
                    </div>
                    <div className="flex items-center gap-2 text-sm text-slate-700">
                      <div className="w-1.5 h-1.5 rounded-full bg-orange-500" />
                      <span>Track engagement & usage</span>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>

          {/* Center connecting element */}
          <div className="hidden md:flex absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 items-center justify-center">
            <div className="w-16 h-16 rounded-full bg-white border-4 border-slate-100 shadow-xl flex items-center justify-center">
              <div className="w-8 h-8 rounded-full bg-gradient-to-br from-purple-500 via-violet-500 to-orange-500 animate-pulse" />
            </div>
          </div>
        </div>
      </section>

      <section className="py-16 px-4 sm:px-6 lg:px-8 bg-white border-y border-slate-100">
        <div className="max-w-[1200px] mx-auto">
          <div className="grid md:grid-cols-2 gap-6 max-w-4xl mx-auto">
            {/* For Agents */}
            <div className="flex items-center gap-4 p-6 rounded-2xl bg-gradient-to-r from-purple-50 to-white border border-purple-100">
              <div className="w-14 h-14 rounded-xl bg-purple-100 flex items-center justify-center flex-shrink-0">
                <User className="w-7 h-7 text-purple-600" />
              </div>
              <div>
                <h3 className="font-display font-semibold text-lg text-slate-900">For Agents</h3>
                <p className="text-slate-600 text-sm">
                  Grow your business and impress clients with branded market intel
                </p>
              </div>
            </div>

            <div className="flex items-center gap-4 p-6 rounded-2xl bg-gradient-to-r from-orange-50 to-white border border-orange-100">
              <div className="w-14 h-14 rounded-xl bg-orange-100 flex items-center justify-center flex-shrink-0">
                <Building2 className="w-7 h-7 text-orange-600" />
              </div>
              <div>
                <h3 className="font-display font-semibold text-lg text-slate-900">
                  For Affiliates (Title, Lenders & Brokerages)
                </h3>
                <p className="text-slate-600 text-sm">
                  Sponsor agents and strengthen relationships with co-branded reports
                </p>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* 4. HOW IT WORKS - 3 step process with video */}
      <section id="demo" className="py-24 px-4 sm:px-6 lg:px-8 bg-slate-900 text-white">
        <div className="max-w-[1200px] mx-auto">
          <div className="text-center mb-12">
            <h2 className="font-display font-semibold text-4xl sm:text-5xl mb-4">From MLS to inbox in 3 clicks</h2>
            <p className="text-xl text-slate-400">No spreadsheets. No manual formatting. Just results.</p>
          </div>

          {/* Video Demo */}
          <div className="mb-20">
            <div className="max-w-4xl mx-auto bg-slate-800 rounded-2xl border border-slate-700 overflow-hidden shadow-2xl">
              <div className="aspect-video bg-slate-800 relative">
                <div className="absolute inset-0 flex items-center justify-center">
                  <button className="w-20 h-20 rounded-full bg-purple-600 hover:bg-purple-700 flex items-center justify-center shadow-2xl hover:scale-110 transition-transform">
                    <Play className="w-8 h-8 text-white ml-1" />
                  </button>
                </div>
                <img
                  src="/placeholder.svg?height=720&width=1280&text=Watch+Demo:+Create+Report+in+60+Seconds"
                  alt="Product demo video"
                  className="w-full h-full object-cover opacity-60"
                />
              </div>
            </div>
            <p className="text-center mt-4 text-slate-500">
              Watch a real agent create a market report in under 60 seconds
            </p>
          </div>

          {/* 3 Steps */}
          <div className="space-y-20">
            <div className="grid lg:grid-cols-2 gap-12 items-center">
              <div className="order-2 lg:order-1">
                <div className="flex items-center gap-4 mb-6">
                  <div className="w-12 h-12 rounded-full bg-purple-500 flex items-center justify-center font-bold text-xl">
                    1
                  </div>
                  <div className="h-px flex-1 bg-gradient-to-r from-purple-500 to-transparent" />
                </div>
                <h3 className="font-display font-semibold text-3xl mb-4">Define your market</h3>
                <p className="text-lg text-slate-400 leading-relaxed mb-6">
                  Select ZIP codes, neighborhoods, or draw custom boundaries. Choose the report type that fits your
                  audience.
                </p>
                <ul className="space-y-3 text-slate-300">
                  <li className="flex items-center gap-3">
                    <Check className="w-5 h-5 text-purple-400" />
                    <span>City, ZIP, or custom polygon selection</span>
                  </li>
                  <li className="flex items-center gap-3">
                    <Check className="w-5 h-5 text-purple-400" />
                    <span>10+ report templates to choose from</span>
                  </li>
                </ul>
              </div>
              <div className="order-1 lg:order-2">
                <div className="bg-slate-800 rounded-2xl border border-slate-700 overflow-hidden shadow-2xl">
                  <div className="bg-slate-700/50 px-4 py-3 flex items-center gap-2">
                    <div className="w-3 h-3 rounded-full bg-red-500" />
                    <div className="w-3 h-3 rounded-full bg-yellow-500" />
                    <div className="w-3 h-3 rounded-full bg-green-500" />
                  </div>
                  <img
                    src="/placeholder.svg?height=400&width=600&text=App:+Market+Selection+Map"
                    alt="Market selection interface"
                    className="w-full"
                  />
                </div>
              </div>
            </div>

            <div className="grid lg:grid-cols-2 gap-12 items-center">
              <div>
                <div className="bg-slate-800 rounded-2xl border border-slate-700 overflow-hidden shadow-2xl">
                  <div className="bg-slate-700/50 px-4 py-3 flex items-center gap-2">
                    <div className="w-3 h-3 rounded-full bg-red-500" />
                    <div className="w-3 h-3 rounded-full bg-yellow-500" />
                    <div className="w-3 h-3 rounded-full bg-green-500" />
                  </div>
                  <img
                    src="/placeholder.svg?height=400&width=600&text=App:+Schedule+%26+Branding"
                    alt="Schedule configuration"
                    className="w-full"
                  />
                </div>
              </div>
              <div>
                <div className="flex items-center gap-4 mb-6">
                  <div className="w-12 h-12 rounded-full bg-orange-500 flex items-center justify-center font-bold text-xl">
                    2
                  </div>
                  <div className="h-px flex-1 bg-gradient-to-r from-orange-500 to-transparent" />
                </div>
                <h3 className="font-display font-semibold text-3xl mb-4">Add your brand & schedule</h3>
                <p className="text-lg text-slate-400 leading-relaxed mb-6">
                  Upload your logo, pick your colors, set your delivery cadence. Every report reflects your professional
                  brand.
                </p>
                <ul className="space-y-3 text-slate-300">
                  <li className="flex items-center gap-3">
                    <Check className="w-5 h-5 text-orange-400" />
                    <span>Logo, colors, and contact info</span>
                  </li>
                  <li className="flex items-center gap-3">
                    <Check className="w-5 h-5 text-orange-400" />
                    <span>Weekly, monthly, or custom schedules</span>
                  </li>
                </ul>
              </div>
            </div>

            <div className="grid lg:grid-cols-2 gap-12 items-center">
              <div className="order-2 lg:order-1">
                <div className="flex items-center gap-4 mb-6">
                  <div className="w-12 h-12 rounded-full bg-green-500 flex items-center justify-center font-bold text-xl">
                    3
                  </div>
                  <div className="h-px flex-1 bg-gradient-to-r from-green-500 to-transparent" />
                </div>
                <h3 className="font-display font-semibold text-3xl mb-4">Deliver and impress</h3>
                <p className="text-lg text-slate-400 leading-relaxed mb-6">
                  Reports generate automatically and land in your clients' inboxes. You stay top-of-mind without lifting
                  a finger.
                </p>
                <ul className="space-y-3 text-slate-300">
                  <li className="flex items-center gap-3">
                    <Check className="w-5 h-5 text-green-400" />
                    <span>PDF download or email delivery</span>
                  </li>
                  <li className="flex items-center gap-3">
                    <Check className="w-5 h-5 text-green-400" />
                    <span>Track opens and engagement</span>
                  </li>
                </ul>
              </div>
              <div className="order-1 lg:order-2">
                <div className="bg-white rounded-2xl overflow-hidden shadow-2xl p-6">
                  <img
                    src="/placeholder.svg?height=450&width=350&text=Finished+Report+Preview"
                    alt="Finished report preview"
                    className="w-full rounded-lg shadow-lg"
                  />
                </div>
              </div>
            </div>
          </div>

          <div className="mt-20 text-center">
            <Button
              size="lg"
              className="bg-white text-slate-900 hover:bg-slate-100 shadow-lg px-8 py-6 text-lg font-semibold"
              asChild
            >
              <Link href="/login">
                Start Your Free Trial
                <ArrowRight className="ml-2 w-5 h-5" />
              </Link>
            </Button>
            <p className="mt-4 text-slate-500 text-sm">No credit card required</p>
          </div>
        </div>
      </section>

      {/* 5. SAMPLE REPORTS CAROUSEL */}
      <section id="reports" className="py-24 px-4 sm:px-6 lg:px-8 bg-slate-50">
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
                    src={`/ceholder-svg-height-220-width-170-text-.jpg?height=220&width=170&text=${encodeURIComponent(sample.title)}`}
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
            <Button
              size="lg"
              variant="outline"
              className="border-purple-300 text-purple-700 hover:bg-purple-50 bg-transparent"
            >
              View Full Sample Reports
              <ChevronRight className="w-5 h-5 ml-2" />
            </Button>
          </div>
        </div>
      </section>

      {/* 6. TESTIMONIALS */}
      <section className="py-24 px-4 sm:px-6 lg:px-8 bg-white">
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
                "TrendyReports recovered 3+ hours every week. That's billable time I now spend on client meetings and
                prospecting. ROI is 20x my subscription cost."
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
                "We sponsor 40 agents under one plan. Every report carries our brand. The usage analytics show clear
                engagement. Best marketing investment we've made."
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
                "My clients forward the reports to their friends. The design is clean and the data is current. I close
                more referrals now than ever before."
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

      {/* 7. INTEGRATIONS */}
      <section className="py-24 px-4 sm:px-6 lg:px-8">
        <div className="max-w-[1200px] mx-auto">
          <div className="text-center mb-16">
            <h2 className="font-display font-semibold text-4xl sm:text-5xl mb-4 text-slate-900">
              Integrates with your MLS
            </h2>
            <p className="text-xl text-slate-600">Connects to the data sources you already use</p>
          </div>

          <div className="grid grid-cols-2 md:grid-cols-4 gap-6">
            {["MLS Grid", "Zillow", "Realtor.com", "ListHub", "Zapier", "Mailchimp", "Salesforce", "HubSpot"].map(
              (integration, idx) => (
                <div
                  key={idx}
                  className="bg-white rounded-xl border border-slate-200 p-6 text-center hover:border-purple-300 hover:shadow-lg transition-all"
                >
                  <div className="font-semibold text-slate-900">{integration}</div>
                </div>
              ),
            )}
          </div>

          <div className="mt-12 text-center">
            <p className="text-slate-600">
              Need a custom integration?{" "}
              <a
                href="mailto:integrations@trendyreports.com"
                className="text-purple-600 hover:text-purple-700 font-semibold underline"
              >
                Contact our team
              </a>
            </p>
          </div>
        </div>
      </section>

      {/* 8. PRICING */}
      <section id="pricing" className="py-24 px-4 sm:px-6 lg:px-8 bg-slate-50">
        <div className="max-w-[1200px] mx-auto">
          <div className="text-center mb-16">
            <h2 className="font-display font-semibold text-4xl sm:text-5xl mb-4 text-slate-900">
              Simple, transparent pricing
            </h2>
            <p className="text-xl text-slate-600">
              Choose the plan that fits your business. Upgrade or downgrade anytime.
            </p>
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
                  <span className="text-slate-700">
                    <strong>50 reports</strong> per month
                  </span>
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
              <Button className="w-full h-12 bg-transparent" variant="outline" asChild>
                <Link href="/login">Get Started Free</Link>
              </Button>
            </div>

            {/* Pro */}
            <div className="bg-gradient-to-br from-purple-50 via-white to-white rounded-3xl border-2 border-purple-300 p-8 relative shadow-lg hover:shadow-xl transition-all transform hover:scale-105">
              <div className="absolute -top-4 left-1/2 -translate-x-1/2 bg-gradient-to-r from-purple-600 to-purple-700 text-white text-xs font-bold px-4 py-1.5 rounded-full shadow-lg">
                MOST POPULAR
              </div>
              <div className="mb-6">
                <h3 className="font-display font-semibold text-2xl mb-2 text-slate-900">Pro</h3>
                <p className="text-slate-700">For individual agents and small teams</p>
              </div>
              <div className="mb-6">
                <span className="font-display font-bold text-5xl text-slate-900">$299</span>
                <span className="text-slate-600 text-lg">/month</span>
              </div>
              <ul className="space-y-3 mb-8">
                <li className="flex items-start gap-3 text-sm">
                  <Check className="w-5 h-5 text-purple-600 shrink-0 mt-0.5" />
                  <span className="text-slate-700">
                    <strong>300 reports</strong> per month
                  </span>
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
              <Button
                className="w-full h-12 bg-gradient-to-r from-purple-600 to-purple-700 hover:from-purple-700 hover:to-purple-800 text-white shadow-lg"
                asChild
              >
                <Link href="/login">Start 14-Day Free Trial</Link>
              </Button>
            </div>

            {/* Team */}
            <div className="bg-white rounded-3xl border border-slate-200 p-8 hover:border-purple-200 hover:shadow-lg transition-all">
              <div className="mb-6">
                <h3 className="font-display font-semibold text-2xl mb-2 text-slate-900">Team</h3>
                <p className="text-slate-600">For brokerages, teams & affiliates</p>
              </div>
              <div className="mb-6">
                <span className="font-display font-bold text-5xl text-slate-900">$999</span>
                <span className="text-slate-600 text-lg">/month</span>
              </div>
              <ul className="space-y-3 mb-8">
                <li className="flex items-start gap-3 text-sm">
                  <Check className="w-5 h-5 text-purple-600 shrink-0 mt-0.5" />
                  <span className="text-slate-700">
                    <strong>Unlimited reports</strong>
                  </span>
                </li>
                <li className="flex items-start gap-3 text-sm">
                  <Check className="w-5 h-5 text-purple-600 shrink-0 mt-0.5" />
                  <span className="text-slate-700">Sponsor agents under one plan</span>
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
              <Button className="w-full h-12 bg-transparent" variant="outline" asChild>
                <Link href="/login">Start 14-Day Free Trial</Link>
              </Button>
            </div>
          </div>

          <div className="mt-16 max-w-3xl mx-auto">
            <div className="grid md:grid-cols-2 gap-8 text-sm">
              <div>
                <h4 className="font-semibold text-slate-900 mb-2">All plans include:</h4>
                <ul className="space-y-1 text-slate-600">
                  <li>14-day free trial, no credit card</li>
                  <li>Cancel or change plans anytime</li>
                  <li>99.9% uptime SLA</li>
                  <li>SOC 2 Type II compliant</li>
                </ul>
              </div>
              <div>
                <h4 className="font-semibold text-slate-900 mb-2">Need something custom?</h4>
                <p className="text-slate-600 mb-2">
                  Enterprise plans available with custom integrations, dedicated infrastructure, and volume pricing.
                </p>
                <a
                  href="mailto:enterprise@trendyreports.com"
                  className="text-purple-600 hover:text-purple-700 font-semibold underline"
                >
                  Contact sales
                </a>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* 9. SECURITY */}
      <section className="py-24 px-4 sm:px-6 lg:px-8">
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
            <p>GDPR compliant | Row-level security | Automatic backups | Secure integrations</p>
          </div>
        </div>
      </section>

      {/* 10. FINAL CTA */}
      <section className="py-24 px-4 sm:px-6 lg:px-8 bg-gradient-to-br from-purple-600 via-purple-700 to-purple-800 relative overflow-hidden">
        <div className="absolute inset-0 opacity-10">
          <div
            className="absolute inset-0"
            style={{
              backgroundImage: "radial-gradient(circle at 2px 2px, white 1px, transparent 0)",
              backgroundSize: "40px 40px",
            }}
          />
        </div>
        <div className="max-w-[1200px] mx-auto text-center relative z-10">
          <h2 className="font-display font-semibold text-4xl sm:text-5xl lg:text-6xl mb-6 text-white leading-tight">
            Ready to automate your market reports?
          </h2>
          <p className="text-xl text-purple-100 mb-8 max-w-3xl mx-auto leading-relaxed">
            Join 1,200+ agents who recovered 150+ hours per year. Start your 14-day free trial today.
          </p>
          <div className="flex flex-col sm:flex-row items-center justify-center gap-4">
            <Button
              size="lg"
              className="bg-white text-purple-700 hover:bg-purple-50 h-14 px-10 text-lg shadow-xl hover:shadow-2xl hover:scale-105 transition-all font-semibold"
              asChild
            >
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

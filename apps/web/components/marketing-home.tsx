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
  Clock,
  Palette,
  User,
  Building2,
  RefreshCw,
  Zap,
  CalendarCheck,
} from "lucide-react"
import Link from "next/link"
import Image from "next/image"
import { Carousel, CarouselContent, CarouselItem, CarouselNext, CarouselPrevious } from "@/components/ui/carousel"

export function MarketingHome() {
  return (
    <div className="min-h-screen bg-white">
      <Navbar />

      {/* ═══════════════════════════════════════════════════════════════════
          1. HERO - Hook them immediately
      ═══════════════════════════════════════════════════════════════════ */}
      <section className="relative pt-32 pb-24 px-4 sm:px-6 lg:px-8">
        <div className="max-w-[1200px] mx-auto">
          <div className="grid lg:grid-cols-2 gap-16 items-center">
            <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.3 }}>
              <div className="inline-flex items-center gap-2 bg-purple-50 border border-purple-200 rounded-full px-4 py-2 mb-6">
                <div className="w-2 h-2 bg-purple-600 rounded-full animate-pulse" />
                <span className="text-sm font-semibold text-purple-900">
                  Trusted by 1,200+ agents at KW, RE/MAX, Coldwell Banker
                </span>
              </div>
              <h1 className="font-display font-semibold text-5xl sm:text-6xl lg:text-7xl mb-6 text-slate-900 leading-[1.05]">
                Beautiful market reports. Zero effort.
              </h1>
              <p className="text-xl text-slate-600 mb-8 leading-relaxed max-w-xl">
                Generate branded market reports in 30 seconds. Automated delivery to clients. 
                Recover 3+ hours every week for prospecting.
              </p>
              <div className="flex flex-col sm:flex-row gap-4 mb-8">
                <Button
                  size="lg"
                  className="bg-gradient-to-r from-purple-600 to-purple-700 hover:from-purple-700 hover:to-purple-800 text-white text-lg px-8 h-14 shadow-lg hover:shadow-xl transition-all"
                  asChild
                >
                  <Link href="/register">
                    Start Free Trial
                    <ArrowRight className="w-5 h-5 ml-2" />
                  </Link>
                </Button>
                <Button
                  size="lg"
                  variant="outline"
                  className="text-lg px-8 h-14 border-slate-300 hover:bg-slate-50 bg-transparent"
                  onClick={() => {
                    const element = document.getElementById('how-it-works')
                    if (element) {
                      element.scrollIntoView({ behavior: 'smooth' })
                    }
                  }}
                >
                  See How It Works
                </Button>
              </div>
              <div className="flex flex-wrap items-center gap-x-6 gap-y-2 text-sm text-slate-600">
                <div className="flex items-center gap-2">
                  <Check className="w-4 h-4 text-green-600" />
                  <span>14-day free trial</span>
                </div>
                <div className="flex items-center gap-2">
                  <Check className="w-4 h-4 text-green-600" />
                  <span>No credit card required</span>
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
              <div className="bg-white rounded-2xl shadow-2xl border border-slate-200 overflow-hidden">
                <img
                  src="/market-snapshot-laverne-hero.jpg"
                  alt="Market Snapshot Report showing $895K median price, 32 closed sales, and complete market analytics"
                  className="w-full h-auto"
                />
              </div>
            </motion.div>
          </div>
        </div>
      </section>

      {/* ═══════════════════════════════════════════════════════════════════
          2. TRUST BAR - Build instant credibility
      ═══════════════════════════════════════════════════════════════════ */}
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
              <div className="font-display font-bold text-4xl text-slate-900 mb-1">3+ hrs</div>
              <div className="text-sm text-slate-600">Saved per week</div>
            </div>
          </div>
        </div>
      </section>

      {/* ═══════════════════════════════════════════════════════════════════
          3. HOW IT WORKS - Show simplicity fast (3 steps)
      ═══════════════════════════════════════════════════════════════════ */}
      <section id="how-it-works" className="py-24 px-4 sm:px-6 lg:px-8 bg-slate-900 text-white">
        <div className="max-w-[1200px] mx-auto">
          <div className="text-center mb-16">
            <h2 className="font-display font-semibold text-4xl sm:text-5xl mb-4">From MLS to inbox in 3 clicks</h2>
            <p className="text-xl text-slate-400">No spreadsheets. No manual formatting. Just results.</p>
          </div>

          {/* 3 Steps - Horizontal Cards */}
          <div className="grid md:grid-cols-3 gap-8 mb-16">
            <div className="relative">
              <div className="bg-slate-800 rounded-2xl border border-slate-700 p-8 h-full">
                <div className="w-12 h-12 rounded-full bg-purple-500 flex items-center justify-center font-bold text-xl mb-6">
                  1
                </div>
                <h3 className="font-display font-semibold text-2xl mb-3">Pick your area</h3>
                <p className="text-slate-400 leading-relaxed">
                  Select ZIP codes, cities, or neighborhoods. Choose from 8 report types.
                </p>
                <ul className="mt-4 space-y-2 text-slate-300 text-sm">
                  <li className="flex items-center gap-2">
                    <Check className="w-4 h-4 text-purple-400" />
                    <span>City or ZIP selection</span>
                  </li>
                  <li className="flex items-center gap-2">
                    <Check className="w-4 h-4 text-purple-400" />
                    <span>8 report templates</span>
                  </li>
                </ul>
              </div>
            </div>

            <div className="relative">
              <div className="bg-slate-800 rounded-2xl border border-slate-700 p-8 h-full">
                <div className="w-12 h-12 rounded-full bg-orange-500 flex items-center justify-center font-bold text-xl mb-6">
                  2
                </div>
                <h3 className="font-display font-semibold text-2xl mb-3">Add your brand</h3>
                <p className="text-slate-400 leading-relaxed">
                  Upload your logo, pick colors, set your schedule. Every report looks 100% yours.
                </p>
                <ul className="mt-4 space-y-2 text-slate-300 text-sm">
                  <li className="flex items-center gap-2">
                    <Check className="w-4 h-4 text-orange-400" />
                    <span>Logo, colors, contact info</span>
                  </li>
                  <li className="flex items-center gap-2">
                    <Check className="w-4 h-4 text-orange-400" />
                    <span>Weekly or monthly delivery</span>
                  </li>
                </ul>
              </div>
            </div>

            <div className="relative">
              <div className="bg-slate-800 rounded-2xl border border-slate-700 p-8 h-full">
                <div className="w-12 h-12 rounded-full bg-green-500 flex items-center justify-center font-bold text-xl mb-6">
                  3
                </div>
                <h3 className="font-display font-semibold text-2xl mb-3">Hit send. Look like a pro.</h3>
                <p className="text-slate-400 leading-relaxed">
                  Reports generate automatically and land in your clients' inboxes. Stay top-of-mind effortlessly.
                </p>
                <ul className="mt-4 space-y-2 text-slate-300 text-sm">
                  <li className="flex items-center gap-2">
                    <Check className="w-4 h-4 text-green-400" />
                    <span>PDF download or email</span>
                  </li>
                  <li className="flex items-center gap-2">
                    <Check className="w-4 h-4 text-green-400" />
                    <span>Social media images</span>
                  </li>
                </ul>
              </div>
            </div>
          </div>

          <div className="text-center">
            <Button
              size="lg"
              className="bg-white text-slate-900 hover:bg-slate-100 shadow-lg px-8 py-6 text-lg font-semibold"
              asChild
            >
              <Link href="/register">
                Start Free Trial
                <ArrowRight className="ml-2 w-5 h-5" />
              </Link>
            </Button>
            <p className="mt-4 text-slate-500 text-sm">No credit card required</p>
          </div>
        </div>
      </section>

      {/* ═══════════════════════════════════════════════════════════════════
          4. PRODUCT SHOWCASE - Email + PDF in one section
      ═══════════════════════════════════════════════════════════════════ */}
      <section className="py-24 px-4 sm:px-6 lg:px-8 bg-white overflow-hidden">
        <div className="max-w-[1400px] mx-auto">
          <div className="text-center mb-16">
            <h2 className="font-display font-semibold text-4xl sm:text-5xl mb-4 text-slate-900">
              Reports clients actually open
            </h2>
            <p className="text-xl text-slate-600">Mobile-optimized emails. Print-ready PDFs. All with your branding.</p>
          </div>

          <div className="grid lg:grid-cols-2 gap-12">
            {/* Email Reports */}
            <div>
              <div className="text-center mb-6">
                <span className="inline-flex items-center gap-2 bg-purple-100 text-purple-700 px-4 py-2 rounded-full text-sm font-semibold">
                  📧 Email Reports
                </span>
              </div>
              <div className="bg-white rounded-2xl shadow-2xl border border-slate-200 overflow-hidden">
                <div className="bg-slate-100 px-4 py-3 border-b border-slate-200 flex items-center gap-3">
                  <div className="flex gap-1.5">
                    <div className="w-3 h-3 rounded-full bg-red-500" />
                    <div className="w-3 h-3 rounded-full bg-yellow-500" />
                    <div className="w-3 h-3 rounded-full bg-green-500" />
                  </div>
                  <div className="text-sm text-slate-600">Market Report — December 2024</div>
                </div>
                <div className="p-6 bg-gradient-to-br from-slate-50 to-white">
                  <Carousel className="w-full">
                    <CarouselContent>
                      <CarouselItem>
                        <img
                          src="/real-estate-market-snapshot-report-with-purple-gra.jpg"
                          alt="Market Snapshot email report"
                          className="w-full rounded-lg shadow-lg"
                        />
                      </CarouselItem>
                      <CarouselItem>
                        <img
                          src="/real-estate-new-listings-gallery-with-property-pho.jpg"
                          alt="New Listings email report"
                          className="w-full rounded-lg shadow-lg"
                        />
                      </CarouselItem>
                      <CarouselItem>
                        <img
                          src="/real-estate-featured-listings-report-with-blue-gra.jpg"
                          alt="Featured Listings email report"
                          className="w-full rounded-lg shadow-lg"
                        />
                      </CarouselItem>
                    </CarouselContent>
                    <CarouselPrevious className="left-2" />
                    <CarouselNext className="right-2" />
                  </Carousel>
                </div>
              </div>
              <div className="mt-6 grid grid-cols-2 gap-4">
                <div className="flex items-center gap-2 text-sm text-slate-600">
                  <Check className="w-4 h-4 text-purple-600" />
                  <span>Mobile-first design</span>
                </div>
                <div className="flex items-center gap-2 text-sm text-slate-600">
                  <Check className="w-4 h-4 text-purple-600" />
                  <span>Your logo & colors</span>
                </div>
                <div className="flex items-center gap-2 text-sm text-slate-600">
                  <Check className="w-4 h-4 text-purple-600" />
                  <span>Key market metrics</span>
                </div>
                <div className="flex items-center gap-2 text-sm text-slate-600">
                  <Check className="w-4 h-4 text-purple-600" />
                  <span>Your contact info</span>
                </div>
              </div>
            </div>

            {/* PDF Reports */}
            <div>
              <div className="text-center mb-6">
                <span className="inline-flex items-center gap-2 bg-orange-100 text-orange-700 px-4 py-2 rounded-full text-sm font-semibold">
                  📄 PDF Reports
                </span>
              </div>
              <div className="bg-white rounded-2xl shadow-2xl border border-slate-200 p-6">
                <div className="bg-slate-100 rounded-lg p-4">
                  <Carousel className="w-full">
                    <CarouselContent>
                      <CarouselItem>
                        <img
                          src="/market-snapshot-report-purple-gradient-header-with.jpg"
                          alt="Market Snapshot PDF report"
                          className="w-full rounded shadow-2xl"
                        />
                      </CarouselItem>
                      <CarouselItem>
                        <img
                          src="/new-listings-gallery-report-purple-header-with-pro.jpg"
                          alt="New Listings Gallery PDF report"
                          className="w-full rounded shadow-2xl"
                        />
                      </CarouselItem>
                      <CarouselItem>
                        <img
                          src="/featured-listings-report-purple-header-with-2x2-pr.jpg"
                          alt="Featured Listings PDF report"
                          className="w-full rounded shadow-2xl"
                        />
                      </CarouselItem>
                    </CarouselContent>
                    <CarouselPrevious className="left-2" />
                    <CarouselNext className="right-2" />
                  </Carousel>
                </div>
              </div>
              <div className="mt-6 grid grid-cols-2 gap-4">
                <div className="flex items-center gap-2 text-sm text-slate-600">
                  <Check className="w-4 h-4 text-orange-600" />
                  <span>8.5×11 print-ready</span>
                </div>
                <div className="flex items-center gap-2 text-sm text-slate-600">
                  <Check className="w-4 h-4 text-orange-600" />
                  <span>Professional header</span>
                </div>
                <div className="flex items-center gap-2 text-sm text-slate-600">
                  <Check className="w-4 h-4 text-orange-600" />
                  <span>Charts & visualizations</span>
                </div>
                <div className="flex items-center gap-2 text-sm text-slate-600">
                  <Check className="w-4 h-4 text-orange-600" />
                  <span>Property galleries</span>
                </div>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* ═══════════════════════════════════════════════════════════════════
          5. WHY CHOOSE US - Benefits after they see the product
      ═══════════════════════════════════════════════════════════════════ */}
      <section className="py-24 px-4 sm:px-6 lg:px-8 text-white overflow-hidden relative">
        <div className="absolute inset-0">
          <Image 
            src="/modern-luxury-real-estate-office-interior-with-gla.jpg" 
            alt="" 
            fill 
            className="object-cover"
            priority={false}
          />
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

      {/* ═══════════════════════════════════════════════════════════════════
          6. TESTIMONIALS - Social proof before pricing
      ═══════════════════════════════════════════════════════════════════ */}
      <section className="py-24 px-4 sm:px-6 lg:px-8 bg-slate-50">
        <div className="max-w-[1200px] mx-auto">
          <div className="text-center mb-16">
            <h2 className="font-display font-semibold text-4xl sm:text-5xl mb-4 text-slate-900">
              Trusted by top-producing agents
            </h2>
            <p className="text-xl text-slate-600">Real results from real estate professionals</p>
          </div>

          <div className="grid md:grid-cols-3 gap-8">
            <div className="bg-white rounded-2xl border border-slate-200 p-8 shadow-sm hover:shadow-lg transition-shadow">
              <div className="flex gap-1 mb-6">
                {[...Array(5)].map((_, i) => (
                  <Star key={i} className="w-5 h-5 fill-orange-400 text-orange-400" />
                ))}
              </div>
              <p className="text-slate-700 text-lg leading-relaxed mb-6">
                &quot;TrendyReports recovered 3+ hours every week. That&apos;s billable time I now spend on client meetings. 
                ROI is 20x my subscription cost.&quot;
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

            <div className="bg-white rounded-2xl border border-slate-200 p-8 shadow-sm hover:shadow-lg transition-shadow">
              <div className="flex gap-1 mb-6">
                {[...Array(5)].map((_, i) => (
                  <Star key={i} className="w-5 h-5 fill-orange-400 text-orange-400" />
                ))}
              </div>
              <p className="text-slate-700 text-lg leading-relaxed mb-6">
                &quot;We sponsor 40 agents under one plan. Every report carries our brand. Best marketing investment we&apos;ve 
                made this year.&quot;
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

            <div className="bg-white rounded-2xl border border-slate-200 p-8 shadow-sm hover:shadow-lg transition-shadow">
              <div className="flex gap-1 mb-6">
                {[...Array(5)].map((_, i) => (
                  <Star key={i} className="w-5 h-5 fill-orange-400 text-orange-400" />
                ))}
              </div>
              <p className="text-slate-700 text-lg leading-relaxed mb-6">
                &quot;My clients forward the reports to their friends. I close more referrals now than ever before.&quot;
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

      {/* ═══════════════════════════════════════════════════════════════════
          7. PRICING - Decision point
      ═══════════════════════════════════════════════════════════════════ */}
      <section id="pricing" className="py-24 px-4 sm:px-6 lg:px-8 bg-white">
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
                <Link href="/register">Start Free Trial</Link>
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
                <span className="font-display font-bold text-5xl text-slate-900">$29</span>
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
                <Link href="/register">Start Free Trial</Link>
              </Button>
            </div>

            {/* Team */}
            <div className="bg-white rounded-3xl border border-slate-200 p-8 hover:border-purple-200 hover:shadow-lg transition-all">
              <div className="mb-6">
                <h3 className="font-display font-semibold text-2xl mb-2 text-slate-900">Team</h3>
                <p className="text-slate-600">For brokerages, teams & affiliates</p>
              </div>
              <div className="mb-6">
                <span className="font-display font-bold text-5xl text-slate-900">$99</span>
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
                <Link href="/register">Start Free Trial</Link>
              </Button>
            </div>
          </div>

          <div className="mt-12 text-center">
            <p className="text-sm text-slate-600">
              All plans include 14-day free trial • No credit card required • Cancel anytime
            </p>
          </div>
        </div>
      </section>

      {/* ═══════════════════════════════════════════════════════════════════
          8. TWO AUDIENCES - Speak to both groups
      ═══════════════════════════════════════════════════════════════════ */}
      <section id="for-agents" className="relative py-20 px-4 sm:px-6 lg:px-8 overflow-hidden bg-slate-50">
        <div className="relative max-w-[1200px] mx-auto">
          <div className="text-center mb-12">
            <h2 className="font-display font-semibold text-4xl sm:text-5xl mb-4 text-slate-900">
              Built for you
            </h2>
            <p className="text-xl text-slate-600">Whether you&apos;re an agent or an affiliate, we&apos;ve got you covered</p>
          </div>

          <div className="grid md:grid-cols-2 gap-8 items-stretch">
            {/* For Agents */}
            <div className="group">
              <div className="relative p-8 rounded-3xl bg-white shadow-lg border border-purple-100 hover:shadow-2xl hover:scale-[1.02] transition-all duration-300 h-full">
                <div className="absolute -top-3 -right-3 w-24 h-24 bg-gradient-to-br from-purple-500 to-purple-600 rounded-2xl opacity-10 blur-2xl group-hover:opacity-20 transition-opacity" />

                <div className="relative">
                  <div className="inline-flex p-4 rounded-2xl bg-gradient-to-br from-purple-500 to-purple-600 mb-6 shadow-lg shadow-purple-500/20">
                    <User className="w-8 h-8 text-white" />
                  </div>

                  <h3 className="font-display font-semibold text-2xl text-slate-900 mb-3">For Agents</h3>
                  <p className="text-slate-600 text-lg leading-relaxed mb-6">
                    Grow your business and impress clients with stunning, branded market reports
                  </p>

                  <div className="space-y-2 mb-6">
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

                  <Button size="lg" className="bg-purple-600 hover:bg-purple-700 text-white" asChild>
                    <Link href="/register">
                      Start Free Trial
                      <ChevronRight className="w-5 h-5 ml-2" />
                    </Link>
                  </Button>
                </div>
              </div>
            </div>

            {/* For Affiliates */}
            <div id="for-affiliates" className="group">
              <div className="relative p-8 rounded-3xl bg-white shadow-lg border border-orange-100 hover:shadow-2xl hover:scale-[1.02] transition-all duration-300 h-full">
                <div className="absolute -top-3 -left-3 w-24 h-24 bg-gradient-to-br from-orange-500 to-orange-600 rounded-2xl opacity-10 blur-2xl group-hover:opacity-20 transition-opacity" />

                <div className="relative">
                  <div className="inline-flex p-4 rounded-2xl bg-gradient-to-br from-orange-500 to-orange-600 mb-6 shadow-lg shadow-orange-500/20">
                    <Building2 className="w-8 h-8 text-white" />
                  </div>

                  <h3 className="font-display font-semibold text-2xl text-slate-900 mb-3">For Affiliates</h3>
                  <p className="text-slate-600 text-sm mb-2">
                    (Title Companies, Lenders & Brokerages)
                  </p>
                  <p className="text-slate-600 text-lg leading-relaxed mb-6">
                    Sponsor agents and strengthen relationships with co-branded reports
                  </p>

                  <div className="space-y-2 mb-6">
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

                  <Button size="lg" className="bg-orange-600 hover:bg-orange-700 text-white" asChild>
                    <a href="mailto:sales@trendyreports.com">
                      Contact Sales
                      <ChevronRight className="w-5 h-5 ml-2" />
                    </a>
                  </Button>
                </div>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* ═══════════════════════════════════════════════════════════════════
          9. SECURITY - Handle objections
      ═══════════════════════════════════════════════════════════════════ */}
      <section className="py-24 px-4 sm:px-6 lg:px-8 bg-white">
        <div className="max-w-[1200px] mx-auto">
          <div className="text-center mb-16">
            <h2 className="font-display font-semibold text-4xl sm:text-5xl mb-4 text-slate-900">
              Enterprise-grade security
            </h2>
            <p className="text-xl text-slate-600">Bank-level protection for your data</p>
          </div>

          <div className="grid md:grid-cols-3 gap-8">
            <div className="bg-slate-50 rounded-2xl border border-slate-200 p-10 text-center">
              <div className="w-16 h-16 rounded-2xl bg-green-100 flex items-center justify-center mx-auto mb-6">
                <Shield className="w-8 h-8 text-green-600" />
              </div>
              <div className="font-display font-bold text-4xl text-slate-900 mb-2">SOC 2</div>
              <div className="text-slate-600">Type II compliant</div>
            </div>

            <div className="bg-slate-50 rounded-2xl border border-slate-200 p-10 text-center">
              <div className="w-16 h-16 rounded-2xl bg-blue-100 flex items-center justify-center mx-auto mb-6">
                <TrendingUp className="w-8 h-8 text-blue-600" />
              </div>
              <div className="font-display font-bold text-4xl text-slate-900 mb-2">99.9%</div>
              <div className="text-slate-600">Uptime SLA</div>
            </div>

            <div className="bg-slate-50 rounded-2xl border border-slate-200 p-10 text-center">
              <div className="w-16 h-16 rounded-2xl bg-purple-100 flex items-center justify-center mx-auto mb-6">
                <FileCheck className="w-8 h-8 text-purple-600" />
              </div>
              <div className="font-display font-bold text-4xl text-slate-900 mb-2">256-bit</div>
              <div className="text-slate-600">AES encryption</div>
            </div>
          </div>

          <div className="mt-12 text-center text-slate-600">
            <p>GDPR compliant • Row-level security • Automatic backups • Secure integrations</p>
          </div>
        </div>
      </section>

      {/* ═══════════════════════════════════════════════════════════════════
          10. FINAL CTA - Close the deal
      ═══════════════════════════════════════════════════════════════════ */}
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
            Join 1,200+ agents who recovered 150+ hours per year. Start your free trial today.
          </p>
          <div className="flex flex-col sm:flex-row items-center justify-center gap-4">
            <Button
              size="lg"
              className="bg-white text-purple-700 hover:bg-purple-50 h-14 px-10 text-lg shadow-xl hover:shadow-2xl hover:scale-105 transition-all font-semibold"
              asChild
            >
              <Link href="/register">
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

"use client"

import { motion } from "framer-motion"

const fadeUp = {
  hidden: { opacity: 0, y: 16 },
  visible: { opacity: 1, y: 0, transition: { duration: 0.4 } },
}

function ReportMockup() {
  return (
    <div className="mx-auto mt-16 max-w-xl" style={{ perspective: "1000px" }}>
      <div
        className="rounded-2xl border border-border bg-card shadow-2xl"
        style={{ transform: "rotateY(-4deg) rotateX(2deg)" }}
      >
        {/* Email header */}
        <div className="rounded-t-2xl bg-gradient-to-r from-[#6366F1] to-[#818CF8] px-8 py-6">
          <div className="flex items-center gap-4">
            <div className="flex h-12 w-12 items-center justify-center rounded-full bg-white/20 text-sm font-bold text-white">
              TR
            </div>
            <div>
              <p className="text-base font-semibold text-white">
                Market Snapshot &mdash; Austin, TX
              </p>
              <p className="text-sm text-white/70">January 2026 Report</p>
            </div>
          </div>
        </div>

        {/* Stats grid */}
        <div className="grid grid-cols-3 gap-4 px-8 py-6">
          {[
            { label: "Median price", value: "$485,000" },
            { label: "Active listings", value: "1,247" },
            { label: "Days on market", value: "28" },
          ].map((stat) => (
            <div key={stat.label} className="text-center">
              <p className="text-xl font-bold text-foreground">{stat.value}</p>
              <p className="text-sm text-muted-foreground">{stat.label}</p>
            </div>
          ))}
        </div>

        {/* Trend bars */}
        <div className="px-8 pb-6">
          <div className="space-y-3">
            <div className="flex items-center gap-3">
              <span className="w-28 text-sm text-muted-foreground">Median price</span>
              <div className="h-2.5 flex-1 rounded-full bg-muted">
                <div className="h-2.5 w-3/4 rounded-full bg-[#6366F1]" />
              </div>
              <span className="text-sm font-medium text-[#4338CA]">+3.2%</span>
            </div>
            <div className="flex items-center gap-3">
              <span className="w-28 text-sm text-muted-foreground">Inventory</span>
              <div className="h-2.5 flex-1 rounded-full bg-muted">
                <div className="h-2.5 w-1/2 rounded-full bg-[#A5B4FC]" />
              </div>
              <span className="text-sm font-medium text-[#64748B]">-8.1%</span>
            </div>
            <div className="flex items-center gap-3">
              <span className="w-28 text-sm text-muted-foreground">Days on mkt</span>
              <div className="h-2.5 flex-1 rounded-full bg-muted">
                <div className="h-2.5 w-2/5 rounded-full bg-[#6366F1]" />
              </div>
              <span className="text-sm font-medium text-[#4338CA]">-12%</span>
            </div>
          </div>
        </div>

        {/* Agent footer */}
        <div className="flex items-center gap-3 rounded-b-2xl border-t border-border bg-muted/50 px-8 py-5">
          <div className="flex h-10 w-10 items-center justify-center rounded-full bg-[#6366F1] text-sm font-bold text-white">
            SJ
          </div>
          <div>
            <p className="text-base font-semibold text-foreground">Sarah Johnson</p>
            <p className="text-sm text-muted-foreground">Compass Real Estate</p>
          </div>
        </div>
      </div>
    </div>
  )
}

export function Hero() {
  return (
    <section className="bg-background px-6 pb-20 pt-16 md:pb-28 md:pt-24">
      <motion.div
        className="mx-auto max-w-4xl text-center"
        initial="hidden"
        whileInView="visible"
        viewport={{ once: true }}
        variants={{
          visible: { transition: { staggerChildren: 0.1 } },
        }}
      >
        <motion.h1
          variants={fadeUp}
          className="text-balance text-5xl font-bold tracking-tight text-foreground md:text-6xl lg:text-7xl"
        >
          Market reports your clients actually want to read
        </motion.h1>
        <motion.p
          variants={fadeUp}
          className="mx-auto mt-6 max-w-2xl text-lg leading-relaxed text-muted-foreground"
        >
          Create beautiful, branded market reports from live MLS data. Schedule
          them once &mdash; they deliver themselves.
        </motion.p>

        <motion.div
          variants={fadeUp}
          className="mt-10 flex flex-col items-center justify-center gap-4 sm:flex-row"
        >
          <a
            href="/register"
            className="inline-flex items-center rounded-full bg-[#6366F1] px-8 py-3.5 text-base font-semibold text-white shadow-lg shadow-[#6366F1]/25 transition-colors hover:bg-[#4F46E5]"
          >
            Start free trial
          </a>
          <a
            href="#email-reports"
            className="inline-flex items-center rounded-full border border-border bg-transparent px-8 py-3.5 text-base font-semibold text-foreground transition-colors hover:bg-muted"
          >
            {"See sample reports \u2193"}
          </a>
        </motion.div>

        <motion.p
          variants={fadeUp}
          className="mt-5 text-sm text-muted-foreground/70"
        >
          {"Free for 14 days \u00B7 No credit card \u00B7 Takes 2 minutes"}
        </motion.p>

        <motion.div variants={fadeUp}>
          <ReportMockup />
        </motion.div>
      </motion.div>
    </section>
  )
}

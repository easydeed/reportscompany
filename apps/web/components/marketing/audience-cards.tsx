"use client"

import Link from "next/link"
import { motion } from "framer-motion"
import { Button } from "@/components/ui/button"
import { User, Building2, ArrowRight } from "lucide-react"

export function AudienceCards() {
  return (
    <section className="py-20 sm:py-24 px-4 sm:px-6 lg:px-8 bg-slate-50">
      <div className="max-w-6xl mx-auto">
        <motion.div
          initial={{ opacity: 0, y: 16 }}
          whileInView={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.4, ease: "easeOut" }}
          viewport={{ once: true, margin: "-50px" }}
          className="text-center mb-14"
        >
          <h2 className="font-display font-bold text-3xl sm:text-4xl text-slate-900 tracking-[-0.02em] mb-3">
            Built for you
          </h2>
          <p className="text-lg text-slate-500">
            Whether you&apos;re an agent or an affiliate, we&apos;ve got you covered
          </p>
        </motion.div>

        <div className="grid md:grid-cols-2 gap-6 max-w-4xl mx-auto">
          {/* For Agents */}
          <motion.div
            initial={{ opacity: 0, y: 16 }}
            whileInView={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.4, ease: "easeOut" }}
            viewport={{ once: true, margin: "-50px" }}
            className="bg-white rounded-2xl border border-slate-200/50 p-8 hover:shadow-md transition-shadow"
          >
            <div className="w-11 h-11 rounded-xl bg-indigo-50 flex items-center justify-center mb-5">
              <User className="w-5 h-5 text-indigo-500" />
            </div>
            <h3 className="font-display font-semibold text-xl text-slate-900 mb-3">
              For agents
            </h3>
            <p className="text-slate-500 leading-relaxed mb-6 text-[15px]">
              Impress clients with branded market reports on autopilot. Generate
              from live MLS data, customize with your branding, and deliver by
              email on a schedule.
            </p>
            <Button
              className="rounded-full bg-indigo-500 hover:bg-indigo-600 text-white px-6"
              asChild
            >
              <Link href="/register">
                Start free trial
                <ArrowRight className="w-4 h-4 ml-2" />
              </Link>
            </Button>
          </motion.div>

          {/* For Affiliates */}
          <motion.div
            initial={{ opacity: 0, y: 16 }}
            whileInView={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.4, delay: 0.08, ease: "easeOut" }}
            viewport={{ once: true, margin: "-50px" }}
            className="bg-white rounded-2xl border border-slate-200/50 p-8 hover:shadow-md transition-shadow"
          >
            <div className="w-11 h-11 rounded-xl bg-amber-50 flex items-center justify-center mb-5">
              <Building2 className="w-5 h-5 text-amber-500" />
            </div>
            <h3 className="font-display font-semibold text-xl text-slate-900 mb-3">
              For title &amp; lending teams
            </h3>
            <p className="text-slate-500 leading-relaxed mb-6 text-[15px]">
              Sponsor agents, strengthen relationships, and track engagement —
              all under one plan with co-branded reports.
            </p>
            <Button
              variant="outline"
              className="rounded-full border-slate-200 hover:bg-slate-50 px-6"
              asChild
            >
              <a href="mailto:sales@trendyreports.com">
                Talk to us
                <ArrowRight className="w-4 h-4 ml-2" />
              </a>
            </Button>
          </motion.div>
        </div>
      </div>
    </section>
  )
}

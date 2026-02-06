"use client"

import { motion } from "framer-motion"
import {
  BarChart3,
  Home,
  TrendingUp,
  DollarSign,
  Layers,
  Image,
  MapPin,
  Star,
} from "lucide-react"

const reportTypes = [
  {
    icon: BarChart3,
    title: "Market Snapshot",
    desc: "Full market overview with stats and trends",
  },
  {
    icon: Home,
    title: "New Listings",
    desc: "Fresh listings for any area",
  },
  {
    icon: TrendingUp,
    title: "Inventory Report",
    desc: "Supply and demand analysis",
  },
  {
    icon: DollarSign,
    title: "Closed Sales",
    desc: "Recent sales and price trends",
  },
  {
    icon: Layers,
    title: "Price Bands",
    desc: "Market segmented by price range",
  },
  {
    icon: Image,
    title: "Listings Gallery",
    desc: "Photo-rich visual grid",
  },
  {
    icon: MapPin,
    title: "Open Houses",
    desc: "Weekend open house schedule",
  },
  {
    icon: Star,
    title: "Featured Listings",
    desc: "Showcase your best properties",
  },
]

const container = {
  hidden: {},
  show: { transition: { staggerChildren: 0.06 } },
} as const
const item = {
  hidden: { opacity: 0, y: 16 },
  show: { opacity: 1, y: 0, transition: { duration: 0.35, ease: "easeOut" as const } },
}

export function ReportTypesGrid() {
  return (
    <section className="py-20 sm:py-24 px-4 sm:px-6 lg:px-8 bg-white">
      <div className="max-w-6xl mx-auto">
        <motion.div
          initial={{ opacity: 0, y: 16 }}
          whileInView={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.4, ease: "easeOut" }}
          viewport={{ once: true, margin: "-50px" }}
          className="text-center mb-14"
        >
          <h2 className="font-display font-bold text-3xl sm:text-4xl text-slate-900 tracking-[-0.02em] mb-3">
            Eight report types. One click each.
          </h2>
          <p className="text-lg text-slate-500 max-w-xl mx-auto">
            Whatever your audience needs, there&apos;s a report for it.
          </p>
        </motion.div>

        <motion.div
          variants={container}
          initial="hidden"
          whileInView="show"
          viewport={{ once: true, margin: "-50px" }}
          className="grid grid-cols-2 lg:grid-cols-4 gap-4"
        >
          {reportTypes.map((rt) => {
            const Icon = rt.icon
            return (
              <motion.div
                key={rt.title}
                variants={item}
                className="bg-white rounded-2xl border border-slate-200/50 p-6 hover:shadow-md transition-shadow"
              >
                <div className="w-10 h-10 rounded-xl bg-indigo-50 flex items-center justify-center mb-4">
                  <Icon className="w-5 h-5 text-indigo-500" />
                </div>
                <h3 className="font-semibold text-sm text-slate-900 mb-1">
                  {rt.title}
                </h3>
                <p className="text-xs text-slate-500 leading-relaxed">
                  {rt.desc}
                </p>
              </motion.div>
            )
          })}
        </motion.div>
      </div>
    </section>
  )
}

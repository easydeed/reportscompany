"use client"

import { motion } from "framer-motion"
import { MapPin, Palette, Send } from "lucide-react"

const steps = [
  {
    icon: MapPin,
    title: "Pick your market",
    description:
      "Choose ZIP codes or cities. Eight report types to match any audience.",
  },
  {
    icon: Palette,
    title: "Add your brand",
    description:
      "Upload your logo and colors. Every report looks like yours.",
  },
  {
    icon: Send,
    title: "Hit send",
    description:
      "Reports deliver on your schedule. Weekly, monthly, or one-time.",
  },
]

const container = {
  hidden: {},
  show: { transition: { staggerChildren: 0.08 } },
} as const
const item = {
  hidden: { opacity: 0, y: 16 },
  show: { opacity: 1, y: 0, transition: { duration: 0.4, ease: "easeOut" as const } },
}

export function HowItWorks() {
  return (
    <section id="how-it-works" className="py-20 sm:py-24 px-4 sm:px-6 lg:px-8 bg-slate-50">
      <div className="max-w-6xl mx-auto">
        <motion.div
          initial={{ opacity: 0, y: 16 }}
          whileInView={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.4, ease: "easeOut" }}
          viewport={{ once: true, margin: "-50px" }}
          className="text-center mb-14"
        >
          <h2 className="font-display font-bold text-3xl sm:text-4xl text-slate-900 tracking-[-0.02em] mb-3">
            From MLS to inbox in three clicks
          </h2>
          <p className="text-lg text-slate-500 max-w-xl mx-auto">
            No spreadsheets. No manual formatting. Just results.
          </p>
        </motion.div>

        <motion.div
          variants={container}
          initial="hidden"
          whileInView="show"
          viewport={{ once: true, margin: "-50px" }}
          className="grid md:grid-cols-3 gap-6"
        >
          {steps.map((step) => {
            const Icon = step.icon
            return (
              <motion.div
                key={step.title}
                variants={item}
                className="bg-white rounded-2xl border border-slate-200/50 p-8 hover:shadow-md transition-shadow"
              >
                <div className="w-11 h-11 rounded-xl bg-indigo-50 flex items-center justify-center mb-5">
                  <Icon className="w-5 h-5 text-indigo-500" />
                </div>
                <h3 className="font-display font-semibold text-lg text-slate-900 mb-2">
                  {step.title}
                </h3>
                <p className="text-slate-500 leading-relaxed text-[15px]">
                  {step.description}
                </p>
              </motion.div>
            )
          })}
        </motion.div>
      </div>
    </section>
  )
}

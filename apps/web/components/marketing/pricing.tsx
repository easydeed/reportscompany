"use client"

import Link from "next/link"
import { motion } from "framer-motion"
import { Button } from "@/components/ui/button"
import { Check } from "lucide-react"
import { cn } from "@/lib/utils"

const plans = [
  {
    name: "Starter",
    tagline: "Get started for free",
    price: "$0",
    period: "/month",
    popular: false,
    features: [
      "50 reports per month",
      "Core report types",
      "Email & PDF delivery",
      "Basic branding",
    ],
  },
  {
    name: "Pro",
    tagline: "For individual agents",
    price: "$29",
    period: "/month",
    popular: true,
    features: [
      "300 reports per month",
      "All 8 report types",
      "Automated scheduling",
      "Full white-label branding",
      "Priority support",
    ],
  },
  {
    name: "Team",
    tagline: "For teams & affiliates",
    price: "$99",
    period: "/month",
    popular: false,
    features: [
      "Unlimited reports",
      "Sponsor agents",
      "Admin dashboard",
      "Co-branded reports",
      "Dedicated support",
    ],
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

export function Pricing() {
  return (
    <section
      id="pricing"
      className="py-20 sm:py-24 px-4 sm:px-6 lg:px-8 bg-white"
    >
      <div className="max-w-6xl mx-auto">
        <motion.div
          initial={{ opacity: 0, y: 16 }}
          whileInView={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.4, ease: "easeOut" }}
          viewport={{ once: true, margin: "-50px" }}
          className="text-center mb-14"
        >
          <h2 className="font-display font-bold text-3xl sm:text-4xl text-slate-900 tracking-[-0.02em] mb-3">
            Simple, transparent pricing
          </h2>
          <p className="text-lg text-slate-500 max-w-xl mx-auto">
            Choose the plan that fits your business. Upgrade or downgrade anytime.
          </p>
        </motion.div>

        <motion.div
          variants={container}
          initial="hidden"
          whileInView="show"
          viewport={{ once: true, margin: "-50px" }}
          className="grid md:grid-cols-3 gap-6 max-w-5xl mx-auto"
        >
          {plans.map((plan) => (
            <motion.div
              key={plan.name}
              variants={item}
              className={cn(
                "relative rounded-2xl p-8 transition-shadow",
                plan.popular
                  ? "bg-white border-2 border-indigo-300 shadow-lg hover:shadow-xl"
                  : "bg-white border border-slate-200/50 hover:shadow-md"
              )}
            >
              {plan.popular && (
                <div className="absolute -top-3.5 left-1/2 -translate-x-1/2 bg-indigo-500 text-white text-xs font-semibold px-4 py-1 rounded-full">
                  Most popular
                </div>
              )}

              <div className="mb-6">
                <h3 className="font-display font-semibold text-xl text-slate-900 mb-1">
                  {plan.name}
                </h3>
                <p className="text-sm text-slate-500">{plan.tagline}</p>
              </div>

              <div className="mb-6">
                <span className="font-display font-bold text-4xl text-slate-900">
                  {plan.price}
                </span>
                <span className="text-slate-500 text-base">{plan.period}</span>
              </div>

              <ul className="space-y-3 mb-8">
                {plan.features.map((f) => (
                  <li key={f} className="flex items-start gap-2.5 text-sm">
                    <Check className="w-4 h-4 text-indigo-500 flex-shrink-0 mt-0.5" />
                    <span className="text-slate-600">{f}</span>
                  </li>
                ))}
              </ul>

              <Button
                className={cn(
                  "w-full rounded-full h-11",
                  plan.popular
                    ? "bg-indigo-500 hover:bg-indigo-600 text-white"
                    : "bg-transparent border border-slate-200 text-slate-700 hover:bg-slate-50"
                )}
                asChild
              >
                <Link href="/register">Start free trial</Link>
              </Button>
            </motion.div>
          ))}
        </motion.div>

        <motion.p
          initial={{ opacity: 0 }}
          whileInView={{ opacity: 1 }}
          transition={{ duration: 0.4, delay: 0.2 }}
          viewport={{ once: true }}
          className="text-center text-sm text-slate-400 mt-10"
        >
          All plans include 14-day free trial · No credit card required
        </motion.p>
      </div>
    </section>
  )
}

"use client";

import { motion } from "framer-motion";
import { Check } from "lucide-react";

const fadeUp = {
  hidden: { opacity: 0, y: 16 },
  visible: { opacity: 1, y: 0, transition: { duration: 0.4 } },
};

const plans = [
  {
    name: "Free",
    price: "$0",
    priceSub: "No credit card required",
    features: [
      "3 Market Reports / month",
      "1 Automated Schedule",
      "1 Property Report / month",
      "CMA Lead Page",
    ],
    cta: "Start Free",
    featured: false,
  },
  {
    name: "Starter",
    price: "$29",
    priceSub: "per month",
    features: [
      "25 Market Reports / month",
      "3 Automated Schedules",
      "5 Property Reports / month",
      "CMA Lead Page",
      "AI Market Insights",
      "CSV Contact Import",
    ],
    cta: "Start Free, Upgrade Later",
    featured: true,
  },
  {
    name: "Pro",
    price: "$59",
    priceSub: "per month",
    features: [
      "Unlimited Market Reports",
      "Unlimited Schedules",
      "25 Property Reports / month",
      "CMA Lead Page",
      "AI Market Insights",
      "Priority Generation",
    ],
    cta: "Start Free, Upgrade Later",
    featured: false,
  },
];

export function Pricing() {
  return (
    <section id="pricing" className="bg-background px-6 py-20 md:py-28">
      <motion.div
        className="mx-auto max-w-6xl"
        initial="hidden"
        whileInView="visible"
        viewport={{ once: true }}
        variants={{ visible: { transition: { staggerChildren: 0.1 } } }}
      >
        <motion.div variants={fadeUp} className="text-center">
          <h2 className="text-4xl font-bold tracking-tight text-foreground md:text-5xl">
            Simple, transparent pricing
          </h2>
          <p className="mt-4 text-muted-foreground">
            Start free. Upgrade when you're ready.
          </p>
        </motion.div>

        <div className="mt-14 grid gap-8 md:grid-cols-3">
          {plans.map((plan) => (
            <motion.div
              key={plan.name}
              variants={fadeUp}
              className={`relative rounded-2xl border p-8 flex flex-col ${
                plan.featured
                  ? "border-transparent ring-2 ring-[#6366F1] bg-card shadow-lg shadow-indigo-100"
                  : "border-[#F1F5F9] bg-card"
              }`}
            >
              {plan.featured && (
                <span className="absolute -top-3 left-1/2 -translate-x-1/2 rounded-full bg-[#6366F1] px-3 py-1 text-xs font-semibold text-white whitespace-nowrap">
                  Most Popular
                </span>
              )}

              <h3 className="text-xl font-bold text-foreground">{plan.name}</h3>
              <div className="mt-3 flex items-baseline gap-1">
                <span className="text-4xl font-bold text-foreground">
                  {plan.price}
                </span>
                {plan.price !== "$0" && (
                  <span className="text-muted-foreground">/month</span>
                )}
              </div>
              <p className="mt-1 text-sm text-muted-foreground">{plan.priceSub}</p>

              <ul className="mt-6 space-y-3 flex-1">
                {plan.features.map((f) => (
                  <li key={f} className="flex items-start gap-3 text-sm text-foreground">
                    <Check className="h-4 w-4 shrink-0 text-[#6366F1] mt-0.5" />
                    {f}
                  </li>
                ))}
              </ul>

              <a
                href="/register"
                className={`mt-8 flex w-full items-center justify-center rounded-full px-6 py-3 text-sm font-semibold transition-colors ${
                  plan.featured
                    ? "bg-[#6366F1] text-white hover:bg-[#4F46E5]"
                    : "border border-border bg-transparent text-foreground hover:bg-muted"
                }`}
              >
                {plan.cta}
              </a>
            </motion.div>
          ))}
        </div>

        <motion.p
          variants={fadeUp}
          className="mt-10 text-center text-sm text-muted-foreground/70"
        >
          All plans include branded PDFs, email delivery, and your CMA lead page. Upgrade or downgrade anytime.
        </motion.p>
      </motion.div>
    </section>
  );
}

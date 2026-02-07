"use client"

import { motion } from "framer-motion"
import { MapPin, Palette, Send } from "lucide-react"

const fadeUp = {
  hidden: { opacity: 0, y: 16 },
  visible: { opacity: 1, y: 0, transition: { duration: 0.4 } },
}

const steps = [
  {
    icon: MapPin,
    title: "Pick your market",
    description:
      "Choose your city, zip code, or custom MLS area to pull live data.",
  },
  {
    icon: Palette,
    title: "Add your brand",
    description:
      "Upload your logo, pick your colors, and add your contact info.",
  },
  {
    icon: Send,
    title: "Hit send",
    description:
      "Deliver reports by email on a schedule or download print-ready PDFs.",
  },
]

export function HowItWorks() {
  return (
    <section id="how-it-works" className="bg-[#F8FAFC] px-6 py-20 md:py-28">
      <motion.div
        className="mx-auto max-w-7xl"
        initial="hidden"
        whileInView="visible"
        viewport={{ once: true }}
        variants={{ visible: { transition: { staggerChildren: 0.1 } } }}
      >
        <motion.h2
          variants={fadeUp}
          className="text-center text-4xl font-bold tracking-tight text-foreground md:text-5xl"
        >
          From MLS to inbox in three clicks
        </motion.h2>
        <motion.p
          variants={fadeUp}
          className="mx-auto mt-4 max-w-xl text-center text-muted-foreground"
        >
          No design skills needed. Just pick your market, brand it, and go.
        </motion.p>

        <div className="mt-14 grid gap-8 md:grid-cols-3">
          {steps.map((step) => (
            <motion.div
              key={step.title}
              variants={fadeUp}
              className="rounded-2xl border border-[#F1F5F9] bg-card p-8 transition-shadow hover:shadow-md"
            >
              <div className="flex h-12 w-12 items-center justify-center rounded-full bg-[#EEF2FF]">
                <step.icon className="h-6 w-6 text-[#6366F1]" />
              </div>
              <h3 className="mt-5 text-xl font-semibold text-foreground">
                {step.title}
              </h3>
              <p className="mt-2 leading-relaxed text-muted-foreground">
                {step.description}
              </p>
            </motion.div>
          ))}
        </div>
      </motion.div>
    </section>
  )
}

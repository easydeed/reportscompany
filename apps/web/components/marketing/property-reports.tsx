"use client"

import { motion } from "framer-motion"
import { FileText, MapPin, BarChart3, QrCode } from "lucide-react"

const fadeUp = {
  hidden: { opacity: 0, y: 16 },
  visible: { opacity: 1, y: 0, transition: { duration: 0.4 } },
}

const features = [
  {
    icon: FileText,
    title: "5 designer templates",
    description:
      "Bold, Classic, Elegant, Modern, and Teal \u2014 each with its own personality",
  },
  {
    icon: MapPin,
    title: "Aerial maps & hero images",
    description:
      "Google Maps integration with satellite views of the property",
  },
  {
    icon: BarChart3,
    title: "Comparable sales analysis",
    description:
      "Up to 6 comps with price, sqft, beds/baths, and distance",
  },
  {
    icon: QrCode,
    title: "Built-in lead capture",
    description:
      "Every report gets a QR code that links to a branded landing page",
  },
]

export function PropertyReports() {
  return (
    <section className="bg-[#F8FAFC] px-6 py-20 md:py-28">
      <motion.div
        className="mx-auto max-w-7xl"
        initial="hidden"
        whileInView="visible"
        viewport={{ once: true }}
        variants={{ visible: { transition: { staggerChildren: 0.1 } } }}
      >
        <motion.div variants={fadeUp} className="text-center">
          <h2 className="text-4xl font-bold tracking-tight text-foreground md:text-5xl">
            Stunning property reports that win listings
          </h2>
          <p className="mx-auto mt-4 max-w-2xl text-muted-foreground">
            Generate branded CMA-style reports with 5 designer templates. Every
            report includes a QR code that captures leads automatically.
          </p>
        </motion.div>

        <div className="mt-14 grid items-center gap-12 lg:grid-cols-2">
          {/* Left — Feature list */}
          <motion.div variants={fadeUp} className="space-y-6">
            {features.map((f) => (
              <div key={f.title} className="flex gap-4">
                <div className="flex h-11 w-11 shrink-0 items-center justify-center rounded-full bg-[#EEF2FF]">
                  <f.icon className="h-5 w-5 text-[#6366F1]" />
                </div>
                <div>
                  <p className="font-semibold text-foreground">{f.title}</p>
                  <p className="mt-0.5 text-sm leading-relaxed text-muted-foreground">
                    {f.description}
                  </p>
                </div>
              </div>
            ))}
          </motion.div>

          {/* Right — Report mockup stack */}
          <motion.div
            variants={fadeUp}
            className="relative mx-auto flex w-full max-w-md items-center justify-center"
          >
            {/* Back card (peek) */}
            <div className="absolute -left-3 top-4 h-full w-full -rotate-3 rounded-2xl border border-border bg-card shadow-lg" />

            {/* Front card */}
            <div className="relative w-full rotate-1 overflow-hidden rounded-2xl border border-border bg-card shadow-xl">
              {/* Header gradient */}
              <div className="bg-gradient-to-br from-[#1E293B] to-[#334155] px-6 py-5">
                <p className="text-xs font-medium uppercase tracking-widest text-white/60">
                  Property Report
                </p>
                <p className="mt-1 text-lg font-bold text-white">
                  Elegant Template
                </p>
              </div>

              {/* Hero photo area */}
              <div className="relative h-48 bg-gradient-to-br from-[#E0E7FF] to-[#C7D2FE]">
                <div className="absolute inset-0 flex items-center justify-center">
                  <div className="text-center">
                    <div className="mx-auto flex h-12 w-12 items-center justify-center rounded-full bg-white/80">
                      <MapPin className="h-6 w-6 text-[#6366F1]" />
                    </div>
                    <p className="mt-2 text-sm font-medium text-[#334155]">
                      Property Photo
                    </p>
                  </div>
                </div>
              </div>

              {/* Property details */}
              <div className="px-6 py-5">
                <p className="text-lg font-bold text-foreground">
                  1205 Lakeview Blvd
                </p>
                <p className="mt-1 text-sm text-muted-foreground">
                  Austin, TX 78703
                </p>
                <div className="mt-3 flex gap-3">
                  {["4 BD", "3 BA", "2,450 sqft"].map((spec) => (
                    <span
                      key={spec}
                      className="inline-flex items-center rounded-full bg-[#EEF2FF] px-3 py-1 text-xs font-medium text-[#6366F1]"
                    >
                      {spec}
                    </span>
                  ))}
                </div>

                {/* Comp summary row */}
                <div className="mt-4 grid grid-cols-3 gap-2">
                  {[
                    { label: "List price", value: "$875,000" },
                    { label: "Comps avg", value: "$842,000" },
                    { label: "Price/sqft", value: "$357" },
                  ].map((s) => (
                    <div
                      key={s.label}
                      className="rounded-lg bg-[#F8FAFC] p-2 text-center"
                    >
                      <p className="text-sm font-bold text-foreground">
                        {s.value}
                      </p>
                      <p className="text-[10px] text-muted-foreground">
                        {s.label}
                      </p>
                    </div>
                  ))}
                </div>

                {/* Agent + QR */}
                <div className="mt-4 flex items-center justify-between border-t border-border pt-4">
                  <div className="flex items-center gap-3">
                    <div className="flex h-9 w-9 items-center justify-center rounded-full bg-[#6366F1] text-xs font-bold text-white">
                      SJ
                    </div>
                    <div>
                      <p className="text-sm font-semibold text-foreground">
                        Sarah Johnson
                      </p>
                      <p className="text-xs text-muted-foreground">
                        Compass Realty
                      </p>
                    </div>
                  </div>
                  {/* QR Code mockup */}
                  <div className="flex h-12 w-12 items-center justify-center rounded-md border border-border bg-white">
                    <QrCode className="h-8 w-8 text-[#334155]" />
                  </div>
                </div>
              </div>
            </div>
          </motion.div>
        </div>
      </motion.div>
    </section>
  )
}

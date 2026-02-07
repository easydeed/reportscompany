"use client"

import { motion } from "framer-motion"
import { QrCode, FileInput, Bell, MapPin, Smartphone } from "lucide-react"

const fadeUp = {
  hidden: { opacity: 0, y: 16 },
  visible: { opacity: 1, y: 0, transition: { duration: 0.4 } },
}

const features = [
  {
    icon: QrCode,
    title: "QR codes on every report",
    description:
      "Every property report includes a unique QR code and short link. Print it on flyers, postcards, or yard signs.",
  },
  {
    icon: Smartphone,
    title: "Branded landing pages",
    description:
      "Prospects land on a mobile-optimized page with property details, photos, and a simple contact form.",
  },
  {
    icon: FileInput,
    title: "Instant lead capture",
    description:
      "Name, email, phone \u2014 captured in one tap. Leads flow straight into your contact list automatically.",
  },
  {
    icon: Bell,
    title: "Real-time notifications",
    description:
      "Get an email and optional SMS alert the moment a lead comes in. Follow up while they\u2019re still interested.",
  },
]

export function LeadCapture() {
  return (
    <section id="lead-capture" className="bg-background px-6 py-20 md:py-28">
      <motion.div
        className="mx-auto max-w-7xl"
        initial="hidden"
        whileInView="visible"
        viewport={{ once: true }}
        variants={{ visible: { transition: { staggerChildren: 0.1 } } }}
      >
        <motion.div variants={fadeUp} className="text-center">
          <h2 className="text-4xl font-bold tracking-tight text-foreground md:text-5xl">
            Every report is a lead magnet
          </h2>
          <p className="mx-auto mt-4 max-w-2xl text-muted-foreground">
            QR codes and landing pages turn your property reports into 24/7 lead
            generation machines.
          </p>
        </motion.div>

        <div className="mt-14 grid items-center gap-12 lg:grid-cols-2">
          {/* Left — Visual mockup */}
          <motion.div
            variants={fadeUp}
            className="relative mx-auto flex w-full max-w-md items-center justify-center"
          >
            {/* Notification card (behind, offset) */}
            <div className="absolute -right-4 top-8 z-0 w-72 rounded-2xl border border-border bg-card p-5 shadow-lg">
              <div className="flex items-center gap-3">
                <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-full bg-[#EEF2FF]">
                  <Bell className="h-5 w-5 text-[#6366F1]" />
                </div>
                <div>
                  <p className="text-sm font-bold text-foreground">New Lead!</p>
                  <p className="text-xs text-muted-foreground">Just now</p>
                </div>
              </div>
              <p className="mt-3 text-sm leading-relaxed text-muted-foreground">
                <span className="font-semibold text-foreground">
                  Sarah Johnson
                </span>{" "}
                viewed{" "}
                <span className="font-semibold text-foreground">
                  1205 Lakeview Blvd
                </span>{" "}
                and requested more information.
              </p>
              <div className="mt-3 grid grid-cols-2 gap-2">
                <div className="rounded-lg bg-[#F8FAFC] p-2.5">
                  <p className="text-[10px] text-muted-foreground">Email</p>
                  <p className="text-xs font-medium text-foreground">
                    sarah@email.com
                  </p>
                </div>
                <div className="rounded-lg bg-[#F8FAFC] p-2.5">
                  <p className="text-[10px] text-muted-foreground">Phone</p>
                  <p className="text-xs font-medium text-foreground">
                    (512) 555-0142
                  </p>
                </div>
              </div>
              <div className="mt-3 flex gap-2">
                <div className="flex-1 rounded-lg bg-[#6366F1] py-2 text-center text-xs font-semibold text-white">
                  Call Now
                </div>
                <div className="flex-1 rounded-lg border border-border py-2 text-center text-xs font-semibold text-foreground">
                  Send Email
                </div>
              </div>
            </div>

            {/* Phone frame (front) */}
            <div className="relative z-10 w-64 shrink-0 overflow-hidden rounded-3xl border-8 border-[#1E293B] bg-card shadow-2xl">
              <div className="bg-gradient-to-br from-[#6366F1] to-[#818CF8] px-5 py-5">
                <div className="flex items-center gap-2">
                  <MapPin className="h-4 w-4 text-white/80" />
                  <p className="text-xs font-medium text-white/70">
                    Property Details
                  </p>
                </div>
                <p className="mt-1 text-sm font-bold text-white">
                  1205 Lakeview Blvd
                </p>
                <p className="text-xs text-white/60">Austin, TX 78703</p>
              </div>

              <div className="h-28 bg-gradient-to-br from-[#E0E7FF] to-[#C7D2FE]" />

              <div className="px-4 py-4">
                <div className="rounded-lg bg-[#6366F1] px-4 py-2.5 text-center text-sm font-semibold text-white">
                  Get More Information
                </div>
                <div className="mt-3 space-y-2">
                  {["Full name", "Email address", "Phone number"].map(
                    (placeholder) => (
                      <div
                        key={placeholder}
                        className="rounded-lg border border-border px-3 py-2"
                      >
                        <p className="text-xs text-muted-foreground">
                          {placeholder}
                        </p>
                      </div>
                    ),
                  )}
                </div>
                <div className="mt-3 rounded-lg bg-[#1E293B] px-4 py-2.5 text-center text-sm font-semibold text-white">
                  Send Request
                </div>
              </div>
            </div>
          </motion.div>

          {/* Right — Feature list */}
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
        </div>
      </motion.div>
    </section>
  )
}

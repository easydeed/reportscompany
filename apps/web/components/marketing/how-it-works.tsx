"use client";

import { motion } from "framer-motion";
import { MapPin, Palette, Send, Check, ChevronRight } from "lucide-react";

const fadeUp = {
  hidden: { opacity: 0, y: 20 },
  visible: { opacity: 1, y: 0, transition: { duration: 0.5, ease: "easeOut" as const } },
};

const steps = [
  {
    number: "01",
    icon: MapPin,
    title: "Pick your market",
    description:
      "Choose a city, zip, or neighborhood. We pull the latest data from your MLS automatically.",
    visual: "map",
  },
  {
    number: "02",
    icon: Palette,
    title: "Make it yours",
    description:
      "Add your logo, pick your brand colors, and choose a template. Every report looks like it came from your marketing department.",
    visual: "brand",
  },
  {
    number: "03",
    icon: Send,
    title: "Set it and forget it",
    description:
      "Schedule weekly or monthly delivery. Your sphere gets a polished, branded report without you lifting a finger.",
    visual: "schedule",
  },
];

function StepVisual({ type }: { type: string }) {
  if (type === "map") {
    return (
      <div className="relative h-full w-full overflow-hidden rounded-xl bg-gradient-to-br from-[#EEF2FF] to-[#E0E7FF]">
        <div className="absolute inset-0">
          <img src="https://images.unsplash.com/photo-1569336415962-a4bd9f69cd83?w=600&h=400&fit=crop" alt="" className="w-full h-full object-cover" />
          <div className="absolute inset-0 bg-white/[0.88]" />
        </div>
        <div className="relative z-10 h-full w-full p-4">
          <div className="absolute inset-0 opacity-20">
            {[...Array(6)].map((_, i) => (
              <div
                key={i}
                className="absolute h-px w-full bg-[#6366F1]"
                style={{ top: `${(i + 1) * 16.67}%` }}
              />
            ))}
            {[...Array(6)].map((_, i) => (
              <div
                key={i}
                className="absolute h-full w-px bg-[#6366F1]"
                style={{ left: `${(i + 1) * 16.67}%` }}
              />
            ))}
          </div>
          <div className="absolute left-1/4 top-1/3 flex h-8 w-8 items-center justify-center rounded-full bg-[#6366F1] shadow-lg">
            <MapPin className="h-4 w-4 text-white" />
          </div>
          <div className="absolute right-1/3 top-1/2 flex h-6 w-6 items-center justify-center rounded-full bg-[#818CF8] shadow-md">
            <MapPin className="h-3 w-3 text-white" />
          </div>
          <div className="absolute bottom-1/4 left-1/2 flex h-7 w-7 items-center justify-center rounded-full bg-[#4338CA] shadow-md">
            <MapPin className="h-3.5 w-3.5 text-white" />
          </div>
          <div className="absolute bottom-4 left-4 right-4 flex items-center gap-2 rounded-lg bg-white px-3 py-2 shadow-md">
            <MapPin className="h-4 w-4 text-[#6366F1]" />
            <span className="text-sm text-muted-foreground">Irvine, CA 92618</span>
            <Check className="ml-auto h-4 w-4 text-[#6366F1]" />
          </div>
        </div>
      </div>
    );
  }

  if (type === "brand") {
    return (
      <div className="relative h-full w-full overflow-hidden rounded-xl bg-gradient-to-br from-[#EEF2FF] to-[#E0E7FF]">
        <div className="absolute inset-0">
          <img src="https://images.unsplash.com/photo-1513364776144-60967b0f800f?w=600&h=400&fit=crop" alt="" className="w-full h-full object-cover" />
          <div className="absolute inset-0 bg-white/[0.88]" />
        </div>
        <div className="relative z-10 h-full w-full p-4">
          <div className="absolute right-4 top-4 flex gap-2">
            <div className="h-8 w-8 rounded-full bg-[#6366F1] shadow-md ring-2 ring-white" />
            <div className="h-8 w-8 rounded-full bg-[#1E293B] shadow-md ring-2 ring-white" />
            <div className="h-8 w-8 rounded-full bg-white shadow-md ring-2 ring-[#E2E8F0]" />
          </div>
          <div className="absolute left-4 top-4 flex h-12 w-12 items-center justify-center rounded-xl bg-white shadow-md">
            <span className="text-lg font-bold text-[#6366F1]">TR</span>
          </div>
          <div className="absolute bottom-4 left-4 right-4 flex gap-2">
            <div className="flex-1 rounded-lg bg-white p-2 shadow-md ring-2 ring-[#6366F1]">
              <div className="h-2 w-8 rounded bg-[#6366F1]" />
              <div className="mt-2 h-1.5 w-full rounded bg-[#E2E8F0]" />
              <div className="mt-1 h-1.5 w-3/4 rounded bg-[#E2E8F0]" />
            </div>
            <div className="flex-1 rounded-lg bg-white p-2 opacity-60 shadow-md">
              <div className="h-2 w-8 rounded bg-[#1E293B]" />
              <div className="mt-2 h-1.5 w-full rounded bg-[#E2E8F0]" />
              <div className="mt-1 h-1.5 w-3/4 rounded bg-[#E2E8F0]" />
            </div>
            <div className="flex-1 rounded-lg bg-white p-2 opacity-60 shadow-md">
              <div className="h-2 w-8 rounded bg-[#4338CA]" />
              <div className="mt-2 h-1.5 w-full rounded bg-[#E2E8F0]" />
              <div className="mt-1 h-1.5 w-3/4 rounded bg-[#E2E8F0]" />
            </div>
          </div>
          <div className="absolute left-1/2 top-1/2 -translate-x-1/2 -translate-y-1/2">
            <Palette className="h-10 w-10 text-[#6366F1] opacity-20" />
          </div>
        </div>
      </div>
    );
  }

  // Schedule visual
  return (
    <div className="relative h-full w-full overflow-hidden rounded-xl bg-gradient-to-br from-[#EEF2FF] to-[#E0E7FF]">
      <div className="absolute inset-0">
        <img src="https://images.unsplash.com/photo-1506784983877-45594efa4cbe?w=600&h=400&fit=crop" alt="" className="w-full h-full object-cover" />
        <div className="absolute inset-0 bg-white/[0.88]" />
      </div>
      <div className="relative z-10 h-full w-full p-4">
        <div className="absolute left-4 right-4 top-4 rounded-lg bg-white p-3 shadow-md">
          <div className="flex items-center justify-between">
            <span className="text-sm font-semibold text-foreground">March 2026</span>
            <div className="flex gap-1">
              <div className="h-2 w-2 rounded-full bg-[#6366F1]" />
              <div className="h-2 w-2 rounded-full bg-[#E2E8F0]" />
            </div>
          </div>
          <div className="mt-2 grid grid-cols-7 gap-1 text-center text-[10px] text-muted-foreground">
            {["S", "M", "T", "W", "T", "F", "S"].map((d, i) => (
              <span key={i}>{d}</span>
            ))}
          </div>
          <div className="mt-1 grid grid-cols-7 gap-1 text-center text-xs">
            {[...Array(7)].map((_, i) => (
              <div
                key={i}
                className={`flex h-5 w-5 items-center justify-center rounded-full ${
                  i === 1 || i === 4
                    ? "bg-[#6366F1] text-white"
                    : "text-muted-foreground"
                }`}
              >
                {i + 1}
              </div>
            ))}
          </div>
        </div>
        <div className="absolute bottom-4 left-4 right-4 rounded-lg bg-white p-3 shadow-md">
          <div className="flex items-center gap-2">
            <div className="flex h-8 w-8 items-center justify-center rounded-full bg-[#DCFCE7]">
              <Check className="h-4 w-4 text-[#16A34A]" />
            </div>
            <div>
              <p className="text-xs font-medium text-foreground">Report sent</p>
              <p className="text-[10px] text-muted-foreground">47 contacts received</p>
            </div>
          </div>
        </div>
        <div className="absolute left-1/2 top-1/2 -translate-x-1/2 -translate-y-1/2">
          <Send className="h-10 w-10 text-[#6366F1] opacity-20" />
        </div>
      </div>
    </div>
  );
}

export function HowItWorks() {
  return (
    <section id="how-it-works" className="bg-[#F8FAFC] px-6 py-20 md:py-28">
      <motion.div
        className="mx-auto max-w-7xl"
        initial="hidden"
        whileInView="visible"
        viewport={{ once: true, margin: "-100px" }}
        variants={{ visible: { transition: { staggerChildren: 0.15 } } }}
      >
        <motion.h2
          variants={fadeUp}
          className="text-center text-4xl font-bold tracking-tight text-foreground md:text-5xl"
        >
          {"From MLS data to your clients' inbox in three steps"}
        </motion.h2>
        <motion.p
          variants={fadeUp}
          className="mx-auto mt-4 max-w-xl text-center text-muted-foreground"
        >
          No design skills needed. No marketing team required.
        </motion.p>

        {/* Steps with alternating layout */}
        <div className="mt-16 space-y-12 md:space-y-0">
          {steps.map((step, index) => (
            <motion.div
              key={step.title}
              variants={fadeUp}
              className={`flex flex-col gap-8 md:flex-row md:items-center md:gap-12 ${
                index % 2 === 1 ? "md:flex-row-reverse" : ""
              } ${index > 0 ? "md:mt-16" : ""}`}
            >
              {/* Visual */}
              <div className="h-64 flex-1 md:h-80">
                <StepVisual type={step.visual} />
              </div>

              {/* Content */}
              <div className="flex-1">
                <div className="flex items-center gap-4">
                  <span className="text-5xl font-bold text-[#E0E7FF]">
                    {step.number}
                  </span>
                  <div className="flex h-12 w-12 items-center justify-center rounded-full bg-[#6366F1]">
                    <step.icon className="h-5 w-5 text-white" />
                  </div>
                </div>
                <h3 className="mt-4 text-2xl font-bold text-foreground">
                  {step.title}
                </h3>
                <p className="mt-3 text-lg leading-relaxed text-muted-foreground">
                  {step.description}
                </p>
                {index < steps.length - 1 && (
                  <div className="mt-6 hidden items-center gap-2 text-sm font-medium text-[#6366F1] md:flex">
                    <span>Next step</span>
                    <ChevronRight className="h-4 w-4" />
                  </div>
                )}
              </div>
            </motion.div>
          ))}
        </div>

        {/* Bottom CTA */}
        <motion.div variants={fadeUp} className="mt-16 text-center">
          <a
            href="/register"
            className="inline-flex items-center gap-2 rounded-full bg-[#6366F1] px-8 py-3 text-sm font-semibold text-white transition-colors hover:bg-[#4F46E5]"
          >
            Try it free
            <ChevronRight className="h-4 w-4" />
          </a>
          <p className="mt-3 text-sm text-muted-foreground">
            Your first report is ready in under 2 minutes
          </p>
        </motion.div>
      </motion.div>
    </section>
  );
}

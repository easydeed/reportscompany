"use client";

import { motion } from "framer-motion";
import { Star } from "lucide-react";

const fadeUp = {
  hidden: { opacity: 0, y: 16 },
  visible: { opacity: 1, y: 0, transition: { duration: 0.4 } },
};

const testimonials = [
  {
    quote:
      "I used to spend 2 hours a week on market updates. Now it takes me 2 minutes.",
    name: "Jessica M.",
    title: "Agent, Orange County",
    initials: "JM",
    color: "bg-[#6366F1]",
  },
  {
    quote:
      "My clients actually reply to these reports. That never happened with my old newsletter.",
    name: "David C.",
    title: "Agent, Irvine",
    initials: "DC",
    color: "bg-[#4338CA]",
  },
  {
    quote:
      "I brought a property report to a listing appointment and the seller signed that day.",
    name: "Sarah T.",
    title: "Agent, Newport Beach",
    initials: "ST",
    color: "bg-[#818CF8]",
  },
];

export function Testimonials() {
  return (
    <section className="bg-[#F8FAFC] px-6 py-16 md:py-20">
      <motion.div
        className="mx-auto max-w-7xl"
        initial="hidden"
        whileInView="visible"
        viewport={{ once: true }}
        variants={{ visible: { transition: { staggerChildren: 0.1 } } }}
      >
        <div className="grid gap-8 md:grid-cols-3">
          {testimonials.map((t) => (
            <motion.div
              key={t.name}
              variants={fadeUp}
              className="rounded-2xl border border-border bg-card p-8"
            >
              {/* Stars */}
              <div className="flex gap-1">
                {[...Array(5)].map((_, i) => (
                  <Star
                    key={`star-${t.name}-${i}`}
                    className="h-4 w-4 fill-[#FBBF24] text-[#FBBF24]"
                  />
                ))}
              </div>

              {/* Quote */}
              <p className="mt-4 leading-relaxed text-foreground">
                "{t.quote}"
              </p>

              {/* Author */}
              <div className="mt-6 flex items-center gap-3">
                <div
                  className={`flex h-10 w-10 items-center justify-center rounded-full text-xs font-bold text-white ${t.color}`}
                >
                  {t.initials}
                </div>
                <div>
                  <p className="text-sm font-semibold text-foreground">
                    {t.name}
                  </p>
                  <p className="text-xs text-muted-foreground">{t.title}</p>
                </div>
              </div>
            </motion.div>
          ))}
        </div>
      </motion.div>
    </section>
  );
}

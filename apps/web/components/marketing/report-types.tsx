"use client";

import { useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import {
  BarChart3,
  Home,
  TrendingUp,
  DollarSign,
  Layers,
  ImageIcon,
  MapPin,
  Star,
  Users,
  Briefcase,
  Sparkles,
  ChevronDown,
} from "lucide-react";

const fadeUp = {
  hidden: { opacity: 0, y: 16 },
  visible: { opacity: 1, y: 0, transition: { duration: 0.4 } },
};

const useCases = [
  {
    icon: Users,
    title: "Stay top of mind with your sphere",
    description:
      "Market Snapshot and Inventory reports give your contacts the numbers they actually want — on autopilot.",
    color: "bg-[#EEF2FF]",
    iconColor: "text-[#6366F1]",
  },
  {
    icon: Briefcase,
    title: "Win the listing appointment",
    description:
      "Walk in with a Closed Sales report and a Property Report. Show sellers you know their neighborhood better than anyone.",
    color: "bg-[#F0FDF4]",
    iconColor: "text-[#16A34A]",
  },
  {
    icon: Home,
    title: "Impress buyers at every showing",
    description:
      "New Listings, Open Houses, and Listings Gallery reports keep buyers engaged and position you as the local expert.",
    color: "bg-[#FEF3C7]",
    iconColor: "text-[#D97706]",
  },
  {
    icon: Sparkles,
    title: "Showcase your listings",
    description:
      "Featured Listings reports put your best properties front and center with professional layouts and your branding.",
    color: "bg-[#FCE7F3]",
    iconColor: "text-[#DB2777]",
  },
];

const types = [
  {
    icon: BarChart3,
    title: "Market Snapshot",
    desc: "The essential numbers your sphere wants — median price, inventory, and days on market.",
  },
  {
    icon: Home,
    title: "New Listings",
    desc: "Show your buyers what just came on the market before anyone else.",
  },
  {
    icon: TrendingUp,
    title: "Inventory Report",
    desc: "Is it a buyer's market or a seller's market? This report answers it with data.",
  },
  {
    icon: DollarSign,
    title: "Closed Sales",
    desc: "Walk into a listing appointment with the sold data that wins the conversation.",
  },
  {
    icon: Layers,
    title: "Price Bands",
    desc: "See where the action is — broken down by price range for your market.",
  },
  {
    icon: ImageIcon,
    title: "Listings Gallery",
    desc: "A beautiful photo grid of active listings. Great for email or print.",
  },
  {
    icon: MapPin,
    title: "Open Houses",
    desc: "Give your buyers a weekend game plan with every upcoming open house.",
  },
  {
    icon: Star,
    title: "Featured Listings",
    desc: "Put your listings in the spotlight with a dedicated, branded report.",
  },
];

export function ReportTypes() {
  const [showAll, setShowAll] = useState(false);

  return (
    <section id="reports" className="bg-background px-6 py-20 md:py-28">
      <motion.div
        className="mx-auto max-w-7xl"
        initial="hidden"
        whileInView="visible"
        viewport={{ once: true }}
        variants={{ visible: { transition: { staggerChildren: 0.05 } } }}
      >
        <motion.h2
          variants={fadeUp}
          className="text-center text-4xl font-bold tracking-tight text-foreground md:text-5xl"
        >
          The right report for every conversation
        </motion.h2>
        <motion.p
          variants={fadeUp}
          className="mx-auto mt-4 max-w-2xl text-center text-muted-foreground"
        >
          Whether you're farming a neighborhood, prepping a listing appointment,
          or keeping your sphere informed — there's a report for that.
        </motion.p>

        {/* Use-case cards */}
        <div className="mt-14 grid gap-6 md:grid-cols-2">
          {useCases.map((uc) => (
            <motion.div
              key={uc.title}
              variants={fadeUp}
              className="rounded-2xl border border-[#F1F5F9] bg-card p-8 transition-shadow hover:shadow-md"
            >
              <div
                className={`flex h-12 w-12 items-center justify-center rounded-full ${uc.color}`}
              >
                <uc.icon className={`h-6 w-6 ${uc.iconColor}`} />
              </div>
              <h3 className="mt-5 text-xl font-semibold text-foreground">
                {uc.title}
              </h3>
              <p className="mt-2 leading-relaxed text-muted-foreground">
                {uc.description}
              </p>
            </motion.div>
          ))}
        </div>

        {/* Expandable section */}
        <motion.div variants={fadeUp} className="mt-10 text-center">
          <button
            type="button"
            onClick={() => setShowAll(!showAll)}
            className="inline-flex items-center gap-2 rounded-full border border-border bg-card px-6 py-3 text-sm font-semibold text-foreground transition-colors hover:bg-muted"
          >
            {showAll ? "Hide report types" : "See all 8 report types"}
            <ChevronDown
              className={`h-4 w-4 transition-transform ${showAll ? "rotate-180" : ""}`}
            />
          </button>
        </motion.div>

        <AnimatePresence>
          {showAll && (
            <motion.div
              initial={{ opacity: 0, height: 0 }}
              animate={{ opacity: 1, height: "auto" }}
              exit={{ opacity: 0, height: 0 }}
              transition={{ duration: 0.3 }}
              className="overflow-hidden"
            >
              <div className="mt-10 grid grid-cols-2 gap-4 md:grid-cols-4">
                {types.map((t) => (
                  <div
                    key={t.title}
                    className="rounded-xl border border-[#F1F5F9] bg-card p-6 text-center transition-shadow hover:shadow-md"
                  >
                    <div className="mx-auto flex h-12 w-12 items-center justify-center rounded-full bg-[#EEF2FF]">
                      <t.icon className="h-6 w-6 text-[#6366F1]" />
                    </div>
                    <h3 className="mt-4 text-base font-semibold text-foreground">
                      {t.title}
                    </h3>
                    <p className="mt-1 text-sm leading-relaxed text-muted-foreground">
                      {t.desc}
                    </p>
                  </div>
                ))}
              </div>
            </motion.div>
          )}
        </AnimatePresence>
      </motion.div>
    </section>
  );
}

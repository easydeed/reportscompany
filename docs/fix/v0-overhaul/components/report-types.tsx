"use client";

import { motion } from "framer-motion";
import {
  BarChart3,
  Home,
  TrendingUp,
  DollarSign,
  Layers,
  ImageIcon,
  MapPin,
  Star,
} from "lucide-react";

const fadeUp = {
  hidden: { opacity: 0, y: 16 },
  visible: { opacity: 1, y: 0, transition: { duration: 0.4 } },
};

const types = [
  {
    icon: BarChart3,
    title: "Market Snapshot",
    desc: "Key metrics at a glance for any market area.",
  },
  {
    icon: Home,
    title: "New Listings",
    desc: "Fresh listings hitting the market this week.",
  },
  {
    icon: TrendingUp,
    title: "Inventory Report",
    desc: "Supply trends and months of inventory data.",
  },
  {
    icon: DollarSign,
    title: "Closed Sales",
    desc: "Recent closings with price and volume details.",
  },
  {
    icon: Layers,
    title: "Price Bands",
    desc: "Activity breakdown by price range segment.",
  },
  {
    icon: ImageIcon,
    title: "Listings Gallery",
    desc: "Visual grid of active properties with photos.",
  },
  {
    icon: MapPin,
    title: "Open Houses",
    desc: "Upcoming open houses in your target market.",
  },
  {
    icon: Star,
    title: "Featured Listings",
    desc: "Showcase your best listings front and center.",
  },
];

export function ReportTypes() {
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
          8 report types. One click each.
        </motion.h2>
        <motion.p
          variants={fadeUp}
          className="mx-auto mt-4 max-w-xl text-center text-muted-foreground"
        >
          Every angle of the market covered, from snapshots to deep dives.
        </motion.p>

        <div className="mt-14 grid grid-cols-2 gap-4 md:grid-cols-4">
          {types.map((t) => (
            <motion.div
              key={t.title}
              variants={fadeUp}
              className="rounded-xl border border-[#F1F5F9] bg-card p-8 text-center transition-shadow hover:shadow-md"
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
            </motion.div>
          ))}
        </div>
      </motion.div>
    </section>
  );
}

"use client";

import { motion } from "framer-motion";
import { ReportCarousel } from "./report-carousel";

const fadeUp = {
  hidden: { opacity: 0, y: 16 },
  visible: { opacity: 1, y: 0, transition: { duration: 0.4 } },
};

const badges = [
  "Your logo & colors",
  "Mobile-first design",
  "Key market metrics",
  "Your contact info",
];

function StatGrid() {
  return (
    <div className="space-y-5">
      <div className="grid grid-cols-3 gap-3">
        {[
          { label: "Median price", value: "$485K" },
          { label: "Active listings", value: "1,247" },
          { label: "Avg DOM", value: "28" },
        ].map((s) => (
          <div
            key={s.label}
            className="rounded-lg bg-[#F8FAFC] p-3 text-center"
          >
            <p className="text-base font-bold text-foreground">{s.value}</p>
            <p className="text-xs text-muted-foreground">{s.label}</p>
          </div>
        ))}
      </div>
      <div className="space-y-3">
        {[
          { label: "Median price", pct: "75%", color: "bg-[#6366F1]" },
          { label: "Inventory", pct: "50%", color: "bg-[#A5B4FC]" },
          { label: "Days on market", pct: "40%", color: "bg-[#6366F1]" },
        ].map((b) => (
          <div key={b.label} className="flex items-center gap-3">
            <span className="w-24 text-xs text-muted-foreground">
              {b.label}
            </span>
            <div className="h-2 flex-1 rounded-full bg-muted">
              <div
                className={`h-2 rounded-full ${b.color}`}
                style={{ width: b.pct }}
              />
            </div>
          </div>
        ))}
      </div>
      {/* Agent footer */}
      <div className="flex items-center gap-3 border-t border-border pt-4">
        <div className="flex h-8 w-8 items-center justify-center rounded-full bg-[#6366F1] text-[10px] font-bold text-white">
          SJ
        </div>
        <div>
          <p className="text-sm font-semibold text-foreground">
            Sarah Johnson
          </p>
          <p className="text-xs text-muted-foreground">Compass</p>
        </div>
      </div>
    </div>
  );
}

function ListingsGrid() {
  return (
    <div className="space-y-3">
      <div className="grid grid-cols-2 gap-2">
        {[
          { addr: "742 Oak Ave", price: "$525,000" },
          { addr: "118 Pine St", price: "$389,000" },
          { addr: "903 Elm Dr", price: "$612,000" },
          { addr: "221 Maple Ln", price: "$445,000" },
        ].map((p) => (
          <div
            key={p.addr}
            className="overflow-hidden rounded-lg border border-border"
          >
            <div className="h-20 bg-gradient-to-br from-[#E0E7FF] to-[#C7D2FE]" />
            <div className="p-2.5">
              <p className="text-xs font-semibold text-foreground">
                {p.price}
              </p>
              <p className="text-[10px] text-muted-foreground">{p.addr}</p>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}

function FeaturedListings() {
  return (
    <div className="space-y-3">
      {[
        {
          addr: "1205 Lakeview Blvd",
          price: "$875,000",
          beds: 4,
          baths: 3,
          sqft: "3,200",
        },
        {
          addr: "437 Sunset Dr",
          price: "$650,000",
          beds: 3,
          baths: 2,
          sqft: "2,100",
        },
      ].map((p) => (
        <div
          key={p.addr}
          className="overflow-hidden rounded-lg border border-border"
        >
            <div className="h-24 bg-gradient-to-br from-[#E0E7FF] to-[#C7D2FE]" />
          <div className="p-3">
            <p className="text-sm font-bold text-foreground">{p.price}</p>
            <p className="text-xs text-muted-foreground">{p.addr}</p>
            <p className="mt-1 text-xs text-muted-foreground">
              {p.beds} bed &middot; {p.baths} bath &middot; {p.sqft} sqft
            </p>
          </div>
        </div>
      ))}
    </div>
  );
}

function MarketAnalysis() {
  return (
    <div className="space-y-3">
      {/* Chart placeholder */}
      <div className="flex h-36 items-end gap-1.5 rounded-lg bg-[#F8FAFC] p-4">
        {[40, 55, 45, 65, 50, 70, 60, 75, 80, 72, 85, 90].map((h, i) => (
          <div
            key={`bar-${h}-${i}`}
            className="flex-1 rounded-t bg-[#6366F1]/70"
            style={{ height: `${h}%` }}
          />
        ))}
      </div>
      <div className="grid grid-cols-2 gap-2">
        {[
          { label: "YoY price change", value: "+5.2%" },
          { label: "Avg sale-to-list", value: "98.4%" },
          { label: "Months of supply", value: "2.1" },
          { label: "New listings", value: "342" },
        ].map((s) => (
          <div key={s.label} className="rounded-lg bg-[#F8FAFC] p-3">
            <p className="text-sm font-bold text-foreground">{s.value}</p>
            <p className="text-[10px] text-muted-foreground">{s.label}</p>
          </div>
        ))}
      </div>
    </div>
  );
}

const emailCards = [
  {
    title: "Market Snapshot",
    gradient: "bg-gradient-to-r from-[#6366F1] to-[#818CF8]",
    content: <StatGrid />,
  },
  {
    title: "New Listings Gallery",
    gradient: "bg-gradient-to-r from-[#6366F1] to-[#818CF8]",
    content: <ListingsGrid />,
  },
  {
    title: "Featured Listings",
    gradient: "bg-gradient-to-r from-[#4338CA] to-[#6366F1]",
    content: <FeaturedListings />,
  },
  {
    title: "Market Analysis",
    gradient: "bg-gradient-to-r from-[#312E81] to-[#4338CA]",
    content: <MarketAnalysis />,
  },
];

export function EmailReports() {
  return (
    <section id="email-reports" className="bg-background px-6 py-20 md:py-28">
      <motion.div
        className="mx-auto max-w-7xl"
        initial="hidden"
        whileInView="visible"
        viewport={{ once: true }}
        variants={{ visible: { transition: { staggerChildren: 0.1 } } }}
      >
        <motion.div variants={fadeUp} className="text-center">
          <h2 className="text-4xl font-bold tracking-tight text-foreground md:text-5xl">
            Email reports clients actually open
          </h2>
          <p className="mx-auto mt-4 max-w-xl text-muted-foreground">
            Mobile-optimized HTML emails with your brand front and center
          </p>
        </motion.div>

        <div className="mt-14 grid items-center gap-12 md:grid-cols-2">
          {/* Feature badges */}
          <motion.div variants={fadeUp}>
            <h3 className="text-2xl font-bold text-foreground">
              What makes them great
            </h3>
            <div className="mt-4 flex flex-wrap gap-3">
              {badges.map((b) => (
                <span
                  key={b}
                  className="inline-flex items-center rounded-full border border-border bg-card px-4 py-2 text-sm font-medium text-foreground"
                >
                  {b}
                </span>
              ))}
            </div>
            <p className="mt-6 leading-relaxed text-muted-foreground">
              Every report is branded with your logo, colors, and contact
              information. Clients see a professional, mobile-friendly email that
              keeps you top of mind.
            </p>
          </motion.div>

          {/* Carousel */}
          <motion.div variants={fadeUp}>
            <ReportCarousel cards={emailCards} aspect="portrait" />
          </motion.div>
        </div>
      </motion.div>
    </section>
  );
}

"use client";

import { motion } from "framer-motion";
import { ReportCarousel } from "./report-carousel";

const fadeUp = {
  hidden: { opacity: 0, y: 16 },
  visible: { opacity: 1, y: 0, transition: { duration: 0.4 } },
};

const PHOTOS = [
  "https://images.unsplash.com/photo-1564013799919-ab600027ffc6",
  "https://images.unsplash.com/photo-1600596542815-ffad4c1539a9",
  "https://images.unsplash.com/photo-1600585154340-be6161a56a0c",
  "https://images.unsplash.com/photo-1600047509807-ba8f99d2cdde",
  "https://images.unsplash.com/photo-1583608205776-bfd35f0d9f83",
  "https://images.unsplash.com/photo-1512917774080-9991f1c4c750",
];

const badges = [
  "Professional headers",
  "Property photo galleries",
  "Market charts & trends",
  "Your branded footer",
];

function PdfStatPage() {
  return (
    <div className="space-y-4">
      <div className="grid grid-cols-3 gap-3">
        {[
          { label: "Median price", value: "$485K" },
          { label: "Active", value: "1,247" },
          { label: "Avg DOM", value: "28" },
        ].map((s) => (
          <div key={s.label} className="rounded-md bg-[#F8FAFC] p-3 text-center">
            <p className="text-sm font-bold text-foreground">{s.value}</p>
            <p className="text-[10px] text-muted-foreground">{s.label}</p>
          </div>
        ))}
      </div>
      <div className="grid grid-cols-2 gap-3">
        {[0, 1, 2, 3].map((i) => (
          <div key={i} className="overflow-hidden rounded-md border border-border">
            <div className="h-14 overflow-hidden">
              <img src={`${PHOTOS[i]}?w=140&h=56&fit=crop`} alt="" className="w-full h-full object-cover" />
            </div>
            <div className="p-1.5">
              <div className="h-1.5 w-3/4 rounded bg-muted" />
              <div className="mt-1 h-1.5 w-1/2 rounded bg-muted" />
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}

function PdfListingsGallery() {
  const listings = [
    { addr: "742 Oak Ave", price: "$525K" },
    { addr: "118 Pine St", price: "$389K" },
    { addr: "903 Elm Dr", price: "$612K" },
    { addr: "221 Maple Ln", price: "$445K" },
    { addr: "56 River Rd", price: "$510K" },
    { addr: "889 Hill St", price: "$475K" },
  ];
  return (
    <div className="grid grid-cols-3 gap-3">
      {listings.map((p, i) => (
        <div key={p.addr} className="overflow-hidden rounded-md border border-border">
          <div className="h-16 overflow-hidden">
            <img src={`${PHOTOS[i]}?w=100&h=64&fit=crop`} alt="" className="w-full h-full object-cover" />
          </div>
          <div className="p-2">
            <p className="text-[10px] font-semibold text-foreground">{p.price}</p>
            <p className="text-[9px] text-muted-foreground">{p.addr}</p>
          </div>
        </div>
      ))}
    </div>
  );
}

function PdfFeatured() {
  const listings = [
    { addr: "1205 Lakeview Blvd", price: "$875K", info: "4 bd / 3 ba" },
    { addr: "437 Sunset Dr", price: "$650K", info: "3 bd / 2 ba" },
    { addr: "802 Crescent Way", price: "$720K", info: "4 bd / 2 ba" },
    { addr: "156 Hilltop Ln", price: "$540K", info: "3 bd / 2 ba" },
  ];
  return (
    <div className="grid grid-cols-2 gap-3">
      {listings.map((p, i) => (
        <div key={p.addr} className="overflow-hidden rounded-md border border-border">
          <div className="h-20 overflow-hidden">
            <img src={`${PHOTOS[i]}?w=200&h=80&fit=crop`} alt="" className="w-full h-full object-cover" />
          </div>
          <div className="p-2.5">
            <p className="text-xs font-bold text-foreground">{p.price}</p>
            <p className="text-[9px] text-muted-foreground">{p.addr}</p>
            <p className="text-[9px] text-muted-foreground">{p.info}</p>
          </div>
        </div>
      ))}
    </div>
  );
}

function PdfPriceTrends() {
  return (
    <div className="space-y-4">
      {/* Chart area */}
      <div className="rounded-md bg-[#F8FAFC] p-4">
        <svg viewBox="0 0 200 60" className="w-full" aria-label="Price trend chart">
          <polyline
            points="0,50 20,45 40,42 60,38 80,35 100,30 120,28 140,25 160,20 180,18 200,12"
            fill="none"
            stroke="#6366F1"
            strokeWidth="2"
          />
          <polyline
            points="0,52 20,50 40,48 60,47 80,44 100,42 120,40 140,38 160,36 180,34 200,30"
            fill="none"
            stroke="#A5B4FC"
            strokeWidth="2"
            strokeDasharray="4,3"
          />
        </svg>
        <div className="mt-2 flex items-center gap-4">
          <div className="flex items-center gap-1">
            <div className="h-1.5 w-4 rounded-full bg-[#6366F1]" />
            <span className="text-[9px] text-muted-foreground">Median price</span>
          </div>
          <div className="flex items-center gap-1">
            <div className="h-1.5 w-4 rounded-full bg-[#A5B4FC]" />
            <span className="text-[9px] text-muted-foreground">Avg price/sqft</span>
          </div>
        </div>
      </div>
      {/* Comparison table */}
      <div className="rounded-md border border-border text-[10px]">
        <div className="grid grid-cols-3 gap-px bg-muted font-semibold text-foreground">
          <div className="bg-card p-1.5">Metric</div>
          <div className="bg-card p-1.5">This month</div>
          <div className="bg-card p-1.5">Last year</div>
        </div>
        {[
          ["Median price", "$485K", "$461K"],
          ["Avg DOM", "28", "34"],
          ["Sold listings", "189", "204"],
        ].map((row) => (
          <div key={row[0]} className="grid grid-cols-3 gap-px bg-muted text-muted-foreground">
            <div className="bg-card p-1.5">{row[0]}</div>
            <div className="bg-card p-1.5">{row[1]}</div>
            <div className="bg-card p-1.5">{row[2]}</div>
          </div>
        ))}
      </div>
    </div>
  );
}

const pdfCards = [
  {
    title: "Market Snapshot PDF",
    gradient: "bg-gradient-to-r from-[#6366F1] to-[#818CF8]",
    content: <PdfStatPage />,
  },
  {
    title: "Listings Gallery PDF",
    gradient: "bg-gradient-to-r from-[#6366F1] to-[#818CF8]",
    content: <PdfListingsGallery />,
  },
  {
    title: "Featured Listings PDF",
    gradient: "bg-gradient-to-r from-[#4338CA] to-[#6366F1]",
    content: <PdfFeatured />,
  },
  {
    title: "Price Trends PDF",
    gradient: "bg-gradient-to-r from-[#312E81] to-[#4338CA]",
    content: <PdfPriceTrends />,
  },
];

export function PdfReports() {
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
            Print-ready PDFs that look like you hired a designer
          </h2>
          <p className="mx-auto mt-4 max-w-xl text-muted-foreground">
            Hand them out at open houses, attach them to listing presentations,
            or text them to a curious buyer. They look polished every time.
          </p>
        </motion.div>

        <div className="mt-14 grid items-center gap-12 md:grid-cols-2">
          {/* Carousel on left */}
          <motion.div variants={fadeUp} className="order-2 md:order-1">
            <ReportCarousel cards={pdfCards} aspect="landscape" />
          </motion.div>

          {/* Feature badges on right */}
          <motion.div variants={fadeUp} className="order-1 md:order-2">
            <h3 className="text-2xl font-bold text-foreground">
              Built for print and digital
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
              {"Every PDF is 8.5\u00D711, print-ready, and fully branded with your logo, colors, and contact info. Professional headers, property galleries, charts, and your agent footer \u2014 ready for print or screen."}
            </p>
          </motion.div>
        </div>
      </motion.div>
    </section>
  );
}

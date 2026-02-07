"use client"

import { motion } from "framer-motion"
import { ReportCarousel } from "./report-carousel"

const fadeUp = {
  hidden: { opacity: 0, y: 16 },
  visible: { opacity: 1, y: 0, transition: { duration: 0.4 } },
}

const badges = [
  "Professional header",
  "Property galleries",
  "Charts & visualizations",
  "Agent footer",
]

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
        {[1, 2, 3, 4].map((i) => (
          <div key={i} className="overflow-hidden rounded-md border border-border">
            <div className="h-14 bg-gradient-to-br from-[#E0E7FF] to-[#C7D2FE]" />
            <div className="p-1.5">
              <div className="h-1.5 w-3/4 rounded bg-muted" />
              <div className="mt-1 h-1.5 w-1/2 rounded bg-muted" />
            </div>
          </div>
        ))}
      </div>
    </div>
  )
}

function PdfListingsGallery() {
  return (
    <div className="grid grid-cols-3 gap-3">
      {[
        { addr: "742 Oak Ave", price: "$525K" },
        { addr: "118 Pine St", price: "$389K" },
        { addr: "903 Elm Dr", price: "$612K" },
        { addr: "221 Maple Ln", price: "$445K" },
        { addr: "56 River Rd", price: "$510K" },
        { addr: "889 Hill St", price: "$475K" },
      ].map((p) => (
        <div key={p.addr} className="overflow-hidden rounded-md border border-border">
          <div className="h-16 bg-gradient-to-br from-[#E0E7FF] to-[#C7D2FE]" />
          <div className="p-2">
            <p className="text-[10px] font-semibold text-foreground">{p.price}</p>
            <p className="text-[9px] text-muted-foreground">{p.addr}</p>
          </div>
        </div>
      ))}
    </div>
  )
}

function PdfFeatured() {
  return (
    <div className="grid grid-cols-2 gap-3">
      {[
        { addr: "1205 Lakeview Blvd", price: "$875K", info: "4 bd / 3 ba" },
        { addr: "437 Sunset Dr", price: "$650K", info: "3 bd / 2 ba" },
        { addr: "802 Crescent Way", price: "$720K", info: "4 bd / 2 ba" },
        { addr: "156 Hilltop Ln", price: "$540K", info: "3 bd / 2 ba" },
      ].map((p) => (
        <div key={p.addr} className="overflow-hidden rounded-md border border-border">
          <div className="h-20 bg-gradient-to-br from-[#E0E7FF] to-[#C7D2FE]" />
          <div className="p-2.5">
            <p className="text-xs font-bold text-foreground">{p.price}</p>
            <p className="text-[9px] text-muted-foreground">{p.addr}</p>
            <p className="text-[9px] text-muted-foreground">{p.info}</p>
          </div>
        </div>
      ))}
    </div>
  )
}

function PdfPriceTrends() {
  return (
    <div className="space-y-4">
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
  )
}

const pdfCards = [
  { title: "Market Snapshot PDF", gradient: "bg-gradient-to-r from-[#6366F1] to-[#818CF8]", content: <PdfStatPage /> },
  { title: "Listings Gallery PDF", gradient: "bg-gradient-to-r from-[#6366F1] to-[#818CF8]", content: <PdfListingsGallery /> },
  { title: "Featured Listings PDF", gradient: "bg-gradient-to-r from-[#4338CA] to-[#6366F1]", content: <PdfFeatured /> },
  { title: "Price Trends PDF", gradient: "bg-gradient-to-r from-[#312E81] to-[#4338CA]", content: <PdfPriceTrends /> },
]

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
            Print-ready PDFs that look expensive
          </h2>
          <p className="mx-auto mt-4 max-w-xl text-muted-foreground">
            {"8.5\u00D711 formatted for perfect printing and digital sharing"}
          </p>
        </motion.div>

        <div className="mt-14 grid items-center gap-12 md:grid-cols-2">
          {/* Carousel on left */}
          <motion.div variants={fadeUp} className="order-2 md:order-1">
            <ReportCarousel cards={pdfCards} aspect="landscape" />
          </motion.div>

          {/* Feature badges on right */}
          <motion.div variants={fadeUp} className="order-1 md:order-2">
            <h3 className="text-2xl font-bold text-foreground">Built for print and digital</h3>
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
              Every PDF is print-ready at 8.5 x 11 inches with professional
              headers, property galleries, charts, and your agent branding in
              the footer.
            </p>
          </motion.div>
        </div>
      </motion.div>
    </section>
  )
}

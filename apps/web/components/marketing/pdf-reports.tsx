"use client"

import { motion } from "framer-motion"
import { Check } from "lucide-react"
import {
  Carousel,
  CarouselContent,
  CarouselItem,
  CarouselNext,
  CarouselPrevious,
} from "@/components/ui/carousel"

const features = [
  { title: "Professional headers", desc: "Gradient design with your branding" },
  { title: "Charts & visualizations", desc: "Price trends, market stats" },
  { title: "Property galleries", desc: "Clean grid layouts with listing details" },
  { title: "Agent footer", desc: "Photo, credentials, and contact info" },
]

export function PdfReports() {
  return (
    <section
      id="pdf-reports"
      className="py-20 sm:py-24 px-4 sm:px-6 lg:px-8 bg-slate-50"
    >
      <div className="max-w-6xl mx-auto">
        <motion.div
          initial={{ opacity: 0, y: 16 }}
          whileInView={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.4, ease: "easeOut" }}
          viewport={{ once: true, margin: "-50px" }}
          className="text-center mb-14"
        >
          <h2 className="font-display font-bold text-3xl sm:text-4xl text-slate-900 tracking-[-0.02em] mb-3">
            Print-ready PDFs that look expensive
          </h2>
          <p className="text-lg text-slate-500">
            8.5×11 formatted for perfect printing and digital sharing
          </p>
        </motion.div>

        <motion.div
          initial={{ opacity: 0, y: 16 }}
          whileInView={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.5, ease: "easeOut" }}
          viewport={{ once: true, margin: "-50px" }}
          className="max-w-2xl mx-auto"
        >
          <div className="bg-white rounded-2xl shadow-xl border border-slate-200/60 p-6 sm:p-8">
            <div className="bg-slate-100 rounded-lg p-6">
              <Carousel className="w-full">
                <CarouselContent>
                  <CarouselItem>
                    <img
                      src="/market-snapshot-report-purple-gradient-header-with.jpg"
                      alt="Market Snapshot PDF report"
                      className="w-full rounded shadow-lg"
                    />
                  </CarouselItem>
                  <CarouselItem>
                    <img
                      src="/new-listings-gallery-report-purple-header-with-pro.jpg"
                      alt="New Listings Gallery PDF report"
                      className="w-full rounded shadow-lg"
                    />
                  </CarouselItem>
                  <CarouselItem>
                    <img
                      src="/featured-listings-report-purple-header-with-2x2-pr.jpg"
                      alt="Featured Listings PDF report"
                      className="w-full rounded shadow-lg"
                    />
                  </CarouselItem>
                  <CarouselItem>
                    <img
                      src="/price-trends-report-purple-header-with-historica.jpg"
                      alt="Price Trends PDF report"
                      className="w-full rounded shadow-lg"
                    />
                  </CarouselItem>
                </CarouselContent>
                <CarouselPrevious className="left-2" />
                <CarouselNext className="right-2" />
              </Carousel>
            </div>
          </div>
        </motion.div>

        {/* Feature pills below */}
        <motion.div
          initial={{ opacity: 0, y: 16 }}
          whileInView={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.4, delay: 0.1, ease: "easeOut" }}
          viewport={{ once: true, margin: "-50px" }}
          className="mt-10 grid sm:grid-cols-2 lg:grid-cols-4 gap-4 max-w-3xl mx-auto"
        >
          {features.map((f) => (
            <div key={f.title} className="flex items-start gap-2.5">
              <Check className="w-4 h-4 text-indigo-500 flex-shrink-0 mt-0.5" />
              <div>
                <div className="text-sm font-medium text-slate-800">{f.title}</div>
                <div className="text-xs text-slate-500">{f.desc}</div>
              </div>
            </div>
          ))}
        </motion.div>
      </div>
    </section>
  )
}

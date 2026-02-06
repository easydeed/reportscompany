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
  { title: "Your logo & colors", desc: "Full white-label branding" },
  { title: "Mobile-first design", desc: "Perfect on every device" },
  { title: "Key market metrics", desc: "Median price, inventory, DOM" },
  { title: "Your contact info", desc: "Photo, phone, social links" },
]

export function EmailReports() {
  return (
    <section
      id="email-reports"
      className="py-20 sm:py-24 px-4 sm:px-6 lg:px-8 bg-white overflow-hidden"
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
            Email reports clients actually open
          </h2>
          <p className="text-lg text-slate-500">
            Mobile-optimized HTML emails with your brand front and center
          </p>
        </motion.div>

        <motion.div
          initial={{ opacity: 0, y: 16 }}
          whileInView={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.5, ease: "easeOut" }}
          viewport={{ once: true, margin: "-50px" }}
          className="max-w-2xl mx-auto"
        >
          {/* Email mockup */}
          <div className="bg-white rounded-2xl shadow-xl border border-slate-200/60 overflow-hidden">
            {/* Browser chrome */}
            <div className="bg-slate-100 px-4 py-3 border-b border-slate-200 flex items-center gap-3">
              <div className="flex gap-1.5">
                <div className="w-3 h-3 rounded-full bg-slate-300" />
                <div className="w-3 h-3 rounded-full bg-slate-300" />
                <div className="w-3 h-3 rounded-full bg-slate-300" />
              </div>
              <div className="text-xs text-slate-500">Market Report</div>
            </div>

            <div className="p-6 sm:p-8 bg-gradient-to-br from-slate-50 to-white">
              <Carousel className="w-full">
                <CarouselContent>
                  <CarouselItem>
                    <img
                      src="/real-estate-market-snapshot-report-with-purple-gra.jpg"
                      alt="Market Snapshot email report"
                      className="w-full rounded-lg shadow-md"
                    />
                  </CarouselItem>
                  <CarouselItem>
                    <img
                      src="/real-estate-new-listings-gallery-with-property-pho.jpg"
                      alt="New Listings email report"
                      className="w-full rounded-lg shadow-md"
                    />
                  </CarouselItem>
                  <CarouselItem>
                    <img
                      src="/real-estate-featured-listings-report-with-blue-gra.jpg"
                      alt="Featured Listings email report"
                      className="w-full rounded-lg shadow-md"
                    />
                  </CarouselItem>
                  <CarouselItem>
                    <img
                      src="/real-estate-market-analysis-report-with-orange-gra.jpg"
                      alt="Market Analysis email report"
                      className="w-full rounded-lg shadow-md"
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

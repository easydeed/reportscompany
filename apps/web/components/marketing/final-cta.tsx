"use client"

import Link from "next/link"
import { motion } from "framer-motion"
import { Button } from "@/components/ui/button"
import { ArrowRight } from "lucide-react"

export function FinalCta() {
  const scrollToSamples = (e: React.MouseEvent) => {
    e.preventDefault()
    const el = document.getElementById("email-reports")
    if (el) {
      const offset = el.getBoundingClientRect().top + window.pageYOffset - 72
      window.scrollTo({ top: offset, behavior: "smooth" })
    }
  }

  return (
    <section className="py-20 sm:py-24 px-4 sm:px-6 lg:px-8 bg-indigo-50/60">
      <motion.div
        initial={{ opacity: 0, y: 16 }}
        whileInView={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.5, ease: "easeOut" }}
        viewport={{ once: true, margin: "-50px" }}
        className="max-w-2xl mx-auto text-center"
      >
        <h2 className="font-display font-bold text-3xl sm:text-4xl text-slate-900 tracking-[-0.02em] mb-4">
          Ready to try it?
        </h2>
        <p className="text-lg text-slate-500 mb-8">
          Setup takes 2 minutes. Your first report is free.
        </p>

        <div className="flex flex-col sm:flex-row items-center justify-center gap-4">
          <Button
            className="rounded-full bg-indigo-500 hover:bg-indigo-600 text-white px-8 py-3 h-auto text-base shadow-sm hover:shadow-md transition-all"
            asChild
          >
            <Link href="/register">
              Start free trial
              <ArrowRight className="w-4 h-4 ml-2" />
            </Link>
          </Button>
          <button
            onClick={scrollToSamples}
            className="text-sm font-medium text-indigo-600 hover:text-indigo-700 transition-colors cursor-pointer py-3"
          >
            See sample reports →
          </button>
        </div>
      </motion.div>
    </section>
  )
}

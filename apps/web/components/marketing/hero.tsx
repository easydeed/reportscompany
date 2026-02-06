"use client"

import Link from "next/link"
import Image from "next/image"
import { Button } from "@/components/ui/button"
import { motion } from "framer-motion"
import { ArrowRight } from "lucide-react"

export function Hero() {
  const scrollToSamples = (e: React.MouseEvent) => {
    e.preventDefault()
    const el = document.getElementById("email-reports")
    if (el) {
      const offset = el.getBoundingClientRect().top + window.pageYOffset - 72
      window.scrollTo({ top: offset, behavior: "smooth" })
    }
  }

  return (
    <section className="relative pt-32 pb-20 sm:pt-40 sm:pb-28 px-4 sm:px-6 lg:px-8 bg-white">
      <div className="max-w-6xl mx-auto">
        <div className="grid lg:grid-cols-2 gap-12 lg:gap-16 items-center">
          {/* Left: copy */}
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.5, ease: "easeOut" }}
          >
            <h1 className="font-display font-bold text-[clamp(2.25rem,5vw,3.5rem)] leading-[1.1] tracking-[-0.02em] text-slate-900 mb-5">
              Market reports your clients actually want to read
            </h1>

            <p className="text-lg sm:text-xl text-slate-500 leading-relaxed mb-8 max-w-lg">
              Create beautiful, branded market reports from live MLS data.
              Schedule them once — they deliver themselves.
            </p>

            <div className="flex flex-col sm:flex-row items-start gap-4 mb-6">
              <Button
                className="rounded-full bg-indigo-500 hover:bg-indigo-600 text-white px-8 py-3 h-auto text-base shadow-sm hover:shadow-md transition-all"
                asChild
              >
                <Link href="/register">
                  Try it free
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

            <p className="text-sm text-slate-400">
              Free for 14 days · No credit card · Takes 2 minutes
            </p>
          </motion.div>

          {/* Right: product visual */}
          <motion.div
            initial={{ opacity: 0, scale: 0.96 }}
            animate={{ opacity: 1, scale: 1 }}
            transition={{ duration: 0.6, delay: 0.15, ease: "easeOut" }}
            className="relative"
          >
            <div className="relative">
              {/* Subtle glow behind the image */}
              <div className="absolute -inset-4 bg-indigo-100/50 rounded-3xl blur-2xl" />
              <Image
                src="/images/hero-dashboard.png"
                alt="TrendyReports — branded market report preview"
                width={1200}
                height={800}
                priority
                className="relative w-full h-auto rounded-2xl shadow-xl border border-slate-200/60"
              />
            </div>
          </motion.div>
        </div>
      </div>
    </section>
  )
}

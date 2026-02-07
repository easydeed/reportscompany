"use client"

import { motion } from "framer-motion"

const fadeUp = {
  hidden: { opacity: 0, y: 16 },
  visible: { opacity: 1, y: 0, transition: { duration: 0.4 } },
}

export function FinalCta() {
  return (
    <section className="bg-[#EEF2FF] px-6 py-20 md:py-28">
      <motion.div
        className="mx-auto max-w-2xl text-center"
        initial="hidden"
        whileInView="visible"
        viewport={{ once: true }}
        variants={{ visible: { transition: { staggerChildren: 0.1 } } }}
      >
        <motion.h2
          variants={fadeUp}
          className="text-4xl font-bold tracking-tight text-foreground md:text-5xl"
        >
          Ready to try it?
        </motion.h2>
        <motion.p variants={fadeUp} className="mt-4 text-muted-foreground">
          Set up takes 2 minutes. Your first report is free.
        </motion.p>
        <motion.div variants={fadeUp} className="mt-8">
          <a
            href="/register"
            className="inline-flex items-center rounded-full bg-[#6366F1] px-8 py-3.5 text-base font-semibold text-white shadow-lg shadow-[#6366F1]/25 transition-colors hover:bg-[#4F46E5]"
          >
            Start free trial
          </a>
        </motion.div>
        <motion.p
          variants={fadeUp}
          className="mt-5 text-sm text-muted-foreground/70"
        >
          {"Free for 14 days \u00B7 No credit card \u00B7 Cancel anytime"}
        </motion.p>
      </motion.div>
    </section>
  )
}

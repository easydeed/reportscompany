"use client";

import { motion } from "framer-motion";

const fadeUp = {
  hidden: { opacity: 0, y: 16 },
  visible: { opacity: 1, y: 0, transition: { duration: 0.4 } },
};

export function WhoItsFor() {
  return (
    <section className="bg-[#F8FAFC] px-6 py-20 md:py-28">
      <motion.div
        className="mx-auto max-w-5xl"
        initial="hidden"
        whileInView="visible"
        viewport={{ once: true }}
        variants={{ visible: { transition: { staggerChildren: 0.1 } } }}
      >
        <motion.h2
          variants={fadeUp}
          className="text-center text-4xl font-bold tracking-tight text-foreground md:text-5xl"
        >
          Built for how you actually work
        </motion.h2>

        <div className="mt-14 grid gap-8 md:grid-cols-2">
          {/* Agents card */}
          <motion.div
            variants={fadeUp}
            className="rounded-2xl bg-[#EEF2FF] p-8 md:p-10"
          >
            <h3 className="text-2xl font-bold text-foreground">
              For Real Estate Agents
            </h3>
            <p className="mt-4 leading-relaxed text-muted-foreground">
              Stop spending hours on market updates — or paying a marketing
              company to do it. TrendyReports gives you polished, branded
              reports from live MLS data, delivered to your sphere
              automatically. You focus on selling. We handle the marketing.
            </p>
            <a
              href="/register"
              className="mt-6 inline-flex items-center rounded-full bg-[#6366F1] px-6 py-2.5 text-sm font-semibold text-white transition-colors hover:bg-[#4F46E5]"
            >
              Start free trial
            </a>
          </motion.div>

          {/* Title & Lending card */}
          <motion.div
            variants={fadeUp}
            className="rounded-2xl bg-[#F1F5F9] p-8 md:p-10"
          >
            <h3 className="text-2xl font-bold text-foreground">
              {"For Title Companies & Lenders"}
            </h3>
            <p className="mt-4 leading-relaxed text-muted-foreground">
              Give your agents something they actually want. Sponsor
              TrendyReports for your agent partners — they get branded market
              reports on autopilot with your logo alongside theirs. Strengthen
              relationships, drive repeat business, and finally have a reason
              to call that isn't "just checking in."
            </p>
            <a
              href="mailto:sales@trendyreports.com"
              className="mt-6 inline-flex items-center rounded-full border border-foreground/20 bg-transparent px-6 py-2.5 text-sm font-semibold text-foreground transition-colors hover:bg-foreground/5"
            >
              Learn more
            </a>
          </motion.div>
        </div>
      </motion.div>
    </section>
  );
}

"use client";

import { motion } from "framer-motion";
import {
  Accordion,
  AccordionContent,
  AccordionItem,
  AccordionTrigger,
} from "@/components/ui/accordion";

const fadeUp = {
  hidden: { opacity: 0, y: 16 },
  visible: { opacity: 1, y: 0, transition: { duration: 0.4 } },
};

const faqs = [
  {
    question: "What MLS data do you use?",
    answer:
      "We pull from CRMLS, which covers all six Southern California counties including Los Angeles, Orange, Riverside, San Bernardino, San Diego, and Ventura.",
  },
  {
    question: "How do my clients receive the reports?",
    answer:
      "By email. You choose the schedule (weekly, monthly, or one-time) and we deliver branded HTML emails directly to your contact list.",
  },
  {
    question: "Can I customize what data shows up?",
    answer:
      "Yes. You choose your market area, report type, and branding. The data is pulled automatically from the MLS.",
  },
  {
    question: "Do my clients know this comes from TrendyReports?",
    answer:
      "On the Pro plan and above, reports are fully white-labeled. Your clients see your brand only.",
  },
  {
    question: "What happens after the free trial?",
    answer:
      "You can stay on the free Starter plan (50 reports/month) or upgrade to Pro or Team. No pressure, no surprise charges.",
  },
  {
    question: "Can I use this for listing presentations?",
    answer:
      "Absolutely. Our property reports with comparable sales analysis are designed exactly for this. Print them or share digitally.",
  },
];

export function FAQ() {
  return (
    <section id="faq" className="bg-background px-6 py-20 md:py-28">
      <motion.div
        className="mx-auto max-w-3xl"
        initial="hidden"
        whileInView="visible"
        viewport={{ once: true }}
        variants={{ visible: { transition: { staggerChildren: 0.1 } } }}
      >
        <motion.h2
          variants={fadeUp}
          className="text-center text-4xl font-bold tracking-tight text-foreground md:text-5xl"
        >
          Frequently asked questions
        </motion.h2>
        <motion.p
          variants={fadeUp}
          className="mx-auto mt-4 max-w-xl text-center text-muted-foreground"
        >
          Everything you need to know about TrendyReports
        </motion.p>

        <motion.div variants={fadeUp} className="mt-12">
          <Accordion type="single" collapsible className="w-full">
            {faqs.map((faq, index) => (
              <AccordionItem
                key={faq.question}
                value={`item-${index}`}
                className="border-b border-border"
              >
                <AccordionTrigger className="py-5 text-left text-base font-semibold text-foreground hover:no-underline">
                  {faq.question}
                </AccordionTrigger>
                <AccordionContent className="pb-5 text-muted-foreground">
                  {faq.answer}
                </AccordionContent>
              </AccordionItem>
            ))}
          </Accordion>
        </motion.div>
      </motion.div>
    </section>
  );
}

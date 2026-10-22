"use client";

/**
 * "Seven reports" — Design's `Landing v4` carousel.
 *
 * THE LIST COMES FROM THE WIZARD, not from the deck. The deck's seventh card is
 * Open Houses, which the product has disabled since 3164cbb4 because
 * SimplyRETS open-house data is not reliably updated — so adopting its list
 * literally would advertise a report the wizard refuses to build. Reading
 * `REPORT_TYPES` and dropping anything `disabled` means this page cannot offer
 * what the product does not, and the heading's number is counted rather than
 * written.
 *
 * Design's one-line notes are kept for the six kinds it named. New Listings
 * Analytics is not in the deck; its note is a shortening of the wizard's own
 * description.
 */
import { useEffect, useRef, useState, type CSSProperties } from "react";
import { ArrowLeft, ArrowRight } from "lucide-react";
import { REPORT_TYPES } from "@/components/unified-wizard/types";
import type { PreviewReportType } from "@/components/shared/email-preview/sample-data";
import { ReportSheet } from "./landing-primitives";

const ORDER: { id: PreviewReportType; note: string }[] = [
  { id: "market_snapshot", note: "One number leads, then the read" },
  { id: "new_listings_gallery", note: "What just hit the market" },
  { id: "closed", note: "Who sold, for how much" },
  { id: "inventory", note: "Everything for sale right now" },
  { id: "price_bands", note: "Which price range is moving" },
  { id: "featured_listings", note: "Four homes you want to show off" },
  { id: "new_listings", note: "How new supply is pricing" },
];

const WORDS = ["No", "One", "Two", "Three", "Four", "Five", "Six", "Seven", "Eight", "Nine"];

const CARD_W = 340;
const GAP = 28;

export function ReportKinds() {
  const offered = ORDER.flatMap(({ id, note }) => {
    const t = REPORT_TYPES.find((r) => r.id === id);
    return t && !t.disabled ? [{ id, note, name: t.title }] : [];
  });
  const n = offered.length;
  const [active, setActive] = useState(0);
  const frame = useRef<HTMLDivElement>(null);
  const [frameW, setFrameW] = useState(1200);

  useEffect(() => {
    const el = frame.current;
    if (!el) return;
    const measure = () => setFrameW(el.clientWidth);
    measure();
    const ro = new ResizeObserver(measure);
    ro.observe(el);
    return () => ro.disconnect();
  }, []);

  const trackX = Math.round(frameW / 2 - CARD_W / 2 - active * (CARD_W + GAP));
  const current = offered[active];

  return (
    <section id="reports" className="flex flex-col gap-8 pb-24 pt-14">
      <div className="mx-auto flex w-full max-w-[1200px] flex-wrap items-end justify-between gap-6 px-4 md:px-8">
        <div className="flex flex-col gap-2">
          <h2
            className="m-0 font-extrabold text-[#0F172A]"
            style={{
              fontSize: "clamp(30px, 3.4vw, 42px)",
              lineHeight: 1.1,
              letterSpacing: "-0.03em",
            } as CSSProperties}
          >
            {WORDS[n] ?? n} reports. Pick what your sphere hears about.
          </h2>
          <span className="text-[17px] text-[#64748B]">
            {current?.name} · {current?.note}
          </span>
        </div>
        <div className="flex gap-2">
          <button
            type="button"
            aria-label="Previous report"
            onClick={() => setActive((active - 1 + n) % n)}
            className="flex h-11 w-11 items-center justify-center rounded-full border border-[#D6D3CB] bg-white"
          >
            <ArrowLeft className="h-[18px] w-[18px] text-[#0F172A]" />
          </button>
          <button
            type="button"
            aria-label="Next report"
            onClick={() => setActive((active + 1) % n)}
            className="flex h-11 w-11 items-center justify-center rounded-full border border-[#D6D3CB] bg-white"
          >
            <ArrowRight className="h-[18px] w-[18px] text-[#0F172A]" />
          </button>
        </div>
      </div>

      <div ref={frame} className="overflow-hidden">
        <div
          className="flex pb-6 pt-3"
          style={{
            gap: GAP,
            transform: `translateX(${trackX}px)`,
            transition: "transform 0.5s cubic-bezier(0.2,0.8,0.2,1)",
            willChange: "transform",
          }}
        >
          {offered.map((k, i) => (
            <button
              key={k.id}
              type="button"
              onClick={() => setActive(i)}
              aria-label={`${k.name} report preview`}
              aria-current={i === active}
              className="flex shrink-0 cursor-pointer flex-col gap-3.5 border-0 bg-transparent p-0 text-left"
              style={{
                width: CARD_W,
                opacity: i === active ? 1 : 0.45,
                transform: `scale(${i === active ? 1 : 0.94})`,
                transition: "opacity 0.4s, transform 0.5s cubic-bezier(0.2,0.8,0.2,1)",
              }}
            >
              <ReportSheet kind={k.id} width={CARD_W} />
              <div className="flex items-baseline justify-between px-1">
                <span className="text-base font-bold text-[#0F172A]">{k.name}</span>
                <span className="text-[13px] tabular-nums text-[#94A3B8]">
                  {i + 1} / {n}
                </span>
              </div>
            </button>
          ))}
        </div>
      </div>
    </section>
  );
}

"use client";

/**
 * Hero — Design's `Landing v4`, header block.
 *
 * Two lines are deliberately not carried over from the deck:
 *
 * - "350+ Southern California cities" in the reassurance line. An unsourced
 *   figure, and the same family G2 answered by deleting every headcount on
 *   /login, /register and /about. Restore it with a source.
 * - "Next: create a free account. Your {city} report will be waiting." The
 *   city typed here is not carried into signup, so the report would not be
 *   waiting. The box personalises the previews on this page, which is what it
 *   does in the deck too.
 */
import type { CSSProperties } from "react";
import { MapPin } from "lucide-react";
import {
  Glow,
  LANDING_THEMES,
  ReportSheet,
  useLandingTheme,
} from "./landing-primitives";

export function Hero({
  onCity,
  theme,
  onTheme,
}: {
  onCity: (city: string) => void;
  theme: number;
  onTheme: (i: number) => void;
}) {
  const { city } = useLandingTheme();
  const trimmed = city.trim();
  const ctaLabel = trimmed ? `Get my ${trimmed} report` : "Get my free report";

  return (
    <header
      className="mx-auto grid w-full max-w-[1200px] items-center gap-12 px-4 pb-10 pt-12 md:px-8 md:pt-[72px]"
      style={{ gridTemplateColumns: "repeat(auto-fit, minmax(min(100%, 440px), 1fr))" }}
    >
      <div className="flex flex-col gap-8">
        <h1
          className="m-0 font-extrabold text-[#0F172A]"
          style={{
            fontSize: "clamp(42px, 5.4vw, 68px)",
            lineHeight: 1,
            letterSpacing: "-0.035em",
            textWrap: "balance",
          } as CSSProperties}
        >
          Market reports your clients actually open.
        </h1>
        <p
          className="m-0 max-w-[480px] text-xl leading-normal text-[#475569]"
          style={{ textWrap: "pretty" } as CSSProperties}
        >
          Live MLS data. Your brand. Sent to your sphere every month, on autopilot.
        </p>

        <div className="flex flex-col gap-3">
          <div className="flex flex-wrap gap-2">
            <label className="relative min-w-[220px] flex-1">
              <span className="sr-only">Your city</span>
              <MapPin className="pointer-events-none absolute left-4 top-1/2 h-[18px] w-[18px] -translate-y-1/2 text-[#94A3B8]" />
              <input
                value={city}
                onChange={(e) => onCity(e.target.value)}
                placeholder="Your city, e.g. Irvine"
                autoComplete="address-level2"
                className="h-[54px] w-full rounded-[10px] border-[1.5px] border-[#D6D3CB] bg-white pl-11 pr-4 text-[17px] text-[#0F172A] outline-none focus:border-[#4F46E5]"
              />
            </label>
            <a
              href="/register"
              className="inline-flex h-[54px] items-center justify-center whitespace-nowrap rounded-[10px] bg-[#4F46E5] px-6 text-[17px] font-semibold text-white transition-colors hover:bg-[#4338CA]"
            >
              {ctaLabel}
            </a>
          </div>
          <span className="text-sm text-[#64748B]">Free plan · No credit card</span>
        </div>

        <div className="flex items-center gap-3">
          <span className="text-[13px] text-[#64748B]">Your colors</span>
          {LANDING_THEMES.map(([p, a], i) => (
            <button
              key={p}
              type="button"
              aria-label={`Color theme ${i + 1}`}
              aria-pressed={i === theme}
              onClick={() => onTheme(i)}
              className="h-7 w-7 cursor-pointer rounded-full border-0"
              style={{
                background: `linear-gradient(135deg, ${p} 50%, ${a} 50%)`,
                boxShadow:
                  i === theme
                    ? `0 0 0 2px #FAFAF7, 0 0 0 4px ${p}`
                    : "inset 0 0 0 1px rgba(0,0,0,0.1)",
              }}
            />
          ))}
        </div>
      </div>

      {/* Two report pages, fanned. One on a phone, both from md up. */}
      <div className="relative h-[460px] min-w-0 md:h-[620px]">
        <Glow />
        <ReportSheet
          kind="closed"
          width={408}
          className="absolute left-[8%] top-[60px] hidden md:block"
          style={{ transform: "rotate(-5deg)" }}
        />
        <ReportSheet
          kind="market_snapshot"
          width={340}
          className="absolute left-1/2 top-0 md:hidden"
          style={{
            transform: "translateX(-50%) rotate(3deg)",
            boxShadow: "0 40px 80px -24px rgba(15,23,42,0.4), 0 0 0 1px rgba(15,23,42,0.06)",
          }}
        />
        <ReportSheet
          kind="market_snapshot"
          width={408}
          className="absolute right-0 top-0 hidden md:block"
          style={{
            transform: "rotate(3deg)",
            boxShadow: "0 40px 80px -24px rgba(15,23,42,0.4), 0 0 0 1px rgba(15,23,42,0.06)",
          }}
        />
      </div>
    </header>
  );
}

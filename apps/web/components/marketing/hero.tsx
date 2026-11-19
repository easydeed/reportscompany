"use client";

/**
 * Hero — Design's `Landing v13`, header block.
 *
 * New in v13: the "who this is for" line above the headline, a subhead that
 * says what the product does in one sentence, and the three-step strip under
 * the fold of the hero. The two report pages drift apart slightly on scroll.
 *
 * Two lines are still deliberately not carried over from the deck (both were
 * removed on main, and v13 does not change the reasons):
 *
 * - "350+ Southern California cities" in the reassurance line. An unsourced
 *   figure. Restore it with a source.
 * - "Next: create a free account. Your {city} report will be waiting." The
 *   city typed here is not carried into signup, so the report would not be
 *   waiting. The box personalises the previews on this page.
 *
 * Everything here is `relative` so it paints above `DotGrid`, which
 * `MarketingHome` puts behind the header and this block.
 */
import type { CSSProperties } from "react";
import { MapPin } from "lucide-react";
import {
  Drift,
  Glow,
  LANDING_THEMES,
  ReportSheet,
  Steps,
  useLandingTheme,
  type Step,
} from "./landing-primitives";

const STEPS: readonly Step[] = [
  ["Pick your city", "We pull the live MLS data for it."],
  ["Add your logo and colors", "Every report goes out under your brand."],
  ["Choose monthly or weekly", "We email it to your contacts on schedule."],
];

const FRONT_SHADOW = "0 40px 80px -24px rgba(15,23,42,0.4), 0 0 0 1px rgba(15,23,42,0.06)";

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
    <>
      <header
        className="relative mx-auto grid w-full max-w-[1200px] items-center gap-12 px-4 pb-10 pt-12 md:px-8 md:pt-[72px]"
        style={{ gridTemplateColumns: "repeat(auto-fit, minmax(min(100%, 440px), 1fr))" }}
      >
        <div className="flex flex-col gap-8">
          <span className="-mb-3.5 text-[13px] font-semibold uppercase tracking-[0.12em] text-[#4F46E5]">
            For Southern California real estate agents
          </span>
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
            TrendyReports turns live MLS data into market reports with your logo and colors, then
            emails them to your client list every month. Set it up once.
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
                      ? `0 0 0 2px #F5F6FB, 0 0 0 4px ${p}`
                      : "inset 0 0 0 1px rgba(0,0,0,0.1)",
                }}
              />
            ))}
          </div>
        </div>

        {/* Two report pages, fanned. One on a phone, both from md up. */}
        <div className="relative h-[460px] min-w-0 md:h-[620px]">
          <Glow />
          <Drift rate={0.06} className="absolute left-[8%] top-[60px] hidden md:block">
            <ReportSheet kind="closed" width={408} style={{ transform: "rotate(-5deg)" }} />
          </Drift>
          <ReportSheet
            kind="market_snapshot"
            width={340}
            className="absolute left-1/2 top-0 md:hidden"
            style={{ transform: "translateX(-50%) rotate(3deg)", boxShadow: FRONT_SHADOW }}
          />
          <Drift rate={-0.1} className="absolute right-0 top-0 hidden md:block">
            <ReportSheet
              kind="market_snapshot"
              width={408}
              style={{ transform: "rotate(3deg)", boxShadow: FRONT_SHADOW }}
            />
          </Drift>
        </div>
      </header>

      <div className="relative mx-auto w-full max-w-[1200px] px-4 pb-14 pt-4 md:px-8">
        <Steps row items={STEPS} />
      </div>
    </>
  );
}

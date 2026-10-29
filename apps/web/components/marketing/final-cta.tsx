"use client";

/**
 * Closing band — Design's `Landing v4`, the ink-to-brand gradient.
 *
 * The deck's reassurance line was "Free for 1 area, monthly." Nothing limits
 * the Free plan to monthly delivery (see pricing.tsx), so the first clause
 * goes and the second, which is true, stays.
 */
import type { CSSProperties } from "react";
import { useLandingTheme } from "./landing-primitives";

export function FinalCta({ onCity }: { onCity: (city: string) => void }) {
  const { primary, city } = useLandingTheme();
  const trimmed = city.trim();

  return (
    <section
      className="text-white"
      style={{
        background: `linear-gradient(135deg, #0F172A 0%, color-mix(in oklch, #0F172A 55%, ${primary}) 100%)`,
      }}
    >
      <div
        className="mx-auto grid max-w-[1200px] items-center gap-10 px-4 py-20 md:px-8"
        style={{ gridTemplateColumns: "repeat(auto-fit, minmax(min(100%, 420px), 1fr))" }}
      >
        <h2
          className="m-0 font-extrabold"
          style={{
            fontSize: "clamp(32px, 3.8vw, 48px)",
            lineHeight: 1.05,
            letterSpacing: "-0.03em",
            textWrap: "balance",
          } as CSSProperties}
        >
          Your first report is two minutes away.
        </h2>
        <div className="flex flex-col gap-3">
          <div className="flex flex-wrap gap-2">
            <label className="min-w-[200px] flex-1">
              <span className="sr-only">Your city</span>
              <input
                value={city}
                onChange={(e) => onCity(e.target.value)}
                placeholder="Your city"
                autoComplete="address-level2"
                className="h-[54px] w-full rounded-[10px] border border-[#334155] bg-[#1E293B] px-4 text-[17px] text-white outline-none placeholder:text-[#94A3B8]"
              />
            </label>
            <a
              href="/register"
              className="inline-flex h-[54px] items-center justify-center whitespace-nowrap rounded-[10px] bg-white px-6 text-[17px] font-semibold text-[#0F172A] transition-colors hover:bg-[#E0E7FF]"
            >
              {trimmed ? `Get my ${trimmed} report` : "Get my free report"}
            </a>
          </div>
          <span className="text-sm text-[#94A3B8]">
            No credit card. Upgrade only when you want more.
          </span>
        </div>
      </div>
    </section>
  );
}

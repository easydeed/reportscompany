"use client";

/**
 * "Property reports & CMAs" — Design's `Landing v4`, the seller-report card.
 *
 * The house and its comparables are `DEMO_LISTING` and `DEMO_COMPS`; the
 * range and median are `DEMO_COMPS_RANGE`, computed from those comps. The
 * report estimates nothing (LR-025, D-383): it shows the range of the
 * comparable sales it lists, over the last 6 months, and so does this card.
 */
import {
  DEMO_AGENT,
  DEMO_COMPS,
  DEMO_COMPS_RANGE,
  DEMO_LISTING,
  reportDate,
} from "@/lib/demo-data";
import { Glow, SectionCopy, SplitSection, useLandingTheme } from "./landing-primitives";

export function PropertyReports() {
  const { primary, accent, area } = useLandingTheme();

  return (
    <SplitSection id="property-reports">
      <div className="relative h-[700px] min-w-0 md:h-[760px]">
        <Glow />
        <div
          className="absolute left-1/2 top-5 flex h-[660px] w-[340px] flex-col overflow-hidden rounded-md bg-white sm:w-[420px] md:h-[710px]"
          style={{
            transform: "translateX(-50%) rotate(3deg)",
            boxShadow: "0 40px 80px -24px rgba(15,23,42,0.4), 0 0 0 1px rgba(15,23,42,0.06)",
          }}
        >
          <div className="flex flex-col gap-[18px] px-[30px] pb-6 pt-[26px] text-white" style={{ background: primary }}>
            <div className="flex items-center justify-between text-[11px] uppercase tracking-[0.08em] text-white/80">
              <span>Property report · {reportDate()}</span>
              <span className="text-sm font-bold normal-case tracking-[-0.01em] text-white">
                {DEMO_AGENT.brokerage}
              </span>
            </div>
            <div className="text-xl font-semibold leading-[1.15]">
              {DEMO_LISTING.address}, {area}
            </div>
            <div className="flex flex-col gap-1.5">
              <span className="whitespace-nowrap text-[34px] font-semibold leading-[0.95] tracking-[-0.04em] sm:text-[44px]">
                {DEMO_COMPS_RANGE.low} – {DEMO_COMPS_RANGE.high}
              </span>
              <span className="text-[13px] leading-[1.35] text-white/85">
                range of comparable sales · median {DEMO_COMPS_RANGE.median}
              </span>
            </div>
            <div className="grid grid-cols-3 gap-3 border-t border-white/25 pt-3.5">
              {[
                [`${DEMO_LISTING.beds} / ${DEMO_LISTING.baths}`, "Bd / Ba"],
                [DEMO_LISTING.sqft, "Sq ft"],
                [DEMO_LISTING.pricePerSqft, "Per sq ft"],
              ].map(([v, l]) => (
                <div key={l}>
                  <div className="text-lg font-semibold">{v}</div>
                  <div className="text-[11px] text-white/85">{l}</div>
                </div>
              ))}
            </div>
          </div>

          <div className="flex flex-1 flex-col gap-3 px-[30px] pb-[26px] pt-[22px]">
            <div className="border-b-[1.5px] border-[#14161A] pb-2 text-[11px] uppercase tracking-[0.06em] text-[#5E636B]">
              Comparable sales · last 6 months
            </div>
            {DEMO_COMPS.map((c) => (
              <div
                key={c.address}
                className="grid items-center gap-3.5 border-b border-[#ECECE8] pb-2.5 text-[13px]"
                style={{ gridTemplateColumns: "minmax(0,1fr) auto auto" }}
              >
                <div className="flex min-w-0 flex-col">
                  <span className="truncate font-semibold text-[#0F172A]">{c.address}</span>
                  <span className="text-[11px] text-[#5E636B]">{c.specs}</span>
                </div>
                <span className="text-[11px] text-[#5E636B]">{c.dist}</span>
                <span className="font-semibold tabular-nums text-[#0F172A]">{c.price}</span>
              </div>
            ))}
            <div className="mt-auto flex flex-col gap-1.5 pt-6">
              <div className="relative h-7 rounded-[5px] bg-[#F4F4F1]">
                <div
                  className="absolute rounded-[5px] opacity-90"
                  style={{ inset: "0 28% 0 12%", background: accent }}
                />
                <div className="absolute left-[52%] top-[-4px] h-9 w-[3px] rounded-sm bg-[#14161A]" />
                <span className="absolute left-[52%] top-[-22px] -translate-x-1/2 whitespace-nowrap text-[11px] font-bold text-[#0F172A]">
                  Your home
                </span>
              </div>
              <div className="flex justify-between text-[11px] text-[#5E636B]">
                <span>{DEMO_COMPS_RANGE.low}</span>
                <span>Range of comparable sales</span>
                <span>{DEMO_COMPS_RANGE.high}</span>
              </div>
            </div>
          </div>
        </div>
      </div>

      <SectionCopy
        eyebrow="Property reports & CMAs"
        title="Type an address. Walk in with a seller report."
        lede="The range of comparable sales, every sale behind it, your branding. Ready before the listing appointment."
      />
    </SplitSection>
  );
}

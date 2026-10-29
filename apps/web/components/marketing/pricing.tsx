"use client";

/**
 * "Pricing" — Design's `Landing v4` row layout, with the verified figures.
 *
 * The deck described the tiers by cities and cadence: "1 city, monthly",
 * "Up to 3 cities, weekly", "Any number of cities". The product limits neither
 * — nothing gates weekly delivery by plan, and a schedule is not a city — so
 * those lines would sell a restriction that does not exist. The rows keep the
 * figures the M-phase verified against the plans table (G1a: Growth is 25,
 * set by migration 0054) in the deck's layout.
 *
 * "Priority Generation" stays out for the reason given in D-046: no
 * implementation exists.
 */
import { Eyebrow, Lede, SectionTitle, SplitSection } from "./landing-primitives";

const plans = [
  {
    name: "Free",
    price: "$0",
    per: "forever",
    summary: "3 market reports a month · 1 schedule · 1 property report",
    recommended: false,
  },
  {
    name: "Growth",
    price: "$19",
    per: "/mo",
    summary: "25 market reports a month · 3 schedules · 5 property reports · CSV import",
    recommended: true,
  },
  {
    name: "Growth Plus",
    price: "$29",
    per: "/mo",
    summary: "Unlimited reports and schedules · 25 property reports",
    recommended: false,
  },
];

export function Pricing() {
  return (
    <SplitSection white id="pricing" align="start">
      <div className="flex flex-col gap-5">
        <Eyebrow>Pricing</Eyebrow>
        <SectionTitle>Free for one city. Pay when you want more.</SectionTitle>
        <Lede>
          Every plan includes property reports, your lead-capture page and contacts. No credit
          card to start.
        </Lede>
      </div>

      <div className="flex flex-col border-t border-[#E4E2DA]">
        {plans.map((p) => (
          <div
            key={p.name}
            className="grid items-center gap-4 border-b border-[#E4E2DA] py-7 sm:gap-6"
            style={{ gridTemplateColumns: "minmax(110px, 150px) minmax(0,1fr) auto" }}
          >
            <div className="flex items-baseline gap-1">
              <span className="text-[36px] font-extrabold leading-none tracking-[-0.035em] text-[#0F172A] sm:text-[44px]">
                {p.price}
              </span>
              <span className="text-sm text-[#64748B]">{p.per}</span>
            </div>
            <div className="flex min-w-0 flex-col gap-1">
              <div className="flex flex-wrap items-center gap-2.5">
                <span className="text-[19px] font-bold text-[#0F172A]">{p.name}</span>
                {p.recommended && (
                  <span className="rounded-full bg-[#4F46E5] px-[9px] py-[3px] text-[11px] font-bold uppercase tracking-[0.04em] text-white">
                    Most popular
                  </span>
                )}
              </div>
              <span className="text-[15px] text-[#64748B]">{p.summary}</span>
            </div>
            <a
              href="/register"
              className={`inline-flex h-11 items-center justify-center whitespace-nowrap rounded-[10px] px-[18px] text-[15px] font-semibold ${
                p.recommended
                  ? "bg-[#4F46E5] text-white hover:bg-[#4338CA]"
                  : "border border-[#E4E2DA] bg-white text-[#0F172A] hover:bg-[#F6F5F1]"
              }`}
            >
              Start free
            </a>
          </div>
        ))}
      </div>
    </SplitSection>
  );
}

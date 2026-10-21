"use client";

/**
 * "Autopilot" — Design's `Landing v4`, the phone with the monthly email.
 *
 * Every person, figure and date comes from `lib/demo-data.ts`. The deck's mock
 * used its own agent and its own Irvine median ($1.46M against the fixture's
 * $1.2M), and its send dates were literal months.
 */
import { Phone } from "lucide-react";
import {
  DEMO_AGENT,
  DEMO_MARKET,
  DEMO_SPHERE,
  currentMonthName,
  monthlySendDates,
} from "@/lib/demo-data";
import {
  AgentDisc,
  DotField,
  PhoneFrame,
  SectionCopy,
  SplitSection,
  useLandingTheme,
} from "./landing-primitives";

export function Autopilot() {
  const { primary, area } = useLandingTheme();
  const { last, next } = monthlySendDates();
  const firstName = DEMO_AGENT.name.split(" ")[0];

  return (
    <SplitSection white>
      <SectionCopy
        eyebrow="Autopilot"
        title="Set it once. It goes out every month."
        lede="Pick a city, pick monthly or weekly. Your sphere hears from you whether you remember or not."
      />

      <div className="relative h-[600px] min-w-0 sm:h-[640px]">
        <DotField />
        <PhoneFrame tilt={-3}>
          <div className="flex items-center gap-3 border-b border-[#F1F5F9] px-5 pb-3.5 pt-2.5">
            <AgentDisc />
            <div className="min-w-0">
              <div className="text-[15px] font-bold text-[#0F172A]">{DEMO_AGENT.name}</div>
              <div className="truncate text-[13px] text-[#475569]">
                {area} market update · {currentMonthName()}
              </div>
            </div>
          </div>
          <div className="flex flex-col gap-3.5 px-5 py-[18px]">
            <div className="flex flex-col gap-1 rounded-xl p-[18px] text-white" style={{ background: primary }}>
              <div className="text-[10px] uppercase tracking-[0.14em] text-white/75">
                {area} · Last 30 days
              </div>
              <div className="text-[40px] font-bold leading-none tracking-[-0.035em]">
                {DEMO_MARKET.medianPrice}
              </div>
              <div className="text-[13px] text-white/85">
                median sale price · ▲ {DEMO_MARKET.trends.medianPrice.replace("+", "")}
              </div>
            </div>
            <div className="grid grid-cols-3 gap-2">
              {[
                [DEMO_MARKET.closedSales, "Sold"],
                [DEMO_MARKET.daysOnMarket, "Days"],
                [DEMO_MARKET.pctOfAsk, "Of ask"],
              ].map(([v, l]) => (
                <div key={l} className="rounded-[10px] bg-[#F6F5F1] px-2 py-3 text-center">
                  <div className="text-xl font-bold text-[#0F172A]">{v}</div>
                  <div className="text-[10px] uppercase tracking-[0.05em] text-[#78716C]">{l}</div>
                </div>
              ))}
            </div>
            <div
              className="flex h-12 items-center justify-center gap-2 rounded-xl text-base font-semibold text-white"
              style={{ background: primary }}
            >
              <Phone className="h-4 w-4" />
              Call {firstName}
            </div>
            <div className="text-center text-xs text-[#94A3B8]">Full report attached (PDF)</div>
          </div>
        </PhoneFrame>

        <div
          className="absolute bottom-9 left-0 flex items-center gap-3.5 rounded-[14px] bg-white px-5 py-4"
          style={{
            transform: "rotate(2deg)",
            boxShadow: "0 24px 48px -16px rgba(15,23,42,0.35), 0 0 0 1px rgba(15,23,42,0.06)",
          }}
        >
          <span
            className="h-3 w-3 shrink-0 rounded-full bg-[#059669]"
            style={{ boxShadow: "0 0 0 5px #D1FAE5" }}
          />
          <div className="flex flex-col gap-0.5">
            <span className="text-base font-bold text-[#0F172A]">
              Monthly {area} Snapshot → {DEMO_SPHERE.all} contacts
            </span>
            <span className="text-sm text-[#64748B]">
              Sent {last} · Next {next}, 9:00 AM
            </span>
          </div>
        </div>
      </div>
    </SplitSection>
  );
}

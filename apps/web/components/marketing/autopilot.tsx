"use client";

/**
 * "Autopilot" — Design's `Landing v13`, the phone with the monthly email.
 *
 * New in v13: the three steps under the copy, and two cards beside the phone
 * that show the other two ends of the loop — the schedule that was set once
 * (top right) and the sends that already went out (right). The status card
 * (bottom left) is v4's. The two new cards are hidden below `sm`, where the
 * phone fills the stage.
 *
 * The market figures are the Market Snapshot preview's own — the sample the
 * worker renders the Snapshot page on this page from, read from the preview
 * route's `/facts` — so the email and the report it attaches agree about the
 * city. The deck prints a delta beside the median ("▲ 3.1%"); `/facts` has no
 * such figure, so it is left off rather than invented. People and dates come
 * from `lib/demo-data.ts`; the "Already sent" dates are the last three firsts
 * of the month, counted back from today, with no figures beside them.
 */
import { useEffect, useState } from "react";
import { CalendarClock, Check, Phone } from "lucide-react";
import {
  DEMO_AGENT,
  DEMO_SPHERE,
  currentMonthName,
  monthlySendDates,
} from "@/lib/demo-data";
import {
  AgentDisc,
  DotField,
  FloatCard,
  PhoneFrame,
  SectionCopy,
  SplitSection,
  useLandingTheme,
  type Step,
} from "./landing-primitives";

const STEPS: readonly Step[] = [
  ["Pick a city and a report", "Any of the market reports above."],
  ["Pick a schedule", "Monthly or weekly."],
  ["It sends itself", "Fresh MLS data, your branding, PDF attached. Nothing more for you to do."],
];

/** "Nov 1", "Oct 1", "Sep 1" — the last `count` monthly sends, newest first. */
function pastSends(count: number, now: Date = new Date()): string[] {
  return Array.from({ length: count }, (_, i) =>
    new Date(now.getFullYear(), now.getMonth() - i, 1).toLocaleDateString("en-US", {
      month: "short",
      day: "numeric",
    }),
  );
}

export function Autopilot() {
  const { primary, area } = useLandingTheme();
  const { last, next } = monthlySendDates();
  const firstName = DEMO_AGENT.name.split(" ")[0];
  const facts = useSnapshotFacts();
  const m = facts?.metrics ?? {};
  const num = (v: unknown, f: (n: number) => string) => (typeof v === "number" ? f(v) : "—");
  const median = num(m.median_close_price, (n) => `$${n.toLocaleString("en-US")}`);

  return (
    <SplitSection id="autopilot">
      <SectionCopy
        eyebrow="Autopilot"
        title="In their inbox every month. Even when you're busy."
        lede="Set a schedule once. TrendyReports builds each new report and emails it to your contacts, so you never go quiet."
        steps={STEPS}
      />

      <div className="relative h-[600px] min-w-0 sm:h-[640px]">
        <DotField />
        <PhoneFrame tilt={-3} x={42}>
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
                {median}
              </div>
              <div className="text-[13px] text-white/85">median sale price</div>
            </div>
            <div className="grid grid-cols-3 gap-2">
              {[
                [num(facts?.counts?.Closed, String), "Sold"],
                [num(m.avg_dom, String), "Days"],
                [num(m.close_to_list_ratio, (n) => `${n}%`), "Of ask"],
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

        {/* 1. The schedule, set once. */}
        <FloatCard tilt={2} className="-top-5 right-0 hidden items-center gap-3 px-4 py-3 sm:flex">
          <span className="flex h-9 w-9 shrink-0 items-center justify-center rounded-[10px] bg-[#EEF0F8]">
            <CalendarClock className="h-[18px] w-[18px] text-[#0F172A]" />
          </span>
          <div className="flex flex-col gap-px">
            <span className="whitespace-nowrap text-sm font-bold text-[#0F172A]">
              Every month on the 1st
            </span>
            <span className="whitespace-nowrap text-xs text-[#64748B]">
              9:00 AM · {area} Snapshot
            </span>
          </div>
          <span aria-hidden className="relative h-[22px] w-[38px] shrink-0 rounded-full bg-[#059669]">
            <span className="absolute right-0.5 top-0.5 h-[18px] w-[18px] rounded-full bg-white" />
          </span>
        </FloatCard>

        {/* 2. What already went out. */}
        <FloatCard tilt={-2} className="right-0 top-[300px] hidden flex-col gap-2 px-4 py-3.5 sm:flex">
          <span className="text-xs font-bold uppercase tracking-[0.1em] text-[#475569]">
            Already sent
          </span>
          {pastSends(3).map((d) => (
            <div key={d} className="flex items-center gap-2 whitespace-nowrap text-[13px]">
              <Check className="h-3.5 w-3.5 shrink-0 text-[#059669]" />
              <span className="font-bold text-[#0F172A]">{d}</span>
              <span className="text-[#64748B]">Sent</span>
            </div>
          ))}
        </FloatCard>

        {/* 3. Where it stands now. */}
        <FloatCard tilt={2} className="bottom-9 left-0 flex items-center gap-3.5 px-5 py-4">
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
        </FloatCard>
      </div>
    </SplitSection>
  );
}

interface SnapshotFacts {
  counts?: Record<string, number>;
  metrics?: Record<string, number>;
}

/** The Snapshot sample's figures. A dash until they arrive, never a guess. */
function useSnapshotFacts() {
  const [facts, setFacts] = useState<SnapshotFacts | null>(null);
  useEffect(() => {
    let live = true;
    fetch("/api/proxy/v1/report-preview/market_snapshot/facts")
      .then((r) => (r.ok ? r.json() : null))
      .then((f) => live && setFacts(f))
      .catch(() => {});
    return () => {
      live = false;
    };
  }, []);
  return facts;
}

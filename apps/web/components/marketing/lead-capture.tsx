"use client";

/**
 * "Lead capture" — Design's `Landing v13`, the home-value page on a phone.
 *
 * New in v13: the three steps under the copy, and the two ends of the loop
 * beside the phone — where the homeowner came from (the QR chip, top right)
 * and what they get back (a property report cover, left). The lead card
 * (bottom right) is v4's. The two new pieces are hidden below `sm`.
 *
 * The page on the phone keeps main's wording, not the deck's: "See what homes
 * like yours sold for" / "Get my report", not "What's your home worth today?"
 * / "Get my estimate". The report estimates nothing (LR-025, D-383), so the
 * page that hands it over does not promise an estimate. The lede was reworded
 * to match for the same reason.
 *
 * The cover is the first template's render the wizard already ships
 * (`/previews/pages/{id}/cover.jpg`).
 *
 * The arriving lead is a fixture contact rather than the deck's own name, so
 * the person who asks here is the same person the contacts preview below
 * lists as a new lead.
 */
import type { CSSProperties } from "react";
import Image from "next/image";
import { QrCode, UserPlus } from "lucide-react";
import { DEMO_AGENT, DEMO_CONTACTS, DEMO_LEAD, currentMonthName } from "@/lib/demo-data";
import { THEMES } from "@/components/property-wizard/types";
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

/** The contact who arrives as a lead — shared with the contacts preview. */
export const LEAD_CONTACT = DEMO_CONTACTS[3];

const STEPS: readonly Step[] = [
  [
    "They scan or tap",
    "A QR code on your reports, and a link for your email signature and open-house sign.",
  ],
  ["They ask", "They enter their address and how to reach them."],
  [
    "You both get something",
    "They receive a property report with your branding. You get their name and number.",
  ],
];

export function LeadCapture() {
  const { primary } = useLandingTheme();

  return (
    <SplitSection id="lead-capture">
      <SectionCopy
        eyebrow="Lead capture"
        title="A home-value page with your name on it."
        lede="Homeowners want to know what homes like theirs sold for. They get a report with your brand on it, and you get the lead."
        steps={STEPS}
      />

      <div className="relative h-[600px] min-w-0 sm:h-[640px]">
        <DotField />

        {/* What they get back. */}
        <div
          className="absolute left-0 top-[84px] hidden w-[204px] flex-col gap-2.5 sm:flex"
          style={{ transform: "rotate(-7deg)" }}
        >
          <span className="whitespace-nowrap text-[13px] font-semibold text-[#475569]">
            They receive this
          </span>
          <div
            className="overflow-hidden rounded-md bg-white"
            style={{
              aspectRatio: "510 / 660",
              boxShadow: "0 30px 60px -20px rgba(15,23,42,0.4), 0 0 0 1px rgba(15,23,42,0.06)",
            }}
          >
            <Image
              src={`/previews/pages/${THEMES[0].id}/cover.jpg`}
              alt=""
              width={510}
              height={660}
              sizes="204px"
              className="block h-full w-full"
            />
          </div>
        </div>

        {/* Where they came from. */}
        <FloatCard tilt={2} className="-top-5 right-0 hidden items-center gap-3 px-4 py-3 sm:flex">
          <span className="flex h-9 w-9 shrink-0 items-center justify-center rounded-[10px] bg-[#EEF0F8]">
            <QrCode className="h-[18px] w-[18px] text-[#0F172A]" />
          </span>
          <div className="flex flex-col gap-px">
            <span className="whitespace-nowrap text-sm font-bold text-[#0F172A]">
              Scanned from your report
            </span>
            <span className="whitespace-nowrap text-xs text-[#64748B]">
              {currentMonthName()} Snapshot
            </span>
          </div>
        </FloatCard>

        <PhoneFrame tilt={3} x={62}>
          <div className="flex flex-col gap-[18px] px-6 pt-6">
            <div className="flex items-center gap-2.5">
              <AgentDisc size={36} />
              <div className="flex flex-col">
                <span className="text-[13px] font-bold text-[#0F172A]">{DEMO_AGENT.name}</span>
                <span className="text-[11px] text-[#64748B]">{DEMO_AGENT.brokerage}</span>
              </div>
            </div>
            <div
              className="text-[28px] font-extrabold leading-[1.05] tracking-[-0.03em] text-[#0F172A]"
              style={{ textWrap: "balance" } as CSSProperties}
            >
              See what homes like yours sold for
            </div>
            <div className="text-sm text-[#64748B]">Based on the last 6 months of sales near you.</div>
            <div className="flex h-[50px] items-center rounded-xl border-[1.5px] border-[#D6D3CB] px-4 text-[15px] text-[#0F172A]">
              {DEMO_LEAD.address}
            </div>
            <div
              className="flex h-[50px] items-center justify-center rounded-xl text-base font-semibold text-white"
              style={{ background: primary }}
            >
              Get my report
            </div>
            <div className="text-center text-xs text-[#94A3B8]">Takes 10 seconds · No obligation</div>
          </div>
        </PhoneFrame>

        {/* What the agent gets. */}
        <FloatCard
          tilt={-2}
          className="bottom-12 right-0 flex w-[280px] items-start gap-3.5 px-[18px] py-4 sm:w-[300px]"
        >
          <span className="flex h-10 w-10 shrink-0 items-center justify-center rounded-xl bg-[#ECFDF5]">
            <UserPlus className="h-[18px] w-[18px] text-[#059669]" />
          </span>
          <div className="flex min-w-0 flex-col gap-0.5">
            <span className="text-[15px] font-bold text-[#0F172A]">New lead · {DEMO_LEAD.address}</span>
            <span className="text-[13px] text-[#64748B]">
              {LEAD_CONTACT.name} · wants a value · just now
            </span>
          </div>
        </FloatCard>
      </div>
    </SplitSection>
  );
}

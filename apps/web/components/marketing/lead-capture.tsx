"use client";

/**
 * "Lead capture" — Design's `Landing v4`, the home-value page on a phone.
 *
 * The arriving lead is a fixture contact rather than the deck's own name, so
 * the person who asks for a value here is the same person the contacts
 * preview below lists as a new lead.
 */
import type { CSSProperties } from "react";
import { UserPlus } from "lucide-react";
import { DEMO_AGENT, DEMO_CONTACTS, DEMO_LEAD } from "@/lib/demo-data";
import {
  AgentDisc,
  DotField,
  PhoneFrame,
  SectionCopy,
  SplitSection,
  useLandingTheme,
} from "./landing-primitives";

/** The contact who arrives as a lead — shared with the contacts preview. */
export const LEAD_CONTACT = DEMO_CONTACTS[3];

export function LeadCapture() {
  const { primary, area } = useLandingTheme();

  return (
    <SplitSection white id="lead-capture">
      <SectionCopy
        eyebrow="Lead capture"
        title="A home-value page with your name on it."
        lede="Put the link in your reports, your signature, your open-house sign. Leads land in your inbox."
      />

      <div className="relative h-[600px] min-w-0 sm:h-[640px]">
        <DotField />
        <PhoneFrame tilt={3}>
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
              What&apos;s your {area} home worth today?
            </div>
            <div className="text-sm text-[#64748B]">Based on this month&apos;s closed sales near you.</div>
            <div className="flex h-[50px] items-center rounded-xl border-[1.5px] border-[#D6D3CB] px-4 text-[15px] text-[#0F172A]">
              {DEMO_LEAD.address}
            </div>
            <div
              className="flex h-[50px] items-center justify-center rounded-xl text-base font-semibold text-white"
              style={{ background: primary }}
            >
              Get my estimate
            </div>
            <div className="text-center text-xs text-[#94A3B8]">Takes 10 seconds · No obligation</div>
          </div>
        </PhoneFrame>

        <div
          className="absolute bottom-12 right-0 flex w-[280px] items-start gap-3.5 rounded-[14px] bg-white px-[18px] py-4 sm:w-[300px]"
          style={{
            transform: "rotate(-2deg)",
            boxShadow: "0 24px 48px -16px rgba(15,23,42,0.35), 0 0 0 1px rgba(15,23,42,0.06)",
          }}
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
        </div>
      </div>
    </SplitSection>
  );
}

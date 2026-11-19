"use client";

/**
 * "Contacts" — Design's `Landing v13`, the contact list with send status.
 *
 * New in v13: which send the list is reporting on (top right of the card),
 * the four totals under the filters, the "Call first" card, and the three
 * steps under the copy.
 *
 * Rows are fixture contacts. The first fixture contact is skipped because it
 * is also `DEMO_AGENT` — the agent does not appear in their own list. The
 * deck draws six rows with neighbourhoods; the fixture has four people and no
 * neighbourhoods, and the fixture wins.
 *
 * The totals are fixtures too: Sent is `DEMO_SPHERE.all`; Opened, Clicked and
 * New lead are `DEMO_SEND`, added to `lib/demo-data.ts` by this handoff so no
 * demo figure is written inline (that file's rule 2).
 *
 * "Call first" is whichever row is marked Clicked, so the card and the list
 * cannot name different people. It sits below the list, not over it.
 */
import { Phone } from "lucide-react";
import { DEMO_CONTACTS, DEMO_SEND, DEMO_SPHERE, currentMonthName } from "@/lib/demo-data";
import {
  FloatCard,
  Glow,
  SectionCopy,
  SplitSection,
  useLandingTheme,
  type Step,
} from "./landing-primitives";
import { LEAD_CONTACT } from "./lead-capture";

type Status = "Opened" | "Clicked" | "New lead" | "Sent";

const STEPS: readonly Step[] = [
  ["Keep one list", "Past clients, your sphere and new leads from your home-value page."],
  ["Send", "Every scheduled report goes out to them."],
  ["Follow up", "Opened, clicked and new-lead tags show who to call first."],
];

export function ContactManagement() {
  const { primary, accent } = useLandingTheme();

  const pill: Record<Status, { fg: string; bg: string }> = {
    Opened: { fg: "#065F46", bg: "#D1FAE5" },
    Clicked: { fg: "#fff", bg: accent },
    "New lead": { fg: "#fff", bg: "#0F172A" },
    Sent: { fg: "#64748B", bg: "#F1F5F9" },
  };

  const rows: { name: string; initials: string; tag: string; status: Status; disc: string }[] =
    DEMO_CONTACTS.slice(1).map((c, i) => {
      if (c.name === LEAD_CONTACT.name) {
        return { ...c, tag: "Lead · Home value", status: "New lead", disc: primary };
      }
      const cycle: [string, Status, string][] = [
        ["Past client", "Opened", primary],
        ["Sphere", "Clicked", "#475569"],
        ["Past client", "Opened", "#7C3AED"],
        ["Sphere", "Sent", "#B45309"],
      ];
      const [tag, status, disc] = cycle[i % cycle.length];
      return { ...c, tag, status, disc };
    });

  const totals: [number, string][] = [
    [DEMO_SPHERE.all, "Sent"],
    [DEMO_SEND.opened, "Opened"],
    [DEMO_SEND.clicked, "Clicked"],
    [DEMO_SEND.newLeads, "New lead"],
  ];

  const callFirst = rows.find((r) => r.status === "Clicked");

  return (
    <SplitSection white id="contacts">
      <div className="relative h-[680px] min-w-0 sm:h-[660px]">
        <Glow />
        <div
          className="absolute left-1/2 top-[30px] flex w-[520px] max-w-full flex-col overflow-hidden rounded-2xl bg-white"
          style={{
            transform: "translateX(-50%) rotate(-2deg)",
            boxShadow: "0 40px 80px -24px rgba(15,23,42,0.4), 0 0 0 1px rgba(15,23,42,0.06)",
          }}
        >
          <div className="flex flex-wrap items-center justify-between gap-3 border-b border-[#ECEAE3] px-6 py-5">
            <div className="flex flex-wrap gap-2">
              <span className="whitespace-nowrap rounded-full bg-[#0F172A] px-3.5 py-[7px] text-[13px] font-semibold text-white">
                All · {DEMO_SPHERE.all}
              </span>
              <span className="whitespace-nowrap rounded-full border border-[#E4E2DA] px-3.5 py-[7px] text-[13px] font-semibold text-[#475569]">
                Past clients · {DEMO_SPHERE.pastClients}
              </span>
              <span className="whitespace-nowrap rounded-full border border-[#E4E2DA] px-3.5 py-[7px] text-[13px] font-semibold text-[#475569]">
                Leads · {DEMO_SPHERE.leads}
              </span>
            </div>
            <span className="text-[13px] text-[#64748B]">{currentMonthName()} Snapshot</span>
          </div>

          <div className="grid grid-cols-4 gap-3 border-b border-[#ECEAE3] bg-[#F8F9FC] px-6 py-4">
            {totals.map(([v, l]) => (
              <div key={l} className="flex flex-col gap-0.5">
                <span className="text-[22px] font-extrabold leading-tight tracking-[-0.02em] tabular-nums text-[#0F172A]">
                  {v}
                </span>
                <span className="text-xs text-[#64748B]">{l}</span>
              </div>
            ))}
          </div>

          {rows.map((r) => (
            <div
              key={r.name}
              className="grid items-center gap-3.5 border-b border-[#F1F1EE] px-6 py-3.5"
              style={{ gridTemplateColumns: "44px minmax(0,1fr) auto" }}
            >
              <div
                className="flex h-11 w-11 items-center justify-center rounded-full text-sm font-bold text-white"
                style={{ background: r.disc }}
              >
                {r.initials}
              </div>
              <div className="flex min-w-0 flex-col">
                <span className="truncate text-base font-semibold text-[#0F172A]">{r.name}</span>
                <span className="text-[13px] text-[#64748B]">{r.tag}</span>
              </div>
              <span
                className="whitespace-nowrap rounded-full px-3 py-[5px] text-[13px] font-bold"
                style={{ color: pill[r.status].fg, background: pill[r.status].bg }}
              >
                {r.status}
              </span>
            </div>
          ))}
        </div>

        {callFirst && (
          <FloatCard
            tilt={2}
            className="bottom-0 right-0 flex w-[300px] max-w-full flex-col gap-3 px-[18px] py-4 md:-right-3"
          >
            <div className="flex flex-col gap-0.5">
              <span className="text-xs font-bold uppercase tracking-[0.1em] text-[#475569]">
                Call first
              </span>
              <span className="text-[17px] font-bold text-[#0F172A]">{callFirst.name}</span>
              <span className="text-[13px] text-[#64748B]">Opened and clicked through · today</span>
            </div>
            <div className="flex h-11 items-center justify-center gap-2 rounded-[10px] bg-[#0F172A] text-[15px] font-semibold text-white">
              <Phone className="h-[18px] w-[18px] shrink-0" />
              Call {callFirst.name.split(" ")[0]}
            </div>
          </FloatCard>
        )}
      </div>

      <SectionCopy
        eyebrow="Contacts"
        title="See who opened. Call them first."
        lede="Every send comes back with a short list of people worth a phone call today."
        steps={STEPS}
      />
    </SplitSection>
  );
}

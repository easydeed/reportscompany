"use client";

/**
 * "Contacts" — Design's `Landing v4`, the sphere list with send status.
 *
 * Rows are fixture contacts. The first fixture contact is skipped because it
 * is also `DEMO_AGENT` — the agent does not appear in their own sphere.
 */
import { DEMO_CONTACTS, DEMO_SPHERE } from "@/lib/demo-data";
import { Glow, SectionCopy, SplitSection, useLandingTheme } from "./landing-primitives";
import { LEAD_CONTACT } from "./lead-capture";

type Status = "Opened" | "Clicked" | "New lead" | "Sent";

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

  return (
    <SplitSection id="contacts">
      <div className="relative h-[480px] min-w-0 md:h-[560px]">
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
              <span className="rounded-full bg-[#0F172A] px-3.5 py-[7px] text-[13px] font-semibold text-white">
                All · {DEMO_SPHERE.all}
              </span>
              <span className="rounded-full border border-[#E4E2DA] px-3.5 py-[7px] text-[13px] font-semibold text-[#475569]">
                Past clients · {DEMO_SPHERE.pastClients}
              </span>
              <span className="rounded-full border border-[#E4E2DA] px-3.5 py-[7px] text-[13px] font-semibold text-[#475569]">
                Leads · {DEMO_SPHERE.leads}
              </span>
            </div>
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
      </div>

      <SectionCopy
        eyebrow="Contacts"
        title="See who opened. Call them first."
        lede="Your whole sphere in one list. Every send tells you who's paying attention."
      />
    </SplitSection>
  );
}

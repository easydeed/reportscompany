/**
 * Site-wide footer. Same rationale as site-nav.tsx — one footer sitewide (M2).
 *
 * Design's `Landing v4` footer, with four entries left out:
 *
 * - "Open Houses" under Reports. The product has that report disabled.
 * - "Status" beside Privacy and Terms. /status was deleted in 725802a7 for
 *   fabricated uptime figures; there is no such route.
 * - "Support" under Company, which the deck made a mailto. The address is
 *   shown in full in the brand column instead, so the reader can see where it
 *   goes and nothing in a list of page links opens a mail client (M4-T1).
 * - "and partner MLSs" in the data line. Unverified; CRMLS is what the help
 *   content states.
 *
 * "Sponsors" anchors to the sponsor band rather than mailing sales directly,
 * for the same M4-T1 reason. All anchors are root-relative.
 */
import { Logo } from "@/components/logo"

const columns: { title: string; links: [string, string][] }[] = [
  {
    title: "Product",
    links: [
      ["Market reports", "/#reports"],
      ["Property reports", "/#property-reports"],
      ["Home-value page", "/#lead-capture"],
      ["Contacts", "/#contacts"],
      ["Pricing", "/#pricing"],
    ],
  },
  {
    title: "Reports",
    links: [
      ["Market Snapshot", "/#reports"],
      ["New Listings", "/#reports"],
      ["Closed Sales", "/#reports"],
      ["Price Bands", "/#reports"],
    ],
  },
  {
    title: "Company",
    links: [
      ["Log in", "/login"],
      ["Start free", "/register"],
      ["Sponsors", "/#sponsors"],
    ],
  },
];

export function SiteFooter() {
  return (
    <footer className="mt-auto border-t border-[#ECEAE3] bg-[#FAFAF7]">
      <div className="mx-auto flex max-w-[1200px] flex-col gap-14 px-4 pb-10 pt-[72px] md:px-8">
        <div
          className="grid gap-10"
          style={{ gridTemplateColumns: "repeat(auto-fit, minmax(150px, 1fr))" }}
        >
          <div className="col-span-full flex max-w-[320px] flex-col gap-4 md:col-span-1">
            <Logo className="h-7 self-start" />
            <p className="m-0 text-[15px] leading-[1.55] text-[#64748B]">
              Automated market reports for Southern California agents. Live MLS data, your brand,
              sent every month.
            </p>
            <a
              href="mailto:support@trendyreports.io"
              className="text-[15px] font-semibold text-[#4F46E5] hover:text-[#3730A3]"
            >
              support@trendyreports.io
            </a>
          </div>
          {columns.map((col) => (
            <div key={col.title} className="flex flex-col gap-3">
              <span className="text-xs font-bold uppercase tracking-[0.12em] text-[#0F172A]">
                {col.title}
              </span>
              {col.links.map(([label, href]) => (
                <a
                  key={label}
                  href={href}
                  className="text-[15px] text-[#475569] hover:text-[#0F172A]"
                >
                  {label}
                </a>
              ))}
            </div>
          ))}
        </div>

        <div className="flex flex-wrap items-center justify-between gap-4 border-t border-[#ECEAE3] pt-6 text-sm text-[#64748B]">
          <span>{"© 2026 TrendyReports · Data from CRMLS"}</span>
          <div className="flex flex-wrap gap-6">
            <a href="/privacy" className="text-[#64748B] hover:text-[#0F172A]">
              Privacy
            </a>
            <a href="/terms" className="text-[#64748B] hover:text-[#0F172A]">
              Terms
            </a>
          </div>
        </div>
      </div>
    </footer>
  );
}

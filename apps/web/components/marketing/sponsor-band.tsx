/**
 * "Title company or lender?" — Design's `Landing v4`, the band above the footer.
 *
 * The conversion action is the same mailto the page already carried in
 * who-its-for.tsx, so this adds no new destination. A dedicated page for title
 * companies is M6 and still waits on G4 (what they buy, and what the action
 * should be); when it exists, this link should point there.
 *
 * `id="sponsors"` is what the footer's Sponsors entry anchors to, so the
 * footer does not carry a mailto in a list of page links (M4-T1).
 */
export function SponsorBand() {
  return (
    <section id="sponsors" className="bg-[#EEEDE7]">
      <div className="mx-auto flex max-w-[1200px] flex-wrap items-center justify-between gap-4 px-4 py-7 md:px-8">
        <span className="text-base text-[#334155]">
          <strong className="text-[#0F172A]">Title company or lender?</strong> Sponsor TrendyReports
          for your agents. Your logo goes next to theirs.
        </span>
        <a
          href="mailto:sales@trendyreports.io"
          className="text-[15px] font-semibold text-[#4F46E5] hover:text-[#3730A3]"
        >
          Talk to us →
        </a>
      </div>
    </section>
  );
}

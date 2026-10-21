/**
 * Site-wide header. Used by the landing page AND every standalone content
 * route (legal, about, blog, careers, docs, 404) — one header sitewide (M2).
 *
 * Design's `Landing v4` nav: logo, two section links, Log in, and an ink
 * "Start free". Not sticky, a hairline underneath — the deck's.
 *
 * Section anchors are ROOT-RELATIVE ("/#pricing", not "#pricing") so they
 * navigate back to the landing page from any route that shares this header.
 *
 * On a phone the two section links go, and Log in and Start free stay: the
 * four together do not fit at 390px beside the logo.
 */
export function SiteNav() {
  return (
    <nav className="border-b border-[#ECEAE3] bg-[#FAFAF7]">
      <div className="mx-auto flex max-w-[1200px] items-center justify-between gap-6 px-4 py-[18px] md:px-8">
        <a href="/">
          <img src="/indigo.png" alt="TrendyReports" className="h-7 w-auto" />
        </a>
        <div className="flex items-center gap-5 md:gap-7">
          <a
            href="/#reports"
            className="hidden text-[15px] font-medium text-[#334155] hover:text-[#0F172A] sm:inline"
          >
            Reports
          </a>
          <a
            href="/#pricing"
            className="hidden text-[15px] font-medium text-[#334155] hover:text-[#0F172A] sm:inline"
          >
            Pricing
          </a>
          <a href="/login" className="text-[15px] font-medium text-[#334155] hover:text-[#0F172A]">
            Log in
          </a>
          <a
            href="/register"
            className="inline-flex h-10 items-center rounded-lg bg-[#0F172A] px-[18px] text-[15px] font-semibold text-white transition-colors hover:bg-[#1E293B]"
          >
            Start free
          </a>
        </div>
      </div>
    </nav>
  );
}

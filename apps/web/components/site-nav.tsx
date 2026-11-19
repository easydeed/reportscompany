/**
 * Site-wide header. Used by the landing page AND every standalone content
 * route (legal, about, blog, careers, docs, 404) — one header sitewide (M2).
 *
 * Design's `Landing v13` nav: logo, four section links, Log in, and an ink
 * "Start free". Not sticky, a hairline underneath.
 *
 * Section anchors are ROOT-RELATIVE ("/#pricing", not "#pricing") so they
 * navigate back to the landing page from any route that shares this header.
 * They are the ids the sections and the footer already use.
 *
 * What fits where: Log in and Start free always; Market reports and Pricing
 * from `sm`; Property reports and Lead capture from `lg`. All six beside the
 * logo need about 900px.
 *
 * `bare` drops the header's own ground so it can sit on the landing page's
 * tinted hero band, above the dotted field (hence `relative`). Every other
 * route mounts it without the prop and gets the header it had.
 */
import { Logo } from "@/components/logo"

const link = "text-[15px] font-medium text-[#334155] hover:text-[#0F172A]"

export function SiteNav({ bare = false }: { bare?: boolean }) {
  return (
    <nav className={`relative border-b border-[#ECEAE3] ${bare ? "" : "bg-[#FAFAF7]"}`}>
      <div className="mx-auto flex max-w-[1200px] items-center justify-between gap-6 px-4 py-[18px] md:px-8">
        <a href="/">
          <Logo className="h-7" />
        </a>
        <div className="flex items-center gap-5 md:gap-7">
          <a href="/#reports" className={`hidden whitespace-nowrap sm:inline ${link}`}>
            Market reports
          </a>
          <a href="/#property-reports" className={`hidden whitespace-nowrap lg:inline ${link}`}>
            Property reports
          </a>
          <a href="/#lead-capture" className={`hidden whitespace-nowrap lg:inline ${link}`}>
            Lead capture
          </a>
          <a href="/#pricing" className={`hidden sm:inline ${link}`}>
            Pricing
          </a>
          <a href="/login" className={`whitespace-nowrap ${link}`}>
            Log in
          </a>
          <a
            href="/register"
            className="inline-flex h-10 items-center whitespace-nowrap rounded-lg bg-[#0F172A] px-[18px] text-[15px] font-semibold text-white transition-colors hover:bg-[#1E293B]"
          >
            Start free
          </a>
        </div>
      </div>
    </nav>
  );
}

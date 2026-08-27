/**
 * Site-wide footer. Same rationale as site-nav.tsx.
 *
 * Anchors are root-relative so they work off the landing page. All three
 * (#how-it-works, #pricing, #faq) were verified to have matching section IDs
 * on the landing page — see how-it-works.tsx:385, pricing.tsx:59, faq.tsx:51.
 *
 * Every remaining entry resolves to a real page or a real section. There are
 * no mailto links left in the navigation columns (M4-T1, M4-T2):
 *
 * - "For Title Companies" was `mailto:sales@trendyreports.io`, sitting in a
 *   list of page links, and `/for-title-companies` does not exist. A nav entry
 *   that silently opens a blank email client is a dead end that looks like a
 *   destination; a missing link is better. The page is M6, gated on G4 —
 *   restore this entry when the route exists.
 * - Support is now one labelled contact line showing the actual address,
 *   instead of a nav-styled "Contact Us" that hid a mailto. The reader can see
 *   where it goes, copy it, or use it in whatever client they actually use.
 */
export function SiteFooter() {
  return (
    <footer className="bg-[#0F172A] px-6 py-24 text-[#94A3B8]">
      <div className="mx-auto max-w-7xl">
        <div className="grid gap-12 md:grid-cols-4">
          {/* Brand */}
          <div className="md:col-span-1">
            <img src="/white.png" alt="TrendyReports" className="h-7 w-auto" />
            <p className="mt-3 text-sm leading-relaxed">
              Turn MLS data into beautiful market reports.
            </p>
          </div>

          {/* Product */}
          <div>
            <p className="text-xs font-semibold uppercase tracking-wider text-white">
              Product
            </p>
            <ul className="mt-4 space-y-3">
              <li>
                <a href="/#how-it-works" className="text-sm transition-colors hover:text-white">
                  For Agents
                </a>
              </li>
              <li>
                <a href="/#pricing" className="text-sm transition-colors hover:text-white">
                  Pricing
                </a>
              </li>
            </ul>
          </div>

          {/* Support */}
          <div>
            <p className="text-xs font-semibold uppercase tracking-wider text-white">
              Support
            </p>
            <ul className="mt-4 space-y-3">
              <li>
                <a href="/#faq" className="text-sm transition-colors hover:text-white">
                  FAQ
                </a>
              </li>
            </ul>
            <p className="mt-4 text-sm">
              Email us at{" "}
              <a
                href="mailto:support@trendyreports.io"
                className="text-white underline underline-offset-2 transition-colors hover:text-[#818CF8]"
              >
                support@trendyreports.io
              </a>
            </p>
          </div>

          {/* Legal */}
          <div>
            <p className="text-xs font-semibold uppercase tracking-wider text-white">
              Legal
            </p>
            <ul className="mt-4 space-y-3">
              <li>
                <a href="/privacy" className="text-sm transition-colors hover:text-white">
                  Privacy Policy
                </a>
              </li>
              <li>
                <a href="/terms" className="text-sm transition-colors hover:text-white">
                  Terms of Service
                </a>
              </li>
            </ul>
          </div>
        </div>

        <div className="mt-16 border-t border-white/10 pt-10 text-center text-sm">
          {"\u00A9 2026 TrendyReports. All rights reserved."}
        </div>
      </div>
    </footer>
  );
}

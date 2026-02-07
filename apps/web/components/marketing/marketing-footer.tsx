import Link from "next/link"

export function MarketingFooter() {
  return (
    <footer className="bg-[#0F172A] px-6 py-24 text-[#94A3B8]">
      <div className="mx-auto max-w-7xl">
        <div className="grid gap-12 md:grid-cols-4">
          {/* Brand */}
          <div className="md:col-span-1">
            <p className="text-lg font-bold text-white">TrendyReports</p>
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
                <a href="#how-it-works" className="text-sm transition-colors hover:text-white">
                  For Agents
                </a>
              </li>
              <li>
                <a href="mailto:sales@trendyreports.com" className="text-sm transition-colors hover:text-white">
                  For Affiliates
                </a>
              </li>
              <li>
                <a href="#pricing" className="text-sm transition-colors hover:text-white">
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
                <a href="mailto:support@trendyreports.com" className="text-sm transition-colors hover:text-white">
                  Contact Us
                </a>
              </li>
            </ul>
          </div>

          {/* Legal */}
          <div>
            <p className="text-xs font-semibold uppercase tracking-wider text-white">
              Legal
            </p>
            <ul className="mt-4 space-y-3">
              <li>
                <Link href="/privacy" className="text-sm transition-colors hover:text-white">
                  Privacy Policy
                </Link>
              </li>
              <li>
                <Link href="/terms" className="text-sm transition-colors hover:text-white">
                  Terms of Service
                </Link>
              </li>
            </ul>
          </div>
        </div>

        <div className="mt-16 border-t border-white/10 pt-10 text-center text-sm">
          {`\u00A9 ${new Date().getFullYear()} TrendyReports. All rights reserved.`}
        </div>
      </div>
    </footer>
  )
}

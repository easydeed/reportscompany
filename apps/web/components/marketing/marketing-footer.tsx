import Link from "next/link"
import { Logo } from "@/components/logo"

export function MarketingFooter() {
  return (
    <footer className="border-t border-slate-200 bg-white">
      <div className="max-w-6xl mx-auto px-4 sm:px-6 lg:px-8 py-16">
        <div className="grid grid-cols-1 md:grid-cols-4 gap-12 mb-12">
          {/* Brand */}
          <div className="md:col-span-1">
            <Logo variant="full" className="h-8 mb-4" />
            <p className="text-sm text-slate-500 leading-relaxed">
              Turn MLS data into beautiful market reports.
            </p>
          </div>

          {/* Product */}
          <div>
            <h3 className="text-sm font-semibold text-slate-900 mb-4">
              Product
            </h3>
            <ul className="space-y-3 text-sm">
              <li>
                <Link
                  href="#how-it-works"
                  className="text-slate-500 hover:text-slate-900 transition-colors"
                >
                  For Agents
                </Link>
              </li>
              <li>
                <a
                  href="mailto:sales@trendyreports.com"
                  className="text-slate-500 hover:text-slate-900 transition-colors"
                >
                  For Affiliates
                </a>
              </li>
              <li>
                <Link
                  href="#pricing"
                  className="text-slate-500 hover:text-slate-900 transition-colors"
                >
                  Pricing
                </Link>
              </li>
            </ul>
          </div>

          {/* Support */}
          <div>
            <h3 className="text-sm font-semibold text-slate-900 mb-4">
              Support
            </h3>
            <ul className="space-y-3 text-sm">
              <li>
                <a
                  href="mailto:support@trendyreports.com"
                  className="text-slate-500 hover:text-slate-900 transition-colors"
                >
                  Contact Us
                </a>
              </li>
            </ul>
          </div>

          {/* Legal */}
          <div>
            <h3 className="text-sm font-semibold text-slate-900 mb-4">
              Legal
            </h3>
            <ul className="space-y-3 text-sm">
              <li>
                <Link
                  href="/privacy"
                  className="text-slate-500 hover:text-slate-900 transition-colors"
                >
                  Privacy Policy
                </Link>
              </li>
              <li>
                <Link
                  href="/terms"
                  className="text-slate-500 hover:text-slate-900 transition-colors"
                >
                  Terms of Service
                </Link>
              </li>
            </ul>
          </div>
        </div>

        {/* Bottom */}
        <div className="pt-8 border-t border-slate-200">
          <p className="text-sm text-slate-400">
            © {new Date().getFullYear()} TrendyReports. All rights reserved.
          </p>
        </div>
      </div>
    </footer>
  )
}

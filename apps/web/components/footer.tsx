import Link from "next/link"
import { MapPin, Mail, Phone } from 'lucide-react'
import { Logo } from "@/components/logo"

export function Footer() {
  return (
    <footer className="border-t border-slate-200 bg-slate-50">
      <div className="max-w-[1200px] mx-auto px-4 sm:px-6 lg:px-8 py-16">
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-5 gap-12 mb-12">
          {/* Brand Column */}
          <div className="lg:col-span-2">
            <div className="mb-4">
              <Logo variant="full" className="h-10" />
            </div>
            <p className="text-slate-600 mb-6 leading-relaxed max-w-sm">
              Turn raw MLS data into beautiful, branded market reports in minutes. Agents love it. Title teams scale
              it.
            </p>
            <div className="space-y-3 text-sm text-slate-600">
              <div className="flex items-start gap-2">
                <MapPin className="w-4 h-4 mt-0.5 text-purple-600 shrink-0" />
                <span>123 Market Street, San Francisco, CA 94103</span>
              </div>
              <div className="flex items-center gap-2">
                <Mail className="w-4 h-4 text-purple-600 shrink-0" />
                <a href="mailto:hello@trendyreports.com" className="hover:text-purple-600 transition-colors">
                  hello@trendyreports.com
                </a>
              </div>
              <div className="flex items-center gap-2">
                <Phone className="w-4 h-4 text-purple-600 shrink-0" />
                <a href="tel:+14155551234" className="hover:text-purple-600 transition-colors">
                  (415) 555-1234
                </a>
              </div>
            </div>
          </div>

          {/* Product Column */}
          <div>
            <h3 className="font-display font-semibold text-slate-900 mb-4">Product</h3>
            <ul className="space-y-3 text-sm">
              <li>
                <Link href="#for-agents" className="text-slate-600 hover:text-purple-600 transition-colors">
                  For Agents
                </Link>
              </li>
              <li>
                <Link href="#for-affiliates" className="text-slate-600 hover:text-purple-600 transition-colors">
                  For Affiliates
                </Link>
              </li>
              <li>
                <Link href="#sample-report" className="text-slate-600 hover:text-purple-600 transition-colors">
                  Sample Reports
                </Link>
              </li>
              <li>
                <Link href="#pricing" className="text-slate-600 hover:text-purple-600 transition-colors">
                  Pricing
                </Link>
              </li>
              <li>
                <Link href="/docs" className="text-slate-600 hover:text-purple-600 transition-colors">
                  API Docs
                </Link>
              </li>
            </ul>
          </div>

          {/* Company Column */}
          <div>
            <h3 className="font-display font-semibold text-slate-900 mb-4">Company</h3>
            <ul className="space-y-3 text-sm">
              <li>
                <Link href="/about" className="text-slate-600 hover:text-purple-600 transition-colors">
                  About Us
                </Link>
              </li>
              <li>
                <Link href="/careers" className="text-slate-600 hover:text-purple-600 transition-colors">
                  Careers
                </Link>
              </li>
              <li>
                <Link href="/blog" className="text-slate-600 hover:text-purple-600 transition-colors">
                  Blog
                </Link>
              </li>
              <li>
                <a
                  href="mailto:partners@trendyreports.com"
                  className="text-slate-600 hover:text-purple-600 transition-colors"
                >
                  Partners
                </a>
              </li>
              <li>
                <a href="mailto:press@trendyreports.com" className="text-slate-600 hover:text-purple-600 transition-colors">
                  Press
                </a>
              </li>
            </ul>
          </div>

          {/* Support Column */}
          <div>
            <h3 className="font-display font-semibold text-slate-900 mb-4">Support</h3>
            <ul className="space-y-3 text-sm">
              <li>
                <Link href="/help" className="text-slate-600 hover:text-purple-600 transition-colors">
                  Help Center
                </Link>
              </li>
              <li>
                <a href="mailto:support@trendyreports.com" className="text-slate-600 hover:text-purple-600 transition-colors">
                  Contact Support
                </a>
              </li>
              <li>
                <Link href="/status" className="text-slate-600 hover:text-purple-600 transition-colors">
                  System Status
                </Link>
              </li>
              <li>
                <Link href="/privacy" className="text-slate-600 hover:text-purple-600 transition-colors">
                  Privacy Policy
                </Link>
              </li>
              <li>
                <Link href="/terms" className="text-slate-600 hover:text-purple-600 transition-colors">
                  Terms of Service
                </Link>
              </li>
            </ul>
          </div>
        </div>

        {/* Bottom Bar */}
        <div className="pt-8 border-t border-slate-200 flex flex-col md:flex-row justify-between items-center gap-4">
          <p className="text-sm text-slate-600">© 2025 TrendyReports. All rights reserved.</p>
          <div className="flex items-center gap-6 text-sm text-slate-600">
            <Link href="/security" className="hover:text-purple-600 transition-colors">
              Security
            </Link>
            <Link href="/privacy" className="hover:text-purple-600 transition-colors">
              Privacy
            </Link>
            <Link href="/terms" className="hover:text-purple-600 transition-colors">
              Terms
            </Link>
          </div>
        </div>
      </div>
    </footer>
  )
}


import { Navbar } from "@/components/navbar"
import { Footer } from "@/components/footer"
import { Building2, Users, Target, Heart, Zap, Shield } from "lucide-react"

export const metadata = {
  title: "About Us | TrendyReports",
  description: "Learn about TrendyReports - the team behind the automated market report platform trusted by real estate professionals.",
}

export default function AboutPage() {
  return (
    <div className="min-h-screen bg-white">
      <Navbar />

      {/* Hero */}
      <section className="pt-32 pb-16 px-4 sm:px-6 lg:px-8">
        <div className="max-w-[800px] mx-auto text-center">
          <h1 className="font-display font-semibold text-4xl sm:text-5xl text-slate-900 mb-6">
            We believe agents should spend time with clients, not spreadsheets
          </h1>
          <p className="text-xl text-slate-600 leading-relaxed">
            TrendyReports was founded to solve a simple problem: real estate professionals were spending
            hours every week creating market reports manually. We built a better way.
          </p>
        </div>
      </section>

      {/* Story Section */}
      <section className="py-16 px-4 sm:px-6 lg:px-8 bg-slate-50">
        <div className="max-w-[1000px] mx-auto">
          <div className="grid md:grid-cols-2 gap-12 items-center">
            <div>
              <h2 className="font-display font-semibold text-3xl text-slate-900 mb-6">Our Story</h2>
              <div className="space-y-4 text-slate-600 leading-relaxed">
                <p>
                  In 2023, our founders noticed something troubling: top-producing real estate agents were
                  spending 3-5 hours every week pulling MLS data, creating charts, and formatting market
                  reports. Time that could be spent building client relationships and closing deals.
                </p>
                <p>
                  We asked: what if generating a beautiful, branded market report took 30 seconds instead
                  of 3 hours? What if it could be automated entirely?
                </p>
                <p>
                  TrendyReports was born from that question. Today, we help over 1,200 real estate
                  professionals reclaim their time while delivering better market intelligence to their clients.
                </p>
              </div>
            </div>
            <div className="bg-gradient-to-br from-purple-600 to-purple-800 rounded-2xl p-8 text-white">
              <div className="grid grid-cols-2 gap-8">
                <div>
                  <div className="text-4xl font-display font-bold mb-2">1,200+</div>
                  <div className="text-purple-200">Active Users</div>
                </div>
                <div>
                  <div className="text-4xl font-display font-bold mb-2">50K+</div>
                  <div className="text-purple-200">Reports Generated</div>
                </div>
                <div>
                  <div className="text-4xl font-display font-bold mb-2">3hrs</div>
                  <div className="text-purple-200">Saved Weekly/User</div>
                </div>
                <div>
                  <div className="text-4xl font-display font-bold mb-2">99.9%</div>
                  <div className="text-purple-200">Uptime</div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* Mission */}
      <section className="py-16 px-4 sm:px-6 lg:px-8">
        <div className="max-w-[1000px] mx-auto">
          <div className="text-center mb-12">
            <h2 className="font-display font-semibold text-3xl text-slate-900 mb-4">Our Mission</h2>
            <p className="text-xl text-slate-600 max-w-2xl mx-auto">
              Empower real estate professionals with automated market intelligence so they can focus
              on what matters most: their clients.
            </p>
          </div>

          <div className="grid md:grid-cols-3 gap-8">
            <div className="text-center">
              <div className="w-14 h-14 bg-purple-100 rounded-xl flex items-center justify-center mx-auto mb-4">
                <Zap className="w-7 h-7 text-purple-600" />
              </div>
              <h3 className="font-display font-semibold text-lg text-slate-900 mb-2">Speed</h3>
              <p className="text-slate-600">
                What used to take hours now takes seconds. Time is your most valuable asset.
              </p>
            </div>
            <div className="text-center">
              <div className="w-14 h-14 bg-purple-100 rounded-xl flex items-center justify-center mx-auto mb-4">
                <Target className="w-7 h-7 text-purple-600" />
              </div>
              <h3 className="font-display font-semibold text-lg text-slate-900 mb-2">Quality</h3>
              <p className="text-slate-600">
                Beautiful, professional reports that make you look like a market expert.
              </p>
            </div>
            <div className="text-center">
              <div className="w-14 h-14 bg-purple-100 rounded-xl flex items-center justify-center mx-auto mb-4">
                <Heart className="w-7 h-7 text-purple-600" />
              </div>
              <h3 className="font-display font-semibold text-lg text-slate-900 mb-2">Simplicity</h3>
              <p className="text-slate-600">
                No training needed. If you can click a button, you can create stunning reports.
              </p>
            </div>
          </div>
        </div>
      </section>

      {/* Values */}
      <section className="py-16 px-4 sm:px-6 lg:px-8 bg-slate-50">
        <div className="max-w-[1000px] mx-auto">
          <h2 className="font-display font-semibold text-3xl text-slate-900 mb-12 text-center">Our Values</h2>

          <div className="grid md:grid-cols-2 gap-8">
            <div className="bg-white rounded-xl p-6 border border-slate-200">
              <div className="flex items-start gap-4">
                <div className="w-10 h-10 bg-purple-100 rounded-lg flex items-center justify-center shrink-0">
                  <Users className="w-5 h-5 text-purple-600" />
                </div>
                <div>
                  <h3 className="font-display font-semibold text-lg text-slate-900 mb-2">Customer First</h3>
                  <p className="text-slate-600">
                    Every feature we build starts with a real customer problem. We listen, we learn, we ship.
                  </p>
                </div>
              </div>
            </div>
            <div className="bg-white rounded-xl p-6 border border-slate-200">
              <div className="flex items-start gap-4">
                <div className="w-10 h-10 bg-purple-100 rounded-lg flex items-center justify-center shrink-0">
                  <Shield className="w-5 h-5 text-purple-600" />
                </div>
                <div>
                  <h3 className="font-display font-semibold text-lg text-slate-900 mb-2">Trust & Security</h3>
                  <p className="text-slate-600">
                    Your data is sacred. We use enterprise-grade security and never share your information.
                  </p>
                </div>
              </div>
            </div>
            <div className="bg-white rounded-xl p-6 border border-slate-200">
              <div className="flex items-start gap-4">
                <div className="w-10 h-10 bg-purple-100 rounded-lg flex items-center justify-center shrink-0">
                  <Zap className="w-5 h-5 text-purple-600" />
                </div>
                <div>
                  <h3 className="font-display font-semibold text-lg text-slate-900 mb-2">Continuous Improvement</h3>
                  <p className="text-slate-600">
                    We ship updates weekly. Your feedback directly shapes our roadmap.
                  </p>
                </div>
              </div>
            </div>
            <div className="bg-white rounded-xl p-6 border border-slate-200">
              <div className="flex items-start gap-4">
                <div className="w-10 h-10 bg-purple-100 rounded-lg flex items-center justify-center shrink-0">
                  <Building2 className="w-5 h-5 text-purple-600" />
                </div>
                <div>
                  <h3 className="font-display font-semibold text-lg text-slate-900 mb-2">Industry Expertise</h3>
                  <p className="text-slate-600">
                    Built by real estate technology veterans who understand your business.
                  </p>
                </div>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* CTA */}
      <section className="py-16 px-4 sm:px-6 lg:px-8">
        <div className="max-w-[800px] mx-auto text-center">
          <h2 className="font-display font-semibold text-3xl text-slate-900 mb-4">
            Ready to reclaim your time?
          </h2>
          <p className="text-xl text-slate-600 mb-8">
            Join 1,200+ real estate professionals who have automated their market reports.
          </p>
          <a
            href="/login"
            className="inline-flex items-center justify-center bg-gradient-to-r from-purple-600 to-purple-700 hover:from-purple-700 hover:to-purple-800 text-white text-lg px-8 h-14 rounded-lg shadow-lg hover:shadow-xl transition-all font-medium"
          >
            Start Your Free Trial
          </a>
        </div>
      </section>

      <Footer />
    </div>
  )
}

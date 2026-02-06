import { Navbar } from "@/components/navbar"
import { Footer } from "@/components/footer"
import { MapPin, Clock, DollarSign, Heart, Zap, Users, ArrowRight } from "lucide-react"
import Link from "next/link"

export const metadata = {
  title: "Careers | TrendyReports",
  description: "Join the TrendyReports team. We're building the future of real estate market intelligence.",
}

const openPositions = [
  {
    title: "Senior Full-Stack Engineer",
    department: "Engineering",
    location: "Remote (US)",
    type: "Full-time",
    description: "Build and scale our report generation platform using Next.js, Python, and PostgreSQL.",
  },
  {
    title: "Product Designer",
    department: "Design",
    location: "Remote (US)",
    type: "Full-time",
    description: "Design beautiful, intuitive experiences for real estate professionals.",
  },
  {
    title: "Customer Success Manager",
    department: "Customer Success",
    location: "Remote (US)",
    type: "Full-time",
    description: "Help our customers get maximum value from TrendyReports.",
  },
  {
    title: "Sales Development Representative",
    department: "Sales",
    location: "Remote (US)",
    type: "Full-time",
    description: "Connect with title companies and brokerages to grow our affiliate network.",
  },
]

const benefits = [
  {
    icon: DollarSign,
    title: "Competitive Compensation",
    description: "Salary + equity that reflects your impact",
  },
  {
    icon: Heart,
    title: "Health & Wellness",
    description: "Medical, dental, vision, and mental health support",
  },
  {
    icon: Clock,
    title: "Flexible Schedule",
    description: "Work when you're most productive",
  },
  {
    icon: MapPin,
    title: "Remote First",
    description: "Work from anywhere in the US",
  },
  {
    icon: Zap,
    title: "Learning Budget",
    description: "$1,500/year for courses, books, and conferences",
  },
  {
    icon: Users,
    title: "Team Retreats",
    description: "Annual in-person gatherings to connect",
  },
]

export default function CareersPage() {
  return (
    <div className="min-h-screen bg-white">
      <Navbar />

      {/* Hero */}
      <section className="pt-32 pb-16 px-4 sm:px-6 lg:px-8">
        <div className="max-w-[800px] mx-auto text-center">
          <h1 className="font-display font-semibold text-4xl sm:text-5xl text-slate-900 mb-6">
            Build the future of real estate technology
          </h1>
          <p className="text-xl text-slate-600 leading-relaxed">
            We're a small, mighty team solving big problems for real estate professionals.
            Join us and make a real impact.
          </p>
        </div>
      </section>

      {/* Why Join */}
      <section className="py-16 px-4 sm:px-6 lg:px-8 bg-slate-50">
        <div className="max-w-[1000px] mx-auto">
          <h2 className="font-display font-semibold text-3xl text-slate-900 mb-12 text-center">
            Why TrendyReports?
          </h2>

          <div className="grid md:grid-cols-3 gap-8">
            <div className="bg-white rounded-xl p-6 border border-slate-200">
              <h3 className="font-display font-semibold text-lg text-slate-900 mb-3">Real Impact</h3>
              <p className="text-slate-600">
                Every feature you build directly helps thousands of real estate professionals
                work smarter. You'll see the impact of your work immediately.
              </p>
            </div>
            <div className="bg-white rounded-xl p-6 border border-slate-200">
              <h3 className="font-display font-semibold text-lg text-slate-900 mb-3">Growth Stage</h3>
              <p className="text-slate-600">
                We're past product-market fit but still small enough that you'll shape the
                company culture and have ownership over major initiatives.
              </p>
            </div>
            <div className="bg-white rounded-xl p-6 border border-slate-200">
              <h3 className="font-display font-semibold text-lg text-slate-900 mb-3">Great Team</h3>
              <p className="text-slate-600">
                Work with experienced, kind, talented people who care deeply about building
                excellent products and supporting each other.
              </p>
            </div>
          </div>
        </div>
      </section>

      {/* Benefits */}
      <section className="py-16 px-4 sm:px-6 lg:px-8">
        <div className="max-w-[1000px] mx-auto">
          <h2 className="font-display font-semibold text-3xl text-slate-900 mb-12 text-center">
            Benefits & Perks
          </h2>

          <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-6">
            {benefits.map((benefit) => (
              <div key={benefit.title} className="flex items-start gap-4">
                <div className="w-10 h-10 bg-indigo-100 rounded-lg flex items-center justify-center shrink-0">
                  <benefit.icon className="w-5 h-5 text-indigo-600" />
                </div>
                <div>
                  <h3 className="font-semibold text-slate-900 mb-1">{benefit.title}</h3>
                  <p className="text-sm text-slate-600">{benefit.description}</p>
                </div>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Open Positions */}
      <section className="py-16 px-4 sm:px-6 lg:px-8 bg-slate-50">
        <div className="max-w-[1000px] mx-auto">
          <h2 className="font-display font-semibold text-3xl text-slate-900 mb-4 text-center">
            Open Positions
          </h2>
          <p className="text-slate-600 text-center mb-12">
            Don't see a perfect fit? Email us at{" "}
            <a href="mailto:careers@trendyreports.com" className="text-indigo-600 hover:underline">
              careers@trendyreports.com
            </a>
          </p>

          <div className="space-y-4">
            {openPositions.map((position) => (
              <a
                key={position.title}
                href={`mailto:careers@trendyreports.com?subject=Application: ${position.title}`}
                className="block bg-white rounded-xl p-6 border border-slate-200 hover:border-indigo-300 hover:shadow-md transition-all group"
              >
                <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
                  <div>
                    <h3 className="font-display font-semibold text-lg text-slate-900 mb-1 group-hover:text-indigo-600 transition-colors">
                      {position.title}
                    </h3>
                    <p className="text-slate-600 text-sm mb-2">{position.description}</p>
                    <div className="flex flex-wrap items-center gap-3 text-sm text-slate-500">
                      <span className="bg-slate-100 px-2 py-1 rounded">{position.department}</span>
                      <span className="flex items-center gap-1">
                        <MapPin className="w-3 h-3" />
                        {position.location}
                      </span>
                      <span className="flex items-center gap-1">
                        <Clock className="w-3 h-3" />
                        {position.type}
                      </span>
                    </div>
                  </div>
                  <ArrowRight className="w-5 h-5 text-slate-400 group-hover:text-indigo-600 transition-colors shrink-0" />
                </div>
              </a>
            ))}
          </div>
        </div>
      </section>

      {/* CTA */}
      <section className="py-16 px-4 sm:px-6 lg:px-8">
        <div className="max-w-[800px] mx-auto text-center">
          <h2 className="font-display font-semibold text-3xl text-slate-900 mb-4">
            Not ready to apply?
          </h2>
          <p className="text-xl text-slate-600 mb-8">
            Follow us on LinkedIn to stay updated on new openings and company news.
          </p>
          <a
            href="https://linkedin.com/company/trendyreports"
            target="_blank"
            rel="noopener noreferrer"
            className="inline-flex items-center justify-center border border-slate-300 hover:border-indigo-300 hover:bg-indigo-50 text-slate-700 text-lg px-8 h-14 rounded-lg transition-all font-medium"
          >
            Follow on LinkedIn
          </a>
        </div>
      </section>

      <Footer />
    </div>
  )
}

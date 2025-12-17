import { Navbar } from "@/components/navbar"
import { Footer } from "@/components/footer"
import { Search, FileText, Calendar, Users, Settings, Mail, ChevronRight, MessageCircle, Video, Book } from "lucide-react"
import Link from "next/link"

export const metadata = {
  title: "Help Center | TrendyReports",
  description: "Get help with TrendyReports. Find answers, tutorials, and contact support.",
}

const categories = [
  {
    icon: FileText,
    title: "Creating Reports",
    description: "Learn how to generate beautiful market reports",
    articles: [
      "How to create your first market report",
      "Choosing the right report type",
      "Customizing report branding",
      "Understanding report data sources",
    ],
  },
  {
    icon: Calendar,
    title: "Scheduling & Automation",
    description: "Set up automated report delivery",
    articles: [
      "Setting up scheduled reports",
      "Managing delivery schedules",
      "Adding recipients to schedules",
      "Troubleshooting delivery issues",
    ],
  },
  {
    icon: Users,
    title: "Account & Billing",
    description: "Manage your account and subscription",
    articles: [
      "Updating your account information",
      "Changing your subscription plan",
      "Understanding your invoice",
      "Canceling your subscription",
    ],
  },
  {
    icon: Settings,
    title: "Settings & Customization",
    description: "Configure TrendyReports to fit your needs",
    articles: [
      "Uploading your logo and branding",
      "Setting default report preferences",
      "Managing notification settings",
      "Integrating with your CRM",
    ],
  },
]

const popularArticles = [
  {
    title: "Getting Started with TrendyReports",
    views: "12,543 views",
  },
  {
    title: "How to Add Your Logo to Reports",
    views: "8,921 views",
  },
  {
    title: "Setting Up Weekly Scheduled Reports",
    views: "7,234 views",
  },
  {
    title: "Understanding MLS Data in Reports",
    views: "5,678 views",
  },
  {
    title: "Sharing Reports with Clients",
    views: "4,892 views",
  },
]

export default function HelpPage() {
  return (
    <div className="min-h-screen bg-white">
      <Navbar />

      {/* Hero with Search */}
      <section className="pt-32 pb-16 px-4 sm:px-6 lg:px-8 bg-gradient-to-b from-purple-50 to-white">
        <div className="max-w-[800px] mx-auto text-center">
          <h1 className="font-display font-semibold text-4xl sm:text-5xl text-slate-900 mb-6">
            How can we help?
          </h1>
          <div className="relative max-w-xl mx-auto">
            <Search className="absolute left-4 top-1/2 -translate-y-1/2 w-5 h-5 text-slate-400" />
            <input
              type="text"
              placeholder="Search for answers..."
              className="w-full pl-12 pr-4 py-4 rounded-xl border border-slate-300 focus:border-purple-500 focus:ring-2 focus:ring-purple-200 outline-none transition-all text-lg"
            />
          </div>
        </div>
      </section>

      {/* Quick Actions */}
      <section className="py-12 px-4 sm:px-6 lg:px-8">
        <div className="max-w-[1000px] mx-auto">
          <div className="grid md:grid-cols-3 gap-6">
            <a
              href="mailto:support@trendyreports.com"
              className="flex items-center gap-4 p-6 bg-white rounded-xl border border-slate-200 hover:border-purple-300 hover:shadow-md transition-all group"
            >
              <div className="w-12 h-12 bg-purple-100 rounded-xl flex items-center justify-center shrink-0">
                <MessageCircle className="w-6 h-6 text-purple-600" />
              </div>
              <div>
                <h3 className="font-semibold text-slate-900 group-hover:text-purple-600 transition-colors">
                  Contact Support
                </h3>
                <p className="text-sm text-slate-600">Get help from our team</p>
              </div>
            </a>
            <a
              href="#"
              className="flex items-center gap-4 p-6 bg-white rounded-xl border border-slate-200 hover:border-purple-300 hover:shadow-md transition-all group"
            >
              <div className="w-12 h-12 bg-purple-100 rounded-xl flex items-center justify-center shrink-0">
                <Video className="w-6 h-6 text-purple-600" />
              </div>
              <div>
                <h3 className="font-semibold text-slate-900 group-hover:text-purple-600 transition-colors">
                  Video Tutorials
                </h3>
                <p className="text-sm text-slate-600">Watch step-by-step guides</p>
              </div>
            </a>
            <a
              href="/docs"
              className="flex items-center gap-4 p-6 bg-white rounded-xl border border-slate-200 hover:border-purple-300 hover:shadow-md transition-all group"
            >
              <div className="w-12 h-12 bg-purple-100 rounded-xl flex items-center justify-center shrink-0">
                <Book className="w-6 h-6 text-purple-600" />
              </div>
              <div>
                <h3 className="font-semibold text-slate-900 group-hover:text-purple-600 transition-colors">
                  API Documentation
                </h3>
                <p className="text-sm text-slate-600">For developers</p>
              </div>
            </a>
          </div>
        </div>
      </section>

      {/* Categories */}
      <section className="py-12 px-4 sm:px-6 lg:px-8 bg-slate-50">
        <div className="max-w-[1000px] mx-auto">
          <h2 className="font-display font-semibold text-2xl text-slate-900 mb-8 text-center">
            Browse by Category
          </h2>

          <div className="grid md:grid-cols-2 gap-6">
            {categories.map((category) => (
              <div
                key={category.title}
                className="bg-white rounded-xl border border-slate-200 overflow-hidden"
              >
                <div className="p-6 border-b border-slate-100">
                  <div className="flex items-center gap-3 mb-2">
                    <div className="w-10 h-10 bg-purple-100 rounded-lg flex items-center justify-center">
                      <category.icon className="w-5 h-5 text-purple-600" />
                    </div>
                    <div>
                      <h3 className="font-display font-semibold text-lg text-slate-900">
                        {category.title}
                      </h3>
                      <p className="text-sm text-slate-600">{category.description}</p>
                    </div>
                  </div>
                </div>
                <div className="divide-y divide-slate-100">
                  {category.articles.map((article) => (
                    <a
                      key={article}
                      href="#"
                      className="flex items-center justify-between px-6 py-3 hover:bg-slate-50 transition-colors group"
                    >
                      <span className="text-slate-700 group-hover:text-purple-600 transition-colors">
                        {article}
                      </span>
                      <ChevronRight className="w-4 h-4 text-slate-400 group-hover:text-purple-600 transition-colors" />
                    </a>
                  ))}
                </div>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Popular Articles */}
      <section className="py-12 px-4 sm:px-6 lg:px-8">
        <div className="max-w-[800px] mx-auto">
          <h2 className="font-display font-semibold text-2xl text-slate-900 mb-8 text-center">
            Popular Articles
          </h2>

          <div className="space-y-3">
            {popularArticles.map((article, index) => (
              <a
                key={article.title}
                href="#"
                className="flex items-center justify-between p-4 bg-white rounded-xl border border-slate-200 hover:border-purple-300 hover:shadow-md transition-all group"
              >
                <div className="flex items-center gap-4">
                  <span className="w-8 h-8 bg-slate-100 rounded-full flex items-center justify-center text-sm font-medium text-slate-600">
                    {index + 1}
                  </span>
                  <span className="font-medium text-slate-900 group-hover:text-purple-600 transition-colors">
                    {article.title}
                  </span>
                </div>
                <span className="text-sm text-slate-500">{article.views}</span>
              </a>
            ))}
          </div>
        </div>
      </section>

      {/* Still Need Help */}
      <section className="py-16 px-4 sm:px-6 lg:px-8 bg-slate-50">
        <div className="max-w-[600px] mx-auto text-center">
          <h2 className="font-display font-semibold text-2xl text-slate-900 mb-4">
            Still need help?
          </h2>
          <p className="text-slate-600 mb-6">
            Our support team typically responds within 2 hours during business hours.
          </p>
          <a
            href="mailto:support@trendyreports.com"
            className="inline-flex items-center justify-center bg-purple-600 hover:bg-purple-700 text-white font-medium px-6 py-3 rounded-lg transition-colors"
          >
            <Mail className="w-5 h-5 mr-2" />
            Contact Support
          </a>
        </div>
      </section>

      <Footer />
    </div>
  )
}

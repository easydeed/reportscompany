import { Navbar } from "@/components/navbar"
import { Footer } from "@/components/footer"
import { Calendar, Clock, ArrowRight, Tag } from "lucide-react"
import Link from "next/link"

export const metadata = {
  title: "Blog | TrendyReports",
  description: "Real estate market insights, product updates, and tips for growing your business.",
}

const featuredPost = {
  title: "How Top Agents Use Market Reports to Win More Listings",
  excerpt: "Discover the strategies that help top-producing agents leverage market data to stand out from the competition and win more listing presentations.",
  date: "December 15, 2025",
  readTime: "8 min read",
  category: "Strategy",
  slug: "top-agents-market-reports",
}

const posts = [
  {
    title: "Introducing Scheduled Reports: Set It and Forget It",
    excerpt: "Automate your weekly market updates with our new scheduling feature. Your clients will love the consistency.",
    date: "December 10, 2025",
    readTime: "4 min read",
    category: "Product",
    slug: "scheduled-reports-launch",
  },
  {
    title: "5 Market Trends Every Agent Should Watch in 2025",
    excerpt: "From inventory levels to mortgage rates, here are the key indicators that will shape the market next year.",
    date: "December 5, 2025",
    readTime: "6 min read",
    category: "Market Insights",
    slug: "market-trends-2025",
  },
  {
    title: "How Title Companies Are Using TrendyReports to Support Their Agents",
    excerpt: "Learn how forward-thinking title companies are adding value to their agent relationships with branded market reports.",
    date: "November 28, 2025",
    readTime: "5 min read",
    category: "Case Study",
    slug: "title-company-case-study",
  },
  {
    title: "The Complete Guide to Real Estate Market Reports",
    excerpt: "Everything you need to know about creating, distributing, and leveraging market reports for your business.",
    date: "November 20, 2025",
    readTime: "12 min read",
    category: "Guide",
    slug: "complete-guide-market-reports",
  },
  {
    title: "New Feature: Neighborhood Analysis Reports",
    excerpt: "Dive deeper into hyperlocal data with our new neighborhood-level market analysis reports.",
    date: "November 15, 2025",
    readTime: "3 min read",
    category: "Product",
    slug: "neighborhood-analysis-launch",
  },
  {
    title: "Why Your Farm Area Needs Consistent Market Updates",
    excerpt: "Building trust and staying top-of-mind with your farm area through regular market intelligence.",
    date: "November 8, 2025",
    readTime: "5 min read",
    category: "Strategy",
    slug: "farm-area-market-updates",
  },
]

const categories = ["All", "Product", "Strategy", "Market Insights", "Case Study", "Guide"]

export default function BlogPage() {
  return (
    <div className="min-h-screen bg-white">
      <Navbar />

      {/* Hero */}
      <section className="pt-32 pb-12 px-4 sm:px-6 lg:px-8">
        <div className="max-w-[1000px] mx-auto">
          <h1 className="font-display font-semibold text-4xl sm:text-5xl text-slate-900 mb-6 text-center">
            The TrendyReports Blog
          </h1>
          <p className="text-xl text-slate-600 text-center max-w-2xl mx-auto">
            Market insights, product updates, and strategies to help you grow your real estate business.
          </p>
        </div>
      </section>

      {/* Categories */}
      <section className="pb-8 px-4 sm:px-6 lg:px-8">
        <div className="max-w-[1000px] mx-auto">
          <div className="flex flex-wrap justify-center gap-2">
            {categories.map((category) => (
              <button
                key={category}
                className={`px-4 py-2 rounded-full text-sm font-medium transition-colors ${
                  category === "All"
                    ? "bg-indigo-600 text-white"
                    : "bg-slate-100 text-slate-600 hover:bg-slate-200"
                }`}
              >
                {category}
              </button>
            ))}
          </div>
        </div>
      </section>

      {/* Featured Post */}
      <section className="py-8 px-4 sm:px-6 lg:px-8">
        <div className="max-w-[1000px] mx-auto">
          <div className="bg-gradient-to-br from-indigo-600 to-indigo-800 rounded-2xl p-8 md:p-12 text-white">
            <div className="flex items-center gap-2 mb-4">
              <span className="bg-white/20 px-3 py-1 rounded-full text-sm font-medium">
                Featured
              </span>
              <span className="bg-white/20 px-3 py-1 rounded-full text-sm font-medium">
                {featuredPost.category}
              </span>
            </div>
            <h2 className="font-display font-semibold text-2xl md:text-3xl mb-4">
              {featuredPost.title}
            </h2>
            <p className="text-indigo-100 text-lg mb-6 max-w-2xl">
              {featuredPost.excerpt}
            </p>
            <div className="flex flex-wrap items-center justify-between gap-4">
              <div className="flex items-center gap-4 text-indigo-200 text-sm">
                <span className="flex items-center gap-1">
                  <Calendar className="w-4 h-4" />
                  {featuredPost.date}
                </span>
                <span className="flex items-center gap-1">
                  <Clock className="w-4 h-4" />
                  {featuredPost.readTime}
                </span>
              </div>
              <span className="inline-flex items-center gap-2 text-white font-medium hover:gap-3 transition-all cursor-pointer">
                Read Article
                <ArrowRight className="w-4 h-4" />
              </span>
            </div>
          </div>
        </div>
      </section>

      {/* Posts Grid */}
      <section className="py-12 px-4 sm:px-6 lg:px-8">
        <div className="max-w-[1000px] mx-auto">
          <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-8">
            {posts.map((post) => (
              <article
                key={post.slug}
                className="bg-white rounded-xl border border-slate-200 overflow-hidden hover:shadow-lg hover:border-indigo-200 transition-all group cursor-pointer"
              >
                <div className="aspect-[16/9] bg-gradient-to-br from-slate-100 to-slate-200" />
                <div className="p-6">
                  <div className="flex items-center gap-2 mb-3">
                    <span className="bg-indigo-100 text-indigo-700 px-2 py-1 rounded text-xs font-medium">
                      {post.category}
                    </span>
                  </div>
                  <h3 className="font-display font-semibold text-lg text-slate-900 mb-2 group-hover:text-indigo-600 transition-colors line-clamp-2">
                    {post.title}
                  </h3>
                  <p className="text-slate-600 text-sm mb-4 line-clamp-2">
                    {post.excerpt}
                  </p>
                  <div className="flex items-center gap-3 text-xs text-slate-500">
                    <span className="flex items-center gap-1">
                      <Calendar className="w-3 h-3" />
                      {post.date}
                    </span>
                    <span className="flex items-center gap-1">
                      <Clock className="w-3 h-3" />
                      {post.readTime}
                    </span>
                  </div>
                </div>
              </article>
            ))}
          </div>
        </div>
      </section>

      {/* Newsletter CTA */}
      <section className="py-16 px-4 sm:px-6 lg:px-8 bg-slate-50">
        <div className="max-w-[600px] mx-auto text-center">
          <h2 className="font-display font-semibold text-2xl text-slate-900 mb-4">
            Get market insights in your inbox
          </h2>
          <p className="text-slate-600 mb-6">
            Join 5,000+ real estate professionals who get our weekly newsletter with market
            trends, tips, and product updates.
          </p>
          <form className="flex flex-col sm:flex-row gap-3 max-w-md mx-auto">
            <input
              type="email"
              placeholder="you@example.com"
              className="flex-1 px-4 py-3 rounded-lg border border-slate-300 focus:border-indigo-500 focus:ring-2 focus:ring-indigo-200 outline-none transition-all"
            />
            <button
              type="submit"
              className="bg-indigo-600 hover:bg-indigo-700 text-white font-medium px-6 py-3 rounded-lg transition-colors"
            >
              Subscribe
            </button>
          </form>
          <p className="text-xs text-slate-500 mt-3">
            No spam. Unsubscribe anytime.
          </p>
        </div>
      </section>

      <Footer />
    </div>
  )
}

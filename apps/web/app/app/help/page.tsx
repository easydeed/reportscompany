"use client"

import { useState, useMemo } from "react"
import {
  Rocket,
  FileText,
  Calendar,
  Users,
  Target,
  Palette,
  CreditCard,
  Building2,
  HelpCircle,
  Search,
  ChevronDown,
  ChevronUp,
  UserPlus,
  Mail,
  ExternalLink,
} from "lucide-react"
import { Input } from "@/components/ui/input"
import { Button } from "@/components/ui/button"
import {
  Accordion,
  AccordionContent,
  AccordionItem,
  AccordionTrigger,
} from "@/components/ui/accordion"
import { PageHeader } from "@/components/page-header"
import { cn } from "@/lib/utils"

// ── Types ──────────────────────────────────────────────

interface Step {
  title: string
  body: string
  screenshot?: string
}

interface WorkflowGuide {
  type: "workflow"
  title: string
  description: string
  steps: Step[]
}

interface FAQItem {
  type: "faq"
  question: string
  answer: string
}

type Article = WorkflowGuide | FAQItem

interface Section {
  id: string
  name: string
  icon: React.ElementType
  articles: Article[]
}

// ── Content Data ───────────────────────────────────────

const sections: Section[] = [
  {
    id: "getting-started",
    name: "Getting Started",
    icon: Rocket,
    articles: [
      {
        type: "workflow",
        title: "Create Your First Report",
        description: "Generate a branded market report in under 2 minutes",
        steps: [
          {
            title: "Choose your market area",
            body: "Click \u2018New Report\u2019 from your dashboard. Enter a city, zip code, or neighborhood name. We\u2019ll pull the latest MLS data automatically.",
            screenshot: "Market area selector with search input",
          },
          {
            title: "Select a report type",
            body: "Choose from 8 report types: Market Snapshot, New Listings, Price Trends, Inventory Analysis, and more. Each type is optimized for different use cases.",
            screenshot: "Report type selection grid",
          },
          {
            title: "Preview and send",
            body: "Review your report, make any final tweaks, then send it to your contacts or download as PDF. Your branding is automatically applied.",
            screenshot: "Report preview with send options",
          },
        ],
      },
      {
        type: "faq",
        question: "How long does it take to set up my account?",
        answer:
          "Most users complete setup in under 2 minutes. Just upload your logo, choose your brand colors, and you\u2019re ready to create reports.",
      },
      {
        type: "faq",
        question: "Do I need any design skills?",
        answer:
          "No design skills required. Our templates are professionally designed and automatically apply your branding. Just pick a template and go.",
      },
    ],
  },
  {
    id: "creating-reports",
    name: "Creating Reports",
    icon: FileText,
    articles: [
      {
        type: "workflow",
        title: "Generate a Property Report",
        description: "Create a CMA-style report for listing presentations",
        steps: [
          {
            title: "Enter the property address",
            body: "Navigate to Property Reports and enter the subject property address. We\u2019ll pull property details, photos, and nearby comps automatically.",
            screenshot: "Property address input with auto-complete",
          },
          {
            title: "Select comparable sales",
            body: "Review the suggested comps or manually select up to 6 comparable properties. Adjust the search radius and filters as needed.",
            screenshot: "Comparable sales selection map",
          },
          {
            title: "Choose your template",
            body: "Pick from 5 designer templates: Bold, Classic, Elegant, Modern, or Teal. Each includes your branding, aerial maps, and a QR code for lead capture.",
            screenshot: "Template selection gallery",
          },
          {
            title: "Download or share",
            body: "Download as a print-ready PDF or share via a unique link. The built-in QR code links to a branded landing page that captures leads.",
            screenshot: "Export options with PDF and link sharing",
          },
        ],
      },
      {
        type: "workflow",
        title: "Customize Report Content",
        description: "Adjust data, add notes, and personalize your reports",
        steps: [
          {
            title: "Edit the header section",
            body: "Click on the header to customize the title, subtitle, and date range. You can also add a personal message to your clients.",
          },
          {
            title: "Adjust market metrics",
            body: "Toggle which metrics to display: median price, days on market, inventory levels, price per square foot, and more.",
          },
          {
            title: "Add agent notes",
            body: "Include a personalized market commentary section. This is where you can add your insights and recommendations.",
          },
        ],
      },
      {
        type: "faq",
        question: "What MLS data do you support?",
        answer:
          "We support over 600 MLS systems across the United States. Data is refreshed daily to ensure accuracy. Contact support if you need a specific MLS added.",
      },
      {
        type: "faq",
        question: "Can I edit a report after creating it?",
        answer:
          "Yes! All reports are saved to your dashboard and can be edited anytime. Changes are saved automatically, and you can regenerate PDFs or resend emails with the updated content.",
      },
      {
        type: "faq",
        question: "How do I add my own market commentary?",
        answer:
          "In the report editor, scroll to the \u201cAgent Notes\u201d section and click to edit. You can add up to 500 characters of personalized commentary that appears below the market data.",
      },
    ],
  },
  {
    id: "scheduling",
    name: "Scheduling Reports",
    icon: Calendar,
    articles: [
      {
        type: "workflow",
        title: "Set Up Automated Delivery",
        description: "Schedule reports to send automatically on a recurring basis",
        steps: [
          {
            title: "Create or select a report",
            body: "Start with any existing report or create a new one. Automated delivery works with all report types.",
            screenshot: "Report selection for scheduling",
          },
          {
            title: "Choose your schedule",
            body: "Select weekly or monthly delivery. Pick the day of the week and time. Reports are generated with fresh data right before sending.",
            screenshot: "Schedule configuration with day/time picker",
          },
          {
            title: "Select recipients",
            body: "Choose individual contacts or entire groups. You can also exclude specific contacts from automated sends.",
            screenshot: "Recipient selection with group filter",
          },
          {
            title: "Activate the schedule",
            body: "Review your settings and click \u2018Activate.\u2019 You\u2019ll receive a confirmation email, and the first report will send on your selected date.",
          },
        ],
      },
      {
        type: "faq",
        question: "Can I pause a scheduled report?",
        answer:
          "Yes. Go to your Schedules page, find the report, and click \u2018Pause.\u2019 You can resume it anytime without losing your settings.",
      },
      {
        type: "faq",
        question: "What time zone are schedules based on?",
        answer:
          "Schedules use the time zone set in your account settings. You can change this under Settings > Account > Time Zone.",
      },
    ],
  },
  {
    id: "contacts",
    name: "Managing Contacts",
    icon: Users,
    articles: [
      {
        type: "workflow",
        title: "Import Contacts from CSV",
        description: "Bulk import your existing contact list",
        steps: [
          {
            title: "Prepare your CSV file",
            body: "Your CSV should have columns for: First Name, Last Name, Email, Phone (optional), and Type (Client or Agent). Download our template for the correct format.",
          },
          {
            title: "Upload the file",
            body: "Go to People > Import and drag your CSV file into the upload zone. We\u2019ll preview the first 5 rows so you can verify the mapping.",
            screenshot: "CSV upload with preview table",
          },
          {
            title: "Map your columns",
            body: "Match your CSV columns to our fields. If your headers match our template, this happens automatically.",
          },
          {
            title: "Complete the import",
            body: "Click \u2018Import\u2019 to add all contacts. Duplicates are detected by email address and skipped automatically.",
          },
        ],
      },
      {
        type: "faq",
        question: "How do I create a contact group?",
        answer:
          "Go to People > Groups tab and click \u201cNew Group.\u201d Give it a name, then add contacts by selecting them from your list or importing a CSV directly into the group.",
      },
      {
        type: "faq",
        question: "Is there a contact limit?",
        answer:
          "Starter plan: 100 contacts. Pro plan: 1,000 contacts. Team plan: Unlimited. You can upgrade anytime from Settings > Billing.",
      },
    ],
  },
  {
    id: "lead-capture",
    name: "Lead Capture",
    icon: Target,
    articles: [
      {
        type: "workflow",
        title: "Set Up a Lead Capture Page",
        description: "Create branded landing pages that capture prospect information",
        steps: [
          {
            title: "Generate a property report",
            body: "Every property report automatically includes a QR code and short link to a branded landing page.",
          },
          {
            title: "Customize the landing page",
            body: "Click \u2018Edit Landing Page\u2019 to customize the headline, description, and which fields to collect (name, email, phone).",
            screenshot: "Landing page editor",
          },
          {
            title: "Share the link or QR code",
            body: "Print the QR code on flyers, yard signs, or postcards. Share the short link via text or social media.",
          },
          {
            title: "Receive leads automatically",
            body: "When someone fills out the form, you\u2019ll get an email notification and the lead is added to your contacts with the source tagged.",
          },
        ],
      },
      {
        type: "faq",
        question: "Where do captured leads go?",
        answer:
          "Leads are automatically added to your Contacts list with the tag \u201cLead\u201d and the source property address. You can also set up automatic group assignment.",
      },
    ],
  },
  {
    id: "branding",
    name: "Branding & Customization",
    icon: Palette,
    articles: [
      {
        type: "workflow",
        title: "Set Up Your Branding",
        description: "Add your logo, colors, and contact information",
        steps: [
          {
            title: "Upload your logo",
            body: "Go to Settings > Branding and upload your logo. We recommend a PNG or SVG file with a transparent background, at least 400px wide.",
            screenshot: "Logo upload with preview",
          },
          {
            title: "Choose your brand colors",
            body: "Select a primary color (used for headers and buttons) and a secondary color (used for accents). Enter hex codes or use the color picker.",
            screenshot: "Color picker with hex input",
          },
          {
            title: "Add your contact information",
            body: "Enter your name, title, phone, email, and website. This information appears in the footer of every report.",
          },
          {
            title: "Preview your branding",
            body: "Click \u2018Preview\u2019 to see how your branding looks on a sample report. Make adjustments until you\u2019re happy, then save.",
            screenshot: "Branded report preview",
          },
        ],
      },
      {
        type: "faq",
        question: "Can I have different branding for different reports?",
        answer:
          "Currently, branding is account-wide. All reports use the same logo and colors. Team plan users can set up multiple brand profiles for different agents.",
      },
    ],
  },
  {
    id: "billing",
    name: "Account & Billing",
    icon: CreditCard,
    articles: [
      {
        type: "faq",
        question: "How do I upgrade my plan?",
        answer:
          "Go to Settings > Billing and click \u2018Change Plan.\u2019 Select your new plan and enter payment details. The upgrade takes effect immediately.",
      },
      {
        type: "faq",
        question: "Can I cancel anytime?",
        answer:
          "Yes, you can cancel anytime from Settings > Billing. Your account will remain active until the end of your current billing period.",
      },
      {
        type: "faq",
        question: "Do you offer refunds?",
        answer:
          "We offer a full refund within the first 14 days if you\u2019re not satisfied. After that, we don\u2019t offer prorated refunds, but you can cancel to prevent future charges.",
      },
    ],
  },
  {
    id: "affiliates",
    name: "For Affiliates",
    icon: Building2,
    articles: [
      {
        type: "workflow",
        title: "Invite an Agent to Your Team",
        description: "Sponsor agents and manage their accounts from your dashboard",
        steps: [
          {
            title: "Go to your Team dashboard",
            body: "Click \u2018Team\u2019 in the sidebar to access your affiliate dashboard. Here you can see all sponsored agents and their activity.",
            screenshot: "Team dashboard overview",
          },
          {
            title: "Send an invitation",
            body: "Click \u2018Invite Agent\u2019 and enter their email address. They\u2019ll receive an invitation to join your team with a sponsored Pro account.",
          },
          {
            title: "Set co-branding options",
            body: "Choose whether your logo appears alongside the agent\u2019s logo on reports. You can set this per agent or as a default for all.",
          },
          {
            title: "Track engagement",
            body: "Monitor each agent\u2019s report activity, contact count, and email open rates from your dashboard.",
            screenshot: "Agent activity analytics",
          },
        ],
      },
      {
        type: "faq",
        question: "How many agents can I sponsor?",
        answer:
          "Team plan includes unlimited agent seats. Each sponsored agent gets full Pro features at no additional cost to them.",
      },
      {
        type: "faq",
        question: "Can agents see my dashboard?",
        answer:
          "No. Agents only see their own reports and contacts. As an affiliate, you can see aggregate activity but not individual contact details.",
      },
    ],
  },
  {
    id: "troubleshooting",
    name: "Troubleshooting",
    icon: HelpCircle,
    articles: [
      {
        type: "faq",
        question: "My report data looks outdated. What should I do?",
        answer:
          "MLS data is refreshed daily. If you see stale data, try clicking \u201cRefresh Data\u201d on the report. If the issue persists, contact support with the property address.",
      },
      {
        type: "faq",
        question: "Emails are going to spam. How do I fix this?",
        answer:
          "Ask your recipients to add reports@trendyreports.com to their contacts. You can also set up a custom sending domain under Settings > Email for better deliverability.",
      },
      {
        type: "faq",
        question: "I can\u2019t find my MLS area. What should I do?",
        answer:
          "We support 600+ MLS systems, but some smaller boards may not be included yet. Contact support@trendyreports.com with your MLS name and we\u2019ll prioritize adding it.",
      },
      {
        type: "faq",
        question: "How do I reset my password?",
        answer:
          "Click \u201cForgot Password\u201d on the login page and enter your email. You\u2019ll receive a reset link within a few minutes. Check your spam folder if you don\u2019t see it.",
      },
    ],
  },
]

const quickStartItems = [
  { title: "Create Your First Report", icon: FileText, sectionId: "getting-started" },
  { title: "Set Up Your Branding", icon: Palette, sectionId: "branding" },
  { title: "Schedule Automated Reports", icon: Calendar, sectionId: "scheduling" },
  { title: "Invite an Agent", icon: UserPlus, sectionId: "affiliates" },
]

// ── Workflow Guide Card ────────────────────────────────

function WorkflowGuideCard({ guide }: { guide: WorkflowGuide }) {
  const [isExpanded, setIsExpanded] = useState(false)

  return (
    <div className="rounded-xl border border-border bg-card overflow-hidden transition-shadow hover:shadow-md">
      <button
        onClick={() => setIsExpanded(!isExpanded)}
        className="w-full p-5 text-left"
      >
        <div className="flex items-start justify-between gap-4">
          <div className="flex-1">
            <h4 className="text-base font-semibold text-foreground">
              {guide.title}
            </h4>
            <p className="mt-1 text-[13px] text-muted-foreground line-clamp-1">
              {guide.description}
            </p>
            <div className="mt-3 flex items-center gap-2">
              {guide.steps.map((_, i) => (
                <div key={i} className="flex items-center gap-1.5">
                  <span className="flex h-5 w-5 items-center justify-center rounded-full bg-primary/10 text-[10px] font-semibold text-primary">
                    {i + 1}
                  </span>
                  {i < guide.steps.length - 1 && (
                    <div className="h-px w-4 bg-border" />
                  )}
                </div>
              ))}
            </div>
          </div>
          <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-full bg-muted">
            {isExpanded ? (
              <ChevronUp className="h-4 w-4 text-muted-foreground" />
            ) : (
              <ChevronDown className="h-4 w-4 text-muted-foreground" />
            )}
          </div>
        </div>
      </button>

      {isExpanded && (
        <div className="border-t border-border px-5 pb-5">
          <div className="mt-4 space-y-6">
            {guide.steps.map((step, i) => (
              <div key={i} className="flex gap-4">
                <div className="flex h-7 w-7 shrink-0 items-center justify-center rounded-full bg-primary text-xs font-semibold text-primary-foreground">
                  {i + 1}
                </div>
                <div className="flex-1">
                  <h5 className="font-semibold text-foreground">{step.title}</h5>
                  <p className="mt-1 text-sm text-muted-foreground leading-relaxed">
                    {step.body}
                  </p>
                  {step.screenshot && (
                    <div className="mt-3 rounded-lg bg-muted p-4 text-center">
                      <div className="mx-auto h-32 w-full max-w-md rounded-md bg-muted-foreground/10 flex items-center justify-center">
                        <span className="text-xs text-muted-foreground">
                          Screenshot: {step.screenshot}
                        </span>
                      </div>
                    </div>
                  )}
                </div>
              </div>
            ))}
          </div>
          <button
            onClick={() => setIsExpanded(false)}
            className="mt-6 text-sm font-medium text-primary hover:text-primary/80"
          >
            Collapse guide
          </button>
        </div>
      )}
    </div>
  )
}

// ── Section Navigation Item ────────────────────────────

function SectionNavItem({
  section,
  isActive,
  articleSummary,
  onClick,
}: {
  section: Section
  isActive: boolean
  articleSummary: string
  onClick: () => void
}) {
  const Icon = section.icon
  return (
    <button
      onClick={onClick}
      className={cn(
        "flex w-full items-center gap-3 rounded-lg px-3 py-2.5 text-left transition-colors",
        isActive
          ? "bg-primary/5 text-primary ring-1 ring-primary/20"
          : "text-muted-foreground hover:bg-muted/50"
      )}
    >
      <Icon
        className={cn(
          "h-4 w-4 shrink-0",
          isActive ? "text-primary" : "text-muted-foreground/60"
        )}
      />
      <div className="flex-1 min-w-0">
        <span
          className={cn(
            "block text-sm font-medium truncate",
            isActive ? "text-primary" : "text-foreground"
          )}
        >
          {section.name}
        </span>
        <span className="text-[11px] text-muted-foreground">
          {articleSummary}
        </span>
      </div>
    </button>
  )
}

// ── Main Page ──────────────────────────────────────────

export default function HelpCenterPage() {
  const [activeSection, setActiveSection] = useState("getting-started")
  const [searchQuery, setSearchQuery] = useState("")

  const currentSection = sections.find((s) => s.id === activeSection)

  const filteredArticles = useMemo(() => {
    if (!searchQuery.trim()) return currentSection?.articles || []

    const query = searchQuery.toLowerCase()
    const allArticles = searchQuery.trim()
      ? sections.flatMap((s) => s.articles)
      : currentSection?.articles || []

    return allArticles.filter((article) => {
      if (article.type === "workflow") {
        return (
          article.title.toLowerCase().includes(query) ||
          article.description.toLowerCase().includes(query) ||
          article.steps.some(
            (s) =>
              s.title.toLowerCase().includes(query) ||
              s.body.toLowerCase().includes(query)
          )
        )
      }
      return (
        article.question.toLowerCase().includes(query) ||
        article.answer.toLowerCase().includes(query)
      )
    })
  }, [currentSection, searchQuery])

  const workflowGuides = filteredArticles.filter(
    (a): a is WorkflowGuide => a.type === "workflow"
  )
  const faqItems = filteredArticles.filter(
    (a): a is FAQItem => a.type === "faq"
  )

  function articleCount(section: Section) {
    const guides = section.articles.filter((a) => a.type === "workflow").length
    const faqs = section.articles.filter((a) => a.type === "faq").length
    if (guides > 0 && faqs > 0) return `${guides} guides, ${faqs} FAQs`
    if (guides > 0) return `${guides} guide${guides > 1 ? "s" : ""}`
    return `${faqs} FAQ${faqs > 1 ? "s" : ""}`
  }

  const isSearching = searchQuery.trim().length > 0

  return (
    <div className="space-y-5">
      <PageHeader
        title="Help Center"
        description="Guides, FAQs, and troubleshooting"
      />

      {/* Welcome Banner + Search */}
      <div className="bg-card border border-border rounded-xl shadow-[var(--shadow-card)] p-6">
        <h2 className="text-lg font-semibold text-foreground">How can we help?</h2>
        <div className="relative mt-3 max-w-xl">
          <Search className="absolute left-3.5 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
          <Input
            type="text"
            placeholder="Search for guides, FAQs, and more..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="h-10 pl-10"
          />
        </div>

        {/* Quick Start Cards */}
        {!isSearching && (
          <div className="mt-5 grid grid-cols-1 gap-3 sm:grid-cols-2 lg:grid-cols-4">
            {quickStartItems.map((item) => {
              const Icon = item.icon
              return (
                <button
                  key={item.title}
                  onClick={() => setActiveSection(item.sectionId)}
                  className="group flex items-center gap-3 rounded-xl border border-border bg-card p-3.5 text-left transition-all hover:border-primary/30 hover:bg-primary/5"
                >
                  <div className="flex h-9 w-9 shrink-0 items-center justify-center rounded-lg bg-primary/10 text-primary transition-colors group-hover:bg-primary group-hover:text-primary-foreground">
                    <Icon className="h-4.5 w-4.5" />
                  </div>
                  <span className="text-sm font-medium text-foreground">
                    {item.title}
                  </span>
                </button>
              )
            })}
          </div>
        )}
      </div>

      {/* Mobile Section Selector */}
      {!isSearching && (
        <div className="lg:hidden">
          <div className="flex flex-wrap gap-2">
            {sections.map((section) => {
              const Icon = section.icon
              return (
                <button
                  key={section.id}
                  onClick={() => setActiveSection(section.id)}
                  className={cn(
                    "flex items-center gap-1.5 rounded-lg px-3 py-1.5 text-xs font-medium transition-colors",
                    activeSection === section.id
                      ? "bg-primary/10 text-primary"
                      : "bg-muted text-muted-foreground hover:bg-muted/80"
                  )}
                >
                  <Icon className="h-3.5 w-3.5" />
                  {section.name}
                </button>
              )
            })}
          </div>
        </div>
      )}

      {/* Main Content: Side Nav + Articles */}
      <div className="flex gap-5">
        {/* In-page Section Nav (desktop only) */}
        {!isSearching && (
          <div className="hidden lg:block w-[200px] shrink-0">
            <div className="sticky top-4 space-y-1">
              {sections.map((section) => (
                <SectionNavItem
                  key={section.id}
                  section={section}
                  isActive={activeSection === section.id}
                  articleSummary={articleCount(section)}
                  onClick={() => setActiveSection(section.id)}
                />
              ))}
            </div>
          </div>
        )}

        {/* Article Content */}
        <div className={cn("flex-1 min-w-0", isSearching && "w-full")}>
          {/* Section Header */}
          {!isSearching && currentSection && (
            <div className="flex items-center gap-2 mb-4">
              <currentSection.icon className="h-5 w-5 text-primary" />
              <h2 className="text-lg font-semibold text-foreground">
                {currentSection.name}
              </h2>
            </div>
          )}

          {isSearching && (
            <div className="flex items-center justify-between mb-4">
              <p className="text-sm text-muted-foreground">
                {filteredArticles.length} result{filteredArticles.length !== 1 ? "s" : ""} for &ldquo;{searchQuery}&rdquo;
              </p>
              <button
                onClick={() => setSearchQuery("")}
                className="text-sm font-medium text-primary hover:text-primary/80"
              >
                Clear search
              </button>
            </div>
          )}

          {/* Workflow Guides */}
          {workflowGuides.length > 0 && (
            <div>
              <h3 className="text-[11px] font-semibold uppercase tracking-[0.05em] text-muted-foreground mb-3">
                Step-by-Step Guides
              </h3>
              <div className="space-y-3">
                {workflowGuides.map((guide, i) => (
                  <WorkflowGuideCard key={i} guide={guide} />
                ))}
              </div>
            </div>
          )}

          {/* FAQ Items */}
          {faqItems.length > 0 && (
            <div className={workflowGuides.length > 0 ? "mt-6" : ""}>
              <h3 className="text-[11px] font-semibold uppercase tracking-[0.05em] text-muted-foreground mb-3">
                Frequently Asked Questions
              </h3>
              <Accordion
                type="single"
                collapsible
                className="rounded-xl border border-border bg-card overflow-hidden shadow-[var(--shadow-card)]"
              >
                {faqItems.map((faq, i) => (
                  <AccordionItem key={i} value={`faq-${i}`}>
                    <AccordionTrigger className="px-5 py-4 text-left text-sm font-medium text-foreground hover:no-underline hover:bg-muted/30">
                      {faq.question}
                    </AccordionTrigger>
                    <AccordionContent className="px-5 text-sm text-muted-foreground leading-relaxed">
                      {faq.answer}
                    </AccordionContent>
                  </AccordionItem>
                ))}
              </Accordion>
            </div>
          )}

          {/* Empty State */}
          {filteredArticles.length === 0 && (
            <div className="rounded-xl border border-border bg-card p-10 text-center shadow-[var(--shadow-card)]">
              <HelpCircle className="mx-auto h-10 w-10 text-muted-foreground/40" />
              <p className="mt-4 text-muted-foreground">
                No articles found matching &ldquo;{searchQuery}&rdquo;
              </p>
              <button
                onClick={() => setSearchQuery("")}
                className="mt-2 text-sm font-medium text-primary hover:text-primary/80"
              >
                Clear search
              </button>
            </div>
          )}
        </div>
      </div>

      {/* Still Need Help Footer */}
      <div className="bg-card border border-border rounded-xl shadow-[var(--shadow-card)] p-5">
        <div className="flex flex-col items-center gap-4 text-center sm:flex-row sm:text-left">
          <div className="flex h-11 w-11 items-center justify-center rounded-full bg-primary/10 shrink-0">
            <Mail className="h-5 w-5 text-primary" />
          </div>
          <div className="flex-1">
            <h3 className="font-semibold text-foreground">Still need help?</h3>
            <p className="mt-0.5 text-sm text-muted-foreground">
              Can&apos;t find what you&apos;re looking for? Our support team is here to help.
            </p>
          </div>
          <div className="flex items-center gap-3">
            <Button variant="outline" size="sm" asChild>
              <a href="mailto:support@trendyreports.com" className="gap-2">
                <Mail className="h-3.5 w-3.5" />
                Contact Support
              </a>
            </Button>
          </div>
        </div>
      </div>
    </div>
  )
}
